import sys
sys.path.append(r'c:\Users\arana\Downloads\Jehova_Jireh_Moto_Repuestos')
from app import get_db_connection

conn = get_db_connection()
conn.autocommit = True
c = conn.cursor()

# 1. solicitudes_empleo
c.execute("SELECT COUNT(*) FROM solicitudes_empleo")
if c.fetchone()[0] == 0:
    c.execute("""
    INSERT INTO solicitudes_empleo 
    (codigo_solicitud, nombres_apellidos, identificacion, direccion, telefono, email, puesto_solicitado, formacion_academica, experiencia_laboral, referencias_laborales, disponibilidad, salario_pretendido, estado, observaciones)
    VALUES
    ('SOL-2026-001', 'Carlos Manuel Rivas Pérez', '401-140598-0004L', 'Bo. San Jerónimo, Masatepe', '+505 8899-1122', 'carlos.rivas@gmail.com', 'Vendedor de Mostrador', 'Bachiller / Técnico en Computación', '2 años vendedor de repuestos en Masatepe', 'Lic. Juan Díaz (Tel: 8877-6655)', 'Inmediata', 9500.00, 'En revisión', 'Excelente conocimiento en repuestos de motocicletas y trato amable.'),
    ('SOL-2026-002', 'Marcos Josué Vega Blandón', '401-201099-0011W', 'Reparto San José, Masatepe', '+505 8765-4321', 'marcos.vega@gmail.com', 'Encargado de Bodega e Inventario', 'Técnico Medio en Logística', '1 año en distribuidora de lubricantes y baterías', 'Ing. Mario Silva (Tel: 8900-1122)', 'Inmediata', 10500.00, 'Entrevista', 'Experiencia en orden de estanterías y recepción de mercadería.')
    """)
    print("Seed: solicitudes_empleo")

# 2. contratos_laborales
c.execute("SELECT COUNT(*) FROM contratos_laborales")
if c.fetchone()[0] == 0:
    c.execute("""
    INSERT INTO contratos_laborales
    (numero_contrato, empleado_id, tipo_contratacion, lugar_trabajo, cargo, jornada_laboral, salario_mensual, forma_pago, fecha_inicio, estado, observaciones)
    VALUES
    ('CTR-2022-001', 1, 'Tiempo Indeterminado', 'Masatepe, Masaya - Tienda Central', 'Administrador General', 'Diurna Ordinaria (48h)', 25000.00, 'Quincenal', '2022-01-15', 'Vigente', 'Contrato formal de gerencia general'),
    ('CTR-2023-002', 2, 'Tiempo Indeterminado', 'Masatepe, Masaya - Tienda Central', 'Vendedor de Mostrador', 'Diurna Ordinaria (48h)', 9500.00, 'Quincenal', '2023-03-01', 'Vigente', 'Ventas de mostrador y cobro en caja POS'),
    ('CTR-2022-003', 3, 'Tiempo Indeterminado', 'Masatepe, Masaya - Tienda Central', 'Encargado de Bodega e Inventario', 'Diurna Ordinaria (48h)', 11000.00, 'Quincenal', '2022-08-10', 'Vigente', 'Recepción de mercadería y control de Kardex')
    """)
    print("Seed: contratos_laborales")

# 3. expediente_empleado
c.execute("SELECT COUNT(*) FROM expediente_empleado")
if c.fetchone()[0] == 0:
    c.execute("""
    INSERT INTO expediente_empleado
    (empleado_id, tipo_documento, nombre_archivo, usuario_responsable, observaciones)
    VALUES
    (1, 'Cédula de Identidad', 'cedula_gilda_perez.pdf', 'admin', 'Copia ampliada escaneada'),
    (1, 'Afiliación INSS', 'inss_afiliacion_gilda.pdf', 'admin', 'Constancia oficial del INSS'),
    (2, 'Cédula de Identidad', 'cedula_ana_gomez.pdf', 'admin', 'Copia legalizada vigente'),
    (2, 'Contrato Firmado', 'contrato_firmado_ana_gomez.pdf', 'admin', 'Firmado por ambas partes'),
    (3, 'Récord de Policía', 'record_roberto_silva.pdf', 'admin', 'Emitido por Policía Nacional Masaya')
    """)
    print("Seed: expediente_empleado")

# 4. higiene_epp
c.execute("SELECT COUNT(*) FROM higiene_epp")
if c.fetchone()[0] == 0:
    c.execute("""
    INSERT INTO higiene_epp
    (empleado_id, tipo_equipo, fecha_entrega, cantidad, estado_equipo, fecha_reposicion_sugerida, entregado_por, observaciones)
    VALUES
    (3, 'Faja lumbar para estiba y carga', '2026-01-10', 1, 'Bueno', '2026-07-10', 'Administración', 'Para uso continuo en estanterías de bodega'),
    (3, 'Guantes de nitrilo antideslizantes', '2026-02-01', 2, 'Bueno', '2026-05-01', 'Administración', 'Manipulación de botes de lubricantes y cadenas'),
    (3, 'Botas con puntera reforzada', '2026-01-10', 1, 'Bueno', '2027-01-10', 'Administración', 'Protección contra caída de repuestos pesados')
    """)
    print("Seed: higiene_epp")

# 5. higiene_capacitaciones
c.execute("SELECT COUNT(*) FROM higiene_capacitaciones")
if c.fetchone()[0] == 0:
    c.execute("""
    INSERT INTO higiene_capacitaciones
    (nombre_capacitacion, fecha, duracion_horas, facilitador, temas_tratados, asistentes_conteo, observaciones)
    VALUES
    ('Prevención de Lesiones en Manipulación de Carga y Ergonomía', '2026-02-15', 2.0, 'Técnico MITRAB Masaya', 'Higiene postural, límite seguro de carga (25 kg), técnicas de estiba y orden en bodega comercial.', 3, 'Participaron bodega, ventas y administración.'),
    ('Uso Práctico de Extintores PQS y Plan de Evacuación Comercial', '2026-05-20', 2.5, 'Cuerpo de Bomberos Masatepe', 'Clases de fuego (A, B, C), manejo de extintor de polvo químico seco y despeje de pasillos.', 5, 'Todo el personal de la tienda.')
    """)
    print("Seed: higiene_capacitaciones")

# 6. higiene_inspecciones
c.execute("SELECT COUNT(*) FROM higiene_inspecciones")
if c.fetchone()[0] == 0:
    c.execute("""
    INSERT INTO higiene_inspecciones
    (fecha_inspeccion, inspector, pasillos_despejados, estanterias_seguras, repuestos_ordenados, extintores_adecuados, salidas_emergencia_libres, area_caja_segura, puntos_aprobados, total_puntos, porcentaje_cumplimiento, observaciones, acciones_correctivas, estado)
    VALUES
    ('2026-10-01', 'Gilda Pérez', 1, 1, 1, 1, 1, 1, 6, 6, 100.0, 'Inspección periódica mensual conforme a Ley 618. Pasillos y extintores en orden.', 'Mantener señalización limpia', 'Aprobada')
    """)
    print("Seed: higiene_inspecciones")

conn.close()
print("Seed de datos Corte V completado!")
