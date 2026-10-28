import copy
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import fiscal_service as fiscal
import app as backend


class FiscalTests(unittest.TestCase):
    def sim(self):
        return fiscal.mapear_formulario_106({
            'anio': 2024, 'fecha_fin': '2024-12-31', 'balance': {}, 'resultados': {}})

    def test_tarifas_limites(self):
        for renta, tasa in [(0,10),(100000,10),(100000.01,15),(200000,15),
                            (200000.01,20),(350000,20),(350000.01,25),
                            (500000,25),(500000.01,30)]:
            with self.subTest(renta=renta):
                self.assertEqual(fiscal.calcular_ir_anual(12000000,renta)['tasa_ir'], tasa)
        self.assertEqual(fiscal.calcular_ir_anual(12000000.01,1000)['tasa_ir'],30)

    def test_ceros_sin_acreditamientos_ficticios(self):
        sim = self.sim()
        self.assertEqual(sim['liquidacion']['saldo_a_pagar'], 0)
        self.assertEqual(sim['liquidacion']['total_acreditamientos'], 0)

    def test_perdida_no_genera_ir_negativo(self):
        self.assertEqual(fiscal.calcular_ir_anual(1000000,-100)['ir_calculado'],0)
        self.assertEqual(fiscal.calcular_ir_anual(1000000,-100)['pmd_calculado'],10000)

    def test_anulados_no_generan_saldo_a_favor(self):
        sim = fiscal.mapear_formulario_106({'anio':2024,'fecha_fin':'2024-12-31',
            'balance':{},'resultados':{}}, acreditamientos=[{
                'tipo':'RETENCION_SUFRIDA','importe_total':1000,'estado':'Anulado'}])
        self.assertEqual(sim['liquidacion']['saldo_a_favor'],0)

    def test_borradores_no_son_antecedentes_de_sustitutiva(self):
        cursor = MagicMock()
        cursor.fetchone.side_effect = [None, (99,)]
        fiscal.guardar_declaracion_completa(cursor,self.sim(),1,True)
        sql, params = cursor.execute.call_args_list[1].args
        self.assertEqual(params[:4],(2024,1,0,None))
        self.assertIn("estado = 'Presentada'",cursor.execute.call_args_list[0].args[0])

    def test_presentada_es_antecedente(self):
        cursor = MagicMock()
        cursor.fetchone.side_effect = [SimpleNamespace(id=7,version=1),(99,)]
        fiscal.guardar_declaracion_completa(cursor,self.sim(),1,True)
        self.assertEqual(cursor.execute.call_args_list[1].args[1][:4],(2024,2,1,7))

    def test_bloquea_aprobacion_descuadrada_y_periodo_incompleto(self):
        for campo, valor in [('balance',{'balance_cuadrado':False}),('fecha_corte','2024-06-30')]:
            sim=self.sim(); sim[campo]=valor
            with self.subTest(campo=campo), self.assertRaises(ValueError):
                fiscal.guardar_declaracion_completa(MagicMock(),sim,1,True)

    def test_guardado_rechaza_totales_alterados(self):
        canonical = self.sim(); submitted = copy.deepcopy(canonical)
        submitted['liquidacion']['saldo_a_pagar']=100
        with patch.object(fiscal,'obtener_saldos_contables_ejercicio'), \
             patch.object(fiscal,'obtener_ajustes_ejercicio'), \
             patch.object(fiscal,'obtener_acreditamientos_ejercicio'), \
             patch.object(fiscal,'obtener_info_tributaria',return_value={}), \
             patch.object(fiscal,'mapear_formulario_106',return_value=canonical):
            with self.assertRaises(ValueError):
                fiscal.preparar_declaracion_desde_contabilidad(MagicMock(),{'simulacion':submitted})

    def test_presentacion_no_se_repite(self):
        cur=MagicMock(); cur.fetchone.return_value=SimpleNamespace(id=1,estado='Presentada')
        with self.assertRaises(ValueError):
            fiscal.registrar_presentacion_dgi(cur,{'declaracion_id':1},1)

    def test_error_constancia_revierte_tambien_la_aprobacion(self):
        client=backend.app.test_client()
        with client.session_transaction() as s:
            s['user']={'id':1,'rol':'Administrador'}
        conn=MagicMock()
        with patch.object(backend,'get_db_connection',return_value=conn), \
             patch.object(fiscal,'preparar_declaracion_desde_contabilidad',return_value=self.sim()), \
             patch.object(fiscal,'guardar_declaracion_completa',return_value=1), \
             patch.object(fiscal,'registrar_presentacion_dgi',side_effect=ValueError('Referencia requerida')):
            response=client.post('/api/fiscal/presentar',json={'simulacion':{}})
        self.assertEqual(response.status_code,400)
        conn.rollback.assert_called_once()
        conn.commit.assert_not_called()


if __name__ == '__main__':
    unittest.main()
