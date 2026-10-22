"""Ejemplo transcrito de las dos imágenes del usuario. Solo datos de prueba."""

# fecha, concepto, entrada, salida. La comisión de la imagen es 1,500, no 10,000.
BANCO = [
    ('02', 'Pago mercadería F-7452', 0, 35000),
    ('05', 'Comisiones bancarias membresía', 0, 1500),
    ('06', 'Pago publicidad factura 4521', 0, 31000),
    ('09', 'Pago factura 8999', 85000, 0),
    ('09', 'Pago factura 9000', 5000, 0),
    ('09', 'Pago factura 9001', 7000, 0),
    ('09', 'Pago factura 9003', 35000, 0),
    ('09', 'Pago factura 9004', 12000, 0),
    ('15', 'Pago sueldos y salarios', 0, 98000),
    ('17', 'Pago impuestos', 0, 36000),
    ('22', 'Pago de teléfono', 0, 4000),
    ('22', 'Pago de luz', 0, 8000),
    ('25', 'Pago factura 9005', 25000, 0),
    ('25', 'Pago factura 9006', 80000, 0),
    ('30', 'Pago sueldos y salarios', 0, 78000),
]
EMPRESA = [
    ('01', 'Croquetas S.A. / enero / F-7452', 0, 35000),
    ('06', 'Publicidad de ventas / enero / F-4521', 0, 31000),
    ('09', 'Cobranza cliente 0005 - documento 8999', 85000, 0),
    ('09', 'Cobranza cliente 0074 - documento 9001', 7000, 0),
    ('09', 'Cobranza cliente 0032 - documento 9002', 16000, 0),
    ('09', 'Cobranza cliente 0001 - documento 9003', 35000, 0),
    ('09', 'Cobranza cliente 0020 - documento 9004', 12000, 0),
    ('15', 'Pago nómina y sueldos quincena 1 enero', 0, 98000),
    ('17', 'Impuestos federales diciembre 2018', 0, 36000),
    ('20', 'Préstamo a trabajador / cheque 002785', 0, 20000),
    ('22', 'Servicio de telefonía enero', 0, 4000),
    ('22', 'Suministro de electricidad enero', 0, 8000),
    ('25', 'Cobranza cliente 0031 - documento 9005', 25000, 0),
    ('25', 'Cobranza cliente 0032 - documento 9006', 80000, 0),
    ('30', 'Pago nómina y sueldos quincena 2 enero', 0, 78000),
]


def ejemplo(periodo='2019-01'):
    banco = [dict(uid=f'b{i}', fecha=f'{periodo}-{dia}', concepto=concepto, referencia=f'B-{i}', deposito=d, retiro=h)
             for i, (dia, concepto, d, h) in enumerate(BANCO)]
    empresa = [dict(movimiento_id=i + 1, asiento_id=i + 1, fecha=f'{periodo}-{dia}', concepto=concepto, debe=d, haber=h)
               for i, (dia, concepto, d, h) in enumerate(EMPRESA)]
    vinculos = []
    for b in banco:
        for m in empresa:
            if b['deposito'] == m['debe'] and b['retiro'] == m['haber']:
                vinculos.append(dict(banco_uid=b['uid'], movimiento_id=m['movimiento_id']))
    partidas = []
    for lado, m, tipo in [('Banco', banco[1], 'Nota de Debito'), ('Banco', banco[4], 'Nota de Credito'),
                          ('Empresa', empresa[4], 'Deposito en Transito'), ('Empresa', empresa[9], 'Cheque en Transito')]:
        monto = m.get('deposito', m.get('debe', 0)) + m.get('retiro', m.get('haber', 0))
        partidas.append(dict(uid=f'p{len(partidas)}', tipo_partida=tipo, fecha=m['fecha'],
            numero_documento_referencia=m.get('referencia', f"M-{m.get('movimiento_id')}"), descripcion=m['concepto'],
            monto=monto, efecto_en_saldo='Suma' if tipo in ('Nota de Credito', 'Deposito en Transito') else 'Resta',
            esta_conciliada=False, origen=lado, origen_id=m.get('uid', str(m.get('movimiento_id'))), periodo_origen=periodo))
    return dict(saldo_inicial=78000, movimientos=banco, vinculos=vinculos), empresa, partidas
