"""Corrige únicamente la carga histórica identificada por demo_fiscal_origenes.

Sin --apply ejecuta la corrección y sus comprobaciones, y revierte la transacción.
Conserva los totales anuales y los identificadores de documentos existentes.
"""
import argparse
from datetime import datetime
from decimal import Decimal
import json
from pathlib import Path

VERSION = 'OPERACIONES-V2'
CANTIDADES = (73, 86, 94, 81, 103, 97, 112, 89, 106, 118, 102, 139)
CLIENTES = ('Marcos Gaitan', 'Ana Martínez', 'José López', 'Karla Mendoza',
            'Luis Hernández', 'Rosa Castillo', 'Carlos Ramírez', 'María Flores',
            'Pedro García', 'Sandra Pérez', 'Jorge Sánchez', 'Lucía Morales')


def corregir(conn):
    cur = conn.cursor()
    cur.execute('SET DATEFORMAT ymd')
    cur.execute('SELECT clave FROM demo_fiscal_origenes WITH (UPDLOCK,HOLDLOCK) WHERE clave=?', (VERSION,))
    if cur.fetchone():
        return {}
    cur.execute("SELECT clave FROM demo_fiscal_origenes WHERE clave='OPERACIONES-V1'")
    if not cur.fetchone():
        raise ValueError('Primero se debe cargar el escenario histórico V1.')
    cur.execute("""SELECT id FROM declaraciones_ir WHERE ejercicio_fiscal IN (2024,2025)
        AND estado<>'Borrador'""")
    if cur.fetchone():
        raise ValueError('Hay declaraciones aprobadas/presentadas; no se modificarán sus fuentes.')

    def codigo(tabla, campo, prefijo, inicio):
        numero = inicio
        while True:
            valor = f'{prefijo}{numero:04d}'
            cur.execute(f'SELECT id FROM {tabla} WITH (UPDLOCK,HOLDLOCK) WHERE {campo}=?', (valor,))
            if not cur.fetchone():
                return valor
            numero += 1
            if numero > 9999:
                raise ValueError(f'Se agotaron los códigos disponibles: {prefijo}')

    def producto(anterior, sku, nombre, categoria, activo=True):
        cur.execute('SELECT id FROM categorias WHERE nombre=?', (categoria,))
        cat = cur.fetchone()
        if not cat:
            raise ValueError(f'Categoría existente no encontrada: {categoria}')
        cur.execute('SELECT id FROM productos WHERE codigo_sku=?', (anterior,))
        row = cur.fetchone()
        if not row:
            raise ValueError(f'Producto histórico no encontrado: {anterior}')
        pid = row[0]
        cur.execute('SELECT id FROM productos WHERE codigo_sku=? AND id<>?', (sku, pid))
        if cur.fetchone():
            raise ValueError(f'Código de producto ocupado: {sku}')
        cur.execute('''UPDATE productos SET codigo_sku=?,nombre=?,categoria_id=?,marca=NULL,
            activo=? WHERE id=?''', (sku,nombre,cat[0],int(activo),pid))
        return pid

    producto('DEMO-IR-APERTURA', 'CIL901', 'CILINDRO COMPLETO CG150 62MM', 'Motor y Partes Internas')
    repuestos = {}
    for anio, sku, nombre, categoria in [
        (2024,'KIT901','KIT DE ARRASTRE CG125 CADENA CORONA Y PIÑÓN','Transmisión y Embrague'),
        (2025,'AMO901','AMORTIGUADORES TRASEROS CG150 PAR','Suspensión y Dirección'),
    ]:
        repuestos[anio] = producto(f'DEMO-IR-REP-{anio}',sku,nombre,categoria)
        producto(f'DEMO-IR-TAL-{anio}',f'SER{anio-1100}', 'Mano de obra de mantenimiento de motocicleta',
                 'Chasis y Accesorios',False)
        for i, concepto in enumerate(('Alquiler del local','Servicio de energía eléctrica','Publicidad del negocio')):
            producto(f'DEMO-IR-G-{anio}-{i}',f'GAS{(anio-2024)*3+i+901}',concepto,
                     'Chasis y Accesorios',False)

    cur.execute("SELECT id FROM clientes WHERE identificacion='DEMO-CLIENTE-IR'")
    original = cur.fetchone()[0]
    cur.execute('UPDATE clientes SET nombre_completo=?,email=NULL WHERE id=?', (CLIENTES[0],original))
    clientes = [original]
    for nombre in CLIENTES[1:]:
        cur.execute('''INSERT INTO clientes (nombre_completo,tipo_cliente,direccion,password_hash)
            OUTPUT INSERTED.id VALUES (?,'General','Datos de demostración','DEMO_SIN_ACCESO')''', (nombre,))
        clientes.append(cur.fetchone()[0])
    cur.execute("""UPDATE proveedores SET nombre_empresa='Repuestos y Accesorios Masatepe',
        contacto_nombre='Roberto Méndez' WHERE identificacion_fiscal='DEMO-SIN-RUC'""")
    for anio, nombre in [(2024,'Daniel Rodríguez'),(2025,'Patricia Gómez')]:
        cur.execute('UPDATE empleados SET nombre_completo=?,cargo=? WHERE identificacion=?',
                    (nombre,'Auxiliar de ventas',f'DEMO-EMP-{anio}'))
        cur.execute('''UPDATE d SET historico_nombre=?,historico_cargo='Auxiliar de ventas'
            FROM detalle_nomina d JOIN empleados e ON e.id=d.empleado_id WHERE e.identificacion=?''',
                    (nombre,f'DEMO-EMP-{anio}'))

    for anio, venta_base, taller_base, costo_base, ret in [(2024,80000,10000,45000,300),(2025,100000,15000,60000,400)]:
        for mes in range(1,13):
            per = f'{anio}-{mes:02d}'
            cantidad = CANTIDADES[(mes-1+(3 if anio==2025 else 0)) % 12]
            factor = Decimal(cantidad)/100
            venta, taller, costo = [Decimal(x)*factor for x in (venta_base,taller_base,costo_base)]
            ingreso = venta+taller
            cur.execute("SELECT documento_id FROM demo_fiscal_origenes WHERE clave=?", ('VENTA-'+per,))
            vid = cur.fetchone()[0]
            cur.execute('SELECT codigo_venta,estado FROM ventas WHERE id=?', (vid,))
            viejo, estado = cur.fetchone()
            if estado != 'Completada':
                raise ValueError(f'La venta {viejo} fue modificada; requiere revisión.')
            nuevo = codigo('ventas','codigo_venta','VEN-',2401+(anio-2024)*100+mes-1)
            nombre = CLIENTES[(mes-1+(5 if anio==2025 else 0)) % 12]
            cliente = clientes[CLIENTES.index(nombre)]
            cur.execute('UPDATE ventas SET codigo_venta=?,cliente_id=?,subtotal=?,total=?,notas=? WHERE id=?',
                        (nuevo,cliente,ingreso,ingreso,f'[DEMO-FISCAL] Venta histórica ficticia. Cobrado {ingreso-ret}; retención IR {ret}.',vid))
            cur.execute('''UPDATE detalle_ventas SET cantidad=?,subtotal=precio_unitario*?
                WHERE venta_id=? AND producto_id=?''', (cantidad,cantidad,vid,repuestos[anio]))
            cur.execute('''UPDATE detalle_ventas SET precio_unitario=?,subtotal=?
                WHERE venta_id=? AND producto_id<>?''', (taller,taller,vid,repuestos[anio]))
            cur.execute('UPDATE pagos SET monto=?,referencia=? WHERE venta_id=?', (ingreso-ret,'Cobro en caja '+nuevo,vid))
            cur.execute('UPDATE comprobantes SET total=?,numero=? WHERE venta_id=?', (ingreso,'TICK-'+nuevo,vid))
            cur.execute('''UPDATE acreditamientos_tributarios SET agente_retenedor_nombre=?,concepto=?
                WHERE numero_referencia=?''', (nombre,f'[DEMO-FISCAL] Retención de venta {nuevo}, constancia ficticia',f'DEMO-IR-{per}-RET'))
            cur.execute('''UPDATE movimientos_inventario SET cantidad=?,stock_anterior=?,stock_posterior=0,
                referencia_origen=? WHERE producto_id=? AND referencia_origen=?''',
                        (cantidad,cantidad,'Venta '+nuevo,repuestos[anio],'Venta '+viejo))
            for clave in ('COMPRA-', 'GASTOS-'):
                cur.execute('SELECT documento_id FROM demo_fiscal_origenes WHERE clave=?',(clave+per,))
                cid = cur.fetchone()[0]
                cur.execute('SELECT codigo_compra,estado FROM compras WHERE id=?',(cid,))
                viejo_c, estado = cur.fetchone()
                if estado != 'Completada':
                    raise ValueError(f'La compra {viejo_c} fue modificada; requiere revisión.')
                nuevo_c = codigo('compras','codigo_compra','COM-#',2401+(anio-2024)*100+(mes-1)*2+(clave=='GASTOS-'))
                cur.execute('UPDATE compras SET codigo_compra=?,numero_factura_proveedor=? WHERE id=?',(nuevo_c,nuevo_c,cid))
                if clave=='COMPRA-':
                    cur.execute('UPDATE compras SET total=? WHERE id=?',(costo,cid))
                    cur.execute('UPDATE detalle_compras SET cantidad=?,subtotal=costo_unitario*? WHERE compra_id=?',(cantidad,cantidad,cid))
                    cur.execute('''UPDATE movimientos_inventario SET cantidad=?,stock_posterior=?,referencia_origen=?
                        WHERE producto_id=? AND referencia_origen=?''',(cantidad,cantidad,'Compra '+nuevo_c,repuestos[anio],'Compra '+viejo_c))
            # Actualizar ambos lados de los asientos sin cambiar las cuentas ni sus enlaces.
            for clave, importes in [
                ('VENTA-',{'1.1.02':(ingreso-ret,0),'1.1.06':(ret,0),'4.1.01':(0,venta),'4.1.02':(0,taller)}),
                ('COMPRA-',{'1.1.04':(costo,0),'1.1.02':(0,costo)}),
                ('COSTO-',{'5.1.01':(costo,0),'1.1.04':(0,costo)}),
            ]:
                for cuenta,(debe,haber) in importes.items():
                    cur.execute('''UPDATE m SET debe=?,haber=? FROM movimientos_contables m
                        JOIN cuentas_contables c ON c.id=m.cuenta_id
                        JOIN demo_fiscal_origenes o ON o.asiento_id=m.asiento_id
                        WHERE o.clave=? AND c.codigo=?''',(debe,haber,clave+per,cuenta))
                cur.execute('UPDATE demo_fiscal_origenes SET importe=? WHERE clave=?',
                            (sum(Decimal(d) for d,_ in importes.values()),clave+per))

    cur.execute("""DELETE FROM categorias WHERE nombre='Demostración histórica IR'
        AND NOT EXISTS (SELECT 1 FROM productos WHERE categoria_id=categorias.id)""")
    cur.execute('''INSERT INTO demo_fiscal_origenes (clave,tabla_origen,fecha,importe,detalle)
        VALUES (?,'carga_demostracion','2025-12-31',0,?)''',
                (VERSION,json.dumps({'clientes':12,'ventas':24,'cantidades':CANTIDADES})))
    return {'ventas_corregidas':24,'clientes_distintos':12,'productos_corregidos':11}


def main():
    from app import get_db_connection
    from seed_fiscal_operaciones import verificar
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true')
    args = parser.parse_args()
    conn = get_db_connection()
    conn.autocommit = False
    try:
        if args.apply:
            # Copia de las tablas afectadas antes de modificar cualquier registro.
            folder = Path(__file__).parent/'output'/'fiscal_demo'
            folder.mkdir(parents=True,exist_ok=True)
            respaldo = {}
            cur = conn.cursor()
            for tabla in ('categorias','productos','clientes','proveedores','empleados','detalle_nomina',
                          'ventas','detalle_ventas','compras','detalle_compras','pagos','comprobantes',
                          'movimientos_inventario','movimientos_contables','acreditamientos_tributarios','demo_fiscal_origenes'):
                cur.execute(f'SELECT * FROM {tabla}')
                cols = [c[0] for c in cur.description]
                respaldo[tabla] = [dict(zip(cols,r)) for r in cur.fetchall()]
            path = folder/f'respaldo_antes_v2_{datetime.now():%Y%m%d_%H%M%S}.json'
            path.write_text(json.dumps(respaldo,ensure_ascii=False,default=str,indent=2),encoding='utf-8')
        cambios = corregir(conn)
        resultado = verificar(conn,cambios)
        if args.apply:
            conn.commit()
            (folder/'operaciones_2024_2025.json').write_text(json.dumps(resultado,ensure_ascii=False,default=str,indent=2),encoding='utf-8')
        else:
            conn.rollback()
        print(json.dumps({k:v for k,v in resultado.items() if k!='fuentes'},ensure_ascii=False,default=str,indent=2))
        print('Aplicado.' if args.apply else 'Validado; transacción revertida.')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__=='__main__':
    main()
