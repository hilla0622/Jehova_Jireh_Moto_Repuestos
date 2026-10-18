"""Regresiones de RRHH. SQLite en memoria: no se conecta a los datos del negocio.

El adaptador traduce únicamente sintaxis SQL Server; no prueba sus bloqueos.
"""
import re
import sqlite3
import unittest
from pathlib import Path
from unittest.mock import patch

import app as backend
from calculos_rrhh import calcular_nomina_empleado
from rrhh_service import dias_en_periodo, limites_periodo, normalizar_parametro


class Cursor:
    def __init__(self, db):
        self.raw = db.cursor()

    def execute(self, sql, params=()):
        sql = re.sub(r'WITH \(UPDLOCK, HOLDLOCK\)', '', sql)
        sql = sql.replace('@@IDENTITY', 'last_insert_rowid()')
        sql = sql.replace('ISNULL(', 'IFNULL(').replace('GETDATE()', 'CURRENT_TIMESTAMP')
        params = tuple(p.isoformat() if hasattr(p, 'isoformat') else p for p in params)
        self.raw.execute(sql, params)
        return self

    def __getattr__(self, key):
        return getattr(self.raw, key)


class Connection:
    def __init__(self, db):
        self.db = db

    def cursor(self):
        return Cursor(self.db)

    def commit(self):
        self.db.commit()

    def rollback(self):
        self.db.rollback()

    def close(self):
        self.db.rollback()


class RRHHTest(unittest.TestCase):
    def setUp(self):
        guard = patch.object(backend.pyodbc, 'connect', side_effect=AssertionError('Las pruebas no pueden abrir SQL Server.'))
        guard.start()
        self.addCleanup(guard.stop)
        self.db = sqlite3.connect(':memory:')
        source = (Path(__file__).parents[1] / 'database.sql').read_text(encoding='utf-8')
        tables = ('empleados', 'nomina', 'detalle_nomina', 'movimientos_laborales',
                  'horas_extras', 'parametros_laborales', 'cuentas_contables',
                  'asientos_contables', 'movimientos_contables', 'colilla_pago', 'pagos_nomina',
                  'expediente_empleado', 'higiene_epp', 'higiene_riesgos', 'higiene_riesgo_seguimientos', 'rrhh_archivos')
        for table in tables:
            body = re.search(r'CREATE TABLE \[' + table + r'\] \((.*?)\n\);', source, re.S)[1]
            lines = [line for line in body.splitlines() if 'CONSTRAINT' not in line]
            body = '\n'.join(lines).rstrip().rstrip(',')
            body = re.sub(r'int IDENTITY\(1,1\) NOT NULL', 'INTEGER PRIMARY KEY AUTOINCREMENT', body)
            body = body.replace('(getdate())', '(CURRENT_TIMESTAMP)')
            body = re.sub(r'(?:n?varchar|varbinary)\(MAX\)', 'BLOB', body, flags=re.I)
            self.db.execute(f'CREATE TABLE [{table}] ({body})')
        self.db.execute("""INSERT INTO empleados
            (nombre_completo, identificacion, cargo, salario_base, fecha_ingreso, activo, dias_vacaciones_disponibles)
            VALUES ('Empleado prueba','TEST-1','Mecánico',10000,'2025-01-01',1,10)""")
        for code in ('6.1.01','6.1.11','6.1.12','2.1.04','2.1.06','2.1.07','2.1.08'):
            self.db.execute("INSERT INTO cuentas_contables (codigo,nombre,clasificacion,naturaleza) VALUES (?,?,'Pasivo corriente','Acreedora')", (code, code))
        for code, value in [('INSS_LABORAL',7),('INSS_PATRONAL',21.5),('INATEC_PATRONAL',2),('VACACIONES_MES',2.5),('HORAS_EXTRAS_RECARGO',100)]:
            self.db.execute("INSERT INTO parametros_laborales (codigo,nombre,valor,unidad) VALUES (?,?,?,'%')", (code,code,value))
        self.db.commit()
        self.mock = patch.object(backend, 'get_db_connection', side_effect=lambda: Connection(self.db))
        self.mock.start()
        self.addCleanup(self.mock.stop)
        self.addCleanup(self.db.close)
        self.client = backend.app.test_client()
        self.login('Administrador')

    def login(self, role):
        with self.client.session_transaction() as s:
            s['user'] = {'id':1, 'rol':role, 'username':'test'}

    def generar(self, mes=1):
        return self.client.post('/api/nomina/generar', json={'mes':mes, 'anio':2026})

    def scalar(self, sql):
        return self.db.execute(sql).fetchone()[0]

    def test_nomina_horas_extra_asiento_y_duplicados(self):
        r = self.client.post('/api/rrhh/horas-extras', json={'empleado_id':1,'fecha':'2026-01-12','cantidad_horas':2})
        self.assertEqual(r.status_code, 201, r.json)
        result = self.generar()
        self.assertEqual(result.status_code, 201, result.json)
        extra = self.scalar('SELECT monto_total FROM horas_extras')
        self.assertEqual(self.scalar('SELECT ingresos_extra FROM detalle_nomina'), extra)
        self.assertAlmostEqual(self.scalar('SELECT SUM(debe)-SUM(haber) FROM movimientos_contables'), 0, places=2)
        self.assertEqual(self.generar().status_code, 400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM detalle_nomina'), 1)
        self.assertEqual(self.scalar('SELECT dias_vacaciones_disponibles FROM empleados'), 12.5)

    def test_ausencia_cruza_meses(self):
        self.db.execute("""INSERT INTO movimientos_laborales (empleado_id,tipo,fecha_inicio,fecha_fin,dias_tomados)
            VALUES (1,'PERMISO_SIN_GOCE','2026-01-30','2026-02-02',4)""")
        self.db.commit()
        for mes in (1,2):
            result = self.generar(mes)
            self.assertEqual(result.status_code, 201, result.json)
        self.assertEqual(self.db.execute('SELECT dias_permiso_sin_goce FROM detalle_nomina').fetchall(), [(2,), (2,)])

    def test_periodo_completamente_dentro_de_ausencia(self):
        d = dias_en_periodo('2026-01-15','2026-03-15',60,*limites_periodo(2,2026))
        self.assertEqual(d,28)

    def test_anular_revierte_contabilidad_y_permite_regenerar(self):
        r = self.generar()
        nid = r.json['nomina_id']
        r = self.client.delete(f'/api/nomina/{nid}')
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM detalle_nomina'),0)
        self.assertEqual(self.scalar('SELECT dias_vacaciones_disponibles FROM empleados'),10)
        for debe, haber in self.db.execute('SELECT SUM(debe),SUM(haber) FROM movimientos_contables GROUP BY cuenta_id'):
            self.assertAlmostEqual(debe, haber, places=2)
        self.assertEqual(self.generar().status_code,201)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM asientos_contables WHERE modulo_origen='RRHH_ANULACION'"),1)

    def test_no_anular_pagada(self):
        self.generar()
        self.db.execute("INSERT INTO pagos_nomina (nomina_id,empleado_id,monto_pagado,estado) VALUES (1,1,100,'Confirmado')")
        self.db.commit()
        self.assertEqual(self.client.delete('/api/nomina/1').status_code,409)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM nomina'),1)

    def test_anulacion_rollback_si_vacaciones_consumidas(self):
        self.generar()
        self.db.execute('UPDATE empleados SET dias_vacaciones_disponibles=0')
        self.db.commit()
        self.assertGreaterEqual(self.client.delete('/api/nomina/1').status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM nomina'),1)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM asientos_contables'),1)

    def test_parametro_editado_se_aplica(self):
        r = self.client.put('/api/rrhh/parametros/INSS_LABORAL',json={'valor':8})
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(self.generar().status_code,201)
        self.assertEqual(self.scalar('SELECT inss_laboral FROM detalle_nomina'),800)
        preview = self.client.get('/api/nomina/previsualizar?salario=10000')
        self.assertEqual(preview.json['inss_laboral'],800)
        self.assertEqual(self.client.put('/api/rrhh/parametros',json={'valor':5}).status_code,400)
        for value in (-1, 'nan', 101, None):
            self.assertEqual(self.client.put('/api/rrhh/parametros/INSS_LABORAL',json={'valor':value}).status_code,400)

    def test_parametros_legacy(self):
        self.db.execute('DROP TABLE parametros_laborales')
        self.db.execute('CREATE TABLE parametros_laborales (id INTEGER PRIMARY KEY, clave TEXT, nombre TEXT, valor REAL, unidad TEXT, fecha_vigencia TEXT, usuario_modifico TEXT)')
        self.db.execute("INSERT INTO parametros_laborales VALUES (1,'INSS_LABORAL','INSS',0.07,'%',NULL,NULL)")
        self.db.commit()
        self.assertEqual(self.client.get('/api/rrhh/parametros').json[0]['valor'],7)
        r = self.client.put('/api/rrhh/parametros/INSS_LABORAL',json={'valor':8})
        self.assertEqual(r.status_code,200,r.json)
        self.assertEqual(self.scalar('SELECT valor FROM parametros_laborales'),0.08)
        self.assertEqual(self.generar().status_code,201)
        self.assertEqual(self.scalar('SELECT inss_laboral FROM detalle_nomina'),800)
        p = normalizar_parametro({'clave':'RECARGO_HORA_EXTRA','valor':2,'unidad':'factor'})
        self.assertEqual((p['codigo'],p['valor']),('HORAS_EXTRAS_RECARGO',100))

    def test_permisos(self):
        self.login('Vendedor')
        for url in ('/api/empleados','/api/rrhh/solicitudes','/api/rrhh/expedientes/1','/api/nomina/historial','/rrhh/colilla/1'):
            self.assertEqual(self.client.get(url).status_code,403,url)
        self.login('Gerente Administrativo y Financiero')
        self.assertEqual(self.generar().status_code,201)

    def test_rollback_cuenta_inactiva(self):
        self.db.execute("UPDATE cuentas_contables SET activo=0 WHERE codigo='6.1.11'")
        self.db.commit()
        self.assertGreaterEqual(self.generar().status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM nomina'),0)
        self.assertEqual(self.scalar('SELECT dias_vacaciones_disponibles FROM empleados'),10)

    def test_crea_cuentas_faltantes(self):
        self.db.execute("DELETE FROM cuentas_contables WHERE codigo NOT IN ('6.1.01','2.1.04')")
        self.db.commit()
        r = self.generar()
        self.assertEqual(r.status_code,201,r.json)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM cuentas_contables'),8)
        self.assertAlmostEqual(self.scalar('SELECT SUM(debe)-SUM(haber) FROM movimientos_contables'),0,places=2)

    def test_sin_empleados_elegibles_y_periodo_invalido(self):
        self.assertEqual(self.generar(13).status_code,400)
        self.db.execute("UPDATE empleados SET fecha_ingreso='2027-01-01'")
        self.db.commit()
        self.assertEqual(self.generar().status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM nomina'),0)

    def test_horas_pendientes_no_se_pagan(self):
        self.db.execute("""INSERT INTO horas_extras
            (empleado_id,fecha,cantidad_horas,valor_hora_ordinaria,monto_total,estado)
            VALUES (1,'2026-01-12',2,50,200,'Pendiente')""")
        self.db.commit()
        self.assertEqual(self.generar().status_code,201)
        self.assertEqual(self.scalar('SELECT ingresos_extra FROM detalle_nomina'),0)

    def test_cuenta_inatec_ocupada_no_se_reutiliza(self):
        self.db.execute("""INSERT INTO cuentas_contables (codigo,nombre,clasificacion,naturaleza)
            VALUES ('2.1.10','Préstamo','Pasivo corriente','Acreedora')""")
        self.db.commit()
        r = self.generar()
        self.assertGreaterEqual(r.status_code,400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM nomina'),0)

    def test_complemento_y_anulacion_de_todos_los_asientos(self):
        self.generar()
        self.db.execute("""INSERT INTO empleados
            (nombre_completo, identificacion, cargo, salario_base, fecha_ingreso, activo, dias_vacaciones_disponibles)
            VALUES ('Segundo','TEST-2','Mecánico',12000,'2025-01-01',1,0)""")
        self.db.commit()
        self.assertEqual(self.generar().status_code,201)
        self.assertEqual(self.scalar('SELECT total_ingresos FROM nomina'),22000)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM detalle_nomina'),2)
        self.assertEqual(self.client.delete('/api/nomina/1').status_code,200)
        self.assertEqual(self.scalar("SELECT COUNT(*) FROM asientos_contables WHERE modulo_origen='RRHH_ANULACION'"),2)

    def test_recargo_configurable(self):
        r = self.client.put('/api/rrhh/parametros/HORAS_EXTRAS_RECARGO',json={'valor':50})
        self.assertEqual(r.status_code,200)
        r = self.client.post('/api/rrhh/horas-extras',json={'empleado_id':1,'fecha':'2026-01-12','cantidad_horas':2})
        self.assertEqual(r.status_code,201,r.json)
        self.assertEqual(self.scalar('SELECT monto_total FROM horas_extras'),125.01)

    def pago(self, **changes):
        data = dict(nomina_id=1, empleado_id=1, monto_pagado='100', fecha_pago='2026-01-31',
                    metodo_pago='Transferencia Bancaria', numero_referencia='TRF-001')
        data.update(changes)
        return self.client.post('/api/rrhh/pagos-nomina', json=data)

    def test_pagos_parciales_duplicados_sobrepago_y_anulacion(self):
        self.generar()
        neto = self.scalar('SELECT neto_pagar FROM detalle_nomina')
        r = self.pago()
        self.assertEqual(r.status_code, 201, r.json)
        self.assertEqual(self.scalar('SELECT registrado_por FROM pagos_nomina'), 'test')
        self.assertEqual(self.pago().status_code, 409)
        self.assertEqual(self.pago(monto_pagado=neto, numero_referencia='TRF-002').status_code, 409)
        self.assertEqual(self.pago(monto_pagado=neto-100, numero_referencia='TRF-002').status_code, 201)
        self.assertEqual(self.pago(numero_referencia='TRF-003').status_code, 409)
        self.assertEqual(self.client.delete('/api/nomina/1').status_code, 409)
        self.assertEqual(self.scalar('SELECT SUM(monto_pagado) FROM pagos_nomina'), neto)

    def test_pago_invalido_no_se_guarda(self):
        self.generar()
        for importe in ('NaN', 'Infinity', '-1', '0', '1.001', '99999999999999999999999999999999999999', None):
            self.assertEqual(self.pago(monto_pagado=importe).status_code, 400, importe)
        self.assertEqual(self.pago(empleado_id=987).status_code, 400)
        self.assertEqual(self.pago(nomina_id=987).status_code, 404)
        self.assertEqual(self.pago(fecha_pago='incorrecta').status_code, 400)
        self.assertEqual(self.pago(numero_referencia='').status_code, 400)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM pagos_nomina'), 0)

    def test_colilla_conserva_snapshot_y_nulos_originales(self):
        self.generar()
        self.db.execute("UPDATE empleados SET salario_base=20000,cargo='Gerente',nombre_completo='Otro nombre',num_inss='123'")
        self.db.commit()
        r = self.client.get('/api/nomina/1/empleado/1')
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(r.json['colilla']['salario_contrato'], 10000)
        self.assertEqual(r.json['colilla']['cargo'], 'Mecánico')
        self.assertIsNone(r.json['colilla']['num_inss'])
        d = self.client.get('/api/nomina/1/detalle').json['detalles'][0]
        self.assertEqual(d['empleado'], 'Empleado prueba')
        self.assertEqual(d['historico_incompleto'], 0)
        html = self.client.get('/rrhh/colilla/1').text
        self.assertIn('Empleado prueba', html)
        self.assertNotIn('Otro nombre', html)

    def test_colilla_cero_dias_y_vacaciones_no_usa_predeterminados(self):
        self.generar()
        self.db.execute('UPDATE detalle_nomina SET dias_trabajados=0, vac_mes=0')
        self.db.commit()
        with patch.object(backend, 'render_template', side_effect=lambda name, **data: data):
            r = self.client.get('/rrhh/colilla/1')
            self.assertEqual(r.json['c']['dias_trabajados'], 0)
            self.assertEqual(r.json['c']['vac_mes'], 0)
        self.db.execute('UPDATE detalle_nomina SET historico_salario=NULL')
        self.db.commit()
        self.assertIn('Registro anterior sin copia', self.client.get('/rrhh/colilla/1').text)

    def test_archivo_real_privado_y_referencia_antigua(self):
        from io import BytesIO
        contenido = b'%PDF-1.4\nDocumento de prueba'
        r = self.client.post('/api/rrhh/expedientes/1', data={
            'tipo_documento':'Contrato', 'observaciones':'Firmado', 'archivo':(BytesIO(contenido),'contrato.pdf')})
        self.assertEqual(r.status_code, 201, r.json)
        rows = self.client.get('/api/rrhh/expedientes/1').json
        aid = rows[0]['archivo_id']
        download = self.client.get(f'/api/rrhh/archivos/{aid}')
        self.assertEqual(download.data, contenido)
        self.assertEqual(download.headers['Cache-Control'], 'no-store')
        self.login('Vendedor')
        self.assertEqual(self.client.get(f'/api/rrhh/archivos/{aid}').status_code, 403)
        self.login('Administrador')
        self.db.execute("INSERT INTO expediente_empleado (empleado_id,tipo_documento,nombre_archivo) VALUES (1,'Referencia','viejo.pdf')")
        self.db.commit()
        self.assertIsNone(self.client.get('/api/rrhh/expedientes/1').json[0]['archivo_id'])
        self.assertEqual(self.client.delete(f"/api/rrhh/expedientes/doc/{rows[0]['id']}").status_code, 200)
        self.assertEqual(self.client.get(f'/api/rrhh/archivos/{aid}').status_code, 404)

    def test_archivo_invalido_o_excesivo_no_crea_documento(self):
        from io import BytesIO
        for filename, contenido in [('falso.pdf', b'<script>bad</script>'), ('test.pdf', b'%PDF-'+b'a'*(5*1024*1024))]:
            r = self.client.post('/api/rrhh/expedientes/1', data={'tipo_documento':'Contrato', 'archivo':(BytesIO(contenido),filename)})
            self.assertEqual(r.status_code, 400, r.json)
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM expediente_empleado'), 0)

    def entrega(self, **changes):
        data = dict(empleado_id=1, tipo_equipo='Guantes de protección mecánica', area='Bodega / Almacén',
                    cantidad=2, estado_equipo='Nuevo', fecha_entrega='2026-01-01', fecha_reposicion_sugerida='2026-06-01')
        data.update(changes)
        return self.client.post('/api/rrhh/higiene/epp', json=data)

    def test_reposicion_preserva_entrega_y_evitar_duplicados(self):
        self.assertEqual(self.entrega().status_code, 201)
        r = self.entrega(repone_a_id=1, motivo_reposicion='Deterioro', fecha_entrega='2026-02-01')
        self.assertEqual(r.status_code, 201, r.json)
        self.assertEqual(self.entrega(repone_a_id=1, motivo_reposicion='Deterioro').status_code, 409)
        rows = self.client.get('/api/rrhh/higiene/epp').json
        original = next(r for r in rows if r['id']==1)
        self.assertEqual(original['reposicion_id'], 2)
        self.assertEqual(original['fecha_entrega'], '2026-01-01')
        self.assertEqual(original['estado_equipo'], 'Nuevo')
        self.assertEqual(self.scalar('SELECT COUNT(*) FROM higiene_epp'), 2)

    def test_validaciones_epp(self):
        for changes in [dict(cantidad=0),dict(cantidad=1.5),dict(empleado_id=999),dict(estado_equipo='Dañado'),
                        dict(fecha_reposicion_sugerida='2025-01-01'),dict(tipo_equipo=''),dict(repone_a_id=1)]:
            self.assertEqual(self.entrega(**changes).status_code, 400, changes)
        self.entrega()
        self.assertEqual(self.entrega(repone_a_id=1,motivo_reposicion='Cambio',cantidad=1).status_code,400)
        self.assertEqual(self.entrega(repone_a_id=1,motivo_reposicion='Cambio',fecha_entrega='2025-12-01').status_code,400)

    def test_riesgos_edicion_seguimiento_y_fechas_atrasadas(self):
        data = dict(area='Bodega', tipo_riesgo='Caída de objetos', descripcion='Estantería', nivel_riesgo='Alto',
                    medidas_preventivas='Asegurar estantes', responsable_seguimiento='Inventario', estado='Pendiente')
        r = self.client.post('/api/rrhh/higiene/riesgos', json=data)
        self.assertEqual(r.status_code, 201, r.json)
        rid = r.json['id']
        data['medidas_preventivas'] = 'Inspección y fijación'
        self.assertEqual(self.client.put(f'/api/rrhh/higiene/riesgos/{rid}',json=data).status_code,200)
        url = f'/api/rrhh/higiene/riesgos/{rid}/seguimiento'
        for dia, estado in [('2026-02-01','Controlado'),('2026-01-01','Pendiente')]:
            r = self.client.post(url,json=dict(fecha_revision=dia,estado=estado,observaciones='Revisión documentada'))
            self.assertEqual(r.status_code,201,r.json)
        self.assertEqual(len(self.client.get(url).json),2)
        row = self.client.get('/api/rrhh/higiene/riesgos').json[0]
        self.assertEqual(row['estado'],'Controlado')
        self.assertEqual(row['fecha_revision'],'2026-02-01')
        self.login('Vendedor')
        self.assertEqual(self.client.post(url,json={}).status_code,403)


if __name__ == '__main__':
    unittest.main()
