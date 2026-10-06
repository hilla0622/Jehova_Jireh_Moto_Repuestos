import pyodbc
import os

DB_SERVER = os.environ.get('DB_SERVER', r'HILLARY')
DB_NAME = 'jehova_jireh_db'

conn_str = (
    r'DRIVER={ODBC Driver 17 for SQL Server};'
    fr'SERVER={DB_SERVER};'
    fr'DATABASE={DB_NAME};'
    r'Trusted_Connection=yes;'
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()

# Create devoluciones table
cursor.execute("""
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='devoluciones' AND xtype='U')
CREATE TABLE devoluciones (
    id INT IDENTITY(1,1) PRIMARY KEY,
    venta_id INT NOT NULL,
    codigo_devolucion VARCHAR(20) NOT NULL,
    fecha DATETIME DEFAULT GETDATE(),
    motivo VARCHAR(500) NOT NULL,
    total_devuelto DECIMAL(12,2) NOT NULL,
    usuario_id INT NOT NULL,
    FOREIGN KEY (venta_id) REFERENCES ventas(id),
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
)
""")
print("Table 'devoluciones' created or already exists.")

# Create detalle_devoluciones table
cursor.execute("""
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='detalle_devoluciones' AND xtype='U')
CREATE TABLE detalle_devoluciones (
    id INT IDENTITY(1,1) PRIMARY KEY,
    devolucion_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(12,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    FOREIGN KEY (devolucion_id) REFERENCES devoluciones(id),
    FOREIGN KEY (producto_id) REFERENCES productos(id)
)
""")
print("Table 'detalle_devoluciones' created or already exists.")

conn.commit()
cursor.close()
conn.close()
print("Database migration completed successfully!")
