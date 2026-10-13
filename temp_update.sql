USE jehova_jireh_db;
GO
-- 11.9 Empleados Activos de Jehová Jireh
SET IDENTITY_INSERT empleados ON;
INSERT INTO empleados (id, nombre_completo, identificacion, num_inss, cargo, salario_base, fecha_ingreso, activo, dias_vacaciones_disponibles, telefono, email, observaciones) VALUES
(1, 'Gilda Pérez', '001-150480-0023K', '6543210-1', 'Administrador General', 25000.00, '2022-01-15', 1, 15.0, '+505 8888-0001', 'admin@jehovajireh.com', 'Propietaria y Gerente General'),
(2, 'Ana Gómez', '401-200595-0012A', '7654321-2', 'Vendedor de Mostrador', 9500.00, '2023-03-01', 1, 8.5, '+505 8888-0002', 'ventas@jehovajireh.com', 'Ventas en mostrador y caja POS'),
(3, 'Roberto Silva', '401-101192-0044B', '8765432-3', 'Encargado de Bodega e Inventario', 11000.00, '2022-08-10', 1, 10.0, '+505 8888-0003', 'bodega@jehovajireh.com', 'Responsable de almacén y Kardex'),
(4, 'Lic. Fernando Rivas', '401-050288-0033C', '9876543-4', 'Contador General', 18000.00, '2023-01-10', 1, 12.0, '+505 8888-0004', 'contabilidad@jehovajireh.com', 'Contador público colegiado'),
(5, 'Lic. María Elena Calero', '401-120790-0019D', '5432109-8', 'Responsable de Recursos Humanos', 15000.00, '2024-02-01', 1, 6.0, '+505 8888-0005', 'rrhh@jehovajireh.com', 'Gestión de personal y nóminas');
SET IDENTITY_INSERT empleados OFF;
GO

-- 11.10 Catálogo Oficial de Cuentas Contables (28 Cuentas según Normas de Nicaragua)
-- 11. INSERCIÓN DEL CATÁLOGO DE CUENTAS (SIMULACIÓN ACADÉMICA)
-- ==============================================================================
SET IDENTITY_INSERT cuentas_contables ON;
INSERT INTO cuentas_contables (id, codigo, nombre, clasificacion, naturaleza, descripcion) VALUES
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
(28, '6.1.10', 'Comisiones y gastos bancarios', 'Gasto', 'Deudora', 'Comisiones y cargos generados por operaciones bancarias.');
SET IDENTITY_INSERT cuentas_contables OFF;
GO
GO

-- ==============================================================================
-- 12. TABLAS AGREGADAS PARA CONCORDANCIA CON DIAGRAMA UML (FASE 1)
-- ==============================================================================

-- Módulo: Seguridad y Autenticación
CREATE TABLE permisos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    rol_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255) NULL,
    CONSTRAINT fk_permisos_roles FOREIGN KEY (rol_id) REFERENCES roles(id)
);
GO

CREATE TABLE sesiones (
    id INT IDENTITY(1,1) PRIMARY KEY,
    usuario_id INT NOT NULL,
    fechaInicio DATETIME DEFAULT GETDATE(),
    estado VARCHAR(20) DEFAULT 'Activa',
    ip VARCHAR(50) NULL,
    CONSTRAINT fk_sesiones_usuarios FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);
GO

-- Módulo: Portal Web y Clientes
CREATE TABLE carritos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    cliente_id INT NOT NULL,
    subtotal DECIMAL(12,2) DEFAULT 0.00,
    estado VARCHAR(20) DEFAULT 'Activo',
    CONSTRAINT fk_carritos_clientes FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);
GO

CREATE TABLE detalle_carritos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    carrito_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precioUnitario DECIMAL(12,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_detcarrito_carritos FOREIGN KEY (carrito_id) REFERENCES carritos(id),
    CONSTRAINT fk_detcarrito_productos FOREIGN KEY (producto_id) REFERENCES productos(id)
);
GO

CREATE TABLE pedidos_web (
    id INT IDENTITY(1,1) PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    cliente_id INT NOT NULL,
    fecha DATETIME DEFAULT GETDATE(),
    subtotal DECIMAL(12,2) NOT NULL,
    total DECIMAL(12,2) NOT NULL,
    formaEntrega VARCHAR(50) NULL,
    metodo VARCHAR(50) NULL,
    estado VARCHAR(30) DEFAULT 'Pendiente',
    CONSTRAINT fk_pedidos_clientes FOREIGN KEY (cliente_id) REFERENCES clientes(id)
);
GO

CREATE TABLE detalle_pedidos_web (
    id INT IDENTITY(1,1) PRIMARY KEY,
    pedido_id INT NOT NULL,
    producto_id INT NOT NULL,
    cantidad INT NOT NULL,
    precioUnitario DECIMAL(12,2) NOT NULL,
    subtotal DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_detpedido_pedidos FOREIGN KEY (pedido_id) REFERENCES pedidos_web(id),
    CONSTRAINT fk_detpedido_productos FOREIGN KEY (producto_id) REFERENCES productos(id)
);
GO

-- Módulo: Facturación y Punto de Venta (POS)
CREATE TABLE pagos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    venta_id INT NOT NULL,
    metodo VARCHAR(50) NOT NULL,
    monto DECIMAL(12,2) NOT NULL,
    referencia VARCHAR(100) NULL,
    fecha DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_pagos_ventas FOREIGN KEY (venta_id) REFERENCES ventas(id)
);
GO

CREATE TABLE comprobantes (
    id INT IDENTITY(1,1) PRIMARY KEY,
    venta_id INT NOT NULL,
    numero VARCHAR(50) NOT NULL UNIQUE,
    fechaEmision DATETIME DEFAULT GETDATE(),
    total DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_comprobantes_ventas FOREIGN KEY (venta_id) REFERENCES ventas(id)
);
GO

-- Módulo: Inventario, Kardex y Proveedores
CREATE TABLE ajustes_inventario (
    id INT IDENTITY(1,1) PRIMARY KEY,
    producto_id INT NOT NULL,
    tipo VARCHAR(30) NOT NULL,
    cantidad INT NOT NULL,
    motivo VARCHAR(255) NULL,
    fecha DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_ajustes_productos FOREIGN KEY (producto_id) REFERENCES productos(id)
);
GO

CREATE TABLE recepciones_compra (
    id INT IDENTITY(1,1) PRIMARY KEY,
    compra_id INT NOT NULL,
    fechaRecepcion DATETIME DEFAULT GETDATE(),
    estado VARCHAR(30) DEFAULT 'Recibido',
    CONSTRAINT fk_recepcion_compras FOREIGN KEY (compra_id) REFERENCES compras(id)
);
GO

-- Módulo: Recursos Humanos y Nómina
CREATE TABLE cargos (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    descripcion VARCHAR(255) NULL
);
GO

CREATE TABLE empleados (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nombre_completo VARCHAR(150) NOT NULL,
    identificacion VARCHAR(30) NULL,
    cargo_id INT NULL,
    salario_base DECIMAL(12,2) NOT NULL DEFAULT 0.00,
    fecha_ingreso DATE NULL,
    activo BIT DEFAULT 1,
    num_inss VARCHAR(30) NULL,
    telefono VARCHAR(25) NULL,
    email VARCHAR(100) NULL,
    vacacionesDisponibles DECIMAL(5,2) DEFAULT 0.00,
    created_at DATETIME DEFAULT GETDATE(),
    CONSTRAINT fk_empleados_cargos FOREIGN KEY (cargo_id) REFERENCES cargos(id)
);
GO

CREATE TABLE movimientos_laborales (
    id INT IDENTITY(1,1) PRIMARY KEY,
    empleado_id INT NOT NULL,
    tipo VARCHAR(50) NOT NULL,
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NULL,
    dias_tomados INT DEFAULT 0,
    observacion VARCHAR(255) NULL,
    CONSTRAINT fk_mov_laborales_empleados FOREIGN KEY (empleado_id) REFERENCES empleados(id)
);
GO

CREATE TABLE vacaciones (
    id INT IDENTITY(1,1) PRIMARY KEY,
    empleado_id INT NOT NULL,
    fechaInicio DATE NOT NULL,
    fechaFin DATE NOT NULL,
    dias INT NOT NULL,
    estado VARCHAR(30) DEFAULT 'Aprobada',
    CONSTRAINT fk_vacaciones_empleados FOREIGN KEY (empleado_id) REFERENCES empleados(id)
);
GO

CREATE TABLE nomina (
    id INT IDENTITY(1,1) PRIMARY KEY,
    periodo_mes INT NOT NULL,
    periodo_anio INT NOT NULL,
    fecha_generacion DATETIME DEFAULT GETDATE(),
    total_ingresos DECIMAL(12,2) DEFAULT 0.00,
    total_deducciones DECIMAL(12,2) DEFAULT 0.00,
    total_neto DECIMAL(12,2) DEFAULT 0.00,
    inss_patronal_total DECIMAL(12,2) DEFAULT 0.00,
    provision_vac_total DECIMAL(12,2) DEFAULT 0.00,
    provision_agui_total DECIMAL(12,2) DEFAULT 0.00,
    estado VARCHAR(30) DEFAULT 'Procesada'
);
GO

CREATE TABLE detalle_nomina (
    id INT IDENTITY(1,1) PRIMARY KEY,
    nomina_id INT NOT NULL,
    empleado_id INT NOT NULL,
    salario_base DECIMAL(12,2) DEFAULT 0.00,
    inss_laboral DECIMAL(12,2) DEFAULT 0.00,
    ir DECIMAL(12,2) DEFAULT 0.00,
    otras_deducciones DECIMAL(12,2) DEFAULT 0.00,
    neto_pagar DECIMAL(12,2) DEFAULT 0.00,
    ingresos_extra DECIMAL(12,2) DEFAULT 0.00,
    inss_patronal DECIMAL(12,2) DEFAULT 0.00,
    provision_vacaciones DECIMAL(12,2) DEFAULT 0.00,
    provision_aguinaldo DECIMAL(12,2) DEFAULT 0.00,
    kpi_comision DECIMAL(12,2) DEFAULT 0.00,
    adelanto_salarial DECIMAL(12,2) DEFAULT 0.00,
    dias_trabajados INT DEFAULT 30,
    vac_acumulada DECIMAL(5,2) DEFAULT 0.00,
    vac_mes DECIMAL(5,2) DEFAULT 0.00,
    CONSTRAINT fk_detnomina_nomina FOREIGN KEY (nomina_id) REFERENCES nomina(id),
    CONSTRAINT fk_detnomina_empleados FOREIGN KEY (empleado_id) REFERENCES empleados(id)
);
GO

CREATE TABLE colilla_pago (
    id INT IDENTITY(1,1) PRIMARY KEY,
    detalle_nomina_id INT NOT NULL,
    periodo VARCHAR(50) NOT NULL,
    netoRecibir DECIMAL(12,2) NOT NULL,
    CONSTRAINT fk_colilla_detnomina FOREIGN KEY (detalle_nomina_id) REFERENCES detalle_nomina(id)
);
GO
-- 11.11 Asientos Contables y Saldos Iniciales Balanceados (Agosto 2026)
DECLARE @UsuarioID INT = 1;
DECLARE @AsientoID INT;

-- ASIENTO 1: Saldos Iniciales de Apertura (01 de Agosto de 2026)
INSERT INTO asientos_contables (fecha, concepto, modulo_origen, usuario_id)
VALUES ('2026-08-01', 'Apertura de saldos iniciales de balance', 'CONTABILIDAD', @UsuarioID);
SET @AsientoID = SCOPE_IDENTITY();

-- DEBE (Total 565,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 420000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.04'; -- Inventario
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 90000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.2.01'; -- Mobiliario
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 55000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.2.02'; -- Cómputo

-- HABER (Total 565,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 250000.00 FROM cuentas_contables WHERE codigo = '3.1.01'; -- Capital
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 250000.00 FROM cuentas_contables WHERE codigo = '2.1.01'; -- Proveedores
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 60000.00 FROM cuentas_contables WHERE codigo = '2.1.02'; -- Doc por pagar
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 5000.00 FROM cuentas_contables WHERE codigo = '3.1.02'; -- Utilidades ac

-- ASIENTO 2: Ventas y Costos Operativos de la Quincena (15 de Agosto de 2026)
INSERT INTO asientos_contables (fecha, concepto, modulo_origen, usuario_id)
VALUES ('2026-08-15', 'Registro de ingresos por ventas y servicios de la quincena', 'VENTAS', @UsuarioID);
SET @AsientoID = SCOPE_IDENTITY();

-- DEBE (Total 1,030,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 650000.00, 0.00 FROM cuentas_contables WHERE codigo = '5.1.01'; -- Costo ventas
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 185000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.02'; -- Bancos
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 60000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.03'; -- Clientes
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 45000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.01'; -- Caja
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 18000.00, 0.00 FROM cuentas_contables WHERE codigo = '1.1.05'; -- IVA acred
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 70000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.01'; -- Sueldos
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 2000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.04'; -- Agua

-- HABER (Total 1,030,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 950000.00 FROM cuentas_contables WHERE codigo = '4.1.01'; -- Ventas rep
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 80000.00 FROM cuentas_contables WHERE codigo = '4.1.02'; -- Ingresos taller

-- ASIENTO 3: Gastos Operativos y Provisiones de Cierre (31 de Agosto de 2026)
INSERT INTO asientos_contables (fecha, concepto, modulo_origen, usuario_id)
VALUES ('2026-08-31', 'Provisión de gastos operativos, depreciación y cierres', 'CONTABILIDAD', @UsuarioID);
SET @AsientoID = SCOPE_IDENTITY();

-- DEBE (Total 103,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 30000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.02'; -- Alquiler
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 12000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.03'; -- Energía
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 5000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.05'; -- Internet
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 10000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.06'; -- Publicidad
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 8000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.07'; -- Mantenimiento
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 3000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.08'; -- Papelería
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 12000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.09'; -- Depreciación gasto
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 22000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.10'; -- Comisiones
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 1000.00, 0.00 FROM cuentas_contables WHERE codigo = '6.1.04'; -- Agua

-- HABER (Total 103,000)
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 12000.00 FROM cuentas_contables WHERE codigo = '1.2.03'; -- Depreciación acum
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 22000.00 FROM cuentas_contables WHERE codigo = '2.1.03'; -- IVA por pagar
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 18000.00 FROM cuentas_contables WHERE codigo = '2.1.04'; -- Sueldos por pagar
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 5000.00 FROM cuentas_contables WHERE codigo = '2.1.05'; -- Servicios por pagar
INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) SELECT @AsientoID, id, 0.00, 46000.00 FROM cuentas_contables WHERE codigo = '3.1.02'; -- Utilidades acumuladas
GO

PRINT '==============================================================================';
PRINT 'BASE DE DATOS jehova_jireh_db CREADA, POBLADA Y ACTUALIZADA EXITOSAMENTE';
PRINT '==============================================================================';
