"""Aplica la ampliación aditiva de RRHH a SQL Server en una sola transacción."""
import re
from pathlib import Path


def aplicar(conn):
    sql = Path(__file__).with_name('migracion_rrhh_control.sql').read_text(encoding='utf-8')
    cur = conn.cursor()
    try:
        for lote in re.split(r'^GO\s*$', sql, flags=re.M):
            if lote.strip():
                cur.execute(lote)
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


if __name__ == '__main__':
    from app import get_db_connection
    conn = get_db_connection()
    try:
        aplicar(conn)
        print('RRHH: migración aplicada. Se conservan los registros existentes.')
    finally:
        conn.close()
