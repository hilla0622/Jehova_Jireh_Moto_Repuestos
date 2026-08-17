import sqlite3
import os

def init_sqlite_db():
    db_path = os.path.join(os.path.dirname(__file__), 'jehova_jireh.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Enable foreign keys in SQLite
    cursor.execute("PRAGMA foreign_keys = ON;")

    # 1. ROLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. USUARIOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rol_id INTEGER NOT NULL,
        username TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        nombre_completo TEXT NOT NULL,
        email TEXT UNIQUE,
        telefono TEXT,
        activo INTEGER DEFAULT 1,
        ultimo_acceso TIMESTAMP,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (rol_id) REFERENCES roles(id)
    );
    """)

    # 3. CATEGORIAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS categorias (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT NOT NULL UNIQUE,
        descripcion TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. CLIENTES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_completo TEXT NOT NULL,
        identificacion TEXT,
        telefono TEXT,
        email TEXT,
        direccion TEXT,
        tipo_cliente TEXT DEFAULT 'General',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. PROVEEDORES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS proveedores (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_empresa TEXT NOT NULL,
        contacto_nombre TEXT,
        identificacion_fiscal TEXT,
        telefono TEXT NOT NULL,
        email TEXT,
        direccion TEXT,
        activo INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 6. PRODUCTOS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS productos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_sku TEXT NOT NULL UNIQUE,
        codigo_barras TEXT UNIQUE,
        categoria_id INTEGER NOT NULL,
        nombre TEXT NOT NULL,
        descripcion TEXT,
        marca TEXT,
        modelo_compatible TEXT,
        ubicacion_estante TEXT,
        costo REAL NOT NULL DEFAULT 0.0,
        precio_venta REAL NOT NULL DEFAULT 0.0,
        stock_actual INTEGER NOT NULL DEFAULT 0,
        stock_minimo INTEGER NOT NULL DEFAULT 5,
        activo INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (categoria_id) REFERENCES categorias(id)
    );
    """)

    # 7. COMPRAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_compra TEXT NOT NULL UNIQUE,
        numero_factura_proveedor TEXT,
        proveedor_id INTEGER NOT NULL,
        usuario_id INTEGER NOT NULL,
        fecha_compra TEXT NOT NULL,
        total REAL NOT NULL DEFAULT 0.0,
        forma_pago TEXT DEFAULT 'Efectivo',
        estado TEXT DEFAULT 'Completada',
        observaciones TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    );
    """)

    # 8. DETALLE COMPRAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalle_compras (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        compra_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        costo_unitario REAL NOT NULL,
        subtotal REAL NOT NULL,
        FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    );
    """)

    # 9. VENTAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo_venta TEXT NOT NULL UNIQUE,
        cliente_id INTEGER,
        usuario_id INTEGER NOT NULL,
        fecha_venta TEXT NOT NULL,
        subtotal REAL NOT NULL DEFAULT 0.0,
        descuento REAL NOT NULL DEFAULT 0.0,
        total REAL NOT NULL DEFAULT 0.0,
        forma_pago TEXT DEFAULT 'Efectivo',
        estado TEXT DEFAULT 'Completada',
        notas TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (cliente_id) REFERENCES clientes(id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    );
    """)

    # 10. DETALLE VENTAS
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS detalle_ventas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        venta_id INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        cantidad INTEGER NOT NULL,
        precio_unitario REAL NOT NULL,
        costo_historico REAL NOT NULL DEFAULT 0.0,
        subtotal REAL NOT NULL,
        FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
        FOREIGN KEY (producto_id) REFERENCES productos(id)
    );
    """)

    # 11. MOVIMIENTOS INVENTARIO (KARDEX)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_inventario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        producto_id INTEGER NOT NULL,
        tipo_movimiento TEXT NOT NULL,
        cantidad INTEGER NOT NULL,
        stock_anterior INTEGER NOT NULL DEFAULT 0,
        stock_posterior INTEGER NOT NULL DEFAULT 0,
        referencia_origen TEXT,
        motivo TEXT NOT NULL,
        usuario_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (producto_id) REFERENCES productos(id),
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    );
    """)

    # SEED DATA (DATOS INICIALES)
    # Roles
    cursor.executemany("INSERT OR IGNORE INTO roles (id, nombre, descripcion) VALUES (?, ?, ?)", [
        (1, 'Administrador', 'Control total administrativo, reportes financieros y usuarios'),
        (2, 'Vendedor', 'Atención en punto de venta, emisión de facturas y cobros'),
        (3, 'Encargado de Inventario', 'Ingreso de compras, gestión de stock, ajustes y Kardex'),
        (4, 'Contador', 'Acceso a balances contables, reportes de compras y ventas')
    ])

    # Usuarios
    cursor.executemany("INSERT OR IGNORE INTO usuarios (id, rol_id, username, password_hash, nombre_completo, email, telefono) VALUES (?, ?, ?, ?, ?, ?, ?)", [
        (1, 1, 'admin', '123', 'Gilda Pérez', 'admin@jehovajireh.com', '+505 8888-0001'),
        (2, 2, 'vendedor', '123', 'Ana Gómez', 'ventas@jehovajireh.com', '+505 8888-0002'),
        (3, 3, 'inventario', '123', 'Roberto Silva', 'bodega@jehovajireh.com', '+505 8888-0003'),
        (4, 4, 'contador', '123', 'Lic. Fernando Rivas (Granada)', 'contabilidad@jehovajireh.com', '+505 8888-0004')
    ])

    # Categorías
    cursor.executemany("INSERT OR IGNORE INTO categorias (id, nombre, descripcion) VALUES (?, ?, ?)", [
        (1, 'Frenos', 'Pastillas, zapatas, discos, bombas y líquidos de freno'),
        (2, 'Transmisión', 'Kits de arrastre, cadenas, piñones, coronas y bandas'),
        (3, 'Lubricantes', 'Aceites 2T, 4T minerales, semi-sintéticos y aditivos'),
        (4, 'Motor / Encendido', 'Bujías, pistones, anillos, empaquetaduras y carburadores'),
        (5, 'Eléctrico', 'Baterías de gel, focos LED, bobinas, reguladores y cables'),
        (6, 'Suspensión', 'Amortiguadores, barras telescópicas y retenes'),
        (7, 'Llantas y Neumáticos', 'Llantas pisteras, todo terreno, cámaras y parches')
    ])

    # Clientes
    cursor.executemany("INSERT OR IGNORE INTO clientes (id, nombre_completo, identificacion, telefono, email, tipo_cliente) VALUES (?, ?, ?, ?, ?, ?)", [
        (1, 'Cliente General (Mostrador)', '000-000000-0000X', '2222-0000', 'mostrador@jehovajireh.com', 'General'),
        (2, 'Taller Hermanos Mendoza', '401-150885-0002K', '+505 8444-1234', 'taller.mendoza@gmail.com', 'Taller'),
        (3, 'Carlos Estrada', '001-200392-0044L', '+505 8999-5544', 'carlos.estrada@yahoo.com', 'Frecuente')
    ])

    # Proveedores
    cursor.executemany("INSERT OR IGNORE INTO proveedores (id, nombre_empresa, contacto_nombre, identificacion_fiscal, telefono, email, direccion) VALUES (?, ?, ?, ?, ?, ?, ?)", [
        (1, 'Distribuidora Repuestos del Pacífico', 'Mario López', 'J0310000123456', '+505 8899-1122', 'ventas@pacificomotos.com', 'Managua, Pista Juan Pablo II'),
        (2, 'Importadora Global Moto Parts', 'Elena Morales', 'J0310000987654', '+505 7766-3344', 'contacto@globalmotoparts.com', 'Masaya, Km 28 Carretera a Granada')
    ])

    # Productos
    cursor.executemany("INSERT OR IGNORE INTO productos (id, codigo_sku, categoria_id, nombre, marca, modelo_compatible, costo, precio_venta, stock_actual, stock_minimo) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, 'REP-001', 1, 'Pastillas de Freno Delanteras Yamaha YBR 125', 'Yamaha Genuine', 'YBR 125 / SZ-R', 9.00, 15.50, 18, 5),
        (2, 'REP-002', 2, 'Kit de Arrastre Cadena y Piñón Pulsar 200 NS', 'Choho Racing', 'Pulsar 200 NS / RS / AS', 30.00, 45.00, 3, 5),
        (3, 'REP-003', 3, 'Aceite 4T 20W50 Mineral Motul 1L', 'Motul', 'Motos 4 Tiempos Universal', 7.50, 12.00, 40, 10),
        (4, 'REP-004', 4, 'Bujía NGK C7HSA para pasola/motos 125cc', 'NGK', 'Scooter / Pasola 125cc - 150cc', 2.20, 4.50, 25, 8),
        (5, 'REP-005', 5, 'Batería de Gel 12V 7Ah Moto Scooter', 'Dynavolt', 'Scooter, Pulsar 135, Mensajeras', 22.00, 35.00, 2, 4)
    ])

    # Compras
    cursor.executemany("INSERT OR IGNORE INTO compras (id, codigo_compra, numero_factura_proveedor, proveedor_id, usuario_id, fecha_compra, total, forma_pago, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, 'COM-#1', 'FAC-PAC-9082', 1, 3, '2026-08-05', 180.00, 'Transferencia', 'Completada')
    ])

    cursor.executemany("INSERT OR IGNORE INTO detalle_compras (id, compra_id, producto_id, cantidad, costo_unitario, subtotal) VALUES (?, ?, ?, ?, ?, ?)", [
        (1, 1, 1, 20, 9.00, 180.00)
    ])

    # Ventas
    cursor.executemany("INSERT OR IGNORE INTO ventas (id, codigo_venta, cliente_id, usuario_id, fecha_venta, subtotal, descuento, total, forma_pago, estado) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, 'VEN-0001', 1, 2, '2026-08-09', 27.50, 0.00, 27.50, 'Efectivo', 'Completada')
    ])

    cursor.executemany("INSERT OR IGNORE INTO detalle_ventas (id, venta_id, producto_id, cantidad, precio_unitario, costo_historico, subtotal) VALUES (?, ?, ?, ?, ?, ?, ?)", [
        (1, 1, 1, 1, 15.50, 9.00, 15.50),
        (2, 1, 3, 1, 12.00, 7.50, 12.00)
    ])

    # Kardex
    cursor.executemany("INSERT OR IGNORE INTO movimientos_inventario (id, fecha, producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, referencia_origen, motivo, usuario_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, '2026-08-01 08:00:00', 1, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1),
        (2, '2026-08-05 10:30:00', 1, 'ENTRADA_COMPRA', 20, 20, 40, 'Compra COM-#1', 'Compra COM-#1 - Distribuidora Repuestos del Pacífico', 3),
        (3, '2026-08-09 14:15:00', 1, 'SALIDA_VENTA', 1, 40, 39, 'Venta VEN-0001', 'Venta mostrador VEN-0001', 2),
        (4, '2026-08-09 14:15:00', 3, 'SALIDA_VENTA', 1, 41, 40, 'Venta VEN-0001', 'Venta mostrador VEN-0001', 2)
    ])

    conn.commit()
    conn.close()
    print(f"Base de datos SQLite generada exitosamente en: {db_path}")

if __name__ == '__main__':
    init_sqlite_db()
