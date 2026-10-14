"""
=============================================================================
  SCRIPT DE ACTUALIZACIÓN COMPLETA DE BASE DE DATOS
  Sistema Jehová Jireh Moto Repuestos
  Fecha: Octubre 2026
  
  Este script verifica y crea TODAS las tablas, columnas, vistas,
  foreign keys y datos de catálogo necesarios para que el sistema
  funcione correctamente en tu computadora.
  
  Es SEGURO ejecutar múltiples veces (usa IF NOT EXISTS).
=============================================================================
"""

import pyodbc
import sys

def get_connection():
    servers = ['.', r'.\SQLEXPRESS', '(localdb)\\MSSQLLocalDB', 'localhost']
    for srv in servers:
        try:
            cs = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={srv};DATABASE=jehova_jireh_db;Trusted_Connection=yes;'
            conn = pyodbc.connect(cs, timeout=3)
            conn.autocommit = True
            print(f"Conectado a SQL Server: {srv}")
            return conn
        except:
            continue
    print("No se pudo conectar a SQL Server.")
    print("   Asegurate de que:")
    print("   - SQL Server este corriendo")
    print("   - La base de datos 'jehova_jireh_db' exista")
    print("   - Tengas ODBC Driver 17 for SQL Server instalado")
    sys.exit(1)


def run_migration():
    conn = get_connection()
    cursor = conn.cursor()
    errores = []

    def ejecutar(desc, sql):
        try:
            cursor.execute(sql)
            print(f"  OK: {desc}")
        except Exception as e:
            errores.append((desc, str(e)))
            print(f"  WARN: {desc} -> {e}")

    # =========================================================================
    # SECCION 1: TABLAS BASE DEL SISTEMA
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 1: TABLAS BASE DEL SISTEMA")
    print("="*70)

    ejecutar("Tabla: roles", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'roles')
    CREATE TABLE roles (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL UNIQUE,
        descripcion VARCHAR(255) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: usuarios", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'usuarios')
    CREATE TABLE usuarios (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre_completo VARCHAR(150) NOT NULL,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(255) NOT NULL,
        rol_id INT NULL REFERENCES roles(id),
        activo BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: sesiones", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'sesiones')
    CREATE TABLE sesiones (
        id INT IDENTITY(1,1) PRIMARY KEY,
        usuario_id INT NOT NULL REFERENCES usuarios(id),
        token VARCHAR(255) NULL,
        ip_address VARCHAR(50) NULL,
        fecha_inicio DATETIME DEFAULT GETDATE(),
        fecha_fin DATETIME NULL,
        activo BIT DEFAULT 1
    )
    """)

    ejecutar("Tabla: permisos", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'permisos')
    CREATE TABLE permisos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        rol_id INT NOT NULL REFERENCES roles(id),
        nombre VARCHAR(100) NOT NULL,
        descripcion VARCHAR(255) NULL
    )
    """)

    # =========================================================================
    # SECCION 2: INVENTARIO Y PRODUCTOS
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 2: INVENTARIO Y PRODUCTOS")
    print("="*70)

    ejecutar("Tabla: categorias", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'categorias')
    CREATE TABLE categorias (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL UNIQUE,
        descripcion VARCHAR(255) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: productos", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'productos')
    CREATE TABLE productos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        codigo VARCHAR(50) NOT NULL UNIQUE,
        nombre VARCHAR(200) NOT NULL,
        descripcion VARCHAR(500) NULL,
        categoria_id INT NULL REFERENCES categorias(id),
        precio_compra DECIMAL(12,2) DEFAULT 0,
        precio_venta DECIMAL(12,2) DEFAULT 0,
        stock INT DEFAULT 0,
        stock_minimo INT DEFAULT 5,
        ubicacion VARCHAR(100) NULL,
        marca VARCHAR(100) NULL,
        modelo_compatible VARCHAR(200) NULL,
        unidad_medida VARCHAR(30) DEFAULT 'Unidad',
        activo BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: movimientos_inventario", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'movimientos_inventario')
    CREATE TABLE movimientos_inventario (
        id INT IDENTITY(1,1) PRIMARY KEY,
        producto_id INT NOT NULL REFERENCES productos(id),
        tipo VARCHAR(30) NOT NULL,
        cantidad INT NOT NULL,
        stock_anterior INT DEFAULT 0,
        stock_nuevo INT DEFAULT 0,
        referencia VARCHAR(100) NULL,
        observacion VARCHAR(255) NULL,
        usuario_id INT NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: ajustes_inventario", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ajustes_inventario')
    CREATE TABLE ajustes_inventario (
        id INT IDENTITY(1,1) PRIMARY KEY,
        producto_id INT NOT NULL REFERENCES productos(id),
        tipo VARCHAR(30) NOT NULL,
        cantidad INT NOT NULL,
        motivo VARCHAR(255) NULL,
        usuario_id INT NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    # =========================================================================
    # SECCION 3: CLIENTES, PROVEEDORES Y VENTAS
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 3: CLIENTES, PROVEEDORES Y VENTAS")
    print("="*70)

    ejecutar("Tabla: clientes", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'clientes')
    CREATE TABLE clientes (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        identificacion VARCHAR(30) NULL,
        telefono VARCHAR(30) NULL,
        email VARCHAR(100) NULL,
        direccion VARCHAR(255) NULL,
        tipo VARCHAR(30) DEFAULT 'Regular',
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: proveedores", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'proveedores')
    CREATE TABLE proveedores (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre VARCHAR(150) NOT NULL,
        ruc VARCHAR(30) NULL,
        telefono VARCHAR(30) NULL,
        email VARCHAR(100) NULL,
        direccion VARCHAR(255) NULL,
        contacto VARCHAR(150) NULL,
        activo BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: ventas", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'ventas')
    CREATE TABLE ventas (
        id INT IDENTITY(1,1) PRIMARY KEY,
        cliente_id INT NULL REFERENCES clientes(id),
        usuario_id INT NULL REFERENCES usuarios(id),
        fecha DATETIME DEFAULT GETDATE(),
        subtotal DECIMAL(12,2) DEFAULT 0,
        iva DECIMAL(12,2) DEFAULT 0,
        descuento DECIMAL(12,2) DEFAULT 0,
        total DECIMAL(12,2) DEFAULT 0,
        metodo_pago VARCHAR(30) DEFAULT 'Efectivo',
        estado VARCHAR(30) DEFAULT 'Completada',
        observaciones VARCHAR(500) NULL
    )
    """)

    ejecutar("Tabla: detalle_ventas", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'detalle_ventas')
    CREATE TABLE detalle_ventas (
        id INT IDENTITY(1,1) PRIMARY KEY,
        venta_id INT NOT NULL REFERENCES ventas(id),
        producto_id INT NOT NULL REFERENCES productos(id),
        cantidad INT NOT NULL,
        precio_unitario DECIMAL(12,2) NOT NULL,
        subtotal DECIMAL(12,2) NOT NULL
    )
    """)

    ejecutar("Tabla: compras", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'compras')
    CREATE TABLE compras (
        id INT IDENTITY(1,1) PRIMARY KEY,
        proveedor_id INT NULL REFERENCES proveedores(id),
        usuario_id INT NULL REFERENCES usuarios(id),
        fecha DATETIME DEFAULT GETDATE(),
        numero_factura VARCHAR(50) NULL,
        subtotal DECIMAL(12,2) DEFAULT 0,
        iva DECIMAL(12,2) DEFAULT 0,
        total DECIMAL(12,2) DEFAULT 0,
        estado VARCHAR(30) DEFAULT 'Completada',
        observaciones VARCHAR(500) NULL
    )
    """)

    ejecutar("Tabla: detalle_compras", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'detalle_compras')
    CREATE TABLE detalle_compras (
        id INT IDENTITY(1,1) PRIMARY KEY,
        compra_id INT NOT NULL REFERENCES compras(id),
        producto_id INT NOT NULL REFERENCES productos(id),
        cantidad INT NOT NULL,
        precio_unitario DECIMAL(12,2) NOT NULL,
        subtotal DECIMAL(12,2) NOT NULL
    )
    """)

    ejecutar("Tabla: recepciones_compra", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'recepciones_compra')
    CREATE TABLE recepciones_compra (
        id INT IDENTITY(1,1) PRIMARY KEY,
        compra_id INT NOT NULL REFERENCES compras(id),
        fecha_recepcion DATETIME DEFAULT GETDATE(),
        recibido_por VARCHAR(150) NULL,
        observaciones VARCHAR(500) NULL
    )
    """)

    ejecutar("Tabla: devoluciones", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'devoluciones')
    CREATE TABLE devoluciones (
        id INT IDENTITY(1,1) PRIMARY KEY,
        venta_id INT NULL REFERENCES ventas(id),
        cliente_id INT NULL REFERENCES clientes(id),
        usuario_id INT NULL REFERENCES usuarios(id),
        fecha DATETIME DEFAULT GETDATE(),
        motivo VARCHAR(255) NULL,
        tipo VARCHAR(30) DEFAULT 'Devolucion',
        monto_devuelto DECIMAL(12,2) DEFAULT 0,
        estado VARCHAR(30) DEFAULT 'Procesada'
    )
    """)

    ejecutar("Tabla: detalle_devoluciones", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'detalle_devoluciones')
    CREATE TABLE detalle_devoluciones (
        id INT IDENTITY(1,1) PRIMARY KEY,
        devolucion_id INT NOT NULL REFERENCES devoluciones(id),
        producto_id INT NOT NULL REFERENCES productos(id),
        cantidad INT NOT NULL,
        precio_unitario DECIMAL(12,2) NOT NULL
    )
    """)

    # =========================================================================
    # SECCION 4: CAJA Y PAGOS
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 4: CAJA Y PAGOS")
    print("="*70)

    ejecutar("Tabla: sesiones_caja", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'sesiones_caja')
    CREATE TABLE sesiones_caja (
        id INT IDENTITY(1,1) PRIMARY KEY,
        usuario_id INT NOT NULL REFERENCES usuarios(id),
        fecha_apertura DATETIME DEFAULT GETDATE(),
        fecha_cierre DATETIME NULL,
        monto_apertura DECIMAL(12,2) DEFAULT 0,
        monto_cierre DECIMAL(12,2) NULL,
        total_ventas DECIMAL(12,2) DEFAULT 0,
        total_efectivo DECIMAL(12,2) DEFAULT 0,
        total_tarjeta DECIMAL(12,2) DEFAULT 0,
        total_transferencia DECIMAL(12,2) DEFAULT 0,
        diferencia DECIMAL(12,2) DEFAULT 0,
        estado VARCHAR(20) DEFAULT 'Abierta',
        observaciones VARCHAR(500) NULL
    )
    """)

    ejecutar("Tabla: pagos", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'pagos')
    CREATE TABLE pagos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        venta_id INT NULL,
        pedido_web_id INT NULL,
        monto DECIMAL(12,2) NOT NULL,
        metodo_pago VARCHAR(30) NOT NULL,
        referencia VARCHAR(100) NULL,
        fecha DATETIME DEFAULT GETDATE(),
        origen VARCHAR(20) NOT NULL DEFAULT 'VENTA_POS'
    )
    """)

    ejecutar("Tabla: comprobantes", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'comprobantes')
    CREATE TABLE comprobantes (
        id INT IDENTITY(1,1) PRIMARY KEY,
        venta_id INT NULL,
        pedido_web_id INT NULL,
        numero VARCHAR(50) NOT NULL,
        tipo VARCHAR(30) DEFAULT 'Factura',
        fecha DATETIME DEFAULT GETDATE(),
        total DECIMAL(12,2) DEFAULT 0,
        origen VARCHAR(20) NOT NULL DEFAULT 'VENTA_POS'
    )
    """)

    # =========================================================================
    # SECCION 5: PEDIDOS WEB / E-COMMERCE
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 5: PEDIDOS WEB / E-COMMERCE")
    print("="*70)

    ejecutar("Tabla: pedidos_web", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'pedidos_web')
    CREATE TABLE pedidos_web (
        id INT IDENTITY(1,1) PRIMARY KEY,
        cliente_id INT NULL,
        nombre_cliente VARCHAR(150) NULL,
        telefono VARCHAR(30) NULL,
        email VARCHAR(100) NULL,
        direccion_entrega VARCHAR(MAX) NULL,
        fecha DATETIME DEFAULT GETDATE(),
        subtotal DECIMAL(12,2) DEFAULT 0,
        iva DECIMAL(12,2) DEFAULT 0,
        total DECIMAL(12,2) DEFAULT 0,
        metodo_pago VARCHAR(30) DEFAULT 'Efectivo',
        estado VARCHAR(30) DEFAULT 'Pendiente',
        observaciones VARCHAR(500) NULL
    )
    """)

    ejecutar("Tabla: detalle_pedidos_web", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'detalle_pedidos_web')
    CREATE TABLE detalle_pedidos_web (
        id INT IDENTITY(1,1) PRIMARY KEY,
        pedido_web_id INT NOT NULL REFERENCES pedidos_web(id),
        producto_id INT NOT NULL REFERENCES productos(id),
        cantidad INT NOT NULL,
        precio_unitario DECIMAL(12,2) NOT NULL,
        subtotal DECIMAL(12,2) NOT NULL
    )
    """)

    ejecutar("Tabla: carritos", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'carritos')
    CREATE TABLE carritos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        session_id VARCHAR(100) NOT NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: detalle_carritos", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'detalle_carritos')
    CREATE TABLE detalle_carritos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        carrito_id INT NOT NULL REFERENCES carritos(id),
        producto_id INT NOT NULL REFERENCES productos(id),
        cantidad INT NOT NULL DEFAULT 1
    )
    """)

    # =========================================================================
    # SECCION 6: CONTABILIDAD
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 6: CONTABILIDAD")
    print("="*70)

    ejecutar("Tabla: cuentas_contables", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'cuentas_contables')
    CREATE TABLE cuentas_contables (
        id INT IDENTITY(1,1) PRIMARY KEY,
        codigo VARCHAR(20) NOT NULL UNIQUE,
        nombre VARCHAR(150) NOT NULL,
        tipo VARCHAR(50) NOT NULL,
        naturaleza VARCHAR(20) DEFAULT 'Deudora',
        padre_id INT NULL,
        nivel INT DEFAULT 1,
        activo BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: asientos_contables", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'asientos_contables')
    CREATE TABLE asientos_contables (
        id INT IDENTITY(1,1) PRIMARY KEY,
        numero INT NOT NULL,
        fecha DATE NOT NULL,
        descripcion VARCHAR(255) NOT NULL,
        referencia VARCHAR(100) NULL,
        usuario_id INT NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: movimientos_contables", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'movimientos_contables')
    CREATE TABLE movimientos_contables (
        id INT IDENTITY(1,1) PRIMARY KEY,
        asiento_id INT NOT NULL REFERENCES asientos_contables(id),
        cuenta_id INT NOT NULL REFERENCES cuentas_contables(id),
        debe DECIMAL(14,2) DEFAULT 0,
        haber DECIMAL(14,2) DEFAULT 0,
        descripcion VARCHAR(255) NULL
    )
    """)

    # =========================================================================
    # SECCION 7: RECURSOS HUMANOS - BASE
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 7: RECURSOS HUMANOS - BASE")
    print("="*70)

    ejecutar("Tabla: cargos", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'cargos')
    CREATE TABLE cargos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        descripcion VARCHAR(255) NULL,
        salario_base DECIMAL(12,2) DEFAULT 0,
        departamento VARCHAR(100) NULL,
        activo BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: jornadas_laborales", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'jornadas_laborales')
    CREATE TABLE jornadas_laborales (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre VARCHAR(100) NOT NULL,
        hora_entrada VARCHAR(10) NOT NULL,
        hora_salida VARCHAR(10) NOT NULL,
        minutos_descanso INT DEFAULT 60,
        dias_laborables VARCHAR(100) DEFAULT 'Lunes a Viernes',
        dia_descanso VARCHAR(50) DEFAULT 'Domingo',
        horas_semanales DECIMAL(5,2) DEFAULT 48.00,
        activo BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: empleados", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'empleados')
    CREATE TABLE empleados (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nombre_completo VARCHAR(150) NOT NULL,
        identificacion VARCHAR(30) NULL,
        cargo VARCHAR(100) NULL,
        salario_base DECIMAL(12,2) NOT NULL DEFAULT 0,
        fecha_ingreso DATE NULL,
        activo BIT DEFAULT 1,
        created_at DATETIME DEFAULT GETDATE(),
        num_inss VARCHAR(20) NULL,
        telefono VARCHAR(25) NULL,
        email VARCHAR(100) NULL,
        dias_vacaciones_disponibles DECIMAL(8,2) NOT NULL DEFAULT 0,
        observaciones VARCHAR(500) NULL,
        cargo_id INT NULL,
        vacacionesDisponibles DECIMAL(8,2) NULL,
        fecha_nacimiento DATE NULL,
        direccion VARCHAR(255) NULL,
        contacto_emergencia VARCHAR(150) NULL,
        telefono_emergencia VARCHAR(30) NULL,
        jornada_asignada VARCHAR(100) NULL,
        fecha_baja DATE NULL,
        motivo_baja VARCHAR(255) NULL,
        inss_regimen VARCHAR(50) NULL,
        inss_fecha_alta DATE NULL,
        inss_estado VARCHAR(30) NULL,
        jornada_id INT NULL
    )
    """)

    # Columnas que podrian faltar en empleados (si la tabla ya existia)
    columnas_empleados = [
        ("num_inss", "VARCHAR(20) NULL"),
        ("telefono", "VARCHAR(25) NULL"),
        ("email", "VARCHAR(100) NULL"),
        ("dias_vacaciones_disponibles", "DECIMAL(8,2) NOT NULL DEFAULT 0"),
        ("observaciones", "VARCHAR(500) NULL"),
        ("cargo_id", "INT NULL"),
        ("vacacionesDisponibles", "DECIMAL(8,2) NULL"),
        ("fecha_nacimiento", "DATE NULL"),
        ("direccion", "VARCHAR(255) NULL"),
        ("contacto_emergencia", "VARCHAR(150) NULL"),
        ("telefono_emergencia", "VARCHAR(30) NULL"),
        ("jornada_asignada", "VARCHAR(100) NULL"),
        ("fecha_baja", "DATE NULL"),
        ("motivo_baja", "VARCHAR(255) NULL"),
        ("inss_regimen", "VARCHAR(50) NULL"),
        ("inss_fecha_alta", "DATE NULL"),
        ("inss_estado", "VARCHAR(30) NULL"),
        ("jornada_id", "INT NULL"),
    ]
    for col, tipo in columnas_empleados:
        ejecutar(f"Columna empleados.{col}", f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='empleados' AND COLUMN_NAME='{col}')
            ALTER TABLE empleados ADD {col} {tipo};
        """)

    # =========================================================================
    # SECCION 8: RRHH - RECLUTAMIENTO Y CONTRATOS
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 8: RRHH - RECLUTAMIENTO Y CONTRATOS")
    print("="*70)

    ejecutar("Tabla: solicitudes_empleo", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'solicitudes_empleo')
    CREATE TABLE solicitudes_empleo (
        id INT IDENTITY(1,1) PRIMARY KEY,
        codigo_solicitud VARCHAR(30) NOT NULL,
        nombres_apellidos VARCHAR(150) NOT NULL,
        identificacion VARCHAR(30) NULL,
        direccion VARCHAR(255) NULL,
        telefono VARCHAR(30) NOT NULL,
        email VARCHAR(100) NULL,
        puesto_solicitado VARCHAR(100) NOT NULL,
        formacion_academica VARCHAR(255) NULL,
        experiencia_laboral VARCHAR(MAX) NULL,
        referencias_laborales VARCHAR(MAX) NULL,
        disponibilidad VARCHAR(50) DEFAULT 'Inmediata',
        salario_pretendido DECIMAL(12,2) NULL,
        curriculum_vitae VARCHAR(255) NULL,
        estado VARCHAR(30) DEFAULT 'Recibida',
        observaciones VARCHAR(MAX) NULL,
        fecha_registro DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: contratos_laborales", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'contratos_laborales')
    CREATE TABLE contratos_laborales (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        tipo_contrato VARCHAR(50) NOT NULL DEFAULT 'Indefinido',
        fecha_inicio DATE NOT NULL,
        fecha_fin DATE NULL,
        salario_acordado DECIMAL(12,2) NOT NULL DEFAULT 0,
        cargo VARCHAR(100) NULL,
        jornada VARCHAR(100) NULL,
        clausulas VARCHAR(MAX) NULL,
        estado VARCHAR(30) DEFAULT 'Vigente',
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: expediente_empleado", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'expediente_empleado')
    CREATE TABLE expediente_empleado (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        tipo_documento VARCHAR(100) NOT NULL,
        nombre_archivo VARCHAR(255) NULL,
        usuario_responsable VARCHAR(150) NULL,
        observaciones VARCHAR(500) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: historial_laboral", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'historial_laboral')
    CREATE TABLE historial_laboral (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        tipo_cambio VARCHAR(50) NOT NULL,
        campo_modificado VARCHAR(100) NULL,
        valor_anterior VARCHAR(255) NULL,
        valor_nuevo VARCHAR(255) NULL,
        fecha_cambio DATE DEFAULT GETDATE(),
        usuario_responsable VARCHAR(150) NULL,
        observaciones VARCHAR(500) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    # =========================================================================
    # SECCION 9: RRHH - ASISTENCIA Y MOVIMIENTOS
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 9: RRHH - ASISTENCIA Y MOVIMIENTOS")
    print("="*70)

    ejecutar("Tabla: movimientos_laborales", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'movimientos_laborales')
    CREATE TABLE movimientos_laborales (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        tipo VARCHAR(30) NOT NULL,
        fecha_inicio DATE NOT NULL,
        fecha_fin DATE NOT NULL,
        dias_tomados DECIMAL(5,2) NOT NULL DEFAULT 0,
        observacion VARCHAR(255) NULL,
        created_at DATETIME DEFAULT GETDATE(),
        afecta_septimo_dia BIT DEFAULT 0,
        estado VARCHAR(30) DEFAULT 'Pendiente',
        aprobado_por VARCHAR(100) NULL,
        documento_respaldo VARCHAR(255) NULL,
        clasificacion VARCHAR(50) NULL
    )
    """)

    cols_ml = [
        ("afecta_septimo_dia", "BIT DEFAULT 0"),
        ("estado", "VARCHAR(30) DEFAULT 'Pendiente'"),
        ("aprobado_por", "VARCHAR(100) NULL"),
        ("documento_respaldo", "VARCHAR(255) NULL"),
        ("clasificacion", "VARCHAR(50) NULL"),
    ]
    for col, tipo in cols_ml:
        ejecutar(f"Columna movimientos_laborales.{col}", f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='movimientos_laborales' AND COLUMN_NAME='{col}')
            ALTER TABLE movimientos_laborales ADD {col} {tipo};
        """)

    ejecutar("Tabla: vacaciones", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'vacaciones')
    CREATE TABLE vacaciones (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        fecha_inicio DATE NOT NULL,
        fecha_fin DATE NOT NULL,
        dias INT NOT NULL,
        estado VARCHAR(30) DEFAULT 'Aprobada',
        observaciones VARCHAR(255) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: asistencia_laboral", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'asistencia_laboral')
    CREATE TABLE asistencia_laboral (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        fecha DATE NOT NULL,
        hora_entrada VARCHAR(10) NULL,
        hora_salida VARCHAR(10) NULL,
        estado VARCHAR(30) DEFAULT 'Presente',
        minutos_tardanza INT DEFAULT 0,
        observaciones VARCHAR(255) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: horas_extras", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'horas_extras')
    CREATE TABLE horas_extras (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        fecha DATE NOT NULL,
        horas DECIMAL(5,2) NOT NULL DEFAULT 0,
        tipo VARCHAR(30) DEFAULT 'Doble',
        monto DECIMAL(12,2) DEFAULT 0,
        aprobado BIT DEFAULT 0,
        observaciones VARCHAR(255) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    # =========================================================================
    # SECCION 10: RRHH - NOMINA Y LIQUIDACIONES
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 10: RRHH - NOMINA Y LIQUIDACIONES")
    print("="*70)

    ejecutar("Tabla: nomina", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'nomina')
    CREATE TABLE nomina (
        id INT IDENTITY(1,1) PRIMARY KEY,
        periodo_mes INT NOT NULL,
        periodo_anio INT NOT NULL,
        fecha_generacion DATETIME DEFAULT GETDATE(),
        total_ingresos DECIMAL(14,2) DEFAULT 0,
        total_deducciones DECIMAL(14,2) DEFAULT 0,
        total_neto DECIMAL(14,2) DEFAULT 0,
        inss_patronal_total DECIMAL(14,2) NOT NULL DEFAULT 0,
        provision_vac_total DECIMAL(14,2) NOT NULL DEFAULT 0,
        provision_agui_total DECIMAL(14,2) NOT NULL DEFAULT 0,
        estado VARCHAR(20) NOT NULL DEFAULT 'Generada',
        inatec_patronal_total DECIMAL(14,2) DEFAULT 0
    )
    """)

    ejecutar("Columna nomina.inatec_patronal_total", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='nomina' AND COLUMN_NAME='inatec_patronal_total')
        ALTER TABLE nomina ADD inatec_patronal_total DECIMAL(14,2) DEFAULT 0;
    """)

    ejecutar("Tabla: detalle_nomina", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'detalle_nomina')
    CREATE TABLE detalle_nomina (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nomina_id INT NOT NULL REFERENCES nomina(id),
        empleado_id INT NOT NULL REFERENCES empleados(id),
        salario_base DECIMAL(12,2) DEFAULT 0,
        dias_trabajados INT DEFAULT 30,
        horas_extra_monto DECIMAL(12,2) DEFAULT 0,
        comisiones DECIMAL(12,2) DEFAULT 0,
        bonificaciones DECIMAL(12,2) DEFAULT 0,
        total_ingresos DECIMAL(12,2) DEFAULT 0,
        inss_laboral DECIMAL(12,2) DEFAULT 0,
        ir DECIMAL(12,2) DEFAULT 0,
        prestamos DECIMAL(12,2) DEFAULT 0,
        otros_descuentos DECIMAL(12,2) DEFAULT 0,
        total_deducciones DECIMAL(12,2) DEFAULT 0,
        neto_pagar DECIMAL(12,2) DEFAULT 0,
        inss_patronal DECIMAL(12,2) DEFAULT 0,
        inatec DECIMAL(12,2) DEFAULT 0,
        provision_vacaciones DECIMAL(12,2) DEFAULT 0,
        provision_aguinaldo DECIMAL(12,2) DEFAULT 0
    )
    """)

    ejecutar("Tabla: colilla_pago", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'colilla_pago')
    CREATE TABLE colilla_pago (
        id INT IDENTITY(1,1) PRIMARY KEY,
        detalle_nomina_id INT NOT NULL REFERENCES detalle_nomina(id),
        empleado_id INT NOT NULL REFERENCES empleados(id),
        fecha_emision DATETIME DEFAULT GETDATE(),
        periodo VARCHAR(50) NULL,
        impresa BIT DEFAULT 0
    )
    """)

    ejecutar("Tabla: pagos_nomina", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'pagos_nomina')
    CREATE TABLE pagos_nomina (
        id INT IDENTITY(1,1) PRIMARY KEY,
        nomina_id INT NOT NULL REFERENCES nomina(id),
        empleado_id INT NOT NULL REFERENCES empleados(id),
        monto DECIMAL(12,2) NOT NULL DEFAULT 0,
        metodo_pago VARCHAR(30) DEFAULT 'Transferencia',
        referencia VARCHAR(100) NULL,
        fecha_pago DATETIME DEFAULT GETDATE(),
        estado VARCHAR(20) DEFAULT 'Pagado'
    )
    """)

    ejecutar("Tabla: liquidaciones_laborales", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'liquidaciones_laborales')
    CREATE TABLE liquidaciones_laborales (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        fecha_liquidacion DATE NOT NULL,
        motivo VARCHAR(100) NOT NULL,
        salario_base DECIMAL(12,2) DEFAULT 0,
        dias_trabajados_mes INT DEFAULT 0,
        salario_proporcional DECIMAL(12,2) DEFAULT 0,
        vacaciones_pendientes DECIMAL(12,2) DEFAULT 0,
        aguinaldo_proporcional DECIMAL(12,2) DEFAULT 0,
        indemnizacion DECIMAL(12,2) DEFAULT 0,
        antiguedad_anios DECIMAL(5,2) DEFAULT 0,
        otros_beneficios DECIMAL(12,2) DEFAULT 0,
        deducciones DECIMAL(12,2) DEFAULT 0,
        total_liquidacion DECIMAL(14,2) DEFAULT 0,
        estado VARCHAR(30) DEFAULT 'Calculada',
        observaciones VARCHAR(500) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    # =========================================================================
    # SECCION 11: RRHH - HIGIENE Y SEGURIDAD
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 11: RRHH - HIGIENE Y SEGURIDAD LABORAL")
    print("="*70)

    ejecutar("Tabla: higiene_riesgos", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'higiene_riesgos')
    CREATE TABLE higiene_riesgos (
        id INT IDENTITY(1,1) PRIMARY KEY,
        area VARCHAR(100) NOT NULL,
        tipo_riesgo VARCHAR(100) NOT NULL,
        descripcion VARCHAR(500) NULL,
        nivel_riesgo VARCHAR(30) DEFAULT 'Medio',
        medidas_preventivas VARCHAR(500) NULL,
        responsable_seguimiento VARCHAR(150) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: higiene_inspecciones", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'higiene_inspecciones')
    CREATE TABLE higiene_inspecciones (
        id INT IDENTITY(1,1) PRIMARY KEY,
        fecha DATE NOT NULL,
        area VARCHAR(100) NOT NULL,
        inspector VARCHAR(150) NULL,
        resultado VARCHAR(30) DEFAULT 'Conforme',
        hallazgos VARCHAR(MAX) NULL,
        acciones_correctivas VARCHAR(MAX) NULL,
        proxima_inspeccion DATE NULL,
        estado VARCHAR(30) DEFAULT 'Completada',
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: higiene_incidentes", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'higiene_incidentes')
    CREATE TABLE higiene_incidentes (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        fecha DATE NOT NULL,
        tipo VARCHAR(50) NOT NULL DEFAULT 'Accidente',
        descripcion VARCHAR(MAX) NULL,
        gravedad VARCHAR(30) DEFAULT 'Leve',
        dias_incapacidad INT DEFAULT 0,
        acciones_tomadas VARCHAR(MAX) NULL,
        estado VARCHAR(30) DEFAULT 'Abierto',
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: higiene_epp", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'higiene_epp')
    CREATE TABLE higiene_epp (
        id INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id INT NOT NULL REFERENCES empleados(id),
        equipo VARCHAR(100) NOT NULL,
        fecha_entrega DATE NOT NULL,
        fecha_vencimiento DATE NULL,
        cantidad INT DEFAULT 1,
        estado VARCHAR(30) DEFAULT 'Entregado',
        observaciones VARCHAR(255) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: higiene_capacitaciones", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'higiene_capacitaciones')
    CREATE TABLE higiene_capacitaciones (
        id INT IDENTITY(1,1) PRIMARY KEY,
        tema VARCHAR(200) NOT NULL,
        fecha DATE NOT NULL,
        instructor VARCHAR(150) NULL,
        duracion_horas DECIMAL(5,2) DEFAULT 0,
        participantes VARCHAR(MAX) NULL,
        observaciones VARCHAR(500) NULL,
        created_at DATETIME DEFAULT GETDATE()
    )
    """)

    # =========================================================================
    # SECCION 12: RRHH - PARAMETROS Y CONFIGURACION
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 12: RRHH - PARAMETROS LABORALES")
    print("="*70)

    ejecutar("Tabla: parametros_laborales", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'parametros_laborales')
    CREATE TABLE parametros_laborales (
        id INT IDENTITY(1,1) PRIMARY KEY,
        clave VARCHAR(100) NOT NULL UNIQUE,
        valor VARCHAR(100) NOT NULL,
        descripcion VARCHAR(255) NULL,
        updated_at DATETIME DEFAULT GETDATE()
    )
    """)

    ejecutar("Tabla: calendario_obligaciones", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'calendario_obligaciones')
    CREATE TABLE calendario_obligaciones (
        id INT IDENTITY(1,1) PRIMARY KEY,
        obligacion VARCHAR(150) NOT NULL,
        descripcion VARCHAR(255) NULL,
        fecha_vencimiento DATE NOT NULL,
        estado VARCHAR(30) DEFAULT 'Pendiente',
        responsable VARCHAR(150) NULL,
        updated_at DATETIME DEFAULT GETDATE()
    )
    """)

    # =========================================================================
    # SECCION 13: COLUMNAS ADICIONALES EN TABLAS EXISTENTES
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 13: COLUMNAS ADICIONALES")
    print("="*70)

    for col, tipo in [
        ("nombre_cliente", "VARCHAR(150) NULL"),
        ("telefono", "VARCHAR(30) NULL"),
        ("email", "VARCHAR(100) NULL"),
        ("direccion_entrega", "VARCHAR(MAX) NULL"),
    ]:
        ejecutar(f"Columna pedidos_web.{col}", f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pedidos_web' AND COLUMN_NAME='{col}')
            ALTER TABLE pedidos_web ADD {col} {tipo};
        """)

    for col, tipo in [
        ("pedido_web_id", "INT NULL"),
        ("origen", "VARCHAR(20) NOT NULL DEFAULT 'VENTA_POS'"),
    ]:
        ejecutar(f"Columna pagos.{col}", f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pagos' AND COLUMN_NAME='{col}')
            ALTER TABLE pagos ADD {col} {tipo};
        """)

    for col, tipo in [
        ("pedido_web_id", "INT NULL"),
        ("origen", "VARCHAR(20) NOT NULL DEFAULT 'VENTA_POS'"),
    ]:
        ejecutar(f"Columna comprobantes.{col}", f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='comprobantes' AND COLUMN_NAME='{col}')
            ALTER TABLE comprobantes ADD {col} {tipo};
        """)

    ejecutar("pagos.venta_id nullable", """
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pagos' AND COLUMN_NAME='venta_id' AND IS_NULLABLE='NO')
        ALTER TABLE pagos ALTER COLUMN venta_id INT NULL;
    """)
    ejecutar("comprobantes.venta_id nullable", """
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='comprobantes' AND COLUMN_NAME='venta_id' AND IS_NULLABLE='NO')
        ALTER TABLE comprobantes ALTER COLUMN venta_id INT NULL;
    """)
    ejecutar("pedidos_web.cliente_id nullable", """
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pedidos_web' AND COLUMN_NAME='cliente_id' AND IS_NULLABLE='NO')
        ALTER TABLE pedidos_web ALTER COLUMN cliente_id INT NULL;
    """)

    # =========================================================================
    # SECCION 14: FOREIGN KEYS
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 14: FOREIGN KEYS")
    print("="*70)

    ejecutar("FK: pagos -> pedidos_web", """
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_pagos_pedidos_web')
    AND EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pagos' AND COLUMN_NAME='pedido_web_id')
        ALTER TABLE pagos ADD CONSTRAINT fk_pagos_pedidos_web FOREIGN KEY (pedido_web_id) REFERENCES pedidos_web(id);
    """)

    ejecutar("FK: comprobantes -> pedidos_web", """
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_comprobantes_pedidos_web')
    AND EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='comprobantes' AND COLUMN_NAME='pedido_web_id')
        ALTER TABLE comprobantes ADD CONSTRAINT fk_comprobantes_pedidos_web FOREIGN KEY (pedido_web_id) REFERENCES pedidos_web(id);
    """)

    # =========================================================================
    # SECCION 15: VISTAS
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 15: VISTAS")
    print("="*70)

    ejecutar("Vista: vista_resumen_rrhh", """
    CREATE OR ALTER VIEW vista_resumen_rrhh AS
    SELECT 
        e.id AS empleado_id,
        e.nombre_completo,
        e.identificacion,
        e.cargo,
        e.salario_base,
        e.dias_vacaciones_disponibles,
        e.activo,
        COUNT(ml.id) AS total_incidencias_registradas
    FROM empleados e
    LEFT JOIN movimientos_laborales ml ON e.id = ml.empleado_id
    GROUP BY e.id, e.nombre_completo, e.identificacion, e.cargo, 
             e.salario_base, e.dias_vacaciones_disponibles, e.activo;
    """)

    ejecutar("Vista: vista_kardex_completo", """
    CREATE OR ALTER VIEW vista_kardex_completo AS
    SELECT 
        mi.id, mi.producto_id, p.codigo, p.nombre AS producto_nombre,
        mi.tipo, mi.cantidad, mi.stock_anterior, mi.stock_nuevo,
        mi.referencia, mi.observacion, mi.created_at
    FROM movimientos_inventario mi
    INNER JOIN productos p ON mi.producto_id = p.id;
    """)

    ejecutar("Vista: vista_stock_bajo", """
    CREATE OR ALTER VIEW vista_stock_bajo AS
    SELECT id, codigo, nombre, stock, stock_minimo, categoria_id, precio_venta
    FROM productos
    WHERE stock <= stock_minimo AND activo = 1;
    """)

    ejecutar("Vista: vista_balance_inventario", """
    CREATE OR ALTER VIEW vista_balance_inventario AS
    SELECT 
        c.nombre AS categoria,
        COUNT(p.id) AS total_productos,
        SUM(p.stock) AS total_stock,
        SUM(p.stock * p.precio_compra) AS valor_costo,
        SUM(p.stock * p.precio_venta) AS valor_venta
    FROM productos p
    LEFT JOIN categorias c ON p.categoria_id = c.id
    WHERE p.activo = 1
    GROUP BY c.nombre;
    """)

    ejecutar("Vista: vista_top_productos_vendidos", """
    CREATE OR ALTER VIEW vista_top_productos_vendidos AS
    SELECT TOP 20
        p.id, p.codigo, p.nombre, 
        SUM(dv.cantidad) AS total_vendido,
        SUM(dv.subtotal) AS total_ingreso
    FROM detalle_ventas dv
    INNER JOIN productos p ON dv.producto_id = p.id
    INNER JOIN ventas v ON dv.venta_id = v.id
    WHERE v.estado = 'Completada'
    GROUP BY p.id, p.codigo, p.nombre
    ORDER BY total_vendido DESC;
    """)

    # =========================================================================
    # SECCION 16: DATOS DE CATALOGO
    # =========================================================================
    print("\n" + "="*70)
    print("  SECCION 16: DATOS DE CATALOGO")
    print("="*70)

    parametros = [
        ('salario_minimo', '6615.35', 'Salario minimo vigente (C$)'),
        ('inss_laboral_porcentaje', '7.00', 'Porcentaje INSS laboral'),
        ('inss_patronal_porcentaje', '22.50', 'Porcentaje INSS patronal'),
        ('inatec_porcentaje', '2.00', 'Porcentaje INATEC patronal'),
        ('dias_vacaciones_anual', '30', 'Dias de vacaciones por anio'),
        ('septimo_dia', '1', 'Incluir septimo dia en calculos (1=Si, 0=No)'),
        ('ir_techo_exento', '100000.00', 'Techo exento anual de IR (C$)'),
    ]
    for clave, valor, desc in parametros:
        ejecutar(f"Parametro: {clave}", f"""
        IF NOT EXISTS (SELECT 1 FROM parametros_laborales WHERE clave = '{clave}')
            INSERT INTO parametros_laborales (clave, valor, descripcion) VALUES ('{clave}', '{valor}', '{desc}');
        """)

    obligaciones = [
        ('Pago INSS', 'Pago mensual de cuotas INSS laboral y patronal', '2026-11-17', 'Pendiente'),
        ('Pago INATEC', 'Pago mensual de aporte INATEC 2%', '2026-11-17', 'Pendiente'),
        ('Declaracion IR', 'Retencion mensual de IR sobre salarios', '2026-11-05', 'Pendiente'),
        ('Aguinaldo', 'Pago de decimo tercer mes (antes del 10 de diciembre)', '2026-12-10', 'Pendiente'),
    ]
    for obl, desc, fv, est in obligaciones:
        ejecutar(f"Obligacion: {obl}", f"""
        IF NOT EXISTS (SELECT 1 FROM calendario_obligaciones WHERE obligacion = '{obl}')
            INSERT INTO calendario_obligaciones (obligacion, descripcion, fecha_vencimiento, estado) 
            VALUES ('{obl}', '{desc}', '{fv}', '{est}');
        """)

    roles = [
        'Administrador', 'Vendedor', 'Encargado de Inventario', 'Contador',
        'Gerente de Operaciones', 'Gerente Administrativo y Financiero',
        'Encargado de Compras y Proveedores', 'Responsable de Recursos Humanos'
    ]
    for rol in roles:
        ejecutar(f"Rol: {rol}", f"""
        IF NOT EXISTS (SELECT 1 FROM roles WHERE nombre = '{rol}')
            INSERT INTO roles (nombre) VALUES ('{rol}');
        """)

    print("\n  Sincronizando permisos...")
    cursor.execute("SELECT id, nombre FROM roles")
    roles_map = {r[1]: r[0] for r in cursor.fetchall()}

    permisos_list = [
        ('Administrador', 'administracion_total', 'Acceso total y configuracion del sistema'),
        ('Administrador', 'usuarios_gestionar', 'Administrar usuarios y accesos'),
        ('Administrador', 'roles_permisos_gestionar', 'Asignar roles y permisos'),
        ('Administrador', 'reportes_gerenciales_ver', 'Visualizacion de reportes ejecutivos y auditoria'),
        ('Administrador', 'auditoria_sesiones_ver', 'Consultar historial y sesiones activas'),
        ('Vendedor', 'ventas_crear', 'Emitir facturas y ventas en mostrador'),
        ('Vendedor', 'caja_operar', 'Abrir caja, cobrar y realizar corte de caja'),
        ('Vendedor', 'clientes_gestionar', 'Consultar y registrar clientes'),
        ('Vendedor', 'productos_consultar', 'Consultar catalogo, precios y existencias'),
        ('Encargado de Inventario', 'productos_gestionar', 'Crear y actualizar repuestos y precios'),
        ('Encargado de Inventario', 'kardex_consultar', 'Consultar movimientos y existencias'),
        ('Encargado de Inventario', 'ajustes_inventario_crear', 'Registrar ajustes de entrada y salida de stock'),
        ('Contador', 'cuentas_contables_gestionar', 'Administrar catalogo de cuentas contables'),
        ('Contador', 'asientos_contables_registrar', 'Registrar asientos en el libro diario'),
        ('Contador', 'estados_financieros_ver', 'Generar balance general, estado de resultados y mayor'),
        ('Contador', 'reportes_fiscales_ver', 'Consultar reportes de IVA y retenciones'),
        ('Gerente de Operaciones', 'inventario_supervisar', 'Supervision de stock, almacen y abastecimiento'),
        ('Gerente de Operaciones', 'compras_supervisar', 'Aprobacion de compras y control de proveedores'),
        ('Gerente de Operaciones', 'ventas_supervisar', 'Monitoreo de rendimiento de ventas y mostrador'),
        ('Gerente Administrativo y Financiero', 'finanzas_supervisar', 'Supervision de balances, costos y rentabilidad'),
        ('Gerente Administrativo y Financiero', 'rrhh_supervisar', 'Supervision de planilla y gestion de personal'),
        ('Gerente Administrativo y Financiero', 'reportes_gerenciales_ver', 'Visualizacion de reportes ejecutivos'),
        ('Encargado de Compras y Proveedores', 'compras_registrar', 'Registrar ordenes de compra y facturas de proveedores'),
        ('Encargado de Compras y Proveedores', 'proveedores_gestionar', 'Administrar catalogo y cuentas de proveedores'),
        ('Encargado de Compras y Proveedores', 'recepciones_compra_registrar', 'Confirmar recepcion fisica de mercaderia'),
        ('Responsable de Recursos Humanos', 'empleados_gestionar', 'Registrar y editar expedientes de empleados'),
        ('Responsable de Recursos Humanos', 'cargos_gestionar', 'Administrar cargos y salarios'),
        ('Responsable de Recursos Humanos', 'movimientos_laborales_registrar', 'Registrar faltas, permisos y justificaciones'),
        ('Responsable de Recursos Humanos', 'vacaciones_gestionar', 'Registrar y aprobar solicitudes de vacaciones'),
        ('Responsable de Recursos Humanos', 'nomina_procesar', 'Calcular y generar nomina quincenal/mensual'),
        ('Responsable de Recursos Humanos', 'colillas_pago_emitir', 'Generar e imprimir colillas de pago'),
    ]

    inserted = 0
    for rol_nombre, nombre, desc in permisos_list:
        rol_id = roles_map.get(rol_nombre)
        if not rol_id:
            continue
        cursor.execute("SELECT 1 FROM permisos WHERE rol_id = ? AND nombre = ?", (rol_id, nombre))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO permisos (rol_id, nombre, descripcion) VALUES (?, ?, ?)", (rol_id, nombre, desc))
            inserted += 1
    print(f"  OK: Permisos sincronizados: {inserted} nuevos insertados")

    cargos_iniciales = [
        ('Vendedor de Mostrador', 'Atencion al cliente y ventas', 7500.00, 'Ventas'),
        ('Encargado de Almacen', 'Gestion de inventario y almacen', 8500.00, 'Inventario'),
        ('Cajero', 'Operaciones de caja y cobros', 7000.00, 'Ventas'),
        ('Auxiliar Contable', 'Apoyo en registros contables', 8000.00, 'Administracion'),
        ('Gerente General', 'Direccion general del negocio', 15000.00, 'Administracion'),
    ]
    for nombre, desc, salario, depto in cargos_iniciales:
        ejecutar(f"Cargo: {nombre}", f"""
        IF NOT EXISTS (SELECT 1 FROM cargos WHERE nombre = '{nombre}')
            INSERT INTO cargos (nombre, descripcion, salario_base, departamento) 
            VALUES ('{nombre}', '{desc}', {salario}, '{depto}');
        """)

    jornadas = [
        ('Jornada Diurna', '07:00', '16:00', 60, 'Lunes a Viernes', 'Domingo', 48.00),
        ('Jornada Mixta', '10:00', '19:00', 60, 'Lunes a Sabado', 'Domingo', 48.00),
        ('Medio Tiempo', '08:00', '12:00', 0, 'Lunes a Viernes', 'Sabado y Domingo', 20.00),
    ]
    for nombre, he, hs, md, dl, dd, hs_val in jornadas:
        ejecutar(f"Jornada: {nombre}", f"""
        IF NOT EXISTS (SELECT 1 FROM jornadas_laborales WHERE nombre = '{nombre}')
            INSERT INTO jornadas_laborales (nombre, hora_entrada, hora_salida, minutos_descanso, dias_laborables, dia_descanso, horas_semanales)
            VALUES ('{nombre}', '{he}', '{hs}', {md}, '{dl}', '{dd}', {hs_val});
        """)

    # =========================================================================
    # RESUMEN FINAL
    # =========================================================================
    print("\n" + "="*70)
    print("  VERIFICACION FINAL")
    print("="*70)

    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_TYPE='BASE TABLE' ORDER BY TABLE_NAME")
    tablas_finales = [r[0] for r in cursor.fetchall()]
    print(f"\n  Total de tablas: {len(tablas_finales)}")
    for t in tablas_finales:
        cursor.execute(f"SELECT COUNT(*) FROM [{t}]")
        cnt = cursor.fetchone()[0]
        print(f"    {t}: {cnt} registros")

    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS ORDER BY TABLE_NAME")
    vistas_finales = [r[0] for r in cursor.fetchall()]
    print(f"\n  Total de vistas: {len(vistas_finales)}")
    for v in vistas_finales:
        print(f"    {v}")

    conn.close()

    if errores:
        print(f"\n  Se encontraron {len(errores)} advertencia(s):")
        for desc, err in errores:
            print(f"    - {desc}: {err}")
    else:
        print("\n  TODAS las operaciones completadas sin errores!")

    print("\n" + "="*70)
    print("  BASE DE DATOS ACTUALIZADA EXITOSAMENTE!")
    print("="*70)


if __name__ == '__main__':
    run_migration()
