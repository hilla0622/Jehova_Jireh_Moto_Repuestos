"""Pagos, archivos privados, dotaciones y seguimiento de riesgos de RRHH."""
from contextlib import contextmanager
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO
from pathlib import PurePath

from flask import jsonify, request, session, send_file
from werkzeug.utils import secure_filename


def texto(data, campo, maximo, obligatorio=True):
    valor = data.get(campo, '')
    if not isinstance(valor, str):
        raise ValueError(f'{campo}: texto inválido.')
    valor = valor.strip()
    if (obligatorio and not valor) or len(valor) > maximo:
        raise ValueError(f'{campo}: complete el campo (máximo {maximo} caracteres).')
    return valor


def entero(data, campo):
    valor = str(data.get(campo, ''))
    if not valor.isdigit() or not 0 < int(valor) <= 2147483647:
        raise ValueError(f'{campo}: debe ser un entero positivo.')
    return int(valor)


def fecha(data, campo, opcional=False):
    valor = data.get(campo)
    if not valor and opcional:
        return None
    try:
        return date.fromisoformat(str(valor)[:10])
    except (TypeError, ValueError):
        raise ValueError(f'{campo}: fecha inválida.')


def archivo_recibido(obligatorio=False):
    archivo = request.files.get('archivo')
    if not archivo or not archivo.filename:
        if obligatorio:
            raise ValueError('Adjunte un archivo PDF, PNG o JPG de hasta 5 MB.')
        return None
    nombre = secure_filename(archivo.filename)
    contenido = archivo.stream.read(5 * 1024 * 1024 + 1)
    tipos = {'.pdf': ('application/pdf', b'%PDF-'), '.png': ('image/png', b'\x89PNG\r\n\x1a\n'),
             '.jpg': ('image/jpeg', b'\xff\xd8\xff'), '.jpeg': ('image/jpeg', b'\xff\xd8\xff')}
    tipo = tipos.get(PurePath(nombre).suffix.lower())
    if not nombre or len(nombre) > 255 or not tipo or not contenido.startswith(tipo[1]):
        raise ValueError('El archivo debe ser un PDF, PNG o JPG válido.')
    if len(contenido) > 5 * 1024 * 1024:
        raise ValueError('El archivo supera el límite de 5 MB.')
    return nombre, tipo[0], contenido


def register_rrhh_control_routes(app):
    from app import execute_query, login_required

    @contextmanager
    def transaccion():
        from app import get_db_connection
        conn = get_db_connection()
        try:
            yield conn.cursor()
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def usuario():
        return session['user'].get('username') or session['user'].get('nombre') or 'RRHH'

    def identidad(cur):
        cur.execute('SELECT @@IDENTITY')
        return int(cur.fetchone()[0])

    def adjuntar(cur, clase, referencia, archivo):
        if archivo:
            cur.execute('''INSERT INTO rrhh_archivos
                (clase, referencia_id, nombre_archivo, mime, contenido, registrado_por)
                VALUES (?, ?, ?, ?, ?, ?)''', (clase, referencia, *archivo, usuario()))

    def serializar(rows):
        if isinstance(rows, dict):
            for key, value in rows.items():
                if isinstance(value, date):
                    rows[key] = value.isoformat()[:10]
                elif isinstance(value, Decimal):
                    rows[key] = float(value)
            return rows
        for row in rows:
            for key, value in row.items():
                if isinstance(value, date):
                    row[key] = value.isoformat()[:10]
                elif isinstance(value, Decimal):
                    row[key] = float(value)
        return rows

    def resolver_cuenta_desembolso(cur, cuenta_id_param, metodo):
        if cuenta_id_param:
            try:
                cur.execute("SELECT id FROM cuentas_contables WHERE id = ?", (int(cuenta_id_param),))
                r = cur.fetchone()
                if r:
                    return int(r[0])
            except Exception:
                pass
        cod = '1.1.01' if metodo == 'Efectivo' else '1.1.02'
        cur.execute("SELECT id FROM cuentas_contables WHERE codigo = ?", (cod,))
        r = cur.fetchone()
        if r:
            return int(r[0])
        nombre = 'Caja' if cod == '1.1.01' else 'Bancos'
        cur.execute("""INSERT INTO cuentas_contables
            (codigo, nombre, clasificacion, naturaleza, descripcion, activo)
            VALUES (?, ?, 'Activo corriente', 'Deudora', ?, 1)""", (cod, nombre, nombre))
        return identidad(cur)

    def resolver_cuenta_sueldos_pagar(cur):
        cur.execute("SELECT id FROM cuentas_contables WHERE codigo = '2.1.04'")
        r = cur.fetchone()
        if r:
            return int(r[0])
        cur.execute("""INSERT INTO cuentas_contables
            (codigo, nombre, clasificacion, naturaleza, descripcion, activo)
            VALUES ('2.1.04', 'Sueldos y salarios por pagar', 'Pasivo corriente', 'Acreedora', 'Sueldos por pagar', 1)""")
        return identidad(cur)

    @app.route('/api/rrhh/pagos-nomina', methods=['GET', 'POST'])
    @login_required
    def pagos_controlados():
        if request.method == 'GET':
            return jsonify(serializar(execute_query('''SELECT p.*, e.nombre_completo AS empleado
                FROM pagos_nomina p JOIN empleados e ON e.id=p.empleado_id
                ORDER BY p.fecha_pago DESC, p.id DESC''', fetchall=True)))
        data = request.get_json(silent=True) or {}
        try:
            nid, eid = entero(data, 'nomina_id'), entero(data, 'empleado_id')
            monto = Decimal(str(data.get('monto_pagado', '')))
            if not monto.is_finite() or monto <= 0 or monto > Decimal('9999999999.99') or monto != monto.quantize(Decimal('.01')):
                raise ValueError('El pago debe ser positivo, finito y tener hasta dos decimales.')
            dia = fecha(data, 'fecha_pago')
            estado = texto(data, 'estado', 30) if data.get('estado') else 'Confirmado'
            if estado not in ('Confirmado', 'Pendiente', 'Anulado'):
                estado = 'Confirmado'

            metodo = texto(data, 'metodo_pago', 50) if data.get('metodo_pago') else 'Transferencia Bancaria'
            if estado == 'Confirmado':
                ref = texto(data, 'numero_referencia', 100)
            else:
                ref = str(data.get('numero_referencia') or '').strip()[:100]
            cuenta_id_in = data.get('cuenta_id')

            with transaccion() as cur:
                # Mismo orden de bloqueo que generación/anulación: cabecera primero.
                cur.execute('SELECT id, periodo_mes, periodo_anio FROM nomina WITH (UPDLOCK, HOLDLOCK) WHERE id=?', (nid,))
                nom_row = cur.fetchone()
                if not nom_row:
                    return jsonify(error='Nómina no encontrada.'), 404
                mes_nom, anio_nom = nom_row[1], nom_row[2]

                cur.execute('SELECT neto_pagar FROM detalle_nomina WHERE nomina_id=? AND empleado_id=?', (nid, eid))
                detalle = cur.fetchone()
                if not detalle:
                    return jsonify(error='El empleado no pertenece a esa nómina.'), 400
                cur.execute("SELECT ISNULL(SUM(monto_pagado),0) FROM pagos_nomina WHERE nomina_id=? AND empleado_id=? AND estado='Confirmado'", (nid, eid))
                saldo = Decimal(str(detalle[0])) - Decimal(str(cur.fetchone()[0]))

                asiento_id = None
                cuenta_id = resolver_cuenta_desembolso(cur, cuenta_id_in, metodo) if (cuenta_id_in or estado == 'Confirmado') else None

                if estado == 'Confirmado':
                    if monto > saldo:
                        return jsonify(error=f'El pago supera el saldo pendiente: C$ {saldo:,.2f}.'), 409
                    if ref:
                        cur.execute('SELECT id FROM pagos_nomina WITH (UPDLOCK, HOLDLOCK) WHERE numero_referencia=? AND metodo_pago=? AND estado=\'Confirmado\'', (ref, metodo))
                        if cur.fetchone():
                            return jsonify(error='La referencia de pago ya fue registrada para ese método.'), 409

                    cur.execute('SELECT nombre_completo FROM empleados WHERE id=?', (eid,))
                    emp_row = cur.fetchone()
                    emp_nom = emp_row[0] if emp_row else f"Empleado #{eid}"

                    cta_sueldos = resolver_cuenta_sueldos_pagar(cur)

                    concepto_asiento = f"Pago de nómina {mes_nom:02d}/{anio_nom} - {emp_nom} ({metodo} Ref: {ref})"
                    uid = session.get('user', {}).get('id', 1)
                    cur.execute("""INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
                        VALUES (GETDATE(), ?, 'RRHH_PAGO', ?, ?)""", (concepto_asiento, nid, uid))
                    asiento_id = identidad(cur)

                    # DEBIT: 2.1.04 Sueldos y salarios por pagar (Disminuye pasivo)
                    cur.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)",
                        (asiento_id, cta_sueldos, float(monto)))
                    # CREDIT: Cuenta de Caja o Banco (Disminuye activo real en balance y mayor)
                    cur.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)",
                        (asiento_id, cuenta_id, float(monto)))

                cur.execute('''INSERT INTO pagos_nomina
                    (nomina_id, empleado_id, monto_pagado, fecha_pago, metodo_pago, numero_referencia, estado, registrado_por, cuenta_id, asiento_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (nid, eid, str(monto), dia, metodo, ref, estado, usuario(), cuenta_id, asiento_id))
            
            msg = 'Pago confirmado y contabilizado.' if estado == 'Confirmado' else f'Comprobante guardado en estado {estado}.'
            saldo_resp = float(saldo - monto) if estado == 'Confirmado' else float(saldo)
            return jsonify(success=True, mensaje=msg, saldo_pendiente=saldo_resp), 201
        except (ValueError, InvalidOperation):
            return jsonify(error='Verifique el importe, los identificadores y los datos del pago.'), 400

    @app.route('/api/rrhh/pagos-nomina/<int:pago_id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def pago_control_item(pago_id):
        if request.method == 'GET':
            row = execute_query('''SELECT p.*, e.nombre_completo AS empleado
                FROM pagos_nomina p JOIN empleados e ON e.id=p.empleado_id
                WHERE p.id=?''', (pago_id,), fetchone=True)
            if not row:
                return jsonify(error='Pago no encontrado.'), 404
            return jsonify(serializar(row))

        if request.method == 'DELETE':
            with transaccion() as cur:
                cur.execute('SELECT id, asiento_id FROM pagos_nomina WITH (UPDLOCK, HOLDLOCK) WHERE id=?', (pago_id,))
                row = cur.fetchone()
                if not row:
                    return jsonify(error='Pago no encontrado.'), 404
                asiento_id = row[1]
                if asiento_id:
                    cur.execute('DELETE FROM movimientos_contables WHERE asiento_id=?', (asiento_id,))
                    cur.execute('DELETE FROM asientos_contables WHERE id=?', (asiento_id,))
                cur.execute('DELETE FROM pagos_nomina WHERE id=?', (pago_id,))
            return jsonify(success=True, mensaje='Comprobante de pago y asiento contable eliminados correctamente.')

        if request.method == 'PUT':
            data = request.get_json(silent=True) or {}
            try:
                dia = fecha(data, 'fecha_pago') if data.get('fecha_pago') else None
                metodo = texto(data, 'metodo_pago', 50) if data.get('metodo_pago') else None
                ref = texto(data, 'numero_referencia', 100) if data.get('numero_referencia') else None
                estado = texto(data, 'estado', 30) if data.get('estado') else None
                cuenta_id_in = data.get('cuenta_id')
                monto_val = data.get('monto_pagado')
                monto = Decimal(str(monto_val)) if monto_val is not None else None
                if monto is not None and (not monto.is_finite() or monto <= 0 or monto > Decimal('9999999999.99') or monto != monto.quantize(Decimal('.01'))):
                    raise ValueError('El pago debe ser positivo, finito y tener hasta dos decimales.')

                with transaccion() as cur:
                    cur.execute('SELECT id, nomina_id, empleado_id, monto_pagado, fecha_pago, metodo_pago, numero_referencia, estado, cuenta_id, asiento_id FROM pagos_nomina WITH (UPDLOCK, HOLDLOCK) WHERE id=?', (pago_id,))
                    actual = cur.fetchone()
                    if not actual:
                        return jsonify(error='Pago no encontrado.'), 404

                    nid, eid = actual[1], actual[2]
                    nuevo_monto = monto if monto is not None else Decimal(str(actual[3]))
                    nuevo_dia = dia or actual[4]
                    nuevo_metodo = metodo or actual[5]
                    nuevo_ref = ref if ref is not None else actual[6]
                    nuevo_estado = estado or actual[7]
                    asiento_id = actual[9]

                    if cuenta_id_in:
                        nuevo_cuenta_id = resolver_cuenta_desembolso(cur, cuenta_id_in, nuevo_metodo)
                    elif actual[8]:
                        nuevo_cuenta_id = actual[8]
                    else:
                        nuevo_cuenta_id = resolver_cuenta_desembolso(cur, None, nuevo_metodo)

                    if nuevo_monto != Decimal(str(actual[3])):
                        cur.execute('SELECT neto_pagar FROM detalle_nomina WHERE nomina_id=? AND empleado_id=?', (nid, eid))
                        detalle = cur.fetchone()
                        if detalle:
                            cur.execute("SELECT ISNULL(SUM(monto_pagado),0) FROM pagos_nomina WHERE nomina_id=? AND empleado_id=? AND estado='Confirmado' AND id!=?", (nid, eid, pago_id))
                            otros_pagos = Decimal(str(cur.fetchone()[0]))
                            saldo_max = Decimal(str(detalle[0])) - otros_pagos
                            if nuevo_monto > saldo_max:
                                return jsonify(error=f'El monto supera el saldo disponible: C$ {saldo_max:,.2f}.'), 409

                    if nuevo_ref:
                        cur.execute('SELECT id FROM pagos_nomina WITH (UPDLOCK, HOLDLOCK) WHERE numero_referencia=? AND metodo_pago=? AND estado=\'Confirmado\' AND id!=?', (nuevo_ref, nuevo_metodo, pago_id))
                        if cur.fetchone():
                            return jsonify(error='La referencia de pago ya fue registrada para ese método.'), 409

                    # Actualización contable sincronizada
                    if nuevo_estado in ('Anulado', 'Pendiente'):
                        if asiento_id:
                            cur.execute('DELETE FROM movimientos_contables WHERE asiento_id=?', (asiento_id,))
                            cur.execute('DELETE FROM asientos_contables WHERE id=?', (asiento_id,))
                            asiento_id = None
                    elif nuevo_estado == 'Confirmado':
                        cta_sueldos = resolver_cuenta_sueldos_pagar(cur)
                        if not asiento_id:
                            cur.execute('SELECT periodo_mes, periodo_anio FROM nomina WHERE id=?', (nid,))
                            nom_row = cur.fetchone()
                            mes_nom, anio_nom = (nom_row[1], nom_row[2]) if nom_row else (1, 2026)
                            cur.execute('SELECT nombre_completo FROM empleados WHERE id=?', (eid,))
                            emp_row = cur.fetchone()
                            emp_nom = emp_row[0] if emp_row else f"Empleado #{eid}"
                            concepto_asiento = f"Pago de nómina {mes_nom:02d}/{anio_nom} - {emp_nom} ({nuevo_metodo} Ref: {nuevo_ref})"
                            uid = session.get('user', {}).get('id', 1)
                            cur.execute("""INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
                                VALUES (GETDATE(), ?, 'RRHH_PAGO', ?, ?)""", (concepto_asiento, nid, uid))
                            asiento_id = identidad(cur)
                        else:
                            cur.execute('DELETE FROM movimientos_contables WHERE asiento_id=?', (asiento_id,))

                        # DEBITO: 2.1.04 Sueldos y salarios por pagar
                        cur.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)",
                            (asiento_id, cta_sueldos, float(nuevo_monto)))
                        # CREDITO: Caja o Bancos (Disminuye activo real)
                        cur.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)",
                            (asiento_id, nuevo_cuenta_id, float(nuevo_monto)))

                    cur.execute('''UPDATE pagos_nomina
                        SET monto_pagado=?, fecha_pago=?, metodo_pago=?, numero_referencia=?, estado=?, cuenta_id=?, asiento_id=?
                        WHERE id=?''', (str(nuevo_monto), nuevo_dia, nuevo_metodo, nuevo_ref, nuevo_estado, nuevo_cuenta_id, asiento_id, pago_id))

                return jsonify(success=True, mensaje='Comprobante de pago actualizado correctamente.')
            except (ValueError, InvalidOperation) as exc:
                return jsonify(error=str(exc) or 'Verifique los datos del pago.'), 400

    @app.route('/api/rrhh/expedientes/<int:emp_id>', methods=['GET', 'POST'])
    @login_required
    def expedientes_con_archivos(emp_id):
        if not execute_query('SELECT id FROM empleados WHERE id=?', (emp_id,), fetchone=True):
            return jsonify(error='Empleado no encontrado.'), 404
        if request.method == 'GET':
            rows = execute_query('''SELECT e.*, a.id AS archivo_id FROM expediente_empleado e
                LEFT JOIN rrhh_archivos a ON a.clase='EXPEDIENTE' AND a.referencia_id=e.id
                WHERE e.empleado_id=? ORDER BY e.id DESC''', (emp_id,), fetchall=True)
            return jsonify(serializar(rows))
        try:
            data = request.form
            tipo, obs = texto(data, 'tipo_documento', 100), texto(data, 'observaciones', 255, False)
            archivo = archivo_recibido(True)
            with transaccion() as cur:
                cur.execute('''INSERT INTO expediente_empleado
                    (empleado_id, tipo_documento, nombre_archivo, usuario_responsable, observaciones)
                    VALUES (?, ?, ?, ?, ?)''', (emp_id, tipo, archivo[0], usuario(), obs))
                adjuntar(cur, 'EXPEDIENTE', identidad(cur), archivo)
            return jsonify(success=True, mensaje='Documento almacenado en el expediente.'), 201
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    @app.route('/api/rrhh/expedientes/doc/<int:doc_id>', methods=['DELETE'])
    @login_required
    def eliminar_documento_privado(doc_id):
        with transaccion() as cur:
            cur.execute('SELECT id FROM expediente_empleado WITH (UPDLOCK, HOLDLOCK) WHERE id=?', (doc_id,))
            if not cur.fetchone():
                return jsonify(error='Documento no encontrado.'), 404
            cur.execute("DELETE FROM rrhh_archivos WHERE clase='EXPEDIENTE' AND referencia_id=?", (doc_id,))
            cur.execute('DELETE FROM expediente_empleado WHERE id=?', (doc_id,))
        return jsonify(success=True)

    @app.route('/api/rrhh/archivos/<int:archivo_id>')
    @login_required
    def descargar_archivo_privado(archivo_id):
        row = execute_query('SELECT nombre_archivo, mime, contenido FROM rrhh_archivos WHERE id=?', (archivo_id,), fetchone=True)
        if not row:
            return jsonify(error='Archivo no encontrado.'), 404
        response = send_file(BytesIO(bytes(row['contenido'])), mimetype=row['mime'],
                             download_name=row['nombre_archivo'], as_attachment=True, max_age=0)
        response.headers['Cache-Control'] = 'no-store'
        response.headers['X-Content-Type-Options'] = 'nosniff'
        return response

    @app.route('/api/rrhh/higiene/epp', methods=['GET', 'POST'])
    @login_required
    def dotaciones_controladas():
        if request.method == 'GET':
            rows = execute_query('''SELECT p.*, e.nombre_completo AS empleado, a.id AS archivo_id,
                r.id AS reposicion_id FROM higiene_epp p
                JOIN empleados e ON e.id=p.empleado_id
                LEFT JOIN rrhh_archivos a ON a.clase='EPP' AND a.referencia_id=p.id
                LEFT JOIN higiene_epp r ON r.repone_a_id=p.id
                ORDER BY p.fecha_entrega DESC, p.id DESC''', fetchall=True)
            return jsonify(serializar(rows))
        try:
            data = request.form if request.mimetype == 'multipart/form-data' else request.get_json(silent=True) or {}
            eid, cantidad = entero(data, 'empleado_id'), entero(data, 'cantidad')
            equipo = texto(data, 'tipo_equipo', 100)
            area = texto(data, 'area', 50)
            estado = texto(data, 'estado_equipo', 50)
            if estado not in ('Nuevo', 'Buen estado'):
                raise ValueError('Seleccione Nuevo o Buen estado para la entrega.')
            entrega = fecha(data, 'fecha_entrega')
            proxima = fecha(data, 'fecha_reposicion_sugerida', True)
            if proxima and proxima < entrega:
                raise ValueError('La reposición prevista no puede ser anterior a la entrega.')
            obs = texto(data, 'observaciones', 255, False)
            anterior = entero(data, 'repone_a_id') if data.get('repone_a_id') else None
            motivo = texto(data, 'motivo_reposicion', 255, bool(anterior))
            archivo = archivo_recibido()
            with transaccion() as cur:
                cur.execute('SELECT activo FROM empleados WHERE id=?', (eid,))
                emp = cur.fetchone()
                if not emp or not emp[0]:
                    raise ValueError('Seleccione un empleado activo.')
                if anterior:
                    cur.execute('SELECT empleado_id, tipo_equipo, fecha_entrega, cantidad FROM higiene_epp WITH (UPDLOCK, HOLDLOCK) WHERE id=?', (anterior,))
                    previo = cur.fetchone()
                    if not previo or previo[0] != eid or previo[1] != equipo or int(previo[3]) != cantidad:
                        raise ValueError('La reposición debe conservar trabajador, equipo y cantidad de la entrega original.')
                    if str(entrega)[:10] < str(previo[2])[:10]:
                        raise ValueError('La reposición no puede ser anterior a la entrega original.')
                    cur.execute('SELECT id FROM higiene_epp WHERE repone_a_id=?', (anterior,))
                    if cur.fetchone():
                        return jsonify(error='Esta entrega ya tiene una reposición registrada.'), 409
                cur.execute('''INSERT INTO higiene_epp
                    (empleado_id, tipo_equipo, area, fecha_entrega, cantidad, estado_equipo,
                     fecha_reposicion_sugerida, entregado_por, observaciones, repone_a_id, motivo_reposicion)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                    (eid, equipo, area, entrega, cantidad, estado, proxima, usuario(), obs, anterior, motivo))
                nuevo = identidad(cur)
                adjuntar(cur, 'EPP', nuevo, archivo)
            return jsonify(success=True, id=nuevo, mensaje='Reposición registrada.' if anterior else 'Entrega registrada.'), 201
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    def campos_riesgo(data):
        campos = [texto(data, 'area', 50), texto(data, 'tipo_riesgo', 100),
                  texto(data, 'descripcion', 4000), texto(data, 'nivel_riesgo', 20),
                  texto(data, 'medidas_preventivas', 4000), texto(data, 'responsable_seguimiento', 100),
                  texto(data, 'estado', 30)]
        if campos[3] not in ('Bajo', 'Medio', 'Alto') or campos[6] not in ('Pendiente', 'En seguimiento', 'Controlado'):
            raise ValueError('Nivel o estado de riesgo inválido.')
        return campos

    @app.route('/api/rrhh/higiene/riesgos', methods=['GET', 'POST'])
    @login_required
    def riesgos_controlados():
        if request.method == 'GET':
            return jsonify(serializar(execute_query('SELECT * FROM higiene_riesgos ORDER BY id DESC', fetchall=True)))
        try:
            campos = campos_riesgo(request.get_json(silent=True) or {})
            with transaccion() as cur:
                cur.execute('''INSERT INTO higiene_riesgos
                    (area, tipo_riesgo, descripcion, nivel_riesgo, medidas_preventivas, responsable_seguimiento, estado)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''', campos)
                nuevo = identidad(cur)
            return jsonify(success=True, id=nuevo), 201
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    @app.route('/api/rrhh/higiene/riesgos/<int:riesgo_id>', methods=['PUT'])
    @login_required
    def editar_riesgo(riesgo_id):
        try:
            campos = campos_riesgo(request.get_json(silent=True) or {})
            with transaccion() as cur:
                cur.execute('''UPDATE higiene_riesgos SET area=?, tipo_riesgo=?, descripcion=?, nivel_riesgo=?,
                    medidas_preventivas=?, responsable_seguimiento=?, estado=? WHERE id=?''', (*campos, riesgo_id))
                if cur.rowcount == 0:
                    return jsonify(error='Riesgo no encontrado.'), 404
            return jsonify(success=True)
        except ValueError as exc:
            return jsonify(error=str(exc)), 400

    @app.route('/api/rrhh/higiene/riesgos/<int:riesgo_id>/seguimiento', methods=['GET', 'POST'])
    @login_required
    def seguimiento_riesgo(riesgo_id):
        if request.method == 'GET':
            return jsonify(serializar(execute_query('SELECT * FROM higiene_riesgo_seguimientos WHERE riesgo_id=? ORDER BY fecha_revision DESC, id DESC', (riesgo_id,), fetchall=True)))
        try:
            data = request.get_json(silent=True) or {}
            dia, obs = fecha(data, 'fecha_revision'), texto(data, 'observaciones', 4000)
            estado = texto(data, 'estado', 30)
            if estado not in ('Pendiente', 'En seguimiento', 'Controlado'):
                raise ValueError('Estado inválido.')
            with transaccion() as cur:
                cur.execute('SELECT fecha_revision FROM higiene_riesgos WITH (UPDLOCK, HOLDLOCK) WHERE id=?', (riesgo_id,))
                row = cur.fetchone()
                if not row:
                    return jsonify(error='Riesgo no encontrado.'), 404
                cur.execute('''INSERT INTO higiene_riesgo_seguimientos
                    (riesgo_id, fecha_revision, observaciones, estado, registrado_por) VALUES (?, ?, ?, ?, ?)''',
                    (riesgo_id, dia, obs, estado, usuario()))
                if row[0] is None or str(dia)[:10] >= str(row[0])[:10]:
                    cur.execute('UPDATE higiene_riesgos SET fecha_revision=?, estado=? WHERE id=?', (dia, estado, riesgo_id))
            return jsonify(success=True), 201
        except ValueError as exc:
            return jsonify(error=str(exc)), 400
