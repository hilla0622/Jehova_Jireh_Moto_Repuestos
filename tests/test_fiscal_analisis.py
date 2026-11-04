import copy
import json
import os
import unittest
from unittest.mock import MagicMock, patch

import fiscal_service as fiscal
import fiscal_analisis as analisis
import app as backend


class AnalisisIRTests(unittest.TestCase):
    def test_clave_local_se_lee_sin_ejecutar_y_entorno_tiene_prioridad(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(analisis.Path, 'read_text', return_value='OPENAI_API_KEY="sk-prueba-local" # comentario'):
            self.assertEqual(analisis.obtener_clave_ia(), 'sk-prueba-local')
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(analisis.Path, 'read_text', return_value='OPENAI_API_KEY=$(comando)'):
            self.assertEqual(analisis.obtener_clave_ia(), '')
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'sk-prueba-entorno'}), \
             patch.object(analisis.Path, 'read_text') as archivo:
            self.assertEqual(analisis.obtener_clave_ia(), 'sk-prueba-entorno')
        archivo.assert_not_called()

    def test_archivo_clave_ausente_no_impide_analisis_contable(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(analisis.Path, 'read_text', side_effect=FileNotFoundError):
            self.assertEqual(analisis.obtener_clave_ia(), '')

    def sim(self, anio=2025, corte=None, cuentas=None):
        return fiscal.mapear_formulario_106(dict(anio=anio,
            fecha_fin=corte or f'{anio}-12-31', balance={}, resultados=cuentas or {}))

    def test_sin_anterior_no_inventa_comparacion(self):
        informe = analisis.construir_analisis(self.sim())
        self.assertFalse(informe['comparacion_disponible'])
        self.assertIsNone(informe['margen'])
        self.assertTrue(all(m['anterior'] is None for m in informe['metricas']))

    def test_base_cero_no_produce_porcentajes_infinitos(self):
        actual = self.sim()
        actual['resultados']['total_ingresos_brutos'] = 100
        informe = analisis.construir_analisis(actual, self.sim(2024))
        self.assertEqual(informe['metricas'][0]['diferencia'], 100)
        self.assertIsNone(informe['metricas'][0]['variacion'])

    def test_informe_explica_margen_variaciones_y_saldo_en_prosa(self):
        def cuentas(ingresos, costos, gastos):
            return {k: {'saldo': v} for k, v in
                    [('4.1.01', ingresos), ('5.1.01', costos), ('6.1.02', gastos)]}
        actual = self.sim(cuentas=cuentas(1380000, 720000, 600499.92))
        anterior = self.sim(2024, cuentas=cuentas(1080000, 540000, 372300))
        actual['liquidacion'].update(total_acreditamientos=18600,
            anticipos_mensuales=13800, retenciones_sufridas=4800,
            saldo_a_favor=4800, saldo_a_pagar=0)
        actual['acreditamientos'] = [{'id': 8, 'documento_respaldo_url': ''}]
        informe = analisis.construir_analisis(actual, anterior)
        texto = '\n\n'.join(informe['parrafos'])
        self.assertEqual(len(informe['parrafos']), 6)
        for fragmento in ['52.17', '43.51', '108,199.92', '15.53 % a 4.31 %',
                          '13,800.00', '4,800.00', 'no implica una devolución',
                          'Un acreditamiento no tiene archivo de respaldo adjunto']:
            self.assertIn(fragmento, texto)

    def test_informe_ceros_y_perdida_no_inventa_margen_ni_devolucion(self):
        cero = analisis.construir_analisis(self.sim())
        texto = '\n'.join(cero['parrafos'])
        self.assertIn('no se calcula un margen', texto)
        self.assertIn('No se encontraron movimientos', texto)
        perdida = self.sim(cuentas={'6.1.02': {'saldo': 100}})
        texto = '\n'.join(analisis.construir_analisis(perdida)['parrafos'])
        self.assertIn('una pérdida contable de C$ 100.00', texto)
        self.assertNotIn('nan', texto.lower())

    def test_observaciones_rastreables_y_sin_modificar_importes(self):
        actual = self.sim()
        actual['acreditamientos'] = [{'id': 8, 'documento_respaldo_url': ''}]
        original = copy.deepcopy(actual)
        informe = analisis.construir_analisis(actual)
        observacion = next(o for o in informe['observaciones'] if o['destino'] == 'acreditamientos')
        self.assertIn('#8', observacion['fuente'])
        self.assertEqual(actual, original)

    def test_periodo_parcial_compara_misma_fecha_y_ajusta_bisiesto(self):
        actual = dict(anio=2024, fecha_fin='2024-02-29', balance={}, resultados={})
        with patch.object(fiscal, 'obtener_saldos_contables_ejercicio', side_effect=[actual,
                dict(anio=2023, fecha_fin='2023-02-28', balance={}, resultados={})]) as saldos, \
             patch.object(fiscal, 'obtener_ajustes_ejercicio', return_value=[]), \
             patch.object(fiscal, 'obtener_acreditamientos_ejercicio', return_value=[]):
            informe = analisis.obtener_analisis(MagicMock(), 2024)
        self.assertEqual(saldos.call_args.args[2], '2023-02-28')
        self.assertFalse(informe['comparacion_disponible'])
        self.assertTrue(any(o['titulo'] == 'Ejercicio en curso' for o in informe['observaciones']))

    def test_sin_clave_no_llama_proveedor(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}), patch.object(analisis, 'urlopen') as red:
            self.assertEqual(analisis.interpretar_con_ia(analisis.construir_analisis(self.sim()))['modo'], 'contable')
        red.assert_not_called()

    def test_ia_real_parseo_y_payload_sin_identidad(self):
        respuesta = MagicMock()
        respuesta.__enter__.return_value.read.return_value = json.dumps(dict(status='completed',
            output=[dict(type='message', content=[dict(type='output_text', text='Interpretación del período.')])])).encode()
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'clave-de-prueba'}), \
             patch.object(analisis, 'urlopen', return_value=respuesta) as red:
            informe = analisis.interpretar_con_ia(analisis.construir_analisis(self.sim()))
        self.assertEqual(informe['modo'], 'ia')
        payload = json.loads(red.call_args.args[0].data)
        self.assertFalse(payload['store'])
        self.assertNotIn('agente_retenedor_ruc', payload['input'])

    def test_falla_ia_conserva_informe_sin_exponer_error(self):
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'clave-de-prueba'}), \
             patch.object(analisis, 'urlopen', side_effect=TimeoutError('secreto')):
            informe = analisis.interpretar_con_ia(analisis.construir_analisis(self.sim()))
        self.assertEqual(informe['modo'], 'contable')
        self.assertNotIn('secreto', informe['aviso_ia'])
        self.assertIn('no está disponible', informe['aviso_ia'])

    def test_limpiar_texto_ia_elimina_markdown_y_mantiene_prosa(self):
        sucio = (
            "## 1. Desempeño Operativo\n\n"
            "Durante el ejercicio 2025, el negocio registró **C$ 1,380,000.00** en ingresos.\n"
            "- Costo de ventas: C$ 720,000.00.\n"
            "* Gastos operativos: C$ 600,499.92.\n\n"
            "### 2. Conciliación Fiscal\n\n"
            "El impuesto determinado corresponde al `Pago Mínimo Definitivo`."
        )
        limpio = analisis.limpiar_texto_ia(sucio)
        self.assertNotIn('#', limpio)
        self.assertNotIn('*', limpio)
        self.assertNotIn('`', limpio)
        self.assertNotIn('- Costo', limpio)
        self.assertIn('C$ 1,380,000.00 en ingresos', limpio)
        self.assertIn('Pago Mínimo Definitivo', limpio)

    def test_modelo_ia_predeterminado_y_configurable(self):
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(analisis.Path, 'read_text', side_effect=FileNotFoundError):
            self.assertEqual(analisis.obtener_modelo_ia(), 'gpt-4o-mini')
        with patch.dict(os.environ, {'FISCAL_AI_MODEL': 'gpt-4o'}):
            self.assertEqual(analisis.obtener_modelo_ia(), 'gpt-4o')
        with patch.dict(os.environ, {}, clear=True), \
             patch.object(analisis.Path, 'read_text', return_value='FISCAL_AI_MODEL="gpt-4o-mini"'):
            self.assertEqual(analisis.obtener_modelo_ia(), 'gpt-4o-mini')

    def test_ia_real_extrae_output_text_directo_y_usa_modelo_configurado(self):
        respuesta = MagicMock()
        respuesta.__enter__.return_value.read.return_value = json.dumps(dict(
            status='completed',
            output_text='Interpretación directa desde output_text.'
        )).encode()
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'clave-de-prueba', 'FISCAL_AI_MODEL': 'gpt-4o'}), \
             patch.object(analisis, 'urlopen', return_value=respuesta) as red:
            informe = analisis.interpretar_con_ia(analisis.construir_analisis(self.sim()))
        self.assertEqual(informe['modo'], 'ia')
        self.assertEqual(informe['interpretacion_ia'], 'Interpretación directa desde output_text.')
        payload = json.loads(red.call_args.args[0].data)
        self.assertEqual(payload['model'], 'gpt-4o')
        self.assertIn('calculo_ir', payload['input'])

    def test_endpoint_restringido_y_no_persiste(self):
        cliente = backend.app.test_client()
        self.assertEqual(cliente.post('/api/fiscal/analisis/2025').status_code, 401)
        with cliente.session_transaction() as sesion:
            sesion['user'] = {'id': 1, 'rol': 'Vendedor'}
        self.assertEqual(cliente.post('/api/fiscal/analisis/2025').status_code, 403)
        with cliente.session_transaction() as sesion:
            sesion['user'] = {'id': 1, 'rol': 'Contador'}
        conn = MagicMock()
        with patch.object(backend, 'get_db_connection', return_value=conn), \
             patch.object(analisis, 'obtener_analisis', return_value={'modo': 'contable'}), \
             patch.object(analisis, 'interpretar_con_ia', side_effect=lambda x: x):
            self.assertEqual(cliente.post('/api/fiscal/analisis/2025').status_code, 200)
        conn.close.assert_called_once()
        conn.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
