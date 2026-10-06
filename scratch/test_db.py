import pyodbc
from datetime import datetime

conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=HILLARY;'
    r'DATABASE=jehova_jireh_db;'
    r'Trusted_Connection=yes;'
)
try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    # Let's find an account ID
    cursor.execute("SELECT TOP 1 id FROM cuentas_contables")
    row = cursor.fetchone()
    if row:
        cuenta_id = row[0]
        print("Testing with cuenta_id:", cuenta_id)
        
        query_movs = '''
            SELECT a.id as asiento_id, a.fecha, a.concepto, m.debe, m.haber
            FROM movimientos_contables m
            INNER JOIN asientos_contables a ON a.id = m.asiento_id
            WHERE m.cuenta_id = ?
        '''
        cursor.execute(query_movs, (cuenta_id,))
        results = cursor.fetchall()
        print("Results:")
        for r in results:
            print(r.asiento_id, r.fecha, type(r.fecha), r.concepto, r.debe, r.haber)
            
    conn.close()
except Exception as e:
    print("DB Error:", e)
