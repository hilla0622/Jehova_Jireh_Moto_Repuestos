import unittest
from unittest.mock import patch
import app

class MovimientosPaginadosTest(unittest.TestCase):
    def setUp(self):
        self.client = app.app.test_client()
        with self.client.session_transaction() as session:
            session['user'] = {'id': 1, 'rol': 'Administrador'}

    @patch.object(app, 'execute_query')
    def test_pagina_limitada_y_busqueda(self, query):
        query.return_value = [{'id': i, 'fecha': '2026-11-05'} for i in range(51)]
        response = self.client.get('/api/movimientos?page=2&q=filtro')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['items']), 50)
        self.assertTrue(response.json['has_more'])
        sql, params = query.call_args.args
        self.assertIn('ORDER BY m.fecha DESC, m.id DESC', sql)
        self.assertIn('FETCH NEXT 51', sql)
        self.assertEqual(params, ('%filtro%',) * 4 + (50,))

    @patch.object(app, 'execute_query', return_value=[])
    def test_vacio_y_compatibilidad(self, query):
        self.assertFalse(self.client.get('/api/movimientos?page=1').json['has_more'])
        self.assertEqual(self.client.get('/api/movimientos').json, [])
        self.assertEqual(self.client.get('/api/movimientos?page=abc').status_code, 400)

    def test_cliente_sin_acceso(self):
        with self.client.session_transaction() as session:
            session['user'] = {'rol': 'Cliente'}
        self.assertEqual(self.client.get('/api/movimientos?page=1').status_code, 403)

if __name__ == '__main__':
    unittest.main()
