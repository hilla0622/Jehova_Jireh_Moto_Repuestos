"""Corrige la modalidad de retiro de los pedidos generados para la feria."""
import json
from app import get_db_connection


def main():
    conn = get_db_connection()
    if conn is None:
        raise RuntimeError('No se pudo conectar a la base de datos')
    try:
        cur = conn.cursor()
        cur.execute('SET XACT_ABORT ON')
        cur.execute("""SELECT r.carga_id,p.id,p.formaEntrega,p.direccion_entrega
            FROM pedidos_web p JOIN carga_negocio_registros r
              ON r.tabla='pedidos_web' AND r.registro_id=p.id
            JOIN cargas_negocio c ON c.id=r.carga_id
            WHERE c.version='NEGOCIO-2024-2026-V1'""")
        cambios = []
        pedidos = set()
        for carga, pid, forma, direccion in cur.fetchall():
            for campo, antes, despues in (
                ('formaEntrega', forma, 'Retiro en Tienda'),
                ('direccion_entrega', direccion, 'Retiro en Tienda (Sucursal Masatepe)'),
            ):
                if antes != despues:
                    cur.execute(f'UPDATE pedidos_web SET [{campo}]=? WHERE id=?', despues, pid)
                    cambios.append((carga, 'pedidos_web', pid, campo, antes, despues))
                    pedidos.add(pid)
        if cambios:
            cur.executemany('''INSERT INTO carga_negocio_cambios
                (carga_id,tabla,registro_id,campo,antes,despues) VALUES(?,?,?,?,?,?)''', cambios)
        cur.execute("""SELECT COUNT(*) FROM pedidos_web p
            JOIN carga_negocio_registros r ON r.tabla='pedidos_web' AND r.registro_id=p.id
            JOIN cargas_negocio c ON c.id=r.carga_id
            WHERE c.version='NEGOCIO-2024-2026-V1'
              AND (ISNULL(p.formaEntrega,'')<>N'Retiro en Tienda'
                OR ISNULL(p.direccion_entrega,'')<>N'Retiro en Tienda (Sucursal Masatepe)')""")
        if cur.fetchone()[0]:
            raise RuntimeError('Quedan pedidos generados sin corregir')
        conn.commit()
        print(json.dumps({'pedidos_corregidos': len(pedidos), 'campos_corregidos': len(cambios)}))
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    main()
