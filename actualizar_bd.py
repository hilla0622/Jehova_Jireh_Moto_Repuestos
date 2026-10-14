import pyodbc

def migrate():
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=.;DATABASE=jehova_jireh_db;Trusted_Connection=yes;')
    conn.autocommit = True
    cursor = conn.cursor()

    print("1. Verificando y agregando columnas a 'pedidos_web'...")
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pedidos_web' AND COLUMN_NAME='nombre_cliente')
        ALTER TABLE pedidos_web ADD nombre_cliente VARCHAR(150) NULL;
    """)
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pedidos_web' AND COLUMN_NAME='telefono')
        ALTER TABLE pedidos_web ADD telefono VARCHAR(30) NULL;
    """)
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pedidos_web' AND COLUMN_NAME='email')
        ALTER TABLE pedidos_web ADD email VARCHAR(100) NULL;
    """)
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pedidos_web' AND COLUMN_NAME='direccion_entrega')
        ALTER TABLE pedidos_web ADD direccion_entrega VARCHAR(MAX) NULL;
    """)
    cursor.execute("""
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pedidos_web' AND COLUMN_NAME='cliente_id' AND IS_NULLABLE='NO')
        ALTER TABLE pedidos_web ALTER COLUMN cliente_id INT NULL;
    """)
    print("   -> pedidos_web actualizado.")

    print("2. Verificando y agregando columnas a 'pagos'...")
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pagos' AND COLUMN_NAME='pedido_web_id')
        ALTER TABLE pagos ADD pedido_web_id INT NULL;
    """)
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pagos' AND COLUMN_NAME='origen')
        ALTER TABLE pagos ADD origen VARCHAR(20) NOT NULL CONSTRAINT df_pagos_origen DEFAULT 'VENTA_POS';
    """)
    cursor.execute("""
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='pagos' AND COLUMN_NAME='venta_id' AND IS_NULLABLE='NO')
        ALTER TABLE pagos ALTER COLUMN venta_id INT NULL;
    """)
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_pagos_pedidos_web')
        ALTER TABLE pagos ADD CONSTRAINT fk_pagos_pedidos_web FOREIGN KEY (pedido_web_id) REFERENCES pedidos_web(id);
    """)
    print("   -> pagos actualizado.")

    print("3. Verificando y agregando columnas a 'comprobantes'...")
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='comprobantes' AND COLUMN_NAME='pedido_web_id')
        ALTER TABLE comprobantes ADD pedido_web_id INT NULL;
    """)
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='comprobantes' AND COLUMN_NAME='origen')
        ALTER TABLE comprobantes ADD origen VARCHAR(20) NOT NULL CONSTRAINT df_comprobantes_origen DEFAULT 'VENTA_POS';
    """)
    cursor.execute("""
    IF EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='comprobantes' AND COLUMN_NAME='venta_id' AND IS_NULLABLE='NO')
        ALTER TABLE comprobantes ALTER COLUMN venta_id INT NULL;
    """)
    cursor.execute("""
    IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_comprobantes_pedidos_web')
        ALTER TABLE comprobantes ADD CONSTRAINT fk_comprobantes_pedidos_web FOREIGN KEY (pedido_web_id) REFERENCES pedidos_web(id);
    """)
    print("   -> comprobantes actualizado.")

    print("4. Verificando y creando vistas faltantes...")
    cursor.execute("""
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
    GROUP BY e.id, e.nombre_completo, e.identificacion, e.cargo, e.salario_base, e.dias_vacaciones_disponibles, e.activo;
    """)
    print("   -> vista_resumen_rrhh creada / actualizada.")

    print("5. Verificando e insertando catálogo de permisos...")
    cursor.execute("SELECT id, nombre FROM roles")
    roles_map = {r[1]: r[0] for r in cursor.fetchall()}

    permisos_by_role_name = [
        # Administrador
        ('Administrador', 'administracion_total', 'Acceso total y configuración del sistema'),
        ('Administrador', 'usuarios_gestionar', 'Administrar usuarios y accesos'),
        ('Administrador', 'roles_permisos_gestionar', 'Asignar roles y permisos'),
        ('Administrador', 'reportes_gerenciales_ver', 'Visualización de reportes ejecutivos y auditoría'),
        ('Administrador', 'auditoria_sesiones_ver', 'Consultar historial y sesiones activas'),
        # Vendedor
        ('Vendedor', 'ventas_crear', 'Emitir facturas y ventas en mostrador'),
        ('Vendedor', 'caja_operar', 'Abrir caja, cobrar y realizar corte de caja'),
        ('Vendedor', 'clientes_gestionar', 'Consultar y registrar clientes'),
        ('Vendedor', 'productos_consultar', 'Consultar catálogo, precios y existencias'),
        # Encargado de Inventario
        ('Encargado de Inventario', 'productos_gestionar', 'Crear y actualizar repuestos y precios'),
        ('Encargado de Inventario', 'kardex_consultar', 'Consultar movimientos y existencias'),
        ('Encargado de Inventario', 'ajustes_inventario_crear', 'Registrar ajustes de entrada y salida de stock'),
        # Contador
        ('Contador', 'cuentas_contables_gestionar', 'Administrar catálogo de cuentas contables'),
        ('Contador', 'asientos_contables_registrar', 'Registrar asientos en el libro diario'),
        ('Contador', 'estados_financieros_ver', 'Generar balance general, estado de resultados y mayor'),
        ('Contador', 'reportes_fiscales_ver', 'Consultar reportes de IVA y retenciones'),
        # Gerente de Operaciones
        ('Gerente de Operaciones', 'inventario_supervisar', 'Supervisión de stock, almacén y abastecimiento'),
        ('Gerente de Operaciones', 'compras_supervisar', 'Aprobación de compras y control de proveedores'),
        ('Gerente de Operaciones', 'ventas_supervisar', 'Monitoreo de rendimiento de ventas y mostrador'),
        # Gerente Administrativo y Financiero
        ('Gerente Administrativo y Financiero', 'finanzas_supervisar', 'Supervisión de balances, costos y rentabilidad'),
        ('Gerente Administrativo y Financiero', 'rrhh_supervisar', 'Supervisión de planilla y gestión de personal'),
        ('Gerente Administrativo y Financiero', 'reportes_gerenciales_ver', 'Visualización de reportes ejecutivos'),
        # Encargado de Compras y Proveedores
        ('Encargado de Compras y Proveedores', 'compras_registrar', 'Registrar órdenes de compra y facturas de proveedores'),
        ('Encargado de Compras y Proveedores', 'proveedores_gestionar', 'Administrar catálogo y cuentas de proveedores'),
        ('Encargado de Compras y Proveedores', 'recepciones_compra_registrar', 'Confirmar recepción física de mercadería'),
        # Responsable de Recursos Humanos
        ('Responsable de Recursos Humanos', 'empleados_gestionar', 'Registrar y editar expedientes de empleados'),
        ('Responsable de Recursos Humanos', 'cargos_gestionar', 'Administrar cargos y salarios'),
        ('Responsable de Recursos Humanos', 'movimientos_laborales_registrar', 'Registrar faltas, permisos y justificaciones'),
        ('Responsable de Recursos Humanos', 'vacaciones_gestionar', 'Registrar y aprobar solicitudes de vacaciones'),
        ('Responsable de Recursos Humanos', 'nomina_procesar', 'Calcular y generar nómina quincenal/mensual'),
        ('Responsable de Recursos Humanos', 'colillas_pago_emitir', 'Generar e imprimir colillas de pago')
    ]

    inserted_permisos = 0
    for rol_nombre, nombre, descripcion in permisos_by_role_name:
        rol_id = roles_map.get(rol_nombre)
        if not rol_id:
            print(f"   [AVISO] Rol no encontrado: {rol_nombre}")
            continue
        cursor.execute("SELECT 1 FROM permisos WHERE rol_id = ? AND nombre = ?", (rol_id, nombre))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO permisos (rol_id, nombre, descripcion) VALUES (?, ?, ?)", (rol_id, nombre, descripcion))
            inserted_permisos += 1
    print(f"   -> Permisos sincronizados: {inserted_permisos} nuevos insertados.")

    conn.close()
    print("¡MIGRACIÓN Y ACTUALIZACIÓN COMPLETADA CON ÉXITO!")

if __name__ == '__main__':
    migrate()
