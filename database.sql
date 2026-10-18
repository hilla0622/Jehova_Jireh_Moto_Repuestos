-- ==============================================================================
-- BASE DE DATOS: JEHOVA JIREH MOTO REPUESTOS
-- SCRIPT INTEGRAL ACTUALIZADO AL 100% (50 TABLAS + 5 VISTAS + DATOS)
-- Compatible con SQL Server 2017 / 2019 / 2022 / Express
-- ==============================================================================

USE master;
GO

IF NOT EXISTS (SELECT 1 FROM sys.databases WHERE name = 'jehova_jireh_db')
BEGIN
    CREATE DATABASE jehova_jireh_db;
END
GO

USE jehova_jireh_db;
GO

-- -------------------------------------------------------------
-- Tabla: ajustes_inventario
-- -------------------------------------------------------------
IF OBJECT_ID('ajustes_inventario', 'U') IS NULL
BEGIN
CREATE TABLE [ajustes_inventario] (
    [id] int IDENTITY(1,1) NOT NULL,
    [producto_id] int NOT NULL,
    [tipo] varchar(30) NOT NULL,
    [cantidad] int NOT NULL,
    [motivo] varchar(255) NULL,
    [fecha] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_ajustes_inventario] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: asientos_contables
-- -------------------------------------------------------------
IF OBJECT_ID('asientos_contables', 'U') IS NULL
BEGIN
CREATE TABLE [asientos_contables] (
    [id] int IDENTITY(1,1) NOT NULL,
    [fecha] date NOT NULL,
    [concepto] varchar(255) NOT NULL,
    [modulo_origen] varchar(50) NULL,
    [referencia_id] int NULL,
    [usuario_id] int NOT NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_asientos_contables] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: asistencia_laboral
-- -------------------------------------------------------------
IF OBJECT_ID('asistencia_laboral', 'U') IS NULL
BEGIN
CREATE TABLE [asistencia_laboral] (
    [id] int IDENTITY(1,1) NOT NULL,
    [empleado_id] int NOT NULL,
    [fecha] date NOT NULL,
    [hora_entrada] time NULL,
    [hora_salida] time NULL,
    [estado] varchar(50) DEFAULT ('Asistencia Completa') NOT NULL,
    [minutos_tardanza] int DEFAULT ((0)) NULL,
    [observaciones] varchar(255) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_asistencia_laboral] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: calendario_obligaciones
-- -------------------------------------------------------------
IF OBJECT_ID('calendario_obligaciones', 'U') IS NULL
BEGIN
CREATE TABLE [calendario_obligaciones] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nombre_obligacion] varchar(150) NOT NULL,
    [institucion] varchar(50) NOT NULL,
    [periodo] varchar(50) NOT NULL,
    [fecha_vencimiento] date NOT NULL,
    [responsable] varchar(100) NULL,
    [estado] varchar(30) DEFAULT ('Pendiente') NULL,
    [fecha_cumplimiento] date NULL,
    [comprobante_adjunto] varchar(255) NULL,
    [observaciones] varchar(255) NULL,
    CONSTRAINT [pk_calendario_obligaciones] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: cargos
-- -------------------------------------------------------------
IF OBJECT_ID('cargos', 'U') IS NULL
BEGIN
CREATE TABLE [cargos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nombre_cargo] varchar(100) NOT NULL,
    [descripcion] varchar(255) NULL,
    [salario_base_sugerido] decimal(12,2) DEFAULT ((0.00)) NULL,
    [activo] bit DEFAULT ((1)) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [area] varchar(100) DEFAULT ('Ventas') NULL,
    [responsabilidades] varchar(MAX) NULL,
    CONSTRAINT [pk_cargos] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: carritos
-- -------------------------------------------------------------
IF OBJECT_ID('carritos', 'U') IS NULL
BEGIN
CREATE TABLE [carritos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [cliente_id] int NOT NULL,
    [subtotal] decimal(12,2) DEFAULT ((0.00)) NULL,
    [estado] varchar(20) DEFAULT ('Activo') NULL,
    CONSTRAINT [pk_carritos] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: categorias
-- -------------------------------------------------------------
IF OBJECT_ID('categorias', 'U') IS NULL
BEGIN
CREATE TABLE [categorias] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nombre] varchar(100) NOT NULL,
    [descripcion] varchar(MAX) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_categorias] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: clientes
-- -------------------------------------------------------------
IF OBJECT_ID('clientes', 'U') IS NULL
BEGIN
CREATE TABLE [clientes] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nombre_completo] varchar(150) NOT NULL,
    [identificacion] varchar(30) NULL,
    [telefono] varchar(25) NULL,
    [email] varchar(100) NULL,
    [direccion] varchar(MAX) NULL,
    [tipo_cliente] varchar(30) DEFAULT ('General') NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [password_hash] varchar(255) NULL,
    CONSTRAINT [pk_clientes] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: colilla_pago
-- -------------------------------------------------------------
IF OBJECT_ID('colilla_pago', 'U') IS NULL
BEGIN
CREATE TABLE [colilla_pago] (
    [id] int IDENTITY(1,1) NOT NULL,
    [detalle_nomina_id] int NOT NULL,
    [periodo] varchar(50) NOT NULL,
    [netoRecibir] decimal(12,2) NOT NULL,
    CONSTRAINT [pk_colilla_pago] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: compras
-- -------------------------------------------------------------
IF OBJECT_ID('compras', 'U') IS NULL
BEGIN
CREATE TABLE [compras] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo_compra] varchar(30) NOT NULL,
    [numero_factura_proveedor] varchar(50) NULL,
    [proveedor_id] int NOT NULL,
    [usuario_id] int NOT NULL,
    [fecha_compra] date NOT NULL,
    [total] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [forma_pago] varchar(30) DEFAULT ('Efectivo') NULL,
    [estado] varchar(30) DEFAULT ('Completada') NULL,
    [observaciones] varchar(MAX) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_compras] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: comprobantes
-- -------------------------------------------------------------
IF OBJECT_ID('comprobantes', 'U') IS NULL
BEGIN
CREATE TABLE [comprobantes] (
    [id] int IDENTITY(1,1) NOT NULL,
    [venta_id] int NULL,
    [numero] varchar(50) NOT NULL,
    [fechaEmision] datetime DEFAULT (getdate()) NULL,
    [total] decimal(12,2) NOT NULL,
    [pedido_web_id] int NULL,
    [origen] varchar(20) DEFAULT ('VENTA_POS') NOT NULL,
    CONSTRAINT [pk_comprobantes] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: contratos_laborales
-- -------------------------------------------------------------
IF OBJECT_ID('contratos_laborales', 'U') IS NULL
BEGIN
CREATE TABLE [contratos_laborales] (
    [id] int IDENTITY(1,1) NOT NULL,
    [numero_contrato] varchar(50) NOT NULL,
    [empleado_id] int NOT NULL,
    [tipo_contratacion] varchar(50) DEFAULT ('Tiempo Indeterminado') NOT NULL,
    [lugar_trabajo] varchar(150) DEFAULT ('Masatepe, Masaya - Tienda Principal') NULL,
    [cargo] varchar(100) NOT NULL,
    [jornada_laboral] varchar(100) NOT NULL,
    [salario_mensual] decimal(12,2) NOT NULL,
    [forma_pago] varchar(50) DEFAULT ('Quincenal / Mensual') NULL,
    [fecha_inicio] date NOT NULL,
    [fecha_fin] date NULL,
    [estado] varchar(30) DEFAULT ('Vigente') NULL,
    [documento_adjunto] varchar(255) NULL,
    [observaciones] varchar(MAX) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_contratos_laborales] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: cuentas_contables
-- -------------------------------------------------------------
IF OBJECT_ID('cuentas_contables', 'U') IS NULL
BEGIN
CREATE TABLE [cuentas_contables] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo] varchar(20) NOT NULL,
    [nombre] varchar(100) NOT NULL,
    [clasificacion] varchar(50) NOT NULL,
    [naturaleza] varchar(20) NOT NULL,
    [descripcion] varchar(255) NULL,
    [activo] bit DEFAULT ((1)) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_cuentas_contables] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: detalle_carritos
-- -------------------------------------------------------------
IF OBJECT_ID('detalle_carritos', 'U') IS NULL
BEGIN
CREATE TABLE [detalle_carritos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [carrito_id] int NOT NULL,
    [producto_id] int NOT NULL,
    [cantidad] int NOT NULL,
    [precioUnitario] decimal(12,2) NOT NULL,
    [subtotal] decimal(12,2) NOT NULL,
    CONSTRAINT [pk_detalle_carritos] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: detalle_compras
-- -------------------------------------------------------------
IF OBJECT_ID('detalle_compras', 'U') IS NULL
BEGIN
CREATE TABLE [detalle_compras] (
    [id] int IDENTITY(1,1) NOT NULL,
    [compra_id] int NOT NULL,
    [producto_id] int NOT NULL,
    [cantidad] int NOT NULL,
    [costo_unitario] decimal(12,2) NOT NULL,
    [subtotal] decimal(12,2) NOT NULL,
    CONSTRAINT [pk_detalle_compras] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: detalle_devoluciones
-- -------------------------------------------------------------
IF OBJECT_ID('detalle_devoluciones', 'U') IS NULL
BEGIN
CREATE TABLE [detalle_devoluciones] (
    [id] int IDENTITY(1,1) NOT NULL,
    [devolucion_id] int NOT NULL,
    [producto_id] int NOT NULL,
    [cantidad] int NOT NULL,
    [precio_unitario] decimal(12,2) NOT NULL,
    [subtotal] decimal(12,2) NOT NULL,
    CONSTRAINT [pk_detalle_devoluciones] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: detalle_nomina
-- -------------------------------------------------------------
IF OBJECT_ID('detalle_nomina', 'U') IS NULL
BEGIN
CREATE TABLE [detalle_nomina] (
    [historico_salario] decimal(12,2) NULL,
    [historico_nombre] nvarchar(150) NULL,
    [historico_identificacion] nvarchar(50) NULL,
    [historico_cargo] nvarchar(100) NULL,
    [historico_inss] nvarchar(50) NULL,
    [historico_ingreso] date NULL,
    [id] int IDENTITY(1,1) NOT NULL,
    [nomina_id] int NOT NULL,
    [empleado_id] int NOT NULL,
    [salario_base] decimal(12,2) NOT NULL,
    [inss_laboral] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [ir] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [otras_deducciones] decimal(12,2) DEFAULT ((0.00)) NULL,
    [neto_pagar] decimal(12,2) NOT NULL,
    [ingresos_extra] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [inss_patronal] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [provision_vacaciones] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [provision_aguinaldo] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [kpi_comision] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [adelanto_salarial] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [dias_trabajados] decimal(4,1) DEFAULT ((15.0)) NOT NULL,
    [vac_acumulada] decimal(5,2) DEFAULT ((0.00)) NOT NULL,
    [vac_mes] decimal(5,2) DEFAULT ((0.00)) NOT NULL,
    [vac_descansados] decimal(5,2) DEFAULT ((0.00)) NOT NULL,
    [vac_saldo_final] decimal(5,2) DEFAULT ((0.00)) NOT NULL,
    [dias_falta] decimal(5,2) DEFAULT ((0)) NULL,
    [monto_falta] decimal(12,2) DEFAULT ((0)) NULL,
    [dias_permiso_sin_goce] decimal(5,2) DEFAULT ((0)) NULL,
    [monto_permiso_sin_goce] decimal(12,2) DEFAULT ((0)) NULL,
    [dias_septimo_dia] decimal(5,2) DEFAULT ((0)) NULL,
    [monto_septimo_dia] decimal(12,2) DEFAULT ((0)) NULL,
    [inatec_patronal] decimal(12,2) DEFAULT ((0)) NULL,
    CONSTRAINT [pk_detalle_nomina] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: detalle_pedidos_web
-- -------------------------------------------------------------
IF OBJECT_ID('detalle_pedidos_web', 'U') IS NULL
BEGIN
CREATE TABLE [detalle_pedidos_web] (
    [id] int IDENTITY(1,1) NOT NULL,
    [pedido_id] int NOT NULL,
    [producto_id] int NOT NULL,
    [cantidad] int NOT NULL,
    [precioUnitario] decimal(12,2) NOT NULL,
    [subtotal] decimal(12,2) NOT NULL,
    CONSTRAINT [pk_detalle_pedidos_web] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: detalle_ventas
-- -------------------------------------------------------------
IF OBJECT_ID('detalle_ventas', 'U') IS NULL
BEGIN
CREATE TABLE [detalle_ventas] (
    [id] int IDENTITY(1,1) NOT NULL,
    [venta_id] int NOT NULL,
    [producto_id] int NOT NULL,
    [cantidad] int NOT NULL,
    [precio_unitario] decimal(12,2) NOT NULL,
    [costo_historico] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [subtotal] decimal(12,2) NOT NULL,
    CONSTRAINT [pk_detalle_ventas] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: devoluciones
-- -------------------------------------------------------------
IF OBJECT_ID('devoluciones', 'U') IS NULL
BEGIN
CREATE TABLE [devoluciones] (
    [id] int IDENTITY(1,1) NOT NULL,
    [venta_id] int NOT NULL,
    [codigo_devolucion] varchar(50) NOT NULL,
    [fecha] datetime DEFAULT (getdate()) NULL,
    [motivo] varchar(255) NULL,
    [total_devuelto] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [usuario_id] int NULL,
    CONSTRAINT [pk_devoluciones] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: empleados
-- -------------------------------------------------------------
IF OBJECT_ID('empleados', 'U') IS NULL
BEGIN
CREATE TABLE [empleados] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nombre_completo] varchar(150) NOT NULL,
    [identificacion] varchar(30) NULL,
    [cargo] varchar(100) NULL,
    [salario_base] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [fecha_ingreso] date NULL,
    [activo] bit DEFAULT ((1)) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [num_inss] varchar(20) NULL,
    [telefono] varchar(25) NULL,
    [email] varchar(100) NULL,
    [dias_vacaciones_disponibles] decimal(5,1) DEFAULT ((0.0)) NOT NULL,
    [observaciones] varchar(500) NULL,
    [cargo_id] int NULL,
    [vacacionesDisponibles] decimal(5,2) DEFAULT ((0.00)) NULL,
    [fecha_nacimiento] date NULL,
    [direccion] varchar(255) NULL,
    [contacto_emergencia] varchar(150) NULL,
    [telefono_emergencia] varchar(30) NULL,
    [jornada_asignada] varchar(100) DEFAULT ('Diurna 8h (Lunes a Sábado)') NULL,
    [fecha_baja] date NULL,
    [motivo_baja] varchar(255) NULL,
    [inss_regimen] varchar(50) DEFAULT ('Integral') NULL,
    [inss_fecha_alta] date NULL,
    [inss_estado] varchar(30) DEFAULT ('Afiliado') NULL,
    [jornada_id] int NULL,
    CONSTRAINT [pk_empleados] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: expediente_empleado
-- -------------------------------------------------------------
IF OBJECT_ID('expediente_empleado', 'U') IS NULL
BEGIN
CREATE TABLE [expediente_empleado] (
    [id] int IDENTITY(1,1) NOT NULL,
    [empleado_id] int NOT NULL,
    [tipo_documento] varchar(100) NOT NULL,
    [nombre_archivo] varchar(255) NOT NULL,
    [fecha_registro] datetime DEFAULT (getdate()) NULL,
    [usuario_responsable] varchar(100) NULL,
    [observaciones] varchar(255) NULL,
    CONSTRAINT [pk_expediente_empleado] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: higiene_capacitaciones
-- -------------------------------------------------------------
IF OBJECT_ID('higiene_capacitaciones', 'U') IS NULL
BEGIN
CREATE TABLE [higiene_capacitaciones] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nombre_capacitacion] varchar(150) NOT NULL,
    [fecha] date NOT NULL,
    [duracion_horas] decimal(3,1) DEFAULT ((2.0)) NULL,
    [facilitador] varchar(150) NULL,
    [temas_tratados] varchar(MAX) NULL,
    [asistentes_conteo] int DEFAULT ((0)) NULL,
    [observaciones] varchar(255) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_higiene_capacitaciones] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: higiene_epp
-- -------------------------------------------------------------
IF OBJECT_ID('higiene_epp', 'U') IS NULL
BEGIN
CREATE TABLE [higiene_epp] (
    [area] nvarchar(50) NULL,
    [repone_a_id] int NULL,
    [motivo_reposicion] nvarchar(255) NULL,
    [id] int IDENTITY(1,1) NOT NULL,
    [empleado_id] int NOT NULL,
    [tipo_equipo] varchar(100) NOT NULL,
    [fecha_entrega] date DEFAULT (getdate()) NOT NULL,
    [cantidad] int DEFAULT ((1)) NULL,
    [estado_equipo] varchar(50) DEFAULT ('Nuevo / Óptimo') NULL,
    [fecha_reposicion_sugerida] date NULL,
    [entregado_por] varchar(100) NULL,
    [observaciones] varchar(255) NULL,
    CONSTRAINT [pk_higiene_epp] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: higiene_incidentes
-- -------------------------------------------------------------
IF OBJECT_ID('higiene_incidentes', 'U') IS NULL
BEGIN
CREATE TABLE [higiene_incidentes] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo_incidente] varchar(30) NOT NULL,
    [fecha] datetime DEFAULT (getdate()) NOT NULL,
    [area] varchar(50) NOT NULL,
    [empleado_id] int NULL,
    [tipo_suceso] varchar(50) DEFAULT ('Incidente Menor') NOT NULL,
    [descripcion] varchar(MAX) NOT NULL,
    [posibles_causas] varchar(MAX) NULL,
    [medidas_correctivas] varchar(MAX) NULL,
    [dias_incapacidad] int DEFAULT ((0)) NULL,
    [estado_seguimiento] varchar(30) DEFAULT ('Cerrado') NULL,
    [registrado_por] varchar(100) NULL,
    CONSTRAINT [pk_higiene_incidentes] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: higiene_inspecciones
-- -------------------------------------------------------------
IF OBJECT_ID('higiene_inspecciones', 'U') IS NULL
BEGIN
CREATE TABLE [higiene_inspecciones] (
    [id] int IDENTITY(1,1) NOT NULL,
    [fecha_inspeccion] datetime DEFAULT (getdate()) NOT NULL,
    [inspector] varchar(100) NOT NULL,
    [pasillos_despejados] bit DEFAULT ((1)) NULL,
    [estanterias_seguras] bit DEFAULT ((1)) NULL,
    [repuestos_ordenados] bit DEFAULT ((1)) NULL,
    [extintores_adecuados] bit DEFAULT ((1)) NULL,
    [salidas_emergencia_libres] bit DEFAULT ((1)) NULL,
    [area_caja_segura] bit DEFAULT ((1)) NULL,
    [puntos_aprobados] int DEFAULT ((6)) NULL,
    [total_puntos] int DEFAULT ((6)) NULL,
    [porcentaje_cumplimiento] decimal(5,2) DEFAULT ((100.00)) NULL,
    [observaciones] varchar(MAX) NULL,
    [acciones_correctivas] varchar(MAX) NULL,
    [estado] varchar(30) DEFAULT ('Conforme') NULL,
    CONSTRAINT [pk_higiene_inspecciones] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: higiene_riesgos
-- -------------------------------------------------------------
IF OBJECT_ID('higiene_riesgos', 'U') IS NULL
BEGIN
CREATE TABLE [higiene_riesgos] (
    [fecha_revision] date NULL,
    [id] int IDENTITY(1,1) NOT NULL,
    [area] varchar(50) NOT NULL,
    [tipo_riesgo] varchar(100) NOT NULL,
    [descripcion] varchar(MAX) NOT NULL,
    [nivel_riesgo] varchar(20) DEFAULT ('Medio') NOT NULL,
    [medidas_preventivas] varchar(MAX) NOT NULL,
    [responsable_seguimiento] varchar(100) NULL,
    [estado] varchar(30) DEFAULT ('Activo') NULL,
    [fecha_registro] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_higiene_riesgos] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: historial_laboral
-- -------------------------------------------------------------
IF OBJECT_ID('historial_laboral', 'U') IS NULL
BEGIN
CREATE TABLE [historial_laboral] (
    [id] int IDENTITY(1,1) NOT NULL,
    [empleado_id] int NOT NULL,
    [fecha_vigencia] date DEFAULT (getdate()) NOT NULL,
    [tipo_modificacion] varchar(50) NOT NULL,
    [campo_afectado] varchar(50) NOT NULL,
    [valor_anterior] varchar(255) NULL,
    [valor_nuevo] varchar(255) NOT NULL,
    [motivo] varchar(MAX) NULL,
    [usuario_responsable] varchar(100) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_historial_laboral] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: horas_extras
-- -------------------------------------------------------------
IF OBJECT_ID('horas_extras', 'U') IS NULL
BEGIN
CREATE TABLE [horas_extras] (
    [id] int IDENTITY(1,1) NOT NULL,
    [empleado_id] int NOT NULL,
    [fecha] date NOT NULL,
    [cantidad_horas] decimal(4,2) NOT NULL,
    [motivo] varchar(255) NULL,
    [valor_hora_ordinaria] decimal(12,2) NOT NULL,
    [recargo_porcentaje] decimal(5,2) DEFAULT ((100.00)) NULL,
    [monto_total] decimal(12,2) NOT NULL,
    [estado] varchar(30) DEFAULT ('Aprobada') NULL,
    [autorizado_por] varchar(100) NULL,
    [nomina_id] int NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_horas_extras] PRIMARY KEY ([id]),
    CONSTRAINT [fk_horasextras_nomina] FOREIGN KEY ([nomina_id]) REFERENCES [nomina]([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: jornadas_laborales
-- -------------------------------------------------------------
IF OBJECT_ID('jornadas_laborales', 'U') IS NULL
BEGIN
CREATE TABLE [jornadas_laborales] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nombre] varchar(100) NOT NULL,
    [hora_entrada] varchar(10) NOT NULL,
    [hora_salida] varchar(10) NOT NULL,
    [minutos_descanso] int DEFAULT ((60)) NULL,
    [dias_laborables] varchar(100) DEFAULT ('Lunes a Sábado') NULL,
    [dia_descanso] varchar(50) DEFAULT ('Domingo') NULL,
    [horas_semanales] decimal(5,2) DEFAULT ((48.0)) NULL,
    [activo] bit DEFAULT ((1)) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_jornadas_laborales] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: liquidaciones_laborales
-- -------------------------------------------------------------
IF OBJECT_ID('liquidaciones_laborales', 'U') IS NULL
BEGIN
CREATE TABLE [liquidaciones_laborales] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo] varchar(50) NOT NULL,
    [empleado_id] int NOT NULL,
    [fecha_ingreso] date NOT NULL,
    [fecha_salida] date NOT NULL,
    [motivo_salida] varchar(100) NOT NULL,
    [salario_base] decimal(12,2) NOT NULL,
    [antiguedad_anios] int DEFAULT ((0)) NULL,
    [antiguedad_meses] int DEFAULT ((0)) NULL,
    [antiguedad_dias] int DEFAULT ((0)) NULL,
    [monto_dias_pendientes] decimal(12,2) DEFAULT ((0.00)) NULL,
    [dias_vacaciones_pendientes] decimal(6,2) DEFAULT ((0.00)) NULL,
    [monto_vacaciones] decimal(12,2) DEFAULT ((0.00)) NULL,
    [monto_aguinaldo_proporcional] decimal(12,2) DEFAULT ((0.00)) NULL,
    [monto_indemnizacion_antiguedad] decimal(12,2) DEFAULT ((0.00)) NULL,
    [total_percepciones] decimal(12,2) NOT NULL,
    [deducciones_totales] decimal(12,2) DEFAULT ((0.00)) NULL,
    [neto_a_pagar] decimal(12,2) NOT NULL,
    [estado] varchar(30) DEFAULT ('Borrador') NULL,
    [elaborado_por] varchar(100) NULL,
    [fecha_elaboracion] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_liquidaciones_laborales] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: movimientos_contables
-- -------------------------------------------------------------
IF OBJECT_ID('movimientos_contables', 'U') IS NULL
BEGIN
CREATE TABLE [movimientos_contables] (
    [id] int IDENTITY(1,1) NOT NULL,
    [asiento_id] int NOT NULL,
    [cuenta_id] int NOT NULL,
    [debe] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [haber] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    CONSTRAINT [pk_movimientos_contables] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: movimientos_inventario
-- -------------------------------------------------------------
IF OBJECT_ID('movimientos_inventario', 'U') IS NULL
BEGIN
CREATE TABLE [movimientos_inventario] (
    [id] int IDENTITY(1,1) NOT NULL,
    [fecha] datetime DEFAULT (getdate()) NULL,
    [producto_id] int NOT NULL,
    [tipo_movimiento] varchar(50) NOT NULL,
    [cantidad] int NOT NULL,
    [stock_anterior] int DEFAULT ((0)) NOT NULL,
    [stock_posterior] int DEFAULT ((0)) NOT NULL,
    [referencia_origen] varchar(100) NULL,
    [motivo] varchar(255) NOT NULL,
    [usuario_id] int NOT NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_movimientos_inventario] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: movimientos_laborales
-- -------------------------------------------------------------
IF OBJECT_ID('movimientos_laborales', 'U') IS NULL
BEGIN
CREATE TABLE [movimientos_laborales] (
    [id] int IDENTITY(1,1) NOT NULL,
    [empleado_id] int NOT NULL,
    [tipo] varchar(30) NOT NULL,
    [fecha_inicio] date NOT NULL,
    [fecha_fin] date NOT NULL,
    [dias_tomados] decimal(4,1) NOT NULL,
    [observacion] varchar(255) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [afecta_septimo_dia] bit DEFAULT ((0)) NULL,
    [estado] varchar(30) DEFAULT ('Aprobada') NULL,
    [aprobado_por] varchar(100) NULL,
    [documento_respaldo] varchar(255) NULL,
    [clasificacion] varchar(50) DEFAULT ('Injustificada') NULL,
    CONSTRAINT [pk_movimientos_laborales] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: nomina
-- -------------------------------------------------------------
IF OBJECT_ID('nomina', 'U') IS NULL
BEGIN
CREATE TABLE [nomina] (
    [id] int IDENTITY(1,1) NOT NULL,
    [periodo_mes] int NOT NULL,
    [periodo_anio] int NOT NULL,
    [fecha_generacion] datetime DEFAULT (getdate()) NULL,
    [total_ingresos] decimal(12,2) DEFAULT ((0.00)) NULL,
    [total_deducciones] decimal(12,2) DEFAULT ((0.00)) NULL,
    [total_neto] decimal(12,2) DEFAULT ((0.00)) NULL,
    [inss_patronal_total] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [provision_vac_total] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [provision_agui_total] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [estado] varchar(20) DEFAULT ('CERRADA') NOT NULL,
    [inatec_patronal_total] decimal(12,2) DEFAULT ((0)) NULL,
    CONSTRAINT [pk_nomina] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: pagos
-- -------------------------------------------------------------
IF OBJECT_ID('pagos', 'U') IS NULL
BEGIN
CREATE TABLE [pagos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [venta_id] int NULL,
    [metodo] varchar(50) NOT NULL,
    [monto] decimal(12,2) NOT NULL,
    [referencia] varchar(100) NULL,
    [fecha] datetime DEFAULT (getdate()) NULL,
    [pedido_web_id] int NULL,
    [origen] varchar(20) DEFAULT ('VENTA_POS') NOT NULL,
    CONSTRAINT [pk_pagos] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: pagos_nomina
-- -------------------------------------------------------------
IF OBJECT_ID('pagos_nomina', 'U') IS NULL
BEGIN
CREATE TABLE [pagos_nomina] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nomina_id] int NULL,
    [empleado_id] int NOT NULL,
    [monto_pagado] decimal(12,2) NOT NULL,
    [fecha_pago] datetime DEFAULT (getdate()) NULL,
    [metodo_pago] varchar(50) DEFAULT ('Transferencia Bancaria') NULL,
    [numero_referencia] varchar(100) NULL,
    [comprobante] varchar(255) NULL,
    [estado] varchar(30) DEFAULT ('Confirmado') NULL,
    [observaciones] varchar(255) NULL,
    [registrado_por] varchar(100) DEFAULT ('Administrador') NULL,
    CONSTRAINT [pk_pagos_nomina] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: parametros_laborales
-- -------------------------------------------------------------
IF OBJECT_ID('parametros_laborales', 'U') IS NULL
BEGIN
CREATE TABLE [parametros_laborales] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo] varchar(50) NOT NULL,
    [nombre] varchar(100) NOT NULL,
    [valor] decimal(10,4) NOT NULL,
    [unidad] varchar(20) DEFAULT ('%') NULL,
    [descripcion] varchar(255) NULL,
    [referencia_legal] varchar(100) NULL,
    [fecha_vigencia] date DEFAULT (getdate()) NULL,
    [usuario_modificacion] varchar(100) DEFAULT ('Administrador') NULL,
    CONSTRAINT [pk_parametros_laborales] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: pedidos_web
-- -------------------------------------------------------------
IF OBJECT_ID('pedidos_web', 'U') IS NULL
BEGIN
CREATE TABLE [pedidos_web] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo] varchar(50) NOT NULL,
    [cliente_id] int NULL,
    [fecha] datetime DEFAULT (getdate()) NULL,
    [subtotal] decimal(12,2) NOT NULL,
    [total] decimal(12,2) NOT NULL,
    [formaEntrega] varchar(50) NULL,
    [metodo] varchar(50) NULL,
    [estado] varchar(30) DEFAULT ('Pendiente') NULL,
    [nombre_cliente] varchar(150) NULL,
    [telefono] varchar(30) NULL,
    [email] varchar(100) NULL,
    [direccion_entrega] varchar(MAX) NULL,
    CONSTRAINT [pk_pedidos_web] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: permisos
-- -------------------------------------------------------------
IF OBJECT_ID('permisos', 'U') IS NULL
BEGIN
CREATE TABLE [permisos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [rol_id] int NOT NULL,
    [nombre] varchar(100) NOT NULL,
    [descripcion] varchar(255) NULL,
    CONSTRAINT [pk_permisos] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: productos
-- -------------------------------------------------------------
IF OBJECT_ID('productos', 'U') IS NULL
BEGIN
CREATE TABLE [productos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo_sku] varchar(50) NOT NULL,
    [codigo_barras] varchar(50) NULL,
    [categoria_id] int NOT NULL,
    [nombre] varchar(200) NOT NULL,
    [descripcion] varchar(MAX) NULL,
    [marca] varchar(100) NULL,
    [modelo_compatible] varchar(255) NULL,
    [ubicacion_estante] varchar(50) NULL,
    [costo] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [precio_venta] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [stock_actual] int DEFAULT ((0)) NOT NULL,
    [stock_minimo] int DEFAULT ((5)) NOT NULL,
    [activo] bit DEFAULT ((1)) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [updated_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_productos] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: proveedores
-- -------------------------------------------------------------
IF OBJECT_ID('proveedores', 'U') IS NULL
BEGIN
CREATE TABLE [proveedores] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nombre_empresa] varchar(150) NOT NULL,
    [contacto_nombre] varchar(100) NULL,
    [identificacion_fiscal] varchar(30) NULL,
    [telefono] varchar(25) NOT NULL,
    [email] varchar(100) NULL,
    [direccion] varchar(MAX) NULL,
    [activo] bit DEFAULT ((1)) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [updated_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_proveedores] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: recepciones_compra
-- -------------------------------------------------------------
IF OBJECT_ID('recepciones_compra', 'U') IS NULL
BEGIN
CREATE TABLE [recepciones_compra] (
    [id] int IDENTITY(1,1) NOT NULL,
    [compra_id] int NOT NULL,
    [fechaRecepcion] datetime DEFAULT (getdate()) NULL,
    [estado] varchar(30) DEFAULT ('Recibido') NULL,
    CONSTRAINT [pk_recepciones_compra] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: roles
-- -------------------------------------------------------------
IF OBJECT_ID('roles', 'U') IS NULL
BEGIN
CREATE TABLE [roles] (
    [id] int IDENTITY(1,1) NOT NULL,
    [nombre] varchar(50) NOT NULL,
    [descripcion] varchar(255) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_roles] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: sesiones
-- -------------------------------------------------------------
IF OBJECT_ID('sesiones', 'U') IS NULL
BEGIN
CREATE TABLE [sesiones] (
    [id] int IDENTITY(1,1) NOT NULL,
    [usuario_id] int NOT NULL,
    [fechaInicio] datetime DEFAULT (getdate()) NULL,
    [estado] varchar(20) DEFAULT ('Activa') NULL,
    [ip] varchar(50) NULL,
    CONSTRAINT [pk_sesiones] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: sesiones_caja
-- -------------------------------------------------------------
IF OBJECT_ID('sesiones_caja', 'U') IS NULL
BEGIN
CREATE TABLE [sesiones_caja] (
    [id] int IDENTITY(1,1) NOT NULL,
    [usuario_id] int NOT NULL,
    [fecha_apertura] datetime DEFAULT (getdate()) NOT NULL,
    [monto_inicial] decimal(12,2) NOT NULL,
    [fecha_cierre] datetime NULL,
    [monto_final_esperado] decimal(12,2) NULL,
    [monto_final_real] decimal(12,2) NULL,
    [diferencia] decimal(12,2) NULL,
    [estado] varchar(20) DEFAULT ('Abierta') NOT NULL,
    [observaciones] varchar(MAX) NULL,
    CONSTRAINT [pk_sesiones_caja] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: solicitudes_empleo
-- -------------------------------------------------------------
IF OBJECT_ID('solicitudes_empleo', 'U') IS NULL
BEGIN
CREATE TABLE [solicitudes_empleo] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo_solicitud] varchar(30) NOT NULL,
    [nombres_apellidos] varchar(150) NOT NULL,
    [identificacion] varchar(30) NULL,
    [direccion] varchar(255) NULL,
    [telefono] varchar(30) NOT NULL,
    [email] varchar(100) NULL,
    [puesto_solicitado] varchar(100) NOT NULL,
    [formacion_academica] varchar(255) NULL,
    [experiencia_laboral] varchar(MAX) NULL,
    [referencias_laborales] varchar(MAX) NULL,
    [disponibilidad] varchar(50) DEFAULT ('Inmediata') NULL,
    [salario_pretendido] decimal(12,2) DEFAULT ((0.00)) NULL,
    [curriculum_vitae] varchar(255) NULL,
    [estado] varchar(30) DEFAULT ('Recibida') NULL,
    [observaciones] varchar(MAX) NULL,
    [fecha_registro] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_solicitudes_empleo] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: usuarios
-- -------------------------------------------------------------
IF OBJECT_ID('usuarios', 'U') IS NULL
BEGIN
CREATE TABLE [usuarios] (
    [id] int IDENTITY(1,1) NOT NULL,
    [rol_id] int NOT NULL,
    [username] varchar(50) NOT NULL,
    [password_hash] varchar(255) NOT NULL,
    [nombre_completo] varchar(150) NOT NULL,
    [email] varchar(100) NULL,
    [telefono] varchar(25) NULL,
    [activo] bit DEFAULT ((1)) NULL,
    [ultimo_acceso] datetime NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [updated_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_usuarios] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: vacaciones
-- -------------------------------------------------------------
IF OBJECT_ID('vacaciones', 'U') IS NULL
BEGIN
CREATE TABLE [vacaciones] (
    [id] int IDENTITY(1,1) NOT NULL,
    [empleado_id] int NOT NULL,
    [fechaInicio] date NOT NULL,
    [fechaFin] date NOT NULL,
    [dias] int NOT NULL,
    [estado] varchar(30) DEFAULT ('Aprobada') NULL,
    CONSTRAINT [pk_vacaciones] PRIMARY KEY ([id])
);
END
GO

-- -------------------------------------------------------------
-- Tabla: ventas
-- -------------------------------------------------------------
IF OBJECT_ID('ventas', 'U') IS NULL
BEGIN
CREATE TABLE [ventas] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo_venta] varchar(30) NOT NULL,
    [cliente_id] int NULL,
    [usuario_id] int NOT NULL,
    [fecha_venta] date NOT NULL,
    [subtotal] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [descuento] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [total] decimal(12,2) DEFAULT ((0.00)) NOT NULL,
    [forma_pago] varchar(30) DEFAULT ('Efectivo') NULL,
    [estado] varchar(30) DEFAULT ('Completada') NULL,
    [notas] varchar(MAX) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [sesion_caja_id] int NULL,
    [nombre_cliente_invitado] varchar(150) NULL,
    CONSTRAINT [pk_ventas] PRIMARY KEY ([id])
);
END
GO

-- ==============================================================
-- RELACIONES Y CLAVES FORÁNEAS
-- ==============================================================

IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_ajustes_productos')
    ALTER TABLE [ajustes_inventario] ADD CONSTRAINT [fk_ajustes_productos] FOREIGN KEY ([producto_id]) REFERENCES [productos]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_asistencia_empleados')
    ALTER TABLE [asistencia_laboral] ADD CONSTRAINT [fk_asistencia_empleados] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_carritos_clientes')
    ALTER TABLE [carritos] ADD CONSTRAINT [fk_carritos_clientes] FOREIGN KEY ([cliente_id]) REFERENCES [clientes]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_colilla_detnomina')
    ALTER TABLE [colilla_pago] ADD CONSTRAINT [fk_colilla_detnomina] FOREIGN KEY ([detalle_nomina_id]) REFERENCES [detalle_nomina]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_compras_proveedores')
    ALTER TABLE [compras] ADD CONSTRAINT [fk_compras_proveedores] FOREIGN KEY ([proveedor_id]) REFERENCES [proveedores]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_compras_usuarios')
    ALTER TABLE [compras] ADD CONSTRAINT [fk_compras_usuarios] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_comprobantes_pedidos_web')
    ALTER TABLE [comprobantes] ADD CONSTRAINT [fk_comprobantes_pedidos_web] FOREIGN KEY ([pedido_web_id]) REFERENCES [pedidos_web]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_comprobantes_ventas')
    ALTER TABLE [comprobantes] ADD CONSTRAINT [fk_comprobantes_ventas] FOREIGN KEY ([venta_id]) REFERENCES [ventas]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_contratos_empleados')
    ALTER TABLE [contratos_laborales] ADD CONSTRAINT [fk_contratos_empleados] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detcarrito_carritos')
    ALTER TABLE [detalle_carritos] ADD CONSTRAINT [fk_detcarrito_carritos] FOREIGN KEY ([carrito_id]) REFERENCES [carritos]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detcarrito_productos')
    ALTER TABLE [detalle_carritos] ADD CONSTRAINT [fk_detcarrito_productos] FOREIGN KEY ([producto_id]) REFERENCES [productos]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detcompras_compras')
    ALTER TABLE [detalle_compras] ADD CONSTRAINT [fk_detcompras_compras] FOREIGN KEY ([compra_id]) REFERENCES [compras]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detcompras_productos')
    ALTER TABLE [detalle_compras] ADD CONSTRAINT [fk_detcompras_productos] FOREIGN KEY ([producto_id]) REFERENCES [productos]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detdevolucion_devolucion')
    ALTER TABLE [detalle_devoluciones] ADD CONSTRAINT [fk_detdevolucion_devolucion] FOREIGN KEY ([devolucion_id]) REFERENCES [devoluciones]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detdevolucion_producto')
    ALTER TABLE [detalle_devoluciones] ADD CONSTRAINT [fk_detdevolucion_producto] FOREIGN KEY ([producto_id]) REFERENCES [productos]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detnomina_empleado')
    ALTER TABLE [detalle_nomina] ADD CONSTRAINT [fk_detnomina_empleado] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detnomina_nomina')
    ALTER TABLE [detalle_nomina] ADD CONSTRAINT [fk_detnomina_nomina] FOREIGN KEY ([nomina_id]) REFERENCES [nomina]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detpedido_pedidos')
    ALTER TABLE [detalle_pedidos_web] ADD CONSTRAINT [fk_detpedido_pedidos] FOREIGN KEY ([pedido_id]) REFERENCES [pedidos_web]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detpedido_productos')
    ALTER TABLE [detalle_pedidos_web] ADD CONSTRAINT [fk_detpedido_productos] FOREIGN KEY ([producto_id]) REFERENCES [productos]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detventas_productos')
    ALTER TABLE [detalle_ventas] ADD CONSTRAINT [fk_detventas_productos] FOREIGN KEY ([producto_id]) REFERENCES [productos]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_detventas_ventas')
    ALTER TABLE [detalle_ventas] ADD CONSTRAINT [fk_detventas_ventas] FOREIGN KEY ([venta_id]) REFERENCES [ventas]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_devoluciones_usuarios')
    ALTER TABLE [devoluciones] ADD CONSTRAINT [fk_devoluciones_usuarios] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_devoluciones_ventas')
    ALTER TABLE [devoluciones] ADD CONSTRAINT [fk_devoluciones_ventas] FOREIGN KEY ([venta_id]) REFERENCES [ventas]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_empleados_cargos')
    ALTER TABLE [empleados] ADD CONSTRAINT [fk_empleados_cargos] FOREIGN KEY ([cargo_id]) REFERENCES [cargos]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_epp_empleados')
    ALTER TABLE [higiene_epp] ADD CONSTRAINT [fk_epp_empleados] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_expediente_empleados')
    ALTER TABLE [expediente_empleado] ADD CONSTRAINT [fk_expediente_empleados] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_historial_empleados')
    ALTER TABLE [historial_laboral] ADD CONSTRAINT [fk_historial_empleados] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_horasextras_empleados')
    ALTER TABLE [horas_extras] ADD CONSTRAINT [fk_horasextras_empleados] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_incidentes_empleados')
    ALTER TABLE [higiene_incidentes] ADD CONSTRAINT [fk_incidentes_empleados] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_liquidaciones_empleados')
    ALTER TABLE [liquidaciones_laborales] ADD CONSTRAINT [fk_liquidaciones_empleados] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_mov_productos')
    ALTER TABLE [movimientos_inventario] ADD CONSTRAINT [fk_mov_productos] FOREIGN KEY ([producto_id]) REFERENCES [productos]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_mov_usuarios')
    ALTER TABLE [movimientos_inventario] ADD CONSTRAINT [fk_mov_usuarios] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_movlab_empleado')
    ALTER TABLE [movimientos_laborales] ADD CONSTRAINT [fk_movlab_empleado] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_pagos_pedidos_web')
    ALTER TABLE [pagos] ADD CONSTRAINT [fk_pagos_pedidos_web] FOREIGN KEY ([pedido_web_id]) REFERENCES [pedidos_web]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_pagos_ventas')
    ALTER TABLE [pagos] ADD CONSTRAINT [fk_pagos_ventas] FOREIGN KEY ([venta_id]) REFERENCES [ventas]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_pedidos_clientes')
    ALTER TABLE [pedidos_web] ADD CONSTRAINT [fk_pedidos_clientes] FOREIGN KEY ([cliente_id]) REFERENCES [clientes]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_permisos_roles')
    ALTER TABLE [permisos] ADD CONSTRAINT [fk_permisos_roles] FOREIGN KEY ([rol_id]) REFERENCES [roles]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_productos_categorias')
    ALTER TABLE [productos] ADD CONSTRAINT [fk_productos_categorias] FOREIGN KEY ([categoria_id]) REFERENCES [categorias]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_recepcion_compras')
    ALTER TABLE [recepciones_compra] ADD CONSTRAINT [fk_recepcion_compras] FOREIGN KEY ([compra_id]) REFERENCES [compras]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_sesiones_caja_usuarios')
    ALTER TABLE [sesiones_caja] ADD CONSTRAINT [fk_sesiones_caja_usuarios] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_sesiones_usuarios')
    ALTER TABLE [sesiones] ADD CONSTRAINT [fk_sesiones_usuarios] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_usuarios_roles')
    ALTER TABLE [usuarios] ADD CONSTRAINT [fk_usuarios_roles] FOREIGN KEY ([rol_id]) REFERENCES [roles]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_vacaciones_empleados')
    ALTER TABLE [vacaciones] ADD CONSTRAINT [fk_vacaciones_empleados] FOREIGN KEY ([empleado_id]) REFERENCES [empleados]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_ventas_clientes')
    ALTER TABLE [ventas] ADD CONSTRAINT [fk_ventas_clientes] FOREIGN KEY ([cliente_id]) REFERENCES [clientes]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_ventas_sesion')
    ALTER TABLE [ventas] ADD CONSTRAINT [fk_ventas_sesion] FOREIGN KEY ([sesion_caja_id]) REFERENCES [sesiones_caja]([id]);
GO
IF NOT EXISTS (SELECT 1 FROM sys.foreign_keys WHERE name = 'fk_ventas_usuarios')
    ALTER TABLE [ventas] ADD CONSTRAINT [fk_ventas_usuarios] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id]);
GO

-- ==============================================================
-- VISTAS DEL SISTEMA
-- ==============================================================

-- Vista: vista_balance_inventario
CREATE OR ALTER VIEW vista_balance_inventario AS
SELECT 
    c.nombre AS categoria,
    COUNT(p.id) AS total_productos,
    SUM(p.stock_actual) AS total_stock,
    SUM(p.stock_actual * p.costo) AS valor_costo,
    SUM(p.stock_actual * p.precio_venta) AS valor_venta
FROM productos p
LEFT JOIN categorias c ON p.categoria_id = c.id
WHERE p.activo = 1
GROUP BY c.nombre;
GO

-- Vista: vista_kardex_completo
CREATE OR ALTER VIEW vista_kardex_completo AS
SELECT 
    mi.id, mi.producto_id, p.codigo_sku AS codigo, p.nombre AS producto_nombre,
    mi.tipo_movimiento AS tipo, mi.cantidad, mi.stock_anterior, 
    mi.stock_posterior AS stock_nuevo,
    mi.referencia_origen AS referencia, mi.motivo AS observacion, mi.created_at
FROM movimientos_inventario mi
INNER JOIN productos p ON mi.producto_id = p.id;
GO

-- Vista: vista_resumen_rrhh
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
GO

-- Vista: vista_stock_bajo
CREATE OR ALTER VIEW vista_stock_bajo AS
SELECT id, codigo_sku AS codigo, nombre, stock_actual AS stock, 
       stock_minimo, categoria_id, precio_venta
FROM productos
WHERE stock_actual <= stock_minimo AND activo = 1;
GO

-- Vista: vista_top_productos_vendidos
CREATE OR ALTER VIEW vista_top_productos_vendidos AS
SELECT TOP 20
    p.id, p.codigo_sku AS codigo, p.nombre, 
    SUM(dv.cantidad) AS total_vendido,
    SUM(dv.subtotal) AS total_ingreso
FROM detalle_ventas dv
INNER JOIN productos p ON dv.producto_id = p.id
INNER JOIN ventas v ON dv.venta_id = v.id
WHERE v.estado = 'Completada'
GROUP BY p.id, p.codigo_sku, p.nombre
ORDER BY total_vendido DESC;
GO


-- ==============================================================
-- INSERCIÓN DE DATOS INICIALES Y CATÁLOGOS
-- ==============================================================

EXEC sp_MSforeachtable 'ALTER TABLE ? NOCHECK CONSTRAINT ALL';
GO

-- Datos para [asientos_contables] (10 registros)
SET IDENTITY_INSERT [asientos_contables] ON;
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (1, '2026-08-01', 'Apertura de saldos iniciales de balance', 'CONTABILIDAD', NULL, 1, '2026-09-17 16:22:41.553000');
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (2, '2026-08-15', 'Registro de ingresos por ventas y servicios de la quincena', 'VENTAS', NULL, 1, '2026-09-17 16:22:41.570000');
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (3, '2026-08-31', 'Provisión de gastos operativos, depreciación y cierres', 'CONTABILIDAD', NULL, 1, '2026-09-17 16:22:41.573000');
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (4, '2026-10-04', 'Registro de nÃ³mina mes 03/2026', 'RRHH', 8, 1, '2026-10-04 21:46:02.410000');
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (5, '2026-10-06', 'Registro de nÃ³mina mes 09/2026 (Complemento)', 'RRHH', 3, 1, '2026-10-06 16:20:19.120000');
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (6, '2026-10-06', 'Registro de nómina mes 09/2026 (Complemento)', 'RRHH', 3, 1, '2026-10-06 17:04:35.280000');
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (7, '2026-10-06', 'Registro de nómina mes 01/2026', 'RRHH', 9, 1, '2026-10-06 17:05:13.917000');
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (8, '2026-10-06', 'Registro de nómina mes 08/2026 (Complemento)', 'RRHH', 2, 1, '2026-10-06 18:54:23.720000');
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (9, '2026-10-06', 'Registro de nómina mes 07/2026', 'RRHH', 10, 1, '2026-10-06 20:30:38.920000');
INSERT INTO [asientos_contables] ([id], [fecha], [concepto], [modulo_origen], [referencia_id], [usuario_id], [created_at]) VALUES (10, '2026-10-06', 'Registro de nómina mes 01/2026', 'RRHH', 11, 1, '2026-10-06 20:31:06.773000');
SET IDENTITY_INSERT [asientos_contables] OFF;
GO

-- Datos para [calendario_obligaciones] (4 registros)
SET IDENTITY_INSERT [calendario_obligaciones] ON;
INSERT INTO [calendario_obligaciones] ([id], [nombre_obligacion], [institucion], [periodo], [fecha_vencimiento], [responsable], [estado], [fecha_cumplimiento], [comprobante_adjunto], [observaciones]) VALUES (1, 'Declaración y Pago de Retenciones en la Fuente (IR)', 'DGI', 'Mensual', '2026-11-05', 'Contador General', 'Pendiente', NULL, NULL, NULL);
INSERT INTO [calendario_obligaciones] ([id], [nombre_obligacion], [institucion], [periodo], [fecha_vencimiento], [responsable], [estado], [fecha_cumplimiento], [comprobante_adjunto], [observaciones]) VALUES (2, 'Pago de Factura Mensual de Cotizaciones Patronal y Laboral', 'INSS', 'Mensual', '2026-11-15', 'Responsable de RRHH', 'Pendiente', NULL, NULL, NULL);
INSERT INTO [calendario_obligaciones] ([id], [nombre_obligacion], [institucion], [periodo], [fecha_vencimiento], [responsable], [estado], [fecha_cumplimiento], [comprobante_adjunto], [observaciones]) VALUES (3, 'Aporte del 2% INATEC por Capacitación Técnica', 'INSS / INATEC', 'Mensual', '2026-11-15', 'Contador General', 'Pendiente', NULL, NULL, NULL);
INSERT INTO [calendario_obligaciones] ([id], [nombre_obligacion], [institucion], [periodo], [fecha_vencimiento], [responsable], [estado], [fecha_cumplimiento], [comprobante_adjunto], [observaciones]) VALUES (4, 'Inspección Periódica Trimestral de Seguridad y Extintores', 'MITRAB / Interno', 'Trimestral', '2026-11-30', 'Responsable de RRHH', 'Pendiente', NULL, NULL, NULL);
SET IDENTITY_INSERT [calendario_obligaciones] OFF;
GO

-- Datos para [cargos] (5 registros)
SET IDENTITY_INSERT [cargos] ON;
INSERT INTO [cargos] ([id], [nombre_cargo], [descripcion], [salario_base_sugerido], [activo], [created_at], [area], [responsabilidades]) VALUES (1, 'Vendedor de Mostrador', 'Atención y ventas en sala', '12000.00', True, '2026-10-04 21:39:36.027000', 'Ventas', NULL);
INSERT INTO [cargos] ([id], [nombre_cargo], [descripcion], [salario_base_sugerido], [activo], [created_at], [area], [responsabilidades]) VALUES (2, 'Cajero / Facturación', 'Gestión de caja y cobros', '11500.00', True, '2026-10-04 21:39:36.027000', 'Administración', NULL);
INSERT INTO [cargos] ([id], [nombre_cargo], [descripcion], [salario_base_sugerido], [activo], [created_at], [area], [responsabilidades]) VALUES (3, 'Encargado de Inventario / Bodega', 'Recepción y despacho de repuestos', '13000.00', True, '2026-10-04 21:39:36.027000', 'Almacén', NULL);
INSERT INTO [cargos] ([id], [nombre_cargo], [descripcion], [salario_base_sugerido], [activo], [created_at], [area], [responsabilidades]) VALUES (4, 'Mecánico / Técnico', 'Servicios mecánicos y ensamblaje', '14000.00', True, '2026-10-04 21:39:36.027000', 'Administración', NULL);
INSERT INTO [cargos] ([id], [nombre_cargo], [descripcion], [salario_base_sugerido], [activo], [created_at], [area], [responsabilidades]) VALUES (5, 'Administrador General', 'Gestión administrativa y operativa', '18000.00', True, '2026-10-04 21:39:36.027000', 'Administración', NULL);
SET IDENTITY_INSERT [cargos] OFF;
GO

-- Datos para [categorias] (9 registros)
SET IDENTITY_INSERT [categorias] ON;
INSERT INTO [categorias] ([id], [nombre], [descripcion], [created_at]) VALUES (1, 'Motor y Partes Internas', 'Cilindros completos, pistones, anillos de pistón, bielas, válvulas, árbol de levas, balancines, empaques de motor, cadenas de tiempo y bombas de lubricación.', '2026-09-17 16:22:40.417000');
INSERT INTO [categorias] ([id], [nombre], [descripcion], [created_at]) VALUES (2, 'Sistema Eléctrico y Encendido', 'Cerebros CDI, bobinas de alta/motor, motores de arranque, carbones, bombillos, relays, fusibles, rectificadores, ignición, mandos de luces/start y sistema eléctrico.', '2026-09-17 16:22:40.427000');
INSERT INTO [categorias] ([id], [nombre], [descripcion], [created_at]) VALUES (3, 'Transmisión y Embrague', 'Cajas de cambios, kit de sprockets (catalinas y piñones), discos/fricciones de clutch, canastas de clutch, cadenas de tracción y bandas de tracción (scooters).', '2026-09-17 16:22:40.430000');
INSERT INTO [categorias] ([id], [nombre], [descripcion], [created_at]) VALUES (4, 'Sistema de Frenos', 'Bombas de freno (delanteras y traseras), mangueras de freno y varillas de freno.', '2026-09-17 16:22:40.430000');
INSERT INTO [categorias] ([id], [nombre], [descripcion], [created_at]) VALUES (5, 'Suspensión y Dirección', 'Amortiguadores, cunas de poste, bushing de tijera y retenedores de barras.', '2026-09-17 16:22:40.433000');
INSERT INTO [categorias] ([id], [nombre], [descripcion], [created_at]) VALUES (6, 'Carburación y Combustible', 'Carburadores, llaves de combustible y tapones de tanque.', '2026-09-17 16:22:40.437000');
INSERT INTO [categorias] ([id], [nombre], [descripcion], [created_at]) VALUES (7, 'Cables y Controles', 'Cables de acelerador, cables de clutch, manecillas de clutch y pedales (de encendido y de cambios).', '2026-09-17 16:22:40.440000');
INSERT INTO [categorias] ([id], [nombre], [descripcion], [created_at]) VALUES (8, 'Chasis y Accesorios', 'Asientos, guardafangos, capas cubre moto, pitos (bocinas) y espejos/viseras.', '2026-09-17 16:22:40.443000');
INSERT INTO [categorias] ([id], [nombre], [descripcion], [created_at]) VALUES (9, 'Rodamientos y Misceláneos', 'Todas las balineras, sellos de válvulas, herramientas, aceites y otros.', '2026-09-17 16:22:40.443000');
SET IDENTITY_INSERT [categorias] OFF;
GO

-- Datos para [clientes] (3 registros)
SET IDENTITY_INSERT [clientes] ON;
INSERT INTO [clientes] ([id], [nombre_completo], [identificacion], [telefono], [email], [direccion], [tipo_cliente], [created_at], [password_hash]) VALUES (1, 'Cliente General (Mostrador)', '000-000000-0000X', '2222-0000', 'mostrador@jehovajireh.com', NULL, 'General', '2026-08-13 17:02:50.490000', NULL);
INSERT INTO [clientes] ([id], [nombre_completo], [identificacion], [telefono], [email], [direccion], [tipo_cliente], [created_at], [password_hash]) VALUES (2, 'Taller Hermanos Mendoza', '401-150885-0002K', '+505 8444-1234', 'taller.mendoza@gmail.com', NULL, 'Taller', '2026-08-13 17:02:50.490000', NULL);
INSERT INTO [clientes] ([id], [nombre_completo], [identificacion], [telefono], [email], [direccion], [tipo_cliente], [created_at], [password_hash]) VALUES (3, 'Carlos Estrada', '001-200392-0044L', '+505 8999-5544', 'carlos.estrada@yahoo.com', NULL, 'Frecuente', '2026-08-13 17:02:50.490000', NULL);
SET IDENTITY_INSERT [clientes] OFF;
GO

-- Datos para [contratos_laborales] (3 registros)
SET IDENTITY_INSERT [contratos_laborales] ON;
INSERT INTO [contratos_laborales] ([id], [numero_contrato], [empleado_id], [tipo_contratacion], [lugar_trabajo], [cargo], [jornada_laboral], [salario_mensual], [forma_pago], [fecha_inicio], [fecha_fin], [estado], [documento_adjunto], [observaciones], [created_at]) VALUES (1, 'CTR-2022-001', 1, 'Tiempo Indeterminado', 'Masatepe, Masaya - Tienda Central', 'Administrador General', 'Diurna Ordinaria (48h)', '25000.00', 'Quincenal', '2022-01-15', NULL, 'Vigente', NULL, 'Contrato formal de gerencia general', '2026-10-13 20:33:08.160000');
INSERT INTO [contratos_laborales] ([id], [numero_contrato], [empleado_id], [tipo_contratacion], [lugar_trabajo], [cargo], [jornada_laboral], [salario_mensual], [forma_pago], [fecha_inicio], [fecha_fin], [estado], [documento_adjunto], [observaciones], [created_at]) VALUES (2, 'CTR-2023-002', 2, 'Tiempo Indeterminado', 'Masatepe, Masaya - Tienda Central', 'Vendedor de Mostrador', 'Diurna Ordinaria (48h)', '9500.00', 'Quincenal', '2023-03-01', NULL, 'Vigente', NULL, 'Ventas de mostrador y cobro en caja POS', '2026-10-13 20:33:08.160000');
INSERT INTO [contratos_laborales] ([id], [numero_contrato], [empleado_id], [tipo_contratacion], [lugar_trabajo], [cargo], [jornada_laboral], [salario_mensual], [forma_pago], [fecha_inicio], [fecha_fin], [estado], [documento_adjunto], [observaciones], [created_at]) VALUES (3, 'CTR-2022-003', 3, 'Tiempo Indeterminado', 'Masatepe, Masaya - Tienda Central', 'Encargado de Bodega e Inventario', 'Diurna Ordinaria (48h)', '11000.00', 'Quincenal', '2022-08-10', NULL, 'Vigente', NULL, 'Recepción de mercadería y control de Kardex', '2026-10-13 20:33:08.160000');
SET IDENTITY_INSERT [contratos_laborales] OFF;
GO

-- Datos para [cuentas_contables] (28 registros)
SET IDENTITY_INSERT [cuentas_contables] ON;
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (1, '1.1.01', 'Caja', 'Activo corriente', 'Deudora', 'Efectivo disponible en caja.', True, '2026-09-17 16:22:41.497000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (2, '1.1.02', 'Bancos', 'Activo corriente', 'Deudora', 'Dinero disponible en cuentas bancarias.', True, '2026-09-17 16:22:41.500000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (3, '1.1.03', 'Clientes', 'Activo corriente', 'Deudora', 'Cuentas por cobrar por ventas realizadas a crédito.', True, '2026-09-17 16:22:41.500000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (4, '1.1.04', 'Inventario de repuestos y accesorios', 'Activo corriente', 'Deudora', 'Existencias de repuestos, accesorios y artículos para motocicletas.', True, '2026-09-17 16:22:41.503000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (5, '1.1.05', 'IVA acreditable', 'Activo corriente', 'Deudora', 'Impuesto acreditable generado por compras gravadas.', True, '2026-09-17 16:22:41.507000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (6, '1.2.01', 'Mobiliario y equipo', 'Activo no corriente', 'Deudora', 'Mostradores, estanterías, muebles y equipo utilizado en el negocio.', True, '2026-09-17 16:22:41.507000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (7, '1.2.02', 'Equipo de cómputo', 'Activo no corriente', 'Deudora', 'Computadoras, impresoras y equipo tecnológico.', True, '2026-09-17 16:22:41.510000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (8, '1.2.03', 'Depreciación acumulada de activos', 'Activo no corriente - contraactivo', 'Acreedora', 'Depreciación acumulada de los activos fijos.', True, '2026-09-17 16:22:41.510000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (9, '2.1.01', 'Proveedores', 'Pasivo corriente', 'Acreedora', 'Obligaciones pendientes por compras realizadas a crédito.', True, '2026-09-17 16:22:41.510000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (10, '2.1.02', 'Documentos por pagar', 'Pasivo corriente', 'Acreedora', 'Obligaciones respaldadas por documentos de pago.', True, '2026-09-17 16:22:41.513000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (11, '2.1.03', 'IVA por pagar', 'Pasivo corriente', 'Acreedora', 'Impuesto generado en las ventas pendiente de pago.', True, '2026-09-17 16:22:41.517000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (12, '2.1.04', 'Sueldos y salarios por pagar', 'Pasivo corriente', 'Acreedora', 'Remuneraciones pendientes de pago.', True, '2026-09-17 16:22:41.517000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (13, '2.1.05', 'Servicios básicos por pagar', 'Pasivo corriente', 'Acreedora', 'Servicios de energía, agua, internet u otros pendientes.', True, '2026-09-17 16:22:41.520000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (14, '3.1.01', 'Capital del propietario', 'Patrimonio', 'Acreedora', 'Aportes realizados por el propietario.', True, '2026-09-17 16:22:41.520000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (15, '3.1.02', 'Utilidades acumuladas', 'Patrimonio', 'Acreedora', 'Resultados de ejercicios anteriores retenidos en el negocio.', True, '2026-09-17 16:22:41.523000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (16, '4.1.01', 'Ventas de repuestos y accesorios', 'Ingresos', 'Acreedora', 'Ingresos provenientes de la comercialización de repuestos y accesorios.', True, '2026-09-17 16:22:41.523000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (17, '4.1.02', 'Ingresos por servicios de taller', 'Ingresos', 'Acreedora', 'Ingresos por instalación, reparación y servicios relacionados con motocicletas.', True, '2026-09-17 16:22:41.527000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (18, '5.1.01', 'Costo de ventas', 'Costo', 'Deudora', 'Costo de los repuestos y accesorios vendidos durante el período.', True, '2026-09-17 16:22:41.527000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (19, '6.1.01', 'Sueldos y salarios', 'Gasto', 'Deudora', 'Remuneraciones del personal.', True, '2026-09-17 16:22:41.530000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (20, '6.1.02', 'Alquiler del local', 'Gasto', 'Deudora', 'Alquiler del establecimiento comercial y taller.', True, '2026-09-17 16:22:41.530000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (21, '6.1.03', 'Energía eléctrica', 'Gasto', 'Deudora', 'Consumo de energía eléctrica.', True, '2026-09-17 16:22:41.533000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (22, '6.1.04', 'Agua', 'Gasto', 'Deudora', 'Consumo de agua.', True, '2026-09-17 16:22:41.533000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (23, '6.1.05', 'Internet y telefonía', 'Gasto', 'Deudora', 'Servicios de comunicación e internet.', True, '2026-09-17 16:22:41.537000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (24, '6.1.06', 'Publicidad y mercadotecnia', 'Gasto', 'Deudora', 'Promoción de productos y servicios del negocio.', True, '2026-09-17 16:22:41.537000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (25, '6.1.07', 'Mantenimiento y reparaciones', 'Gasto', 'Deudora', 'Mantenimiento del local, herramientas y equipos.', True, '2026-09-17 16:22:41.540000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (26, '6.1.08', 'Papelería y útiles', 'Gasto', 'Deudora', 'Materiales administrativos y de oficina.', True, '2026-09-17 16:22:41.540000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (27, '6.1.09', 'Depreciación del período', 'Gasto', 'Deudora', 'Depreciación correspondiente al período.', True, '2026-09-17 16:22:41.543000');
INSERT INTO [cuentas_contables] ([id], [codigo], [nombre], [clasificacion], [naturaleza], [descripcion], [activo], [created_at]) VALUES (28, '6.1.10', 'Comisiones y gastos bancarios', 'Gasto', 'Deudora', 'Comisiones y cargos generados por operaciones bancarias.', True, '2026-09-17 16:22:41.547000');
SET IDENTITY_INSERT [cuentas_contables] OFF;
GO

-- Datos para [detalle_nomina] (8 registros)
SET IDENTITY_INSERT [detalle_nomina] ON;
INSERT INTO [detalle_nomina] ([id], [nomina_id], [empleado_id], [salario_base], [inss_laboral], [ir], [otras_deducciones], [neto_pagar], [ingresos_extra], [inss_patronal], [provision_vacaciones], [provision_aguinaldo], [kpi_comision], [adelanto_salarial], [dias_trabajados], [vac_acumulada], [vac_mes], [vac_descansados], [vac_saldo_final], [dias_falta], [monto_falta], [dias_permiso_sin_goce], [monto_permiso_sin_goce], [dias_septimo_dia], [monto_septimo_dia], [inatec_patronal]) VALUES (2, 2, 1, '12000.00', '840.00', '424.00', '0.00', '10736.00', '0.00', '2700.00', '1000.00', '1000.00', '0.00', '0.00', '15.0', '0.00', '0.00', '0.00', '0.00', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [detalle_nomina] ([id], [nomina_id], [empleado_id], [salario_base], [inss_laboral], [ir], [otras_deducciones], [neto_pagar], [ingresos_extra], [inss_patronal], [provision_vacaciones], [provision_aguinaldo], [kpi_comision], [adelanto_salarial], [dias_trabajados], [vac_acumulada], [vac_mes], [vac_descansados], [vac_saldo_final], [dias_falta], [monto_falta], [dias_permiso_sin_goce], [monto_permiso_sin_goce], [dias_septimo_dia], [monto_septimo_dia], [inatec_patronal]) VALUES (3, 3, 1, '12000.00', '840.00', '424.00', '0.00', '10736.00', '0.00', '2700.00', '1000.00', '1000.00', '0.00', '0.00', '15.0', '0.00', '0.00', '0.00', '0.00', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [detalle_nomina] ([id], [nomina_id], [empleado_id], [salario_base], [inss_laboral], [ir], [otras_deducciones], [neto_pagar], [ingresos_extra], [inss_patronal], [provision_vacaciones], [provision_aguinaldo], [kpi_comision], [adelanto_salarial], [dias_trabajados], [vac_acumulada], [vac_mes], [vac_descansados], [vac_saldo_final], [dias_falta], [monto_falta], [dias_permiso_sin_goce], [monto_permiso_sin_goce], [dias_septimo_dia], [monto_septimo_dia], [inatec_patronal]) VALUES (4, 3, 2, '10000.00', '700.00', '145.00', '0.00', '9155.00', '0.00', '2250.00', '833.33', '833.33', '0.00', '0.00', '15.0', '0.00', '0.00', '0.00', '0.00', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [detalle_nomina] ([id], [nomina_id], [empleado_id], [salario_base], [inss_laboral], [ir], [otras_deducciones], [neto_pagar], [ingresos_extra], [inss_patronal], [provision_vacaciones], [provision_aguinaldo], [kpi_comision], [adelanto_salarial], [dias_trabajados], [vac_acumulada], [vac_mes], [vac_descansados], [vac_saldo_final], [dias_falta], [monto_falta], [dias_permiso_sin_goce], [monto_permiso_sin_goce], [dias_septimo_dia], [monto_septimo_dia], [inatec_patronal]) VALUES (15, 3, 5, '12000.00', '840.00', '424.00', '0.00', '10736.00', '0.00', '2700.00', '1000.00', '1000.00', '0.00', '0.00', '15.0', '0.00', '0.00', '0.00', '0.00', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [detalle_nomina] ([id], [nomina_id], [empleado_id], [salario_base], [inss_laboral], [ir], [otras_deducciones], [neto_pagar], [ingresos_extra], [inss_patronal], [provision_vacaciones], [provision_aguinaldo], [kpi_comision], [adelanto_salarial], [dias_trabajados], [vac_acumulada], [vac_mes], [vac_descansados], [vac_saldo_final], [dias_falta], [monto_falta], [dias_permiso_sin_goce], [monto_permiso_sin_goce], [dias_septimo_dia], [monto_septimo_dia], [inatec_patronal]) VALUES (16, 3, 3, '12500.00', '875.00', '493.75', '0.00', '11131.25', '0.00', '2812.50', '1041.67', '1041.67', '0.00', '0.00', '15.0', '0.00', '0.00', '0.00', '0.00', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [detalle_nomina] ([id], [nomina_id], [empleado_id], [salario_base], [inss_laboral], [ir], [otras_deducciones], [neto_pagar], [ingresos_extra], [inss_patronal], [provision_vacaciones], [provision_aguinaldo], [kpi_comision], [adelanto_salarial], [dias_trabajados], [vac_acumulada], [vac_mes], [vac_descansados], [vac_saldo_final], [dias_falta], [monto_falta], [dias_permiso_sin_goce], [monto_permiso_sin_goce], [dias_septimo_dia], [monto_septimo_dia], [inatec_patronal]) VALUES (17, 3, 4, '15000.00', '1050.00', '842.50', '0.00', '13107.50', '0.00', '3375.00', '1250.00', '1250.00', '0.00', '0.00', '15.0', '0.00', '0.00', '0.00', '0.00', NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [detalle_nomina] ([id], [nomina_id], [empleado_id], [salario_base], [inss_laboral], [ir], [otras_deducciones], [neto_pagar], [ingresos_extra], [inss_patronal], [provision_vacaciones], [provision_aguinaldo], [kpi_comision], [adelanto_salarial], [dias_trabajados], [vac_acumulada], [vac_mes], [vac_descansados], [vac_saldo_final], [dias_falta], [monto_falta], [dias_permiso_sin_goce], [monto_permiso_sin_goce], [dias_septimo_dia], [monto_septimo_dia], [inatec_patronal]) VALUES (23, 2, 5, '9200.00', '644.00', '33.40', '0.00', '8522.60', '0.00', '1978.00', '766.67', '766.67', '0.00', '0.00', '23.0', '90.10', '1.92', '0.00', '92.02', '7.00', '2800.00', '0.00', '0.00', '0.00', '0.00', '184.00');
INSERT INTO [detalle_nomina] ([id], [nomina_id], [empleado_id], [salario_base], [inss_laboral], [ir], [otras_deducciones], [neto_pagar], [ingresos_extra], [inss_patronal], [provision_vacaciones], [provision_aguinaldo], [kpi_comision], [adelanto_salarial], [dias_trabajados], [vac_acumulada], [vac_mes], [vac_descansados], [vac_saldo_final], [dias_falta], [monto_falta], [dias_permiso_sin_goce], [monto_permiso_sin_goce], [dias_septimo_dia], [monto_septimo_dia], [inatec_patronal]) VALUES (24, 10, 3, '12500.00', '875.00', '493.75', '0.00', '11131.25', '0.00', '2687.50', '1041.67', '1041.67', '0.00', '0.00', '30.0', '104.20', '2.50', '0.00', '106.70', '0.00', '0.00', '0.00', '0.00', '0.00', '0.00', '250.00');
SET IDENTITY_INSERT [detalle_nomina] OFF;
GO

-- Datos para [empleados] (5 registros)
SET IDENTITY_INSERT [empleados] ON;
INSERT INTO [empleados] ([id], [nombre_completo], [identificacion], [cargo], [salario_base], [fecha_ingreso], [activo], [created_at], [num_inss], [telefono], [email], [dias_vacaciones_disponibles], [observaciones], [cargo_id], [vacacionesDisponibles], [fecha_nacimiento], [direccion], [contacto_emergencia], [telefono_emergencia], [jornada_asignada], [fecha_baja], [motivo_baja], [inss_regimen], [inss_fecha_alta], [inss_estado], [jornada_id]) VALUES (1, 'Juan Perez', '001-080995-1006D', 'Vendedor', '12000.00', '2025-06-01', True, '2026-09-06 13:52:04.180000', '123456', '8886-9630', 'juanperez@gmail.com', '40.4', '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [empleados] ([id], [nombre_completo], [identificacion], [cargo], [salario_base], [fecha_ingreso], [activo], [created_at], [num_inss], [telefono], [email], [dias_vacaciones_disponibles], [observaciones], [cargo_id], [vacacionesDisponibles], [fecha_nacimiento], [direccion], [contacto_emergencia], [telefono_emergencia], [jornada_asignada], [fecha_baja], [motivo_baja], [inss_regimen], [inss_fecha_alta], [inss_estado], [jornada_id]) VALUES (2, 'Martha Lopez', '401-250196-1008F', 'Bodeguero', '10000.00', '2026-07-05', True, '2026-09-06 14:17:35.040000', '2863459', '8895-6302', 'marthalopez@gmail.com', '7.6', '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [empleados] ([id], [nombre_completo], [identificacion], [cargo], [salario_base], [fecha_ingreso], [activo], [created_at], [num_inss], [telefono], [email], [dias_vacaciones_disponibles], [observaciones], [cargo_id], [vacacionesDisponibles], [fecha_nacimiento], [direccion], [contacto_emergencia], [telefono_emergencia], [jornada_asignada], [fecha_baja], [motivo_baja], [inss_regimen], [inss_fecha_alta], [inss_estado], [jornada_id]) VALUES (3, 'Roberto Mejía', '001-010103', 'Vendedor', '12500.00', '2023-04-16', True, '2026-09-06 15:11:29.060000', '369582', '7593-3220', 'robertomejia@gmail.com', '91.7', '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [empleados] ([id], [nombre_completo], [identificacion], [cargo], [salario_base], [fecha_ingreso], [activo], [created_at], [num_inss], [telefono], [email], [dias_vacaciones_disponibles], [observaciones], [cargo_id], [vacacionesDisponibles], [fecha_nacimiento], [direccion], [contacto_emergencia], [telefono_emergencia], [jornada_asignada], [fecha_baja], [motivo_baja], [inss_regimen], [inss_fecha_alta], [inss_estado], [jornada_id]) VALUES (4, 'Angela Ramírez', '001-030403-1006C', 'Contador', '15000.00', '2024-08-05', True, '2026-09-06 17:52:27.143000', '286942', '8185-6970', 'angelaramirez@gmail.com', '57.1', '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
INSERT INTO [empleados] ([id], [nombre_completo], [identificacion], [cargo], [salario_base], [fecha_ingreso], [activo], [created_at], [num_inss], [telefono], [email], [dias_vacaciones_disponibles], [observaciones], [cargo_id], [vacacionesDisponibles], [fecha_nacimiento], [direccion], [contacto_emergencia], [telefono_emergencia], [jornada_asignada], [fecha_baja], [motivo_baja], [inss_regimen], [inss_fecha_alta], [inss_estado], [jornada_id]) VALUES (5, 'María Ramírez', '401-010596-1006V', 'Vendedor', '12000.00', '2023-10-05', True, '2026-09-06 23:28:17.040000', '23456', '8896-2033', 'mariaramirez@gmail.com', '92.0', '', NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
SET IDENTITY_INSERT [empleados] OFF;
GO

-- Datos para [expediente_empleado] (5 registros)
SET IDENTITY_INSERT [expediente_empleado] ON;
INSERT INTO [expediente_empleado] ([id], [empleado_id], [tipo_documento], [nombre_archivo], [fecha_registro], [usuario_responsable], [observaciones]) VALUES (1, 1, 'Cédula de Identidad', 'cedula_gilda_perez.pdf', '2026-10-13 20:33:08.170000', 'admin', 'Copia ampliada escaneada');
INSERT INTO [expediente_empleado] ([id], [empleado_id], [tipo_documento], [nombre_archivo], [fecha_registro], [usuario_responsable], [observaciones]) VALUES (2, 1, 'Afiliación INSS', 'inss_afiliacion_gilda.pdf', '2026-10-13 20:33:08.170000', 'admin', 'Constancia oficial del INSS');
INSERT INTO [expediente_empleado] ([id], [empleado_id], [tipo_documento], [nombre_archivo], [fecha_registro], [usuario_responsable], [observaciones]) VALUES (3, 2, 'Cédula de Identidad', 'cedula_ana_gomez.pdf', '2026-10-13 20:33:08.170000', 'admin', 'Copia legalizada vigente');
INSERT INTO [expediente_empleado] ([id], [empleado_id], [tipo_documento], [nombre_archivo], [fecha_registro], [usuario_responsable], [observaciones]) VALUES (4, 2, 'Contrato Firmado', 'contrato_firmado_ana_gomez.pdf', '2026-10-13 20:33:08.170000', 'admin', 'Firmado por ambas partes');
INSERT INTO [expediente_empleado] ([id], [empleado_id], [tipo_documento], [nombre_archivo], [fecha_registro], [usuario_responsable], [observaciones]) VALUES (5, 3, 'Récord de Policía', 'record_roberto_silva.pdf', '2026-10-13 20:33:08.170000', 'admin', 'Emitido por Policía Nacional Masaya');
SET IDENTITY_INSERT [expediente_empleado] OFF;
GO

-- Datos para [higiene_capacitaciones] (2 registros)
SET IDENTITY_INSERT [higiene_capacitaciones] ON;
INSERT INTO [higiene_capacitaciones] ([id], [nombre_capacitacion], [fecha], [duracion_horas], [facilitador], [temas_tratados], [asistentes_conteo], [observaciones], [created_at]) VALUES (1, 'Prevención de Lesiones en Manipulación de Carga y Ergonomía', '2026-02-15', '2.0', 'Técnico MITRAB Masaya', 'Higiene postural, límite seguro de carga (25 kg), técnicas de estiba y orden en bodega comercial.', 3, 'Participaron bodega, ventas y administración.', '2026-10-13 20:33:08.183000');
INSERT INTO [higiene_capacitaciones] ([id], [nombre_capacitacion], [fecha], [duracion_horas], [facilitador], [temas_tratados], [asistentes_conteo], [observaciones], [created_at]) VALUES (2, 'Uso Práctico de Extintores PQS y Plan de Evacuación Comercial', '2026-05-20', '2.5', 'Cuerpo de Bomberos Masatepe', 'Clases de fuego (A, B, C), manejo de extintor de polvo químico seco y despeje de pasillos.', 5, 'Todo el personal de la tienda.', '2026-10-13 20:33:08.183000');
SET IDENTITY_INSERT [higiene_capacitaciones] OFF;
GO

-- Datos para [higiene_epp] (3 registros)
SET IDENTITY_INSERT [higiene_epp] ON;
INSERT INTO [higiene_epp] ([id], [empleado_id], [tipo_equipo], [fecha_entrega], [cantidad], [estado_equipo], [fecha_reposicion_sugerida], [entregado_por], [observaciones]) VALUES (1, 3, 'Faja lumbar para estiba y carga', '2026-01-10', 1, 'Bueno', '2026-07-10', 'Administración', 'Para uso continuo en estanterías de bodega');
INSERT INTO [higiene_epp] ([id], [empleado_id], [tipo_equipo], [fecha_entrega], [cantidad], [estado_equipo], [fecha_reposicion_sugerida], [entregado_por], [observaciones]) VALUES (2, 3, 'Guantes de nitrilo antideslizantes', '2026-02-01', 2, 'Bueno', '2026-05-01', 'Administración', 'Manipulación de botes de lubricantes y cadenas');
INSERT INTO [higiene_epp] ([id], [empleado_id], [tipo_equipo], [fecha_entrega], [cantidad], [estado_equipo], [fecha_reposicion_sugerida], [entregado_por], [observaciones]) VALUES (3, 3, 'Botas con puntera reforzada', '2026-01-10', 1, 'Bueno', '2027-01-10', 'Administración', 'Protección contra caída de repuestos pesados');
SET IDENTITY_INSERT [higiene_epp] OFF;
GO

-- Datos para [higiene_inspecciones] (1 registros)
SET IDENTITY_INSERT [higiene_inspecciones] ON;
INSERT INTO [higiene_inspecciones] ([id], [fecha_inspeccion], [inspector], [pasillos_despejados], [estanterias_seguras], [repuestos_ordenados], [extintores_adecuados], [salidas_emergencia_libres], [area_caja_segura], [puntos_aprobados], [total_puntos], [porcentaje_cumplimiento], [observaciones], [acciones_correctivas], [estado]) VALUES (1, '2026-10-01 00:00:00', 'Gilda Pérez', True, True, True, True, True, True, 6, 6, '100.00', 'Inspección periódica mensual conforme a Ley 618. Pasillos y extintores en orden.', 'Mantener señalización limpia', 'Aprobada');
SET IDENTITY_INSERT [higiene_inspecciones] OFF;
GO

-- Datos para [higiene_riesgos] (4 registros)
SET IDENTITY_INSERT [higiene_riesgos] ON;
INSERT INTO [higiene_riesgos] ([id], [area], [tipo_riesgo], [descripcion], [nivel_riesgo], [medidas_preventivas], [responsable_seguimiento], [estado], [fecha_registro]) VALUES (1, 'Bodega / Almacén', 'Manipulación de Cargas', 'Levantamiento manual de cajas pesadas de cadenas, catalinas y baterías de gel', 'Medio', 'Uso obligatorio de faja lumbar, técnica de levantamiento con flexión de piernas y carretilla de transporte', 'Encargado de Bodega', 'Activo', '2026-10-13 20:08:18.870000');
INSERT INTO [higiene_riesgos] ([id], [area], [tipo_riesgo], [descripcion], [nivel_riesgo], [medidas_preventivas], [responsable_seguimiento], [estado], [fecha_registro]) VALUES (2, 'Bodega / Almacén', 'Caída de Objetos', 'Almacenamiento de repuestos y cascos en niveles superiores de estanterías metálicas', 'Alto', 'Fijación de estantes a la pared, topes de contención y no sobrecargar niveles altos', 'Encargado de Bodega', 'Activo', '2026-10-13 20:08:18.870000');
INSERT INTO [higiene_riesgos] ([id], [area], [tipo_riesgo], [descripcion], [nivel_riesgo], [medidas_preventivas], [responsable_seguimiento], [estado], [fecha_registro]) VALUES (3, 'Ventas / Mostrador', 'Ergonómico / Postura', 'Jornada prolongada de pie durante atención continua a clientes de mostrador', 'Bajo', 'Uso de calzado con soporte acolchado y pausas activas breves cada 2 horas', 'Administrador General', 'Activo', '2026-10-13 20:08:18.870000');
INSERT INTO [higiene_riesgos] ([id], [area], [tipo_riesgo], [descripcion], [nivel_riesgo], [medidas_preventivas], [responsable_seguimiento], [estado], [fecha_registro]) VALUES (4, 'Caja', 'Riesgo Eléctrico / Enredos', 'Conexión de múltiples periféricos (impresora térmica, monitor, UPS, lector de barras)', 'Bajo', 'Canalización de cables con canaletas plásticas e inspección periódica de tomacorrientes', 'Administrador General', 'Activo', '2026-10-13 20:08:18.870000');
SET IDENTITY_INSERT [higiene_riesgos] OFF;
GO

-- Datos para [jornadas_laborales] (6 registros)
SET IDENTITY_INSERT [jornadas_laborales] ON;
INSERT INTO [jornadas_laborales] ([id], [nombre], [hora_entrada], [hora_salida], [minutos_descanso], [dias_laborables], [dia_descanso], [horas_semanales], [activo], [created_at]) VALUES (1, 'Diurna Comercial Mostrador (8h)', '08:00', '17:00', 60, 'Lunes a Sábado', 'Domingo', '48.00', True, '2026-10-13 20:25:39.500000');
INSERT INTO [jornadas_laborales] ([id], [nombre], [hora_entrada], [hora_salida], [minutos_descanso], [dias_laborables], [dia_descanso], [horas_semanales], [activo], [created_at]) VALUES (2, 'Bodega y Almacén (8h)', '07:30', '16:30', 60, 'Lunes a Sábado', 'Domingo', '48.00', True, '2026-10-13 20:25:39.500000');
INSERT INTO [jornadas_laborales] ([id], [nombre], [hora_entrada], [hora_salida], [minutos_descanso], [dias_laborables], [dia_descanso], [horas_semanales], [activo], [created_at]) VALUES (3, 'Administración y Finanzas', '08:00', '17:00', 60, 'Lunes a Viernes', 'Sábado y Domingo', '40.00', True, '2026-10-13 20:25:39.500000');
INSERT INTO [jornadas_laborales] ([id], [nombre], [hora_entrada], [hora_salida], [minutos_descanso], [dias_laborables], [dia_descanso], [horas_semanales], [activo], [created_at]) VALUES (4, 'Jornada Diurna', '07:00', '16:00', 60, 'Lunes a Viernes', 'Domingo', '48.00', True, '2026-10-13 22:07:35.450000');
INSERT INTO [jornadas_laborales] ([id], [nombre], [hora_entrada], [hora_salida], [minutos_descanso], [dias_laborables], [dia_descanso], [horas_semanales], [activo], [created_at]) VALUES (5, 'Jornada Mixta', '10:00', '19:00', 60, 'Lunes a Sabado', 'Domingo', '48.00', True, '2026-10-13 22:07:35.467000');
INSERT INTO [jornadas_laborales] ([id], [nombre], [hora_entrada], [hora_salida], [minutos_descanso], [dias_laborables], [dia_descanso], [horas_semanales], [activo], [created_at]) VALUES (6, 'Medio Tiempo', '08:00', '12:00', 0, 'Lunes a Viernes', 'Sabado y Domingo', '20.00', True, '2026-10-13 22:07:35.480000');
SET IDENTITY_INSERT [jornadas_laborales] OFF;
GO

-- Datos para [liquidaciones_laborales] (1 registros)
SET IDENTITY_INSERT [liquidaciones_laborales] ON;
INSERT INTO [liquidaciones_laborales] ([id], [codigo], [empleado_id], [fecha_ingreso], [fecha_salida], [motivo_salida], [salario_base], [antiguedad_anios], [antiguedad_meses], [antiguedad_dias], [monto_dias_pendientes], [dias_vacaciones_pendientes], [monto_vacaciones], [monto_aguinaldo_proporcional], [monto_indemnizacion_antiguedad], [total_percepciones], [deducciones_totales], [neto_a_pagar], [estado], [elaborado_por], [fecha_elaboracion]) VALUES (1, 'LIQ-2026-001', 1, '2025-06-01', '2026-10-10', 'Renuncia Voluntaria', '12000.00', 1, 4, 11, '0.00', '40.40', '16160.00', '10466.67', '0.00', '26626.67', '0.00', '26626.67', 'Borrador', 'admin', '2026-10-13 20:49:44.817000');
SET IDENTITY_INSERT [liquidaciones_laborales] OFF;
GO

-- Datos para [movimientos_contables] (44 registros)
SET IDENTITY_INSERT [movimientos_contables] ON;
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (1, 1, 4, '420000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (2, 1, 6, '90000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (3, 1, 7, '55000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (4, 1, 14, '0.00', '250000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (5, 1, 9, '0.00', '250000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (6, 1, 10, '0.00', '60000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (7, 1, 15, '0.00', '5000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (8, 2, 18, '650000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (9, 2, 2, '185000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (10, 2, 3, '60000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (11, 2, 1, '45000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (12, 2, 5, '18000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (13, 2, 19, '70000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (14, 2, 22, '2000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (15, 2, 16, '0.00', '950000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (16, 2, 17, '0.00', '80000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (17, 3, 20, '30000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (18, 3, 21, '12000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (19, 3, 23, '5000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (20, 3, 24, '10000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (21, 3, 25, '8000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (22, 3, 26, '3000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (23, 3, 27, '12000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (24, 3, 28, '22000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (25, 3, 22, '1000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (26, 3, 8, '0.00', '12000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (27, 3, 11, '0.00', '22000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (28, 3, 12, '0.00', '18000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (29, 3, 13, '0.00', '5000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (30, 3, 15, '0.00', '46000.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (31, 4, 19, '61500.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (32, 4, 12, '0.00', '54865.75');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (33, 5, 19, '12000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (34, 5, 12, '0.00', '10736.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (35, 6, 19, '27500.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (36, 6, 12, '0.00', '24238.75');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (37, 7, 19, '61500.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (38, 7, 12, '0.00', '54865.75');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (39, 8, 19, '12000.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (40, 8, 12, '0.00', '10736.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (41, 9, 19, '12500.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (42, 9, 12, '0.00', '11131.25');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (43, 10, 19, '12500.00', '0.00');
INSERT INTO [movimientos_contables] ([id], [asiento_id], [cuenta_id], [debe], [haber]) VALUES (44, 10, 12, '0.00', '11131.25');
SET IDENTITY_INSERT [movimientos_contables] OFF;
GO

-- Datos para [movimientos_inventario] (235 registros)
SET IDENTITY_INSERT [movimientos_inventario] ON;
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (1, '2026-08-17 08:00:00', 1, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.407000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (2, '2026-08-17 08:00:00', 2, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.407000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (3, '2026-08-17 08:00:00', 3, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.407000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (4, '2026-08-17 08:00:00', 4, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.407000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (5, '2026-08-17 08:00:00', 5, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.407000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (6, '2026-08-17 08:00:00', 6, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.407000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (7, '2026-08-17 08:00:00', 7, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.407000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (8, '2026-08-17 08:00:00', 8, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.407000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (9, '2026-08-17 08:00:00', 9, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.407000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (10, '2026-08-17 08:00:00', 10, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (11, '2026-08-17 08:00:00', 11, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (12, '2026-08-17 08:00:00', 12, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (13, '2026-08-17 08:00:00', 13, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (14, '2026-08-17 08:00:00', 14, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (15, '2026-08-17 08:00:00', 15, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (16, '2026-08-17 08:00:00', 16, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (17, '2026-08-17 08:00:00', 17, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (18, '2026-08-17 08:00:00', 18, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (19, '2026-08-17 08:00:00', 19, 'ENTRADA_INICIAL', 4, 0, 4, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (20, '2026-08-17 08:00:00', 20, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (21, '2026-08-17 08:00:00', 21, 'ENTRADA_INICIAL', 2, 0, 2, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (22, '2026-08-17 08:00:00', 22, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (23, '2026-08-17 08:00:00', 23, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (24, '2026-08-17 08:00:00', 24, 'ENTRADA_INICIAL', 15, 0, 15, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (25, '2026-08-17 08:00:00', 25, 'ENTRADA_INICIAL', 15, 0, 15, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (26, '2026-08-17 08:00:00', 26, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (27, '2026-08-17 08:00:00', 27, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (28, '2026-08-17 08:00:00', 28, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (29, '2026-08-17 08:00:00', 29, 'ENTRADA_INICIAL', 60, 0, 60, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (30, '2026-08-17 08:00:00', 30, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.410000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (31, '2026-08-17 08:00:00', 31, 'ENTRADA_INICIAL', 60, 0, 60, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (32, '2026-08-17 08:00:00', 32, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (33, '2026-08-17 08:00:00', 33, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (34, '2026-08-17 08:00:00', 34, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (35, '2026-08-17 08:00:00', 35, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (36, '2026-08-17 08:00:00', 36, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (37, '2026-08-17 08:00:00', 37, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (38, '2026-08-17 08:00:00', 38, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (39, '2026-08-17 08:00:00', 39, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (40, '2026-08-17 08:00:00', 40, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.423000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (41, '2026-08-17 08:00:00', 41, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (42, '2026-08-17 08:00:00', 42, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (43, '2026-08-17 08:00:00', 43, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (44, '2026-08-17 08:00:00', 44, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (45, '2026-08-17 08:00:00', 45, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (46, '2026-08-17 08:00:00', 46, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (47, '2026-08-17 08:00:00', 47, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (48, '2026-08-17 08:00:00', 48, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (49, '2026-08-17 08:00:00', 49, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (50, '2026-08-17 08:00:00', 50, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (51, '2026-08-17 08:00:00', 51, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (52, '2026-08-17 08:00:00', 52, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (53, '2026-08-17 08:00:00', 53, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (54, '2026-08-17 08:00:00', 54, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (55, '2026-08-17 08:00:00', 55, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (56, '2026-08-17 08:00:00', 56, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (57, '2026-08-17 08:00:00', 57, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (58, '2026-08-17 08:00:00', 58, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (59, '2026-08-17 08:00:00', 59, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.427000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (60, '2026-08-17 08:00:00', 60, 'ENTRADA_INICIAL', 100, 0, 100, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (61, '2026-08-17 08:00:00', 61, 'ENTRADA_INICIAL', 100, 0, 100, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (62, '2026-08-17 08:00:00', 62, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (63, '2026-08-17 08:00:00', 63, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (64, '2026-08-17 08:00:00', 64, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (65, '2026-08-17 08:00:00', 65, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (66, '2026-08-17 08:00:00', 66, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (67, '2026-08-17 08:00:00', 67, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (68, '2026-08-17 08:00:00', 68, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (69, '2026-08-17 08:00:00', 69, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (70, '2026-08-17 08:00:00', 70, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (71, '2026-08-17 08:00:00', 71, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (72, '2026-08-17 08:00:00', 72, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (73, '2026-08-17 08:00:00', 73, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (74, '2026-08-17 08:00:00', 74, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (75, '2026-08-17 08:00:00', 75, 'ENTRADA_INICIAL', 100, 0, 100, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (76, '2026-08-17 08:00:00', 76, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (77, '2026-08-17 08:00:00', 77, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.430000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (78, '2026-08-17 08:00:00', 78, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.433000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (79, '2026-08-17 08:00:00', 79, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.433000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (80, '2026-08-17 08:00:00', 80, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.433000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (81, '2026-08-17 08:00:00', 81, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.433000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (82, '2026-08-17 08:00:00', 82, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.433000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (83, '2026-08-17 08:00:00', 83, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.433000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (84, '2026-08-17 08:00:00', 84, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.433000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (85, '2026-08-17 08:00:00', 85, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (86, '2026-08-17 08:00:00', 86, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (87, '2026-08-17 08:00:00', 87, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (88, '2026-08-17 08:00:00', 88, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (89, '2026-08-17 08:00:00', 89, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (90, '2026-08-17 08:00:00', 90, 'ENTRADA_INICIAL', 2, 0, 2, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (91, '2026-08-17 08:00:00', 91, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (92, '2026-08-17 08:00:00', 92, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (93, '2026-08-17 08:00:00', 93, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (94, '2026-08-17 08:00:00', 94, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (95, '2026-08-17 08:00:00', 95, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (96, '2026-08-17 08:00:00', 96, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (97, '2026-08-17 08:00:00', 97, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (98, '2026-08-17 08:00:00', 98, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.437000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (99, '2026-08-17 08:00:00', 99, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (100, '2026-08-17 08:00:00', 100, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (101, '2026-08-17 08:00:00', 101, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (102, '2026-08-17 08:00:00', 102, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (103, '2026-08-17 08:00:00', 103, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (104, '2026-08-17 08:00:00', 104, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (105, '2026-08-17 08:00:00', 105, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (106, '2026-08-17 08:00:00', 106, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (107, '2026-08-17 08:00:00', 107, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (108, '2026-08-17 08:00:00', 108, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (109, '2026-08-17 08:00:00', 109, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (110, '2026-08-17 08:00:00', 110, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (111, '2026-08-17 08:00:00', 111, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (112, '2026-08-17 08:00:00', 112, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (113, '2026-08-17 08:00:00', 113, 'ENTRADA_INICIAL', 8, 0, 8, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (114, '2026-08-17 08:00:00', 114, 'ENTRADA_INICIAL', 8, 0, 8, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (115, '2026-08-17 08:00:00', 115, 'ENTRADA_INICIAL', 8, 0, 8, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (116, '2026-08-17 08:00:00', 116, 'ENTRADA_INICIAL', 2, 0, 2, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (117, '2026-08-17 08:00:00', 117, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (118, '2026-08-17 08:00:00', 118, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (119, '2026-08-17 08:00:00', 119, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (120, '2026-08-17 08:00:00', 120, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.440000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (121, '2026-08-17 08:00:00', 121, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (122, '2026-08-17 08:00:00', 122, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (123, '2026-08-17 08:00:00', 123, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (124, '2026-08-17 08:00:00', 124, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (125, '2026-08-17 08:00:00', 125, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (126, '2026-08-17 08:00:00', 126, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (127, '2026-08-17 08:00:00', 127, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (128, '2026-08-17 08:00:00', 128, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (129, '2026-08-17 08:00:00', 129, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (130, '2026-08-17 08:00:00', 130, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (131, '2026-08-17 08:00:00', 131, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (132, '2026-08-17 08:00:00', 132, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (133, '2026-08-17 08:00:00', 133, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (134, '2026-08-17 08:00:00', 134, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (135, '2026-08-17 08:00:00', 135, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (136, '2026-08-17 08:00:00', 136, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (137, '2026-08-17 08:00:00', 137, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (138, '2026-08-17 08:00:00', 138, 'ENTRADA_INICIAL', 15, 0, 15, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (139, '2026-08-17 08:00:00', 139, 'ENTRADA_INICIAL', 15, 0, 15, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (140, '2026-08-17 08:00:00', 140, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (141, '2026-08-17 08:00:00', 141, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.443000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (142, '2026-08-17 08:00:00', 142, 'ENTRADA_INICIAL', 200, 0, 200, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (143, '2026-08-17 08:00:00', 143, 'ENTRADA_INICIAL', 200, 0, 200, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (144, '2026-08-17 08:00:00', 144, 'ENTRADA_INICIAL', 200, 0, 200, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (145, '2026-08-17 08:00:00', 145, 'ENTRADA_INICIAL', 200, 0, 200, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (146, '2026-08-17 08:00:00', 146, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (147, '2026-08-17 08:00:00', 147, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (148, '2026-08-17 08:00:00', 148, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (149, '2026-08-17 08:00:00', 149, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (150, '2026-08-17 08:00:00', 150, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (151, '2026-08-17 08:00:00', 151, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (152, '2026-08-17 08:00:00', 152, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (153, '2026-08-17 08:00:00', 153, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (154, '2026-08-17 08:00:00', 154, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (155, '2026-08-17 08:00:00', 155, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (156, '2026-08-17 08:00:00', 156, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (157, '2026-08-17 08:00:00', 157, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (158, '2026-08-17 08:00:00', 158, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (159, '2026-08-17 08:00:00', 159, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (160, '2026-08-17 08:00:00', 160, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (161, '2026-08-17 08:00:00', 161, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.447000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (162, '2026-08-17 08:00:00', 162, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (163, '2026-08-17 08:00:00', 163, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (164, '2026-08-17 08:00:00', 164, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (165, '2026-08-17 08:00:00', 165, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (166, '2026-08-17 08:00:00', 166, 'ENTRADA_INICIAL', 2, 0, 2, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (167, '2026-08-17 08:00:00', 167, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (168, '2026-08-17 08:00:00', 168, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (169, '2026-08-17 08:00:00', 169, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (170, '2026-08-17 08:00:00', 170, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (171, '2026-08-17 08:00:00', 171, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (172, '2026-08-17 08:00:00', 172, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (173, '2026-08-17 08:00:00', 173, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (174, '2026-08-17 08:00:00', 174, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (175, '2026-08-17 08:00:00', 175, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (176, '2026-08-17 08:00:00', 176, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (177, '2026-08-17 08:00:00', 177, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (178, '2026-08-17 08:00:00', 178, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (179, '2026-08-17 08:00:00', 179, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (180, '2026-08-17 08:00:00', 180, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (181, '2026-08-17 08:00:00', 181, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (182, '2026-08-17 08:00:00', 182, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (183, '2026-08-17 08:00:00', 183, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (184, '2026-08-17 08:00:00', 184, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.450000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (185, '2026-08-17 08:00:00', 185, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (186, '2026-08-17 08:00:00', 186, 'ENTRADA_INICIAL', 15, 0, 15, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (187, '2026-08-17 08:00:00', 187, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (188, '2026-08-17 08:00:00', 188, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (189, '2026-08-17 08:00:00', 189, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (190, '2026-08-17 08:00:00', 190, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (191, '2026-08-17 08:00:00', 191, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (192, '2026-08-17 08:00:00', 192, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (193, '2026-08-17 08:00:00', 193, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (194, '2026-08-17 08:00:00', 194, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (195, '2026-08-17 08:00:00', 195, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (196, '2026-08-17 08:00:00', 196, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (197, '2026-08-17 08:00:00', 197, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (198, '2026-08-17 08:00:00', 198, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (199, '2026-08-17 08:00:00', 199, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (200, '2026-08-17 08:00:00', 200, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (201, '2026-08-17 08:00:00', 201, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (202, '2026-08-17 08:00:00', 202, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (203, '2026-08-17 08:00:00', 203, 'ENTRADA_INICIAL', 50, 0, 50, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (204, '2026-08-17 08:00:00', 204, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (205, '2026-08-17 08:00:00', 205, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (206, '2026-08-17 08:00:00', 206, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (207, '2026-08-17 08:00:00', 207, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (208, '2026-08-17 08:00:00', 208, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (209, '2026-08-17 08:00:00', 209, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (210, '2026-08-17 08:00:00', 210, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.453000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (211, '2026-08-17 08:00:00', 211, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (212, '2026-08-17 08:00:00', 212, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (213, '2026-08-17 08:00:00', 213, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (214, '2026-08-17 08:00:00', 214, 'ENTRADA_INICIAL', 5, 0, 5, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (215, '2026-08-17 08:00:00', 215, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (216, '2026-08-17 08:00:00', 216, 'ENTRADA_INICIAL', 3, 0, 3, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (217, '2026-08-17 08:00:00', 217, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (218, '2026-08-17 08:00:00', 218, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (219, '2026-08-17 08:00:00', 219, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (220, '2026-08-17 08:00:00', 220, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (221, '2026-08-17 08:00:00', 221, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (222, '2026-08-17 08:00:00', 222, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (223, '2026-08-17 08:00:00', 223, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (224, '2026-08-17 08:00:00', 224, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (225, '2026-08-17 08:00:00', 225, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (226, '2026-08-17 08:00:00', 226, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (227, '2026-08-17 08:00:00', 227, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (228, '2026-08-17 08:00:00', 228, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (229, '2026-08-17 08:00:00', 229, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (230, '2026-08-17 08:00:00', 230, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (231, '2026-08-17 08:00:00', 231, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (232, '2026-08-17 08:00:00', 232, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (233, '2026-08-17 08:00:00', 233, 'ENTRADA_INICIAL', 10, 0, 10, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (234, '2026-08-17 08:00:00', 234, 'ENTRADA_INICIAL', 30, 0, 30, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
INSERT INTO [movimientos_inventario] ([id], [fecha], [producto_id], [tipo_movimiento], [cantidad], [stock_anterior], [stock_posterior], [referencia_origen], [motivo], [usuario_id], [created_at]) VALUES (235, '2026-08-17 08:00:00', 235, 'ENTRADA_INICIAL', 20, 0, 20, 'INICIO', 'Carga inicial de inventario', 1, '2026-09-17 16:22:41.457000');
SET IDENTITY_INSERT [movimientos_inventario] OFF;
GO

-- Datos para [movimientos_laborales] (5 registros)
SET IDENTITY_INSERT [movimientos_laborales] ON;
INSERT INTO [movimientos_laborales] ([id], [empleado_id], [tipo], [fecha_inicio], [fecha_fin], [dias_tomados], [observacion], [created_at], [afecta_septimo_dia], [estado], [aprobado_por], [documento_respaldo], [clasificacion]) VALUES (1, 1, 'PERMISO_CON_GOCE', '2026-08-21', '2026-08-25', '5.0', '', '2026-09-06 14:59:32.487000', NULL, NULL, NULL, NULL, NULL);
INSERT INTO [movimientos_laborales] ([id], [empleado_id], [tipo], [fecha_inicio], [fecha_fin], [dias_tomados], [observacion], [created_at], [afecta_septimo_dia], [estado], [aprobado_por], [documento_respaldo], [clasificacion]) VALUES (4, 4, 'VACACIONES', '2026-10-06', '2026-10-13', '8.0', 'Enfermedad', '2026-10-06 18:27:45.910000', NULL, NULL, NULL, NULL, NULL);
INSERT INTO [movimientos_laborales] ([id], [empleado_id], [tipo], [fecha_inicio], [fecha_fin], [dias_tomados], [observacion], [created_at], [afecta_septimo_dia], [estado], [aprobado_por], [documento_respaldo], [clasificacion]) VALUES (5, 5, 'FALTA', '2026-09-08', '2026-09-10', '3.0', '', '2026-10-06 18:54:03.620000', NULL, NULL, NULL, NULL, NULL);
INSERT INTO [movimientos_laborales] ([id], [empleado_id], [tipo], [fecha_inicio], [fecha_fin], [dias_tomados], [observacion], [created_at], [afecta_septimo_dia], [estado], [aprobado_por], [documento_respaldo], [clasificacion]) VALUES (6, 5, 'FALTA', '2026-08-10', '2026-08-16', '7.0', 'Ausencia injustificada reportada', '2026-10-06 19:58:11.277000', False, NULL, NULL, NULL, NULL);
INSERT INTO [movimientos_laborales] ([id], [empleado_id], [tipo], [fecha_inicio], [fecha_fin], [dias_tomados], [observacion], [created_at], [afecta_septimo_dia], [estado], [aprobado_por], [documento_respaldo], [clasificacion]) VALUES (7, 3, 'VACACIONES', '2026-07-15', '2026-07-29', '15.0', '', '2026-10-06 20:43:30.600000', False, NULL, NULL, NULL, NULL);
SET IDENTITY_INSERT [movimientos_laborales] OFF;
GO

-- Datos para [nomina] (3 registros)
SET IDENTITY_INSERT [nomina] ON;
INSERT INTO [nomina] ([id], [periodo_mes], [periodo_anio], [fecha_generacion], [total_ingresos], [total_deducciones], [total_neto], [inss_patronal_total], [provision_vac_total], [provision_agui_total], [estado], [inatec_patronal_total]) VALUES (2, 8, 2026, '2026-09-06 13:55:24.290000', '21200.00', '1941.40', '19258.60', '4678.00', '1766.67', '1766.67', 'CERRADA', '184.00');
INSERT INTO [nomina] ([id], [periodo_mes], [periodo_anio], [fecha_generacion], [total_ingresos], [total_deducciones], [total_neto], [inss_patronal_total], [provision_vac_total], [provision_agui_total], [estado], [inatec_patronal_total]) VALUES (3, 9, 2026, '2026-09-06 14:18:24.810000', '61500.00', '6634.25', '54865.75', '13837.50', '5125.00', '5125.00', 'CERRADA', NULL);
INSERT INTO [nomina] ([id], [periodo_mes], [periodo_anio], [fecha_generacion], [total_ingresos], [total_deducciones], [total_neto], [inss_patronal_total], [provision_vac_total], [provision_agui_total], [estado], [inatec_patronal_total]) VALUES (10, 7, 2026, '2026-10-06 20:30:38.847000', '12500.00', '1368.75', '11131.25', '2687.50', '1041.67', '1041.67', 'CERRADA', '250.00');
SET IDENTITY_INSERT [nomina] OFF;
GO

-- Datos para [pagos_nomina] (3 registros)
SET IDENTITY_INSERT [pagos_nomina] ON;
INSERT INTO [pagos_nomina] ([id], [nomina_id], [empleado_id], [monto_pagado], [fecha_pago], [metodo_pago], [numero_referencia], [comprobante], [estado], [observaciones], [registrado_por]) VALUES (1, 1, 1, '11160.00', '2026-10-13 20:47:29.480000', 'Transferencia Bancaria', 'TRF-BAC-2026-001', NULL, 'Confirmado', 'Pago de nómina ordinaria quincenal', 'Administrador');
INSERT INTO [pagos_nomina] ([id], [nomina_id], [empleado_id], [monto_pagado], [fecha_pago], [metodo_pago], [numero_referencia], [comprobante], [estado], [observaciones], [registrado_por]) VALUES (2, 1, 2, '9300.00', '2026-10-13 20:47:29.480000', 'Transferencia Bancaria', 'TRF-BAC-2026-002', NULL, 'Confirmado', 'Pago de nómina ordinaria quincenal', 'Administrador');
INSERT INTO [pagos_nomina] ([id], [nomina_id], [empleado_id], [monto_pagado], [fecha_pago], [metodo_pago], [numero_referencia], [comprobante], [estado], [observaciones], [registrado_por]) VALUES (3, 1, 3, '11625.00', '2026-10-13 20:47:29.480000', 'Transferencia Bancaria', 'TRF-BAC-2026-003', NULL, 'Confirmado', 'Pago de nómina ordinaria quincenal', 'Administrador');
SET IDENTITY_INSERT [pagos_nomina] OFF;
GO

-- Datos para [parametros_laborales] (7 registros)
SET IDENTITY_INSERT [parametros_laborales] ON;
INSERT INTO [parametros_laborales] ([id], [codigo], [nombre], [valor], [unidad], [descripcion], [referencia_legal], [fecha_vigencia], [usuario_modificacion]) VALUES (1, 'INSS_LABORAL', 'Aporte INSS Laboral', '7.0000', '%', 'Deducción salarial obligatoria del trabajador', 'Ley de Seguridad Social Art. 16', '2026-10-13', 'Administrador');
INSERT INTO [parametros_laborales] ([id], [codigo], [nombre], [valor], [unidad], [descripcion], [referencia_legal], [fecha_vigencia], [usuario_modificacion]) VALUES (2, 'INSS_PATRONAL', 'Aporte INSS Patronal', '21.5000', '%', 'Aporte patronal de seguridad social', 'Ley de Seguridad Social Art. 17', '2026-10-13', 'Administrador');
INSERT INTO [parametros_laborales] ([id], [codigo], [nombre], [valor], [unidad], [descripcion], [referencia_legal], [fecha_vigencia], [usuario_modificacion]) VALUES (3, 'INATEC_PATRONAL', 'Aporte Patronal INATEC', '2.0000', '%', 'Contribución a capacitación técnica nacional', 'Decreto Creador INATEC', '2026-10-13', 'Administrador');
INSERT INTO [parametros_laborales] ([id], [codigo], [nombre], [valor], [unidad], [descripcion], [referencia_legal], [fecha_vigencia], [usuario_modificacion]) VALUES (4, 'VACACIONES_MES', 'Acumulación de Vacaciones', '2.5000', 'Días/Mes', 'Derecho a 30 días de descanso por año cumplido (15 días cada 6 meses)', 'Art. 76 Ley 185', '2026-10-13', 'Administrador');
INSERT INTO [parametros_laborales] ([id], [codigo], [nombre], [valor], [unidad], [descripcion], [referencia_legal], [fecha_vigencia], [usuario_modificacion]) VALUES (5, 'AGUINALDO_PROV', 'Provisión Décimo Tercer Mes', '8.3333', '%', 'Provisión obligatoria del aguinaldo proporcional anual', 'Art. 93 Ley 185', '2026-10-13', 'Administrador');
INSERT INTO [parametros_laborales] ([id], [codigo], [nombre], [valor], [unidad], [descripcion], [referencia_legal], [fecha_vigencia], [usuario_modificacion]) VALUES (6, 'HORAS_EXTRAS_RECARGO', 'Recargo de Horas Extras', '100.0000', '%', 'Remuneración de horas fuera de jornada ordinaria con 100% de recargo', 'Art. 62 Ley 185', '2026-10-13', 'Administrador');
INSERT INTO [parametros_laborales] ([id], [codigo], [nombre], [valor], [unidad], [descripcion], [referencia_legal], [fecha_vigencia], [usuario_modificacion]) VALUES (7, 'SALARIO_MINIMO_COMERCIO', 'Salario Mínimo Comercio', '6672.0000', 'C$', 'Salario mínimo legal aplicable al sector comercio en Masatepe', 'Comisión Nacional del Salario Mínimo', '2026-10-13', 'Administrador');
SET IDENTITY_INSERT [parametros_laborales] OFF;
GO

-- Datos para [permisos] (31 registros)
SET IDENTITY_INSERT [permisos] ON;
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (1, 1, 'administracion_total', 'Acceso total y configuración del sistema');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (2, 1, 'usuarios_gestionar', 'Administrar usuarios y accesos');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (3, 1, 'roles_permisos_gestionar', 'Asignar roles y permisos');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (4, 1, 'reportes_gerenciales_ver', 'Visualización de reportes ejecutivos y auditoría');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (5, 1, 'auditoria_sesiones_ver', 'Consultar historial y sesiones activas');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (6, 2, 'ventas_crear', 'Emitir facturas y ventas en mostrador');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (7, 2, 'caja_operar', 'Abrir caja, cobrar y realizar corte de caja');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (8, 2, 'clientes_gestionar', 'Consultar y registrar clientes');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (9, 2, 'productos_consultar', 'Consultar catálogo, precios y existencias');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (10, 3, 'productos_gestionar', 'Crear y actualizar repuestos y precios');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (11, 3, 'kardex_consultar', 'Consultar movimientos y existencias');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (12, 3, 'ajustes_inventario_crear', 'Registrar ajustes de entrada y salida de stock');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (13, 4, 'cuentas_contables_gestionar', 'Administrar catálogo de cuentas contables');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (14, 4, 'asientos_contables_registrar', 'Registrar asientos en el libro diario');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (15, 4, 'estados_financieros_ver', 'Generar balance general, estado de resultados y mayor');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (16, 4, 'reportes_fiscales_ver', 'Consultar reportes de IVA y retenciones');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (18, 1002, 'inventario_supervisar', 'Supervisión de stock, almacén y abastecimiento');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (19, 1002, 'compras_supervisar', 'Aprobación de compras y control de proveedores');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (20, 1002, 'ventas_supervisar', 'Monitoreo de rendimiento de ventas y mostrador');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (21, 1003, 'finanzas_supervisar', 'Supervisión de balances, costos y rentabilidad');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (22, 1003, 'rrhh_supervisar', 'Supervisión de planilla y gestión de personal');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (23, 1003, 'reportes_gerenciales_ver', 'Visualización de reportes ejecutivos');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (24, 1004, 'compras_registrar', 'Registrar órdenes de compra y facturas de proveedores');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (25, 1004, 'proveedores_gestionar', 'Administrar catálogo y cuentas de proveedores');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (26, 1004, 'recepciones_compra_registrar', 'Confirmar recepción física de mercadería');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (27, 1001, 'empleados_gestionar', 'Registrar y editar expedientes de empleados');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (28, 1001, 'cargos_gestionar', 'Administrar cargos y salarios');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (29, 1001, 'movimientos_laborales_registrar', 'Registrar faltas, permisos y justificaciones');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (30, 1001, 'vacaciones_gestionar', 'Registrar y aprobar solicitudes de vacaciones');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (31, 1001, 'nomina_procesar', 'Calcular y generar nómina quincenal/mensual');
INSERT INTO [permisos] ([id], [rol_id], [nombre], [descripcion]) VALUES (32, 1001, 'colillas_pago_emitir', 'Generar e imprimir colillas de pago');
SET IDENTITY_INSERT [permisos] OFF;
GO

-- Datos para [productos] (235 registros)
SET IDENTITY_INSERT [productos] ON;
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (1, 'MAN037', NULL, 5, 'AMORTIGUADOR AKT TT150-180 - GENESIS SX200 VINI', NULL, NULL, NULL, NULL, '1661.75', '2326.45', 3, 5, True, '2026-09-17 16:22:40.463000', '2026-09-17 16:22:40.463000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (2, 'AMO026', NULL, 5, 'AMORTIGUADORES GN125H VINI', NULL, NULL, NULL, NULL, '833.00', '1166.20', 5, 5, True, '2026-09-17 16:22:40.470000', '2026-09-17 16:22:40.470000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (3, 'AMO033', NULL, 4, 'AMORTIGUADORES PULSAR 135-DISCOVER VINI', NULL, NULL, NULL, NULL, '1462.00', '2046.80', 5, 5, True, '2026-09-17 16:22:40.473000', '2026-09-17 16:22:40.473000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (4, 'Ani088', NULL, 1, 'ANILLOS DE PISTON AG200 A MEDIDA 0.25 VINI', NULL, NULL, NULL, NULL, '127.50', '178.50', 10, 5, True, '2026-09-17 16:22:40.480000', '2026-09-17 16:22:40.480000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (5, 'Ani089', NULL, 1, 'ANILLOS DE PISTON AG200 A MEDIDA 0.50 VINI', NULL, NULL, NULL, NULL, '127.50', '178.50', 10, 5, True, '2026-09-17 16:22:40.480000', '2026-09-17 16:22:40.480000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (6, 'Ani059', NULL, 1, 'ANILLOS DE PISTON AG200-UM200-RAYBAR200 (67MM*15MM) STD VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 10, 5, True, '2026-09-17 16:22:40.490000', '2026-09-17 16:22:40.490000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (7, 'Ani086', NULL, 1, 'ANILLOS DE PISTON CG150 STD VINI', NULL, NULL, NULL, NULL, '85.00', '119.00', 20, 5, True, '2026-09-17 16:22:40.493000', '2026-09-17 16:22:40.493000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (8, 'Ani060', NULL, 1, 'ANILLOS DE PISTON CG200-WY200 63.5 MM STD VINI', NULL, NULL, NULL, NULL, '93.50', '130.90', 20, 5, True, '2026-09-17 16:22:40.500000', '2026-09-17 16:22:40.500000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (9, 'Ani061', NULL, 1, 'ANILLOS DE PISTON GXT200-DR200 66MM STD VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 10, 5, True, '2026-09-17 16:22:40.503000', '2026-09-17 16:22:40.503000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (10, 'Ani018', NULL, 1, 'ANILLOS DE PISTON GY200 69MM-198CM STD VINI', NULL, NULL, NULL, NULL, '106.25', '148.75', 10, 5, True, '2026-09-17 16:22:40.510000', '2026-09-17 16:22:40.510000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (11, 'Ani062', NULL, 1, 'ANILLOS DE PISTON PULSAR 135-XCD125-PLATINA125 STD VINI', NULL, NULL, NULL, NULL, '125.80', '176.12', 20, 5, True, '2026-09-17 16:22:40.533000', '2026-09-17 16:22:40.533000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (12, 'Ani066', NULL, 1, 'ANILLOS DE PISTON PULSAR 180 UG3-UG4 STD VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 20, 5, True, '2026-09-17 16:22:40.557000', '2026-09-17 16:22:40.557000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (13, 'Ani098', NULL, 1, 'ANILLOS DE PISTON PULSAR NS200 STD VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 20, 5, True, '2026-09-17 16:22:40.563000', '2026-09-17 16:22:40.563000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (14, 'ARB050', NULL, 1, 'ARBOL DE LEVAS AKT CR5 180 VINI', NULL, NULL, NULL, NULL, '433.50', '606.90', 10, 5, True, '2026-09-17 16:22:40.573000', '2026-09-17 16:22:40.573000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (15, 'ARB032', NULL, 1, 'ARBOL DE LEVAS CG-GY200 NO BALANZA COMPLETA VINI', NULL, NULL, NULL, NULL, '357.00', '499.80', 20, 5, True, '2026-09-17 16:22:40.583000', '2026-09-17 16:22:40.583000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (16, 'ARB042', NULL, 1, 'ARBOL DE LEVAS PULSAR 135 VINI', NULL, NULL, NULL, NULL, '365.50', '511.70', 20, 5, True, '2026-09-17 16:22:40.593000', '2026-09-17 16:22:40.593000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (17, 'ARB058', NULL, 1, 'ARBOL DE LEVAS SCOOTER 125-150 VINI', NULL, NULL, NULL, NULL, '272.00', '380.80', 10, 5, True, '2026-09-17 16:22:40.673000', '2026-09-17 16:22:40.673000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (18, 'ARB051', NULL, 1, 'ARBOL DE LEVAS WY200-JH150 MOTOR CADENA BUSHING VINI', NULL, NULL, NULL, NULL, '331.50', '464.10', 10, 5, True, '2026-09-17 16:22:40.683000', '2026-09-17 16:22:40.683000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (19, 'ASI015', NULL, 8, 'ASIENTO CG RACING MODIFIC AZUL VINI', NULL, NULL, NULL, NULL, '841.50', '1178.10', 4, 5, True, '2026-09-17 16:22:40.687000', '2026-09-17 16:22:40.687000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (20, 'Asi023', NULL, 8, 'ASIENTO CG RACING MODIFIED VINI', NULL, NULL, NULL, NULL, '765.00', '1071.00', 5, 5, True, '2026-09-17 16:22:40.693000', '2026-09-17 16:22:40.693000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (21, 'Asi021', NULL, 8, 'ASIENTO RAYBAR 200-NXR125 BROSS-UM DSR 2026 VINI', NULL, NULL, NULL, NULL, '697.00', '975.80', 2, 5, True, '2026-09-17 16:22:40.700000', '2026-09-17 16:22:40.700000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (22, 'BLN060', NULL, 1, 'BALANCINES DE MOTOR AN125 VINI', NULL, NULL, NULL, NULL, '119.00', '166.60', 10, 5, True, '2026-09-17 16:22:40.700000', '2026-09-17 16:22:40.700000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (23, 'BLN061', NULL, 1, 'BALANCINES DE MOTOR APACHE160-180 VINI', NULL, NULL, NULL, NULL, '289.00', '404.60', 5, 5, True, '2026-09-17 16:22:40.707000', '2026-09-17 16:22:40.707000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (24, 'BLN041', NULL, 1, 'BALANCINES DE MOTOR COMPLETOS HJ125-CG150-CG200 VINI', NULL, NULL, NULL, NULL, '144.50', '202.30', 15, 5, True, '2026-09-17 16:22:40.707000', '2026-09-17 16:22:40.707000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (25, 'BLN042', NULL, 1, 'BALANCINES DE MOTOR WY125-JH150-WY200 VINI', NULL, NULL, NULL, NULL, '161.50', '226.10', 15, 5, True, '2026-09-17 16:22:40.710000', '2026-09-17 16:22:40.710000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (26, 'Bal127', NULL, 9, 'BALINERA 6004 2RS VINI', NULL, NULL, NULL, NULL, '38.25', '53.55', 50, 5, True, '2026-09-17 16:22:40.710000', '2026-09-17 16:22:40.710000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (27, 'Bal147', NULL, 9, 'BALINERA 6005 2RS VINI', NULL, NULL, NULL, NULL, '49.30', '69.02', 50, 5, True, '2026-09-17 16:22:40.710000', '2026-09-17 16:22:40.710000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (28, 'Bal148', NULL, 9, 'BALINERA 6006 2RS VINI', NULL, NULL, NULL, NULL, '62.90', '88.06', 50, 5, True, '2026-09-17 16:22:40.710000', '2026-09-17 16:22:40.710000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (29, 'Bal108', NULL, 9, 'BALINERA 6202 2RS VINI', NULL, NULL, NULL, NULL, '32.30', '45.22', 60, 5, True, '2026-09-17 16:22:40.710000', '2026-09-17 16:22:40.710000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (30, 'Bal1013', NULL, 9, 'BALINERA 6204 2RS VINI', NULL, NULL, NULL, NULL, '49.30', '69.02', 50, 5, True, '2026-09-17 16:22:40.713000', '2026-09-17 16:22:40.713000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (31, 'Bal020', NULL, 9, 'BALINERA 6301 2RS VINI', NULL, NULL, NULL, NULL, '38.25', '53.55', 60, 5, True, '2026-09-17 16:22:40.713000', '2026-09-17 16:22:40.713000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (32, 'Bal100', NULL, 9, 'BALINERA 6302 2RS VINI', NULL, NULL, NULL, NULL, '40.80', '57.12', 50, 5, True, '2026-09-17 16:22:40.713000', '2026-09-17 16:22:40.713000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (33, 'Bal125', NULL, 9, 'BALINERA DE CIGUEÑAL 6205 2RS YBR-XTZ VINI', NULL, NULL, NULL, NULL, '86.70', '121.38', 10, 5, True, '2026-09-17 16:22:40.717000', '2026-09-17 16:22:40.717000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (34, 'Bal083', NULL, 9, 'BALINERA DE CIGUEÑAL 63-28 28MM*68MM VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 20, 5, True, '2026-09-17 16:22:40.717000', '2026-09-17 16:22:40.717000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (35, 'Bal084', NULL, 9, 'BALINERA DE CIGUEÑAL 63-28 P5 28MM*72MM VINI', NULL, NULL, NULL, NULL, '165.75', '232.05', 20, 5, True, '2026-09-17 16:22:40.720000', '2026-09-17 16:22:40.720000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (36, 'Bal082', NULL, 9, 'BALINERA DE CIGUEÑAL PULSAR135-BOXER-DISC-PLATINA VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 20, 5, True, '2026-09-17 16:22:40.723000', '2026-09-17 16:22:40.723000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (37, 'Bal149', NULL, 2, 'BALINERA DE MOTOR DE ARRANQUE CG HK1010 VINI', NULL, NULL, NULL, NULL, '17.85', '24.99', 30, 5, True, '2026-09-17 16:22:40.723000', '2026-09-17 16:22:40.723000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (38, 'Bal079', NULL, 9, 'BALINERA DE PROPULSOR CG200 NK 152312 VINI', NULL, NULL, NULL, NULL, '34.00', '47.60', 30, 5, True, '2026-09-17 16:22:40.723000', '2026-09-17 16:22:40.723000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (39, 'BAN005', NULL, 3, 'BANDA DE TRACCION SCOOTER GY6125 835x20x30 VINI', NULL, NULL, NULL, NULL, '225.25', '315.35', 20, 5, True, '2026-09-17 16:22:40.730000', '2026-09-17 16:22:40.730000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (40, 'Bie066', NULL, 1, 'BIELA KIT AKT150TT-NKD125 NXR125 BROSS-XR125L VINI', NULL, NULL, NULL, NULL, '348.50', '487.90', 10, 5, True, '2026-09-17 16:22:40.730000', '2026-09-17 16:22:40.730000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (41, 'Bie043', NULL, 1, 'BIELA KIT GXT200-DR200 VINI', NULL, NULL, NULL, NULL, '527.00', '737.80', 10, 5, True, '2026-09-17 16:22:40.737000', '2026-09-17 16:22:40.737000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (42, 'Bie053', NULL, 1, 'BIELA KIT PULSAR135-PLATINA125-BM150 VINI', NULL, NULL, NULL, NULL, '365.50', '511.70', 10, 5, True, '2026-09-17 16:22:40.737000', '2026-09-17 16:22:40.737000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (43, 'Bie063', NULL, 1, 'BIELA KIT XCD125-PLATINA 125-DISCOVER 125 ST VINI', NULL, NULL, NULL, NULL, '323.00', '452.20', 10, 5, True, '2026-09-17 16:22:40.740000', '2026-09-17 16:22:40.740000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (44, 'Bie040', NULL, 1, 'BIELA KIT XL185-XL125-CG150-CG125 VINI', NULL, NULL, NULL, NULL, '323.00', '452.20', 10, 5, True, '2026-09-17 16:22:40.740000', '2026-09-17 16:22:40.740000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (45, 'Bie048', NULL, 1, 'BIELA KIT YBR125-XTZ125 VINI', NULL, NULL, NULL, NULL, '331.50', '464.10', 10, 5, True, '2026-09-17 16:22:40.743000', '2026-09-17 16:22:40.743000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (46, 'Bie068', NULL, 1, 'BIELA KIT YUMBO200-UM200-PULSAR180 VINI', NULL, NULL, NULL, NULL, '408.00', '571.20', 5, 5, True, '2026-09-17 16:22:40.747000', '2026-09-17 16:22:40.747000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (47, 'BOB098', NULL, 2, 'BOBINA DE ALTA CG-AKT TT150-EVO150 1 LINEA VINI', NULL, NULL, NULL, NULL, '119.00', '166.60', 20, 5, True, '2026-09-17 16:22:40.747000', '2026-09-17 16:22:40.747000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (48, 'BOB079', NULL, 2, 'BOBINA DE MOTOR AKT CR5 VINI', NULL, NULL, NULL, NULL, '578.00', '809.20', 10, 5, True, '2026-09-17 16:22:40.747000', '2026-09-17 16:22:40.747000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (49, 'BOB058', NULL, 2, 'BOBINA DE MOTOR CG 8X3 MOTOR VARILLA VINI', NULL, NULL, NULL, NULL, '408.00', '571.20', 10, 5, True, '2026-09-17 16:22:40.750000', '2026-09-17 16:22:40.750000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (50, 'BOB059', NULL, 2, 'BOBINA DE MOTOR DISCOVER 125 ST VINI', NULL, NULL, NULL, NULL, '510.00', '714.00', 5, 5, True, '2026-09-17 16:22:40.750000', '2026-09-17 16:22:40.750000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (51, 'BOB073', NULL, 2, 'BOBINA DE MOTOR GN125H-GXT200 VINI', NULL, NULL, NULL, NULL, '578.00', '809.20', 5, 5, True, '2026-09-17 16:22:40.757000', '2026-09-17 16:22:40.757000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (52, 'BOM039', NULL, 1, 'BOMBA DE FRENO DELANTERA HJ125-GN125 BLANCA VINI', NULL, NULL, NULL, NULL, '233.75', '327.25', 10, 5, True, '2026-09-17 16:22:40.757000', '2026-09-17 16:22:40.757000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (53, 'BOM046', NULL, 1, 'BOMBA DE FRENO DELANTERA PULSAR 135-180-220 VINI', NULL, NULL, NULL, NULL, '314.50', '440.30', 10, 5, True, '2026-09-17 16:22:40.757000', '2026-09-17 16:22:40.757000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (54, 'BOM066', NULL, 1, 'BOMBA DE FRENO DELANTERA XL-GY200 NEGRA VINI', NULL, NULL, NULL, NULL, '255.00', '357.00', 10, 5, True, '2026-09-17 16:22:40.757000', '2026-09-17 16:22:40.757000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (55, 'BOM087', NULL, 1, 'BOMBA DE FRENO TRASERA COMPLETA PULSAR NS200-RS200-180-220 VINI', NULL, NULL, NULL, NULL, '254.15', '355.81', 10, 5, True, '2026-09-17 16:22:40.760000', '2026-09-17 16:22:40.760000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (56, 'BOM067', NULL, 1, 'BOMBA DE FRENO TRASERA DAYUN150-CON DEPOSITO VINI', NULL, NULL, NULL, NULL, '272.00', '380.80', 10, 5, True, '2026-09-17 16:22:40.760000', '2026-09-17 16:22:40.760000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (57, 'BOM088', NULL, 1, 'BOMBA DE LUBRICACION AX100 VINI', NULL, NULL, NULL, NULL, '552.50', '773.50', 5, 5, True, '2026-09-17 16:22:40.760000', '2026-09-17 16:22:40.760000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (58, 'BOM044', NULL, 1, 'BOMBA DE LUBRICACION CG150 39D C-ORING VINI', NULL, NULL, NULL, NULL, '114.75', '160.65', 30, 5, True, '2026-09-17 16:22:40.763000', '2026-09-17 16:22:40.763000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (59, 'BOM073', NULL, 1, 'BOMBA DE LUBRICACION YUMBO 200-YARA 200 37D VINI', NULL, NULL, NULL, NULL, '110.50', '154.70', 20, 5, True, '2026-09-17 16:22:40.763000', '2026-09-17 16:22:40.763000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (60, 'BUJ122', NULL, 2, 'BOMBILLO DE PIDEVIAS 12V VINI', NULL, NULL, NULL, NULL, '5.06', '7.08', 100, 5, True, '2026-09-17 16:22:40.767000', '2026-09-17 16:22:40.767000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (61, 'BUJ081', NULL, 2, 'BOMBILLO DE STOP 12V VINI', NULL, NULL, NULL, NULL, '7.23', '10.12', 100, 5, True, '2026-09-17 16:22:40.770000', '2026-09-17 16:22:40.770000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (62, 'BUC036', NULL, 5, 'BUSHING DE TIJERA KIT + EJE AKT TT150-TT180 VINI', NULL, NULL, NULL, NULL, '187.00', '261.80', 10, 5, True, '2026-09-17 16:22:40.773000', '2026-09-17 16:22:40.773000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (63, 'BUC059', NULL, 5, 'BUSHING DE TIJERA KIT + EJE GY200-JH125L-XL185S VINI', NULL, NULL, NULL, NULL, '144.50', '202.30', 10, 5, True, '2026-09-17 16:22:40.773000', '2026-09-17 16:22:40.773000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (64, 'BUC066', NULL, 5, 'BUSHING DE TIJERA KIT + EJE RAYBAR 200 VINI', NULL, NULL, NULL, NULL, '187.00', '261.80', 10, 5, True, '2026-09-17 16:22:40.773000', '2026-09-17 16:22:40.773000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (65, 'CAB193', NULL, 7, 'CABLE ACELERADOR CG-WY VINI', NULL, NULL, NULL, NULL, '44.20', '61.88', 30, 5, True, '2026-09-17 16:22:40.773000', '2026-09-17 16:22:40.773000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (66, 'CAB211', NULL, 7, 'CABLE ACELERADOR GIXXER 150 VINI', NULL, NULL, NULL, NULL, '72.25', '101.15', 20, 5, True, '2026-09-17 16:22:40.777000', '2026-09-17 16:22:40.777000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (67, 'CAB187', NULL, 7, 'CABLE ACELERADOR GXT200 VINI', NULL, NULL, NULL, NULL, '44.20', '61.88', 20, 5, True, '2026-09-17 16:22:40.777000', '2026-09-17 16:22:40.777000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (68, 'CAB143', NULL, 7, 'CABLE ACELERADOR PULSAR 135 VINI', NULL, NULL, NULL, NULL, '46.75', '65.45', 30, 5, True, '2026-09-17 16:22:40.777000', '2026-09-17 16:22:40.777000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (69, 'CAB144', NULL, 7, 'CABLE ACELERADOR PULSAR180-220 VINI', NULL, NULL, NULL, NULL, '46.75', '65.45', 30, 5, True, '2026-09-17 16:22:40.780000', '2026-09-17 16:22:40.780000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (70, 'CAB212', NULL, 3, 'CABLE CLUTCH CGL125 VINI', NULL, NULL, NULL, NULL, '46.75', '65.45', 20, 5, True, '2026-09-17 16:22:40.780000', '2026-09-17 16:22:40.780000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (71, 'CAB213', NULL, 3, 'CABLE CLUTCH GN125H VINI', NULL, NULL, NULL, NULL, '55.25', '77.35', 20, 5, True, '2026-09-17 16:22:40.780000', '2026-09-17 16:22:40.780000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (72, 'CAB314', NULL, 3, 'CABLE CLUTCH HJ125-7 VINI', NULL, NULL, NULL, NULL, '46.75', '65.45', 30, 5, True, '2026-09-17 16:22:40.783000', '2026-09-17 16:22:40.783000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (73, 'CAB131', NULL, 3, 'CABLE CLUTCH XTZ125 (2012-2018) C-POLVERA VINI', NULL, NULL, NULL, NULL, '68.00', '95.20', 10, 5, True, '2026-09-17 16:22:40.787000', '2026-09-17 16:22:40.787000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (74, 'CAB190', NULL, 3, 'CABLE CLUTCH YBR125 VINI', NULL, NULL, NULL, NULL, '83.30', '116.62', 20, 5, True, '2026-09-17 16:22:40.790000', '2026-09-17 16:22:40.790000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (75, 'CAB090', NULL, 2, 'CABLE DE BOBINA ALTA UNIVERSAL ROLLO', NULL, NULL, NULL, NULL, '246.50', '345.10', 100, 5, True, '2026-09-17 16:22:40.793000', '2026-09-17 16:22:40.793000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (76, 'CAB156', NULL, 4, 'CABLE FRENO YBR125 VINI', NULL, NULL, NULL, NULL, '83.30', '116.62', 10, 5, True, '2026-09-17 16:22:40.797000', '2026-09-17 16:22:40.797000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (77, 'CAD081', NULL, 3, 'CADENA DE LUBRICACION RAYBAR200-RKS150 CONTRAPESA VINI', NULL, NULL, NULL, NULL, '59.50', '83.30', 20, 5, True, '2026-09-17 16:22:40.803000', '2026-09-17 16:22:40.803000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (78, 'CAD032', NULL, 1, 'CADENA DE TIEMPO AKT CR5 VINI', NULL, NULL, NULL, NULL, '119.00', '166.60', 20, 5, True, '2026-09-17 16:22:40.810000', '2026-09-17 16:22:40.810000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (79, 'CAD094', NULL, 1, 'CADENA DE TIEMPO APACHE 150-160-180 (409H 94L) VINI', NULL, NULL, NULL, NULL, '161.50', '226.10', 20, 5, True, '2026-09-17 16:22:40.813000', '2026-09-17 16:22:40.813000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (80, 'CAD095', NULL, 1, 'CADENA DE TIEMPO CRF230-XT250 SERROW (2X3H 104L) VINI', NULL, NULL, NULL, NULL, '114.75', '160.65', 10, 5, True, '2026-09-17 16:22:40.820000', '2026-09-17 16:22:40.820000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (81, 'CAD062', NULL, 1, 'CADENA DE TIEMPO PULSAR NS200-AS200-RS200(94L) VINI', NULL, NULL, NULL, NULL, '161.50', '226.10', 20, 5, True, '2026-09-17 16:22:40.823000', '2026-09-17 16:22:40.823000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (82, 'CAD074', NULL, 1, 'CADENA DE TIEMPO SCOOTER-150F-22 (90L) VINI', NULL, NULL, NULL, NULL, '127.50', '178.50', 20, 5, True, '2026-09-17 16:22:40.827000', '2026-09-17 16:22:40.827000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (83, 'CAD071', NULL, 1, 'CADENA DE TIEMPO XTZ125-YBR125 2006 2X3L 90L ORUGA VINI', NULL, NULL, NULL, NULL, '127.50', '178.50', 20, 5, True, '2026-09-17 16:22:40.830000', '2026-09-17 16:22:40.830000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (84, 'CAD096', NULL, 1, 'CADENA DE TIEMPO YUMBO200 (3X4H 100L) VINI', NULL, NULL, NULL, NULL, '144.50', '202.30', 20, 5, True, '2026-09-17 16:22:40.837000', '2026-09-17 16:22:40.837000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (85, 'CAD061', NULL, 3, 'CADENA DE TRACCION 520X120L EXTRA REFORZADA DORADA VINI', NULL, NULL, NULL, NULL, '344.25', '481.95', 20, 5, True, '2026-09-17 16:22:40.840000', '2026-09-17 16:22:40.840000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (86, 'CAJ001', NULL, 3, 'CAJA DE CAMBIOS AKT180TT-CR5 (6 CAMBIOS) VINI', NULL, NULL, NULL, NULL, '1249.50', '1749.30', 5, 5, True, '2026-09-17 16:22:40.843000', '2026-09-17 16:22:40.843000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (87, 'CAJ023', NULL, 3, 'CAJA DE CAMBIOS CG125-CG150-AKT 150 VINI', NULL, NULL, NULL, NULL, '935.00', '1309.00', 5, 5, True, '2026-09-17 16:22:40.850000', '2026-09-17 16:22:40.850000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (88, 'CAJ029', NULL, 3, 'CAJA DE CAMBIOS CG200-RAYBAR200-250-UM200-CONTRAPESA VINI', NULL, NULL, NULL, NULL, '1190.00', '1666.00', 5, 5, True, '2026-09-17 16:22:40.857000', '2026-09-17 16:22:40.857000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (89, 'CAJ046', NULL, 3, 'CAJA DE CAMBIOS GXT200 VINI', NULL, NULL, NULL, NULL, '2125.00', '2975.00', 5, 5, True, '2026-09-17 16:22:40.860000', '2026-09-17 16:22:40.860000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (90, 'CAJ047', NULL, 3, 'CAJA DE CAMBIOS PULSAR NS125-BOXER150X MODERNA VINI', NULL, NULL, NULL, NULL, '1377.00', '1927.80', 2, 5, True, '2026-09-17 16:22:40.867000', '2026-09-17 16:22:40.867000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (91, 'ARA050', NULL, 3, 'CANASTA CLUTCH AKT CR5-TT 180 (SOLA) VINI', NULL, NULL, NULL, NULL, '442.00', '618.80', 10, 5, True, '2026-09-17 16:22:40.870000', '2026-09-17 16:22:40.870000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (92, 'ARA051', NULL, 3, 'CANASTA CLUTCH CG125-CG150-RKS150 73T COMPLETA VINI', NULL, NULL, NULL, NULL, '637.50', '892.50', 5, 5, True, '2026-09-17 16:22:40.873000', '2026-09-17 16:22:40.873000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (93, 'DIR326', NULL, 8, 'CAPA CUBRE MOTO PREMIUM UNIVERSAL VINI', NULL, NULL, NULL, NULL, '382.50', '535.50', 3, 5, True, '2026-09-17 16:22:40.880000', '2026-09-17 16:22:40.880000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (94, 'JUB024', NULL, 2, 'CARBONES MOTOR ARRANQUE CBF150-XR150L VINI', NULL, NULL, NULL, NULL, '55.25', '77.35', 20, 5, True, '2026-09-17 16:22:40.887000', '2026-09-17 16:22:40.887000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (95, 'JUB040', NULL, 2, 'CARBONES MOTOR ARRANQUE CG125-150-200 VINI', NULL, NULL, NULL, NULL, '55.25', '77.35', 20, 5, True, '2026-09-17 16:22:40.887000', '2026-09-17 16:22:40.887000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (96, 'JUB028', NULL, 2, 'CARBONES MOTOR ARRANQUE GXT200-GN125 VINI', NULL, NULL, NULL, NULL, '68.00', '95.20', 20, 5, True, '2026-09-17 16:22:40.893000', '2026-09-17 16:22:40.893000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (97, 'JUB041', NULL, 2, 'CARBONES MOTOR ARRANQUE PULSAR NS200 VINI', NULL, NULL, NULL, NULL, '55.25', '77.35', 20, 5, True, '2026-09-17 16:22:40.893000', '2026-09-17 16:22:40.893000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (98, 'CAR050', NULL, 6, 'CARBURADOR CG150 PZ27 VINI', NULL, NULL, NULL, NULL, '459.00', '642.60', 10, 5, True, '2026-09-17 16:22:40.897000', '2026-09-17 16:22:40.897000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (99, 'CAR047', NULL, 6, 'CARBURADOR CG200-XL200-DAKAR200 VINI', NULL, NULL, NULL, NULL, '484.50', '678.30', 10, 5, True, '2026-09-17 16:22:40.900000', '2026-09-17 16:22:40.900000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (100, 'CAR069', NULL, 6, 'CARBURADOR GIXXER 150 VINI', NULL, NULL, NULL, NULL, '1955.00', '2737.00', 10, 5, True, '2026-09-17 16:22:40.907000', '2026-09-17 16:22:40.907000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (101, 'CAR070', NULL, 6, 'CARBURADOR SCOOTER GY6150 VINI', NULL, NULL, NULL, NULL, '756.50', '1059.10', 5, 5, True, '2026-09-17 16:22:40.910000', '2026-09-17 16:22:40.910000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (102, 'CAR046', NULL, 6, 'CARBURADOR XL125-185-CG125 VINI', NULL, NULL, NULL, NULL, '467.50', '654.50', 10, 5, True, '2026-09-17 16:22:40.913000', '2026-09-17 16:22:40.913000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (103, 'CDI027', NULL, 9, 'CEPO PARA CEREBRO REDONDO 6L (2PCS) VINI', NULL, NULL, NULL, NULL, '16.15', '22.61', 50, 5, True, '2026-09-17 16:22:40.917000', '2026-09-17 16:22:40.917000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (104, 'CDI049', NULL, 2, 'CEREBRO CDI AK CR5-AK180 TT-180CRX VINI', NULL, NULL, NULL, NULL, '165.75', '232.05', 3, 5, True, '2026-09-17 16:22:40.920000', '2026-09-17 16:22:40.920000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (105, 'CDI051', NULL, 2, 'CEREBRO CDI DAYUN 150 CUADRADO CORRIENTE DIRECTA C-CABLE VINI', NULL, NULL, NULL, NULL, '165.75', '232.05', 30, 5, True, '2026-09-17 16:22:40.923000', '2026-09-17 16:22:40.923000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (106, 'CDI053', NULL, 2, 'CEREBRO CDI GXT200-GN125H-DR200 8L D-C VINI', NULL, NULL, NULL, NULL, '433.50', '606.90', 5, 5, True, '2026-09-17 16:22:40.927000', '2026-09-17 16:22:40.927000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (107, 'CDI032', NULL, 2, 'CEREBRO CDI NXR125 REDONDO CORRIENTE DIRECTA C-CABLE VINI', NULL, NULL, NULL, NULL, '161.50', '226.10', 20, 5, True, '2026-09-17 16:22:40.930000', '2026-09-17 16:22:40.930000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (108, 'CDI034', NULL, 2, 'CEREBRO CDI PULSAR 135 VINI', NULL, NULL, NULL, NULL, '408.00', '571.20', 5, 5, True, '2026-09-17 16:22:40.933000', '2026-09-17 16:22:40.933000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (109, 'CDI055', NULL, 2, 'CEREBRO CDI PULSAR150-180 UG4', NULL, NULL, NULL, NULL, '357.00', '499.80', 5, 5, True, '2026-09-17 16:22:40.943000', '2026-09-17 16:22:40.943000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (110, 'CDI059', NULL, 2, 'CEREBRO CDI YBR 125 VINI', NULL, NULL, NULL, NULL, '280.50', '392.70', 5, 5, True, '2026-09-17 16:22:40.950000', '2026-09-17 16:22:40.950000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (111, 'CIL086', NULL, 1, 'CILINDRO COMPLETO AKT TTR150-EVO 150NE BULON 13 62M VINI', NULL, NULL, NULL, NULL, '1054.00', '1475.60', 10, 5, True, '2026-09-17 16:22:40.953000', '2026-09-17 16:22:40.953000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (112, 'CIL160', NULL, 1, 'CILINDRO COMPLETO APACHE 160 RTR 62M 15M 2V VINI', NULL, NULL, NULL, NULL, '1419.50', '1987.30', 3, 5, True, '2026-09-17 16:22:40.957000', '2026-09-17 16:22:40.957000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (113, 'CIL094', NULL, 1, 'CILINDRO COMPLETO CG125-HJ125-7 56M-15M VINI', NULL, NULL, NULL, NULL, '977.50', '1368.50', 8, 5, True, '2026-09-17 16:22:40.960000', '2026-09-17 16:22:40.960000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (114, 'CIL087', NULL, 1, 'CILINDRO COMPLETO CG150 GRIS BULON 15 62-15M VINI', NULL, NULL, NULL, NULL, '1079.50', '1511.30', 8, 5, True, '2026-09-17 16:22:40.967000', '2026-09-17 16:22:40.967000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (115, 'CIL144', NULL, 1, 'CILINDRO COMPLETO CG200 63.5MM-15M VINI', NULL, NULL, NULL, NULL, '1122.00', '1570.80', 8, 5, True, '2026-09-17 16:22:40.970000', '2026-09-17 16:22:40.970000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (116, 'CIL161', NULL, 1, 'CILINDRO COMPLETO CRF230-LONCIN250 SX3-TRUENO GRIS 65.5-15B VINI', NULL, NULL, NULL, NULL, '1487.50', '2082.50', 2, 5, True, '2026-09-17 16:22:40.977000', '2026-09-17 16:22:40.977000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (117, 'CIL162', NULL, 1, 'CILINDRO COMPLETO GY6150 SCOOTER 57-15M VINI', NULL, NULL, NULL, NULL, '918.00', '1285.20', 5, 5, True, '2026-09-17 16:22:40.980000', '2026-09-17 16:22:40.980000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (118, 'CIL166', NULL, 1, 'CILINDRO COMPLETO JH125-WY125 CADENA ALTA COMPRESION 56.5-B15 VINI', NULL, NULL, NULL, NULL, '1096.50', '1535.10', 5, 5, True, '2026-09-17 16:22:40.983000', '2026-09-17 16:22:40.983000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (119, 'CIL163', NULL, 1, 'CILINDRO COMPLETO LUCKY110 HJ110 52-13 VINI', NULL, NULL, NULL, NULL, '892.50', '1249.50', 3, 5, True, '2026-09-17 16:22:40.990000', '2026-09-17 16:22:40.990000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (120, 'CIL143', NULL, 1, 'CILINDRO COMPLETO PLATINA 125 14-54M-2V VINI', NULL, NULL, NULL, NULL, '1326.00', '1856.40', 5, 5, True, '2026-09-17 16:22:40.990000', '2026-09-17 16:22:40.990000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (121, 'CIL146', NULL, 1, 'CILINDRO COMPLETO PULSAR 135 54MM-14B-4V VINI', NULL, NULL, NULL, NULL, '1185.75', '1660.05', 10, 5, True, '2026-09-17 16:22:40.997000', '2026-09-17 16:22:40.997000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (122, 'CIL138', NULL, 1, 'CILINDRO COMPLETO RAYBAR 250 NEGRO 65.5MM-15M VINI', NULL, NULL, NULL, NULL, '1190.00', '1666.00', 5, 5, True, '2026-09-17 16:22:41', '2026-09-17 16:22:41');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (123, 'CIL164', NULL, 1, 'CILINDRO COMPLETO SCOOTER 125 52-15 VINI', NULL, NULL, NULL, NULL, '833.00', '1166.20', 5, 5, True, '2026-09-17 16:22:41.003000', '2026-09-17 16:22:41.003000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (124, 'CIL129', NULL, 1, 'CILINDRO COMPLETO UM200-RAYBAR200 67MM GRIS 16B VINI', NULL, NULL, NULL, NULL, '1232.50', '1725.50', 3, 5, True, '2026-09-17 16:22:41.010000', '2026-09-17 16:22:41.010000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (125, 'CIL165', NULL, 1, 'CILINDRO COMPLETO WY150-JH150 62MM-15 VINI', NULL, NULL, NULL, NULL, '1105.00', '1547.00', 5, 5, True, '2026-09-17 16:22:41.017000', '2026-09-17 16:22:41.017000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (126, 'CUN038', NULL, 5, 'CUNAS DE POSTE CG-XL125-XL185-AKT125 CONICA VINI', NULL, NULL, NULL, NULL, '76.50', '107.10', 30, 5, True, '2026-09-17 16:22:41.017000', '2026-09-17 16:22:41.017000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (127, 'CUN039', NULL, 5, 'CUNAS DE POSTE CG-XL125-XL185-AKT125 REDONDA VINI', NULL, NULL, NULL, NULL, '76.50', '107.10', 30, 5, True, '2026-09-17 16:22:41.020000', '2026-09-17 16:22:41.020000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (128, 'CUN042', NULL, 5, 'CUNAS DE POSTE HJ110 LUCKY VINI', NULL, NULL, NULL, NULL, '97.75', '136.85', 20, 5, True, '2026-09-17 16:22:41.030000', '2026-09-17 16:22:41.030000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (129, 'CUN056', NULL, 5, 'CUNAS DE POSTE NXR-BROS CONICA VINI', NULL, NULL, NULL, NULL, '106.25', '148.75', 20, 5, True, '2026-09-17 16:22:41.033000', '2026-09-17 16:22:41.033000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (130, 'CUN054', NULL, 5, 'CUNAS DE POSTE NXR-BROS REDONDA VINI', NULL, NULL, NULL, NULL, '106.25', '148.75', 20, 5, True, '2026-09-17 16:22:41.037000', '2026-09-17 16:22:41.037000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (131, 'DEL054', NULL, 3, 'DISCOS DE CLUTCH CG125-150-YBR125 5PCS VINI', NULL, NULL, NULL, NULL, '106.25', '148.75', 20, 5, True, '2026-09-17 16:22:41.037000', '2026-09-17 16:22:41.037000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (132, 'EMM080', NULL, 1, 'EMPAQUES DE MOTOR KIT CG150 VINI', NULL, NULL, NULL, NULL, '106.25', '148.75', 30, 5, True, '2026-09-17 16:22:41.040000', '2026-09-17 16:22:41.040000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (133, 'EMM062', NULL, 1, 'EMPAQUES DE MOTOR KIT GXT200 VINI', NULL, NULL, NULL, NULL, '182.75', '255.85', 20, 5, True, '2026-09-17 16:22:41.047000', '2026-09-17 16:22:41.047000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (134, 'EMM102', NULL, 1, 'EMPAQUES DE MOTOR KIT GY200-YUMBO 69MM VINI', NULL, NULL, NULL, NULL, '174.25', '243.95', 30, 5, True, '2026-09-17 16:22:41.047000', '2026-09-17 16:22:41.047000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (135, 'EMM092', NULL, 1, 'EMPAQUES DE MOTOR KIT PULSAR 135-DISCOVER 150 VINI', NULL, NULL, NULL, NULL, '97.75', '136.85', 30, 5, True, '2026-09-17 16:22:41.047000', '2026-09-17 16:22:41.047000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (136, 'DES029', NULL, 1, 'EMPAQUES DESCARBONADO DAKAR 200 69MM VINI', NULL, NULL, NULL, NULL, '51.00', '71.40', 30, 5, True, '2026-09-17 16:22:41.050000', '2026-09-17 16:22:41.050000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (137, 'DES045', NULL, 1, 'EMPAQUES DESCARBONADO PULSAR 135 VINI', NULL, NULL, NULL, NULL, '38.25', '53.55', 30, 5, True, '2026-09-17 16:22:41.057000', '2026-09-17 16:22:41.057000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (138, 'ENG013', NULL, 2, 'ENGRANAJE DE ARRANQUE + BALINERA CG200 MULTIBALINES VINI', NULL, NULL, NULL, NULL, '476.00', '666.40', 15, 5, True, '2026-09-17 16:22:41.060000', '2026-09-17 16:22:41.060000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (139, 'ENG047', NULL, 2, 'ENGRANAJE DE ARRANQUE + BALINERA GENESIS RKS150 VINI', NULL, NULL, NULL, NULL, '297.50', '416.50', 15, 5, True, '2026-09-17 16:22:41.063000', '2026-09-17 16:22:41.063000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (140, 'FRI045', NULL, 3, 'FRICCIONES HJ125-GXT200 VINI', NULL, NULL, NULL, NULL, '131.75', '184.45', 20, 5, True, '2026-09-17 16:22:41.070000', '2026-09-17 16:22:41.070000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (141, 'FRI038', NULL, 3, 'FRICCIONES PULSAR-BOXER-DISCOVER VINI', NULL, NULL, NULL, NULL, '131.75', '184.45', 20, 5, True, '2026-09-17 16:22:41.073000', '2026-09-17 16:22:41.073000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (142, 'FUS003', NULL, 2, 'FUSIBLE 15 AH GAVETA (100 UND) VINI', NULL, NULL, NULL, NULL, '1.61', '2.25', 200, 5, True, '2026-09-17 16:22:41.077000', '2026-09-17 16:22:41.077000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (143, 'FUS004', NULL, 2, 'FUSIBLE 20 AH GAVETA (100UND) VINI', NULL, NULL, NULL, NULL, '1.61', '2.25', 200, 5, True, '2026-09-17 16:22:41.080000', '2026-09-17 16:22:41.080000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (144, 'FUS005', NULL, 2, 'FUSIBLE 25 AH GAVETA (100 UND) VINI', NULL, NULL, NULL, NULL, '1.61', '2.25', 200, 5, True, '2026-09-17 16:22:41.087000', '2026-09-17 16:22:41.087000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (145, 'FUS006', NULL, 2, 'FUSIBLE 30 AH GAVETA (100UND) VINI', NULL, NULL, NULL, NULL, '1.61', '2.25', 200, 5, True, '2026-09-17 16:22:41.090000', '2026-09-17 16:22:41.090000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (146, 'GUA134', NULL, 8, 'GUARDAFANGO WR250F-YZ250F UNIVERSAL AZUL VINI', NULL, NULL, NULL, NULL, '289.00', '404.60', 3, 5, True, '2026-09-17 16:22:41.097000', '2026-09-17 16:22:41.097000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (147, 'GUA135', NULL, 8, 'GUARDAFANGO WR250F-YZ250F UNIVERSAL BLANCO VINI', NULL, NULL, NULL, NULL, '289.00', '404.60', 3, 5, True, '2026-09-17 16:22:41.100000', '2026-09-17 16:22:41.100000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (148, 'GUA136', NULL, 8, 'GUARDAFANGO WR250F-YZ250F UNIVERSAL NEGRO VINI', NULL, NULL, NULL, NULL, '289.00', '404.60', 3, 5, True, '2026-09-17 16:22:41.107000', '2026-09-17 16:22:41.107000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (149, 'CPI037', NULL, 9, 'GUIAS DE TIEMPO (CEPILLOS) CBF150-TITAN150-DAYUN 150GY VINI', NULL, NULL, NULL, NULL, '106.25', '148.75', 20, 5, True, '2026-09-17 16:22:41.110000', '2026-09-17 16:22:41.110000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (150, 'CPI019', NULL, 9, 'GUIAS DE TIEMPO (CEPILLOS) PULSAR 135 VINI', NULL, NULL, NULL, NULL, '93.50', '130.90', 20, 5, True, '2026-09-17 16:22:41.113000', '2026-09-17 16:22:41.113000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (151, 'VAL016', NULL, 1, 'GUIAS DE VALVULAS CG125-150-200 CORTA RACING MODIFIC VINI', NULL, NULL, NULL, NULL, '85.00', '119.00', 10, 5, True, '2026-09-17 16:22:41.120000', '2026-09-17 16:22:41.120000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (152, 'VAL088', NULL, 1, 'GUIAS DE VALVULAS CG125-CG200-300 VINI', NULL, NULL, NULL, NULL, '55.25', '77.35', 20, 5, True, '2026-09-17 16:22:41.123000', '2026-09-17 16:22:41.123000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (153, 'INI055', NULL, 2, 'IGNICION AKT NKD125-SERPENTO CORAL150-TAYPAN VINI', NULL, NULL, NULL, NULL, '106.25', '148.75', 10, 5, True, '2026-09-17 16:22:41.130000', '2026-09-17 16:22:41.130000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (154, 'MDC098', NULL, 2, 'IGNICION HAYATE VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 5, 5, True, '2026-09-17 16:22:41.130000', '2026-09-17 16:22:41.130000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (155, 'LAV044', NULL, 6, 'LLAVE DE COMBUSTIBLE AKT -XL GRUESA VINI', NULL, NULL, NULL, NULL, '63.75', '89.25', 20, 5, True, '2026-09-17 16:22:41.137000', '2026-09-17 16:22:41.137000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (156, 'LAV047', NULL, 9, 'LLAVIN DE TAPADERAS LATERALES YBR125-DT175-XTZ125 VINI', NULL, NULL, NULL, NULL, '55.25', '77.35', 10, 5, True, '2026-09-17 16:22:41.140000', '2026-09-17 16:22:41.140000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (157, 'MDO073', NULL, 2, 'MANDO DER START PULSAR 135 VINI', NULL, NULL, NULL, NULL, '272.00', '380.80', 10, 5, True, '2026-09-17 16:22:41.147000', '2026-09-17 16:22:41.147000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (158, 'MDO074', NULL, 2, 'MANDO DER START PULSAR NS200 VINI', NULL, NULL, NULL, NULL, '497.25', '696.15', 10, 5, True, '2026-09-17 16:22:41.150000', '2026-09-17 16:22:41.150000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (159, 'MDO036', NULL, 2, 'MANDO DER START WY125-RAYBAR VINI', NULL, NULL, NULL, NULL, '127.50', '178.50', 10, 5, True, '2026-09-17 16:22:41.160000', '2026-09-17 16:22:41.160000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (160, 'MDO075', NULL, 2, 'MANDO IZQ LUCES GXT200 VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 10, 5, True, '2026-09-17 16:22:41.163000', '2026-09-17 16:22:41.163000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (161, 'MDO076', NULL, 2, 'MANDO IZQ LUCES PULSAR 135 VINI', NULL, NULL, NULL, NULL, '263.50', '368.90', 10, 5, True, '2026-09-17 16:22:41.167000', '2026-09-17 16:22:41.167000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (162, 'MDO077', NULL, 2, 'MANDO IZQ LUCES PULSAR NS200 VINI', NULL, NULL, NULL, NULL, '497.25', '696.15', 10, 5, True, '2026-09-17 16:22:41.170000', '2026-09-17 16:22:41.170000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (163, 'MCI074', NULL, 3, 'MANECILLA DE CLUTCH HJ125-WY COMPLETA VINI', NULL, NULL, NULL, NULL, '93.50', '130.90', 50, 5, True, '2026-09-17 16:22:41.177000', '2026-09-17 16:22:41.177000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (164, 'MGA024', NULL, 4, 'MANGUERA DE FRENO DELANTERA GXT200 VINI', NULL, NULL, NULL, NULL, '134.30', '188.02', 10, 5, True, '2026-09-17 16:22:41.180000', '2026-09-17 16:22:41.180000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (165, 'MGA013', NULL, 4, 'MANGUERA DE FRENO TRASERA 60CM UNIVERSAL VINI', NULL, NULL, NULL, NULL, '119.00', '166.60', 10, 5, True, '2026-09-17 16:22:41.187000', '2026-09-17 16:22:41.187000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (166, 'MOT047', NULL, 2, 'MOTOR DE ARRANQUE AG200-XT225 VINI', NULL, NULL, NULL, NULL, '1228.25', '1719.55', 2, 5, True, '2026-09-17 16:22:41.190000', '2026-09-17 16:22:41.190000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (167, 'MOT050', NULL, 2, 'MOTOR DE ARRANQUE CGL125-HJ125 9 DIENTES VINI', NULL, NULL, NULL, NULL, '722.50', '1011.50', 5, 5, True, '2026-09-17 16:22:41.193000', '2026-09-17 16:22:41.193000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (168, 'MOT025', NULL, 2, 'MOTOR DE ARRANQUE GXT200-GN125-EN125 VINI', NULL, NULL, NULL, NULL, '705.50', '987.70', 5, 5, True, '2026-09-17 16:22:41.200000', '2026-09-17 16:22:41.200000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (169, 'PAL035', NULL, 7, 'PEDAL DE CAMBIOS HJ125-7 VINI', NULL, NULL, NULL, NULL, '204.00', '285.60', 5, 5, True, '2026-09-17 16:22:41.203000', '2026-09-17 16:22:41.203000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (170, 'PAT027', NULL, 7, 'PEDAL DE ENCENDIDO AKT TT150-TT180-TT200-GENESIS SX200-SX250 VINI', NULL, NULL, NULL, NULL, '187.00', '261.80', 10, 5, True, '2026-09-17 16:22:41.207000', '2026-09-17 16:22:41.207000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (171, 'PAT028', NULL, 7, 'PEDAL DE ENCENDIDO GXT200 VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 10, 5, True, '2026-09-17 16:22:41.210000', '2026-09-17 16:22:41.210000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (172, 'PAT029', NULL, 7, 'PEDAL DE ENCENDIDO HJ125 VINI', NULL, NULL, NULL, NULL, '173.40', '242.76', 10, 5, True, '2026-09-17 16:22:41.213000', '2026-09-17 16:22:41.213000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (173, 'PIS197', NULL, 1, 'PISTON COMPLETO AG200-UM200-RAYBAR200 STD 67MM-B16 VINI', NULL, NULL, NULL, NULL, '404.60', '566.44', 10, 5, True, '2026-09-17 16:22:41.217000', '2026-09-17 16:22:41.217000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (174, 'PIS166', NULL, 1, 'PISTON COMPLETO AKT CR5-CUPULA 200 STD B15 63 VINI', NULL, NULL, NULL, NULL, '303.45', '424.83', 10, 5, True, '2026-09-17 16:22:41.220000', '2026-09-17 16:22:41.220000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (175, 'PIS193', NULL, 1, 'PISTON COMPLETO AKT EVO 150NE-TT150 (B13) 62MM VINI', NULL, NULL, NULL, NULL, '280.50', '392.70', 10, 5, True, '2026-09-17 16:22:41.223000', '2026-09-17 16:22:41.223000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (176, 'PIS198', NULL, 1, 'PISTON COMPLETO APACHE 160 STD 62M-15-2V VINI', NULL, NULL, NULL, NULL, '314.50', '440.30', 5, 5, True, '2026-09-17 16:22:41.227000', '2026-09-17 16:22:41.227000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (177, 'PIS199', NULL, 1, 'PISTON COMPLETO APACHE 180 RTR STD 2V-B15-62.5 VINI', NULL, NULL, NULL, NULL, '382.50', '535.50', 5, 5, True, '2026-09-17 16:22:41.227000', '2026-09-17 16:22:41.227000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (178, 'PIS145', NULL, 1, 'PISTON COMPLETO CG125-WY125 (56MM*B15MM) STD VINI', NULL, NULL, NULL, NULL, '216.75', '303.45', 10, 5, True, '2026-09-17 16:22:41.230000', '2026-09-17 16:22:41.230000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (179, 'PIS146', NULL, 1, 'PISTON COMPLETO CG150-WY150 (62MM*B15MM) STD VINI', NULL, NULL, NULL, NULL, '255.00', '357.00', 5, 5, True, '2026-09-17 16:22:41.230000', '2026-09-17 16:22:41.230000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (180, 'PIS147', NULL, 1, 'PISTON COMPLETO CG200-WY200-XL200 (63.5MM*B15MM) STD VINI', NULL, NULL, NULL, NULL, '272.00', '380.80', 10, 5, True, '2026-09-17 16:22:41.233000', '2026-09-17 16:22:41.233000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (181, 'PIS153', NULL, 1, 'PISTON COMPLETO DAYUN150-CBF150-RTX STD B14-57MM VINI', NULL, NULL, NULL, NULL, '272.00', '380.80', 10, 5, True, '2026-09-17 16:22:41.237000', '2026-09-17 16:22:41.237000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (182, 'PIS152', NULL, 1, 'PISTON COMPLETO MODIFICADO CG200 63.5MM-B15 CON CUPULA RACING VINI', NULL, NULL, NULL, NULL, '420.75', '589.05', 5, 5, True, '2026-09-17 16:22:41.240000', '2026-09-17 16:22:41.240000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (183, 'PIS148', NULL, 1, 'PISTON COMPLETO PULSAR 135 STD 54MM-B14 VINI', NULL, NULL, NULL, NULL, '297.50', '416.50', 10, 5, True, '2026-09-17 16:22:41.243000', '2026-09-17 16:22:41.243000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (184, 'PIS162', NULL, 1, 'PISTON COMPLETO PULSAR 180 STD 63.5MM-B16 VINI', NULL, NULL, NULL, NULL, '331.50', '464.10', 5, 5, True, '2026-09-17 16:22:41.250000', '2026-09-17 16:22:41.250000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (185, 'PIS163', NULL, 1, 'PISTON COMPLETO PULSAR NS200-RS200-AS200 72MM-B17 STD VINI', NULL, NULL, NULL, NULL, '408.00', '571.20', 5, 5, True, '2026-09-17 16:22:41.253000', '2026-09-17 16:22:41.253000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (186, 'PIS149', NULL, 1, 'PISTON COMPLETO TORITO175-205 KIT LF200 B17-61MM VINI', NULL, NULL, NULL, NULL, '331.50', '464.10', 15, 5, True, '2026-09-17 16:22:41.253000', '2026-09-17 16:22:41.253000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (187, 'PIT009', NULL, 8, 'PITO UNIVERSAL DL128ZB VINI', NULL, NULL, NULL, NULL, '63.75', '89.25', 50, 5, True, '2026-09-17 16:22:41.257000', '2026-09-17 16:22:41.257000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (188, 'REC053', NULL, 2, 'RECTIFICADOR 4L RAYBAR200 CON DIODO VINI', NULL, NULL, NULL, NULL, '158.95', '222.53', 20, 5, True, '2026-09-17 16:22:41.260000', '2026-09-17 16:22:41.260000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (189, 'REC055', NULL, 2, 'RECTIFICADOR AKT 180-CR5- GENESIS LONCIN SX250 SX3 VINI', NULL, NULL, NULL, NULL, '212.50', '297.50', 5, 5, True, '2026-09-17 16:22:41.260000', '2026-09-17 16:22:41.260000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (190, 'REC056', NULL, 2, 'RECTIFICADOR BOXER BM150 VINI', NULL, NULL, NULL, NULL, '212.50', '297.50', 5, 5, True, '2026-09-17 16:22:41.260000', '2026-09-17 16:22:41.260000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (191, 'REC057', NULL, 2, 'RECTIFICADOR PULSAR 135 VINI', NULL, NULL, NULL, NULL, '346.80', '485.52', 5, 5, True, '2026-09-17 16:22:41.263000', '2026-09-17 16:22:41.263000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (192, 'RGL004', NULL, 3, 'REGULADORES DE CADENA TRACCION BROSS150-XR150-AKT TT150-180 VINI', NULL, NULL, NULL, NULL, '115.60', '161.84', 10, 5, True, '2026-09-17 16:22:41.267000', '2026-09-17 16:22:41.267000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (193, 'RGL005', NULL, 3, 'REGULADORES DE CADENA TRACCION CG125-XL VINI', NULL, NULL, NULL, NULL, '21.25', '29.75', 20, 5, True, '2026-09-17 16:22:41.267000', '2026-09-17 16:22:41.267000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (194, 'RGL006', NULL, 3, 'REGULADORES DE CADENA TRACCION WY125-CGL125-AKT HUNTER 150 VINI', NULL, NULL, NULL, NULL, '68.00', '95.20', 20, 5, True, '2026-09-17 16:22:41.270000', '2026-09-17 16:22:41.270000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (195, 'CCH009', NULL, 2, 'RELAY DE ARRANQUE CG-WY VINI', NULL, NULL, NULL, NULL, '119.00', '166.60', 30, 5, True, '2026-09-17 16:22:41.270000', '2026-09-17 16:22:41.270000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (196, 'CCH017', NULL, 2, 'RELAY DE ARRANQUE PULSAR 135-DISCOVER-RS200 VINI', NULL, NULL, NULL, NULL, '216.75', '303.45', 10, 5, True, '2026-09-17 16:22:41.273000', '2026-09-17 16:22:41.273000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (197, 'RET122', NULL, 1, 'RETENEDORES DE BARRAS CG-AKT NKD 27-37-10.5 VINI', NULL, NULL, NULL, NULL, '28.90', '40.46', 30, 5, True, '2026-09-17 16:22:41.273000', '2026-09-17 16:22:41.273000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (198, 'RET060', NULL, 1, 'RETENEDORES DE BARRAS PULSAR NS200-PULSAR180-220 VINI', NULL, NULL, NULL, NULL, '63.75', '89.25', 30, 5, True, '2026-09-17 16:22:41.277000', '2026-09-17 16:22:41.277000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (199, 'RET092', NULL, 1, 'RETENEDORES DE BARRAS PULSAR135-DISC150-YBR125-2020-25 CRUX110-REV 30-42-10.5 VINI', NULL, NULL, NULL, NULL, '38.25', '53.55', 30, 5, True, '2026-09-17 16:22:41.280000', '2026-09-17 16:22:41.280000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (200, 'RET115', NULL, 1, 'RETENEDORES DE BARRAS SZ150-NAGA 200-JIALING150 33X46X10.5 VINI', NULL, NULL, NULL, NULL, '46.75', '65.45', 30, 5, True, '2026-09-17 16:22:41.280000', '2026-09-17 16:22:41.280000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (201, 'RET090', NULL, 1, 'RETENEDORES DE BARRAS XL-WY BOXER150 NS160-N160-NS125UG 31X43X10.5 VINI', NULL, NULL, NULL, NULL, '42.50', '59.50', 50, 5, True, '2026-09-17 16:22:41.283000', '2026-09-17 16:22:41.283000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (202, 'RET065', NULL, 1, 'RETENEDORES DE BARRAS YBR125-CRUX110(VIEJA)-RX100-HJ125-7 (30*40.5*10.5) VINI', NULL, NULL, NULL, NULL, '42.50', '59.50', 30, 5, True, '2026-09-17 16:22:41.287000', '2026-09-17 16:22:41.287000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (203, 'OTR362', NULL, 1, 'SELLOS DE VALVULAS EN125-GN125 VINI', NULL, NULL, NULL, NULL, '25.50', '35.70', 50, 5, True, '2026-09-17 16:22:41.290000', '2026-09-17 16:22:41.290000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (204, 'OTR363', NULL, 1, 'SELLOS DE VALVULAS TORITO LF200 RE205 VINI', NULL, NULL, NULL, NULL, '25.50', '35.70', 30, 5, True, '2026-09-17 16:22:41.293000', '2026-09-17 16:22:41.293000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (205, 'SIN025', NULL, 9, 'SINFIN DE VELOCIMETRO AKT TT150 VINI', NULL, NULL, NULL, NULL, '110.50', '154.70', 20, 5, True, '2026-09-17 16:22:41.300000', '2026-09-17 16:22:41.300000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (206, 'SIS016', NULL, 9, 'SISTEMA ELECTRICO CG-DY125-ZS150 VINI', NULL, NULL, NULL, NULL, '408.00', '571.20', 5, 5, True, '2026-09-17 16:22:41.303000', '2026-09-17 16:22:41.303000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (207, 'SIS023', NULL, 9, 'SISTEMA ELECTRICO SX150 - AKT150TT-ZX150L VINI', NULL, NULL, NULL, NULL, '535.50', '749.70', 5, 5, True, '2026-09-17 16:22:41.307000', '2026-09-17 16:22:41.307000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (208, 'SPR175', NULL, 3, 'SPROCKET KIT AKT 150NE EVO 428H 41TX15T + 120L COMPLETO VINI', NULL, NULL, NULL, NULL, '391.00', '547.40', 10, 5, True, '2026-09-17 16:22:41.310000', '2026-09-17 16:22:41.310000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (209, 'SPR209', NULL, 3, 'SPROCKET KIT AKT SL-NKD-EVO-SERPENTO CORAL-COBRA 428H 38X15T + 130L COMPLETO VINI', NULL, NULL, NULL, NULL, '416.50', '583.10', 10, 5, True, '2026-09-17 16:22:41.313000', '2026-09-17 16:22:41.313000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (210, 'SPR309', NULL, 3, 'SPROCKET KIT AKT SL-NKD-EVO-SERPENTO CORAL-COBRA 428H 42X15T + 130L COMPLETO VINI', NULL, NULL, NULL, NULL, '442.00', '618.80', 10, 5, True, '2026-09-17 16:22:41.313000', '2026-09-17 16:22:41.313000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (211, 'SPR310', NULL, 3, 'SPROCKET KIT FZ16 428H 40T X 14T + 132L COMPLETO VINI', NULL, NULL, NULL, NULL, '442.00', '618.80', 5, 5, True, '2026-09-17 16:22:41.317000', '2026-09-17 16:22:41.317000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (212, 'SPR255', NULL, 3, 'SPROCKET KIT PULSAR 135 428H 43X15T + 130L DORADA COMPLETO VINI', NULL, NULL, NULL, NULL, '493.00', '690.20', 10, 5, True, '2026-09-17 16:22:41.320000', '2026-09-17 16:22:41.320000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (213, 'SPR268', NULL, 3, 'SPROCKET KIT PULSAR NS200 428H 45X15T + 136 DORADA RACING COMPLETO VINI', NULL, NULL, NULL, NULL, '544.00', '761.60', 10, 5, True, '2026-09-17 16:22:41.323000', '2026-09-17 16:22:41.323000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (214, 'SPR311', NULL, 3, 'SPROCKET KIT XR150L 428H 49T X 17T + 136L COMPLETO VINI', NULL, NULL, NULL, NULL, '493.00', '690.20', 5, 5, True, '2026-09-17 16:22:41.327000', '2026-09-17 16:22:41.327000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (215, 'SPR126', NULL, 3, 'SPROCKET TRASERO CGL125 428H 38T CONCAVO VINI', NULL, NULL, NULL, NULL, '123.25', '172.55', 10, 5, True, '2026-09-17 16:22:41.330000', '2026-09-17 16:22:41.330000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (216, 'BUJ257', NULL, 9, 'STOP TRASERO GN125H', NULL, NULL, NULL, NULL, '306.00', '428.40', 3, 5, True, '2026-09-17 16:22:41.333000', '2026-09-17 16:22:41.333000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (217, 'TPO075', NULL, 6, 'TAPON DE TANQUE PULSAR 135 VINI', NULL, NULL, NULL, NULL, '399.50', '559.30', 10, 5, True, '2026-09-17 16:22:41.340000', '2026-09-17 16:22:41.340000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (218, 'TEN021', NULL, 9, 'TENSOR AUTOMATICO BOXER BM150-BM100-PULSAR 135 GRIS VINI', NULL, NULL, NULL, NULL, '122.83', '171.96', 10, 5, True, '2026-09-17 16:22:41.340000', '2026-09-17 16:22:41.340000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (219, 'VAL089', NULL, 1, 'VALVULAS DE MOTOR CG125-HJ125-7 (5MM) VINI', NULL, NULL, NULL, NULL, '178.50', '249.90', 30, 5, True, '2026-09-17 16:22:41.343000', '2026-09-17 16:22:41.343000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (220, 'VAL090', NULL, 1, 'VALVULAS DE MOTOR CG150-AKT TT150-EVO150 VINI', NULL, NULL, NULL, NULL, '195.50', '273.70', 30, 5, True, '2026-09-17 16:22:41.347000', '2026-09-17 16:22:41.347000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (221, 'VAL091', NULL, 1, 'VALVULAS DE MOTOR CG200 (5MM) VINI', NULL, NULL, NULL, NULL, '229.50', '321.30', 30, 5, True, '2026-09-17 16:22:41.350000', '2026-09-17 16:22:41.350000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (222, 'VAL145', NULL, 1, 'VALVULAS DE MOTOR CG250-RAYBAR250 HI RPM ALTO CARBONO VINI', NULL, NULL, NULL, NULL, '263.50', '368.90', 10, 5, True, '2026-09-17 16:22:41.357000', '2026-09-17 16:22:41.357000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (223, 'VAL092', NULL, 1, 'VALVULAS DE MOTOR CG250-YUMBO250-RAYBAR250 VINI', NULL, NULL, NULL, NULL, '238.00', '333.20', 10, 5, True, '2026-09-17 16:22:41.360000', '2026-09-17 16:22:41.360000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (224, 'VAL134', NULL, 1, 'VALVULAS DE MOTOR DISCOVER 125 ST 4PCS VINI', NULL, NULL, NULL, NULL, '297.50', '416.50', 10, 5, True, '2026-09-17 16:22:41.363000', '2026-09-17 16:22:41.363000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (225, 'VAL150', NULL, 1, 'VALVULAS DE MOTOR HONDA NAVI-CB1 VINI', NULL, NULL, NULL, NULL, '204.00', '285.60', 10, 5, True, '2026-09-17 16:22:41.367000', '2026-09-17 16:22:41.367000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (226, 'VAL097', NULL, 1, 'VALVULAS DE MOTOR PULSAR 135 4PZS VINI', NULL, NULL, NULL, NULL, '306.00', '428.40', 20, 5, True, '2026-09-17 16:22:41.370000', '2026-09-17 16:22:41.370000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (227, 'VAL148', NULL, 1, 'VALVULAS DE MOTOR PULSAR 180 VINI', NULL, NULL, NULL, NULL, '280.50', '392.70', 10, 5, True, '2026-09-17 16:22:41.373000', '2026-09-17 16:22:41.373000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (228, 'VAL147', NULL, 1, 'VALVULAS DE MOTOR SCOOTER 150 VINI', NULL, NULL, NULL, NULL, '212.50', '297.50', 10, 5, True, '2026-09-17 16:22:41.377000', '2026-09-17 16:22:41.377000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (229, 'VAL178', NULL, 1, 'VALVULAS DE MOTOR SCOOTER GY6 125 VINI', NULL, NULL, NULL, NULL, '136.00', '190.40', 10, 5, True, '2026-09-17 16:22:41.380000', '2026-09-17 16:22:41.380000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (230, 'VAL149', NULL, 1, 'VALVULAS DE MOTOR SUZUKI AN125 VINI', NULL, NULL, NULL, NULL, '255.00', '357.00', 10, 5, True, '2026-09-17 16:22:41.383000', '2026-09-17 16:22:41.383000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (231, 'VAL079', NULL, 1, 'VALVULAS DE MOTOR SUZUKI AX4 VINI', NULL, NULL, NULL, NULL, '229.50', '321.30', 10, 5, True, '2026-09-17 16:22:41.387000', '2026-09-17 16:22:41.387000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (232, 'VAR022', NULL, 4, 'VARILLA DE FRENO CG125-TAYPAN-NKD125 VINI', NULL, NULL, NULL, NULL, '34.00', '47.60', 20, 5, True, '2026-09-17 16:22:41.390000', '2026-09-17 16:22:41.390000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (233, 'VAR023', NULL, 4, 'VARILLA DE FRENO YBR125ED-G VINI', NULL, NULL, NULL, NULL, '46.75', '65.45', 10, 5, True, '2026-09-17 16:22:41.393000', '2026-09-17 16:22:41.393000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (234, 'VAR016', NULL, 4, 'VARILLAS DE EMPUJE ALUMINIO CG150-AKT TT150-EVO-XM20 VINI', NULL, NULL, NULL, NULL, '68.00', '95.20', 30, 5, True, '2026-09-17 16:22:41.397000', '2026-09-17 16:22:41.397000');
INSERT INTO [productos] ([id], [codigo_sku], [codigo_barras], [categoria_id], [nombre], [descripcion], [marca], [modelo_compatible], [ubicacion_estante], [costo], [precio_venta], [stock_actual], [stock_minimo], [activo], [created_at], [updated_at]) VALUES (235, 'VAR017', NULL, 4, 'VARILLAS DE EMPUJE ALUMINIO CG-GY200-XM 200 VINI', NULL, NULL, NULL, NULL, '68.00', '95.20', 20, 5, True, '2026-09-17 16:22:41.400000', '2026-09-17 16:22:41.400000');
SET IDENTITY_INSERT [productos] OFF;
GO

-- Datos para [proveedores] (2 registros)
SET IDENTITY_INSERT [proveedores] ON;
INSERT INTO [proveedores] ([id], [nombre_empresa], [contacto_nombre], [identificacion_fiscal], [telefono], [email], [direccion], [activo], [created_at], [updated_at]) VALUES (1, 'Distribuidora Repuestos del Pacífico', 'Mario López', 'J0310000123456', '+505 8899-1122', 'ventas@pacificomotos.com', 'Managua, Pista Juan Pablo II', True, '2026-08-13 17:02:50.500000', '2026-08-13 17:02:50.500000');
INSERT INTO [proveedores] ([id], [nombre_empresa], [contacto_nombre], [identificacion_fiscal], [telefono], [email], [direccion], [activo], [created_at], [updated_at]) VALUES (2, 'Importadora Global Moto Parts', 'Elena Morales', 'J0310000987654', '+505 7766-3344', 'contacto@globalmotoparts.com', 'Masaya, Km 28 Carretera a Granada', True, '2026-08-13 17:02:50.500000', '2026-08-13 17:02:50.500000');
SET IDENTITY_INSERT [proveedores] OFF;
GO

-- Datos para [roles] (8 registros)
SET IDENTITY_INSERT [roles] ON;
INSERT INTO [roles] ([id], [nombre], [descripcion], [created_at]) VALUES (1, 'Administrador', 'Control total administrativo y reportes', '2026-08-13 17:02:50.447000');
INSERT INTO [roles] ([id], [nombre], [descripcion], [created_at]) VALUES (2, 'Vendedor', 'Atención al cliente y facturación en caja', '2026-08-13 17:02:50.447000');
INSERT INTO [roles] ([id], [nombre], [descripcion], [created_at]) VALUES (3, 'Encargado de Inventario', 'Ingreso de compras, bodega y Kardex', '2026-08-13 17:02:50.447000');
INSERT INTO [roles] ([id], [nombre], [descripcion], [created_at]) VALUES (4, 'Contador', 'Balances contables y reportes de rentabilidad', '2026-08-13 17:02:50.447000');
INSERT INTO [roles] ([id], [nombre], [descripcion], [created_at]) VALUES (1001, 'Responsable de Recursos Humanos', 'Gestión de empleados, vacaciones, permisos y nómina', '2026-10-06 20:55:00.803000');
INSERT INTO [roles] ([id], [nombre], [descripcion], [created_at]) VALUES (1002, 'Gerente de Operaciones', 'Supervisión general de operaciones de ventas e inventario', '2026-10-06 20:55:00.817000');
INSERT INTO [roles] ([id], [nombre], [descripcion], [created_at]) VALUES (1003, 'Gerente Administrativo y Financiero', 'Supervisión de finanzas, contabilidad y administración', '2026-10-06 20:55:00.820000');
INSERT INTO [roles] ([id], [nombre], [descripcion], [created_at]) VALUES (1004, 'Encargado de Compras y Proveedores', 'Gestión de compras, órdenes y proveedores', '2026-10-06 20:55:00.827000');
SET IDENTITY_INSERT [roles] OFF;
GO

-- Datos para [sesiones] (1 registros)
SET IDENTITY_INSERT [sesiones] ON;
INSERT INTO [sesiones] ([id], [usuario_id], [fechaInicio], [estado], [ip]) VALUES (1, 1, '2026-10-13 20:55:01.413000', 'Activa', '192.168.0.7');
SET IDENTITY_INSERT [sesiones] OFF;
GO

-- Datos para [solicitudes_empleo] (2 registros)
SET IDENTITY_INSERT [solicitudes_empleo] ON;
INSERT INTO [solicitudes_empleo] ([id], [codigo_solicitud], [nombres_apellidos], [identificacion], [direccion], [telefono], [email], [puesto_solicitado], [formacion_academica], [experiencia_laboral], [referencias_laborales], [disponibilidad], [salario_pretendido], [curriculum_vitae], [estado], [observaciones], [fecha_registro]) VALUES (1, 'SOL-2026-001', 'Carlos Manuel Rivas Pérez', '401-140598-0004L', 'Bo. San Jerónimo, Masatepe', '+505 8899-1122', 'carlos.rivas@gmail.com', 'Vendedor de Mostrador', 'Bachiller / Técnico en Computación', '2 años vendedor de repuestos en Masatepe', 'Lic. Juan Díaz (Tel: 8877-6655)', 'Inmediata', '9500.00', NULL, 'En revisión', 'Excelente conocimiento en repuestos de motocicletas y trato amable.', '2026-10-13 20:33:08.140000');
INSERT INTO [solicitudes_empleo] ([id], [codigo_solicitud], [nombres_apellidos], [identificacion], [direccion], [telefono], [email], [puesto_solicitado], [formacion_academica], [experiencia_laboral], [referencias_laborales], [disponibilidad], [salario_pretendido], [curriculum_vitae], [estado], [observaciones], [fecha_registro]) VALUES (2, 'SOL-2026-002', 'Marcos Josué Vega Blandón', '401-201099-0011W', 'Reparto San José, Masatepe', '+505 8765-4321', 'marcos.vega@gmail.com', 'Encargado de Bodega e Inventario', 'Técnico Medio en Logística', '1 año en distribuidora de lubricantes y baterías', 'Ing. Mario Silva (Tel: 8900-1122)', 'Inmediata', '10500.00', NULL, 'Entrevista', 'Experiencia en orden de estanterías y recepción de mercadería.', '2026-10-13 20:33:08.140000');
SET IDENTITY_INSERT [solicitudes_empleo] OFF;
GO

-- Datos para [usuarios] (8 registros)
SET IDENTITY_INSERT [usuarios] ON;
INSERT INTO [usuarios] ([id], [rol_id], [username], [password_hash], [nombre_completo], [email], [telefono], [activo], [ultimo_acceso], [created_at], [updated_at]) VALUES (1, 1, 'admin', '123', 'Gilda Pérez', 'admin@jehovajireh.com', '+505 8888-0001', True, '2026-10-13 20:55:01.427000', '2026-08-13 17:02:50.473000', '2026-08-13 17:02:50.473000');
INSERT INTO [usuarios] ([id], [rol_id], [username], [password_hash], [nombre_completo], [email], [telefono], [activo], [ultimo_acceso], [created_at], [updated_at]) VALUES (2, 2, 'vendedor', '123', 'Ana Gómez', 'ventas@jehovajireh.com', '+505 8888-0002', True, NULL, '2026-08-13 17:02:50.473000', '2026-08-13 17:02:50.473000');
INSERT INTO [usuarios] ([id], [rol_id], [username], [password_hash], [nombre_completo], [email], [telefono], [activo], [ultimo_acceso], [created_at], [updated_at]) VALUES (3, 3, 'inventario', '123', 'Roberto Silva', 'bodega@jehovajireh.com', '+505 8888-0003', True, NULL, '2026-08-13 17:02:50.473000', '2026-08-13 17:02:50.473000');
INSERT INTO [usuarios] ([id], [rol_id], [username], [password_hash], [nombre_completo], [email], [telefono], [activo], [ultimo_acceso], [created_at], [updated_at]) VALUES (4, 4, 'contador', '123', 'Lic. Fernando Rivas (Granada)', 'contabilidad@jehovajireh.com', '+505 8888-0004', True, NULL, '2026-08-13 17:02:50.473000', '2026-08-13 17:02:50.473000');
INSERT INTO [usuarios] ([id], [rol_id], [username], [password_hash], [nombre_completo], [email], [telefono], [activo], [ultimo_acceso], [created_at], [updated_at]) VALUES (1001, 1001, 'rrhh', '123', 'Lic. María Elena Calero', 'rrhh@jehovajireh.com', '+505 8888-0005', True, NULL, '2026-10-06 20:55:00.840000', '2026-10-06 20:55:00.840000');
INSERT INTO [usuarios] ([id], [rol_id], [username], [password_hash], [nombre_completo], [email], [telefono], [activo], [ultimo_acceso], [created_at], [updated_at]) VALUES (1002, 1002, 'gerente_op', '123', 'Gerente de Operaciones', 'gerente_op@jehovajireh.com', '+505 8888-0006', True, NULL, '2026-10-06 20:55:00.850000', '2026-10-06 20:55:00.850000');
INSERT INTO [usuarios] ([id], [rol_id], [username], [password_hash], [nombre_completo], [email], [telefono], [activo], [ultimo_acceso], [created_at], [updated_at]) VALUES (1003, 1003, 'gerente_admin', '123', 'Gerente Admin Financiero', 'gerente_admin@jehovajireh.com', '+505 8888-0007', True, NULL, '2026-10-06 20:55:00.867000', '2026-10-06 20:55:00.867000');
INSERT INTO [usuarios] ([id], [rol_id], [username], [password_hash], [nombre_completo], [email], [telefono], [activo], [ultimo_acceso], [created_at], [updated_at]) VALUES (1004, 1004, 'encargado_comp', '123', 'Encargado de Compras', 'compras@jehovajireh.com', '+505 8888-0008', True, NULL, '2026-10-06 20:55:00.873000', '2026-10-06 20:55:00.873000');
SET IDENTITY_INSERT [usuarios] OFF;
GO


-- -----------------------------------------------------------------------------
-- SECCIÓN: MÓDULO TRIBUTARIO Y FISCAL (RF129 - RF139: DECLARACIÓN ANUAL DEL IR)
-- -----------------------------------------------------------------------------

-- 1. Tabla: negocio_info_tributaria (RF129)
IF OBJECT_ID('negocio_info_tributaria', 'U') IS NULL
BEGIN
CREATE TABLE [negocio_info_tributaria] (
    [id] int IDENTITY(1,1) NOT NULL,
    [ruc] varchar(30) NOT NULL,
    [razon_social] varchar(200) NOT NULL,
    [nombre_comercial] varchar(200) NOT NULL,
    [actividad_economica] varchar(255) NOT NULL,
    [domicilio_fiscal] varchar(300) NOT NULL,
    [regimen_tributario] varchar(100) DEFAULT ('Régimen General') NOT NULL,
    [fecha_inicio_vigencia] date NOT NULL,
    [fecha_fin_vigencia] date NULL,
    [activo] bit DEFAULT ((1)) NOT NULL,
    [usuario_id] int NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [updated_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_negocio_info_tributaria] PRIMARY KEY ([id]),
    CONSTRAINT [fk_negocio_info_usuario] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id])
);
END
GO

-- 2. Tabla: reglas_tributarias (RF130)
IF OBJECT_ID('reglas_tributarias', 'U') IS NULL
BEGIN
CREATE TABLE [reglas_tributarias] (
    [id] int IDENTITY(1,1) NOT NULL,
    [codigo_regla] varchar(50) NOT NULL,
    [nombre_regla] varchar(150) NOT NULL,
    [regimen_tributario] varchar(100) DEFAULT ('Régimen General') NOT NULL,
    [tipo_parametro] varchar(30) DEFAULT ('Porcentaje') NOT NULL,
    [valor] decimal(18,4) NOT NULL,
    [condiciones_aplicacion] nvarchar(max) NULL,
    [referencia_normativa] varchar(255) NULL,
    [fecha_inicio_vigencia] date NOT NULL,
    [fecha_fin_vigencia] date NULL,
    [activo] bit DEFAULT ((1)) NOT NULL,
    [usuario_id] int NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_reglas_tributarias] PRIMARY KEY ([id]),
    CONSTRAINT [uq_reglas_tributarias_codigo] UNIQUE ([codigo_regla]),
    CONSTRAINT [fk_reglas_trib_usuario] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id])
);
END
GO

-- 3. Tabla: acreditamientos_tributarios (RF132)
IF OBJECT_ID('acreditamientos_tributarios', 'U') IS NULL
BEGIN
CREATE TABLE [acreditamientos_tributarios] (
    [id] int IDENTITY(1,1) NOT NULL,
    [tipo] varchar(50) NOT NULL,
    [concepto] varchar(255) NOT NULL,
    [ejercicio_fiscal] int NOT NULL,
    [periodo_mes] int NULL,
    [fecha] date NOT NULL,
    [numero_referencia] varchar(100) NOT NULL,
    [agente_retenedor_ruc] varchar(30) NULL,
    [agente_retenedor_nombre] varchar(200) NULL,
    [monto_base] decimal(18,2) DEFAULT ((0.00)) NULL,
    [porcentaje_aplicado] decimal(6,2) DEFAULT ((0.00)) NULL,
    [importe_total] decimal(18,2) NOT NULL,
    [importe_aplicado] decimal(18,2) DEFAULT ((0.00)) NULL,
    [documento_respaldo_url] varchar(300) NULL,
    [estado] varchar(30) DEFAULT ('Disponible') NULL,
    [usuario_id] int NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_acreditamientos_tributarios] PRIMARY KEY ([id]),
    CONSTRAINT [fk_acreditamientos_usuario] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id])
);
END
GO

-- 4. Tabla: declaraciones_ir (RF133, RF135, RF137)
IF OBJECT_ID('declaraciones_ir', 'U') IS NULL
BEGIN
CREATE TABLE [declaraciones_ir] (
    [id] int IDENTITY(1,1) NOT NULL,
    [ejercicio_fiscal] int NOT NULL,
    [version] int DEFAULT ((1)) NOT NULL,
    [es_sustitutiva] bit DEFAULT ((0)) NOT NULL,
    [declaracion_anterior_id] int NULL,
    [estado] varchar(30) DEFAULT ('Borrador') NOT NULL,
    [regimen_tributario_aplicado] varchar(100) NOT NULL,
    [datos_fiscales_snapshot] nvarchar(max) NULL,
    [reglas_snapshot] nvarchar(max) NULL,
    [total_ingresos_brutos] decimal(18,2) DEFAULT ((0.00)) NULL,
    [total_costos] decimal(18,2) DEFAULT ((0.00)) NULL,
    [total_gastos_deducibles] decimal(18,2) DEFAULT ((0.00)) NULL,
    [renta_neta_gravable] decimal(18,2) DEFAULT ((0.00)) NULL,
    [ir_calculado] decimal(18,2) DEFAULT ((0.00)) NULL,
    [pago_minimo_definitivo] decimal(18,2) DEFAULT ((0.00)) NULL,
    [ir_determinado] decimal(18,2) DEFAULT ((0.00)) NULL,
    [total_acreditamientos] decimal(18,2) DEFAULT ((0.00)) NULL,
    [saldo_a_pagar] decimal(18,2) DEFAULT ((0.00)) NULL,
    [saldo_a_favor] decimal(18,2) DEFAULT ((0.00)) NULL,
    [tiene_errores_bloqueantes] bit DEFAULT ((0)) NULL,
    [observaciones] nvarchar(max) NULL,
    [usuario_elaboro_id] int NULL,
    [usuario_aprobo_id] int NULL,
    [fecha_aprobacion] datetime NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    [updated_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_declaraciones_ir] PRIMARY KEY ([id]),
    CONSTRAINT [fk_decl_anterior] FOREIGN KEY ([declaracion_anterior_id]) REFERENCES [declaraciones_ir]([id]),
    CONSTRAINT [fk_decl_usuario_elaboro] FOREIGN KEY ([usuario_elaboro_id]) REFERENCES [usuarios]([id]),
    CONSTRAINT [fk_decl_usuario_aprobo] FOREIGN KEY ([usuario_aprobo_id]) REFERENCES [usuarios]([id])
);
END
GO

-- 5. Tabla: declaracion_renglones_detalle (RF133)
IF OBJECT_ID('declaracion_renglones_detalle', 'U') IS NULL
BEGIN
CREATE TABLE [declaracion_renglones_detalle] (
    [id] int IDENTITY(1,1) NOT NULL,
    [declaracion_id] int NOT NULL,
    [seccion] varchar(50) NOT NULL,
    [numero_renglon] int NOT NULL,
    [descripcion_renglon] varchar(255) NOT NULL,
    [tipo_renglon] varchar(30) NOT NULL,
    [importe_base_contable] decimal(18,2) DEFAULT ((0.00)) NULL,
    [importe_ajustes] decimal(18,2) DEFAULT ((0.00)) NULL,
    [importe_declarado] decimal(18,2) DEFAULT ((0.00)) NULL,
    [origen_detalle] nvarchar(max) NULL,
    [cuentas_asociadas] varchar(255) NULL,
    CONSTRAINT [pk_declaracion_renglones_detalle] PRIMARY KEY ([id]),
    CONSTRAINT [fk_renglones_declaracion] FOREIGN KEY ([declaracion_id]) REFERENCES [declaraciones_ir]([id]) ON DELETE CASCADE
);
END
GO

-- 6. Tabla: declaracion_ajustes_fiscales (RF136)
IF OBJECT_ID('declaracion_ajustes_fiscales', 'U') IS NULL
BEGIN
CREATE TABLE [declaracion_ajustes_fiscales] (
    [id] int IDENTITY(1,1) NOT NULL,
    [declaracion_id] int NOT NULL,
    [ejercicio_fiscal] int NOT NULL,
    [numero_renglon] int NOT NULL,
    [concepto] varchar(255) NOT NULL,
    [tipo_ajuste] varchar(50) NOT NULL,
    [efecto] varchar(30) NOT NULL,
    [importe] decimal(18,2) NOT NULL,
    [justificacion] nvarchar(max) NOT NULL,
    [referencia_normativa] varchar(255) NULL,
    [documento_respaldo_url] varchar(300) NULL,
    [usuario_id] int NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_declaracion_ajustes_fiscales] PRIMARY KEY ([id]),
    CONSTRAINT [fk_ajustes_declaracion] FOREIGN KEY ([declaracion_id]) REFERENCES [declaraciones_ir]([id]) ON DELETE CASCADE,
    CONSTRAINT [fk_ajustes_usuario] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id])
);
END
GO

-- 7. Tabla: declaracion_validaciones (RF134)
IF OBJECT_ID('declaracion_validaciones', 'U') IS NULL
BEGIN
CREATE TABLE [declaracion_validaciones] (
    [id] int IDENTITY(1,1) NOT NULL,
    [declaracion_id] int NOT NULL,
    [tipo] varchar(30) NOT NULL,
    [codigo_validacion] varchar(50) NOT NULL,
    [renglon_afectado] int NULL,
    [modulo_origen] varchar(50) NULL,
    [motivo] nvarchar(max) NOT NULL,
    [resuelto] bit DEFAULT ((0)) NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_declaracion_validaciones] PRIMARY KEY ([id]),
    CONSTRAINT [fk_validaciones_declaracion] FOREIGN KEY ([declaracion_id]) REFERENCES [declaraciones_ir]([id]) ON DELETE CASCADE
);
END
GO

-- 8. Tabla: declaracion_presentacion_pagos (RF138, RF139)
IF OBJECT_ID('declaracion_presentacion_pagos', 'U') IS NULL
BEGIN
CREATE TABLE [declaracion_presentacion_pagos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [declaracion_id] int NOT NULL,
    [tipo_evento] varchar(30) NOT NULL,
    [fecha_evento] date NOT NULL,
    [numero_referencia_dgi] varchar(100) NOT NULL,
    [importe_pagado] decimal(18,2) DEFAULT ((0.00)) NULL,
    [banco_caja] varchar(100) NULL,
    [medio_pago] varchar(50) NULL,
    [archivo_constancia_url] varchar(300) NULL,
    [observaciones] nvarchar(max) NULL,
    [usuario_id] int NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_declaracion_presentacion_pagos] PRIMARY KEY ([id]),
    CONSTRAINT [fk_pagos_declaracion] FOREIGN KEY ([declaracion_id]) REFERENCES [declaraciones_ir]([id]),
    CONSTRAINT [fk_pagos_usuario] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id])
);
END
GO

-- Datos iniciales del módulo tributario
IF NOT EXISTS (SELECT 1 FROM [negocio_info_tributaria] WHERE [ruc] = 'J0310000000001')
BEGIN
INSERT INTO [negocio_info_tributaria] ([ruc], [razon_social], [nombre_comercial], [actividad_economica], [domicilio_fiscal], [regimen_tributario], [fecha_inicio_vigencia], [activo], [usuario_id])
VALUES ('J0310000000001', 'Jehová Jireh Moto Repuestos y Servicios', 'Jehová Jireh Moto Repuestos', 'Comercio al por menor de repuestos, lubricantes y mantenimiento de motocicletas', 'Del Hospital Amistad Japón-Nicaragua 2 cuadras al norte, Granada, Nicaragua', 'Régimen General', '2026-01-01', 1, 1);
END
GO

IF NOT EXISTS (SELECT 1 FROM [reglas_tributarias] WHERE [codigo_regla] = 'IR_ANUAL_GENERAL')
BEGIN
INSERT INTO [reglas_tributarias] ([codigo_regla], [nombre_regla], [regimen_tributario], [tipo_parametro], [valor], [condiciones_aplicacion], [referencia_normativa], [fecha_inicio_vigencia], [activo], [usuario_id])
VALUES 
('IR_ANUAL_GENERAL', 'Tasa General IR Actividades Económicas', 'Régimen General', 'Porcentaje', 30.0000, 'Aplica sobre la renta neta gravable positiva al cierre fiscal.', 'Ley 822 Art. 52', '2026-01-01', 1, 1),
('PMD_ANUAL_INGRESOS', 'Pago Mínimo Definitivo Anual', 'Régimen General', 'Porcentaje', 1.0000, '1% sobre la renta bruta gravable anual.', 'Ley 822 Art. 59', '2026-01-01', 1, 1),
('RETENCION_IR_BIENES_2', 'Retención Definitiva IR en la Fuente (Bienes)', 'Régimen General', 'Porcentaje', 2.0000, 'Retención que aplican grandes contribuyentes en compra de repuestos.', 'Ley 822 Art. 65', '2026-01-01', 1, 1),
('RETENCION_IR_SERVICIOS_10', 'Retención Definitiva IR (Servicios Técnicos)', 'Régimen General', 'Porcentaje', 10.0000, 'Retención por servicios profesionales o técnicos de taller.', 'Ley 822 Art. 65', '2026-01-01', 1, 1),
('ANTICIPO_MENSUAL_1', 'Anticipo Mensual a Cuenta del IR', 'Régimen General', 'Porcentaje', 1.0000, 'Anticipo mensual liquidado en declaraciones mensuales.', 'Ley 822 Art. 61', '2026-01-01', 1, 1);
END
GO

-- -----------------------------------------------------------------------------
-- SECCIÓN: MÓDULO DE ESTADO DE FLUJO DE EFECTIVO (RF96 - RF102)
-- -----------------------------------------------------------------------------

-- 1. Actualización de columnas en cuentas_contables (RF96)
IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='cuentas_contables' AND COLUMN_NAME='flujo_categoria')
BEGIN
    ALTER TABLE [cuentas_contables] ADD [flujo_categoria] varchar(30) NULL;
END
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='cuentas_contables' AND COLUMN_NAME='es_efectivo_equivalente')
BEGIN
    ALTER TABLE [cuentas_contables] ADD [es_efectivo_equivalente] bit DEFAULT ((0)) NULL;
END
GO

IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='cuentas_contables' AND COLUMN_NAME='ajuste_no_monetario')
BEGIN
    ALTER TABLE [cuentas_contables] ADD [ajuste_no_monetario] bit DEFAULT ((0)) NOT NULL;
END
GO

-- Etiquetas iniciales para cuentas contables
UPDATE [cuentas_contables] SET [flujo_categoria] = 'Efectivo_Equivalente', [es_efectivo_equivalente] = 1 WHERE [codigo] IN ('1.1.01', '1.1.02');
UPDATE [cuentas_contables] SET [flujo_categoria] = 'Inversion', [es_efectivo_equivalente] = 0 WHERE [codigo] IN ('1.2.01', '1.2.02', '1.2.03');
UPDATE [cuentas_contables] SET [flujo_categoria] = 'Financiamiento', [es_efectivo_equivalente] = 0 WHERE [codigo] IN ('3.1.01', '3.1.02');
UPDATE [cuentas_contables] SET [flujo_categoria] = 'Operacion', [es_efectivo_equivalente] = 0 WHERE [flujo_categoria] IS NULL OR [codigo] = '2.1.02';
UPDATE [cuentas_contables] SET [ajuste_no_monetario] = 1 WHERE [codigo] = '6.1.09';
GO

-- 2. Tabla: conciliaciones_bancarias (RF98)
IF OBJECT_ID('conciliaciones_bancarias', 'U') IS NULL
BEGIN
CREATE TABLE [conciliaciones_bancarias] (
    [id] int IDENTITY(1,1) NOT NULL,
    [cuenta_id] int NOT NULL,
    [anio] int NOT NULL,
    [mes] int NOT NULL,
    [fecha_corte] date NOT NULL,
    [saldo_segun_libros] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [saldo_segun_banco] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [diferencia] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [estado] varchar(30) DEFAULT ('Borrador') NULL,
    [observaciones] nvarchar(max) NULL,
    [usuario_id] int NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_conciliaciones_bancarias] PRIMARY KEY ([id]),
    CONSTRAINT [fk_conciliacion_cuenta] FOREIGN KEY ([cuenta_id]) REFERENCES [cuentas_contables]([id]),
    CONSTRAINT [fk_conciliacion_usuario] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id])
);
END
GO

-- 3. Tabla: conciliacion_partidas_pendientes (RF98)
IF OBJECT_ID('conciliacion_partidas_pendientes', 'U') IS NULL
BEGIN
CREATE TABLE [conciliacion_partidas_pendientes] (
    [id] int IDENTITY(1,1) NOT NULL,
    [conciliacion_id] int NOT NULL,
    [tipo_partida] varchar(50) NOT NULL,
    [fecha] date NOT NULL,
    [numero_documento_referencia] varchar(100) NOT NULL,
    [descripcion] varchar(255) NOT NULL,
    [monto] decimal(18,2) NOT NULL,
    [efecto_en_saldo] varchar(20) NOT NULL,
    [esta_conciliada] bit DEFAULT ((0)) NULL,
    [movimiento_contable_id] int NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_conciliacion_partidas_pendientes] PRIMARY KEY ([id]),
    CONSTRAINT [fk_partida_conciliacion] FOREIGN KEY ([conciliacion_id]) REFERENCES [conciliaciones_bancarias]([id]) ON DELETE CASCADE,
    CONSTRAINT [fk_partida_movimiento] FOREIGN KEY ([movimiento_contable_id]) REFERENCES [movimientos_contables]([id])
);
END
GO

-- 4. Tabla: estados_flujo_efectivo (RF101, RF102)
IF OBJECT_ID('estados_flujo_efectivo', 'U') IS NULL
BEGIN
CREATE TABLE [estados_flujo_efectivo] (
    [id] int IDENTITY(1,1) NOT NULL,
    [ejercicio_fiscal] int NOT NULL,
    [periodo_tipo] varchar(20) DEFAULT ('Anual') NOT NULL,
    [fecha_inicio] date NOT NULL,
    [fecha_fin] date NOT NULL,
    [metodo] varchar(20) DEFAULT ('Indirecto') NOT NULL,
    [saldo_inicial_efectivo] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [flujo_neto_operacion] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [flujo_neto_inversion] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [flujo_neto_financiamiento] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [variacion_neta_efectivo] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [saldo_final_calculado] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [saldo_final_balance_general] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [diferencia_cuadratura] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [esta_cuadrado] bit DEFAULT ((0)) NOT NULL,
    [estado] varchar(30) DEFAULT ('Borrador') NULL,
    [observaciones] nvarchar(max) NULL,
    [usuario_elaboro_id] int NULL,
    [usuario_aprobo_id] int NULL,
    [fecha_aprobacion] datetime NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_estados_flujo_efectivo] PRIMARY KEY ([id]),
    CONSTRAINT [fk_flujo_usuario_elaboro] FOREIGN KEY ([usuario_elaboro_id]) REFERENCES [usuarios]([id]),
    CONSTRAINT [fk_flujo_usuario_aprobo] FOREIGN KEY ([usuario_aprobo_id]) REFERENCES [usuarios]([id])
);
END
GO

-- 5. Tabla: estado_flujo_efectivo_detalle (RF101)
IF OBJECT_ID('estado_flujo_efectivo_detalle', 'U') IS NULL
BEGIN
CREATE TABLE [estado_flujo_efectivo_detalle] (
    [id] int IDENTITY(1,1) NOT NULL,
    [flujo_id] int NOT NULL,
    [actividad] varchar(30) NOT NULL,
    [concepto] varchar(255) NOT NULL,
    [tipo_movimiento] varchar(20) NOT NULL,
    [importe] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [orden_presentacion] int DEFAULT ((1)) NOT NULL,
    CONSTRAINT [pk_estado_flujo_efectivo_detalle] PRIMARY KEY ([id]),
    CONSTRAINT [fk_detalle_flujo] FOREIGN KEY ([flujo_id]) REFERENCES [estados_flujo_efectivo]([id]) ON DELETE CASCADE
);
END
GO

-- 6. Tabla: flujo_ajustes_no_monetarios (RF100)
IF OBJECT_ID('flujo_ajustes_no_monetarios', 'U') IS NULL
BEGIN
CREATE TABLE [flujo_ajustes_no_monetarios] (
    [id] int IDENTITY(1,1) NOT NULL,
    [flujo_id] int NOT NULL,
    [concepto] varchar(255) NOT NULL,
    [cuenta_id] int NULL,
    [efecto] varchar(20) NOT NULL,
    [importe] decimal(18,2) DEFAULT ((0.00)) NOT NULL,
    [justificacion] nvarchar(max) NOT NULL,
    [usuario_id] int NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_flujo_ajustes_no_monetarios] PRIMARY KEY ([id]),
    CONSTRAINT [fk_ajustes_no_monetarios_flujo] FOREIGN KEY ([flujo_id]) REFERENCES [estados_flujo_efectivo]([id]) ON DELETE CASCADE,
    CONSTRAINT [fk_ajustes_no_monetarios_cuenta] FOREIGN KEY ([cuenta_id]) REFERENCES [cuentas_contables]([id]),
    CONSTRAINT [fk_ajustes_no_monetarios_usuario] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id])
);
END
GO

-- 7. Tabla: flujo_reclasificaciones_auditoria (RF97, RF99)
IF OBJECT_ID('flujo_reclasificaciones_auditoria', 'U') IS NULL
BEGIN
CREATE TABLE [flujo_reclasificaciones_auditoria] (
    [id] int IDENTITY(1,1) NOT NULL,
    [asiento_id] int NULL,
    [movimiento_id] int NULL,
    [origen_modulo] varchar(50) NOT NULL,
    [actividad_anterior] varchar(30) NULL,
    [actividad_nueva] varchar(30) NOT NULL,
    [motivo_reclasificacion] nvarchar(max) NOT NULL,
    [usuario_id] int NOT NULL,
    [created_at] datetime DEFAULT (getdate()) NULL,
    CONSTRAINT [pk_flujo_reclasificaciones_auditoria] PRIMARY KEY ([id]),
    CONSTRAINT [fk_reclasif_asiento] FOREIGN KEY ([asiento_id]) REFERENCES [asientos_contables]([id]),
    CONSTRAINT [fk_reclasif_movimiento] FOREIGN KEY ([movimiento_id]) REFERENCES [movimientos_contables]([id]),
    CONSTRAINT [fk_reclasif_usuario] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id])
);
END
GO

-- 8. Tabla: flujo_eventos (RF96-RF102 Auditoría de eventos y versiones)
IF OBJECT_ID('flujo_eventos', 'U') IS NULL
BEGIN
CREATE TABLE [flujo_eventos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [tipo] varchar(30) NOT NULL,
    [clave] varchar(100) NOT NULL,
    [contenido] nvarchar(max) NOT NULL,
    [motivo] nvarchar(1000) NOT NULL,
    [usuario_id] int NOT NULL,
    [created_at] datetime2 NOT NULL DEFAULT SYSUTCDATETIME(),
    CONSTRAINT [pk_flujo_eventos] PRIMARY KEY ([id]),
    CONSTRAINT [fk_flujo_eventos_usuario] FOREIGN KEY ([usuario_id]) REFERENCES [usuarios]([id])
);
CREATE INDEX [IX_flujo_eventos_tipo_clave] ON [flujo_eventos]([tipo], [clave], [id]);
END
GO

-- 9. Índice de unicidad para conciliaciones bancarias por cuenta y período
IF NOT EXISTS (SELECT 1 FROM sys.indexes WHERE name = 'UX_conciliacion_periodo' AND object_id = OBJECT_ID('conciliaciones_bancarias'))
BEGIN
    CREATE UNIQUE INDEX [UX_conciliacion_periodo] ON [conciliaciones_bancarias]([cuenta_id], [anio], [mes]);
END
GO

EXEC sp_MSforeachtable 'ALTER TABLE ? WITH CHECK CHECK CONSTRAINT ALL';
GO

PRINT 'Base de datos jehova_jireh_db configurada y actualizada al 100% con éxito!';
GO

-- Ampliación aditiva de RRHH. No reescribe nóminas ni dotaciones históricas.
IF COL_LENGTH('detalle_nomina', 'historico_salario') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_salario] decimal(12,2) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_nombre') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_nombre] nvarchar(150) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_identificacion') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_identificacion] nvarchar(50) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_cargo') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_cargo] nvarchar(100) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_inss') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_inss] nvarchar(50) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_ingreso') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_ingreso] date NULL;
GO
IF COL_LENGTH('higiene_epp', 'area') IS NULL
    ALTER TABLE [higiene_epp] ADD [area] nvarchar(50) NULL;
GO
IF COL_LENGTH('higiene_epp', 'repone_a_id') IS NULL
    ALTER TABLE [higiene_epp] ADD [repone_a_id] int NULL;
GO
IF COL_LENGTH('higiene_epp', 'motivo_reposicion') IS NULL
    ALTER TABLE [higiene_epp] ADD [motivo_reposicion] nvarchar(255) NULL;
GO
IF COL_LENGTH('higiene_riesgos', 'fecha_revision') IS NULL
    ALTER TABLE [higiene_riesgos] ADD [fecha_revision] date NULL;
GO
IF COL_LENGTH('pagos_nomina', 'registrado_por') IS NULL
    ALTER TABLE pagos_nomina ADD registrado_por nvarchar(100) NULL;
GO
IF OBJECT_ID('rrhh_archivos', 'U') IS NULL
BEGIN
CREATE TABLE [rrhh_archivos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [clase] varchar(20) NOT NULL,
    [referencia_id] int NOT NULL,
    [nombre_archivo] nvarchar(255) NOT NULL,
    [mime] varchar(100) NOT NULL,
    [contenido] varbinary(MAX) NOT NULL,
    [registrado_por] nvarchar(100) NOT NULL,
    [fecha_registro] datetime DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [pk_rrhh_archivos] PRIMARY KEY ([id]),
    CONSTRAINT [uq_rrhh_archivo_referencia] UNIQUE ([clase], [referencia_id])
);
END
GO
IF OBJECT_ID('higiene_riesgo_seguimientos', 'U') IS NULL
BEGIN
CREATE TABLE [higiene_riesgo_seguimientos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [riesgo_id] int NOT NULL,
    [fecha_revision] date NOT NULL,
    [observaciones] nvarchar(4000) NOT NULL,
    [estado] nvarchar(30) NOT NULL,
    [registrado_por] nvarchar(100) NOT NULL,
    CONSTRAINT [pk_higiene_riesgo_seguimientos] PRIMARY KEY ([id]),
    CONSTRAINT [fk_seguimiento_riesgo] FOREIGN KEY ([riesgo_id]) REFERENCES higiene_riesgos(id)
);
END
GO
