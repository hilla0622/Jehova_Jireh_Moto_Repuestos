import pyodbc

conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    r'SERVER=HILLARY;'
    r'DATABASE=jehova_jireh_db;'
    r'Trusted_Connection=yes;'
)
conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

new_users = [
    ('Gerente de Operaciones', 'gerente_op', '123', 'Gerente de Operaciones', 'gerente_op@jehovajireh.com'),
    ('Gerente Administrativo y Financiero', 'gerente_admin', '123', 'Gerente Admin Financiero', 'gerente_admin@jehovajireh.com'),
    ('Encargado de Compras y Proveedores', 'encargado_comp', '123', 'Encargado de Compras', 'compras@jehovajireh.com'),
    ('Responsable de Recursos Humanos', 'rrhh', '123', 'Responsable RRHH', 'rrhh@jehovajireh.com')
]

for role_name, username, password, full_name, email in new_users:
    # Get role ID
    cursor.execute("SELECT id FROM roles WHERE nombre = ?", (role_name,))
    role_row = cursor.fetchone()
    if role_row:
        role_id = role_row.id
        # Check if user exists
        cursor.execute("SELECT id FROM usuarios WHERE username = ?", (username,))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO usuarios (rol_id, username, password_hash, nombre_completo, email, activo)
                VALUES (?, ?, ?, ?, ?, 1)
            """, (role_id, username, password, full_name, email))

conn.commit()
print("New users inserted successfully.")
conn.close()
