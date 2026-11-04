import unittest
from unittest.mock import patch, MagicMock
from decimal import Decimal
import app as backend


class TestComprasMultiplesYEliminar(unittest.TestCase):
    def setUp(self):
        backend.app.config['TESTING'] = True
        self.client = backend.app.test_client()
        with self.client.session_transaction() as s:
            s['user'] = {
                'id': 1,
                'rol': 'Administrador',
                'username': 'admin'
            }

    @patch('app.get_db_connection')
    def test_registrar_compra_multiples_repuestos(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        prod1 = MagicMock(stock_actual=10, costo=Decimal('25.00'))
        prod2 = MagicMock(stock_actual=4, costo=Decimal('50.00'))

        mock_cursor.fetchone.side_effect = [
            (101,),
            prod1,
            prod2,
            (1,),
            (2,),
            (501,)
        ]

        payload = {
            'proveedor_id': 1,
            'numero_factura_proveedor': 'FAC-2026-001',
            'items': [
                {'producto_id': 1, 'cantidad': 5, 'costo_unitario': 25.00},
                {'producto_id': 2, 'cantidad': 10, 'costo_unitario': 52.00}
            ]
        }

        res = self.client.post('/api/compras', json=payload)
        self.assertEqual(res.status_code, 201)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertEqual(data['id'], 101)
        self.assertTrue(mock_conn.commit.called)

        updates = [c for c in mock_cursor.execute.call_args_list if 'UPDATE productos SET stock_actual' in str(c)]
        self.assertEqual(len(updates), 2)
        self.assertEqual(updates[0][0][1], (15, 25.0, 1))
        self.assertEqual(updates[1][0][1], (14, 52.0, 2))

    @patch('app.get_db_connection')
    def test_eliminar_compra_revierte_stock(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_compra = MagicMock(id=101, codigo_compra='COM-#101', total=Decimal('645.00'), estado='Completada')
        det1 = MagicMock(producto_id=1, cantidad=5, costo_unitario=Decimal('25.00'))
        det2 = MagicMock(producto_id=2, cantidad=10, costo_unitario=Decimal('52.00'))

        prod1 = MagicMock(stock_actual=15, nombre='Repuesto A')
        prod2 = MagicMock(stock_actual=14, nombre='Repuesto B')

        mock_cursor.fetchone.side_effect = [
            mock_compra,
            prod1,
            prod2
        ]
        mock_cursor.fetchall.side_effect = [
            [det1, det2],
            [(501,)]
        ]

        res = self.client.delete('/api/compras/101')
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertTrue(data['success'])
        self.assertIn('eliminada exitosamente y stock revertido', data['mensaje'])

        updates = [c for c in mock_cursor.execute.call_args_list if 'UPDATE productos SET stock_actual' in str(c)]
        self.assertEqual(len(updates), 2)
        self.assertEqual(updates[0][0][1], (10, 1))
        self.assertEqual(updates[1][0][1], (4, 2))

        delete_det = [c for c in mock_cursor.execute.call_args_list if 'DELETE FROM detalle_compras WHERE compra_id' in str(c)]
        delete_compra = [c for c in mock_cursor.execute.call_args_list if 'DELETE FROM compras WHERE id' in str(c)]
        self.assertTrue(len(delete_det) > 0)
        self.assertTrue(len(delete_compra) > 0)
        self.assertTrue(mock_conn.commit.called)

    @patch('app.get_db_connection')
    def test_eliminar_compra_inexistente(self, mock_get_db):
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_get_db.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor

        mock_cursor.fetchone.return_value = None

        res = self.client.delete('/api/compras/999999')
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertIn('error', data)

    def test_registrar_compra_sin_items(self):
        res = self.client.post('/api/compras', json={
            'proveedor_id': 1,
            'items': []
        })
        self.assertEqual(res.status_code, 400)
        data = res.get_json()
        self.assertIn('error', data)


if __name__ == '__main__':
    unittest.main()
