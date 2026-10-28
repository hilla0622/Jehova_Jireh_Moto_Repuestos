"""Ejemplos contables/fiscales 2024-2025. Sin --apply valida y revierte todo.

Usa DB_SERVER y la misma conexión de app.py. No crea presentaciones ante DGI.
No contiene facturas ni constancias reales. Los asientos afectan saldos acumulados
posteriores, como cualquier movimiento histórico, y se identifican DEMO_FISCAL.
"""
import argparse
import json
import re
from calendar import monthrange
from pathlib import Path

import fiscal_service as fiscal

MARK = '[DEMO-FISCAL]'
TABLES = ('negocio_info_tributaria', 'reglas_tributarias',
          'acreditamientos_tributarios', 'declaraciones_ir',
          'declaracion_renglones_detalle', 'declaracion_ajustes_fiscales',
          'declaracion_validaciones', 'declaracion_presentacion_pagos')


def cargar(conn):
    cur = conn.cursor()
    schema = Path(__file__).with_name('database.sql').read_text(encoding='utf-8-sig')
    bloques = re.split(r'^GO\s*$', schema, flags=re.M | re.I)
    for tabla in TABLES:
        bloque = next(b for b in bloques if f'CREATE TABLE [{tabla}]' in b)
        cur.execute(bloque)
    cur.execute('SELECT TOP 1 id FROM usuarios ORDER BY id')
    user = cur.fetchone()
    if not user:
        raise ValueError('Se necesita al menos un usuario existente.')
    uid = user[0]
    # Cuenta separada del IVA para los pagos a cuenta del IR.
    cur.execute("""IF NOT EXISTS (SELECT 1 FROM cuentas_contables WHERE codigo='1.1.06')
        INSERT INTO cuentas_contables (codigo,nombre,clasificacion,naturaleza,descripcion,activo)
        VALUES ('1.1.06','Anticipos y retenciones IR a favor','Activo corriente','Deudora',
                'Pagos a cuenta del impuesto sobre la renta',1)""")
    cur.execute('SELECT id,codigo FROM cuentas_contables')
    cuentas = {r.codigo: r.id for r in cur.fetchall()}
    insertados = {'asientos': 0, 'acreditamientos': 0, 'borradores': 0}

    def asiento(fecha, referencia, lineas):
        if sum(d for _, d, _ in lineas) != sum(h for _, _, h in lineas):
            raise ValueError(f'Asiento no balanceado: {referencia}')
        concepto = f'{MARK} {referencia} - muestra sin validez oficial'
        cur.execute('SELECT id FROM asientos_contables WITH (UPDLOCK,HOLDLOCK) WHERE concepto=?', (concepto,))
        if cur.fetchone():
            return
        cur.execute("""INSERT INTO asientos_contables (fecha,concepto,modulo_origen,usuario_id)
            OUTPUT INSERTED.id VALUES (?,?,'DEMO_FISCAL',?)""", (fecha, concepto, uid))
        aid = cur.fetchone()[0]
        for codigo, debe, haber in lineas:
            cur.execute('INSERT INTO movimientos_contables (asiento_id,cuenta_id,debe,haber) VALUES (?,?,?,?)',
                        (aid, cuentas[codigo], debe, haber))
        insertados['asientos'] += 1

    def acreditamiento(anio, mes, tipo, base, pct, importe, sufijo):
        ref = f'DEMO-IR-{anio}-{mes:02}-{sufijo}'
        cur.execute('SELECT id FROM acreditamientos_tributarios WITH (UPDLOCK,HOLDLOCK) WHERE numero_referencia=?', (ref,))
        if cur.fetchone():
            return
        fiscal.guardar_acreditamiento(cur, {
            'tipo': tipo, 'concepto': f'{MARK} {ref} - constancia ficticia',
            'ejercicio_fiscal': anio, 'periodo_mes': mes,
            'fecha': f'{anio}-{mes:02}-{monthrange(anio,mes)[1]}',
            'numero_referencia': ref, 'monto_base': base,
            'porcentaje_aplicado': pct, 'importe_total': importe,
            'agente_retenedor_nombre': 'Agente de demostración (ficticio)',
        }, uid)
        insertados['acreditamientos'] += 1

    asiento('2024-01-01', 'Apertura 2024', [
        ('1.1.02',100000,0), ('1.1.04',100000,0),
        ('1.2.01',60000,0), ('3.1.01',0,260000)])
    for anio, ventas, taller, costo, sueldos, alquiler, energia, depreciacion, publicidad, ret in [
        (2024,80000,10000,45000,15000,5000,3000,1000,1000,300),
        (2025,100000,15000,60000,25000,6000,5000,2000,2000,400),
    ]:
        for mes in range(1,13):
            periodo = f'{anio}-{mes:02}'
            fecha = f'{periodo}-{monthrange(anio,mes)[1]}'
            ingreso = ventas + taller
            asiento(fecha, f'{periodo} ventas y taller', [
                ('1.1.02',ingreso-ret,0), ('1.1.06',ret,0),
                ('4.1.01',0,ventas), ('4.1.02',0,taller)])
            asiento(fecha, f'{periodo} compra de repuestos', [('1.1.04',costo,0),('1.1.02',0,costo)])
            asiento(fecha, f'{periodo} costo de ventas', [('5.1.01',costo,0),('1.1.04',0,costo)])
            gastos = [('6.1.01',sueldos,0),('6.1.02',alquiler,0),
                      ('6.1.03',energia,0),('6.1.06',publicidad,0),
                      ('6.1.09',depreciacion,0),('1.2.03',0,depreciacion),
                      ('1.1.02',0,sueldos+alquiler+energia+publicidad)]
            asiento(fecha, f'{periodo} gastos', gastos)
            anticipo = ingreso // 100
            asiento(fecha, f'{periodo} anticipo IR', [('1.1.06',anticipo,0),('1.1.02',0,anticipo)])
            acreditamiento(anio,mes,'RETENCION_SUFRIDA',ret*50,2,ret,'RET')
            acreditamiento(anio,mes,'ANTICIPO_PAGADO',ingreso,1,anticipo,'ANT')

    resultados = {}
    for anio in (2024,2025):
        sim = fiscal.preparar_declaracion_desde_contabilidad(cur, {'anio': anio})
        if not sim['balance']['balance_cuadrado']:
            raise ValueError(f'El balance {anio} no cuadra; no se aplicará la carga.')
        cur.execute("SELECT id FROM declaraciones_ir WHERE ejercicio_fiscal=? AND observaciones LIKE ?",
                    (anio, '[[]DEMO-FISCAL]%'))
        if not cur.fetchone():
            fiscal.guardar_declaracion_completa(cur, sim, uid)
            insertados['borradores'] += 1
        resultados[anio] = {'ingresos': sim['resultados']['total_ingresos_brutos'],
                            'renta': sim['calculo_ir']['renta_neta_gravable'],
                            'tasa_ir': sim['calculo_ir']['tasa_ir'], **sim['liquidacion']}
    return {'marca': MARK, 'insertados': insertados, 'ejercicios': resultados}


def main():
    from app import get_db_connection
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    conn = get_db_connection()
    conn.autocommit = False
    try:
        resultado = cargar(conn)
        if args.apply:
            conn.commit()
        else:
            conn.rollback()
        resultado['aplicado'] = args.apply
        print(json.dumps(resultado, ensure_ascii=False, indent=2))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
