"""Completa las gerencias del personal generado para la feria, desde 02/11/2024."""
from datetime import date
import json
from app import get_db_connection

PERSONAS = [
    (1002, 'Gerente de Operaciones', 'Eduardo Antonio Méndez Vargas', 22000,
     'Operaciones', 'Supervisar ventas, inventario, compras, proveedores y retiro de pedidos en tienda.'),
    (1003, 'Gerente Administrativo y Financiero', 'Claudia Patricia Salazar Ruiz', 25000,
     'Administración y Finanzas', 'Supervisar contabilidad, presupuestos, tesorería, nómina y procesos administrativos.'),
]

def main():
    conn=get_db_connection()
    try:
        cur=conn.cursor()
        cur.execute('SET XACT_ABORT ON')
        cur.execute("""DECLARE @r INT; EXEC @r=sp_getapplock @Resource='gerencias_feria',
            @LockMode='Exclusive',@LockOwner='Transaction',@LockTimeout=5000;
            IF @r<0 THROW 50001,'Otra actualización está en curso',1;""")
        cur.execute("SELECT id FROM cargas_negocio WHERE version='NEGOCIO-2024-2026-V1'")
        cid=cur.fetchone()[0]
        def insertar(tabla,datos):
            cur.execute(f"INSERT INTO [{tabla}] ({','.join(datos)}) OUTPUT inserted.id VALUES ({','.join('?' for _ in datos)})",tuple(datos.values()))
            rid=cur.fetchone()[0]
            cur.execute('INSERT INTO carga_negocio_registros(carga_id,tabla,registro_id) VALUES(?,?,?)',cid,tabla,rid)
            return rid
        cur.execute("SELECT TOP 1 id,nombre FROM jornadas_laborales WHERE nombre LIKE '%Administraci%' AND activo=1 ORDER BY id")
        jornada=cur.fetchone()
        if not jornada:raise ValueError('Falta la jornada administrativa')
        resultado=[]
        for uid,puesto,nombre,salario,area,funciones in PERSONAS:
            cur.execute('SELECT u.nombre_completo,r.nombre FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.id=?',uid)
            usuario=cur.fetchone()
            if not usuario or usuario[1]!=puesto:raise ValueError('La cuenta no corresponde a la gerencia prevista')
            cur.execute('SELECT id,activo FROM cargos WHERE nombre_cargo=?',puesto)
            cargo=cur.fetchone()
            if cargo and not cargo[1]:raise ValueError('El cargo está inactivo; revisar antes de continuar')
            cargo_id=cargo[0] if cargo else insertar('cargos',dict(nombre_cargo=puesto,descripcion=funciones,
                responsabilidades=funciones,area=area,salario_base_sugerido=salario,activo=True))
            cur.execute('SELECT id FROM empleados WHERE identificacion=?',f'EMP-GER-{uid}')
            emp=cur.fetchone()
            eid=emp[0] if emp else insertar('empleados',dict(nombre_completo=nombre,identificacion=f'EMP-GER-{uid}',
                cargo=puesto,cargo_id=cargo_id,salario_base=salario,fecha_ingreso=date(2024,11,2),activo=True,
                dias_vacaciones_disponibles=0,vacacionesDisponibles=0,jornada_id=jornada[0],jornada_asignada=jornada[1],
                direccion='Zona urbana de Masatepe, Masaya'))
            if not emp:
                insertar('historial_laboral',dict(empleado_id=eid,fecha_vigencia=date(2024,11,2),tipo_modificacion='Ingreso',
                    campo_afectado='cargo',valor_nuevo=puesto,motivo='Incorporación a la gerencia de la tienda',usuario_responsable='Gilda Pérez'))
            cur.execute('SELECT id FROM contratos_laborales WHERE empleado_id=?',eid)
            contrato=cur.fetchone()
            if not contrato:
                insertar('contratos_laborales',dict(numero_contrato=f'CTR-2024-{eid:04d}',empleado_id=eid,
                    tipo_contratacion='Tiempo Indeterminado',lugar_trabajo='Tienda principal, Masatepe',cargo=puesto,
                    jornada_laboral=jornada[1],salario_mensual=salario,forma_pago='Mensual',fecha_inicio=date(2024,11,2),
                    estado='Vigente',observaciones=funciones))
            if usuario[0]!=nombre:
                cur.execute('UPDATE usuarios SET nombre_completo=? WHERE id=?',nombre,uid)
                cur.execute('INSERT INTO carga_negocio_cambios(carga_id,tabla,registro_id,campo,antes,despues) VALUES(?,?,?,?,?,?)',
                    cid,'usuarios',uid,'nombre_completo',usuario[0],nombre)
            resultado.append(dict(empleado=eid,nombre=nombre,cargo=puesto,nuevo=not bool(emp)))
        conn.commit()
        print(json.dumps(resultado,ensure_ascii=True))
    except Exception:
        conn.rollback();raise
    finally:conn.close()

if __name__=='__main__':main()
