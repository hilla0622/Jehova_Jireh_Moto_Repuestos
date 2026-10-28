"""Verifica operaciones DEMO, trazabilidad y API dentro de una transacción revertida."""
import json
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
        cur.execute('SELECT * FROM productos ORDER BY id'); productos=[tuple(r) for r in cur.fetchall()]
        cur.execute('SELECT * FROM empleados ORDER BY id'); empleados=[tuple(r) for r in cur.fetchall()]
        primero=cargar(conn)
        segundo=cargar(conn)
        assert segundo['insertados']=={}, segundo['insertados']
        for anio,pagar,favor in [(2024,10755,0),(2025,0,4800)]:
            d=primero['ejercicios'][anio]
            assert d['saldo_a_pagar']==pagar and d['saldo_a_favor']==favor,d
        # Todas las filas existentes se conservan exactamente (incluidos empleados actuales).
        for tabla,anteriores in [('productos',productos),('empleados',empleados)]:
            if anteriores:
                ids=[r[0] for r in anteriores]
                cur.execute(f"SELECT * FROM {tabla} WHERE id IN ({','.join('?' for _ in ids)}) ORDER BY id",tuple(ids))
                assert [tuple(r) for r in cur.fetchall()]==anteriores,tabla
        cur.execute("SELECT stock_actual FROM productos WHERE codigo_sku IN ('DEMO-IR-REP-2024','DEMO-IR-REP-2025')")
        assert [r[0] for r in cur.fetchall()]==[0,0]
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
