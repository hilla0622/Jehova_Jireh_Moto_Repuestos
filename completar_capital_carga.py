"""Completa únicamente el capital y cortes derivados de la carga identificada.

Sin --apply verifica y revierte. No altera ventas, compras, costos ni nóminas.
"""
import argparse
from collections import Counter, defaultdict
from decimal import Decimal
import json
from seed_negocio import Carga, VERSION, ROOT, dinero
import fiscal_service as fiscal
from routes_flujo_efectivo import generar
from flujo_service import serializable


def completar(conn):
    cur=conn.cursor()
    cur.execute('SELECT id,fecha_inicio,fecha_fin,resumen FROM cargas_negocio WITH(UPDLOCK,HOLDLOCK) WHERE version=?',VERSION)
    fila=cur.fetchone()
    if not fila:raise ValueError('No existe la carga integral que se pretende completar.')
    resumen=json.loads(fila[3])
    if 'financiacion' in resumen:return dict(ya_completado=True,resumen=resumen)
    m=object.__new__(Carga)
    m.conn,m.cur,m.cid,m.inicio,m.fin=conn,cur,fila[0],fila[1],fila[2]
    m.uid=1;m.registros=[];m.conteos=Counter();m.cambios=[];m.saldos=defaultdict(lambda:Decimal(0))
    cur.execute('SELECT codigo,id FROM cuentas_contables');m.cuentas=dict(cur.fetchall())
    m.asegurar_liquidez(aporte_confirmado=Decimal('300000'))
    m.normalizar_textos()
    cur.execute('''SELECT f.id,f.fecha_inicio,f.fecha_fin FROM estados_flujo_efectivo f JOIN carga_negocio_registros r
        ON r.tabla='estados_flujo_efectivo' AND r.registro_id=f.id WHERE r.carga_id=? AND f.estado='Borrador' ''',m.cid)
    for fid,inicio,fin in list(cur.fetchall()):
        reporte=generar(cur,dict(start=inicio.isoformat(),end=fin.isoformat(),metodo='Directo'))
        if not reporte['puede_guardar']:raise ValueError('El corte de flujo revisado no cuadra.')
        campos={'saldo_inicial_efectivo':'saldo_inicial','flujo_neto_operacion':'flujo_neto_operacion',
            'flujo_neto_inversion':'flujo_neto_inversion','flujo_neto_financiamiento':'flujo_neto_financiamiento',
            'variacion_neta_efectivo':'variacion_neta_efectivo','saldo_final_calculado':'saldo_final_calculado',
            'saldo_final_balance_general':'saldo_final_balance'}
        cur.execute('SELECT '+','.join(campos)+' FROM estados_flujo_efectivo WHERE id=?',fid)
        for (campo,origen),antes in zip(campos.items(),cur.fetchone()):
            m.cambiar('estados_flujo_efectivo',fid,campo,antes,dinero(reporte[origen]))
        for actividad,clave in [('Operacion','actividades_operacion'),('Inversion','actividades_inversion'),('Financiamiento','actividades_financiamiento')]:
            for orden,linea in enumerate(reporte[clave],1):
                cur.execute('''SELECT id,importe FROM estado_flujo_efectivo_detalle WHERE flujo_id=?
                    AND actividad=? AND concepto=? AND tipo_movimiento=?''',fid,actividad,linea['concepto'][:255],linea['tipo'])
                existente=cur.fetchone()
                if existente:m.cambiar('estado_flujo_efectivo_detalle',existente[0],'importe',existente[1],dinero(linea['importe']))
                else:m.insertar('estado_flujo_efectivo_detalle',flujo_id=fid,actividad=actividad,concepto=linea['concepto'][:255],
                    tipo_movimiento=linea['tipo'],importe=dinero(linea['importe']),orden_presentacion=orden)
        m.insertar('flujo_eventos',tipo='corte',clave=str(fid),contenido=json.dumps(serializable(reporte),ensure_ascii=False),
            motivo='Actualización del corte por aporte inicial para capital de trabajo',usuario_id=m.uid)
    cur.execute('''SELECT d.id,d.ejercicio_fiscal FROM declaraciones_ir d JOIN carga_negocio_registros r
        ON r.tabla='declaraciones_ir' AND r.registro_id=d.id WHERE r.carga_id=? AND d.estado='Borrador' ''',m.cid)
    for did,anio in list(cur.fetchall()):
        sim=fiscal.preparar_declaracion_desde_contabilidad(cur,{'anio':anio})
        if not sim['balance']['balance_cuadrado']:raise ValueError('Balance fiscal no cuadra.')
        for renglon in sim['balance']['renglones']:
            cur.execute('''SELECT id,importe_base_contable,importe_declarado FROM declaracion_renglones_detalle
                WHERE declaracion_id=? AND seccion='BALANCE_GENERAL' AND numero_renglon=?''',did,renglon['renglon'])
            row=cur.fetchone()
            if not row:raise ValueError('Falta un renglón del balance en el borrador de la carga.')
            m.cambiar('declaracion_renglones_detalle',row[0],'importe_base_contable',row[1],dinero(renglon['importe']))
            m.cambiar('declaracion_renglones_detalle',row[0],'importe_declarado',row[2],dinero(renglon['importe']))
    # Actualizar también los borradores de conciliación propios de la carga; no se crea extracto.
    cur.execute('''SELECT c.id,c.fecha_corte FROM conciliaciones_bancarias c JOIN carga_negocio_registros r
        ON r.tabla='conciliaciones_bancarias' AND r.registro_id=c.id WHERE r.carga_id=? AND c.estado='Borrador' ''',m.cid)
    for rid,fin in list(cur.fetchall()):
        cur.execute('''SELECT SUM(v.debe-v.haber) FROM movimientos_contables v JOIN asientos_contables a ON a.id=v.asiento_id
            WHERE v.cuenta_id=? AND a.fecha<=?''',m.cuentas['1.1.02'],fin)
        saldo=cur.fetchone()[0]
        cur.execute('SELECT saldo_segun_libros,diferencia FROM conciliaciones_bancarias WHERE id=?',rid)
        libros,diferencia=cur.fetchone()
        m.cambiar('conciliaciones_bancarias',rid,'saldo_segun_libros',libros,saldo)
        m.cambiar('conciliaciones_bancarias',rid,'diferencia',diferencia,saldo)
    cur.executemany('INSERT INTO carga_negocio_registros(carga_id,tabla,registro_id) VALUES(?,?,?)',m.registros)
    if m.cambios:cur.executemany('INSERT INTO carga_negocio_cambios(carga_id,tabla,registro_id,campo,antes,despues) VALUES(?,?,?,?,?,?)',m.cambios)
    for tabla,cantidad in m.conteos.items():resumen['insertados'][tabla]=resumen['insertados'].get(tabla,0)+cantidad
    resumen['normalizaciones']+=len(m.cambios)
    resumen['financiacion']=m.financiacion
    cur.execute('''SELECT MIN(saldo) FROM (SELECT SUM(SUM(v.debe-v.haber)) OVER(ORDER BY a.fecha) saldo
        FROM movimientos_contables v JOIN asientos_contables a ON a.id=v.asiento_id
        WHERE v.cuenta_id=? AND a.fecha<=? GROUP BY a.fecha) s''',m.cuentas['1.1.02'],m.fin)
    minimo=cur.fetchone()[0]
    if minimo<20000:raise ValueError('La financiación no cubre la reserva bancaria mínima.')
    resumen['comprobaciones']['liquidez_bancaria_minima']=str(minimo)
    cur.execute('UPDATE cargas_negocio SET resumen=? WHERE id=?',json.dumps(resumen,ensure_ascii=False),m.cid)
    return dict(ya_completado=False,resumen=resumen)


if __name__=='__main__':
    from app import get_db_connection
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--apply',action='store_true');args=p.parse_args()
    conn=get_db_connection();conn.autocommit=False
    try:
        resultado=completar(conn)
        if args.apply:
            conn.commit()
            (ROOT/'output/carga_negocio/resultado.json').write_text(json.dumps(resultado['resumen'],ensure_ascii=False,indent=2),encoding='utf-8')
        else:conn.rollback()
        print(json.dumps(dict(ya_completado=resultado['ya_completado'],financiacion=resultado['resumen']['financiacion'],aplicado=args.apply),ensure_ascii=False,indent=2))
    except Exception:conn.rollback();raise
    finally:conn.close()
