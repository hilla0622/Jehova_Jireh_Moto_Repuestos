"""Prueba integración fiscal en SQL Server; revierte TODAS sus inserciones."""
import json
import subprocess
from pathlib import Path

from app import get_db_connection
import fiscal_service as fiscal
from seed_fiscal_demo import cargar


def main():
    conn = get_db_connection()
    conn.autocommit = False
    try:
        primera = cargar(conn)
        segunda = cargar(conn)
        assert all(v == 0 for v in segunda['insertados'].values()), segunda
        cur = conn.cursor()
        fixtures = [fiscal.preparar_declaracion_desde_contabilidad(cur, {'anio': y}) for y in (2024,2025)]
        con_nominas=fixtures[0]['cuentas_resultados'].get('6.1.11',0)>0
        assert fixtures[0]['liquidacion']['saldo_a_pagar'] == (10755 if con_nominas else 33600)
        assert fixtures[1]['liquidacion']['saldo_a_pagar'] == (0 if con_nominas else 8400)
        assert all(s['balance']['balance_cuadrado'] for s in fixtures)
        # Agregar un movimiento de 2025 no debe cambiar el balance de 2024.
        cur.execute("""INSERT INTO asientos_contables (fecha,concepto,modulo_origen,usuario_id)
            OUTPUT INSERTED.id VALUES ('2025-01-01','[TEST-FISCAL] corte','TEST_FISCAL',1)""")
        aid=cur.fetchone()[0]
        for codigo, debe, haber in [('1.1.02',123,0),('3.1.01',0,123)]:
            cur.execute('INSERT INTO movimientos_contables (asiento_id,cuenta_id,debe,haber) '
                        'SELECT ?,id,?,? FROM cuentas_contables WHERE codigo=?', (aid,debe,haber,codigo))
        posterior=fiscal.preparar_declaracion_desde_contabilidad(cur,{'anio':2024})
        assert posterior['balance'] == fixtures[0]['balance']
        assert fiscal.preparar_declaracion_desde_contabilidad(cur,{'anio':2025})['balance']['total_activos'] == fixtures[1]['balance']['total_activos']+123
        # Los borradores que ya existen no convierten la primera aprobación en sustitutiva.
        decl=fiscal.guardar_declaracion_completa(cur,fixtures[0],1,True)
        cur.execute('SELECT version,es_sustitutiva,declaracion_anterior_id FROM declaraciones_ir WHERE id=?',(decl,))
        assert tuple(cur.fetchone()) == (1,False,None)
        fiscal.registrar_presentacion_dgi(cur,{'declaracion_id':decl,'numero_referencia_dgi':'DEMO-TEST-NO-REAL'},1)
        sustituta=fiscal.guardar_declaracion_completa(cur,fixtures[0],1,True)
        cur.execute('SELECT version,es_sustitutiva,declaracion_anterior_id FROM declaraciones_ir WHERE id=?',(sustituta,))
        assert tuple(cur.fetchone()) == (2,True,decl)
        try:
            fiscal.eliminar_declaracion(cur,decl)
        except ValueError:
            pass
        else:
            raise AssertionError('Permitió eliminar una presentada')
        result=subprocess.run(['node', str(Path(__file__).with_name('fiscal_frontend.cjs')),'--stdin'],
                              input=json.dumps(fixtures),text=True,capture_output=True)
        assert result.returncode == 0, result.stdout + result.stderr
        print(result.stdout.strip())
        print('OK: SQL Server, corte anual, balances, versiones, protección e idempotencia.')
        print(json.dumps(primera,ensure_ascii=False,indent=2))
    finally:
        conn.rollback()
        conn.close()


if __name__ == '__main__':
    main()
