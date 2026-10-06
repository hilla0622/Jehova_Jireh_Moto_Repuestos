import pyodbc

conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=HILLARY;'
    r'DATABASE=jehova_jireh_db;'
    r'Trusted_Connection=yes;'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

new_roles = [
    'Gerente de Operaciones',
    'Gerente Administrativo y Financiero',
    'Encargado de Compras y Proveedores',
    'Responsable de Recursos Humanos'
]

for role in new_roles:
    cursor.execute("SELECT id FROM roles WHERE nombre = ?", (role,))
    if not cursor.fetchone():
        cursor.execute("INSERT INTO roles (nombre) VALUES (?)", (role,))
        
conn.commit()
print("Roles updated successfully.")
conn.close()
