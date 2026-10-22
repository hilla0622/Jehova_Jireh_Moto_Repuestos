"""Cálculos de flujo y conciliación, independientes de Flask y de SQL Server.

El mayor es la fuente de los importes. La clasificación nunca crea efectivo.
Los casos ambiguos se presentan como pendientes, sin forzar la cuadratura.
"""
from collections import defaultdict
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import hashlib
import json

CENTAVO = Decimal('0.01')
CERO = Decimal('0.00')
ACTIVIDADES = ('Operacion', 'Inversion', 'Financiamiento')
RESULTADOS = ('Ingresos', 'Costo', 'Gasto')


def dinero(value):
    try:
        n = Decimal(str(value if value is not None else 0))
        if not n.is_finite() or abs(n) >= Decimal('100000000000000'):
            raise ValueError('Importe fuera de rango.')
        if n != n.quantize(CENTAVO, rounding=ROUND_HALF_UP):
            raise ValueError('Los importes deben tener como máximo dos decimales.')
        return n.quantize(CENTAVO)
    except (InvalidOperation, TypeError):
        raise ValueError('Importe monetario inválido.') from None


def fecha(value):
    try:
        return date.fromisoformat(str(value)[:10]).isoformat()
    except (TypeError, ValueError):
        raise ValueError('Fecha inválida; utilice AAAA-MM-DD.') from None


def serializable(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: serializable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [serializable(v) for v in value]
    return value


def huella(value):
    return hashlib.sha256(json.dumps(serializable(value), sort_keys=True,
                                     ensure_ascii=False).encode('utf-8')).hexdigest()


def validar_distribucion(movs, partes):
    if not isinstance(partes, list) or any(not isinstance(p, dict) for p in partes):
        raise ValueError('La distribución debe ser una lista de actividades e importes.')
    entradas = sum((dinero(m['debe']) for m in movs if m['es_efectivo']), CERO)
    salidas = sum((dinero(m['haber']) for m in movs if m['es_efectivo']), CERO)
    result = []
    for p in partes:
        if p.get('actividad') not in ACTIVIDADES:
            raise ValueError('Actividad de flujo inválida.')
        importe = dinero(p.get('importe'))
        if not importe:
            raise ValueError('Cada distribución debe tener un importe distinto de cero.')
        result.append({'actividad': p['actividad'], 'importe': importe})
    positivos = sum((p['importe'] for p in result if p['importe'] > 0), CERO)
    negativos = -sum((p['importe'] for p in result if p['importe'] < 0), CERO)
    if positivos > entradas or negativos > salidas or positivos - negativos != entradas - salidas:
        raise ValueError('La distribución debe coincidir con el efectivo del asiento, sin exceder sus cobros o pagos.')
    if not entradas and not salidas:
        raise ValueError('El asiento no tiene movimiento de efectivo.')
    return result


def clasificar(movs, regla=None, manual=None):
    caja = [m for m in movs if m['es_efectivo']]
    contra = [m for m in movs if not m['es_efectivo']]
    neto = sum((m['debe'] - m['haber'] for m in caja), CERO)
    if not caja or not contra:
        return [], None  # Sin efectivo o transferencia pura.
    if manual is not None:
        try:
            return validar_distribucion(movs, manual), None
        except ValueError as e:
            return [], str(e)
    if any(m['debe'] for m in caja) and any(m['haber'] for m in caja):
        return [], 'Asiento con cobros y pagos simultáneos; distribuya el efectivo y excluya las transferencias internas.'
    if regla in ACTIVIDADES:
        return [{'actividad': regla, 'importe': neto}] if neto else [], None
    # Solo las contrapartidas del sentido del pago/cobro pueden clasificarlo.
    candidatos = [m for m in contra if (m['haber'] - m['debe']) * neto > 0]
    cats = {m['flujo_categoria'] for m in candidatos}
    if not cats or not cats.issubset(set(ACTIVIDADES)):
        return [], 'Configure las etiquetas de las cuentas que intervienen en el cobro o pago.'
    if len(cats) == 1:
        return [{'actividad': cats.pop(), 'importe': neto}], None
    # Una venta de activo con ganancia no es un cobro operativo por la ganancia.
    if any(m['clasificacion'] in RESULTADOS for m in candidatos) and 'Inversion' in cats:
        return [], 'Operación de inversión con resultado; revise la distribución del cobro/pago completo.'
    efectos = [m['haber'] - m['debe'] for m in contra]
    if all(e * neto >= 0 for e in efectos) and sum(efectos, CERO) == neto:
        return [{'actividad': m['flujo_categoria'], 'importe': m['haber'] - m['debe']}
                for m in contra if m['haber'] != m['debe']], None
    return [], 'Transacción mixta: el contador debe distribuir el efectivo entre actividades.'


ORDEN_RUBROS_OPERACION = {
    'Cobros en efectivo por ventas de bienes y prestación de servicios': 1,
    'Otros cobros de operación': 2,
    'Pagos en efectivo a proveedores por mercancías y suministros': 3,
    'Pagos en efectivo a y por cuenta de los empleados (Nómina)': 4,
    'Pagos de tributos, impuestos y retenciones operativas': 5,
    'Pagos por otros gastos operativos y de administración': 6,
    'Otros pagos operativos': 7,
}


def identificar_rubro_operacion(movs, importe):
    contra = [m for m in movs if not m['es_efectivo']]
    codigos = {m['codigo'] for m in contra}
    clasificaciones = {m['clasificacion'] for m in contra}
    concepto_lower = (movs[0]['concepto'] or '').lower()

    if any(c.startswith('4.') for c in codigos) or any(c.startswith('1.1.03') for c in codigos) or 'Ingresos' in clasificaciones or any(w in concepto_lower for w in ('venta', 'cobro', 'pedido web', 'factura', 'devolucion', 'anulacion')):
        return 'Cobros en efectivo por ventas de bienes y prestación de servicios'

    if any(c.startswith('2.1.01') or c.startswith('1.1.04') for c in codigos) or any(w in concepto_lower for w in ('proveedor', 'compra', 'mercaderia', 'inventario')):
        return 'Pagos en efectivo a proveedores por mercancías y suministros'

    if any(c.startswith('6.1.01') or c.startswith('2.1.04') for c in codigos) or any(w in concepto_lower for w in ('nomina', 'sueldo', 'salario', 'empleado', 'quincena')):
        return 'Pagos en efectivo a y por cuenta de los empleados (Nómina)'

    if any(c.startswith(('2.1.03', '2.1.06', '2.1.07', '2.1.08')) for c in codigos) or any(w in concepto_lower for w in ('impuesto', 'iva', 'inss', 'dgi', 'alcaldia', 'retencion')):
        return 'Pagos de tributos, impuestos y retenciones operativas'

    if any(c.startswith('6.') for c in codigos) or 'Gasto' in clasificaciones or any(w in concepto_lower for w in ('alquiler', 'publicidad', 'servicio', 'luz', 'agua', 'internet', 'comision')):
        return 'Pagos por otros gastos operativos y de administración'

    return 'Otros cobros de operación' if importe >= 0 else 'Otros pagos operativos'


def calcular_flujo(movimientos, inicio, fin, metodo, reglas=None, distribuciones=None, ajustes=None):
    inicio, fin = fecha(inicio), fecha(fin)
    if inicio > fin:
        raise ValueError('La fecha inicial no puede ser posterior a la final.')
    if metodo not in ('Directo', 'Indirecto'):
        raise ValueError('Método inválido.')
    reglas, distribuciones, ajustes = reglas or {}, distribuciones or {}, ajustes or {}
    asientos, saldos = defaultdict(list), {}
    configuracion_pendiente = {}
    saldo_inicial = CERO
    for raw in movimientos:
        m = dict(raw, debe=dinero(raw['debe']), haber=dinero(raw['haber']))
        f = fecha(m['fecha'])
        if f > fin:
            continue
        if m['codigo'].startswith(('1.1.01', '1.1.02')) and not m['es_efectivo']:
            configuracion_pendiente[m['cuenta_id']] = {'asiento_id': m['asiento_id'],
                'motivo': f"Configure {m['codigo']} como efectivo y equivalentes antes de emitir el corte."}
        if m['es_efectivo']:
            item = saldos.setdefault(m['cuenta_id'], {'codigo': m['codigo'], 'nombre': m['nombre'], 'saldo': CERO})
            item['saldo'] += m['debe'] - m['haber']
            if f < inicio:
                saldo_inicial += m['debe'] - m['haber']
        if f >= inicio:
            asientos[m['asiento_id']].append(m)
    listas = {c: [] for c in ACTIVIDADES}
    operaciones_raw = []
    pendientes, detalle_ajustes, capital_raw, no_monetarias = list(configuracion_pendiente.values()), [], [], []
    utilidad = CERO
    for aid, movs in asientos.items():
        if sum((m['debe'] - m['haber'] for m in movs), CERO):
            pendientes.append({'asiento_id': aid, 'motivo': 'Asiento descuadrado en el mayor.'})
        partes, error = clasificar(movs, reglas.get(movs[0]['modulo_origen']), distribuciones.get(aid))
        if error:
            pendientes.append({'asiento_id': aid, 'motivo': error})
        for p in partes:
            item_flujo = {'asiento_id': aid, 'fecha': movs[0]['fecha'], 'concepto': movs[0]['concepto'],
                          'importe': p['importe'], 'tipo': 'Entrada' if p['importe'] > 0 else 'Salida'}
            if p['actividad'] == 'Operacion':
                rubro = identificar_rubro_operacion(movs, p['importe'])
                operaciones_raw.append((rubro, item_flujo))
            else:
                listas[p['actividad']].append(item_flujo)
        if not any(m['es_efectivo'] for m in movs):
            no_monetarias.append({'asiento_id': aid, 'concepto': movs[0]['concepto']})
        es_no_operativo = bool(partes) and all(p['actividad'] != 'Operacion' for p in partes)
        resultados_asiento = [m for m in movs if m['clasificacion'] in RESULTADOS]
        sin_caja = not any(m['es_efectivo'] for m in movs)
        todos_no_monetarios = bool(resultados_asiento) and all(m.get('ajuste_no_monetario') for m in resultados_asiento)
        inv_fin_real = any(
            m['flujo_categoria'] in ('Inversion', 'Financiamiento') and 'contraactivo' not in m.get('clasificacion', '').lower()
            for m in movs
        )
        excluir_wk = sin_caja and (
            todos_no_monetarios
            or (inv_fin_real and not any(m['clasificacion'] in RESULTADOS for m in movs))
            or (not resultados_asiento and not any(m['flujo_categoria'] == 'Operacion' for m in movs))
        )
        # Ajustes identificables, nunca una diferencia residual para forzar el saldo.
        for m in movs:
            neto = m['debe'] - m['haber']
            es_resultado = m['clasificacion'] in RESULTADOS
            if es_resultado:
                utilidad -= neto
            es_wk = (not m['es_efectivo'] and m['flujo_categoria'] == 'Operacion'
                     and m['clasificacion'] in ('Activo corriente', 'Pasivo corriente'))
            automatico = CERO
            if es_resultado and (m.get('ajuste_no_monetario') or es_no_operativo or (sin_caja and inv_fin_real)):
                automatico = neto
            elif es_wk and not es_no_operativo and not excluir_wk:
                automatico = -neto
            ajuste = ajustes.get(m['movimiento_id'])
            valor = dinero(ajuste['importe']) if ajuste else automatico
            if valor or ajuste:
                concepto = f"{m['codigo']} {m['nombre']} (asiento {aid})"
                if es_wk and not ajuste:
                    capital_raw.append({
                        'cuenta_id': m['cuenta_id'],
                        'codigo': m['codigo'],
                        'cuenta': m['nombre'],
                        'tipo': m['clasificacion'],
                        'asiento_id': aid,
                        'fecha': m['fecha'],
                        'variacion': neto if m['clasificacion'] == 'Activo corriente' else -neto,
                        'impacto': valor,
                        'descripcion': concepto
                    })
                else:
                    detalle_ajustes.append({'movimiento_id': m['movimiento_id'], 'concepto': concepto,
                                           'importe': valor, 'efecto': 'Suma_a_Utilidad' if valor >= 0 else 'Resta_a_Utilidad',
                                           'justificacion': ajuste['motivo'] if ajuste else 'Ajuste automático identificado en el mayor.',
                                           'manual': bool(ajuste)})
    # Consolidar capital de trabajo por cuenta para presentación oficial, conservando auditoría de asientos
    capital_dict = {}
    for c in capital_raw:
        cid = c['cuenta_id']
        if cid not in capital_dict:
            capital_dict[cid] = {
                'cuenta_id': cid,
                'codigo': c['codigo'],
                'cuenta': c['cuenta'],
                'tipo': c['tipo'],
                'variacion': CERO,
                'impacto': CERO,
                'descripcion': f"{c['codigo']} {c['cuenta']}",
                'movimientos': []
            }
        capital_dict[cid]['variacion'] += c['variacion']
        capital_dict[cid]['impacto'] += c['impacto']
        capital_dict[cid]['movimientos'].append({
            'asiento_id': c['asiento_id'],
            'fecha': c['fecha'],
            'descripcion': c['descripcion'],
            'variacion': c['variacion'],
            'impacto': c['impacto']
        })
    capital = sorted(capital_dict.values(), key=lambda x: x['codigo'])

    # Consolidar actividades de operación por rubro oficial de NIC 7 (agrupación de cobros y pagos brutos)
    operaciones_dict = {}
    for rubro, item in operaciones_raw:
        if rubro not in operaciones_dict:
            operaciones_dict[rubro] = {
                'concepto': rubro,
                'importe': CERO,
                'tipo': 'Entrada' if item['importe'] >= 0 else 'Salida',
                'movimientos': []
            }
        operaciones_dict[rubro]['importe'] += item['importe']
        operaciones_dict[rubro]['movimientos'].append(item)
        operaciones_dict[rubro]['tipo'] = 'Entrada' if operaciones_dict[rubro]['importe'] >= 0 else 'Salida'

    listas['Operacion'] = sorted(
        operaciones_dict.values(),
        key=lambda x: (0 if x['tipo'] == 'Entrada' else 1, ORDEN_RUBROS_OPERACION.get(x['concepto'], 99))
    )

    netos = {c: sum((i['importe'] for i in listas[c]), CERO) for c in ACTIVIDADES}
    total_ajustes = sum((a['importe'] for a in detalle_ajustes), CERO) + sum((c['impacto'] for c in capital), CERO)
    operacion_indirecto = utilidad + total_ajustes
    diferencia_metodos = operacion_indirecto - netos['Operacion']
    if metodo == 'Indirecto':
        netos['Operacion'] = operacion_indirecto
    variacion = sum(netos.values(), CERO)
    saldo_balance = sum((s['saldo'] for s in saldos.values()), CERO)
    diferencia = saldo_inicial + variacion - saldo_balance
    result = dict(metodo=metodo, periodo={'start': inicio, 'end': fin}, saldo_inicial=saldo_inicial,
                  actividades_operacion=listas['Operacion'] if metodo == 'Directo' else [],
                  actividades_inversion=listas['Inversion'], actividades_financiamiento=listas['Financiamiento'],
                  flujo_neto_operacion=netos['Operacion'], flujo_neto_inversion=netos['Inversion'],
                  flujo_neto_financiamiento=netos['Financiamiento'], variacion_neta_efectivo=variacion,
                  saldo_final_calculado=saldo_inicial + variacion, saldo_final_balance=saldo_balance,
                  diferencia_cuadratura=diferencia, esta_cuadrado=diferencia == 0,
                  diferencia_entre_metodos=diferencia_metodos, pendientes_clasificacion=pendientes,
                  operaciones_sin_efectivo=no_monetarias, desglose_efectivo=list(saldos.values()),
                  puede_guardar=not pendientes and diferencia == 0 and (metodo == 'Directo' or diferencia_metodos == 0),
                  indirecto_data={'utilidad_neta': utilidad, 'ajustes_no_monetarios': detalle_ajustes,
                                  'cambios_capital_trabajo': capital, 'total_ajustes': total_ajustes} if metodo == 'Indirecto' else None)
    result = serializable(result)
    result['revision'] = huella({'reporte': result, 'mayor': movimientos, 'reglas': reglas,
                                'distribuciones': distribuciones, 'ajustes': ajustes})
    return result


TIPOS_PARTIDA = {'Deposito en Transito': ('Banco', 'Suma'), 'Cheque en Transito': ('Banco', 'Resta'),
                'Nota de Credito': ('Libros', 'Suma'), 'Nota de Debito': ('Libros', 'Resta'),
                'Error en Libros': ('Libros', None)}


def calcular_conciliacion(libros, banco, partidas, corte):
    libros, banco = dinero(libros), dinero(banco)
    ajuste_libros, ajuste_banco = CERO, CERO
    for p in partidas:
        if p.get('tipo_partida') not in TIPOS_PARTIDA:
            raise ValueError('Tipo de partida inválido.')
        lado, signo = TIPOS_PARTIDA[p['tipo_partida']]
        signo = signo or p.get('efecto_en_saldo')
        if signo not in ('Suma', 'Resta'):
            raise ValueError('Seleccione suma o resta para el error en libros.')
        monto = dinero(p.get('monto'))
        if monto <= 0 or fecha(p.get('fecha')) > fecha(corte):
            raise ValueError('La partida requiere monto positivo y fecha no posterior al corte.')
        if not str(p.get('numero_documento_referencia', '')).strip() or not str(p.get('descripcion', '')).strip():
            raise ValueError('Cada partida requiere referencia y descripción.')
        if not isinstance(p.get('esta_conciliada', False), (bool, int)) or p.get('esta_conciliada', False) not in (False, True, 0, 1):
            raise ValueError('Estado de partida inválido.')
        if p.get('esta_conciliada'):
            continue
        efecto = monto if signo == 'Suma' else -monto
        if lado == 'Libros':
            ajuste_libros += efecto
        else:
            ajuste_banco += efecto
    diferencia = banco + ajuste_banco - libros - ajuste_libros
    # Papel de trabajo aritmético del banco a libros (mismos ajustes, otra presentación).
    puente = banco + ajuste_banco - ajuste_libros
    return serializable(dict(saldo_segun_libros=libros, saldo_segun_banco=banco,
                             saldo_libros_ajustado=libros + ajuste_libros,
                             saldo_banco_ajustado=banco + ajuste_banco, diferencia=diferencia,
                             saldo_en_conciliacion=puente,
                             estado='Conciliada' if diferencia == 0 else 'Borrador'))
