"""Comprobación optativa contra SQL Server usando exclusivamente tablas temporales.

Ejecutar directamente, con el entorno de la aplicación. No modifica tablas del negocio.
"""
import re
from pathlib import Path
from unittest.mock import patch

import app as backend

TABLES = ('empleados', 'nomina', 'detalle_nomina', 'movimientos_laborales',
          'horas_extras', 'parametros_laborales', 'cuentas_contables',
          'asientos_contables', 'movimientos_contables', 'colilla_pago', 'pagos_nomina',
          'expediente_empleado', 'higiene_epp', 'higiene_riesgos', 'higiene_riesgo_seguimientos', 'rrhh_archivos')


class CursorTemporal:
    def __init__(self, conexion):
        self.cursor = conexion.cursor()

    def execute(self, sql, params=()):
        for table in TABLES:
            sql = re.sub(r'\b' + table + r'\b', '#rrhh_' + table, sql, flags=re.I)
        self.cursor.execute(sql, params)
        return self

    def __getattr__(self, key):
        return getattr(self.cursor, key)


class ConexionTemporal:
    def __init__(self, conexion):
        self.conexion = conexion

    def cursor(self):
        return CursorTemporal(self.conexion)

    def commit(self):
        self.conexion.commit()

    def rollback(self):
        self.conexion.rollback()

    def close(self):
        self.conexion.rollback()


def main():
    real = backend.get_db_connection()
    try:
        source = (Path(__file__).parents[1] / 'database.sql').read_text(encoding='utf-8')
        cur = real.cursor()
        for table in TABLES:
            body = re.search(r'CREATE TABLE \[' + table + r'\] \((.*?)\n\);', source, re.S)[1]
            body = '\n'.join(line for line in body.splitlines() if 'CONSTRAINT' not in line).rstrip().rstrip(',')
            cur.execute(f'CREATE TABLE #rrhh_{table} ({body})')
        isolated = ConexionTemporal(real)
        cur = isolated.cursor()
        cur.execute("""INSERT INTO empleados
            (nombre_completo,identificacion,cargo,salario_base,fecha_ingreso,activo,dias_vacaciones_disponibles)
            VALUES ('Prueba temporal','TEST-TEMP','Prueba',10000,'2025-01-01',1,10)""")
        cur.execute("""INSERT INTO parametros_laborales (codigo,nombre,valor,unidad)
            VALUES ('INSS_LABORAL','INSS',7,'%')""")
        cur.execute("""INSERT INTO movimientos_laborales
            (empleado_id,tipo,fecha_inicio,fecha_fin,dias_tomados)
            VALUES (1,'PERMISO_SIN_GOCE','2026-01-30','2026-02-02',4)""")
        real.commit()
        with patch.object(backend, 'get_db_connection', return_value=isolated):
            client = backend.app.test_client()
            with client.session_transaction() as s:
                s['user'] = {'id':1,'rol':'Administrador','username':'test'}
            r = client.put('/api/rrhh/parametros/INSS_LABORAL',json={'valor':8})
            assert r.status_code == 200, r.json
            r = client.post('/api/rrhh/horas-extras',json={'empleado_id':1,'fecha':'2026-01-12','cantidad_horas':2})
            assert r.status_code == 201, r.json
            for mes in (1,2):
                r = client.post('/api/nomina/generar',json={'mes':mes,'anio':2026})
                assert r.status_code == 201, r.json
            cur.execute('SELECT dias_permiso_sin_goce FROM detalle_nomina ORDER BY id')
            assert [float(r[0]) for r in cur.fetchall()] == [2,2]
            cur.execute('SELECT SUM(debe)-SUM(haber) FROM movimientos_contables')
            assert float(cur.fetchone()[0]) == 0
            r = client.get('/api/nomina/1/detalle')
            assert r.status_code == 200, r.json
            assert r.json['detalles'][0]['ingresos_extra'] > 0
            r = client.delete('/api/nomina/1')
            assert r.status_code == 200, r.json
            cur.execute("SELECT COUNT(*) FROM asientos_contables WHERE modulo_origen='RRHH_ANULACION'")
            assert cur.fetchone()[0] == 1
            r = client.post('/api/nomina/generar',json={'mes':1,'anio':2026})
            assert r.status_code == 201, r.json
            nid = r.json['nomina_id']
            cur.execute("UPDATE empleados SET salario_base=20000,cargo='Otro' WHERE id=1")
            real.commit()
            r = client.get(f'/api/nomina/{nid}/empleado/1')
            assert r.json['colilla']['salario_contrato'] == 10000, r.json
            pago = dict(nomina_id=nid,empleado_id=1,monto_pagado=100,fecha_pago='2026-01-31',metodo_pago='Efectivo',numero_referencia='SMOKE-001')
            r = client.post('/api/rrhh/pagos-nomina',json=pago)
            assert r.status_code == 201, r.json
            assert client.post('/api/rrhh/pagos-nomina',json=pago).status_code == 409
            entrega = dict(empleado_id=1,tipo_equipo='Guantes',area='Bodega',cantidad=1,estado_equipo='Nuevo',fecha_entrega='2026-01-01')
            r = client.post('/api/rrhh/higiene/epp',json=entrega)
            assert r.status_code == 201, r.json
            entrega.update(repone_a_id=r.json['id'],motivo_reposicion='Desgaste',fecha_entrega='2026-02-01')
            r = client.post('/api/rrhh/higiene/epp',json=entrega)
            assert r.status_code == 201, r.json
            assert len(client.get('/api/rrhh/higiene/epp').json) == 2
            riesgo = dict(area='Bodega',tipo_riesgo='Caída de objetos',descripcion='Estantes',nivel_riesgo='Alto',medidas_preventivas='Fijación',responsable_seguimiento='Inventario',estado='Pendiente')
            r = client.post('/api/rrhh/higiene/riesgos',json=riesgo)
            assert r.status_code == 201, r.json
            rid = r.json['id']
            r = client.post(f'/api/rrhh/higiene/riesgos/{rid}/seguimiento',json=dict(fecha_revision='2026-01-01',observaciones='Revisión',estado='Controlado'))
            assert r.status_code == 201, r.json
            from io import BytesIO
            contenido = b'%PDF-1.4\nTest'
            r = client.post('/api/rrhh/expedientes/1',data={'tipo_documento':'Contrato','archivo':(BytesIO(contenido),'test.pdf')})
            assert r.status_code == 201, r.json
            aid = client.get('/api/rrhh/expedientes/1').json[0]['archivo_id']
            assert client.get(f'/api/rrhh/archivos/{aid}').data == contenido
        print('SQL Server OK: nomina, snapshot, pagos, EPP, reposiciones, riesgos, seguimientos y archivos privados. Solo tablas temporales.')
    finally:
        real.rollback()
        real.close()


if __name__ == '__main__':
    main()
