"""Prepara una salida y liquidación en borrador del empleado generado para la feria."""
from app import app, get_db_connection


def main():
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        for columna, tipo in [('metodo_pago','varchar(50)'), ('numero_referencia','varchar(100)'),
                              ('cuenta_id','int'), ('asiento_id','int'), ('fecha_pago','date')]:
            cur.execute(f"IF COL_LENGTH('liquidaciones_laborales','{columna}') IS NULL ALTER TABLE liquidaciones_laborales ADD {columna} {tipo} NULL")
        conn.commit()
        cur.execute("""SELECT e.id FROM empleados e JOIN carga_negocio_registros r
            ON r.tabla='empleados' AND r.registro_id=e.id
            WHERE e.nombre_completo=N'Óscar David Espinoza Rivas'""")
        eid = cur.fetchone()[0]
        cur.execute('SELECT id FROM liquidaciones_laborales WHERE empleado_id=? AND fecha_salida=?', eid, '2026-11-02')
        existente = cur.fetchone()
        client = app.test_client()
        with client.session_transaction() as ses:
            ses['user'] = {'id':1,'rol':'Administrador','username':'admin'}
        if not existente:
            res = client.post('/api/rrhh/liquidaciones', json={
                'empleado_id':eid,'fecha_salida':'2026-11-02',
                'motivo_salida':'Despido Injustificado (Art. 45)',
                'dias_pendientes_pago':2,'deducciones_totales':0})
            if res.status_code != 201:
                raise RuntimeError(str(res.get_json()))
        cur.execute('SELECT id,neto_a_pagar,estado FROM liquidaciones_laborales WHERE empleado_id=? AND fecha_salida=?',eid,'2026-11-02')
        lid, neto, estado = cur.fetchone()
        cur.execute('SELECT activo FROM empleados WHERE id=?',eid)
        if cur.fetchone()[0]:
            cur.execute("SELECT carga_id FROM carga_negocio_registros WHERE tabla='empleados' AND registro_id=?",eid)
            cid = cur.fetchone()[0]
            for campo, nuevo in [('activo',False),('fecha_baja','2026-11-02'),('motivo_baja','Despido Injustificado (Art. 45)'),('inss_estado','Inactivo')]:
                cur.execute(f'SELECT [{campo}] FROM empleados WHERE id=?',eid)
                antes = cur.fetchone()[0]
                cur.execute(f'UPDATE empleados SET [{campo}]=? WHERE id=?',nuevo,eid)
                cur.execute('INSERT INTO carga_negocio_cambios(carga_id,tabla,registro_id,campo,antes,despues) VALUES(?,?,?,?,?,?)',cid,'empleados',eid,campo,str(antes),str(nuevo))
            cur.execute("UPDATE contratos_laborales SET estado='Finalizado',fecha_fin=? WHERE empleado_id=? AND estado='Vigente'",'2026-11-02',eid)
            cur.execute('''INSERT INTO historial_laboral(empleado_id,fecha_vigencia,tipo_modificacion,campo_afectado,valor_nuevo,motivo,usuario_responsable)
                VALUES(?,?,'Baja','activo','Inactivo',?,'Gilda Pérez')''',eid,'2026-11-02','Despido Injustificado (Art. 45)')
        conn.commit()
        assert client.get('/api/rrhh/liquidaciones').status_code == 200
        impresion = client.get(f'/rrhh/liquidacion/{lid}/imprimir')
        assert impresion.status_code == 200, impresion.status_code
        print(f'Liquidación {lid}: {estado}, neto C${neto}. Listado e impresión: OK.')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
