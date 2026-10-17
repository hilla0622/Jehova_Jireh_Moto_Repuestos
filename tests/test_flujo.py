"""Regresiones RF96-RF102. Datos sintéticos; nunca conectan a la base del negocio.

Las pruebas de rutas usan SQLite en memoria con una adaptación mínima de sintaxis;
no sustituyen la prueba de migración en una copia de SQL Server.
"""
import json
import re
import sqlite3
import unittest
from decimal import Decimal
from pathlib import Path

from flask import Flask
from flujo_service import calcular_flujo, calcular_conciliacion, dinero, validar_distribucion
from routes_flujo_efectivo import register_flujo_efectivo_routes

CUENTAS = {
    1: ('1.1.01', 'Caja', 'Activo corriente', 'Efectivo_Equivalente', 1, 0),
    2: ('1.1.02', 'Bancos', 'Activo corriente', 'Efectivo_Equivalente', 1, 0),
    3: ('1.1.03', 'Clientes', 'Activo corriente', 'Operacion', 0, 0),
    4: ('1.1.04', 'Inventario', 'Activo corriente', 'Operacion', 0, 0),
    5: ('1.2.01', 'Equipo', 'Activo no corriente', 'Inversion', 0, 0),
    6: ('1.2.03', 'Depreciación acumulada', 'Activo no corriente - contraactivo', 'Inversion', 0, 0),
    7: ('2.1.01', 'Proveedores', 'Pasivo corriente', 'Operacion', 0, 0),
    8: ('2.1.02', 'Documento por pagar', 'Pasivo corriente', 'Financiamiento', 0, 0),
    9: ('3.1.01', 'Capital', 'Patrimonio', 'Financiamiento', 0, 0),
    10: ('4.1.01', 'Ventas', 'Ingresos', 'Operacion', 0, 0),
    11: ('5.1.01', 'Costo de ventas', 'Costo', 'Operacion', 0, 0),
    12: ('6.1.09', 'Depreciación', 'Gasto', 'Operacion', 0, 1),
    13: ('6.1.10', 'Comisiones', 'Gasto', 'Operacion', 0, 0),
    14: ('2.1.09', 'Provisión litigios', 'Pasivo corriente', 'Operacion', 0, 0),
    15: ('6.1.11', 'Gasto provisión', 'Gasto', 'Operacion', 0, 1),
}


def asiento(aid, lineas, f='2026-10-10'):
    result = []
    for idx, (cid, d, h) in enumerate(lineas, 1):
        c = CUENTAS[cid]
        result.append(dict(asiento_id=aid, movimiento_id=aid * 100 + idx, cuenta_id=cid, fecha=f,
                           concepto=f'Asiento {aid}', modulo_origen='MANUAL', debe=dinero(d), haber=dinero(h),
                           codigo=c[0], nombre=c[1], clasificacion=c[2], flujo_categoria=c[3],
                           es_efectivo=c[4], ajuste_no_monetario=c[5]))
    return result


APERTURA = asiento(1, [(2, 10000, 0), (9, 0, 10000)], '2026-09-01')


class CalculosTest(unittest.TestCase):
    def flujo(self, movs, metodo='Directo', **kwargs):
        return calcular_flujo(APERTURA + movs, '2026-10-01', '2026-10-31', metodo, **kwargs)

    def test_operaciones_basicas_ambos_metodos(self):
        casos = [([(2, 200, 0), (10, 0, 200)], (200, 0, 0)),
                 ([(13, 100, 0), (2, 0, 100)], (-100, 0, 0)),
                 ([(2, 1000, 0), (8, 0, 1000)], (0, 0, 1000)),
                 ([(5, 1000, 0), (2, 0, 1000)], (0, -1000, 0)),
                 ([(5, 10000, 0), (8, 0, 8000), (2, 0, 2000)], (0, -2000, 0)),
                 ([(5, 10000, 0), (8, 0, 10000)], (0, 0, 0)),
                 ([(5, 10000, 0), (7, 0, 10000)], (0, 0, 0)),
                 ([(3, 100, 0), (10, 0, 100)], (0, 0, 0)),
                 ([(2, 100, 0), (3, 0, 100)], (100, 0, 0)),
                 ([(7, 100, 0), (2, 0, 100)], (-100, 0, 0)),
                 ([(12, 100, 0), (6, 0, 100)], (0, 0, 0)),
                 ([(15, 100, 0), (14, 0, 100)], (0, 0, 0)),
                 ([(1, 100, 0), (2, 0, 100)], (0, 0, 0))]
        for lineas, esperado in casos:
            for metodo in ('Directo', 'Indirecto'):
                with self.subTest(lineas=lineas, metodo=metodo):
                    d = self.flujo(asiento(2, lineas), metodo)
                    self.assertEqual(tuple(d['flujo_neto_' + k] for k in ('operacion', 'inversion', 'financiamiento')), esperado)
                    self.assertTrue(d['puede_guardar'], d)

    def test_venta_con_costo_no_inventa_efectivo(self):
        d = self.flujo(asiento(2, [(2, 200, 0), (10, 0, 200), (11, 100, 0), (4, 0, 100)]), 'Indirecto')
        self.assertEqual(d['indirecto_data']['utilidad_neta'], 100)
        self.assertEqual(d['flujo_neto_operacion'], 200)
        self.assertTrue(d['puede_guardar'])

    def test_venta_activo_ganancia_exige_criterio_y_aplica_distribucion(self):
        movs = asiento(2, [(2, 9000, 0), (6, 3000, 0), (5, 0, 10000), (10, 0, 2000)])
        self.assertFalse(self.flujo(movs)['puede_guardar'])
        for metodo in ('Directo', 'Indirecto'):
            d = self.flujo(movs, metodo, distribuciones={2: [{'actividad': 'Inversion', 'importe': 9000}]})
            self.assertEqual(d['flujo_neto_inversion'], 9000)
            self.assertEqual(d['flujo_neto_operacion'], 0)
            self.assertTrue(d['puede_guardar'])

    def test_transferencia_con_comision(self):
        movs = asiento(2, [(1, 100, 0), (13, 2, 0), (2, 0, 102)])
        self.assertFalse(self.flujo(movs)['puede_guardar'])
        d = self.flujo(movs, distribuciones={2: [{'actividad': 'Operacion', 'importe': -2}]})
        self.assertEqual(d['flujo_neto_operacion'], -2)
        self.assertTrue(d['puede_guardar'])

    def test_no_netea_cobros_y_pagos(self):
        d = self.flujo(asiento(2, [(2, 200, 0), (10, 0, 200)]) + asiento(3, [(13, 100, 0), (2, 0, 100)]))
        self.assertEqual([i['importe'] for i in d['actividades_operacion']], [200, -100])

    def test_centavos_fechas_y_saldos(self):
        d = self.flujo(asiento(2, [(2, '0.10', 0), (10, 0, '0.10')]) + asiento(3, [(2, '0.20', 0), (10, 0, '0.20')]) + asiento(4, [(2, 99, 0), (10, 0, 99)], '2026-11-01'))
        self.assertEqual(d['saldo_inicial'], 10000)
        self.assertEqual(d['saldo_final_balance'], 10000.30)
        self.assertEqual(d['diferencia_cuadratura'], 0)
        for valor in ('nan', 'Infinity', '0.001'):
            with self.assertRaises(ValueError): dinero(valor)
        with self.assertRaises(ValueError):
            calcular_flujo([], '2026-10-31', '2026-10-01', 'Directo')

    def test_ajuste_manual_sustituye_automatico(self):
        movs = asiento(2, [(12, 100, 0), (6, 0, 100)])
        d = self.flujo(movs, 'Indirecto', ajustes={201: {'importe': 100, 'motivo': 'Revisado'}})
        self.assertEqual(d['indirecto_data']['total_ajustes'], 100)
        self.assertTrue(d['puede_guardar'])
        d = self.flujo(movs, 'Indirecto', ajustes={201: {'importe': 50, 'motivo': 'Error manual'}})
        self.assertFalse(d['puede_guardar'])
        self.assertEqual(d['diferencia_entre_metodos'], -50)

    def test_cuenta_nueva_no_se_clasifica_silenciosamente(self):
        movs = asiento(2, [(2, 100, 0), (10, 0, 100)])
        movs[1]['flujo_categoria'] = None
        self.assertFalse(self.flujo(movs)['puede_guardar'])

    def test_distribucion_no_puede_inventar_dinero(self):
        movs = asiento(2, [(2, 100, 0), (10, 0, 100)])
        with self.assertRaises(ValueError):
            validar_distribucion(movs, [{'actividad': 'Inversion', 'importe': 200}, {'actividad': 'Financiamiento', 'importe': -100}])

    def test_conciliacion_signos_y_resueltas(self):
        def p(tipo, importe, **kw):
            return dict(tipo_partida=tipo, monto=importe, fecha='2026-10-10', numero_documento_referencia='REF', descripcion='Prueba', **kw)
        d = calcular_conciliacion(1000, 900, [p('Deposito en Transito', 200), p('Cheque en Transito', 100)], '2026-10-31')
        self.assertEqual(d['diferencia'], 0)
        d = calcular_conciliacion(1000, 1050, [p('Nota de Credito', 100), p('Nota de Debito', 50)], '2026-10-31')
        self.assertEqual(d['diferencia'], 0)
        d = calcular_conciliacion(900, 1000, [p('Error en Libros', 100, efecto_en_saldo='Suma')], '2026-10-31')
        self.assertEqual(d['saldo_libros_ajustado'], 1000)
        self.assertEqual(d['saldo_banco_ajustado'], 1000)
        d = calcular_conciliacion(1000, 1000, [p('Cheque en Transito', 100, esta_conciliada=True)], '2026-10-31')
        self.assertEqual(d['diferencia'], 0)
        with self.assertRaises(ValueError):
            calcular_conciliacion(0, 0, [p('Cheque en Transito', -100)], '2026-10-31')


SCHEMA = '''
CREATE TABLE usuarios (id INTEGER PRIMARY KEY, nombre_completo TEXT);
INSERT INTO usuarios VALUES (1, 'Contador de prueba');
CREATE TABLE cuentas_contables (id INTEGER PRIMARY KEY, codigo TEXT, nombre TEXT, clasificacion TEXT,
    flujo_categoria TEXT, es_efectivo_equivalente INTEGER, ajuste_no_monetario INTEGER);
CREATE TABLE asientos_contables (id INTEGER PRIMARY KEY, fecha TEXT, concepto TEXT, modulo_origen TEXT, referencia_id INTEGER, usuario_id INTEGER);
CREATE TABLE movimientos_contables (id INTEGER PRIMARY KEY, asiento_id INTEGER, cuenta_id INTEGER, debe NUMERIC, haber NUMERIC);
CREATE TABLE flujo_eventos (id INTEGER PRIMARY KEY, tipo TEXT, clave TEXT, contenido TEXT, motivo TEXT, usuario_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
CREATE TABLE conciliaciones_bancarias (id INTEGER PRIMARY KEY, cuenta_id INTEGER, anio INTEGER, mes INTEGER,
    fecha_corte TEXT, saldo_segun_libros NUMERIC, saldo_segun_banco NUMERIC, diferencia NUMERIC, estado TEXT,
    observaciones TEXT, usuario_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(cuenta_id,anio,mes));
CREATE TABLE conciliacion_partidas_pendientes (id INTEGER PRIMARY KEY, conciliacion_id INTEGER, tipo_partida TEXT,
    fecha TEXT, numero_documento_referencia TEXT, descripcion TEXT, monto NUMERIC, efecto_en_saldo TEXT,
    esta_conciliada INTEGER, movimiento_contable_id INTEGER);
CREATE TABLE estados_flujo_efectivo (id INTEGER PRIMARY KEY, ejercicio_fiscal INTEGER, periodo_tipo TEXT,
    fecha_inicio TEXT, fecha_fin TEXT, metodo TEXT, saldo_inicial_efectivo NUMERIC, flujo_neto_operacion NUMERIC,
    flujo_neto_inversion NUMERIC, flujo_neto_financiamiento NUMERIC, variacion_neta_efectivo NUMERIC,
    saldo_final_calculado NUMERIC, saldo_final_balance_general NUMERIC, diferencia_cuadratura NUMERIC,
    esta_cuadrado INTEGER, estado TEXT, observaciones TEXT, usuario_elaboro_id INTEGER);
CREATE TABLE estado_flujo_efectivo_detalle (id INTEGER PRIMARY KEY, flujo_id INTEGER, actividad TEXT, concepto TEXT,
    tipo_movimiento TEXT, importe NUMERIC, orden_presentacion INTEGER);
CREATE TABLE flujo_ajustes_no_monetarios (id INTEGER PRIMARY KEY, flujo_id INTEGER, concepto TEXT, efecto TEXT,
    importe NUMERIC, justificacion TEXT, usuario_id INTEGER);
CREATE TABLE flujo_reclasificaciones_auditoria (id INTEGER PRIMARY KEY, asiento_id INTEGER, origen_modulo TEXT,
    actividad_anterior TEXT, actividad_nueva TEXT, motivo_reclasificacion TEXT, usuario_id INTEGER, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
'''


class CursorAdapter:
    def __init__(self, db): self.cursor = db.cursor()
    def execute(self, sql, params=()):
        if sql.startswith('SET TRANSACTION'): return self
        returning = 'OUTPUT INSERTED.id' in sql
        sql = sql.replace('OUTPUT INSERTED.id', '')
        sql = re.sub(r'CAST\(a.fecha AS DATE\)', 'date(a.fecha)', sql)
        if returning: sql += ' RETURNING id'
        self.cursor.execute(sql, tuple(str(p) if isinstance(p, Decimal) else p for p in params))
        return self
    @property
    def description(self): return self.cursor.description
    def fetchall(self): return self.cursor.fetchall()
    def fetchone(self): return self.cursor.fetchone()


class ConnectionAdapter:
    def __init__(self, db): self.db = db
    def cursor(self): return CursorAdapter(self.db)
    def commit(self): self.db.commit()
    def rollback(self): self.db.rollback()
    def close(self): pass


class ApiTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript(SCHEMA)
        self.db.executemany('INSERT INTO cuentas_contables VALUES (?,?,?,?,?,?,?)', [(k, *v) for k,v in CUENTAS.items()])
        self.insert(APERTURA)
        self.app = Flask(__name__)
        self.app.template_folder = str(Path(__file__).resolve().parents[1] / 'Fronted/templates')
        self.app.secret_key = 'tests'
        self.app.config['GET_DB_CONNECTION'] = lambda: ConnectionAdapter(self.db)
        register_flujo_efectivo_routes(self.app)
        self.client = self.app.test_client()
        with self.client.session_transaction() as s: s['user'] = {'id': 1, 'rol': 'Contador'}

    def tearDown(self): self.db.close()

    def insert(self, movs):
        m = movs[0]
        self.db.execute('INSERT INTO asientos_contables (id, fecha, concepto, modulo_origen) VALUES (?,?,?,?)',
                        (m['asiento_id'], m['fecha'], m['concepto'], m['modulo_origen']))
        self.db.executemany('INSERT INTO movimientos_contables VALUES (?,?,?,?,?)',
                            [(m['movimiento_id'], m['asiento_id'], m['cuenta_id'], str(m['debe']), str(m['haber'])) for m in movs])
        self.db.commit()

    def reporte(self, metodo='Directo'):
        r = self.client.get('/api/finanzas/flujo_efectivo', query_string={'start': '2026-10-01', 'end': '2026-10-31', 'metodo': metodo})
        self.assertEqual(r.status_code, 200, r.json)
        return r.json

    def conc(self, mes=10):
        r = self.client.get('/api/finanzas/conciliacion/datos', query_string={'cuenta_id': 2, 'anio': 2026, 'mes': mes})
        self.assertEqual(r.status_code, 200, r.json)
        return r.json

    def post_conc(self, ctx, **kw):
        payload = dict(cuenta_id=2, anio=2026, mes=ctx['mes'], revision=ctx['revision'], saldo_segun_banco=10000,
                       partidas=ctx['partidas_pendientes'])
        payload.update(kw)
        return self.client.post('/api/finanzas/conciliacion/guardar', json=payload)

    def test_guardado_recalcula_y_conserva_indirecto(self):
        self.insert(asiento(2, [(12, 100, 0), (6, 0, 100)]))
        d = self.reporte('Indirecto')
        r = self.client.post('/api/finanzas/flujo_efectivo/guardar', json=dict(fecha_inicio='2026-10-01', fecha_fin='2026-10-31', metodo='Indirecto', revision=d['revision'], saldo_inicial_efectivo=999, flujo_neto_operacion=999))
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(self.db.execute('SELECT saldo_inicial_efectivo,flujo_neto_operacion FROM estados_flujo_efectivo').fetchone(), (10000, 0))
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM flujo_ajustes_no_monetarios').fetchone()[0], 1)
        snapshot = self.client.get('/api/finanzas/flujo_efectivo/cortes').json['cortes'][str(r.json['flujo_id'])]
        self.assertEqual(snapshot['indirecto_data']['utilidad_neta'], -100)

    def test_guardar_sin_revision_o_con_mayor_modificado_rechazado(self):
        d = self.reporte()
        payload = dict(fecha_inicio='2026-10-01', fecha_fin='2026-10-31', revision=d['revision'])
        self.insert(asiento(2, [(2, 10, 0), (10, 0, 10)]))
        self.assertEqual(self.client.post('/api/finanzas/flujo_efectivo/guardar', json=payload).status_code, 409)
        self.assertEqual(self.client.post('/api/finanzas/flujo_efectivo/guardar', json={}).status_code, 409)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM estados_flujo_efectivo').fetchone()[0], 0)

    def test_conciliacion_no_confia_en_diferencia_cliente(self):
        r = self.post_conc(self.conc(), saldo_segun_banco=1, diferencia=0, estado='Conciliada', saldo_segun_libros=1)
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(r.json['resumen']['estado'], 'Borrador')
        self.assertEqual(r.json['resumen']['diferencia'], -9999)
        self.assertEqual(r.json['resumen']['saldo_segun_libros'], 10000)

    def test_pendientes_continuidad_resolucion_y_lectura_historica(self):
        partida = dict(uid='cheque-1', tipo_partida='Cheque en Transito', fecha='2026-10-10',
                       numero_documento_referencia='CH-1', descripcion='Cheque pendiente', monto=100,
                       efecto_en_saldo='Resta', esta_conciliada=False)
        r = self.post_conc(self.conc(), partidas=[partida], saldo_segun_banco=10100)
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(r.json['resumen']['estado'], 'Conciliada')
        nov = self.conc(11)
        self.assertEqual(nov['partidas_pendientes'][0]['uid'], 'cheque-1')
        self.assertTrue(nov['partidas_pendientes'][0]['heredada'])
        self.assertEqual(self.post_conc(nov, partidas=[]).status_code, 400)
        nov['partidas_pendientes'][0].update(esta_conciliada=True, resolucion='Cobrado según extracto noviembre')
        r = self.post_conc(nov)
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(self.conc(12)['partidas_pendientes'], [])
        self.assertTrue(self.conc()['solo_lectura'])
        self.assertEqual(self.post_conc(self.conc()).status_code, 400)
        self.assertEqual(self.db.execute("SELECT COUNT(*) FROM flujo_eventos WHERE tipo='conciliacion'").fetchone()[0], 2)

    def test_conciliacion_revision_evitar_sobreescritura(self):
        ctx = self.conc()
        self.assertEqual(self.post_conc(ctx).status_code, 200)
        self.assertEqual(self.post_conc(ctx).status_code, 409)

    def test_configuracion_y_regla_se_aplican_y_auditan(self):
        self.insert(asiento(2, [(2, 100, 0), (10, 0, 100)]))
        r = self.client.post('/api/finanzas/flujo/configuracion', json=dict(tipo='regla', modulo_origen='MANUAL', actividad='Inversion', motivo='Prueba de regla'))
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(self.reporte()['flujo_neto_inversion'], 100)
        self.assertEqual(len(self.client.get('/api/finanzas/flujo/auditoria').json['eventos']), 1)

    def test_reclasificacion_aplicada_no_solo_auditoria(self):
        self.insert(asiento(2, [(2, 9000, 0), (6, 3000, 0), (5, 0, 10000), (10, 0, 2000)]))
        a = self.client.get('/api/finanzas/flujo/asiento/2').json
        r = self.client.post('/api/finanzas/reclasificaciones', json=dict(asiento_id=2, revision=a['revision'], actividad_nueva='Inversion', motivo='Venta de equipo'))
        self.assertEqual(r.status_code, 200, r.json)
        self.assertTrue(self.reporte('Indirecto')['puede_guardar'])
        self.assertEqual(self.reporte()['flujo_neto_inversion'], 9000)

    def test_correccion_diferencia_conserva_original_y_evitar_duplicado(self):
        self.insert(asiento(2, [(13, 100, 0), (2, 0, 100)]))
        a = self.client.get('/api/finanzas/flujo/asiento/2').json
        payload = dict(asiento_id=2, revision=a['revision'], fecha='2026-10-11', motivo='Importe correcto 150',
                       movimientos=[dict(cuenta_id=13, debe=150, haber=0), dict(cuenta_id=2, debe=0, haber=150)])
        r = self.client.post('/api/finanzas/flujo/correcciones', json=payload)
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(self.db.execute('SELECT haber FROM movimientos_contables WHERE id=202').fetchone()[0], 100)
        self.assertEqual(self.reporte()['flujo_neto_operacion'], -150)
        self.assertEqual(self.client.post('/api/finanzas/flujo/correcciones', json=payload).status_code, 400)

    def test_ajustes_reemplazan_y_restauran(self):
        self.insert(asiento(2, [(12, 100, 0), (6, 0, 100)]))
        for importe, restaurar, esperado in [(50, False, -50), (100, False, 0), (0, True, 0)]:
            r = self.client.post('/api/finanzas/flujo/ajustes', json=dict(movimiento_id=201, importe=importe, restaurar=restaurar, motivo='Revisión de depreciación'))
            self.assertEqual(r.status_code, 200, r.json)
            self.assertEqual(self.reporte('Indirecto')['flujo_neto_operacion'], esperado)

    def test_correccion_de_cuenta_requiere_confirmar_actividad(self):
        self.insert(asiento(2, [(13, 100, 0), (2, 0, 100)]))
        a = self.client.get('/api/finanzas/flujo/asiento/2').json
        r = self.client.post('/api/finanzas/flujo/correcciones', json=dict(asiento_id=2, revision=a['revision'],
            fecha='2026-10-10', motivo='Era equipo, no comisión',
            movimientos=[dict(cuenta_id=5, debe=100, haber=0), dict(cuenta_id=2, debe=0, haber=100)]))
        self.assertEqual(r.status_code, 200, r.json)
        self.assertFalse(self.reporte()['puede_guardar'])
        r = self.client.post('/api/finanzas/reclasificaciones', json=dict(asiento_id=2, revision=a['revision'],
            actividad_nueva='Inversion', motivo='Confirmación posterior a la corrección'))
        self.assertEqual(r.status_code, 200, r.json)
        for metodo in ('Directo', 'Indirecto'):
            d = self.reporte(metodo)
            self.assertTrue(d['puede_guardar'], d)
            self.assertEqual(d['flujo_neto_operacion'], 0)
            self.assertEqual(d['flujo_neto_inversion'], -100)

    def test_autorizacion_y_fechas_invalidas(self):
        self.assertEqual(self.client.get('/api/finanzas/conciliacion/datos?anio=2026&mes=13').status_code, 400)
        with self.client.session_transaction() as s: s['user'] = {'id': 1, 'rol': 'Vendedor'}
        self.assertEqual(self.client.get('/api/finanzas/flujo/configuracion').status_code, 403)
        with self.client.session_transaction() as s: s.clear()
        self.assertEqual(self.client.get('/api/finanzas/flujo/configuracion').status_code, 401)

    def test_exportacion_cuatro_estados_y_fecha_corte(self):
        self.insert(asiento(2, [(2, 200, 0), (10, 0, 200)]))
        self.insert(asiento(3, [(2, 999, 0), (10, 0, 999)], '2026-11-01'))
        for tipo in ('flujo', 'resultados', 'balance', 'comprobacion'):
            r = self.client.get(f'/api/finanzas/reportes/exportar/{tipo}?start=2026-10-01&end=2026-10-31&descargar=1')
            self.assertEqual(r.status_code, 200, r.get_data(as_text=True))
            html = r.get_data(as_text=True)
            self.assertIn('Contador Externo', html)
            self.assertIn('2026-10-31', html)
            self.assertNotIn('999.00', html)
            self.assertIn('attachment;', r.headers['Content-Disposition'])

    def test_error_en_guardado_revierte_cabecera(self):
        ctx = self.conc()
        self.db.execute("CREATE TRIGGER prueba_error BEFORE INSERT ON flujo_eventos BEGIN SELECT RAISE(ABORT, 'fallo simulado'); END")
        with self.assertLogs(self.app.logger, level='ERROR'):
            r = self.post_conc(ctx)
        self.assertEqual(r.status_code, 500)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM conciliaciones_bancarias').fetchone()[0], 0)


if __name__ == '__main__':
    unittest.main()
