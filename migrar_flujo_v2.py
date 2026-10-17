"""Migración aditiva RF96-RF102. Ejecutar después de migrar_modulo_flujo_efectivo.py.

No modifica asientos ni saldos. Una única transacción; falla sin cambios ante errores.
"""
import argparse
import os
import pyodbc
from migrar_modulo_flujo_efectivo import get_connection


def run_migration(server=None, database='jehova_jireh_db'):
    server = server or os.environ.get('DB_SERVER')
    if server or database != 'jehova_jireh_db':
        server = server or os.environ.get('COMPUTERNAME', '.')
        conn = pyodbc.connect(
            f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;',
            timeout=5)
    else:
        conn = get_connection()
    conn.autocommit = False
    try:
        cursor = conn.cursor()
        cursor.execute("""
            IF COL_LENGTH('cuentas_contables', 'flujo_categoria') IS NULL
                THROW 50001, 'Ejecute primero migrar_modulo_flujo_efectivo.py', 1;
            IF COL_LENGTH('cuentas_contables', 'ajuste_no_monetario') IS NULL
            BEGIN
                ALTER TABLE cuentas_contables ADD ajuste_no_monetario BIT NOT NULL
                    CONSTRAINT DF_cuentas_ajuste_no_monetario DEFAULT 0;
            END;
        """)
        cursor.execute("""
            IF OBJECT_ID('flujo_eventos', 'U') IS NULL
            BEGIN
                CREATE TABLE flujo_eventos (
                    id INT IDENTITY(1,1) PRIMARY KEY,
                    tipo VARCHAR(30) NOT NULL,
                    clave VARCHAR(100) NOT NULL,
                    contenido NVARCHAR(MAX) NOT NULL,
                    motivo NVARCHAR(1000) NOT NULL,
                    usuario_id INT NOT NULL REFERENCES usuarios(id),
                    created_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME()
                );
                CREATE INDEX IX_flujo_eventos_tipo_clave ON flujo_eventos(tipo, clave, id);
                UPDATE cuentas_contables SET ajuste_no_monetario = 1 WHERE codigo = '6.1.09';
            END;
            IF EXISTS (SELECT cuenta_id, anio, mes FROM conciliaciones_bancarias
                       GROUP BY cuenta_id, anio, mes HAVING COUNT(*) > 1)
                THROW 50002, 'Existen conciliaciones duplicadas. Revisarlas antes de migrar.', 1;
            IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_conciliacion_periodo'
                           AND object_id = OBJECT_ID('conciliaciones_bancarias'))
                CREATE UNIQUE INDEX UX_conciliacion_periodo
                    ON conciliaciones_bancarias(cuenta_id, anio, mes);
        """)
        conn.commit()
        print('Migración de flujo v2 completada. No se modificaron saldos ni asientos.')
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--server', help='Instancia SQL Server; por defecto DB_SERVER o servidor local.')
    parser.add_argument('--database', default='jehova_jireh_db', help='Base destino; permite verificar sobre una copia.')
    args = parser.parse_args()
    run_migration(args.server, args.database)
