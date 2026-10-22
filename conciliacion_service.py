"""Cotejo bancario: evidencia de movimientos, independiente de la base de datos."""
from flujo_service import CERO, dinero, fecha, serializable


def validar_extracto(extracto, movimientos_empresa, partidas, corte, saldo_banco):
    """Valida vínculos uno a uno y clasificaciones sin confiar en totales del cliente.

    None conserva la lectura/guardado de conciliaciones anteriores, por saldos.
    Un extracto incompleto puede guardarse como borrador, nunca como conciliado.
    """
    if extracto is None:
        return None, {'modo': 'saldos', 'sin_revisar': None, 'completo': False}
    if not isinstance(extracto, dict):
        raise ValueError('El estado de cuenta bancario debe ser un objeto.')
    if extracto.get('saldo_inicial') in (None, ''):
        raise ValueError('Ingrese el saldo inicial del estado de cuenta bancario.')
    inicial = dinero(extracto['saldo_inicial'])
    filas, vinculos = extracto.get('movimientos', []), extracto.get('vinculos', [])
    if not isinstance(filas, list) or not isinstance(vinculos, list) or len(filas) > 5000:
        raise ValueError('El extracto admite hasta 5,000 movimientos y una lista de vínculos.')
    banco, empresa = {}, {str(m['movimiento_id']): m for m in movimientos_empresa}
    normalizados, acumulado = [], inicial
    for m in filas:
        if not isinstance(m, dict):
            raise ValueError('Movimiento bancario inválido.')
        uid = str(m.get('uid', ''))
        if not uid or len(uid) > 64 or uid in banco:
            raise ValueError('Cada movimiento bancario necesita un identificador único.')
        dia = fecha(m.get('fecha'))
        if dia[:7] != corte[:7]:
            raise ValueError('Los movimientos del extracto deben pertenecer al mes seleccionado.')
        concepto, referencia = str(m.get('concepto', '')).strip(), str(m.get('referencia', '')).strip()
        if not concepto or len(concepto) > 255 or len(referencia) > 100:
            raise ValueError('Indique un concepto de hasta 255 caracteres y una referencia de hasta 100.')
        retiro, deposito = dinero(m.get('retiro')), dinero(m.get('deposito'))
        if retiro < 0 or deposito < 0 or (retiro > 0) == (deposito > 0):
            raise ValueError('Cada movimiento debe tener un retiro o un depósito positivo, no ambos.')
        row = dict(uid=uid, fecha=dia, concepto=concepto, referencia=referencia,
                   retiro=retiro, deposito=deposito)
        banco[uid] = row
        normalizados.append(row)
        acumulado += deposito - retiro
    usados_banco, usados_empresa, usados_pendientes = set(), set(), set()
    pendientes = {p['uid']: p for p in partidas if p.get('heredada')}
    enlaces = []
    for v in vinculos:
        if not isinstance(v, dict):
            raise ValueError('Vínculo inválido.')
        bid, mid, pid = str(v.get('banco_uid', '')), str(v.get('movimiento_id', '')), str(v.get('partida_uid', ''))
        if bid not in banco or bid in usados_banco or bool(mid) == bool(pid):
            raise ValueError('Seleccione un movimiento bancario disponible y una sola contraparte.')
        if pid:
            p = pendientes.get(pid)
            if not p or pid in usados_pendientes or p['tipo_partida'] not in ('Deposito en Transito', 'Cheque en Transito'):
                raise ValueError('Seleccione un depósito o cheque pendiente de un corte anterior.')
            if not p.get('esta_conciliada'):
                raise ValueError('El pendiente vinculado debe marcarse resuelto con su referencia.')
            importe_empresa = dinero(p['monto']) * (1 if p['tipo_partida'] == 'Deposito en Transito' else -1)
            usados_pendientes.add(pid)
            enlaces.append(dict(banco_uid=bid, partida_uid=pid))
        else:
            if mid not in empresa or mid in usados_empresa:
                raise ValueError('El movimiento de la empresa no existe en este período o ya fue vinculado.')
            importe_empresa = dinero(empresa[mid]['debe']) - dinero(empresa[mid]['haber'])
            usados_empresa.add(mid)
            enlaces.append(dict(banco_uid=bid, movimiento_id=int(mid)))
        if importe_empresa != banco[bid]['deposito'] - banco[bid]['retiro']:
            raise ValueError('Para vincular, el importe y el sentido de entrada o salida deben coincidir.')
        usados_banco.add(bid)
    clasificados_banco, clasificados_empresa = set(), set()
    for p in partidas:
        origen = p.get('origen')
        if not origen or p.get('periodo_origen') != corte[:7] or p.get('esta_conciliada'):
            continue
        oid = str(p.get('origen_id', ''))
        if origen == 'Banco':
            m = banco.get(oid)
            if not m or oid in usados_banco or oid in clasificados_banco:
                raise ValueError('Una diferencia bancaria no puede estar vinculada ni clasificada dos veces.')
            tipo = 'Nota de Credito' if m['deposito'] > 0 else 'Nota de Debito'
            importe = m['deposito'] + m['retiro']
            clasificados_banco.add(oid)
        elif origen == 'Empresa':
            m = empresa.get(oid)
            if not m or oid in usados_empresa or oid in clasificados_empresa:
                raise ValueError('Una diferencia de la empresa no puede estar vinculada ni clasificada dos veces.')
            neto = dinero(m['debe']) - dinero(m['haber'])
            tipo = 'Deposito en Transito' if neto > 0 else 'Cheque en Transito'
            importe = abs(neto)
            clasificados_empresa.add(oid)
        else:
            raise ValueError('Origen de partida inválido.')
        if p['tipo_partida'] != tipo or dinero(p['monto']) != importe or fecha(p['fecha']) != fecha(m['fecha']):
            raise ValueError('La partida debe conservar el tipo, la fecha y el importe del movimiento de origen.')
    # Las notas de meses anteriores pueden resolverse con un asiento registrado este mes.
    for p in partidas:
        mid = str(p.get('movimiento_contable_id') or '')
        if p.get('heredada') and p.get('esta_conciliada') and p['tipo_partida'] in ('Nota de Credito', 'Nota de Debito') and mid in empresa:
            esperado = dinero(p['monto']) * (1 if p['tipo_partida'] == 'Nota de Credito' else -1)
            if mid in usados_empresa or mid in clasificados_empresa or dinero(empresa[mid]['debe']) - dinero(empresa[mid]['haber']) != esperado:
                raise ValueError('El asiento de resolución debe coincidir con la nota y estar disponible.')
            clasificados_empresa.add(mid)
    faltan_banco = len(banco) - len(usados_banco) - len(clasificados_banco)
    faltan_empresa = len(empresa) - len(usados_empresa) - len(clasificados_empresa)
    diferencia = acumulado - dinero(saldo_banco)
    datos = dict(saldo_inicial=inicial, movimientos=normalizados, vinculos=enlaces)
    control = dict(modo='movimientos', saldo_final_calculado=acumulado, diferencia_extracto=diferencia,
                   sin_revisar_banco=faltan_banco, sin_revisar_empresa=faltan_empresa,
                   sin_revisar=faltan_banco + faltan_empresa, vinculados=len(enlaces),
                   completo=diferencia == CERO and faltan_banco + faltan_empresa == 0)
    return serializable(datos), serializable(control)
