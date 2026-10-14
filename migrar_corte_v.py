import pyodbc

def run_migration():
    from app import get_db_connection
    conn = get_db_connection()
    conn.autocommit = True
    cursor = conn.cursor()
    print("Iniciando migración completa para Corte V (Estadística y Recursos Humanos)...")

    def exec_sql(sql):
        try:
            cursor.execute(sql)
        except Exception as e:
            print("Error en SQL:", e)
            print("Query:", sql[:200])
            raise e

    # 1. JORNADAS LABORALES (RF102)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='jornadas_laborales')
    BEGIN
        CREATE TABLE jornadas_laborales (
            id INT IDENTITY(1,1) PRIMARY KEY,
            nombre VARCHAR(100) NOT NULL,
            hora_entrada VARCHAR(10) NOT NULL,
            hora_salida VARCHAR(10) NOT NULL,
            minutos_descanso INT DEFAULT 60,
            dias_laborables VARCHAR(100) DEFAULT 'Lunes a Sábado',
            dia_descanso VARCHAR(50) DEFAULT 'Domingo',
            horas_semanales DECIMAL(5,2) DEFAULT 48.0,
            activo BIT DEFAULT 1,
            created_at DATETIME DEFAULT GETDATE()
        );
    END
    """)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM jornadas_laborales)
    BEGIN
        INSERT INTO jornadas_laborales (nombre, hora_entrada, hora_salida, minutos_descanso, dias_laborables, dia_descanso, horas_semanales)
        VALUES 
        ('Diurna Comercial Mostrador (8h)', '08:00', '17:00', 60, 'Lunes a Sábado', 'Domingo', 48.0),
        ('Bodega y Almacén (8h)', '07:30', '16:30', 60, 'Lunes a Sábado', 'Domingo', 48.0),
        ('Administración y Finanzas', '08:00', '17:00', 60, 'Lunes a Viernes', 'Sábado y Domingo', 40.0);
    END
    """)
    print("1. jornadas_laborales OK")

    # 2. ACTUALIZACIÓN DE CARGOS (RF63 / RF74)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='cargos' AND COLUMN_NAME='area')
    BEGIN
        ALTER TABLE cargos ADD area VARCHAR(50) DEFAULT 'Administración';
        ALTER TABLE cargos ADD responsabilidades VARCHAR(MAX) NULL;
    END
    """)
    exec_sql("""
    UPDATE cargos SET area = 'Administración' WHERE area IS NULL OR area = '';
    UPDATE cargos SET area = 'Ventas' WHERE nombre_cargo LIKE '%Venta%' OR nombre_cargo LIKE '%Mostrador%';
    UPDATE cargos SET area = 'Almacén' WHERE nombre_cargo LIKE '%Bodega%' OR nombre_cargo LIKE '%Inventario%';
    UPDATE cargos SET area = 'Compras' WHERE nombre_cargo LIKE '%Compra%' OR nombre_cargo LIKE '%Proveedor%';
    UPDATE cargos SET area = 'Caja' WHERE nombre_cargo LIKE '%Caja%' OR nombre_cargo LIKE '%Cobro%';
    """)
    print("2. cargos OK")

    # 3. ACTUALIZACIÓN DE EMPLEADOS (RF58 / RF69, RF61 / RF72, RF100)
    campos_empleados = [
        ("fecha_nacimiento", "DATE NULL"),
        ("direccion", "VARCHAR(255) NULL"),
        ("contacto_emergencia", "VARCHAR(150) NULL"),
        ("jornada_id", "INT NULL"),
        ("inss_regimen", "VARCHAR(50) DEFAULT 'Integral'"),
        ("inss_fecha_alta", "DATE NULL"),
        ("inss_estado", "VARCHAR(30) DEFAULT 'Afiliado'"),
        ("fecha_baja", "DATE NULL"),
        ("motivo_baja", "VARCHAR(255) NULL")
    ]
    for campo, tipo in campos_empleados:
        exec_sql(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='empleados' AND COLUMN_NAME='{campo}')
            ALTER TABLE empleados ADD {campo} {tipo};
        """)
    print("3. empleados OK")

    # 4. ACTUALIZACIÓN DE MOVIMIENTOS LABORALES (RF105, RF106)
    campos_mov = [
        ("estado", "VARCHAR(20) DEFAULT 'Aprobada'"),
        ("aprobado_por", "VARCHAR(100) NULL"),
        ("documento_respaldo", "VARCHAR(255) NULL"),
        ("clasificacion", "VARCHAR(50) DEFAULT 'Ordinaria'")
    ]
    for campo, tipo in campos_mov:
        exec_sql(f"""
        IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='movimientos_laborales' AND COLUMN_NAME='{campo}')
            ALTER TABLE movimientos_laborales ADD {campo} {tipo};
        """)
    print("4. movimientos_laborales OK")

    # 5. SOLICITUDES DE EMPLEO (RF95, RF96)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='solicitudes_empleo')
    BEGIN
        CREATE TABLE solicitudes_empleo (
            id INT IDENTITY(1,1) PRIMARY KEY,
            codigo VARCHAR(30) NOT NULL UNIQUE,
            nombre_completo VARCHAR(150) NOT NULL,
            identificacion VARCHAR(30) NOT NULL,
            telefono VARCHAR(30) NOT NULL,
            email VARCHAR(100) NULL,
            direccion VARCHAR(255) NULL,
            puesto_solicitado VARCHAR(100) NOT NULL,
            area VARCHAR(50) DEFAULT 'Ventas',
            formacion_academica VARCHAR(255) NULL,
            experiencia_laboral VARCHAR(MAX) NULL,
            referencias_laborales VARCHAR(MAX) NULL,
            disponibilidad VARCHAR(50) DEFAULT 'Inmediata',
            salario_pretendido DECIMAL(12,2) DEFAULT 0.00,
            archivo_cv VARCHAR(255) NULL,
            estado VARCHAR(30) DEFAULT 'Recibida',
            observaciones VARCHAR(MAX) NULL,
            created_at DATETIME DEFAULT GETDATE()
        );
    END
    """)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM solicitudes_empleo)
    BEGIN
        INSERT INTO solicitudes_empleo (codigo, nombre_completo, identificacion, telefono, email, puesto_solicitado, area, formacion_academica, experiencia_laboral, referencias_laborales, disponibilidad, salario_pretendido, estado, observaciones)
        VALUES
        ('SOL-2026-001', 'Carlos Manuel Rivas Pérez', '401-140598-0004L', '+505 8899-1122', 'carlos.rivas@gmail.com', 'Asesor de Ventas de Mostrador', 'Ventas', 'Bachiller / Técnico en Computación', '2 años vendedor de repuestos en Masatepe', 'Lic. Juan Díaz (Tel: 8877-6655)', 'Inmediata', 9500.00, 'En revisión', 'Excelente presentación y conocimiento de repuestos de motos chinas.'),
        ('SOL-2026-002', 'Marcos Josué Vega Blandón', '401-201099-0011W', '+505 8765-4321', 'marcos.vega@gmail.com', 'Auxiliar de Bodega e Inventario', 'Almacén', 'Técnico Medio en Logística', '1 año en distribuidora de baterías y lubricantes', 'Ing. Mario Silva (Tel: 8900-1122)', 'Inmediata', 10500.00, 'Entrevista', 'Disponibilidad para turnos de recepción de mercadería.');
    END
    """)
    print("5. solicitudes_empleo OK")

    # 6. EXPEDIENTES DE EMPLEADOS (RF97)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='expedientes_empleados')
    BEGIN
        CREATE TABLE expedientes_empleados (
            id INT IDENTITY(1,1) PRIMARY KEY,
            empleado_id INT NOT NULL,
            tipo_documento VARCHAR(100) NOT NULL,
            nombre_archivo VARCHAR(255) NOT NULL,
            url_archivo VARCHAR(255) NULL,
            fecha_registro DATETIME DEFAULT GETDATE(),
            usuario_responsable VARCHAR(100) NULL,
            observaciones VARCHAR(255) NULL,
            CONSTRAINT fk_expediente_emp FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE
        );
    END
    """)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM expedientes_empleados)
    BEGIN
        INSERT INTO expedientes_empleados (empleado_id, tipo_documento, nombre_archivo, usuario_responsable, observaciones)
        VALUES
        (1, 'Cédula de Identidad', 'cedula_gilda_perez.pdf', 'admin', 'Copia ampliada escaneada'),
        (1, 'Afiliación INSS', 'inss_afiliacion_gilda.pdf', 'admin', 'Constancia oficial INSS'),
        (2, 'Cédula de Identidad', 'cedula_ana_gomez.pdf', 'admin', 'Copia vigente'),
        (3, 'Récord de Policía', 'record_roberto_silva.pdf', 'admin', 'Emitido en Masaya 2026');
    END
    """)
    print("6. expedientes_empleados OK")

    # 7. CONTRATOS LABORALES (RF98, RF99)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='contratos_laborales')
    BEGIN
        CREATE TABLE contratos_laborales (
            id INT IDENTITY(1,1) PRIMARY KEY,
            numero_contrato VARCHAR(50) NOT NULL UNIQUE,
            empleado_id INT NOT NULL,
            tipo_contratacion VARCHAR(50) DEFAULT 'Tiempo Indeterminado',
            cargo VARCHAR(100) NOT NULL,
            funciones VARCHAR(MAX) NULL,
            lugar_trabajo VARCHAR(150) DEFAULT 'Masatepe, Masaya - Tienda Central',
            fecha_inicio DATE NOT NULL,
            fecha_fin DATE NULL,
            jornada_laboral VARCHAR(100) DEFAULT 'Diurna Ordinaria (48 horas semanales)',
            salario_mensual DECIMAL(12,2) NOT NULL,
            periodicidad_pago VARCHAR(50) DEFAULT 'Quincenal',
            estado VARCHAR(30) DEFAULT 'Vigente',
            archivo_firmado VARCHAR(255) NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_contratos_emp FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE
        );
    END
    """)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM contratos_laborales)
    BEGIN
        INSERT INTO contratos_laborales (numero_contrato, empleado_id, tipo_contratacion, cargo, funciones, fecha_inicio, salario_mensual, estado)
        VALUES
        ('CTR-2022-001', 1, 'Tiempo Indeterminado', 'Administrador General', 'Gerencia general y control administrativo integral de la tienda.', '2022-01-15', 25000.00, 'Vigente'),
        ('CTR-2023-002', 2, 'Tiempo Indeterminado', 'Vendedor de Mostrador', 'Atención directa a clientes de mostrador, cobro en caja POS y asesoramiento de repuestos.', '2023-03-01', 9500.00, 'Vigente'),
        ('CTR-2022-003', 3, 'Tiempo Indeterminado', 'Encargado de Bodega e Inventario', 'Recepción de mercadería, control de Kardex, almacenamiento y despacho.', '2022-08-10', 11000.00, 'Vigente');
    END
    """)
    print("7. contratos_laborales OK")

    # 8. HISTORIAL LABORAL (RF101)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='historial_laboral')
    BEGIN
        CREATE TABLE historial_laboral (
            id INT IDENTITY(1,1) PRIMARY KEY,
            empleado_id INT NOT NULL,
            tipo_modificacion VARCHAR(50) NOT NULL,
            valor_anterior VARCHAR(150) NOT NULL,
            valor_nuevo VARCHAR(150) NOT NULL,
            fecha_vigencia DATE NOT NULL,
            motivo VARCHAR(255) NOT NULL,
            usuario_responsable VARCHAR(100) NOT NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_historial_emp FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE
        );
    END
    """)
    print("8. historial_laboral OK")

    # 9. ASISTENCIA LABORAL (RF103)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='asistencia_laboral')
    BEGIN
        CREATE TABLE asistencia_laboral (
            id INT IDENTITY(1,1) PRIMARY KEY,
            empleado_id INT NOT NULL,
            fecha DATE NOT NULL,
            hora_entrada VARCHAR(10) NULL,
            hora_salida VARCHAR(10) NULL,
            estado VARCHAR(30) DEFAULT 'Completa',
            minutos_tardanza INT DEFAULT 0,
            observaciones VARCHAR(255) NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_asistencia_emp FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE
        );
    END
    """)
    print("9. asistencia_laboral OK")

    # 10. HORAS EXTRAS (RF104)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='horas_extras')
    BEGIN
        CREATE TABLE horas_extras (
            id INT IDENTITY(1,1) PRIMARY KEY,
            empleado_id INT NOT NULL,
            fecha DATE NOT NULL,
            cantidad_horas DECIMAL(5,2) NOT NULL,
            motivo VARCHAR(255) NOT NULL,
            valor_por_hora DECIMAL(12,2) NOT NULL,
            monto_total DECIMAL(12,2) NOT NULL,
            estado VARCHAR(30) DEFAULT 'Aprobada',
            responsable_aprobacion VARCHAR(100) NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_horas_extras_emp FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE
        );
    END
    """)
    print("10. horas_extras OK")

    # 11. LIQUIDACIONES LABORALES (RF108)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='liquidaciones_laborales')
    BEGIN
        CREATE TABLE liquidaciones_laborales (
            id INT IDENTITY(1,1) PRIMARY KEY,
            codigo VARCHAR(50) NOT NULL UNIQUE,
            empleado_id INT NOT NULL,
            fecha_ingreso DATE NOT NULL,
            fecha_egreso DATE NOT NULL,
            motivo_salida VARCHAR(100) NOT NULL,
            salario_base DECIMAL(12,2) NOT NULL,
            salario_promedio_6m DECIMAL(12,2) NOT NULL,
            anios_servicio DECIMAL(5,2) NOT NULL,
            dias_pendientes_pago INT DEFAULT 0,
            monto_dias_pendientes DECIMAL(12,2) DEFAULT 0.00,
            dias_vacaciones_pendientes DECIMAL(5,2) DEFAULT 0.00,
            monto_vacaciones DECIMAL(12,2) DEFAULT 0.00,
            monto_aguinaldo_proporcional DECIMAL(12,2) DEFAULT 0.00,
            monto_indemnizacion_antiguedad DECIMAL(12,2) DEFAULT 0.00,
            total_percepciones DECIMAL(12,2) NOT NULL,
            deduccion_inss_salario DECIMAL(12,2) DEFAULT 0.00,
            deduccion_ir DECIMAL(12,2) DEFAULT 0.00,
            otras_deducciones DECIMAL(12,2) DEFAULT 0.00,
            neto_a_pagar DECIMAL(12,2) NOT NULL,
            estado VARCHAR(30) DEFAULT 'Borrador',
            observaciones VARCHAR(MAX) NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_liquidaciones_emp FOREIGN KEY (empleado_id) REFERENCES empleados(id)
        );
    END
    """)
    print("11. liquidaciones_laborales OK")

    # 12. PAGOS DE NÓMINA (RF109)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='pagos_nomina')
    BEGIN
        CREATE TABLE pagos_nomina (
            id INT IDENTITY(1,1) PRIMARY KEY,
            nomina_id INT NOT NULL,
            empleado_id INT NOT NULL,
            monto_pagado DECIMAL(12,2) NOT NULL,
            fecha_pago DATE NOT NULL,
            metodo_pago VARCHAR(50) DEFAULT 'Efectivo',
            numero_referencia VARCHAR(100) NULL,
            estado VARCHAR(30) DEFAULT 'Confirmado',
            usuario_responsable VARCHAR(100) NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_pagosnom_nom FOREIGN KEY (nomina_id) REFERENCES nomina(id) ON DELETE CASCADE,
            CONSTRAINT fk_pagosnom_emp FOREIGN KEY (empleado_id) REFERENCES empleados(id)
        );
    END
    """)
    print("12. pagos_nomina OK")

    # 13. HIGIENE Y SEGURIDAD: RIESGOS (RF110)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='higiene_riesgos')
    BEGIN
        CREATE TABLE higiene_riesgos (
            id INT IDENTITY(1,1) PRIMARY KEY,
            area VARCHAR(50) NOT NULL,
            tipo_riesgo VARCHAR(100) NOT NULL,
            descripcion VARCHAR(MAX) NOT NULL,
            nivel_riesgo VARCHAR(20) DEFAULT 'Medio',
            medidas_preventivas VARCHAR(MAX) NOT NULL,
            responsable_seguimiento VARCHAR(100) NOT NULL,
            estado VARCHAR(30) DEFAULT 'Identificado y Controlado',
            created_at DATETIME DEFAULT GETDATE()
        );
    END
    """)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM higiene_riesgos)
    BEGIN
        INSERT INTO higiene_riesgos (area, tipo_riesgo, descripcion, nivel_riesgo, medidas_preventivas, responsable_seguimiento)
        VALUES
        ('Almacén y Bodega de Repuestos', 'Manipulación de Carga Pesada', 'Levantamiento manual de cajas con cadenas, llantas, aceites y kits de arrastre.', 'Medio', 'Uso obligatorio de faja lumbar, técnica de flexión de rodillas y ayuda entre compañeros para cargas superiores a 25 kg.', 'Roberto Silva'),
        ('Almacén y Bodega de Repuestos', 'Caída de Repuestos en Estanterías', 'Almacenamiento de repuestos y cascos en niveles superiores de estanterías metálicas.', 'Medio', 'Uso de escalera de tijera con tope de seguridad; repuestos más pesados colocados en niveles inferiores.', 'Roberto Silva'),
        ('Ventas y Mostrador', 'Caídas y Tropiezos en Pasillos', 'Obstáculos temporales por cajas de mercadería recién ingresada en el área de exhibición.', 'Bajo', 'Despeje inmediato de pasillos comerciales hacia bodega; delimitación de zonas de tránsito.', 'Ana Gómez'),
        ('Caja y Cobro', 'Ergonómico / Postura Prolongada', 'Permanencia de pie o sentado continuo en caja POS sin apoyo lumbar.', 'Bajo', 'Silla ergonómica con respaldo ajustable y pausas activas programadas.', 'Ana Gómez'),
        ('Tienda y Establecimiento', 'Riesgo de Incendio', 'Presencia de material combustible como empaques de cartón y lubricantes almacenados.', 'Medio', 'Extintor PQS de 10 libras vigente con acceso 100% despejado y señalizado; prohibido fumar.', 'Gilda Pérez');
    END
    """)
    print("13. higiene_riesgos OK")

    # 14. HIGIENE Y SEGURIDAD: ACCIDENTES E INCIDENTES (RF111)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='higiene_accidentes')
    BEGIN
        CREATE TABLE higiene_accidentes (
            id INT IDENTITY(1,1) PRIMARY KEY,
            codigo VARCHAR(50) NOT NULL UNIQUE,
            fecha DATETIME NOT NULL,
            area VARCHAR(50) NOT NULL,
            empleado_id INT NULL,
            tipo_evento VARCHAR(50) DEFAULT 'Incidente',
            descripcion VARCHAR(MAX) NOT NULL,
            posibles_causas VARCHAR(MAX) NOT NULL,
            medidas_correctivas VARCHAR(MAX) NOT NULL,
            dias_incapacidad INT DEFAULT 0,
            estado VARCHAR(30) DEFAULT 'En Seguimiento',
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_higiene_acc_emp FOREIGN KEY (empleado_id) REFERENCES empleados(id)
        );
    END
    """)
    print("14. higiene_accidentes OK")

    # 15. HIGIENE Y SEGURIDAD: CONTROL DE EPP (RF112)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='higiene_epp')
    BEGIN
        CREATE TABLE higiene_epp (
            id INT IDENTITY(1,1) PRIMARY KEY,
            empleado_id INT NOT NULL,
            tipo_equipo VARCHAR(100) NOT NULL,
            fecha_entrega DATE NOT NULL,
            cantidad INT DEFAULT 1,
            estado_equipo VARCHAR(30) DEFAULT 'Nuevo',
            fecha_reposicion_programada DATE NULL,
            entregado_por VARCHAR(100) NOT NULL,
            observaciones VARCHAR(255) NULL,
            created_at DATETIME DEFAULT GETDATE(),
            CONSTRAINT fk_higiene_epp_emp FOREIGN KEY (empleado_id) REFERENCES empleados(id) ON DELETE CASCADE
        );
    END
    """)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM higiene_epp)
    BEGIN
        INSERT INTO higiene_epp (empleado_id, tipo_equipo, fecha_entrega, cantidad, estado_equipo, fecha_reposicion_programada, entregado_por, observaciones)
        VALUES
        (3, 'Faja lumbar para estiba y carga', '2026-01-10', 1, 'Bueno', '2026-07-10', 'Administración', 'Para uso continuo en estanterías de bodega'),
        (3, 'Guantes de nitrilo antideslizantes', '2026-02-01', 2, 'Bueno', '2026-05-01', 'Administración', 'Manipulación de botes de lubricantes y cadenas'),
        (3, 'Botas con puntera reforzada', '2026-01-10', 1, 'Bueno', '2027-01-10', 'Administración', 'Protección contra caída de repuestos pesados');
    END
    """)
    print("15. higiene_epp OK")

    # 16. HIGIENE Y SEGURIDAD: CAPACITACIONES (RF113)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='higiene_capacitaciones')
    BEGIN
        CREATE TABLE higiene_capacitaciones (
            id INT IDENTITY(1,1) PRIMARY KEY,
            nombre VARCHAR(150) NOT NULL,
            fecha DATE NOT NULL,
            duracion_horas DECIMAL(4,2) DEFAULT 2.0,
            instructor_responsable VARCHAR(150) NOT NULL,
            temas_tratados VARCHAR(MAX) NOT NULL,
            empleados_participantes VARCHAR(MAX) NOT NULL,
            constancia_archivo VARCHAR(255) NULL,
            created_at DATETIME DEFAULT GETDATE()
        );
    END
    """)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM higiene_capacitaciones)
    BEGIN
        INSERT INTO higiene_capacitaciones (nombre, fecha, duracion_horas, instructor_responsable, temas_tratados, empleados_participantes)
        VALUES
        ('Prevención de Lesiones en Manipulación de Carga y Ergonomía', '2026-02-15', 2.0, 'Técnico MITRAB Masaya', 'Higiene postural, límite seguro de carga, técnicas de estiba y orden en bodega comercial.', 'Roberto Silva, Ana Gómez, Gilda Pérez'),
        ('Uso Práctico de Extintores PQS y Plan de Evacuación Comercial', '2026-05-20', 2.5, 'Cuerpo de Bomberos Masatepe', 'Clases de fuego (A, B, C), manejo de extintor de polvo químico, corte eléctrico y evacuación de clientes.', 'Todo el personal de Jehová Jireh');
    END
    """)
    print("16. higiene_capacitaciones OK")

    # 17. HIGIENE Y SEGURIDAD: INSPECCIONES DE 6 PUNTOS (RF114)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='higiene_inspecciones')
    BEGIN
        CREATE TABLE higiene_inspecciones (
            id INT IDENTITY(1,1) PRIMARY KEY,
            fecha DATE NOT NULL,
            inspector VARCHAR(100) NOT NULL,
            punto_1_pasillos BIT DEFAULT 1,
            punto_2_estanterias BIT DEFAULT 1,
            punto_3_cajas_ordenadas BIT DEFAULT 1,
            punto_4_extintores BIT DEFAULT 1,
            punto_5_salidas_emergencia BIT DEFAULT 1,
            punto_6_area_caja BIT DEFAULT 1,
            observaciones VARCHAR(MAX) NULL,
            medidas_correctivas VARCHAR(MAX) NULL,
            estado VARCHAR(30) DEFAULT 'Aprobada',
            created_at DATETIME DEFAULT GETDATE()
        );
    END
    """)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM higiene_inspecciones)
    BEGIN
        INSERT INTO higiene_inspecciones (fecha, inspector, punto_1_pasillos, punto_2_estanterias, punto_3_cajas_ordenadas, punto_4_extintores, punto_5_salidas_emergencia, punto_6_area_caja, observaciones, estado)
        VALUES
        ('2026-10-01', 'Gilda Pérez', 1, 1, 1, 1, 1, 1, 'Inspección mensual conforme a Ley 618. Pasillos y extintores en orden.', 'Aprobada');
    END
    """)
    print("17. higiene_inspecciones OK")

    # 18. PARÁMETROS LABORALES DEL SISTEMA (RF116)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME='parametros_laborales')
    BEGIN
        CREATE TABLE parametros_laborales (
            id INT IDENTITY(1,1) PRIMARY KEY,
            clave VARCHAR(50) NOT NULL UNIQUE,
            nombre VARCHAR(150) NOT NULL,
            valor DECIMAL(12,4) NOT NULL,
            unidad VARCHAR(20) DEFAULT '%',
            referencia_legal VARCHAR(150) NOT NULL,
            descripcion VARCHAR(255) NULL,
            fecha_vigencia DATE NOT NULL,
            usuario_modifico VARCHAR(100) NULL,
            created_at DATETIME DEFAULT GETDATE()
        );
    END
    """)
    exec_sql("""
    IF NOT EXISTS (SELECT 1 FROM parametros_laborales)
    BEGIN
        INSERT INTO parametros_laborales (clave, nombre, valor, unidad, referencia_legal, descripcion, fecha_vigencia, usuario_modifico)
        VALUES
        ('INSS_LABORAL', 'Aporte Laboral INSS', 0.0700, '%', 'Ley 539 de Seguridad Social', 'Porcentaje descontado del salario del colaborador', '2026-01-01', 'admin'),
        ('INSS_PATRONAL', 'Aporte Patronal INSS', 0.2150, '%', 'Decreto 06-2019 de Nicaragua', 'Empresas con menos de 50 trabajadores (Régimen Integral)', '2026-01-01', 'admin'),
        ('INATEC_PATRONAL', 'Aporte Patronal INATEC', 0.0200, '%', 'Ley 185 / Normativa INATEC', 'Aporte del empleador para capacitación técnica', '2026-01-01', 'admin'),
        ('VACACIONES_DIAS_MES', 'Días Vacaciones Acumulables al Mes', 2.5000, 'días/mes', 'Art. 76 Ley 185 (Código del Trabajo)', '15 días por cada 6 meses continuos de labor', '2026-01-01', 'admin'),
        ('RECARGO_HORA_EXTRA', 'Factor Recargo Horas Extras', 2.0000, 'factor (100%)', 'Art. 62 Ley 185 (Código del Trabajo)', 'Pago doble del valor de la hora ordinaria', '2026-01-01', 'admin');
    END
    """)
    print("18. parametros_laborales OK")

    conn.close()
    print("¡Migración y creación de estructuras para Corte V completada con éxito!")

if __name__ == '__main__':
    run_migration()
