-- ==============================================================================
-- MIGRACIÓN RRHH v2 — Módulo Completo de Recursos Humanos y Nómina
-- Archivo: database_rrhh_migracion.sql
-- 
-- INSTRUCCIONES: Ejecutar este script UNA SOLA VEZ en SSMS sobre jehova_jireh_db.
-- NO borra datos existentes — solo agrega columnas y tablas nuevas.
-- ==============================================================================

USE jehova_jireh_db;
GO

-- =============================================================
-- 1. Ampliar tabla EMPLEADOS con campos faltantes
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('empleados') AND name = 'num_inss')
    ALTER TABLE empleados ADD num_inss VARCHAR(20) NULL;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('empleados') AND name = 'telefono')
    ALTER TABLE empleados ADD telefono VARCHAR(25) NULL;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('empleados') AND name = 'email')
    ALTER TABLE empleados ADD email VARCHAR(100) NULL;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('empleados') AND name = 'dias_vacaciones_disponibles')
    ALTER TABLE empleados ADD dias_vacaciones_disponibles DECIMAL(5,1) NOT NULL DEFAULT 0.0;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('empleados') AND name = 'observaciones')
    ALTER TABLE empleados ADD observaciones VARCHAR(500) NULL;
GO

-- =============================================================
-- 2. Ampliar cabecera de NOMINA
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('nomina') AND name = 'inss_patronal_total')
    ALTER TABLE nomina ADD inss_patronal_total DECIMAL(12,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('nomina') AND name = 'provision_vac_total')
    ALTER TABLE nomina ADD provision_vac_total DECIMAL(12,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('nomina') AND name = 'provision_agui_total')
    ALTER TABLE nomina ADD provision_agui_total DECIMAL(12,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('nomina') AND name = 'estado')
    ALTER TABLE nomina ADD estado VARCHAR(20) NOT NULL DEFAULT 'CERRADA';
GO

-- =============================================================
-- 3. Ampliar DETALLE_NOMINA con cargas patronales y provisiones
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'ingresos_extra')
    ALTER TABLE detalle_nomina ADD ingresos_extra DECIMAL(12,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'inss_patronal')
    ALTER TABLE detalle_nomina ADD inss_patronal DECIMAL(12,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'provision_vacaciones')
    ALTER TABLE detalle_nomina ADD provision_vacaciones DECIMAL(12,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'provision_aguinaldo')
    ALTER TABLE detalle_nomina ADD provision_aguinaldo DECIMAL(12,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'kpi_comision')
    ALTER TABLE detalle_nomina ADD kpi_comision DECIMAL(12,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'adelanto_salarial')
    ALTER TABLE detalle_nomina ADD adelanto_salarial DECIMAL(12,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'dias_trabajados')
    ALTER TABLE detalle_nomina ADD dias_trabajados DECIMAL(4,1) NOT NULL DEFAULT 15.0;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'vac_acumulada')
    ALTER TABLE detalle_nomina ADD vac_acumulada DECIMAL(5,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'vac_mes')
    ALTER TABLE detalle_nomina ADD vac_mes DECIMAL(5,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'vac_descansados')
    ALTER TABLE detalle_nomina ADD vac_descansados DECIMAL(5,2) NOT NULL DEFAULT 0.00;
GO

IF NOT EXISTS (SELECT * FROM sys.columns WHERE object_id = OBJECT_ID('detalle_nomina') AND name = 'vac_saldo_final')
    ALTER TABLE detalle_nomina ADD vac_saldo_final DECIMAL(5,2) NOT NULL DEFAULT 0.00;
GO

-- =============================================================
-- 4. NUEVA TABLA: Movimientos Laborales (vacaciones / permisos / faltas)
-- =============================================================
IF NOT EXISTS (SELECT * FROM sys.objects WHERE object_id = OBJECT_ID(N'movimientos_laborales') AND type = 'U')
BEGIN
    CREATE TABLE movimientos_laborales (
        id           INT IDENTITY(1,1) PRIMARY KEY,
        empleado_id  INT NOT NULL,
        tipo         VARCHAR(30) NOT NULL
                     CHECK (tipo IN ('VACACIONES', 'PERMISO_CON_GOCE', 'PERMISO_SIN_GOCE', 'FALTA')),
        fecha_inicio DATE NOT NULL,
        fecha_fin    DATE NOT NULL,
        dias_tomados DECIMAL(4,1) NOT NULL,
        observacion  VARCHAR(255) NULL,
        created_at   DATETIME DEFAULT GETDATE(),
        CONSTRAINT fk_movlab_empleado
            FOREIGN KEY (empleado_id) REFERENCES empleados(id)
    );
    PRINT 'Tabla movimientos_laborales creada correctamente.';
END
ELSE
    PRINT 'Tabla movimientos_laborales ya existe, se omite.';
GO

-- =============================================================
-- 5. Insertar rol "Responsable de Recursos Humanos" si no existe
-- =============================================================
IF NOT EXISTS (SELECT id FROM roles WHERE nombre = 'Responsable de Recursos Humanos')
BEGIN
    INSERT INTO roles (nombre, descripcion)
    VALUES ('Responsable de Recursos Humanos',
            'Gestion de empleados, vacaciones, permisos y generacion de nominas mensuales.');
    PRINT 'Rol Responsable de Recursos Humanos insertado.';
END
ELSE
    PRINT 'Rol ya existe, se omite.';
GO

PRINT '=== Migracion RRHH v2 completada exitosamente ===';
GO
