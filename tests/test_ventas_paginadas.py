import copy
import unittest
from unittest.mock import patch
import app

class VentasPaginadasTest(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        with self.client.session_transaction() as session:
            session['user'] = {'id': 1, 'rol': 'Administrador'}

    def test_paginas_y_detalles_limitados(self):
        for endpoint, foreign, precio in [('ventas', 'venta_id', 'precio_unitario'), ('pedidos_web', 'pedido_id', 'precioUnitario')]:
            with self.subTest(endpoint=endpoint):
                filas = [dict(id=i, fecha='2026-11-05', total=10, subtotal=10, codigo=f'WEB-{i}', metodo='Efectivo') for i in range(51)]
                detalle = {foreign: 4, precio: 10, 'subtotal': 10, 'cantidad': 1, 'producto_id': 2}
                with patch.object(app, 'execute_query', side_effect=copy.deepcopy([filas, [detalle]])) as query:
                    response = self.client.get(f'/api/{endpoint}?page=2&q=Ana&order=asc')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(len(response.json['items']), 50)
                self.assertTrue(response.json['has_more'])
                self.assertEqual(response.json['items'][4]['detalles'][0]['producto_id'], 2)
                sql, params = query.call_args_list[0].args
                self.assertIn('OFFSET ? ROWS FETCH NEXT 51 ROWS ONLY', sql)
                self.assertEqual(params[-1], 50)
                self.assertIn('%Ana%', params)
                if endpoint == 'ventas':
                    self.assertIn('v.fecha_venta ASC, v.id ASC', sql)
                    self.assertIn("NOT LIKE 'WEB-%'", sql)
                sql, ids = query.call_args_list[1].args
                self.assertIn(f'{foreign} IN (', sql)
                self.assertEqual(ids, tuple(range(50)))

    def test_vacio_error_y_permisos(self):
        for endpoint in ('ventas', 'pedidos_web'):
            with patch.object(app, 'execute_query', return_value=[]) as query:
                response = self.client.get(f'/api/{endpoint}?page=1')
                self.assertEqual(response.json, dict(items=[], page=1, has_more=False))
                self.assertEqual(query.call_count, 1)
                self.assertEqual(self.client.get(f'/api/{endpoint}?page=x').status_code, 400)
        with self.client.session_transaction() as session:
            session['user'] = {'rol': 'Cliente'}
        for endpoint in ('ventas', 'pedidos_web'):
            self.assertEqual(self.client.get(f'/api/{endpoint}?page=1').status_code, 403)

if __name__ == '__main__':
    unittest.main()
