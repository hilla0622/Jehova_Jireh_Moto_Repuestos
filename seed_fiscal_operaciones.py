"""Respaldo operativo DEMO 2024/2025. Sin --apply, revierte toda la carga.

Convierte el escenario seed_fiscal_demo en operaciones trazables. Solo reemplaza
movimientos de los asientos marcados del escenario; no modifica operaciones ajenas.
"""
import argparse
from calendar import monthrange
from collections import Counter
from decimal import Decimal
import json
from pathlib import Path

import fiscal_service as fiscal
from calculos_rrhh import calcular_nomina_empleado

MARK = '[DEMO-FISCAL]'
VERSION = 'OPERACIONES-V1'
PARAMETROS = {'INSS_LABORAL': 7, 'INSS_PATRONAL': 21.5,
              'INATEC_PATRONAL': 2, 'VACACIONES_MES': 2.5, 'AGUINALDO_PROV': 100 / 12}


def cargar(conn):
    cur = conn.cursor()
    cur.execute("""IF OBJECT_ID('demo_fiscal_origenes','U') IS NULL
        CREATE TABLE demo_fiscal_origenes (
            clave VARCHAR(100) PRIMARY KEY, tabla_origen VARCHAR(50) NOT NULL,
            documento_id INT NULL, asiento_id INT NULL,
            fecha DATE NOT NULL, importe DECIMAL(18,2) NOT NULL,
            detalle NVARCHAR(MAX) NOT NULL,
            CONSTRAINT fk_demo_fiscal_asiento FOREIGN KEY(asiento_id) REFERENCES asientos_contables(id)
        )""")
    cur.execute('SELECT clave FROM demo_fiscal_origenes WITH (UPDLOCK,HOLDLOCK) WHERE clave=?',(VERSION,))
    if cur.fetchone():
        return verificar(conn, {})
    # Crear el escenario inicial si aún no existe. Después se transforma en esta transacción.
    from seed_fiscal_demo import cargar as cargar_base
    cargar_base(conn)
    cur.execute("""SELECT id FROM declaraciones_ir WHERE ejercicio_fiscal IN (2024,2025)
        AND observaciones LIKE '[[]DEMO-FISCAL]%' AND estado <> 'Borrador'""")
    if cur.fetchone():
        raise ValueError('Existe una declaración DEMO aprobada/presentada. No se reemplazarán sus fuentes.')
    cur.execute('SELECT TOP 1 id FROM usuarios ORDER BY id'); uid=cur.fetchone()[0]
    cur.execute('SELECT codigo,id FROM cuentas_contables'); cuentas={r[0]:r[1] for r in cur.fetchall()}
    counts=Counter()

    def insertar(tabla, valores):
        # Los identificadores vienen exclusivamente de constantes de este script.
        cols=','.join(f'[{k}]' for k in valores)
        cur.execute(f"INSERT INTO [{tabla}] ({cols}) OUTPUT INSERTED.id VALUES ({','.join('?' for _ in valores)})",
                    tuple(valores.values()))
        counts[tabla]+=1
        return int(cur.fetchone()[0])

    def origen(clave, tabla, doc, fecha, importe=0, asiento=None, **detalle):
        cur.execute('INSERT INTO demo_fiscal_origenes VALUES (?,?,?,?,?,?,?)',
                    (clave,tabla,doc,asiento,fecha,importe,json.dumps(detalle,ensure_ascii=False,default=str)))

    def asiento(clave, fecha, lineas, tabla, doc, original=None):
        lineas=[(cod,Decimal(str(d)),Decimal(str(h))) for cod,d,h in lineas if d or h]
        if sum(d for _,d,_ in lineas) != sum(h for _,_,h in lineas):
            raise ValueError(f'Asiento desbalanceado: {clave}')
        if original:
            concepto=f'{MARK} {original} - muestra sin validez oficial'
            cur.execute("SELECT id FROM asientos_contables WITH (UPDLOCK,HOLDLOCK) WHERE concepto=? AND modulo_origen='DEMO_FISCAL'",(concepto,))
            r=cur.fetchone()
            if not r:
                raise ValueError(f'No se encontró el asiento DEMO original: {original}')
            aid=int(r[0])
            cur.execute('SELECT c.codigo,m.debe,m.haber FROM movimientos_contables m JOIN cuentas_contables c ON c.id=m.cuenta_id WHERE m.asiento_id=?',(aid,))
            anteriores=[tuple(r) for r in cur.fetchall()]
            origen('ANTES-'+clave,'asientos_contables',aid,fecha,asiento=aid,movimientos=anteriores)
            cur.execute('DELETE FROM movimientos_contables WHERE asiento_id=?',(aid,))
            cur.execute('UPDATE asientos_contables SET referencia_id=?,fecha=? WHERE id=?',(doc,fecha,aid))
        else:
            aid=insertar('asientos_contables',dict(fecha=fecha,concepto=f'{MARK} {clave} - demostración',
                         modulo_origen='DEMO_FISCAL',referencia_id=doc,usuario_id=uid))
        for cod,d,h in lineas:
            insertar('movimientos_contables',dict(asiento_id=aid,cuenta_id=cuentas[cod],debe=d,haber=h))
        origen(clave,tabla,doc,fecha,sum(d for _,d,_ in lineas),aid)
        return aid

    cat=insertar('categorias',dict(nombre='Demostración histórica IR',descripcion=MARK+' Muestras académicas 2024/2025'))
    cliente=insertar('clientes',dict(nombre_completo='Cliente DEMO histórico (ficticio)',
        identificacion='DEMO-CLIENTE-IR',tipo_cliente='General',direccion='Datos de demostración'))
    proveedor=insertar('proveedores',dict(nombre_empresa='Proveedor DEMO repuestos y servicios',
        contacto_nombre='Contacto ficticio',identificacion_fiscal='DEMO-SIN-RUC',telefono='00000000',
        direccion='Datos de demostración',activo=1))

    def producto(sku,nombre,costo,precio,stock=0,fisico=True):
        return insertar('productos',dict(codigo_sku=sku,categoria_id=cat,nombre='[DEMO] '+nombre,
            descripcion=MARK+' Solo para escenario histórico, sin validez comercial.',marca='DEMO',
            costo=costo,precio_venta=precio,stock_actual=stock,stock_minimo=0,activo=int(fisico)))

    inicial=producto('DEMO-IR-APERTURA','Inventario aportado al inicio 2024',1000,1500,100)
    cur.execute("SELECT id FROM asientos_contables WHERE concepto=?",(f'{MARK} Apertura 2024 - muestra sin validez oficial',))
    apertura=cur.fetchone()[0]
    mid=insertar('movimientos_inventario',dict(fecha='2024-01-01',producto_id=inicial,
        tipo_movimiento='ENTRADA_INICIAL',cantidad=100,stock_anterior=0,stock_posterior=100,
        referencia_origen='DEMO-IR-APERTURA',motivo=MARK+' Aporte inicial de inventario (100 × C$1,000)',usuario_id=uid))
    origen('APERTURA-INVENTARIO','movimientos_inventario',mid,'2024-01-01',100000,apertura)
    origen('APERTURA-EQUIPO','soporte_demostracion',None,'2024-01-01',60000,apertura,
           concepto='Equipo aportado al capital',depreciacion_2024_mensual=1000,
           revision_vida_util_2025='Saldo C$48,000 distribuido en 24 meses: C$2,000 mensuales')

    # Extensión ya prevista por las rutas de pagos RRHH, ausente en algunas bases locales.
    for col in ('cuenta_id','asiento_id'):
        cur.execute(f"IF COL_LENGTH('pagos_nomina','{col}') IS NULL ALTER TABLE pagos_nomina ADD {col} INT NULL")

    for anio, venta, taller, costo, salario, alquiler, energia, dep, publicidad, ret in [
        (2024,80000,10000,45000,15000,5000,3000,1000,1000,300),
        (2025,100000,15000,60000,25000,6000,5000,2000,2000,400),
    ]:
        repuesto=producto(f'DEMO-IR-REP-{anio}',f'Repuestos escenario {anio}',costo/100,venta/100)
        servicio=producto(f'DEMO-IR-TAL-{anio}',f'Servicio de taller {anio}',0,taller,fisico=False)
        conceptos=[('6.1.02','Alquiler',alquiler),('6.1.03','Energía',energia),('6.1.06','Publicidad',publicidad)]
        productos_gasto=[producto(f'DEMO-IR-G-{anio}-{i}',f'{nombre} {anio}',monto,0,fisico=False)
                          for i,(_,nombre,monto) in enumerate(conceptos)]
        emp=insertar('empleados',dict(nombre_completo=f'Empleado DEMO histórico {anio}',
            identificacion=f'DEMO-EMP-{anio}',cargo='Auxiliar de demostración',salario_base=salario,
            fecha_ingreso=f'{anio}-01-01',activo=0,fecha_baja=f'{anio}-12-31',
            motivo_baja='Fin del escenario histórico de demostración',num_inss=f'DEMO{anio}',
            observaciones=MARK+' Persona ficticia. No incluir en nóminas actuales.'))
        calc=calcular_nomina_empleado(salario,parametros=PARAMETROS)
        for mes in range(1,13):
            per=f'{anio}-{mes:02}'; dia=f'{per}-{monthrange(anio,mes)[1]}'
            codigo_c=f'DEMO-C-{per}'; codigo_v=f'DEMO-V-{per}'; codigo_g=f'DEMO-G-{per}'
            # Compra recibida y pagada, seguida de su salida al vender.
            compra=insertar('compras',dict(codigo_compra=codigo_c,numero_factura_proveedor=codigo_c,
                proveedor_id=proveedor,usuario_id=uid,fecha_compra=f'{per}-01',total=costo,
                forma_pago='Transferencia',estado='Completada',observaciones=MARK+' Repuestos recibidos y pagados.'))
            insertar('detalle_compras',dict(compra_id=compra,producto_id=repuesto,cantidad=100,costo_unitario=costo/100,subtotal=costo))
            insertar('movimientos_inventario',dict(fecha=f'{per}-01',producto_id=repuesto,tipo_movimiento='ENTRADA_COMPRA',
                cantidad=100,stock_anterior=0,stock_posterior=100,referencia_origen=f'Compra {codigo_c}',motivo=MARK+' Recepción de repuestos',usuario_id=uid))
            asiento('COMPRA-'+per,f'{per}-01',[('1.1.04',costo,0),('1.1.02',0,costo)],'compras',compra,per+' compra de repuestos')
            ingreso=venta+taller
            vid=insertar('ventas',dict(codigo_venta=codigo_v,cliente_id=cliente,usuario_id=uid,fecha_venta=dia,
                subtotal=ingreso,descuento=0,total=ingreso,forma_pago='Transferencia',estado='Completada',
                notas=MARK+f' Venta histórica ficticia. Cobrado {ingreso-ret}; retención a cuenta IR {ret}.'))
            for pid,cant,precio,cost in [(repuesto,100,venta/100,costo/100),(servicio,1,taller,0)]:
                insertar('detalle_ventas',dict(venta_id=vid,producto_id=pid,cantidad=cant,
                    precio_unitario=precio,costo_historico=cost,subtotal=cant*precio))
            insertar('movimientos_inventario',dict(fecha=dia,producto_id=repuesto,tipo_movimiento='SALIDA_VENTA',
                cantidad=100,stock_anterior=100,stock_posterior=0,referencia_origen=f'Venta {codigo_v}',motivo=MARK+' Costo de repuestos vendidos',usuario_id=uid))
            insertar('pagos',dict(venta_id=vid,origen='VENTA_POS',metodo='Transferencia',monto=ingreso-ret,referencia=codigo_v+'-COBRO',fecha=dia))
            insertar('comprobantes',dict(venta_id=vid,origen='VENTA_POS',numero='TICK-'+codigo_v,fechaEmision=dia,total=ingreso))
            asiento('VENTA-'+per,dia,[('1.1.02',ingreso-ret,0),('1.1.06',ret,0),('4.1.01',0,venta),('4.1.02',0,taller)],'ventas',vid,per+' ventas y taller')
            asiento('COSTO-'+per,dia,[('5.1.01',costo,0),('1.1.04',0,costo)],'ventas',vid,per+' costo de ventas')
            cur.execute("""UPDATE acreditamientos_tributarios SET agente_retenedor_nombre=?,
                concepto=? WHERE numero_referencia=?""",('Cliente DEMO histórico (ficticio)',
                MARK+f' Retención de venta {codigo_v}, constancia ficticia',f'DEMO-IR-{per}-RET'))
            # Gastos no inventariables respaldados en Compras. La depreciación es un soporte contable.
            gasto=insertar('compras',dict(codigo_compra=codigo_g,numero_factura_proveedor=codigo_g,
                proveedor_id=proveedor,usuario_id=uid,fecha_compra=dia,total=alquiler+energia+publicidad,
                forma_pago='Transferencia',estado='Completada',observaciones=MARK+' Servicios/gastos no inventariables, pagados.'))
            for pid,(_,_,monto) in zip(productos_gasto,conceptos):
                insertar('detalle_compras',dict(compra_id=gasto,producto_id=pid,cantidad=1,costo_unitario=monto,subtotal=monto))
            asiento('GASTOS-'+per,dia,[(cod,monto,0) for cod,_,monto in conceptos]+[
                ('6.1.09',dep,0),('1.2.03',0,dep),('1.1.02',0,alquiler+energia+publicidad)],
                'compras',gasto,per+' gastos')
            origen('DEPRECIACION-'+per,'soporte_demostracion',None,dia,dep,
                   concepto='Depreciación del equipo aportado',soporte='APERTURA-EQUIPO')
            # No utilizar empleados ni parámetros actuales: instantánea explícita de la simulación.
            cur.execute('SELECT id FROM nomina WHERE periodo_mes=? AND periodo_anio=?',(mes,anio))
            if cur.fetchone():
                raise ValueError(f'Ya existe una nómina ajena al escenario para {per}.')
            nid=insertar('nomina',dict(periodo_mes=mes,periodo_anio=anio,fecha_generacion=dia,
                total_ingresos=calc['salario_bruto'],total_deducciones=calc['total_deducciones'],
                total_neto=calc['salario_neto'],inss_patronal_total=calc['inss_patronal'],
                inatec_patronal_total=calc['inatec_patronal'],provision_vac_total=calc['provision_vacaciones'],
                provision_agui_total=calc['provision_aguinaldo'],estado='CERRADA'))
            insertar('detalle_nomina',dict(nomina_id=nid,empleado_id=emp,salario_base=salario,ingresos_extra=0,
                inss_laboral=calc['inss_laboral'],ir=calc['ir_retencion'],neto_pagar=calc['salario_neto'],
                inss_patronal=calc['inss_patronal'],inatec_patronal=calc['inatec_patronal'],
                provision_vacaciones=calc['provision_vacaciones'],provision_aguinaldo=calc['provision_aguinaldo'],
                dias_trabajados=30,vac_acumulada=(mes-1)*2.5,vac_mes=2.5,vac_saldo_final=mes*2.5,
                historico_salario=salario,historico_nombre=f'Empleado DEMO histórico {anio}',
                historico_identificacion=f'DEMO-EMP-{anio}',historico_cargo='Auxiliar de demostración',
                historico_inss=f'DEMO{anio}',historico_ingreso=f'{anio}-01-01'))
            cargas=round(calc['inss_patronal']+calc['inatec_patronal'],2)
            prov=round(calc['provision_vacaciones']+calc['provision_aguinaldo'],2)
            aid=asiento('NOMINA-'+per,dia,[('6.1.01',salario,0),('6.1.11',cargas,0),('6.1.12',prov,0),
                ('2.1.06',0,round(calc['inss_laboral']+calc['inss_patronal'],2)),
                ('2.1.07',0,calc['ir_retencion']),('2.1.08',0,prov),('2.1.04',0,calc['salario_neto']),
                ('2.1.10',0,calc['inatec_patronal'])],'nomina',nid)
            pid=insertar('pagos_nomina',dict(nomina_id=nid,empleado_id=emp,monto_pagado=calc['salario_neto'],
                fecha_pago=dia,metodo_pago='Transferencia Bancaria',numero_referencia='DEMO-PN-'+per,
                estado='Confirmado',observaciones=MARK+' Pago ficticio del neto, sin transferencia real.',
                registrado_por='Demo académica',cuenta_id=cuentas['1.1.02']))
            pago_asiento=asiento('PAGO-NOMINA-'+per,dia,[('2.1.04',calc['salario_neto'],0),('1.1.02',0,calc['salario_neto'])],'pagos_nomina',pid)
            cur.execute('UPDATE pagos_nomina SET asiento_id=? WHERE id=?',(pago_asiento,pid))
            origen('PARAMETROS-NOMINA-'+per,'nomina',nid,dia,salario,parametros=PARAMETROS)

    # Sustituir solamente los borradores de esta carga: nunca una declaración presentada.
    cur.execute("SELECT id FROM declaraciones_ir WHERE ejercicio_fiscal IN (2024,2025) AND observaciones LIKE '[[]DEMO-FISCAL]%' AND estado='Borrador'")
    for r in cur.fetchall():
        fiscal.eliminar_declaracion(cur,r.id)
    for anio in (2024,2025):
        sim=fiscal.preparar_declaracion_desde_contabilidad(cur,{'anio':anio})
        did=fiscal.guardar_declaracion_completa(cur,sim,uid)
        origen('DECLARACION-'+str(anio),'declaraciones_ir',did,f'{anio}-12-31',sim['liquidacion']['saldo_a_pagar'])
    origen(VERSION,'carga_demostracion',None,'2025-12-31',parametros=PARAMETROS)
    return verificar(conn,dict(counts))


def verificar(conn, insertados):
    cur=conn.cursor()
    resultados={}
    for anio in (2024,2025):
        sim=fiscal.preparar_declaracion_desde_contabilidad(cur,{'anio':anio})
        if not sim['balance']['balance_cuadrado']:
            raise ValueError(f'Balance {anio} descuadrado; se cancela la carga.')
        cur.execute("""SELECT SUM(d.subtotal),SUM(d.cantidad*d.costo_historico)
            FROM ventas v JOIN detalle_ventas d ON d.venta_id=v.id
            WHERE v.codigo_venta LIKE 'DEMO-V-%' AND YEAR(v.fecha_venta)=?""",(anio,))
        ingresos,costos=map(float,cur.fetchone())
        if ingresos!=sim['resultados']['total_ingresos_brutos'] or costos!=sim['resultados']['total_costos']:
            raise ValueError(f'Ventas y costos no coinciden con el IR {anio}.')
        cur.execute("""SELECT SUM(c.total) FROM compras c WHERE c.codigo_compra LIKE 'DEMO-C-%'
            AND YEAR(c.fecha_compra)=?""",(anio,))
        if float(cur.fetchone()[0])!=costos: raise ValueError(f'Compras no coinciden con costo vendido {anio}.')
        cur.execute("""SELECT SUM(c.total) FROM compras c WHERE c.codigo_compra LIKE 'DEMO-G-%'
            AND YEAR(c.fecha_compra)=?""",(anio,))
        gastos_compras=float(cur.fetchone()[0])
        cur.execute("""SELECT SUM(d.salario_base),SUM(d.inss_patronal+d.inatec_patronal),
            SUM(d.provision_vacaciones+d.provision_aguinaldo) FROM detalle_nomina d
            JOIN nomina n ON n.id=d.nomina_id WHERE n.periodo_anio=?""",(anio,))
        salarios,cargas,provisiones=map(float,cur.fetchone())
        res=sim['cuentas_resultados']
        if gastos_compras!=sum(res[c] for c in ('6.1.02','6.1.03','6.1.06')):
            raise ValueError(f'Compras de servicios no coinciden con gastos {anio}.')
        for importe,codigo in [(salarios,'6.1.01'),(cargas,'6.1.11'),(provisiones,'6.1.12')]:
            if abs(importe-res[codigo])>.01: raise ValueError(f'Nómina no coincide con {codigo}: {anio}')
        resultados[anio]={'ingresos':ingresos,'costos':costos,'salarios':salarios,'cargas':cargas,
            'provisiones':provisiones,'gastos':sim['resultados']['total_gastos'],
            'renta_neta':sim['calculo_ir']['renta_neta_gravable'],'tasa_ir':sim['calculo_ir']['tasa_ir'],
            **sim['liquidacion']}
    # Cobro neto + retención respaldan el total de cada venta.
    cur.execute("""SELECT v.id FROM ventas v
        LEFT JOIN (SELECT venta_id,SUM(monto) monto FROM pagos GROUP BY venta_id) p ON p.venta_id=v.id
        LEFT JOIN acreditamientos_tributarios ac ON ac.numero_referencia=REPLACE(v.codigo_venta,'DEMO-V-','DEMO-IR-')+'-RET'
        WHERE v.codigo_venta LIKE 'DEMO-V-%' AND ABS(v.total-ISNULL(p.monto,0)-ISNULL(ac.importe_total,0))>.001""")
    if cur.fetchone(): raise ValueError('Venta DEMO sin respaldo completo de cobro y retención.')
    cur.execute("""SELECT d.id FROM detalle_nomina d JOIN empleados e ON e.id=d.empleado_id
        LEFT JOIN (SELECT nomina_id,empleado_id,SUM(monto_pagado) monto FROM pagos_nomina
                   WHERE estado='Confirmado' GROUP BY nomina_id,empleado_id) p
        ON p.nomina_id=d.nomina_id AND p.empleado_id=d.empleado_id
        WHERE e.identificacion LIKE 'DEMO-EMP-%' AND ABS(d.neto_pagar-ISNULL(p.monto,0))>.001""")
    if cur.fetchone(): raise ValueError('Nómina DEMO sin respaldo completo de pago.')
    cur.execute("""SELECT a.id FROM asientos_contables a JOIN movimientos_contables m ON m.asiento_id=a.id
        WHERE a.modulo_origen='DEMO_FISCAL' GROUP BY a.id HAVING ABS(SUM(m.debe)-SUM(m.haber))>.001""")
    if cur.fetchone(): raise ValueError('Existe un asiento DEMO desbalanceado.')
    cur.execute("""SELECT d.clave FROM demo_fiscal_origenes d LEFT JOIN asientos_contables a ON a.id=d.asiento_id
        WHERE d.asiento_id IS NOT NULL AND a.id IS NULL""")
    if cur.fetchone(): raise ValueError('Origen sin asiento.')
    cur.execute("""SELECT d.clave FROM demo_fiscal_origenes d JOIN asientos_contables a ON a.id=d.asiento_id
        WHERE d.clave NOT LIKE 'ANTES-%' AND CAST(a.fecha AS DATE)<>d.fecha""")
    if cur.fetchone(): raise ValueError('Las fechas de los documentos y sus asientos no coinciden.')
    cur.execute('SELECT clave,tabla_origen,documento_id,asiento_id,fecha,importe,detalle FROM demo_fiscal_origenes ORDER BY fecha,clave')
    fuentes=[dict(zip([c[0] for c in cur.description],r)) for r in cur.fetchall()]
    return {'marca':MARK,'version':VERSION,'insertados':insertados,'ejercicios':resultados,'fuentes':fuentes}


def main():
    from app import get_db_connection
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args=parser.parse_args()
    conn=get_db_connection(); conn.autocommit=False
    try:
        result=cargar(conn)
        if args.apply: conn.commit()
        else: conn.rollback()
        result['aplicado']=args.apply
        if args.apply:
            folder=Path(__file__).parent/'output'/'fiscal_demo';folder.mkdir(parents=True,exist_ok=True)
            (folder/'operaciones_2024_2025.json').write_text(json.dumps(result,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
        print(json.dumps({k:v for k,v in result.items() if k!='fuentes'},ensure_ascii=False,indent=2,default=str))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__=='__main__': main()
