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

    # 12. CUENTAS CONTABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS cuentas_contables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT NOT NULL UNIQUE,
        nombre TEXT NOT NULL,
        clasificacion TEXT NOT NULL,
        naturaleza TEXT NOT NULL CHECK (naturaleza IN ('Deudora', 'Acreedora')),
        descripcion TEXT,
        activo INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 13. ASIENTOS CONTABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS asientos_contables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT NOT NULL,
        concepto TEXT NOT NULL,
        modulo_origen TEXT,
        referencia_id INTEGER,
        usuario_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
    );
    """)

    # 14. MOVIMIENTOS CONTABLES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS movimientos_contables (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        asiento_id INTEGER NOT NULL,
        cuenta_id INTEGER NOT NULL,
        debe REAL NOT NULL DEFAULT 0.00,
        haber REAL NOT NULL DEFAULT 0.00,
        FOREIGN KEY (asiento_id) REFERENCES asientos_contables(id) ON DELETE CASCADE,
        FOREIGN KEY (cuenta_id) REFERENCES cuentas_contables(id),
        CHECK (debe >= 0 AND haber >= 0 AND (debe > 0 OR haber > 0))
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
        (1, 'Motor y Partes Internas', 'Cilindros completos, pistones, anillos de pistón, bielas, válvulas, árbol de levas, balancines, empaques de motor, cadenas de tiempo y bombas de lubricación.'),
        (2, 'Sistema Eléctrico y Encendido', 'Cerebros CDI, bobinas de alta/motor, motores de arranque, carbones, bombillos, relays, fusibles, rectificadores, ignición, mandos de luces/start y sistema eléctrico.'),
        (3, 'Transmisión y Embrague', 'Cajas de cambios, kit de sprockets (catalinas y piñones), discos/fricciones de clutch, canastas de clutch, cadenas de tracción y bandas de tracción (scooters).'),
        (4, 'Sistema de Frenos', 'Bombas de freno (delanteras y traseras), mangueras de freno y varillas de freno.'),
        (5, 'Suspensión y Dirección', 'Amortiguadores, cunas de poste, bushing de tijera y retenedores de barras.'),
        (6, 'Carburación y Combustible', 'Carburadores, llaves de combustible y tapones de tanque.'),
        (7, 'Cables y Controles', 'Cables de acelerador, cables de clutch, manecillas de clutch y pedales (de encendido y de cambios).'),
        (8, 'Chasis y Accesorios', 'Asientos, guardafangos, capas cubre moto, pitos (bocinas) y espejos/viseras.'),
        (9, 'Rodamientos y Misceláneos', 'Todas las balineras, sellos de válvulas, herramientas, aceites y otros.')
    ])

    # Productos
    cursor.executemany("INSERT OR IGNORE INTO productos (id, codigo_sku, categoria_id, nombre, costo, precio_venta, stock_actual, stock_minimo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", [
        (1, 'MAN037', 5, 'AMORTIGUADOR AKT TT150-180 - GENESIS SX200 VINI', 1661.75, 2326.45, 3, 5),
        (2, 'AMO026', 5, 'AMORTIGUADORES GN125H VINI', 833.0, 1166.2, 5, 5),
        (3, 'AMO033', 4, 'AMORTIGUADORES PULSAR 135-DISCOVER VINI', 1462.0, 2046.8, 5, 5),
        (4, 'Ani088', 1, 'ANILLOS DE PISTON AG200 A MEDIDA 0.25 VINI', 127.5, 178.5, 10, 5),
        (5, 'Ani089', 1, 'ANILLOS DE PISTON AG200 A MEDIDA 0.50 VINI', 127.5, 178.5, 10, 5),
        (6, 'Ani059', 1, 'ANILLOS DE PISTON AG200-UM200-RAYBAR200 (67MM*15MM) STD VINI', 136.0, 190.4, 10, 5),
        (7, 'Ani086', 1, 'ANILLOS DE PISTON CG150 STD VINI', 85.0, 119.0, 20, 5),
        (8, 'Ani060', 1, 'ANILLOS DE PISTON CG200-WY200 63.5 MM STD VINI', 93.5, 130.9, 20, 5),
        (9, 'Ani061', 1, 'ANILLOS DE PISTON GXT200-DR200 66MM STD VINI', 136.0, 190.4, 10, 5),
        (10, 'Ani018', 1, 'ANILLOS DE PISTON GY200 69MM-198CM STD VINI', 106.25, 148.75, 10, 5),
        (11, 'Ani062', 1, 'ANILLOS DE PISTON PULSAR 135-XCD125-PLATINA125 STD VINI', 125.8, 176.12, 20, 5),
        (12, 'Ani066', 1, 'ANILLOS DE PISTON PULSAR 180 UG3-UG4 STD VINI', 136.0, 190.4, 20, 5),
        (13, 'Ani098', 1, 'ANILLOS DE PISTON PULSAR NS200 STD VINI', 136.0, 190.4, 20, 5),
        (14, 'ARB050', 1, 'ARBOL DE LEVAS AKT CR5 180 VINI', 433.5, 606.9, 10, 5),
        (15, 'ARB032', 1, 'ARBOL DE LEVAS CG-GY200 NO BALANZA COMPLETA VINI', 357.0, 499.8, 20, 5),
        (16, 'ARB042', 1, 'ARBOL DE LEVAS PULSAR 135 VINI', 365.5, 511.7, 20, 5),
        (17, 'ARB058', 1, 'ARBOL DE LEVAS SCOOTER 125-150 VINI', 272.0, 380.8, 10, 5),
        (18, 'ARB051', 1, 'ARBOL DE LEVAS WY200-JH150 MOTOR CADENA BUSHING VINI', 331.5, 464.1, 10, 5),
        (19, 'ASI015', 8, 'ASIENTO CG RACING MODIFIC AZUL VINI', 841.5, 1178.1, 4, 5),
        (20, 'Asi023', 8, 'ASIENTO CG RACING MODIFIED VINI', 765.0, 1071.0, 5, 5),
        (21, 'Asi021', 8, 'ASIENTO RAYBAR 200-NXR125 BROSS-UM DSR 2026 VINI', 697.0, 975.8, 2, 5),
        (22, 'BLN060', 1, 'BALANCINES DE MOTOR AN125 VINI', 119.0, 166.6, 10, 5),
        (23, 'BLN061', 1, 'BALANCINES DE MOTOR APACHE160-180 VINI', 289.0, 404.6, 5, 5),
        (24, 'BLN041', 1, 'BALANCINES DE MOTOR COMPLETOS HJ125-CG150-CG200 VINI', 144.5, 202.3, 15, 5),
        (25, 'BLN042', 1, 'BALANCINES DE MOTOR WY125-JH150-WY200 VINI', 161.5, 226.1, 15, 5),
        (26, 'Bal127', 9, 'BALINERA 6004 2RS VINI', 38.25, 53.55, 50, 5),
        (27, 'Bal147', 9, 'BALINERA 6005 2RS VINI', 49.3, 69.02, 50, 5),
        (28, 'Bal148', 9, 'BALINERA 6006 2RS VINI', 62.9, 88.06, 50, 5),
        (29, 'Bal108', 9, 'BALINERA 6202 2RS VINI', 32.3, 45.22, 60, 5),
        (30, 'Bal1013', 9, 'BALINERA 6204 2RS VINI', 49.3, 69.02, 50, 5),
        (31, 'Bal020', 9, 'BALINERA 6301 2RS VINI', 38.25, 53.55, 60, 5),
        (32, 'Bal100', 9, 'BALINERA 6302 2RS VINI', 40.8, 57.12, 50, 5),
        (33, 'Bal125', 9, 'BALINERA DE CIGUEÑAL 6205 2RS YBR-XTZ VINI', 86.7, 121.38, 10, 5),
        (34, 'Bal083', 9, 'BALINERA DE CIGUEÑAL 63-28 28MM*68MM VINI', 136.0, 190.4, 20, 5),
        (35, 'Bal084', 9, 'BALINERA DE CIGUEÑAL 63-28 P5 28MM*72MM VINI', 165.75, 232.05, 20, 5),
        (36, 'Bal082', 9, 'BALINERA DE CIGUEÑAL PULSAR135-BOXER-DISC-PLATINA VINI', 136.0, 190.4, 20, 5),
        (37, 'Bal149', 2, 'BALINERA DE MOTOR DE ARRANQUE CG HK1010 VINI', 17.85, 24.99, 30, 5),
        (38, 'Bal079', 9, 'BALINERA DE PROPULSOR CG200 NK 152312 VINI', 34.0, 47.6, 30, 5),
        (39, 'BAN005', 3, 'BANDA DE TRACCION SCOOTER GY6125 835x20x30 VINI', 225.25, 315.35, 20, 5),
        (40, 'Bie066', 1, 'BIELA KIT AKT150TT-NKD125 NXR125 BROSS-XR125L VINI', 348.5, 487.9, 10, 5),
        (41, 'Bie043', 1, 'BIELA KIT GXT200-DR200 VINI', 527.0, 737.8, 10, 5),
        (42, 'Bie053', 1, 'BIELA KIT PULSAR135-PLATINA125-BM150 VINI', 365.5, 511.7, 10, 5),
        (43, 'Bie063', 1, 'BIELA KIT XCD125-PLATINA 125-DISCOVER 125 ST VINI', 323.0, 452.2, 10, 5),
        (44, 'Bie040', 1, 'BIELA KIT XL185-XL125-CG150-CG125 VINI', 323.0, 452.2, 10, 5),
        (45, 'Bie048', 1, 'BIELA KIT YBR125-XTZ125 VINI', 331.5, 464.1, 10, 5),
        (46, 'Bie068', 1, 'BIELA KIT YUMBO200-UM200-PULSAR180 VINI', 408.0, 571.2, 5, 5),
        (47, 'BOB098', 2, 'BOBINA DE ALTA CG-AKT TT150-EVO150 1 LINEA VINI', 119.0, 166.6, 20, 5),
        (48, 'BOB079', 2, 'BOBINA DE MOTOR AKT CR5 VINI', 578.0, 809.2, 10, 5),
        (49, 'BOB058', 2, 'BOBINA DE MOTOR CG 8X3 MOTOR VARILLA VINI', 408.0, 571.2, 10, 5),
        (50, 'BOB059', 2, 'BOBINA DE MOTOR DISCOVER 125 ST VINI', 510.0, 714.0, 5, 5),
        (51, 'BOB073', 2, 'BOBINA DE MOTOR GN125H-GXT200 VINI', 578.0, 809.2, 5, 5),
        (52, 'BOM039', 1, 'BOMBA DE FRENO DELANTERA HJ125-GN125 BLANCA VINI', 233.75, 327.25, 10, 5),
        (53, 'BOM046', 1, 'BOMBA DE FRENO DELANTERA PULSAR 135-180-220 VINI', 314.5, 440.3, 10, 5),
        (54, 'BOM066', 1, 'BOMBA DE FRENO DELANTERA XL-GY200 NEGRA VINI', 255.0, 357.0, 10, 5),
        (55, 'BOM087', 1, 'BOMBA DE FRENO TRASERA COMPLETA PULSAR NS200-RS200-180-220 VINI', 254.15, 355.81, 10, 5),
        (56, 'BOM067', 1, 'BOMBA DE FRENO TRASERA DAYUN150-CON DEPOSITO VINI', 272.0, 380.8, 10, 5),
        (57, 'BOM088', 1, 'BOMBA DE LUBRICACION AX100 VINI', 552.5, 773.5, 5, 5),
        (58, 'BOM044', 1, 'BOMBA DE LUBRICACION CG150 39D C-ORING VINI', 114.75, 160.65, 30, 5),
        (59, 'BOM073', 1, 'BOMBA DE LUBRICACION YUMBO 200-YARA 200 37D VINI', 110.5, 154.7, 20, 5),
        (60, 'BUJ122', 2, 'BOMBILLO DE PIDEVIAS 12V VINI', 5.06, 7.08, 100, 5),
        (61, 'BUJ081', 2, 'BOMBILLO DE STOP 12V VINI', 7.23, 10.12, 100, 5),
        (62, 'BUC036', 5, 'BUSHING DE TIJERA KIT + EJE AKT TT150-TT180 VINI', 187.0, 261.8, 10, 5),
        (63, 'BUC059', 5, 'BUSHING DE TIJERA KIT + EJE GY200-JH125L-XL185S VINI', 144.5, 202.3, 10, 5),
        (64, 'BUC066', 5, 'BUSHING DE TIJERA KIT + EJE RAYBAR 200 VINI', 187.0, 261.8, 10, 5),
        (65, 'CAB193', 7, 'CABLE ACELERADOR CG-WY VINI', 44.2, 61.88, 30, 5),
        (66, 'CAB211', 7, 'CABLE ACELERADOR GIXXER 150 VINI', 72.25, 101.15, 20, 5),
        (67, 'CAB187', 7, 'CABLE ACELERADOR GXT200 VINI', 44.2, 61.88, 20, 5),
        (68, 'CAB143', 7, 'CABLE ACELERADOR PULSAR 135 VINI', 46.75, 65.45, 30, 5),
        (69, 'CAB144', 7, 'CABLE ACELERADOR PULSAR180-220 VINI', 46.75, 65.45, 30, 5),
        (70, 'CAB212', 3, 'CABLE CLUTCH CGL125 VINI', 46.75, 65.45, 20, 5),
        (71, 'CAB213', 3, 'CABLE CLUTCH GN125H VINI', 55.25, 77.35, 20, 5),
        (72, 'CAB314', 3, 'CABLE CLUTCH HJ125-7 VINI', 46.75, 65.45, 30, 5),
        (73, 'CAB131', 3, 'CABLE CLUTCH XTZ125 (2012-2018) C-POLVERA VINI', 68.0, 95.2, 10, 5),
        (74, 'CAB190', 3, 'CABLE CLUTCH YBR125 VINI', 83.3, 116.62, 20, 5),
        (75, 'CAB090', 2, 'CABLE DE BOBINA ALTA UNIVERSAL ROLLO', 246.5, 345.1, 100, 5),
        (76, 'CAB156', 4, 'CABLE FRENO YBR125 VINI', 83.3, 116.62, 10, 5),
        (77, 'CAD081', 3, 'CADENA DE LUBRICACION RAYBAR200-RKS150 CONTRAPESA VINI', 59.5, 83.3, 20, 5),
        (78, 'CAD032', 1, 'CADENA DE TIEMPO AKT CR5 VINI', 119.0, 166.6, 20, 5),
        (79, 'CAD094', 1, 'CADENA DE TIEMPO APACHE 150-160-180 (409H 94L) VINI', 161.5, 226.1, 20, 5),
        (80, 'CAD095', 1, 'CADENA DE TIEMPO CRF230-XT250 SERROW (2X3H 104L) VINI', 114.75, 160.65, 10, 5),
        (81, 'CAD062', 1, 'CADENA DE TIEMPO PULSAR NS200-AS200-RS200(94L) VINI', 161.5, 226.1, 20, 5),
        (82, 'CAD074', 1, 'CADENA DE TIEMPO SCOOTER-150F-22 (90L) VINI', 127.5, 178.5, 20, 5),
        (83, 'CAD071', 1, 'CADENA DE TIEMPO XTZ125-YBR125 2006 2X3L 90L ORUGA VINI', 127.5, 178.5, 20, 5),
        (84, 'CAD096', 1, 'CADENA DE TIEMPO YUMBO200 (3X4H 100L) VINI', 144.5, 202.3, 20, 5),
        (85, 'CAD061', 3, 'CADENA DE TRACCION 520X120L EXTRA REFORZADA DORADA VINI', 344.25, 481.95, 20, 5),
        (86, 'CAJ001', 3, 'CAJA DE CAMBIOS AKT180TT-CR5 (6 CAMBIOS) VINI', 1249.5, 1749.3, 5, 5),
        (87, 'CAJ023', 3, 'CAJA DE CAMBIOS CG125-CG150-AKT 150 VINI', 935.0, 1309.0, 5, 5),
        (88, 'CAJ029', 3, 'CAJA DE CAMBIOS CG200-RAYBAR200-250-UM200-CONTRAPESA VINI', 1190.0, 1666.0, 5, 5),
        (89, 'CAJ046', 3, 'CAJA DE CAMBIOS GXT200 VINI', 2125.0, 2975.0, 5, 5),
        (90, 'CAJ047', 3, 'CAJA DE CAMBIOS PULSAR NS125-BOXER150X MODERNA VINI', 1377.0, 1927.8, 2, 5),
        (91, 'ARA050', 3, 'CANASTA CLUTCH AKT CR5-TT 180 (SOLA) VINI', 442.0, 618.8, 10, 5),
        (92, 'ARA051', 3, 'CANASTA CLUTCH CG125-CG150-RKS150 73T COMPLETA VINI', 637.5, 892.5, 5, 5),
        (93, 'DIR326', 8, 'CAPA CUBRE MOTO PREMIUM UNIVERSAL VINI', 382.5, 535.5, 3, 5),
        (94, 'JUB024', 2, 'CARBONES MOTOR ARRANQUE CBF150-XR150L VINI', 55.25, 77.35, 20, 5),
        (95, 'JUB040', 2, 'CARBONES MOTOR ARRANQUE CG125-150-200 VINI', 55.25, 77.35, 20, 5),
        (96, 'JUB028', 2, 'CARBONES MOTOR ARRANQUE GXT200-GN125 VINI', 68.0, 95.2, 20, 5),
        (97, 'JUB041', 2, 'CARBONES MOTOR ARRANQUE PULSAR NS200 VINI', 55.25, 77.35, 20, 5),
        (98, 'CAR050', 6, 'CARBURADOR CG150 PZ27 VINI', 459.0, 642.6, 10, 5),
        (99, 'CAR047', 6, 'CARBURADOR CG200-XL200-DAKAR200 VINI', 484.5, 678.3, 10, 5),
        (100, 'CAR069', 6, 'CARBURADOR GIXXER 150 VINI', 1955.0, 2737.0, 10, 5),
        (101, 'CAR070', 6, 'CARBURADOR SCOOTER GY6150 VINI', 756.5, 1059.1, 5, 5),
        (102, 'CAR046', 6, 'CARBURADOR XL125-185-CG125 VINI', 467.5, 654.5, 10, 5),
        (103, 'CDI027', 9, 'CEPO PARA CEREBRO REDONDO 6L (2PCS) VINI', 16.15, 22.61, 50, 5),
        (104, 'CDI049', 2, 'CEREBRO CDI AK CR5-AK180 TT-180CRX VINI', 165.75, 232.05, 3, 5),
        (105, 'CDI051', 2, 'CEREBRO CDI DAYUN 150 CUADRADO CORRIENTE DIRECTA C-CABLE VINI', 165.75, 232.05, 30, 5),
        (106, 'CDI053', 2, 'CEREBRO CDI GXT200-GN125H-DR200 8L D-C VINI', 433.5, 606.9, 5, 5),
        (107, 'CDI032', 2, 'CEREBRO CDI NXR125 REDONDO CORRIENTE DIRECTA C-CABLE VINI', 161.5, 226.1, 20, 5),
        (108, 'CDI034', 2, 'CEREBRO CDI PULSAR 135 VINI', 408.0, 571.2, 5, 5),
        (109, 'CDI055', 2, 'CEREBRO CDI PULSAR150-180 UG4', 357.0, 499.8, 5, 5),
        (110, 'CDI059', 2, 'CEREBRO CDI YBR 125 VINI', 280.5, 392.7, 5, 5),
        (111, 'CIL086', 1, 'CILINDRO COMPLETO AKT TTR150-EVO 150NE BULON 13 62M VINI', 1054.0, 1475.6, 10, 5),
        (112, 'CIL160', 1, 'CILINDRO COMPLETO APACHE 160 RTR 62M 15M 2V VINI', 1419.5, 1987.3, 3, 5),
        (113, 'CIL094', 1, 'CILINDRO COMPLETO CG125-HJ125-7 56M-15M VINI', 977.5, 1368.5, 8, 5),
        (114, 'CIL087', 1, 'CILINDRO COMPLETO CG150 GRIS BULON 15 62-15M VINI', 1079.5, 1511.3, 8, 5),
        (115, 'CIL144', 1, 'CILINDRO COMPLETO CG200 63.5MM-15M VINI', 1122.0, 1570.8, 8, 5),
        (116, 'CIL161', 1, 'CILINDRO COMPLETO CRF230-LONCIN250 SX3-TRUENO GRIS 65.5-15B VINI', 1487.5, 2082.5, 2, 5),
        (117, 'CIL162', 1, 'CILINDRO COMPLETO GY6150 SCOOTER 57-15M VINI', 918.0, 1285.2, 5, 5),
        (118, 'CIL166', 1, 'CILINDRO COMPLETO JH125-WY125 CADENA ALTA COMPRESION 56.5-B15 VINI', 1096.5, 1535.1, 5, 5),
        (119, 'CIL163', 1, 'CILINDRO COMPLETO LUCKY110 HJ110 52-13 VINI', 892.5, 1249.5, 3, 5),
        (120, 'CIL143', 1, 'CILINDRO COMPLETO PLATINA 125 14-54M-2V VINI', 1326.0, 1856.4, 5, 5),
        (121, 'CIL146', 1, 'CILINDRO COMPLETO PULSAR 135 54MM-14B-4V VINI', 1185.75, 1660.05, 10, 5),
        (122, 'CIL138', 1, 'CILINDRO COMPLETO RAYBAR 250 NEGRO 65.5MM-15M VINI', 1190.0, 1666.0, 5, 5),
        (123, 'CIL164', 1, 'CILINDRO COMPLETO SCOOTER 125 52-15 VINI', 833.0, 1166.2, 5, 5),
        (124, 'CIL129', 1, 'CILINDRO COMPLETO UM200-RAYBAR200 67MM GRIS 16B VINI', 1232.5, 1725.5, 3, 5),
        (125, 'CIL165', 1, 'CILINDRO COMPLETO WY150-JH150 62MM-15 VINI', 1105.0, 1547.0, 5, 5),
        (126, 'CUN038', 5, 'CUNAS DE POSTE CG-XL125-XL185-AKT125 CONICA VINI', 76.5, 107.1, 30, 5),
        (127, 'CUN039', 5, 'CUNAS DE POSTE CG-XL125-XL185-AKT125 REDONDA VINI', 76.5, 107.1, 30, 5),
        (128, 'CUN042', 5, 'CUNAS DE POSTE HJ110 LUCKY VINI', 97.75, 136.85, 20, 5),
        (129, 'CUN056', 5, 'CUNAS DE POSTE NXR-BROS CONICA VINI', 106.25, 148.75, 20, 5),
        (130, 'CUN054', 5, 'CUNAS DE POSTE NXR-BROS REDONDA VINI', 106.25, 148.75, 20, 5),
        (131, 'DEL054', 3, 'DISCOS DE CLUTCH CG125-150-YBR125 5PCS VINI', 106.25, 148.75, 20, 5),
        (132, 'EMM080', 1, 'EMPAQUES DE MOTOR KIT CG150 VINI', 106.25, 148.75, 30, 5),
        (133, 'EMM062', 1, 'EMPAQUES DE MOTOR KIT GXT200 VINI', 182.75, 255.85, 20, 5),
        (134, 'EMM102', 1, 'EMPAQUES DE MOTOR KIT GY200-YUMBO 69MM VINI', 174.25, 243.95, 30, 5),
        (135, 'EMM092', 1, 'EMPAQUES DE MOTOR KIT PULSAR 135-DISCOVER 150 VINI', 97.75, 136.85, 30, 5),
        (136, 'DES029', 1, 'EMPAQUES DESCARBONADO DAKAR 200 69MM VINI', 51.0, 71.4, 30, 5),
        (137, 'DES045', 1, 'EMPAQUES DESCARBONADO PULSAR 135 VINI', 38.25, 53.55, 30, 5),
        (138, 'ENG013', 2, 'ENGRANAJE DE ARRANQUE + BALINERA CG200 MULTIBALINES VINI', 476.0, 666.4, 15, 5),
        (139, 'ENG047', 2, 'ENGRANAJE DE ARRANQUE + BALINERA GENESIS RKS150 VINI', 297.5, 416.5, 15, 5),
        (140, 'FRI045', 3, 'FRICCIONES HJ125-GXT200 VINI', 131.75, 184.45, 20, 5),
        (141, 'FRI038', 3, 'FRICCIONES PULSAR-BOXER-DISCOVER VINI', 131.75, 184.45, 20, 5),
        (142, 'FUS003', 2, 'FUSIBLE 15 AH GAVETA (100 UND) VINI', 1.61, 2.25, 200, 5),
        (143, 'FUS004', 2, 'FUSIBLE 20 AH GAVETA (100UND) VINI', 1.61, 2.25, 200, 5),
        (144, 'FUS005', 2, 'FUSIBLE 25 AH GAVETA (100 UND) VINI', 1.61, 2.25, 200, 5),
        (145, 'FUS006', 2, 'FUSIBLE 30 AH GAVETA (100UND) VINI', 1.61, 2.25, 200, 5),
        (146, 'GUA134', 8, 'GUARDAFANGO WR250F-YZ250F UNIVERSAL AZUL VINI', 289.0, 404.6, 3, 5),
        (147, 'GUA135', 8, 'GUARDAFANGO WR250F-YZ250F UNIVERSAL BLANCO VINI', 289.0, 404.6, 3, 5),
        (148, 'GUA136', 8, 'GUARDAFANGO WR250F-YZ250F UNIVERSAL NEGRO VINI', 289.0, 404.6, 3, 5),
        (149, 'CPI037', 9, 'GUIAS DE TIEMPO (CEPILLOS) CBF150-TITAN150-DAYUN 150GY VINI', 106.25, 148.75, 20, 5),
        (150, 'CPI019', 9, 'GUIAS DE TIEMPO (CEPILLOS) PULSAR 135 VINI', 93.5, 130.9, 20, 5),
        (151, 'VAL016', 1, 'GUIAS DE VALVULAS CG125-150-200 CORTA RACING MODIFIC VINI', 85.0, 119.0, 10, 5),
        (152, 'VAL088', 1, 'GUIAS DE VALVULAS CG125-CG200-300 VINI', 55.25, 77.35, 20, 5),
        (153, 'INI055', 2, 'IGNICION AKT NKD125-SERPENTO CORAL150-TAYPAN VINI', 106.25, 148.75, 10, 5),
        (154, 'MDC098', 2, 'IGNICION HAYATE VINI', 136.0, 190.4, 5, 5),
        (155, 'LAV044', 6, 'LLAVE DE COMBUSTIBLE AKT -XL GRUESA VINI', 63.75, 89.25, 20, 5),
        (156, 'LAV047', 9, 'LLAVIN DE TAPADERAS LATERALES YBR125-DT175-XTZ125 VINI', 55.25, 77.35, 10, 5),
        (157, 'MDO073', 2, 'MANDO DER START PULSAR 135 VINI', 272.0, 380.8, 10, 5),
        (158, 'MDO074', 2, 'MANDO DER START PULSAR NS200 VINI', 497.25, 696.15, 10, 5),
        (159, 'MDO036', 2, 'MANDO DER START WY125-RAYBAR VINI', 127.5, 178.5, 10, 5),
        (160, 'MDO075', 2, 'MANDO IZQ LUCES GXT200 VINI', 136.0, 190.4, 10, 5),
        (161, 'MDO076', 2, 'MANDO IZQ LUCES PULSAR 135 VINI', 263.5, 368.9, 10, 5),
        (162, 'MDO077', 2, 'MANDO IZQ LUCES PULSAR NS200 VINI', 497.25, 696.15, 10, 5),
        (163, 'MCI074', 3, 'MANECILLA DE CLUTCH HJ125-WY COMPLETA VINI', 93.5, 130.9, 50, 5),
        (164, 'MGA024', 4, 'MANGUERA DE FRENO DELANTERA GXT200 VINI', 134.3, 188.02, 10, 5),
        (165, 'MGA013', 4, 'MANGUERA DE FRENO TRASERA 60CM UNIVERSAL VINI', 119.0, 166.6, 10, 5),
        (166, 'MOT047', 2, 'MOTOR DE ARRANQUE AG200-XT225 VINI', 1228.25, 1719.55, 2, 5),
        (167, 'MOT050', 2, 'MOTOR DE ARRANQUE CGL125-HJ125 9 DIENTES VINI', 722.5, 1011.5, 5, 5),
        (168, 'MOT025', 2, 'MOTOR DE ARRANQUE GXT200-GN125-EN125 VINI', 705.5, 987.7, 5, 5),
        (169, 'PAL035', 7, 'PEDAL DE CAMBIOS HJ125-7 VINI', 204.0, 285.6, 5, 5),
        (170, 'PAT027', 7, 'PEDAL DE ENCENDIDO AKT TT150-TT180-TT200-GENESIS SX200-SX250 VINI', 187.0, 261.8, 10, 5),
        (171, 'PAT028', 7, 'PEDAL DE ENCENDIDO GXT200 VINI', 136.0, 190.4, 10, 5),
        (172, 'PAT029', 7, 'PEDAL DE ENCENDIDO HJ125 VINI', 173.4, 242.76, 10, 5),
        (173, 'PIS197', 1, 'PISTON COMPLETO AG200-UM200-RAYBAR200 STD 67MM-B16 VINI', 404.6, 566.44, 10, 5),
        (174, 'PIS166', 1, 'PISTON COMPLETO AKT CR5-CUPULA 200 STD B15 63 VINI', 303.45, 424.83, 10, 5),
        (175, 'PIS193', 1, 'PISTON COMPLETO AKT EVO 150NE-TT150 (B13) 62MM VINI', 280.5, 392.7, 10, 5),
        (176, 'PIS198', 1, 'PISTON COMPLETO APACHE 160 STD 62M-15-2V VINI', 314.5, 440.3, 5, 5),
        (177, 'PIS199', 1, 'PISTON COMPLETO APACHE 180 RTR STD 2V-B15-62.5 VINI', 382.5, 535.5, 5, 5),
        (178, 'PIS145', 1, 'PISTON COMPLETO CG125-WY125 (56MM*B15MM) STD VINI', 216.75, 303.45, 10, 5),
        (179, 'PIS146', 1, 'PISTON COMPLETO CG150-WY150 (62MM*B15MM) STD VINI', 255.0, 357.0, 5, 5),
        (180, 'PIS147', 1, 'PISTON COMPLETO CG200-WY200-XL200 (63.5MM*B15MM) STD VINI', 272.0, 380.8, 10, 5),
        (181, 'PIS153', 1, 'PISTON COMPLETO DAYUN150-CBF150-RTX STD B14-57MM VINI', 272.0, 380.8, 10, 5),
        (182, 'PIS152', 1, 'PISTON COMPLETO MODIFICADO CG200 63.5MM-B15 CON CUPULA RACING VINI', 420.75, 589.05, 5, 5),
        (183, 'PIS148', 1, 'PISTON COMPLETO PULSAR 135 STD 54MM-B14 VINI', 297.5, 416.5, 10, 5),
        (184, 'PIS162', 1, 'PISTON COMPLETO PULSAR 180 STD 63.5MM-B16 VINI', 331.5, 464.1, 5, 5),
        (185, 'PIS163', 1, 'PISTON COMPLETO PULSAR NS200-RS200-AS200 72MM-B17 STD VINI', 408.0, 571.2, 5, 5),
        (186, 'PIS149', 1, 'PISTON COMPLETO TORITO175-205 KIT LF200 B17-61MM VINI', 331.5, 464.1, 15, 5),
        (187, 'PIT009', 8, 'PITO UNIVERSAL DL128ZB VINI', 63.75, 89.25, 50, 5),
        (188, 'REC053', 2, 'RECTIFICADOR 4L RAYBAR200 CON DIODO VINI', 158.95, 222.53, 20, 5),
        (189, 'REC055', 2, 'RECTIFICADOR AKT 180-CR5- GENESIS LONCIN SX250 SX3 VINI', 212.5, 297.5, 5, 5),
        (190, 'REC056', 2, 'RECTIFICADOR BOXER BM150 VINI', 212.5, 297.5, 5, 5),
        (191, 'REC057', 2, 'RECTIFICADOR PULSAR 135 VINI', 346.8, 485.52, 5, 5),
        (192, 'RGL004', 3, 'REGULADORES DE CADENA TRACCION BROSS150-XR150-AKT TT150-180 VINI', 115.6, 161.84, 10, 5),
        (193, 'RGL005', 3, 'REGULADORES DE CADENA TRACCION CG125-XL VINI', 21.25, 29.75, 20, 5),
        (194, 'RGL006', 3, 'REGULADORES DE CADENA TRACCION WY125-CGL125-AKT HUNTER 150 VINI', 68.0, 95.2, 20, 5),
        (195, 'CCH009', 2, 'RELAY DE ARRANQUE CG-WY VINI', 119.0, 166.6, 30, 5),
        (196, 'CCH017', 2, 'RELAY DE ARRANQUE PULSAR 135-DISCOVER-RS200 VINI', 216.75, 303.45, 10, 5),
        (197, 'RET122', 1, 'RETENEDORES DE BARRAS CG-AKT NKD 27-37-10.5 VINI', 28.9, 40.46, 30, 5),
        (198, 'RET060', 1, 'RETENEDORES DE BARRAS PULSAR NS200-PULSAR180-220 VINI', 63.75, 89.25, 30, 5),
        (199, 'RET092', 1, 'RETENEDORES DE BARRAS PULSAR135-DISC150-YBR125-2020-25 CRUX110-REV 30-42-10.5 VINI', 38.25, 53.55, 30, 5),
        (200, 'RET115', 1, 'RETENEDORES DE BARRAS SZ150-NAGA 200-JIALING150 33X46X10.5 VINI', 46.75, 65.45, 30, 5),
        (201, 'RET090', 1, 'RETENEDORES DE BARRAS XL-WY BOXER150 NS160-N160-NS125UG 31X43X10.5 VINI', 42.5, 59.5, 50, 5),
        (202, 'RET065', 1, 'RETENEDORES DE BARRAS YBR125-CRUX110(VIEJA)-RX100-HJ125-7 (30*40.5*10.5) VINI', 42.5, 59.5, 30, 5),
        (203, 'OTR362', 1, 'SELLOS DE VALVULAS EN125-GN125 VINI', 25.5, 35.7, 50, 5),
        (204, 'OTR363', 1, 'SELLOS DE VALVULAS TORITO LF200 RE205 VINI', 25.5, 35.7, 30, 5),
        (205, 'SIN025', 9, 'SINFIN DE VELOCIMETRO AKT TT150 VINI', 110.5, 154.7, 20, 5),
        (206, 'SIS016', 9, 'SISTEMA ELECTRICO CG-DY125-ZS150 VINI', 408.0, 571.2, 5, 5),
        (207, 'SIS023', 9, 'SISTEMA ELECTRICO SX150 - AKT150TT-ZX150L VINI', 535.5, 749.7, 5, 5),
        (208, 'SPR175', 3, 'SPROCKET KIT AKT 150NE EVO 428H 41TX15T + 120L COMPLETO VINI', 391.0, 547.4, 10, 5),
        (209, 'SPR209', 3, 'SPROCKET KIT AKT SL-NKD-EVO-SERPENTO CORAL-COBRA 428H 38X15T + 130L COMPLETO VINI', 416.5, 583.1, 10, 5),
        (210, 'SPR309', 3, 'SPROCKET KIT AKT SL-NKD-EVO-SERPENTO CORAL-COBRA 428H 42X15T + 130L COMPLETO VINI', 442.0, 618.8, 10, 5),
        (211, 'SPR310', 3, 'SPROCKET KIT FZ16 428H 40T X 14T + 132L COMPLETO VINI', 442.0, 618.8, 5, 5),
        (212, 'SPR255', 3, 'SPROCKET KIT PULSAR 135 428H 43X15T + 130L DORADA COMPLETO VINI', 493.0, 690.2, 10, 5),
        (213, 'SPR268', 3, 'SPROCKET KIT PULSAR NS200 428H 45X15T + 136 DORADA RACING COMPLETO VINI', 544.0, 761.6, 10, 5),
        (214, 'SPR311', 3, 'SPROCKET KIT XR150L 428H 49T X 17T + 136L COMPLETO VINI', 493.0, 690.2, 5, 5),
        (215, 'SPR126', 3, 'SPROCKET TRASERO CGL125 428H 38T CONCAVO VINI', 123.25, 172.55, 10, 5),
        (216, 'BUJ257', 9, 'STOP TRASERO GN125H', 306.0, 428.4, 3, 5),
        (217, 'TPO075', 6, 'TAPON DE TANQUE PULSAR 135 VINI', 399.5, 559.3, 10, 5),
        (218, 'TEN021', 9, 'TENSOR AUTOMATICO BOXER BM150-BM100-PULSAR 135 GRIS VINI', 122.83, 171.96, 10, 5),
        (219, 'VAL089', 1, 'VALVULAS DE MOTOR CG125-HJ125-7 (5MM) VINI', 178.5, 249.9, 30, 5),
        (220, 'VAL090', 1, 'VALVULAS DE MOTOR CG150-AKT TT150-EVO150 VINI', 195.5, 273.7, 30, 5),
        (221, 'VAL091', 1, 'VALVULAS DE MOTOR CG200 (5MM) VINI', 229.5, 321.3, 30, 5),
        (222, 'VAL145', 1, 'VALVULAS DE MOTOR CG250-RAYBAR250 HI RPM ALTO CARBONO VINI', 263.5, 368.9, 10, 5),
        (223, 'VAL092', 1, 'VALVULAS DE MOTOR CG250-YUMBO250-RAYBAR250 VINI', 238.0, 333.2, 10, 5),
        (224, 'VAL134', 1, 'VALVULAS DE MOTOR DISCOVER 125 ST 4PCS VINI', 297.5, 416.5, 10, 5),
        (225, 'VAL150', 1, 'VALVULAS DE MOTOR HONDA NAVI-CB1 VINI', 204.0, 285.6, 10, 5),
        (226, 'VAL097', 1, 'VALVULAS DE MOTOR PULSAR 135 4PZS VINI', 306.0, 428.4, 20, 5),
        (227, 'VAL148', 1, 'VALVULAS DE MOTOR PULSAR 180 VINI', 280.5, 392.7, 10, 5),
        (228, 'VAL147', 1, 'VALVULAS DE MOTOR SCOOTER 150 VINI', 212.5, 297.5, 10, 5),
        (229, 'VAL178', 1, 'VALVULAS DE MOTOR SCOOTER GY6 125 VINI', 136.0, 190.4, 10, 5),
        (230, 'VAL149', 1, 'VALVULAS DE MOTOR SUZUKI AN125 VINI', 255.0, 357.0, 10, 5),
        (231, 'VAL079', 1, 'VALVULAS DE MOTOR SUZUKI AX4 VINI', 229.5, 321.3, 10, 5),
        (232, 'VAR022', 4, 'VARILLA DE FRENO CG125-TAYPAN-NKD125 VINI', 34.0, 47.6, 20, 5),
        (233, 'VAR023', 4, 'VARILLA DE FRENO YBR125ED-G VINI', 46.75, 65.45, 10, 5),
        (234, 'VAR016', 4, 'VARILLAS DE EMPUJE ALUMINIO CG150-AKT TT150-EVO-XM20 VINI', 68.0, 95.2, 30, 5),
        (235, 'VAR017', 4, 'VARILLAS DE EMPUJE ALUMINIO CG-GY200-XM 200 VINI', 68.0, 95.2, 20, 5)
    ])

    # Cuentas Contables (Catálogo de Cuentas - Simulación)
    cursor.executemany("INSERT OR IGNORE INTO cuentas_contables (id, codigo, nombre, clasificacion, naturaleza, descripcion) VALUES (?, ?, ?, ?, ?, ?)", [
        (1, '1.1.01', 'Caja', 'Activo corriente', 'Deudora', 'Efectivo disponible en caja.'),
        (2, '1.1.02', 'Bancos', 'Activo corriente', 'Deudora', 'Dinero disponible en cuentas bancarias.'),
        (3, '1.1.03', 'Clientes', 'Activo corriente', 'Deudora', 'Cuentas por cobrar por ventas realizadas a crédito.'),
        (4, '1.1.04', 'Inventario de repuestos y accesorios', 'Activo corriente', 'Deudora', 'Existencias de repuestos, accesorios y artículos para motocicletas.'),
        (5, '1.1.05', 'IVA acreditable', 'Activo corriente', 'Deudora', 'Impuesto acreditable generado por compras gravadas.'),
        (6, '1.2.01', 'Mobiliario y equipo', 'Activo no corriente', 'Deudora', 'Mostradores, estanterías, muebles y equipo utilizado en el negocio.'),
        (7, '1.2.02', 'Equipo de cómputo', 'Activo no corriente', 'Deudora', 'Computadoras, impresoras y equipo tecnológico.'),
        (8, '1.2.03', 'Depreciación acumulada de activos', 'Activo no corriente - contraactivo', 'Acreedora', 'Depreciación acumulada de los activos fijos.'),
        (9, '2.1.01', 'Proveedores', 'Pasivo corriente', 'Acreedora', 'Obligaciones pendientes por compras realizadas a crédito.'),
        (10, '2.1.02', 'Documentos por pagar', 'Pasivo corriente', 'Acreedora', 'Obligaciones respaldadas por documentos de pago.'),
        (11, '2.1.03', 'IVA por pagar', 'Pasivo corriente', 'Acreedora', 'Impuesto generado en las ventas pendiente de pago.'),
        (12, '2.1.04', 'Sueldos y salarios por pagar', 'Pasivo corriente', 'Acreedora', 'Remuneraciones pendientes de pago.'),
        (13, '2.1.05', 'Servicios básicos por pagar', 'Pasivo corriente', 'Acreedora', 'Servicios de energía, agua, internet u otros pendientes.'),
        (14, '3.1.01', 'Capital del propietario', 'Patrimonio', 'Acreedora', 'Aportes realizados por el propietario.'),
        (15, '3.1.02', 'Utilidades acumuladas', 'Patrimonio', 'Acreedora', 'Resultados de ejercicios anteriores retenidos en el negocio.'),
        (16, '4.1.01', 'Ventas de repuestos y accesorios', 'Ingresos', 'Acreedora', 'Ingresos provenientes de la comercialización de repuestos y accesorios.'),
        (17, '4.1.02', 'Ingresos por servicios de taller', 'Ingresos', 'Acreedora', 'Ingresos por instalación, reparación y servicios relacionados con motocicletas.'),
        (18, '5.1.01', 'Costo de ventas', 'Costo', 'Deudora', 'Costo de los repuestos y accesorios vendidos durante el período.'),
        (19, '6.1.01', 'Sueldos y salarios', 'Gasto', 'Deudora', 'Remuneraciones del personal.'),
        (20, '6.1.02', 'Alquiler del local', 'Gasto', 'Deudora', 'Alquiler del establecimiento comercial y taller.'),
        (21, '6.1.03', 'Energía eléctrica', 'Gasto', 'Deudora', 'Consumo de energía eléctrica.'),
        (22, '6.1.04', 'Agua', 'Gasto', 'Deudora', 'Consumo de agua.'),
        (23, '6.1.05', 'Internet y telefonía', 'Gasto', 'Deudora', 'Servicios de comunicación e internet.'),
        (24, '6.1.06', 'Publicidad y mercadotecnia', 'Gasto', 'Deudora', 'Promoción de productos y servicios del negocio.'),
        (25, '6.1.07', 'Mantenimiento y reparaciones', 'Gasto', 'Deudora', 'Mantenimiento del local, herramientas y equipos.'),
        (26, '6.1.08', 'Papelería y útiles', 'Gasto', 'Deudora', 'Materiales administrativos y de oficina.'),
        (27, '6.1.09', 'Depreciación del período', 'Gasto', 'Deudora', 'Depreciación correspondiente al período.'),
        (28, '6.1.10', 'Comisiones y gastos bancarios', 'Gasto', 'Deudora', 'Comisiones y cargos generados por operaciones bancarias.')
    ])

    conn.commit()
    conn.close()
    print("Base de datos SQLite inicializada correctamente con el nuevo módulo contable.")

if __name__ == '__main__':
    init_sqlite_db()

