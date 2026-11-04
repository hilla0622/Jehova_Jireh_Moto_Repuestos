"""Unifica referencias generadas para la feria; conserva IDs, importes y asientos."""
from collections import Counter
import json
import re
from app import get_db_connection


def main():
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError('No se pudo conectar a la base de datos')
    try:
        cur = conn.cursor()
        cur.execute('SET XACT_ABORT ON')
        cur.execute("""DECLARE @r INT; EXEC @r=sp_getapplock
            @Resource='normalizar_transferencias_nomina',@LockMode='Exclusive',
            @LockOwner='Transaction',@LockTimeout=5000;
            IF @r<0 THROW 50001,'Hay otra normalización en ejecución',1;""")
        cur.execute("SELECT id FROM cargas_negocio WHERE version='NEGOCIO-2024-2026-V1'")
        carga = cur.fetchone()
        if not carga:
            raise RuntimeError('No existe la carga de la feria')
        cur.execute('''SELECT id,fecha_pago,numero_referencia,metodo_pago
            FROM pagos_nomina WITH(UPDLOCK,HOLDLOCK) ORDER BY fecha_pago,id''')
        filas = cur.fetchall()
        conteos = Counter()
        cambios = []
        for pid, fecha, anterior, metodo in filas:
            if metodo != 'Transferencia Bancaria' or not re.fullmatch(
                r'(?:PN-\d{6}-\d+|TRF-BAC-\d{4}-\d{2,4})', anterior or ''
            ):
                continue
            conteos[fecha.year] += 1
            nueva = f'TRF-BAC-{fecha.year}-{conteos[fecha.year]:04d}'
            if nueva != anterior:
                cambios.append((pid, anterior, nueva))
        ids = {pid for pid, _, _ in cambios}
        for _, _, nueva in cambios:
            if any(ref == nueva and pid not in ids for pid, _, ref, _ in filas):
                raise ValueError('La referencia propuesta ya está utilizada: ' + nueva)
        for pid, _, _ in cambios:
            cur.execute('UPDATE pagos_nomina SET numero_referencia=? WHERE id=?', f'TEMP-REF-NOM-{pid}', pid)
        for pid, anterior, nueva in cambios:
            cur.execute('UPDATE pagos_nomina SET numero_referencia=? WHERE id=?', nueva, pid)
            cur.execute('''INSERT INTO carga_negocio_cambios
                (carga_id,tabla,registro_id,campo,antes,despues) VALUES(?,?,?,?,?,?)''',
                carga[0], 'pagos_nomina', pid, 'numero_referencia', anterior, nueva)
        conn.commit()
        print(json.dumps({'referencias_actualizadas':len(cambios), 'pagos_por_anio':dict(conteos)}))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
