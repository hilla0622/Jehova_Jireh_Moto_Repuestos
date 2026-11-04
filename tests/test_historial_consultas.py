"""El historial masivo conserva sus detalles con dos consultas, no una por fila."""
import copy
from datetime import date
from decimal import Decimal
import unittest
from unittest.mock import patch
import app as backend


class ConsultasHistorialTests(unittest.TestCase):
    def setUp(self):
        self.client=backend.app.test_client()
        with self.client.session_transaction() as s:s['user']={'id':1,'rol':'Administrador'}

    def test_ventas_detalles_en_lote_y_sin_mezclar_clientes(self):
        headers=[dict(id=i,fecha=date(2026,10,1),total=Decimal('180.50')) for i in (8,7,6)]
        detalles=[dict(venta_id=7,producto_id=1,cantidad=1,precio_unitario=Decimal('180.50'),subtotal=Decimal('180.50')),
                  dict(venta_id=8,producto_id=2,cantidad=1,precio_unitario=Decimal('180.50'),subtotal=Decimal('180.50'))]
        with patch.object(backend,'execute_query',side_effect=copy.deepcopy([headers,detalles])) as query:
            respuesta=self.client.get('/api/ventas')
        self.assertEqual(respuesta.status_code,200);self.assertEqual(query.call_count,2)
        filas=respuesta.get_json()
        self.assertEqual(filas[0]['detalles'][0]['producto_id'],2)
        self.assertEqual(filas[1]['detalles'][0]['producto_id'],1)
        self.assertEqual(filas[2]['detalles'],[])

    def test_compras_lote_conserva_costos_y_fechas(self):
        headers=[dict(id=i,fecha=date(2026,10,1),total=Decimal('54.80')) for i in (10,11)]
        detalles=[dict(compra_id=11,producto_id=4,cantidad=2,costo_unitario=Decimal('27.40'),subtotal=Decimal('54.80'))]
        with patch.object(backend,'execute_query',side_effect=copy.deepcopy([headers,detalles])) as query:
            respuesta=self.client.get('/api/compras')
        self.assertEqual(query.call_count,2)
        self.assertEqual(respuesta.get_json()[1]['detalles'][0]['costo_unitario'],27.4)
        self.assertEqual(respuesta.get_json()[0]['fecha_formateada'],'01/10/2026')

    def test_pedidos_lote_conserva_aliases_del_frontend(self):
        headers=[dict(id=3,codigo='WEB-3',metodo='Transferencia',fecha=date(2026,10,1),subtotal=Decimal(50),total=Decimal(50))]
        detalles=[dict(pedido_id=3,producto_id=5,cantidad=1,precioUnitario=Decimal(50),subtotal=Decimal(50))]
        with patch.object(backend,'execute_query',side_effect=copy.deepcopy([headers,detalles])) as query:
            respuesta=self.client.get('/api/pedidos_web')
        self.assertEqual(query.call_count,2)
        pedido=respuesta.get_json()[0]
        self.assertEqual(pedido['detalles'][0]['precio_unitario'],50)
        self.assertEqual(pedido['codigo_venta'],'WEB-3')

    def test_listas_vacias_no_consultan_detalles(self):
        for endpoint in ['/api/ventas','/api/compras','/api/pedidos_web']:
            with self.subTest(endpoint=endpoint),patch.object(backend,'execute_query',return_value=[]) as query:
                self.assertEqual(self.client.get(endpoint).get_json(),[])
                self.assertEqual(query.call_count,1)

    def test_asientos_en_lote_conservan_filtro_y_partidas(self):
        headers=[dict(id=20,fecha=date(2026,10,1),created_at=None),dict(id=19,fecha=date(2026,10,1),created_at=None)]
        detalles=[dict(asiento_id=19,id=40,codigo='1.1.01',cuenta='Caja',debe=Decimal(100),haber=Decimal(0))]
        with patch.object(backend,'execute_query',side_effect=copy.deepcopy([headers,detalles])) as query:
            respuesta=self.client.get('/api/finanzas/asientos?start=2026-10-01&end=2026-10-31')
        self.assertEqual(respuesta.status_code,200);self.assertEqual(query.call_count,2)
        self.assertEqual(query.call_args.kwargs['params'],('2026-10-01','2026-10-31'))
        self.assertEqual(respuesta.get_json()[1]['movimientos'][0]['debe'],100)
        self.assertEqual(respuesta.get_json()[0]['movimientos'],[])


if __name__=='__main__':unittest.main()
