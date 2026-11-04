"""Verifica operaciones DEMO, trazabilidad y API dentro de una transacción revertida."""
import json
import re
from unittest.mock import patch
import app
import fiscal_service as fiscal
from seed_fiscal_operaciones import cargar


class LecturaTransaccion:
    def __init__(self, conn): self.conn=conn
    def cursor(self): return self.conn.cursor()
    def close(self): pass
    def commit(self): raise AssertionError('Una consulta GET intentó confirmar la transacción')
    def rollback(self): raise AssertionError('Una consulta GET intentó revertir la transacción')


def main():
    conn=app.get_db_connection(); conn.autocommit=False
    try:
        cur=conn.cursor()
        cur.execute("SELECT * FROM productos WHERE descripcion IS NULL OR descripcion NOT LIKE '[[]DEMO-FISCAL]%' ORDER BY id"); productos=[tuple(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM empleados WHERE identificacion NOT LIKE 'DEMO-EMP-%' ORDER BY id"); empleados=[tuple(r) for r in cur.fetchall()]
        cur.execute("SELECT * FROM ventas WHERE notas IS NULL OR notas NOT LIKE '[[]DEMO-FISCAL]%' ORDER BY id"); ventas=[tuple(r) for r in cur.fetchall()]
        primero=cargar(conn)
        segundo=cargar(conn)
        assert segundo['insertados']=={}, segundo['insertados']
        for anio,pagar,favor in [(2024,10755,0),(2025,0,4800)]:
            d=primero['ejercicios'][anio]
            assert d['saldo_a_pagar']==pagar and d['saldo_a_favor']==favor,d
        # Las operaciones y los registros ajenos a esta carga se conservan exactamente.
        for tabla,anteriores in [('productos',productos),('empleados',empleados),('ventas',ventas)]:
            if anteriores:
                ids=[r[0] for r in anteriores]
                cur.execute(f"SELECT * FROM {tabla} WHERE id IN ({','.join('?' for _ in ids)}) ORDER BY id",tuple(ids))
                assert [tuple(r) for r in cur.fetchall()]==anteriores,tabla
        cur.execute("SELECT stock_actual FROM productos WHERE codigo_sku IN ('KIT901','AMO901')")
        assert [r[0] for r in cur.fetchall()]==[0,0]
        cur.execute("""SELECT v.id,v.codigo_venta,c.nombre_completo,v.total FROM ventas v
            JOIN clientes c ON c.id=v.cliente_id JOIN demo_fiscal_origenes o ON o.documento_id=v.id
            AND o.tabla_origen='ventas' AND o.clave LIKE 'VENTA-%'""")
        historicas=cur.fetchall()
        assert len(historicas)==24
        assert all(re.fullmatch(r'VEN-\d{4}',r.codigo_venta) for r in historicas)
        assert len({r.nombre_completo for r in historicas})==12
        assert 'Marcos Gaitan' in {r.nombre_completo for r in historicas}
        assert len({r.total for r in historicas})>=12
        cur.execute("""SELECT v.id FROM ventas v JOIN demo_fiscal_origenes o ON o.documento_id=v.id
            AND o.tabla_origen='ventas' AND o.clave LIKE 'VENTA-%'
            WHERE v.total<>(SELECT SUM(subtotal) FROM detalle_ventas WHERE venta_id=v.id)
            OR EXISTS (SELECT 1 FROM comprobantes c WHERE c.venta_id=v.id
                AND (c.total<>v.total OR c.numero<>'TICK-'+v.codigo_venta))""")
        assert not cur.fetchone(), 'Detalles o comprobantes inconsistentes'
        cur.execute("""SELECT id FROM productos WHERE activo=1 AND descripcion LIKE '[[]DEMO-FISCAL]%'
            AND (nombre LIKE '%DEMO%' OR codigo_sku LIKE 'DEMO%')""")
        assert not cur.fetchone(), 'Productos sin nombres/códigos apropiados'
        # Verificar que las pantallas pueden consultar los registros sin confirmar la carga.
        with patch.object(app,'get_db_connection',return_value=LecturaTransaccion(conn)):
            with app.app.test_client() as client:
                with client.session_transaction() as s: s['user']={'id':1,'rol':'Administrador'}
                for url, minimo in [('/api/ventas',24),('/api/compras',48),('/api/movimientos',49),
                                     ('/api/nomina/historial',24),('/api/empleados',2)]:
                    response=client.get(url)
                    assert response.status_code==200,(url,response.get_json())
                    assert len(response.get_json())>=minimo,url
                for anio in (2024,2025):
                    r=client.get(f'/api/fiscal/simulacion/{anio}')
                    assert r.status_code==200,r.get_json()
                    assert r.get_json()['balance']['balance_cuadrado']
                    respaldo=client.get(f'/api/fiscal/respaldo-demo/{anio}')
                    assert respaldo.status_code==200,respaldo.get_json()
                    assert len(respaldo.get_json()['documentos'])==72
                cur.execute("SELECT documento_id FROM demo_fiscal_origenes WHERE clave='NOMINA-2024-01'")
                nid=cur.fetchone()[0]
                for url in [f'/api/nomina/{nid}/detalle', '/api/rrhh/pagos-nomina']:
                    response=client.get(url)
                    assert response.status_code==200,(url,response.get_json())
        print('OK: operaciones, balances, cobros, pagos, idempotencia y registros anteriores intactos.')
        print(json.dumps({k:v for k,v in primero.items() if k!='fuentes'},ensure_ascii=False,indent=2,default=str))
    finally:
        conn.rollback();conn.close()


if __name__=='__main__':main()
