-- ==============================================================================
-- BASE DE DATOS: JEHOVA JIREH MOTO REPUESTOS
-- COMPATIBLE 100% CON MICROSOFT SQL SERVER (T-SQL / SSMS)
-- ==============================================================================

USE master;
GO

-- 1. CREACIÓN DE LA BASE DE DATOS
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'jehova_jireh_db')
BEGIN
    CREATE DATABASE jehova_jireh_db;
END
GO

USE jehova_jireh_db;
GO

-- Limpieza previa de tablas (en orden de dependencias)
IF OBJECT_ID('movimientos_inventario', 'U') IS NOT NULL DROP TABLE movimientos_inventario;
IF OBJECT_ID('detalle_ventas', 'U') IS NOT NULL DROP TABLE detalle_ventas;
IF OBJECT_ID('ventas', 'U') IS NOT NULL DROP TABLE ventas;
IF OBJECT_ID('detalle_compras', 'U') IS NOT NULL DROP TABLE detalle_compras;
IF OBJECT_ID('compras', 'U') IS NOT NULL DROP TABLE compras;
IF OBJECT_ID('productos', 'U') IS NOT NULL DROP TABLE productos;
IF OBJECT_ID('proveedores', 'U') IS NOT NULL DROP TABLE proveedores;
IF OBJECT_ID('clientes', 'U') IS NOT NULL DROP TABLE clientes;
IF OBJECT_ID('usuarios', 'U') IS NOT NULL DROP TABLE usuarios;
IF OBJECT_ID('categorias', 'U') IS NOT NULL DROP TABLE categorias;
IF OBJECT_ID('roles', 'U') IS NOT NULL DROP TABLE roles;
GO

-- ==============================================================================
-- 2. TABLAS DE CATÁLOGOS BASE Y SEGURIDAD
-- ==============================================================================

-- Tabla: ROLES
CREATE TABLE roles (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(255) NULL,
    created_at DATETIME DEFAULT GETDATE()
);
GO

-- Tabla: USUARIOS
CREATE TABLE usuarios (
    id INT IDENTITY(1,1) PRIMARY KEY,
    rol_id INT NOT NULL,
    username VARCHAR(50) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    nombre_completo VARCHAR(150) NOT NULL,
    email VARCHAR(100) UNIQUE NULL,
    telefono VARCHAR(25) NULL,
    activo BIT DEFAULT 1,
    ultimo_acceso DATETIME NULL,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_usuarios_roles FOREIGN KEY (rol_id) REFERENCES roles(id)
);
GO

-- Tabla: CATEGORÍAS
CREATE TABLE categorias (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    descripcion VARCHAR(MAX) NULL,
    created_at DATETIME DEFAULT GETDATE()
);
GO

-- Tabla: CLIENTES
CREATE TABLE clientes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    identificacion VARCHAR(30) NULL,
    telefono VARCHAR(25) NULL,
    email VARCHAR(100) NULL,
    direccion VARCHAR(MAX) NULL,
    tipo_cliente VARCHAR(30) DEFAULT 'General' CHECK (tipo_cliente IN ('General', 'Taller', 'Frecuente', 'Mayorista')),
    created_at DATETIME DEFAULT GETDATE()
);
GO

-- Tabla: PROVEEDORES
CREATE TABLE proveedores (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre_empresa VARCHAR(150) NOT NULL,
    contacto_nombre VARCHAR(100) NULL,
    identificacion_fiscal VARCHAR(30) NULL,
    telefono VARCHAR(25) NOT NULL,
    email VARCHAR(100) NULL,
    direccion VARCHAR(MAX) NULL,
    activo BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE()
);
GO

-- ==============================================================================
-- 3. CATÁLOGO DE PRODUCTOS / REPUESTOS
-- ==============================================================================

CREATE TABLE productos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    codigo_sku VARCHAR(50) NOT NULL UNIQUE,
    codigo_barras VARCHAR(50) UNIQUE NULL,
    categoria_id INT NOT NULL,
    nombre VARCHAR(200) NOT NULL,
    descripcion VARCHAR(MAX) NULL,
    marca VARCHAR(100) NULL,
    modelo_compatible VARCHAR(255) NULL,
    ubicacion_estante VARCHAR(50) NULL,
    costo DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    precio_venta DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    stock_actual INT NOT NULL DEFAULT 0,
    stock_minimo INT NOT NULL DEFAULT 5,
    activo BIT DEFAULT 1,
    created_at DATETIME DEFAULT GETDATE(),
    updated_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_productos_categorias FOREIGN KEY (categoria_id) REFERENCES categorias(id),
    CONSTRAINT chk_stock_minimo CHECK (stock_minimo >= 0),
    CONSTRAINT chk_precios CHECK (precio_venta >= 0 AND costo >= 0)
);
GO

-- ==============================================================================
-- 4. GESTIÓN DE COMPRAS
-- ==============================================================================

CREATE TABLE compras (
    id INT IDENTITY(1,1) PRIMARY KEY,
    codigo_compra VARCHAR(30) NOT NULL UNIQUE,
    numero_factura_proveedor VARCHAR(50) NULL,
    proveedor_id INT NOT NULL,
    usuario_id INT NOT NULL,
    fecha_compra DATE NOT NULL,
    total DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    forma_pago VARCHAR(30) DEFAULT 'Efectivo' CHECK (forma_pago IN ('Efectivo', 'Transferencia', 'Crédito', 'Cheque')),
    estado VARCHAR(30) DEFAULT 'Completada' CHECK (estado IN ('Completada', 'Pendiente', 'Anulada')),
    observaciones VARCHAR(MAX) NULL,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_compras_proveedores FOREIGN KEY (proveedor_id) REFERENCES proveedores(id),
    CONSTRAINT fk_compras_usuarios FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
GO

CREATE TABLE detalle_compras (
    id INT IDENTITY(1,1) PRIMARY KEY,
    compra_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    costo_unitario DECIMAL(12, 2) NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL,
    CONSTRAINT fk_detcompras_compras FOREIGN KEY (compra_id) REFERENCES compras(id) ON DELETE CASCADE,
    CONSTRAINT fk_detcompras_productos FOREIGN KEY (producto_id) REFERENCES productos(id),
    CONSTRAINT chk_detcompra_cantidad CHECK (cantidad > 0)
);
GO

-- ==============================================================================
-- 5. FACTURACIÓN Y VENTAS (PUNTO DE VENTA / POS)
-- ==============================================================================

CREATE TABLE ventas (
    id INT IDENTITY(1,1) PRIMARY KEY,
    codigo_venta VARCHAR(30) NOT NULL UNIQUE,
    cliente_id INT NULL,
    usuario_id INT NOT NULL,
    fecha_venta DATE NOT NULL,
    subtotal DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    descuento DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    total DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    forma_pago VARCHAR(30) DEFAULT 'Efectivo' CHECK (forma_pago IN ('Efectivo', 'Tarjeta', 'Transferencia', 'Crédito', 'Mixto')),
    estado VARCHAR(30) DEFAULT 'Completada' CHECK (estado IN ('Completada', 'Anulada', 'Pendiente')),
    notas VARCHAR(MAX) NULL,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_ventas_clientes FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE SET NULL,
    CONSTRAINT fk_ventas_usuarios FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
GO

CREATE TABLE detalle_ventas (
    id INT IDENTITY(1,1) PRIMARY KEY,
    venta_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precio_unitario DECIMAL(12, 2) NOT NULL,
    costo_historico DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    subtotal DECIMAL(12, 2) NOT NULL,
    CONSTRAINT fk_detventas_ventas FOREIGN KEY (venta_id) REFERENCES ventas(id) ON DELETE CASCADE,
    CONSTRAINT fk_detventas_productos FOREIGN KEY (producto_id) REFERENCES productos(id),
    CONSTRAINT chk_detventa_cantidad CHECK (cantidad > 0)
);
GO

-- ==============================================================================
-- 6. CONTROL KARDEX / MOVIMIENTOS DE INVENTARIO
-- ==============================================================================

CREATE TABLE movimientos_inventario (
    id INT IDENTITY(1,1) PRIMARY KEY,
    fecha DATETIME DEFAULT GETDATE(),
    producto_id INT NOT NULL,
    tipo_movimiento VARCHAR(50) NOT NULL CHECK (tipo_movimiento IN (
        'ENTRADA_INICIAL',
        'ENTRADA_COMPRA',
        'SALIDA_VENTA',
        'AJUSTE_ENTRADA',
        'AJUSTE_SALIDA',
        'DEFECTUOSO_GARANTIA',
        'DEVOLUCION_CLIENTE'
    )),
    cantidad INT NOT NULL,
    stock_anterior INT NOT NULL DEFAULT 0,
    stock_posterior INT NOT NULL DEFAULT 0,
    referencia_origen VARCHAR(100) NULL,
    motivo VARCHAR(255) NOT NULL,
    usuario_id INT NOT NULL,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_mov_productos FOREIGN KEY (producto_id) REFERENCES productos(id),
    CONSTRAINT fk_mov_usuarios FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
GO

-- ==============================================================================
-- 7. ÍNDICES DE RENDIMIENTO
-- ==============================================================================

CREATE NONCLUSTERED INDEX idx_productos_sku ON productos(codigo_sku);
CREATE NONCLUSTERED INDEX idx_productos_nombre ON productos(nombre);
CREATE NONCLUSTERED INDEX idx_productos_categoria ON productos(categoria_id);
CREATE NONCLUSTERED INDEX idx_ventas_fecha ON ventas(fecha_venta);
CREATE NONCLUSTERED INDEX idx_compras_fecha ON compras(fecha_compra);
CREATE NONCLUSTERED INDEX idx_movimientos_producto ON movimientos_inventario(producto_id);
GO

-- ==============================================================================
-- 8. VISTAS SQL PARA REPORTES Y DASHBOARDS
-- ==============================================================================

CREATE OR ALTER VIEW vista_stock_bajo AS
SELECT 
    p.id,
    p.codigo_sku,
    p.nombre AS repuesto,
    c.nombre AS categoria,
    p.stock_actual,
    p.stock_minimo,
    (p.stock_minimo - p.stock_actual) AS unidades_por_comprar,
    p.costo,
    p.precio_venta
FROM productos p
INNER JOIN categorias c ON p.categoria_id = c.id
WHERE p.stock_actual <= p.stock_minimo AND p.activo = 1;
GO

CREATE OR ALTER VIEW vista_kardex_completo AS
SELECT 
    m.id AS movimiento_id,
    m.fecha,
    p.codigo_sku,
    p.nombre AS repuesto,
    c.nombre AS categoria,
    m.tipo_movimiento,
    m.cantidad,
    m.stock_anterior,
    m.stock_posterior,
    m.referencia_origen,
    m.motivo,
    u.nombre_completo AS realizado_por,
    r.nombre AS rol_usuario
FROM movimientos_inventario m
INNER JOIN productos p ON m.producto_id = p.id
INNER JOIN categorias c ON p.categoria_id = c.id
INNER JOIN usuarios u ON m.usuario_id = u.id
INNER JOIN roles r ON u.rol_id = r.id;
GO

CREATE OR ALTER VIEW vista_top_productos_vendidos AS
SELECT 
    p.id AS producto_id,
    p.codigo_sku,
    p.nombre AS repuesto,
    c.nombre AS categoria,
    SUM(dv.cantidad) AS total_unidades_vendidas,
    SUM(dv.subtotal) AS ingreso_total_generado,
    SUM(dv.subtotal - (dv.costo_historico * dv.cantidad)) AS ganancia_neta_generada
FROM detalle_ventas dv
INNER JOIN productos p ON dv.producto_id = p.id
INNER JOIN categorias c ON p.categoria_id = c.id
INNER JOIN ventas v ON dv.venta_id = v.id
WHERE v.estado = 'Completada'
GROUP BY p.id, p.codigo_sku, p.nombre, c.nombre;
GO

CREATE OR ALTER VIEW vista_balance_inventario AS
SELECT 
    COUNT(p.id) AS total_tipos_repuestos,
    SUM(p.stock_actual) AS total_unidades_fisicas,
    SUM(p.stock_actual * p.costo) AS valor_total_costo,
    SUM(p.stock_actual * p.precio_venta) AS valor_total_venta,
    SUM(p.stock_actual * (p.precio_venta - p.costo)) AS ganancia_proyectada
FROM productos p
WHERE p.activo = 1;
GO

-- ==============================================================================
-- 9. INSERCIÓN DE DATOS INICIALES (CON IDENTITY_INSERT HABILITADO)
-- ==============================================================================

-- 1. Roles
SET IDENTITY_INSERT roles ON;
INSERT INTO roles (id, nombre, descripcion) VALUES
(1, 'Administrador', 'Control total administrativo y reportes'),
(2, 'Vendedor', 'Atención al cliente y facturación en caja'),
(3, 'Encargado de Inventario', 'Ingreso de compras, bodega y Kardex'),
(4, 'Contador', 'Balances contables y reportes de rentabilidad');
SET IDENTITY_INSERT roles OFF;
GO

-- 2. Usuarios
SET IDENTITY_INSERT usuarios ON;
INSERT INTO usuarios (id, rol_id, username, password_hash, nombre_completo, email, telefono) VALUES
(1, 1, 'admin', '123', 'Gilda Pérez', 'admin@jehovajireh.com', '+505 8888-0001'),
(2, 2, 'vendedor', '123', 'Ana Gómez', 'ventas@jehovajireh.com', '+505 8888-0002'),
(3, 3, 'inventario', '123', 'Roberto Silva', 'bodega@jehovajireh.com', '+505 8888-0003'),
(4, 4, 'contador', '123', 'Lic. Fernando Rivas (Granada)', 'contabilidad@jehovajireh.com', '+505 8888-0004');
SET IDENTITY_INSERT usuarios OFF;
GO

-- 3. Categorías
SET IDENTITY_INSERT categorias ON;
INSERT INTO categorias (id, nombre, descripcion) VALUES
(1, 'Frenos', 'Pastillas, zapatas, discos, bombas y líquidos de freno'),
(2, 'Transmisión', 'Kits de arrastre, cadenas, piñones y coronas'),
(3, 'Lubricantes', 'Aceites 2T, 4T minerales, semi-sintéticos y aditivos'),
(4, 'Motor / Encendido', 'Bujías, pistones, anillos y carburadores'),
(5, 'Eléctrico', 'Baterías de gel, focos LED, bobinas y reguladores'),
(6, 'Suspensión', 'Amortiguadores y barras telescópicas'),
(7, 'Llantas y Neumáticos', 'Llantas pisteras, todo terreno y neumáticos');
SET IDENTITY_INSERT categorias OFF;
GO

-- 4. Clientes
SET IDENTITY_INSERT clientes ON;
INSERT INTO clientes (id, nombre_completo, identificacion, telefono, email, tipo_cliente) VALUES
(1, 'Cliente General (Mostrador)', '000-000000-0000X', '2222-0000', 'mostrador@jehovajireh.com', 'General'),
(2, 'Taller Hermanos Mendoza', '401-150885-0002K', '+505 8444-1234', 'taller.mendoza@gmail.com', 'Taller'),
(3, 'Carlos Estrada', '001-200392-0044L', '+505 8999-5544', 'carlos.estrada@yahoo.com', 'Frecuente');
SET IDENTITY_INSERT clientes OFF;
GO

-- 5. Proveedores
SET IDENTITY_INSERT proveedores ON;
INSERT INTO proveedores (id, nombre_empresa, contacto_nombre, identificacion_fiscal, telefono, email, direccion) VALUES
(1, 'Distribuidora Repuestos del Pacífico', 'Mario López', 'J0310000123456', '+505 8899-1122', 'ventas@pacificomotos.com', 'Managua, Pista Juan Pablo II'),
(2, 'Importadora Global Moto Parts', 'Elena Morales', 'J0310000987654', '+505 7766-3344', 'contacto@globalmotoparts.com', 'Masaya, Km 28 Carretera a Granada');
SET IDENTITY_INSERT proveedores OFF;
GO

-- 6. Catálogo de Repuestos
SET IDENTITY_INSERT productos ON;
INSERT INTO productos (id, codigo_sku, categoria_id, nombre, marca, modelo_compatible, costo, precio_venta, stock_actual, stock_minimo) VALUES
(1, 'REP-001', 1, 'Pastillas de Freno Delanteras Yamaha YBR 125', 'Yamaha Genuine', 'YBR 125 / SZ-R', 9.00, 15.50, 18, 5),
(2, 'REP-002', 2, 'Kit de Arrastre Cadena y Piñón Pulsar 200 NS', 'Choho Racing', 'Pulsar 200 NS / RS / AS', 30.00, 45.00, 3, 5),
(3, 'REP-003', 3, 'Aceite 4T 20W50 Mineral Motul 1L', 'Motul', 'Motos 4 Tiempos Universal', 7.50, 12.00, 40, 10),
(4, 'REP-004', 4, 'Bujía NGK C7HSA para pasola/motos 125cc', 'NGK', 'Scooter / Pasola 125cc - 150cc', 2.20, 4.50, 25, 8),
(5, 'REP-005', 5, 'Batería de Gel 12V 7Ah Moto Scooter', 'Dynavolt', 'Scooter, Pulsar 135, Mensajeras', 22.00, 35.00, 2, 4);
SET IDENTITY_INSERT productos OFF;
GO

-- 7. Compras
SET IDENTITY_INSERT compras ON;
INSERT INTO compras (id, codigo_compra, numero_factura_proveedor, proveedor_id, usuario_id, fecha_compra, total, forma_pago, estado) VALUES
(1, 'COM-#1', 'FAC-PAC-9082', 1, 3, '2026-08-05', 180.00, 'Transferencia', 'Completada');
SET IDENTITY_INSERT compras OFF;
GO

SET IDENTITY_INSERT detalle_compras ON;
INSERT INTO detalle_compras (id, compra_id, producto_id, cantidad, costo_unitario, subtotal) VALUES
(1, 1, 1, 20, 9.00, 180.00);
SET IDENTITY_INSERT detalle_compras OFF;
GO

-- 8. Ventas
SET IDENTITY_INSERT ventas ON;
INSERT INTO ventas (id, codigo_venta, cliente_id, usuario_id, fecha_venta, subtotal, descuento, total, forma_pago, estado) VALUES
(1, 'VEN-0001', 1, 2, '2026-08-09', 27.50, 0.00, 27.50, 'Efectivo', 'Completada');
SET IDENTITY_INSERT ventas OFF;
GO

SET IDENTITY_INSERT detalle_ventas ON;
INSERT INTO detalle_ventas (id, venta_id, producto_id, cantidad, precio_unitario, costo_historico, subtotal) VALUES
(1, 1, 1, 1, 15.50, 9.00, 15.50),
(2, 1, 3, 1, 12.00, 7.50, 12.00);
SET IDENTITY_INSERT detalle_ventas OFF;
GO

-- 9. Movimientos Kardex
SET IDENTITY_INSERT movimientos_inventario ON;
INSERT INTO movimientos_inventario (id, fecha, producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, referencia_origen, motivo, usuario_id) VALUES
(1, '2026-08-01 08:00:00', 1, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1),
(2, '2026-08-05 10:30:00', 1, 'ENTRADA_COMPRA', 20, 20, 40, 'Compra COM-#1', 'Compra COM-#1 - Distribuidora Repuestos del Pacífico', 3),
(3, '2026-08-09 14:15:00', 1, 'SALIDA_VENTA', 1, 40, 39, 'Venta VEN-0001', 'Venta mostrador VEN-0001', 2),
(4, '2026-08-09 14:15:00', 3, 'SALIDA_VENTA', 1, 41, 40, 'Venta VEN-0001', 'Venta mostrador VEN-0001', 2);
SET IDENTITY_INSERT movimientos_inventario OFF;
GO
