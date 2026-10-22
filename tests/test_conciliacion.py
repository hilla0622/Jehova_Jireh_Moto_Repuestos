import copy
import unittest

from conciliacion_service import validar_extracto
from flujo_service import calcular_conciliacion
from ejemplo_conciliacion import ejemplo
import test_flujo


class CotejoTest(unittest.TestCase):
    def setUp(self):
        self.extracto, self.empresa, self.partidas = ejemplo()

    def validar(self):
        return validar_extracto(self.extracto, self.empresa, self.partidas, '2019-01-31', 35500)

    def test_ejemplo_video_y_cuatro_diferencias(self):
        self.assertEqual(78000 + sum(m['debe'] - m['haber'] for m in self.empresa), 28000)
        normal, control = self.validar()
        self.assertTrue(control['completo'])
        self.assertEqual(control['saldo_final_calculado'], 35500)
        self.assertEqual(control['vinculados'], 13)
        self.assertEqual(len(normal['movimientos']), 15)
        resumen = calcular_conciliacion(28000, 35500, self.partidas, '2019-01-31')
        self.assertEqual(resumen['saldo_en_conciliacion'], 28000)
        self.assertEqual(resumen['diferencia'], 0)
        self.assertEqual(resumen['saldo_libros_ajustado'], 31500)
        self.assertEqual(resumen['saldo_banco_ajustado'], 31500)

    def test_retiro_y_deposito_compensados_no_equivalen_a_revision(self):
        self.extracto['vinculos'] = []
        _, control = self.validar()
        self.assertFalse(control['completo'])
        self.assertEqual(control['sin_revisar'], 26)

    def test_rechaza_vinculos_repetidos_y_sentido_incorrecto(self):
        self.extracto['vinculos'].append(self.extracto['vinculos'][0])
        with self.assertRaisesRegex(ValueError, 'disponible'): self.validar()
        self.setUp()
        self.extracto['vinculos'][0]['movimiento_id'] = 6  # entrada de 35,000 frente a retiro de 35,000
        self.extracto['vinculos'] = self.extracto['vinculos'][:1]
        with self.assertRaisesRegex(ValueError, 'sentido'): self.validar()

    def test_rechaza_partida_inventada_o_doble_clasificacion(self):
        self.partidas[0]['monto'] = 10000
        with self.assertRaisesRegex(ValueError, 'importe'): self.validar()
        self.setUp()
        self.partidas.append(copy.deepcopy(self.partidas[0]))
        with self.assertRaisesRegex(ValueError, 'dos veces'): self.validar()

    def test_extracto_incompleto_es_borrador(self):
        self.extracto['saldo_inicial'] = 77000
        _, control = self.validar()
        self.assertEqual(control['diferencia_extracto'], -1000)
        self.assertFalse(control['completo'])

    def test_fecha_fuera_de_mes_y_dos_importes_rechazados(self):
        self.extracto['movimientos'][0]['fecha'] = '2019-02-01'
        with self.assertRaisesRegex(ValueError, 'mes'): self.validar()
        self.setUp()
        self.extracto['movimientos'][0]['deposito'] = 1
        with self.assertRaisesRegex(ValueError, 'ambos'): self.validar()

    def test_cheque_anterior_se_vincula_sin_duplicar_gasto(self):
        p = dict(uid='anterior', heredada=True, tipo_partida='Cheque en Transito', monto=100,
                 esta_conciliada=True, resolucion='Cobrado en febrero')
        e = dict(saldo_inicial=1000, movimientos=[dict(uid='b1', fecha='2019-02-01', concepto='Cheque cobrado', retiro=100)],
                 vinculos=[dict(banco_uid='b1', partida_uid='anterior')])
        _, control = validar_extracto(e, [], [p], '2019-02-28', 900)
        self.assertTrue(control['completo'])
        p['esta_conciliada'] = False
        with self.assertRaisesRegex(ValueError, 'resuelto'): validar_extracto(e, [], [p], '2019-02-28', 900)


class PersistenciaTest(unittest.TestCase):
    def setUp(self):
        self.fixture = test_flujo.ApiTest()
        self.fixture.setUp()
        self.client, self.db = self.fixture.client, self.fixture.db

    def tearDown(self): self.fixture.tearDown()

    def test_cero_sin_cotejo_no_cierra_y_revision_detecta_cambio_de_extracto(self):
        self.fixture.insert(test_flujo.asiento(2, [(2, 100, 0), (10, 0, 100)]))
        ctx = self.fixture.conc()
        e = dict(saldo_inicial=10000, movimientos=[dict(uid='b', fecha='2026-10-10', concepto='Cobro', deposito=100)], vinculos=[])
        r = self.fixture.post_conc(ctx, saldo_segun_banco=10100, extracto=e)
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(r.json['resumen']['diferencia'], 0)
        self.assertEqual(r.json['resumen']['estado'], 'Borrador')
        ctx = self.fixture.conc()
        self.assertEqual(ctx['extracto']['movimientos'][0]['concepto'], 'Cobro')
        e['vinculos'] = [dict(banco_uid='b', movimiento_id=201)]
        r = self.fixture.post_conc(ctx, saldo_segun_banco=10100, extracto=e)
        self.assertEqual(r.status_code, 200, r.json)
        self.assertEqual(r.json['resumen']['estado'], 'Conciliada')
        self.assertEqual(self.fixture.post_conc(ctx, saldo_segun_banco=10100, extracto=e).status_code, 409)
        self.assertEqual(self.fixture.post_conc(self.fixture.conc(), saldo_segun_banco=10100).status_code, 400)

    def test_historico_conserva_mayor_guardado_y_extracto_no_se_hereda(self):
        e = dict(saldo_inicial=10000, movimientos=[], vinculos=[])
        r = self.fixture.post_conc(self.fixture.conc(), extracto=e)
        self.assertEqual(r.status_code, 200, r.json)
        noviembre = self.fixture.conc(11)
        self.assertIsNone(noviembre['extracto'])
        self.assertEqual(self.fixture.post_conc(noviembre, extracto=e).status_code, 200)
        self.fixture.insert(test_flujo.asiento(2, [(2, 100, 0), (10, 0, 100)]))
        octubre = self.fixture.conc()
        self.assertTrue(octubre['solo_lectura'])
        self.assertEqual(octubre['saldo_segun_libros'], 10000)
        self.assertEqual(octubre['movimientos_mes'], [])
        self.assertEqual(self.fixture.post_conc(octubre, extracto=e).status_code, 400)

    def test_extracto_invalido_no_escribe_cabecera(self):
        e = dict(saldo_inicial=10000, movimientos=[dict(uid='b', fecha='2026-11-01', concepto='Fuera de mes', deposito=10)], vinculos=[])
        r = self.fixture.post_conc(self.fixture.conc(), extracto=e)
        self.assertEqual(r.status_code, 400, r.json)
        self.assertEqual(self.db.execute('SELECT COUNT(*) FROM conciliaciones_bancarias').fetchone()[0], 0)


if __name__ == '__main__': unittest.main()
