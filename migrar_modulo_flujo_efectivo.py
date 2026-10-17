"""
=============================================================================
  SCRIPT DE MIGRACIÓN: MÓDULO DE ESTADO DE FLUJO DE EFECTIVO (RF96 - RF102)
  Sistema Jehová Jireh Moto Repuestos
  Fecha: Octubre 2026
  
  1. Modifica la tabla 'cuentas_contables' agregando clasificación de flujo.
  2. Asigna etiquetas contables estándar (NIIF para PYMES Sección 7 / NIC 7).
  3. Crea las tablas de conciliación bancaria, estados de flujo, detalle,
     ajustes no monetarios y auditoría de reclasificaciones.
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
            
    print("[ERROR] No se pudo conectar a SQL Server.")
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
    print("  1. ACTUALIZANDO TABLA 'cuentas_contables' (RF96)")
    print("="*70)

    # 1. Agregar columnas a cuentas_contables
    ejecutar(cursor, "Columna: flujo_categoria en cuentas_contables", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='cuentas_contables' AND COLUMN_NAME='flujo_categoria')
    BEGIN
        ALTER TABLE cuentas_contables ADD flujo_categoria VARCHAR(30) NULL;
    END
    """)

    ejecutar(cursor, "Columna: es_efectivo_equivalente en cuentas_contables", """
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='cuentas_contables' AND COLUMN_NAME='es_efectivo_equivalente')
    BEGIN
        ALTER TABLE cuentas_contables ADD es_efectivo_equivalente BIT DEFAULT 0;
    END
    """)

    # 2. Asignar etiquetas a las cuentas del catálogo existente
    print("\n" + "="*70)
    print("  2. ETIQUETANDO CATÁLOGO DE CUENTAS (RF96)")
    print("="*70)

    # Efectivo y equivalentes (Caja y Bancos)
    ejecutar(cursor, "Etiquetar: Efectivo y Equivalentes", """
    UPDATE cuentas_contables 
    SET flujo_categoria = 'Efectivo_Equivalente', es_efectivo_equivalente = 1
    WHERE codigo IN ('1.1.01', '1.1.02');
    """)

    # Actividades de Inversión (Activos no corrientes / fijos)
    ejecutar(cursor, "Etiquetar: Actividades de Inversión", """
    UPDATE cuentas_contables 
    SET flujo_categoria = 'Inversion', es_efectivo_equivalente = 0
    WHERE codigo IN ('1.2.01', '1.2.02', '1.2.03');
    """)

    # Actividades de Financiamiento (Capital, utilidades, documentos por pagar a LP)
    ejecutar(cursor, "Etiquetar: Actividades de Financiamiento", """
    UPDATE cuentas_contables 
    SET flujo_categoria = 'Financiamiento', es_efectivo_equivalente = 0
    WHERE codigo IN ('2.1.02', '3.1.01', '3.1.02');
    """)

    # Actividades de Operación (Clientes, inventario, impuestos, proveedores, ventas, costos y gastos)
    ejecutar(cursor, "Etiquetar: Actividades de Operación", """
    UPDATE cuentas_contables 
    SET flujo_categoria = 'Operacion', es_efectivo_equivalente = 0
    WHERE flujo_categoria IS NULL;
    """)

    # =========================================================================
    # 3. CREANDO TABLAS NUEVAS DEL MÓDULO DE FLUJO DE EFECTIVO
    # =========================================================================
    print("\n" + "="*70)
    print("  3. CREANDO TABLAS DEL ESTADO DE FLUJO DE EFECTIVO")
    print("="*70)

    # A. conciliaciones_bancarias (RF98)
    ejecutar(cursor, "Tabla: conciliaciones_bancarias", """
    IF OBJECT_ID('conciliaciones_bancarias', 'U') IS NULL
    BEGIN
        CREATE TABLE conciliaciones_bancarias (
            id INT IDENTITY(1,1) PRIMARY KEY,
            cuenta_id INT NOT NULL,
            anio INT NOT NULL,
            mes INT NOT NULL,
            fecha_corte DATE NOT NULL,
            saldo_segun_libros DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            saldo_segun_banco DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            diferencia DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            estado VARCHAR(30) DEFAULT 'Borrador', -- 'Borrador', 'Conciliada', 'Aprobada'
            observaciones NVARCHAR(MAX) NULL,
            usuario_id INT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_conciliacion_cuenta FOREIGN KEY (cuenta_id) REFERENCES cuentas_contables(id),
            CONSTRAINT fk_conciliacion_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    END
    """)

    # B. conciliacion_partidas_pendientes (RF98)
    ejecutar(cursor, "Tabla: conciliacion_partidas_pendientes", """
    IF OBJECT_ID('conciliacion_partidas_pendientes', 'U') IS NULL
    BEGIN
        CREATE TABLE conciliacion_partidas_pendientes (
            id INT IDENTITY(1,1) PRIMARY KEY,
            conciliacion_id INT NOT NULL,
            tipo_partida VARCHAR(50) NOT NULL, -- 'Cheque en Transito', 'Deposito en Transito', 'Nota de Debito', 'Nota de Credito', 'Error en Libros'
            fecha DATE NOT NULL,
            numero_documento_referencia VARCHAR(100) NOT NULL,
            descripcion VARCHAR(255) NOT NULL,
            monto DECIMAL(18,2) NOT NULL,
            efecto_en_saldo VARCHAR(20) NOT NULL, -- 'Suma', 'Resta'
            esta_conciliada BIT DEFAULT 0,
            movimiento_contable_id INT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_partida_conciliacion FOREIGN KEY (conciliacion_id) REFERENCES conciliaciones_bancarias(id) ON DELETE CASCADE,
            CONSTRAINT fk_partida_movimiento FOREIGN KEY (movimiento_contable_id) REFERENCES movimientos_contables(id)
        );
    END
    """)

    # C. estados_flujo_efectivo (RF101, RF102)
    ejecutar(cursor, "Tabla: estados_flujo_efectivo", """
    IF OBJECT_ID('estados_flujo_efectivo', 'U') IS NULL
    BEGIN
        CREATE TABLE estados_flujo_efectivo (
            id INT IDENTITY(1,1) PRIMARY KEY,
            ejercicio_fiscal INT NOT NULL,
            periodo_tipo VARCHAR(20) NOT NULL DEFAULT 'Anual', -- 'Mensual', 'Trimestral', 'Anual'
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NOT NULL,
            metodo VARCHAR(20) NOT NULL DEFAULT 'Indirecto', -- 'Directo', 'Indirecto'
            saldo_inicial_efectivo DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            flujo_neto_operacion DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            flujo_neto_inversion DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            flujo_neto_financiamiento DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            variacion_neta_efectivo DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            saldo_final_calculado DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            saldo_final_balance_general DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            diferencia_cuadratura DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            esta_cuadrado BIT NOT NULL DEFAULT 0,
            estado VARCHAR(30) DEFAULT 'Borrador', -- 'Borrador', 'Aprobado', 'Auditado'
            observaciones NVARCHAR(MAX) NULL,
            usuario_elaboro_id INT NULL,
            usuario_aprobo_id INT NULL,
            fecha_aprobacion DATETIME NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_flujo_usuario_elaboro FOREIGN KEY (usuario_elaboro_id) REFERENCES usuarios(id),
            CONSTRAINT fk_flujo_usuario_aprobo FOREIGN KEY (usuario_aprobo_id) REFERENCES usuarios(id)
        );
    END
    """)

    # D. estado_flujo_efectivo_detalle (RF101)
    ejecutar(cursor, "Tabla: estado_flujo_efectivo_detalle", """
    IF OBJECT_ID('estado_flujo_efectivo_detalle', 'U') IS NULL
    BEGIN
        CREATE TABLE estado_flujo_efectivo_detalle (
            id INT IDENTITY(1,1) PRIMARY KEY,
            flujo_id INT NOT NULL,
            actividad VARCHAR(30) NOT NULL, -- 'Operacion', 'Inversion', 'Financiamiento'
            concepto VARCHAR(255) NOT NULL,
            tipo_movimiento VARCHAR(20) NOT NULL, -- 'Entrada', 'Salida', 'Ajuste'
            importe DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            orden_presentacion INT NOT NULL DEFAULT 1,
            CONSTRAINT fk_detalle_flujo FOREIGN KEY (flujo_id) REFERENCES estados_flujo_efectivo(id) ON DELETE CASCADE
        );
    END
    """)

    # E. flujo_ajustes_no_monetarios (RF100)
    ejecutar(cursor, "Tabla: flujo_ajustes_no_monetarios", """
    IF OBJECT_ID('flujo_ajustes_no_monetarios', 'U') IS NULL
    BEGIN
        CREATE TABLE flujo_ajustes_no_monetarios (
            id INT IDENTITY(1,1) PRIMARY KEY,
            flujo_id INT NOT NULL,
            concepto VARCHAR(255) NOT NULL,
            cuenta_id INT NULL,
            efecto VARCHAR(20) NOT NULL, -- 'Suma_a_Utilidad', 'Resta_a_Utilidad'
            importe DECIMAL(18,2) NOT NULL DEFAULT 0.00,
            justificacion NVARCHAR(MAX) NOT NULL,
            usuario_id INT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_ajustes_no_monetarios_flujo FOREIGN KEY (flujo_id) REFERENCES estados_flujo_efectivo(id) ON DELETE CASCADE,
            CONSTRAINT fk_ajustes_no_monetarios_cuenta FOREIGN KEY (cuenta_id) REFERENCES cuentas_contables(id),
            CONSTRAINT fk_ajustes_no_monetarios_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    END
    """)

    # F. flujo_reclasificaciones_auditoria (RF97, RF99)
    ejecutar(cursor, "Tabla: flujo_reclasificaciones_auditoria", """
    IF OBJECT_ID('flujo_reclasificaciones_auditoria', 'U') IS NULL
    BEGIN
        CREATE TABLE flujo_reclasificaciones_auditoria (
            id INT IDENTITY(1,1) PRIMARY KEY,
            asiento_id INT NULL,
            movimiento_id INT NULL,
            origen_modulo VARCHAR(50) NOT NULL, -- 'COMPRA', 'VENTA', 'ASIENTO_MANUAL', 'ACTIVO_FIJO'
            actividad_anterior VARCHAR(30) NULL,
            actividad_nueva VARCHAR(30) NOT NULL,
            motivo_reclasificacion NVARCHAR(MAX) NOT NULL,
            usuario_id INT NOT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_reclasif_asiento FOREIGN KEY (asiento_id) REFERENCES asientos_contables(id),
            CONSTRAINT fk_reclasif_movimiento FOREIGN KEY (movimiento_id) REFERENCES movimientos_contables(id),
            CONSTRAINT fk_reclasif_usuario FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
        );
    END
    """)

    conn.close()
    print("\n" + "="*70)
    print("  MIGRACIÓN DEL MÓDULO DE FLUJO DE EFECTIVO COMPLETADA")
    print("="*70)

if __name__ == '__main__':
    run_migration()
