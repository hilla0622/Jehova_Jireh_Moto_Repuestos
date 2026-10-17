"""
=============================================================================
  SCRIPT DE MIGRACIÓN: MÓDULO TRIBUTARIO Y FISCAL (RF129 - RF139)
  Sistema Jehová Jireh Moto Repuestos
  Fecha: Octubre 2026
  
  Crea las 8 tablas requeridas para la preparación, validación,
  liquidación y seguimiento de la Declaración Anual del IR ante la DGI.
=============================================================================
"""

import os
import sys
import pyodbc

def get_connection():
    db_name = 'jehova_jireh_db'
    comp_name = os.environ.get('COMPUTERNAME', 'LAPTOP-CNR3S3I3')
    servidores = [comp_name, '.', 'localhost', 'HILLARY']
    
    for srv in servidores:
        try:
            conn_str = (
                r'DRIVER={ODBC Driver 17 for SQL Server};'
                fr'SERVER={srv};'
                fr'DATABASE={db_name};'
                r'Trusted_Connection=yes;'
            )
            conn = pyodbc.connect(conn_str, timeout=3)
            conn.autocommit = True
            print(f"[OK] Conectado exitosamente a SQL Server: {srv}")
            return conn
        except Exception:
            continue
            
    print("[ERROR] No se pudo conectar a SQL Server en ningún servidor conocido.")
    sys.exit(1)

def ejecutar(cursor, desc, sql):
    try:
        cursor.execute(sql)
        print(f"  [OK] {desc}")
    except Exception as e:
        print(f"  [WARN] Error en '{desc}': {e}")

def run_migration():
    conn = get_connection()
    cursor = conn.cursor()
    print("\n" + "="*70)
    print("  CREANDO TABLAS DEL MÓDULO TRIBUTARIO Y FISCAL")
    print("="*70)

    # 1. TABLA: negocio_info_tributaria (RF129)
    ejecutar(cursor, "Tabla: negocio_info_tributaria", """
    IF OBJECT_ID('negocio_info_tributaria', 'U') IS NULL
    BEGIN
        CREATE TABLE negocio_info_tributaria (
            id INT IDENTITY(1,1) PRIMARY KEY,
            ruc VARCHAR(30) NOT NULL,
            razon_social VARCHAR(200) NOT NULL,
            nombre_comercial VARCHAR(200) NOT NULL,
            actividad_economica VARCHAR(255) NOT NULL,
            domicilio_fiscal VARCHAR(300) NOT NULL,
            regimen_tributario VARCHAR(100) NOT NULL DEFAULT 'Régimen General',
            fecha_inicio_vigencia DATE NOT NULL,
            fecha_fin_vigencia DATE NULL,
            activo BIT NOT NULL DEFAULT 1,
            usuario_id INT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_negocio_info_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    END
    """)

    # 2. TABLA: reglas_tributarias (RF130)
    ejecutar(cursor, "Tabla: reglas_tributarias", """
    IF OBJECT_ID('reglas_tributarias', 'U') IS NULL
    BEGIN
        CREATE TABLE reglas_tributarias (
            id INT IDENTITY(1,1) PRIMARY KEY,
            codigo_regla VARCHAR(50) NOT NULL UNIQUE,
            nombre_regla VARCHAR(150) NOT NULL,
            regimen_tributario VARCHAR(100) NOT NULL DEFAULT 'Régimen General',
            tipo_parametro VARCHAR(30) NOT NULL DEFAULT 'Porcentaje',
            valor DECIMAL(18,4) NOT NULL,
            condiciones_aplicacion NVARCHAR(MAX) NULL,
            referencia_normativa VARCHAR(255) NULL,
            fecha_inicio_vigencia DATE NOT NULL,
            fecha_fin_vigencia DATE NULL,
            activo BIT NOT NULL DEFAULT 1,
            usuario_id INT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_reglas_trib_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    END
    """)

    # 3. TABLA: acreditamientos_tributarios (RF132)
    ejecutar(cursor, "Tabla: acreditamientos_tributarios", """
    IF OBJECT_ID('acreditamientos_tributarios', 'U') IS NULL
    BEGIN
        CREATE TABLE acreditamientos_tributarios (
            id INT IDENTITY(1,1) PRIMARY KEY,
            tipo VARCHAR(50) NOT NULL, -- 'RETENCION_SUFRIDA', 'ANTICIPO_PAGADO', 'CREDITO_FISCAL'
            concepto VARCHAR(255) NOT NULL,
            ejercicio_fiscal INT NOT NULL,
            periodo_mes INT NULL,
            fecha DATE NOT NULL,
            numero_referencia VARCHAR(100) NOT NULL,
            agente_retenedor_ruc VARCHAR(30) NULL,
            agente_retenedor_nombre VARCHAR(200) NULL,
            monto_base DECIMAL(18,2) DEFAULT 0.00,
            porcentaje_aplicado DECIMAL(6,2) DEFAULT 0.00,
            importe_total DECIMAL(18,2) NOT NULL,
            importe_aplicado DECIMAL(18,2) DEFAULT 0.00,
            documento_respaldo_url VARCHAR(300) NULL,
            estado VARCHAR(30) DEFAULT 'Disponible', -- 'Disponible', 'Aplicado Total', 'Aplicado Parcial', 'Anulado'
            usuario_id INT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_acreditamientos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    END
    """)

    # 4. TABLA: declaraciones_ir (RF133, RF135, RF137)
    ejecutar(cursor, "Tabla: declaraciones_ir", """
    IF OBJECT_ID('declaraciones_ir', 'U') IS NULL
    BEGIN
        CREATE TABLE declaraciones_ir (
            id INT IDENTITY(1,1) PRIMARY KEY,
            ejercicio_fiscal INT NOT NULL,
            version INT NOT NULL DEFAULT 1,
            es_sustitutiva BIT NOT NULL DEFAULT 0,
            declaracion_anterior_id INT NULL,
            estado VARCHAR(30) NOT NULL DEFAULT 'Borrador', -- 'Borrador', 'En Revision', 'Aprobada', 'Presentada'
            regimen_tributario_aplicado VARCHAR(100) NOT NULL,
            datos_fiscales_snapshot NVARCHAR(MAX) NULL,
            reglas_snapshot NVARCHAR(MAX) NULL,
            total_ingresos_brutos DECIMAL(18,2) DEFAULT 0.00,
            total_costos DECIMAL(18,2) DEFAULT 0.00,
            total_gastos_deducibles DECIMAL(18,2) DEFAULT 0.00,
            renta_neta_gravable DECIMAL(18,2) DEFAULT 0.00,
            ir_calculado DECIMAL(18,2) DEFAULT 0.00,
            pago_minimo_definitivo DECIMAL(18,2) DEFAULT 0.00,
            ir_determinado DECIMAL(18,2) DEFAULT 0.00,
            total_acreditamientos DECIMAL(18,2) DEFAULT 0.00,
            saldo_a_pagar DECIMAL(18,2) DEFAULT 0.00,
            saldo_a_favor DECIMAL(18,2) DEFAULT 0.00,
            tiene_errores_bloqueantes BIT DEFAULT 0,
            observaciones NVARCHAR(MAX) NULL,
            usuario_elaboro_id INT NULL,
            usuario_aprobo_id INT NULL,
            fecha_aprobacion DATETIME NULL,
            created_at DATETIME DEFAULT GETDATE(),
            updated_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_decl_anterior FOREIGN KEY (declaracion_anterior_id) REFERENCES declaraciones_ir(id),
            CONSTRAINT fk_decl_usuario_elaboro FOREIGN KEY (usuario_elaboro_id) REFERENCES usuarios(id),
            CONSTRAINT fk_decl_usuario_aprobo FOREIGN KEY (usuario_aprobo_id) REFERENCES usuarios(id)
        );
    END
    """)

    # 5. TABLA: declaracion_renglones_detalle (RF133)
    ejecutar(cursor, "Tabla: declaracion_renglones_detalle", """
    IF OBJECT_ID('declaracion_renglones_detalle', 'U') IS NULL
    BEGIN
        CREATE TABLE declaracion_renglones_detalle (
            id INT IDENTITY(1,1) PRIMARY KEY,
            declaracion_id INT NOT NULL,
            seccion VARCHAR(50) NOT NULL, -- 'PATRIMONIO', 'INGRESOS', 'COSTOS_GASTOS', 'LIQUIDACION'
            numero_renglon INT NOT NULL,
            descripcion_renglon VARCHAR(255) NOT NULL,
            tipo_renglon VARCHAR(30) NOT NULL, -- 'Calculado', 'Contable', 'Manual', 'No Aplicable'
            importe_base_contable DECIMAL(18,2) DEFAULT 0.00,
            importe_ajustes DECIMAL(18,2) DEFAULT 0.00,
            importe_declarado DECIMAL(18,2) DEFAULT 0.00,
            origen_detalle NVARCHAR(MAX) NULL,
            cuentas_asociadas VARCHAR(255) NULL,
            CONSTRAINT fk_renglones_declaracion FOREIGN KEY (declaracion_id) REFERENCES declaraciones_ir(id) ON DELETE CASCADE
        );
    END
    """)

    # 6. TABLA: declaracion_ajustes_fiscales (RF136)
    ejecutar(cursor, "Tabla: declaracion_ajustes_fiscales", """
    IF OBJECT_ID('declaracion_ajustes_fiscales', 'U') IS NULL
    BEGIN
        CREATE TABLE declaracion_ajustes_fiscales (
            id INT IDENTITY(1,1) PRIMARY KEY,
            declaracion_id INT NOT NULL,
            ejercicio_fiscal INT NOT NULL,
            numero_renglon INT NOT NULL,
            concepto VARCHAR(255) NOT NULL,
            tipo_ajuste VARCHAR(50) NOT NULL, -- 'Gasto No Deducible', 'Ingreso No Gravable', 'Deducción Especial'
            efecto VARCHAR(30) NOT NULL, -- 'Aumenta Renta', 'Disminuye Renta', 'Aumenta Ingreso'
            importe DECIMAL(18,2) NOT NULL,
            justificacion NVARCHAR(MAX) NOT NULL,
            referencia_normativa VARCHAR(255) NULL,
            documento_respaldo_url VARCHAR(300) NULL,
            usuario_id INT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_ajustes_declaracion FOREIGN KEY (declaracion_id) REFERENCES declaraciones_ir(id) ON DELETE CASCADE,
            CONSTRAINT fk_ajustes_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    END
    """)

    # 7. TABLA: declaracion_validaciones (RF134)
    ejecutar(cursor, "Tabla: declaracion_validaciones", """
    IF OBJECT_ID('declaracion_validaciones', 'U') IS NULL
    BEGIN
        CREATE TABLE declaracion_validaciones (
            id INT IDENTITY(1,1) PRIMARY KEY,
            declaracion_id INT NOT NULL,
            tipo VARCHAR(30) NOT NULL, -- 'Bloqueante', 'Advertencia'
            codigo_validacion VARCHAR(50) NOT NULL,
            renglon_afectado INT NULL,
            modulo_origen VARCHAR(50) NULL,
            motivo NVARCHAR(MAX) NOT NULL,
            resuelto BIT DEFAULT 0,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_validaciones_declaracion FOREIGN KEY (declaracion_id) REFERENCES declaraciones_ir(id) ON DELETE CASCADE
        );
    END
    """)

    # 8. TABLA: declaracion_presentacion_pagos (RF138, RF139)
    ejecutar(cursor, "Tabla: declaracion_presentacion_pagos", """
    IF OBJECT_ID('declaracion_presentacion_pagos', 'U') IS NULL
    BEGIN
        CREATE TABLE declaracion_presentacion_pagos (
            id INT IDENTITY(1,1) PRIMARY KEY,
            declaracion_id INT NOT NULL,
            tipo_evento VARCHAR(30) NOT NULL, -- 'Presentacion_DGI', 'Pago_Impuesto'
            fecha_evento DATE NOT NULL,
            numero_referencia_dgi VARCHAR(100) NOT NULL,
            importe_pagado DECIMAL(18,2) DEFAULT 0.00,
            banco_caja VARCHAR(100) NULL,
            medio_pago VARCHAR(50) NULL,
            archivo_constancia_url VARCHAR(300) NULL,
            observaciones NVARCHAR(MAX) NULL,
            usuario_id INT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_pagos_declaracion FOREIGN KEY (declaracion_id) REFERENCES declaraciones_ir(id),
            CONSTRAINT fk_pagos_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    END
    """)

    # =========================================================================
    # DATOS INICIALES (CATÁLOGOS FISCALES - NICARAGUA DGI)
    # =========================================================================
    print("\n" + "="*70)
    print("  INSERTANDO DATOS INICIALES (CATÁLOGOS FISCALES)")
    print("="*70)

    # 1. Datos iniciales del negocio
    ejecutar(cursor, "Datos iniciales: negocio_info_tributaria", """
    IF NOT EXISTS (SELECT 1 FROM negocio_info_tributaria WHERE ruc = 'J0310000000001')
    BEGIN
        INSERT INTO negocio_info_tributaria (
            ruc, razon_social, nombre_comercial, actividad_economica,
            domicilio_fiscal, regimen_tributario, fecha_inicio_vigencia, activo, usuario_id
        ) VALUES (
            'J0310000000001',
            'Jehová Jireh Moto Repuestos y Servicios',
            'Jehová Jireh Moto Repuestos',
            'Comercio al por menor de repuestos, lubricantes y mantenimiento de motocicletas',
            'Del Hospital Amistad Japón-Nicaragua 2 cuadras al norte, Granada, Nicaragua',
            'Régimen General',
            '2026-01-01',
            1,
            1
        );
    END
    """)

    # 2. Reglas tributarias iniciales (Ley 822 de Concertación Tributaria)
    reglas = [
        ('IR_ANUAL_GENERAL', 'Tasa General IR Actividades Económicas', 'Régimen General', 'Porcentaje', 30.0000, 'Aplica sobre la renta neta gravable positiva al cierre fiscal.', 'Ley 822 Art. 52', '2026-01-01'),
        ('PMD_ANUAL_INGRESOS', 'Pago Mínimo Definitivo Anual', 'Régimen General', 'Porcentaje', 1.0000, '1% sobre la renta bruta gravable anual.', 'Ley 822 Art. 59', '2026-01-01'),
        ('RETENCION_IR_BIENES_2', 'Retención Definitiva IR en la Fuente (Bienes)', 'Régimen General', 'Porcentaje', 2.0000, 'Retención que aplican grandes contribuyentes en compra de repuestos.', 'Ley 822 Art. 65', '2026-01-01'),
        ('RETENCION_IR_SERVICIOS_10', 'Retención Definitiva IR (Servicios Técnicos)', 'Régimen General', 'Porcentaje', 10.0000, 'Retención por servicios profesionales o técnicos de taller.', 'Ley 822 Art. 65', '2026-01-01'),
        ('ANTICIPO_MENSUAL_1', 'Anticipo Mensual a Cuenta del IR', 'Régimen General', 'Porcentaje', 1.0000, 'Anticipo mensual liquidado en declaraciones mensuales.', 'Ley 822 Art. 61', '2026-01-01')
    ]

    for codigo, nombre, regimen, tipo, valor, cond, ref, vigencia in reglas:
        sql = f"""
        IF NOT EXISTS (SELECT 1 FROM reglas_tributarias WHERE codigo_regla = '{codigo}')
        BEGIN
            INSERT INTO reglas_tributarias (
                codigo_regla, nombre_regla, regimen_tributario, tipo_parametro,
                valor, condiciones_aplicacion, referencia_normativa, fecha_inicio_vigencia, activo, usuario_id
            ) VALUES (
                '{codigo}', '{nombre}', '{regimen}', '{tipo}',
                {valor}, '{cond}', '{ref}', '{vigencia}', 1, 1
            );
        END
        """
        ejecutar(cursor, f"Regla tributaria: {codigo}", sql)

    conn.close()
    print("\n" + "="*70)
    print("  MIGRACIÓN COMPLETADA EXITOSAMENTE EN SQL SERVER")
    print("="*70)

if __name__ == '__main__':
    run_migration()
