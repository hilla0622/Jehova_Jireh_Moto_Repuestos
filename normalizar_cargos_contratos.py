"""Normalización auditable del personal y contratos de la carga para la feria."""
import json
from pathlib import Path
from datetime import datetime
from app import get_db_connection

def main():
    conn=get_db_connection()
    try:
        cur=conn.cursor()
        cur.execute('SET XACT_ABORT ON')
        cur.execute("SELECT id FROM cargas_negocio WHERE version='NEGOCIO-2024-2026-V1'")
        cid=cur.fetchone()[0]
        def rows(tabla):
            cur.execute(f'SELECT * FROM [{tabla}]'); cols=[x[0] for x in cur.description]
            return [dict(zip(cols,r)) for r in cur.fetchall()]
        snapshot={t:rows(t) for t in ['cargos','empleados','contratos_laborales']}
        dest=Path('output/carga_negocio');dest.mkdir(parents=True,exist_ok=True)
        (dest/f'cargos_contratos_antes_{datetime.now():%Y%m%d_%H%M%S}.json').write_text(json.dumps(snapshot,default=str,ensure_ascii=False,indent=2),encoding='utf-8')
        cambios=0
        def cambiar(tabla,rid,campo,antes,despues):
            nonlocal cambios
            if antes==despues:return
            cur.execute(f'UPDATE [{tabla}] SET [{campo}]=? WHERE id=?',despues,rid)
            cur.execute('INSERT INTO carga_negocio_cambios(carga_id,tabla,registro_id,campo,antes,despues) VALUES(?,?,?,?,?,?)',cid,tabla,rid,campo,None if antes is None else str(antes),None if despues is None else str(despues))
            cambios+=1
        def insertar(tabla,datos):
            cur.execute(f"INSERT INTO [{tabla}] ({','.join(datos)}) OUTPUT inserted.id VALUES ({','.join('?' for _ in datos)})",tuple(datos.values()))
            rid=cur.fetchone()[0]
            cur.execute('INSERT INTO carga_negocio_registros(carga_id,tabla,registro_id) VALUES(?,?,?)',cid,tabla,rid)
            return rid
        definiciones=[
            (1,'Vendedor de Mostrador','Ventas','Asesorar sobre compatibilidad de repuestos, atender clientes y registrar ventas.',12000),
            (2,'Cajero de tienda','Caja','Cobrar ventas, emitir comprobantes y realizar apertura y cierre de caja.',11500),
            (3,'Encargado de inventario y bodega','Inventario','Recibir mercancía, verificar existencias y controlar movimientos y niveles mínimos.',13000),
            (5,'Administrador del negocio','Administración','Coordinar la operación de la tienda, compras, personal y seguimiento de resultados.',18000),
            (16,'Auxiliar de bodega','Inventario','Ordenar repuestos, apoyar conteos y preparar productos para entrega en tienda.',9200),
            (None,'Contador','Contabilidad','Registrar y revisar operaciones contables, conciliaciones, estados financieros y declaraciones.',15000),
            (None,'Auxiliar de ventas','Ventas','Apoyar la atención al cliente, exhibición y preparación de pedidos para retiro.',12000)]
        ids={}; descripciones={}
        for rid,nombre,area,descripcion,salario in definiciones:
            previo=next((r for r in snapshot['cargos'] if r['id']==rid or (rid is None and r['nombre_cargo']==nombre)),None)
            datos=dict(nombre_cargo=nombre,area=area,descripcion=descripcion,responsabilidades=descripcion,activo=True)
            if previo:
                rid=previo['id']
                for k,v in datos.items():cambiar('cargos',rid,k,previo[k],v)
            else:rid=insertar('cargos',dict(**datos,salario_base_sugerido=salario))
            ids[nombre]=rid;descripciones[nombre]=descripcion
        for r in snapshot['cargos']:
            if r['id'] not in ids.values():cambiar('cargos',r['id'],'activo',r['activo'],False)
        mapa={'Vendedor':'Vendedor de Mostrador','Bodeguero':'Encargado de inventario y bodega',
              'Mecánico de motocicletas':'Vendedor de Mostrador','Cajera':'Cajero de tienda'}
        for e in snapshot['empleados']:
            cargo=mapa.get(e['cargo'],e['cargo'])
            if cargo not in ids:raise ValueError('Cargo sin correspondencia: '+cargo)
            cambiar('empleados',e['id'],'cargo',e['cargo'],cargo)
            cambiar('empleados',e['id'],'cargo_id',e['cargo_id'],ids[cargo])
            contratos=[c for c in snapshot['contratos_laborales'] if c['empleado_id']==e['id']]
            if len(contratos)>1:raise ValueError('Revisar contratos múltiples antes de continuar')
            datos=dict(cargo=cargo,salario_mensual=e['salario_base'],fecha_inicio=e['fecha_ingreso'],
                fecha_fin=e['fecha_baja'] if not e['activo'] else None,estado='Vigente' if e['activo'] else 'Finalizado',
                numero_contrato=f"CTR-{e['fecha_ingreso'].year}-{e['id']:04d}",
                lugar_trabajo='Tienda principal, Masatepe',forma_pago='Mensual',
                jornada_laboral=e['jornada_asignada'] or 'Diurna, lunes a sábado',
                observaciones=descripciones[cargo])
            if contratos:
                c=contratos[0]
                if c['documento_adjunto']:raise ValueError('El contrato tiene adjunto; requiere revisión específica')
                for k,v in datos.items():cambiar('contratos_laborales',c['id'],k,c[k],v)
            else:insertar('contratos_laborales',dict(**datos,empleado_id=e['id'],tipo_contratacion='Tiempo Indeterminado'))
        cur.execute('''SELECT COUNT(*) FROM empleados e LEFT JOIN cargos c ON c.id=e.cargo_id
            WHERE c.id IS NULL OR c.activo=0 OR c.nombre_cargo<>e.cargo''')
        assert cur.fetchone()[0]==0
        cur.execute('''SELECT COUNT(*) FROM contratos_laborales c JOIN empleados e ON e.id=c.empleado_id
            WHERE c.cargo<>e.cargo OR c.salario_mensual<>e.salario_base OR c.fecha_inicio<>e.fecha_ingreso
            OR (e.activo=1 AND (c.estado<>'Vigente' OR c.fecha_fin IS NOT NULL))
            OR (e.activo=0 AND (c.estado<>'Finalizado' OR c.fecha_fin<>e.fecha_baja))''')
        assert cur.fetchone()[0]==0
        conn.commit()
        print(json.dumps({'cambios':cambios,'cargos_activos':list(ids),'contratos':len(snapshot['empleados'])},ensure_ascii=True))
    except Exception:
        conn.rollback();raise
    finally:conn.close()

if __name__=='__main__':main()
