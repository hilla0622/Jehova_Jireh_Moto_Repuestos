import pyodbc

conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=HILLARY;'
    r'DATABASE=jehova_jireh_db;'
    r'Trusted_Connection=yes;'
)

try:
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()

    cuentas_nuevas = [
        ('2.1.06', 'Retenciones INSS por pagar', 'Pasivo corriente', 'Acreedora', 'INSS Laboral y Patronal pendiente de pago.'),
        ('2.1.07', 'Retenciones IR por pagar', 'Pasivo corriente', 'Acreedora', 'Impuesto sobre la renta retenido a empleados.'),
        ('2.1.08', 'Provisiones sociales por pagar', 'Pasivo corriente', 'Acreedora', 'Vacaciones y Aguinaldo acumulado.'),
        ('6.1.11', 'Cargas sociales patronales', 'Gasto', 'Deudora', 'Gasto por cuota patronal del INSS.'),
        ('6.1.12', 'Prestaciones sociales', 'Gasto', 'Deudora', 'Gasto por vacaciones y aguinaldo de los empleados.')
    ]

    for codigo, nombre, clasif, nat, desc in cuentas_nuevas:
        cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = ?", (codigo,))
        if not cursor.fetchone():
            cursor.execute('''
                INSERT INTO cuentas_contables (codigo, nombre, clasificacion, naturaleza, descripcion)
                VALUES (?, ?, ?, ?, ?)
            ''', (codigo, nombre, clasif, nat, desc))
            print(f"Insertada: {codigo} - {nombre}")
        else:
            print(f"Ya existe: {codigo} - {nombre}")

    conn.commit()
    print("Cuentas actualizadas.")
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
