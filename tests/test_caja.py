import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
import datetime
import app as backend


class TestCaja(unittest.TestCase):
    def setUp(self):
        backend.app.config['TESTING'] = True
        self.client = backend.app.test_client()
        with self.client.session_transaction() as s:
            s['user'] = {'id': 1, 'rol': 'Administrador', 'username': 'admin'}

    @patch('app.get_db_connection')
    def test_caja_cierre_exitoso(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Simular sesión de caja abierta con monto_inicial 20000.00
        mock_caja = MagicMock()
        mock_caja.monto_inicial = Decimal('20000.00')
        mock_caja.estado = 'Abierta'

        # Cursor returns: 1) caja abierta, 2) suma de ventas en efectivo
        mock_cursor.fetchone.side_effect = [
            mock_caja,
            (Decimal('500.00'),)
        ]

        res = self.client.post('/api/caja/cierre', json={
            'sesion_caja_id': 4,
            'monto_final_real': 20500.0,
            'observaciones': 'Turno normal'
        })

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['diferencia'], 0.0)
        self.assertIn('correctamente', data['mensaje'])

    @patch('app.get_db_connection')
    def test_caja_cierre_maneja_nulos_y_auto_sesion(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_open_ses = MagicMock()
        mock_open_ses.id = 4

        mock_caja = MagicMock()
        mock_caja.monto_inicial = Decimal('1000.00')
        mock_caja.estado = 'Abierta'

        mock_cursor.fetchone.side_effect = [
            mock_open_ses,      # SELECT TOP 1 id FROM sesiones_caja (auto resolver)
            mock_caja,          # SELECT monto_inicial, estado FROM sesiones_caja
            (Decimal('0.00'),)  # SELECT ISNULL(SUM(total), 0) FROM ventas
        ]

        # Enviar sin sesion_caja_id y con monto_final_real nulo
        res = self.client.post('/api/caja/cierre', json={
            'sesion_caja_id': None,
            'monto_final_real': None,
            'observaciones': ''
        })

        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['diferencia'], -1000.0)

    @patch('app.get_db_connection')
    def test_caja_cierre_caja_inexistente_o_ya_cerrada(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        # Retorna None para sesión
        mock_cursor.fetchone.return_value = None

        res = self.client.post('/api/caja/cierre', json={
            'sesion_caja_id': 999,
            'monto_final_real': 500.0
        })

        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()
