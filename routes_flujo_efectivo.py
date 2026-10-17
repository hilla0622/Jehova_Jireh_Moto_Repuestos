"""RF96-RF102: rutas contables con cálculo en servidor y auditoría inmutable."""
import calendar
import json
from datetime import datetime, timedelta, timezone
from functools import wraps
from uuid import uuid4

from flask import jsonify, request, session, render_template, make_response
from flujo_service import (ACTIVIDADES, RESULTADOS, TIPOS_PARTIDA, calcular_conciliacion,
                           calcular_flujo, dinero, fecha, huella, serializable, validar_distribucion)


def filas(cursor, sql, params=()):
    cursor.execute(sql, params)
    keys = [c[0] for c in cursor.description]
    return [dict(zip(keys, row)) for row in cursor.fetchall()]


def eventos(cursor, tipo):
    result = {}
    for row in filas(cursor, 'SELECT clave, contenido FROM flujo_eventos WHERE tipo = ? ORDER BY id DESC', (tipo,)):
        result.setdefault(row['clave'], json.loads(row['contenido']))
    return result


def evento(cursor, tipo, clave, contenido, motivo):
    cursor.execute('INSERT INTO flujo_eventos (tipo, clave, contenido, motivo, usuario_id) VALUES (?, ?, ?, ?, ?)',
                   (tipo, str(clave), json.dumps(serializable(contenido), ensure_ascii=False), motivo, session['user']['id']))


def motivo_requerido(data):
    motivo = str(data.get('motivo', data.get('motivo_reclasificacion', ''))).strip()
    if not motivo or len(motivo) > 1000:
        raise ValueError('Ingrese una justificación de entre 1 y 1000 caracteres.')
    return motivo


def mayor(cursor, fin):
    rows = filas(cursor, '''
        SELECT a.id AS asiento_id, a.fecha, a.concepto, a.modulo_origen,
               m.id AS movimiento_id, m.cuenta_id, m.debe, m.haber,
               c.codigo, c.nombre, c.clasificacion, c.flujo_categoria,
               c.es_efectivo_equivalente AS es_efectivo, c.ajuste_no_monetario
        FROM asientos_contables a
        INNER JOIN movimientos_contables m ON m.asiento_id = a.id
        INNER JOIN cuentas_contables c ON c.id = m.cuenta_id
        WHERE CAST(a.fecha AS DATE) <= ? ORDER BY a.fecha, a.id, m.id
    ''', (fin,))
    for row in rows:
        row['fecha'] = fecha(row['fecha'])
    return rows


def generar(cursor, args):
    # Nicaragua: UTC-6 sin horario de verano. El corte implícito nunca incluye futuro.
    hoy = datetime.now(timezone(timedelta(hours=-6))).date().isoformat()
    fin = fecha(args.get('end') or args.get('fecha_fin') or hoy)
    movs = mayor(cursor, fin)
    inicio_param = args.get('start') or args.get('fecha_inicio')
    inicio = fecha(inicio_param or f"{fin[:7]}-01")
    if not inicio_param and inicio > fin:
        inicio = min(inicio, fin)
    reglas = {k: v['actividad'] for k, v in eventos(cursor, 'regla').items()}
    decisiones = eventos(cursor, 'distribucion')
    distribuciones = {int(k): v['partes'] for k, v in decisiones.items()}
    ajustes = {int(k): v for k, v in eventos(cursor, 'ajuste').items() if v.get('activo', True)}
    reporte = calcular_flujo(movs, inicio, fin, args.get('metodo', 'Directo'), reglas, distribuciones, ajustes)
    correcciones = eventos(cursor, 'correccion')
    for aid, correccion in correcciones.items():
        efectivo = [m for m in movs if m['asiento_id'] == int(aid) and m['es_efectivo'] and inicio <= m['fecha'] <= fin]
        if efectivo and decisiones.get(aid, {}).get('revision_correccion') != huella(correccion):
            reporte['pendientes_clasificacion'].append({'asiento_id': int(aid), 'motivo': 'Comprobante corregido: revise y confirme la distribución del efectivo original.'})
            reporte['puede_guardar'] = False
    reporte['revision'] = huella({'reporte': reporte, 'correcciones': correcciones})
    return reporte


def contexto_conciliacion(cursor, args):
    anio, mes = int(args.get('anio')), int(args.get('mes'))
    if not 1900 <= anio <= 9999 or not 1 <= mes <= 12:
        raise ValueError('Año o mes inválido.')
    corte = f'{anio:04d}-{mes:02d}-{calendar.monthrange(anio, mes)[1]:02d}'
    cuentas = filas(cursor, """SELECT id, codigo, nombre FROM cuentas_contables
        WHERE es_efectivo_equivalente = 1 AND (codigo LIKE '1.1.02%' OR nombre LIKE '%banco%') ORDER BY codigo""")
    cuenta_id = int(args.get('cuenta_id') or (cuentas[0]['id'] if cuentas else 0))
    cuenta = next((c for c in cuentas if c['id'] == cuenta_id), None)
    if not cuenta:
        raise ValueError('Seleccione una cuenta bancaria configurada como efectivo.')
    movs = filas(cursor, '''SELECT m.id AS movimiento_id, a.id AS asiento_id, a.fecha, a.concepto, m.debe, m.haber
        FROM movimientos_contables m INNER JOIN asientos_contables a ON a.id = m.asiento_id
        WHERE m.cuenta_id = ? AND CAST(a.fecha AS DATE) <= ? ORDER BY a.fecha, a.id, m.id''', (cuenta_id, corte))
    for m in movs:
        m['fecha'] = fecha(m['fecha'])
    saldo = sum((dinero(m['debe']) - dinero(m['haber']) for m in movs), dinero(0))
    cabeceras = filas(cursor, '''SELECT id, anio, mes, saldo_segun_libros, saldo_segun_banco,
        diferencia, estado, observaciones FROM conciliaciones_bancarias
        WHERE cuenta_id = ? ORDER BY anio DESC, mes DESC''', (cuenta_id,))
    actual = next((c for c in cabeceras if (c['anio'], c['mes']) == (anio, mes)), None)
    anterior = next((c for c in cabeceras if (c['anio'], c['mes']) < (anio, mes)), None)
    snapshots = eventos(cursor, 'conciliacion')

    def partidas_de(c):
        if not c:
            return []
        snap = snapshots.get(str(c['id']))
        if snap:
            return snap['partidas']
        legacy = filas(cursor, '''SELECT id, tipo_partida, fecha, numero_documento_referencia,
            descripcion, monto, efecto_en_saldo, esta_conciliada, movimiento_contable_id
            FROM conciliacion_partidas_pendientes WHERE conciliacion_id = ? ORDER BY id''', (c['id'],))
        for p in legacy:
            p['uid'] = 'legacy-' + str(p['id'])
            p['fecha'] = fecha(p['fecha'])
        return serializable(legacy)

    heredadas = [dict(p, heredada=True) for p in partidas_de(anterior) if not p.get('esta_conciliada')]
    partidas = partidas_de(actual) if actual else heredadas
    rev = huella({'saldo': saldo, 'movimientos': movs, 'actual': actual, 'partidas': partidas,
                  'heredadas': heredadas, 'ultima': cabeceras[0] if cabeceras else None})
    return serializable(dict(cuenta=cuenta, cuentas_bancos=cuentas, anio=anio, mes=mes, fecha_corte=corte,
                             saldo_segun_libros=saldo, movimientos_mes=[m for m in movs if m['fecha'][:7] == corte[:7]],
                             conciliacion_guardada=actual, partidas_pendientes=partidas,
                             heredadas=heredadas, revision=rev,
                             solo_lectura=bool(cabeceras and (cabeceras[0]['anio'], cabeceras[0]['mes']) > (anio, mes))))


def register_flujo_efectivo_routes(app):
    get_db = app.config.get('GET_DB_CONNECTION')
    if not get_db:
        from app import get_db_connection
        get_db = get_db_connection

    def api(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            if 'user' not in session:
                return jsonify(error='Sesión no iniciada.'), 401
            if session['user'].get('rol') not in ('Administrador', 'Gerente Administrativo y Financiero', 'Contador', 'Contador Externo'):
                return jsonify(error='Acceso reservado al personal financiero.'), 403
            conn = None
            try:
                if request.method == 'POST' and not isinstance(request.get_json(silent=True), dict):
                    raise ValueError('Se requiere un objeto JSON con los datos de la operación.')
                conn = get_db()
                cursor = conn.cursor()
                # Protege recalcular+guardar y la creación concurrente de un mismo período.
                cursor.execute('SET TRANSACTION ISOLATION LEVEL SERIALIZABLE')
                result = f(cursor, *args, **kwargs)
                conn.commit()
                return result
            except (ValueError, TypeError, KeyError) as e:
                if conn:
                    conn.rollback()
                return jsonify(error=str(e)), 400
            except Exception:
                if conn:
                    conn.rollback()
                app.logger.exception('Error en módulo de flujo de efectivo')
                return jsonify(error='No se pudo completar la operación. Verifique la conexión y la migración migrar_flujo_v2.py.'), 500
            finally:
                if conn:
                    conn.close()
        return wrapped

    @app.route('/api/finanzas/flujo_efectivo', methods=['GET'])
    @api
    def flujo(cursor):
        return jsonify(generar(cursor, request.args))

    @app.route('/api/finanzas/flujo_efectivo/guardar', methods=['POST'])
    @api
    def guardar_flujo(cursor):
        data = request.get_json() or {}
        reporte = generar(cursor, data)
        if data.get('revision') != reporte['revision']:
            return jsonify(error='El reporte cambió o no tiene revisión válida. Genérelo nuevamente.'), 409
        if not reporte['puede_guardar']:
            raise ValueError('Resuelva las clasificaciones pendientes y la diferencia antes de guardar el corte.')
        inicio, fin = reporte['periodo']['start'], reporte['periodo']['end']
        periodo = data.get('periodo_tipo', 'Personalizado')
        if periodo not in ('Mensual', 'Trimestral', 'Anual', 'Personalizado'):
            raise ValueError('Tipo de período inválido.')
        cursor.execute('''INSERT INTO estados_flujo_efectivo (ejercicio_fiscal, periodo_tipo, fecha_inicio,
            fecha_fin, metodo, saldo_inicial_efectivo, flujo_neto_operacion, flujo_neto_inversion,
            flujo_neto_financiamiento, variacion_neta_efectivo, saldo_final_calculado,
            saldo_final_balance_general, diferencia_cuadratura, esta_cuadrado, estado, observaciones, usuario_elaboro_id)
            OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (int(fin[:4]), periodo, inicio, fin, reporte['metodo'], dinero(reporte['saldo_inicial']),
             dinero(reporte['flujo_neto_operacion']), dinero(reporte['flujo_neto_inversion']),
             dinero(reporte['flujo_neto_financiamiento']), dinero(reporte['variacion_neta_efectivo']),
             dinero(reporte['saldo_final_calculado']), dinero(reporte['saldo_final_balance']),
             dinero(0), 1, 'Borrador', 'Corte verificado; pendiente de aprobación.', session['user']['id']))
        fid = cursor.fetchone()[0]
        detalles = [(c, i['concepto'], i['tipo'], i['importe']) for c, key in
                    [('Operacion', 'actividades_operacion'), ('Inversion', 'actividades_inversion'),
                     ('Financiamiento', 'actividades_financiamiento')] for i in reporte[key]]
        ind = reporte['indirecto_data']
        if ind:
            detalles.insert(0, ('Operacion', 'Utilidad neta', 'Ajuste', ind['utilidad_neta']))
            detalles += [('Operacion', a['concepto'], 'Ajuste', a['importe']) for a in ind['ajustes_no_monetarios']]
            detalles += [('Operacion', c['descripcion'], 'Ajuste', c['impacto']) for c in ind['cambios_capital_trabajo']]
            for a in ind['ajustes_no_monetarios']:
                cursor.execute('''INSERT INTO flujo_ajustes_no_monetarios
                    (flujo_id, concepto, efecto, importe, justificacion, usuario_id) VALUES (?, ?, ?, ?, ?, ?)''',
                    (fid, a['concepto'][:255], a['efecto'], dinero(a['importe']), a['justificacion'], session['user']['id']))
        for orden, (actividad, concepto, tipo, importe) in enumerate(detalles, 1):
            cursor.execute('''INSERT INTO estado_flujo_efectivo_detalle
                (flujo_id, actividad, concepto, tipo_movimiento, importe, orden_presentacion) VALUES (?, ?, ?, ?, ?, ?)''',
                (fid, actividad, concepto[:255], tipo, dinero(importe), orden))
        evento(cursor, 'corte', fid, reporte, 'Corte recalculado y verificado contra el mayor.')
        return jsonify(success=True, flujo_id=fid, message='Corte verificado guardado con su detalle. Estado: Borrador.')

    @app.route('/api/finanzas/flujo_efectivo/cortes', methods=['GET'])
    @api
    def cortes(cursor):
        return jsonify(cortes=eventos(cursor, 'corte'))

    @app.route('/api/finanzas/flujo/configuracion', methods=['GET', 'POST'])
    @api
    def configuracion(cursor):
        if request.method == 'GET':
            cuentas = filas(cursor, '''SELECT id, codigo, nombre, clasificacion, flujo_categoria,
                es_efectivo_equivalente, ajuste_no_monetario FROM cuentas_contables ORDER BY codigo''')
            modulos = filas(cursor, 'SELECT DISTINCT modulo_origen FROM asientos_contables ORDER BY modulo_origen')
            return jsonify(cuentas=cuentas, reglas=eventos(cursor, 'regla'), modulos=modulos)
        data = request.get_json() or {}
        motivo = motivo_requerido(data)
        if data.get('tipo') == 'regla':
            origen = str(data.get('modulo_origen', '')).strip()
            if not origen or len(origen) > 50 or data.get('actividad') not in (*ACTIVIDADES, None):
                raise ValueError('Tipo de transacción o actividad inválidos.')
            evento(cursor, 'regla', origen, {'actividad': data.get('actividad')}, motivo)
        else:
            cid = int(data['cuenta_id'])
            cuentas = filas(cursor, 'SELECT id, flujo_categoria, es_efectivo_equivalente, ajuste_no_monetario, clasificacion FROM cuentas_contables WHERE id = ?', (cid,))
            if not cuentas:
                raise ValueError('Cuenta inexistente.')
            cat = data.get('flujo_categoria')
            if cat not in (*ACTIVIDADES, 'Efectivo_Equivalente'):
                raise ValueError('Seleccione la etiqueta de flujo.')
            no_monetario = data.get('ajuste_no_monetario', False)
            if not isinstance(no_monetario, bool):
                raise ValueError('Indicador no monetario inválido.')
            if no_monetario and cuentas[0]['clasificacion'] not in RESULTADOS:
                raise ValueError('El ajuste automático se configura en la cuenta de ingreso o gasto, no en su contrapartida.')
            if cat == 'Efectivo_Equivalente' and cuentas[0]['clasificacion'] != 'Activo corriente':
                raise ValueError('El efectivo debe ser una cuenta de activo corriente.')
            cursor.execute('UPDATE cuentas_contables SET flujo_categoria = ?, es_efectivo_equivalente = ?, ajuste_no_monetario = ? WHERE id = ?',
                           (cat, int(cat == 'Efectivo_Equivalente'), int(no_monetario), cid))
            evento(cursor, 'cuenta', cid, {'antes': cuentas[0], 'despues': data}, motivo)
        return jsonify(success=True, message='Regla guardada y auditada. Regenere el reporte.')

    @app.route('/api/finanzas/flujo/asiento/<int:aid>', methods=['GET'])
    @api
    def consultar_asiento(cursor, aid):
        rows = filas(cursor, 'SELECT fecha FROM asientos_contables WHERE id = ?', (aid,))
        if not rows:
            raise ValueError('Asiento inexistente.')
        movs = [m for m in mayor(cursor, fecha(rows[0]['fecha'])) if m['asiento_id'] == aid]
        ajustes_guardados = eventos(cursor, 'ajuste')
        return jsonify(movimientos=serializable(movs), revision=huella(movs),
                       distribucion=eventos(cursor, 'distribucion').get(str(aid)),
                       ajustes={str(m['movimiento_id']): ajustes_guardados.get(str(m['movimiento_id'])) for m in movs})

    @app.route('/api/finanzas/reclasificaciones', methods=['GET', 'POST'])
    @api
    def reclasificaciones(cursor):
        if request.method == 'GET':
            rows = filas(cursor, '''SELECT r.id, r.asiento_id, a.fecha AS asiento_fecha, a.concepto AS asiento_concepto,
                r.origen_modulo, r.actividad_anterior, r.actividad_nueva,
                r.motivo_reclasificacion AS motivo, u.nombre_completo AS usuario, r.created_at
                FROM flujo_reclasificaciones_auditoria r LEFT JOIN asientos_contables a ON a.id = r.asiento_id
                LEFT JOIN usuarios u ON u.id = r.usuario_id ORDER BY r.id DESC''')
            for r in rows:
                r['asiento_fecha'], r['created_at'] = str(r['asiento_fecha']), str(r['created_at'])
            return jsonify(reclasificaciones=rows)
        data = request.get_json() or {}
        aid, motivo = int(data['asiento_id']), motivo_requerido(data)
        a = filas(cursor, 'SELECT fecha FROM asientos_contables WHERE id = ?', (aid,))
        if not a:
            raise ValueError('Asiento inexistente.')
        movs = [m for m in mayor(cursor, fecha(a[0]['fecha'])) if m['asiento_id'] == aid]
        if data.get('revision') != huella(movs):
            return jsonify(error='Consulte nuevamente el asiento antes de reclasificarlo.'), 409
        partes = data.get('partes')
        if partes is None:
            efectivo = sum((dinero(m['debe']) - dinero(m['haber']) for m in movs if m['es_efectivo']), dinero(0))
            partes = [{'actividad': data.get('actividad_nueva'), 'importe': efectivo}]
        partes = validar_distribucion(movs, partes)
        anterior = eventos(cursor, 'distribucion').get(str(aid))
        correccion = eventos(cursor, 'correccion').get(str(aid))
        evento(cursor, 'distribucion', aid, {'partes': partes, 'anterior': anterior['partes'] if anterior else None,
               'revision_mayor': huella(movs), 'revision_correccion': huella(correccion) if correccion else None}, motivo)
        cats = sorted({p['actividad'] for p in partes})
        cursor.execute('''INSERT INTO flujo_reclasificaciones_auditoria
            (asiento_id, origen_modulo, actividad_anterior, actividad_nueva, motivo_reclasificacion, usuario_id)
            VALUES (?, ?, ?, ?, ?, ?)''', (aid, movs[0]['modulo_origen'] or 'MANUAL', 'Manual' if anterior else 'Automatica',
                                          cats[0] if len(cats) == 1 else 'Mixta', motivo, session['user']['id']))
        return jsonify(success=True, message='Distribución aplicada al flujo y registrada en auditoría.')

    @app.route('/api/finanzas/flujo/ajustes', methods=['POST'])
    @api
    def ajustes(cursor):
        data = request.get_json() or {}
        mid, motivo = int(data['movimiento_id']), motivo_requerido(data)
        row = filas(cursor, '''SELECT m.debe, m.haber, c.es_efectivo_equivalente FROM movimientos_contables m
            INNER JOIN cuentas_contables c ON c.id = m.cuenta_id WHERE m.id = ?''', (mid,))
        if not row or row[0]['es_efectivo_equivalente']:
            raise ValueError('El ajuste debe referirse a un movimiento no monetario o de capital de trabajo.')
        importe = dinero(data.get('importe'))
        if abs(importe) > abs(dinero(row[0]['debe']) - dinero(row[0]['haber'])):
            raise ValueError('El ajuste no puede superar el importe del movimiento de referencia.')
        evento(cursor, 'ajuste', mid, {'importe': importe, 'motivo': motivo, 'activo': not data.get('restaurar', False)}, motivo)
        return jsonify(success=True, message='Ajuste registrado. Sustituye el ajuste automático de ese movimiento; no lo duplica.')

    @app.route('/api/finanzas/flujo/correcciones', methods=['POST'])
    @api
    def correcciones(cursor):
        data = request.get_json() or {}
        aid, motivo = int(data['asiento_id']), motivo_requerido(data)
        origen = filas(cursor, 'SELECT fecha, modulo_origen FROM asientos_contables WHERE id = ?', (aid,))
        if not origen:
            raise ValueError('Asiento inexistente.')
        if str(aid) in eventos(cursor, 'correccion'):
            raise ValueError('Este asiento ya tiene corrección. Revise el asiento de ajuste para no duplicarla.')
        movs = [m for m in mayor(cursor, fecha(origen[0]['fecha'])) if m['asiento_id'] == aid]
        if data.get('revision') != huella(movs):
            return jsonify(error='El asiento cambió. Consúltelo nuevamente.'), 409
        f = fecha(data.get('fecha'))
        if f < fecha(origen[0]['fecha']):
            raise ValueError('La corrección no puede ser anterior al comprobante original.')
        nuevos = data.get('movimientos', [])
        cuentas = {c['id'] for c in filas(cursor, 'SELECT id FROM cuentas_contables')}
        validados = []
        for m in nuevos:
            d, h, cid = dinero(m.get('debe', 0)), dinero(m.get('haber', 0)), int(m['cuenta_id'])
            if cid not in cuentas or d < 0 or h < 0 or bool(d) == bool(h):
                raise ValueError('Cada línea requiere cuenta válida y un importe positivo en Debe o Haber.')
            validados.append({'cuenta_id': cid, 'debe': d, 'haber': h})
        if len(validados) < 2 or sum((m['debe'] - m['haber'] for m in validados), dinero(0)):
            raise ValueError('El comprobante corregido debe tener al menos dos líneas y cuadrar al centavo.')
        cursor.execute('''INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
            OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?)''',
            (f, f'Ajuste del asiento {aid}: {motivo}'[:255], 'AJUSTE_FLUJO', aid, session['user']['id']))
        nuevo_id = cursor.fetchone()[0]
        # Registrar solamente las diferencias por cuenta: no crear cobros y pagos ficticios por reversar.
        delta = {}
        for m in movs:
            delta[m['cuenta_id']] = delta.get(m['cuenta_id'], dinero(0)) - dinero(m['debe']) + dinero(m['haber'])
        for m in validados:
            delta[m['cuenta_id']] = delta.get(m['cuenta_id'], dinero(0)) + m['debe'] - m['haber']
        if not any(delta.values()):
            raise ValueError('No hay diferencias contables; utilice reclasificación de flujo si solo cambia la actividad.')
        for cid, importe in delta.items():
            if importe:
                cursor.execute('INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, ?)',
                               (nuevo_id, cid, max(importe, dinero(0)), max(-importe, dinero(0))))
        evento(cursor, 'correccion', aid, {'antes': movs, 'corregido': validados, 'asiento_ajuste_id': nuevo_id, 'fecha': f}, motivo)
        return jsonify(success=True, message=f'Corrección registrada en asiento {nuevo_id}. Revise y confirme la distribución de efectivo del asiento original {aid}.', asiento_id=nuevo_id)

    @app.route('/api/finanzas/conciliacion/datos', methods=['GET'])
    @api
    def conciliacion(cursor):
        return jsonify(contexto_conciliacion(cursor, request.args))

    @app.route('/api/finanzas/conciliacion/guardar', methods=['POST'])
    @api
    def guardar_conciliacion(cursor):
        data = request.get_json() or {}
        ctx = contexto_conciliacion(cursor, data)
        if ctx['solo_lectura']:
            raise ValueError('Hay conciliaciones posteriores. Este corte histórico es de solo lectura.')
        if data.get('revision') != ctx['revision']:
            return jsonify(error='El mayor o la conciliación cambiaron. Recargue antes de guardar.'), 409
        if data.get('saldo_segun_banco') in (None, ''):
            raise ValueError('Ingrese el saldo del extracto bancario del período.')
        partidas = data.get('partidas', [])
        if not isinstance(partidas, list):
            raise ValueError('Partidas inválidas.')
        uids = set()
        originales = {p['uid']: p for p in ctx['partidas_pendientes']}
        for p in partidas:
            if not isinstance(p, dict):
                raise ValueError('Partida inválida.')
            if len(str(p.get('descripcion', ''))) > 255 or len(str(p.get('numero_documento_referencia', ''))) > 100:
                raise ValueError('La descripción admite 255 caracteres y la referencia 100.')
            p['uid'] = str(p.get('uid') or uuid4())
            if p['uid'] in uids or len(p['uid']) > 64:
                raise ValueError('Hay partidas duplicadas.')
            uids.add(p['uid'])
            anterior = originales.get(p['uid'])
            if anterior and anterior.get('heredada'):
                for campo in ('tipo_partida', 'fecha', 'numero_documento_referencia', 'descripcion', 'monto', 'efecto_en_saldo'):
                    if p.get(campo) != anterior.get(campo):
                        raise ValueError('Una partida heredada no puede cambiar de importe o identidad; registre su resolución.')
                p['heredada'] = True
            if p.get('esta_conciliada') and not str(p.get('resolucion', '')).strip():
                raise ValueError('Indique la referencia o explicación de cada partida resuelta.')
            mid = p.get('movimiento_contable_id')
            if mid:
                row = filas(cursor, '''SELECT m.id FROM movimientos_contables m INNER JOIN asientos_contables a ON a.id=m.asiento_id
                    WHERE m.id=? AND m.cuenta_id=? AND CAST(a.fecha AS DATE)<=?''', (int(mid), ctx['cuenta']['id'], ctx['fecha_corte']))
                if not row:
                    raise ValueError('El movimiento vinculado no pertenece a la cuenta o es posterior al corte.')
        if any(p['uid'] not in uids for p in ctx['partidas_pendientes'] if p.get('heredada')):
            raise ValueError('No elimine partidas heredadas; márquelas resueltas con su referencia.')
        resumen = calcular_conciliacion(ctx['saldo_segun_libros'], data['saldo_segun_banco'], partidas, ctx['fecha_corte'])
        cid = ctx['conciliacion_guardada']['id'] if ctx['conciliacion_guardada'] else None
        params = (ctx['fecha_corte'], dinero(resumen['saldo_segun_libros']), dinero(resumen['saldo_segun_banco']),
                  dinero(resumen['diferencia']), resumen['estado'], str(data.get('observaciones', '')), session['user']['id'])
        if cid:
            cursor.execute('''UPDATE conciliaciones_bancarias SET fecha_corte=?, saldo_segun_libros=?, saldo_segun_banco=?,
                diferencia=?, estado=?, observaciones=?, usuario_id=? WHERE id=?''', (*params, cid))
            cursor.execute('DELETE FROM conciliacion_partidas_pendientes WHERE conciliacion_id=?', (cid,))
        else:
            cursor.execute('''INSERT INTO conciliaciones_bancarias (cuenta_id, anio, mes, fecha_corte, saldo_segun_libros,
                saldo_segun_banco, diferencia, estado, observaciones, usuario_id) OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (ctx['cuenta']['id'], ctx['anio'], ctx['mes'], *params))
            cid = cursor.fetchone()[0]
        for p in partidas:
            signo = TIPOS_PARTIDA[p['tipo_partida']][1] or p['efecto_en_saldo']
            cursor.execute('''INSERT INTO conciliacion_partidas_pendientes (conciliacion_id, tipo_partida, fecha,
                numero_documento_referencia, descripcion, monto, efecto_en_saldo, esta_conciliada, movimiento_contable_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''', (cid, p['tipo_partida'], p['fecha'], p['numero_documento_referencia'],
                p['descripcion'], dinero(p['monto']), signo, int(bool(p.get('esta_conciliada'))), p.get('movimiento_contable_id') or None))
        evento(cursor, 'conciliacion', cid, {'resumen': resumen, 'partidas': partidas, 'fecha_corte': ctx['fecha_corte']},
               'Conciliación recalculada contra el mayor; versión completa conservada.')
        return jsonify(success=True, conciliacion_id=cid, resumen=resumen, message=f"Conciliación guardada: {resumen['estado']}.")

    @app.route('/api/finanzas/conciliaciones', methods=['GET'])
    @api
    def historial(cursor):
        rows = filas(cursor, '''SELECT cb.*, c.nombre AS cuenta, u.nombre_completo AS usuario
            FROM conciliaciones_bancarias cb INNER JOIN cuentas_contables c ON c.id=cb.cuenta_id
            LEFT JOIN usuarios u ON u.id=cb.usuario_id ORDER BY cb.anio DESC, cb.mes DESC''')
        for row in rows:
            row['fecha_corte'], row['created_at'] = str(row['fecha_corte']), str(row['created_at'])
        return jsonify(conciliaciones=serializable(rows))

    @app.route('/api/finanzas/flujo/auditoria', methods=['GET'])
    @api
    def auditoria(cursor):
        rows = filas(cursor, '''SELECT e.id, e.tipo, e.clave, e.contenido, e.motivo, e.created_at, u.nombre_completo AS usuario
            FROM flujo_eventos e LEFT JOIN usuarios u ON u.id=e.usuario_id ORDER BY e.id DESC''')
        for row in rows:
            row['created_at'] = str(row['created_at'])
            row['contenido'] = json.loads(row['contenido'])
        return jsonify(eventos=rows)

    @app.route('/api/finanzas/reportes/exportar/<tipo>', methods=['GET'])
    @api
    def exportar(cursor, tipo):
        if tipo not in ('flujo', 'resultados', 'balance', 'comprobacion'):
            raise ValueError('Tipo de estado financiero inválido.')
        hoy = datetime.now(timezone(timedelta(hours=-6))).date().isoformat()
        fin = fecha(request.args.get('end') or hoy)
        movs = mayor(cursor, fin)
        inicio_param = request.args.get('start')
        inicio = fecha(inicio_param or f"{fin[:7]}-01")
        if not inicio_param and inicio > fin:
            inicio = min(inicio, fin)
        elif inicio > fin:
            raise ValueError('Período inválido.')
        titulos = {'flujo': 'Estado de Flujos de Efectivo', 'resultados': 'Estado de Resultados',
                   'balance': 'Balance General', 'comprobacion': 'Balance de Comprobación'}
        filas_reporte, advertencias = [], []
        encabezados = ['Concepto', 'Importe (C$)']
        periodo = f'Del {inicio} al {fin}' if tipo in ('flujo', 'resultados') else f'Al {fin}'
        if tipo == 'flujo':
            r = generar(cursor, request.args)
            titulos[tipo] += f" — Método {r['metodo']}"
            if not r['puede_guardar']:
                advertencias.append('BORRADOR: existen diferencias o clasificaciones pendientes de revisión.')
            advertencias += [f"Asiento {p['asiento_id']}: {p['motivo']}" for p in r['pendientes_clasificacion']]
            filas_reporte.append(['Saldo inicial de efectivo', dinero(r['saldo_inicial'])])
            if r['indirecto_data']:
                ind = r['indirecto_data']
                filas_reporte.append(['Utilidad neta', dinero(ind['utilidad_neta'])])
                filas_reporte += [[a['concepto'], dinero(a['importe'])] for a in ind['ajustes_no_monetarios']]
                filas_reporte += [[a['descripcion'], dinero(a['impacto'])] for a in ind['cambios_capital_trabajo']]
            for actividad in ('operacion', 'inversion', 'financiamiento'):
                filas_reporte += [[i['concepto'], dinero(i['importe'])] for i in r['actividades_' + actividad]]
                filas_reporte.append(['Flujo neto de ' + actividad, dinero(r['flujo_neto_' + actividad])])
            filas_reporte += [[label, dinero(r[key])] for label, key in [
                ('Variación neta de efectivo', 'variacion_neta_efectivo'), ('Saldo final calculado', 'saldo_final_calculado'),
                ('Caja y bancos según mayor', 'saldo_final_balance'), ('Diferencia de cuadratura', 'diferencia_cuadratura')]]
        else:
            saldos = {}
            for m in movs:
                if tipo == 'resultados' and (m['fecha'] < inicio or m['clasificacion'] not in RESULTADOS):
                    continue
                item = saldos.setdefault(m['cuenta_id'], {'codigo': m['codigo'], 'nombre': m['nombre'],
                                        'clasificacion': m['clasificacion'], 'neto': dinero(0)})
                item['neto'] += dinero(m['debe']) - dinero(m['haber'])
            saldos = sorted(saldos.values(), key=lambda c: c['codigo'])
            if tipo == 'resultados':
                filas_reporte = [[f"{s['codigo']} {s['nombre']}", -s['neto']] for s in saldos]
                filas_reporte.append(['Utilidad / pérdida neta', sum((-s['neto'] for s in saldos), dinero(0))])
            else:
                encabezados = ['Cuenta', 'Saldo deudor (C$)', 'Saldo acreedor (C$)'] if tipo == 'comprobacion' else ['Cuenta', 'Activos (C$)', 'Pasivos y patrimonio (C$)']
                for s in saldos:
                    if tipo == 'balance' and s['clasificacion'] in RESULTADOS:
                        continue
                    if tipo == 'comprobacion':
                        d, h = max(s['neto'], dinero(0)), max(-s['neto'], dinero(0))
                    elif s['clasificacion'].startswith('Activo'):
                        d, h = s['neto'], dinero(0)
                    else:
                        d, h = dinero(0), -s['neto']
                    filas_reporte.append([f"{s['codigo']} {s['nombre']}", d, h])
                if tipo == 'balance':
                    utilidad = sum((-s['neto'] for s in saldos if s['clasificacion'] in RESULTADOS), dinero(0))
                    filas_reporte.append(['Resultado acumulado pendiente de cierre', dinero(0), utilidad])
                d, h = (sum((row[i] for row in filas_reporte), dinero(0)) for i in (1, 2))
                filas_reporte.append(['Totales', d, h])
                if d != h:
                    advertencias.append(f'BORRADOR: diferencia de cuadratura C$ {d-h:.2f}.')
        html = render_template('estado_financiero_export.html', titulo=titulos[tipo], periodo=periodo,
                               encabezados=encabezados, filas=filas_reporte, advertencias=advertencias)
        response = make_response(html)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        if request.args.get('descargar') == '1':
            response.headers['Content-Disposition'] = f'attachment; filename="estado-{tipo}-{fin}.html"'
        return response
