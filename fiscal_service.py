"""
=============================================================================
  fiscal_service.py — Motor de Simulación y Liquidación Fiscal DGI (Nicaragua)
  Sistema Jehová Jireh Moto Repuestos
  
  Basado en:
  - Formulario 106: Declaración Anual del Impuesto Sobre la Renta (IR)
    Ventanilla Electrónica Tributaria (VET - DGI Nicaragua)
  - Ley 822: Ley de Concertación Tributaria (LCT) y sus Reglamentos
  - Catálogo Oficial de Códigos de Retención en la Fuente DGI
=============================================================================
"""

import json
from datetime import datetime, timezone, timedelta

def fecha_hoy_nicaragua():
    return datetime.now(timezone(timedelta(hours=-6))).date().isoformat()

CATALOGO_RETENCIONES_DGI = [
    {
        "codigo": "2.1",
        "descripcion": "Venta de bienes y prestaciones de servicios en que se utilice como medio de pago tarjeta de crédito/débito",
        "alicuota": 1.5,
        "base_legal": "Art. 44, 2.1 Reglamento LCT"
    },
    {
        "codigo": "2.2",
        "descripcion": "Compra de bienes y prestación de servicios en general",
        "alicuota": 2.0,
        "base_legal": "Art. 44, 2.2 Reglamento LCT"
    },
    {
        "codigo": "2.4",
        "descripcion": "Alquiler y arrendamientos de actividad económica",
        "alicuota": 2.0,
        "base_legal": "Art. 44, 2.2 Reglamento LCT"
    },
    {
        "codigo": "2.7",
        "descripcion": "Sobre servicios profesionales o técnico superior prestados por personas naturales",
        "alicuota": 10.0,
        "base_legal": "Art. 44, 2.5.a Reglamento LCT"
    },
    {
        "codigo": "ANTICIPO",
        "descripcion": "Anticipo Mensual a Cuenta del IR (1% Renta Bruta)",
        "alicuota": 1.0,
        "base_legal": "Art. 61 Ley 822 LCT"
    },
    {
        "codigo": "SALDO_FAVOR_ANT",
        "descripcion": "Crédito Tributario / Saldo a Favor de Período Anterior",
        "alicuota": 0.0,
        "base_legal": "Art. 67 Ley 822 LCT"
    }
]

def obtener_info_tributaria(cursor):
    cursor.execute("""
        SELECT TOP 1 id, ruc, razon_social, nombre_comercial, actividad_economica,
                     domicilio_fiscal, regimen_tributario, fecha_inicio_vigencia, activo
        FROM negocio_info_tributaria
        WHERE activo = 1
        ORDER BY id DESC
    """)
    row = cursor.fetchone()
    if row:
        return {
            "id": row.id,
            "ruc": row.ruc,
            "razon_social": row.razon_social,
            "nombre_comercial": row.nombre_comercial,
            "actividad_economica": row.actividad_economica,
            "domicilio_fiscal": row.domicilio_fiscal,
            "regimen_tributario": row.regimen_tributario,
            "fecha_inicio_vigencia": str(row.fecha_inicio_vigencia)
        }
    return {
        "id": 0,
        "ruc": "J0310000000001",
        "razon_social": "Jehová Jireh Moto Repuestos y Servicios",
        "nombre_comercial": "Jehová Jireh Moto Repuestos",
        "actividad_economica": "Comercio al por menor de repuestos, lubricantes y mantenimiento de motocicletas",
        "domicilio_fiscal": "Granada, Nicaragua",
        "regimen_tributario": "Régimen General",
        "fecha_inicio_vigencia": "2026-01-01"
    }

def obtener_reglas_fiscales(cursor):
    cursor.execute("""
        SELECT codigo_regla, nombre_regla, regimen_tributario, tipo_parametro,
               valor, condiciones_aplicacion, referencia_normativa
        FROM reglas_tributarias
        WHERE activo = 1
    """)
    reglas = {}
    for r in cursor.fetchall():
        reglas[r.codigo_regla] = {
            "codigo": r.codigo_regla,
            "nombre": r.nombre_regla,
            "tipo": r.tipo_parametro,
            "valor": float(r.valor),
            "condiciones": r.condiciones_aplicacion,
            "referencia": r.referencia_normativa
        }
    return reglas

def obtener_saldos_contables_ejercicio(cursor, anio):
    """
    Obtiene los saldos contables agrupados por cuenta para un año fiscal específico
    (desde el 1 de enero hasta el 31 de diciembre o la fecha actual si es el año en curso).
    """
    fecha_inicio = f"{anio}-01-01"
    hoy = fecha_hoy_nicaragua()
    fecha_fin = f"{anio}-12-31" if str(anio) < hoy[:4] else min(hoy, f"{anio}-12-31")

    # 1. Movimientos acumulados para cuentas de Balance (hasta fecha_fin)
    cursor.execute("""
        SELECT c.id, c.codigo, c.nombre, c.clasificacion, c.naturaleza,
               ISNULL(SUM(m.debe), 0) AS total_debe,
               ISNULL(SUM(m.haber), 0) AS total_haber
        FROM cuentas_contables c
        LEFT JOIN movimientos_contables m ON c.id = m.cuenta_id
        LEFT JOIN asientos_contables a ON a.id = m.asiento_id AND CAST(a.fecha AS DATE) <= ?
        GROUP BY c.id, c.codigo, c.nombre, c.clasificacion, c.naturaleza
        ORDER BY c.codigo
    """, (fecha_fin,))
    
    cuentas_balance = {}
    for r in cursor.fetchall():
        debe = float(r.total_debe)
        haber = float(r.total_haber)
        if r.naturaleza == 'Acreedora':
            saldo = haber - debe
        else:
            saldo = debe - haber

        cuentas_balance[r.codigo] = {
            "id": r.id,
            "codigo": r.codigo,
            "nombre": r.nombre,
            "clasificacion": r.clasificacion,
            "naturaleza": r.naturaleza,
            "debe": debe,
            "haber": haber,
            "saldo": saldo
        }

    # 2. Movimientos del período para cuentas de Resultados (entre fecha_inicio y fecha_fin)
    cursor.execute("""
        SELECT c.id, c.codigo, c.nombre, c.clasificacion, c.naturaleza,
               ISNULL(SUM(m.debe), 0) AS total_debe,
               ISNULL(SUM(m.haber), 0) AS total_haber
        FROM cuentas_contables c
        INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
        INNER JOIN asientos_contables a ON a.id = m.asiento_id
        WHERE CAST(a.fecha AS DATE) >= ? AND CAST(a.fecha AS DATE) <= ?
          AND c.clasificacion IN ('Ingresos', 'Costo', 'Gasto')
        GROUP BY c.id, c.codigo, c.nombre, c.clasificacion, c.naturaleza
        ORDER BY c.codigo
    """, (fecha_inicio, fecha_fin))

    cuentas_resultados = {}
    for r in cursor.fetchall():
        debe = float(r.total_debe)
        haber = float(r.total_haber)
        if r.naturaleza == 'Acreedora':
            saldo = haber - debe
        else:
            saldo = debe - haber

        cuentas_resultados[r.codigo] = {
            "id": r.id,
            "codigo": r.codigo,
            "nombre": r.nombre,
            "clasificacion": r.clasificacion,
            "naturaleza": r.naturaleza,
            "debe": debe,
            "haber": haber,
            "saldo": saldo
        }

    return {
        "anio": anio,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "balance": cuentas_balance,
        "resultados": cuentas_resultados
    }

def mapear_formulario_106(datos_contables, ajustes_fiscales=None, acreditamientos=None):
    """
    Construye con exactitud los renglones oficiales del Formulario 106 de la DGI
    con base en el catálogo de cuentas y los saldos contables.
    """
    cb = datos_contables["balance"]
    cr = datos_contables["resultados"]
    
    def sal(cod):
        return round(float(cb.get(cod, {}).get("saldo", 0.0)), 2)

    def sal_res(cod):
        return round(float(cr.get(cod, {}).get("saldo", 0.0)), 2)

    # =========================================================================
    # SECCIÓN B: BALANCE GENERAL (Renglones 1 al 23 oficiales)
    # =========================================================================
    r1_efectivo = round(sal("1.1.01") + sal("1.1.02"), 2)   # Caja + Bancos
    r2_cuentas_cobrar = sal("1.1.03")                      # Clientes
    r3_inventarios = sal("1.1.04")                         # Inventarios
    r4_terrenos = 0.00
    r5_edificios = 0.00
    r6_otros_inmobiliarios = 0.00
    r7_total_inmobiliario = round(r4_terrenos + r5_edificios + r6_otros_inmobiliarios, 2)
    
    r8_parque_vehicular = 0.00
    # Mobiliario y equipo (1.2.01) + Cómputo (1.2.02) - Depreciación acumulada (1.2.03)
    r9_otros_mobiliarios = round(sal("1.2.01") + sal("1.2.02") - abs(sal("1.2.03")), 2)
    r10_total_mobiliarios = round(r8_parque_vehicular + r9_otros_mobiliarios, 2)
    
    # Otros activos (IVA acreditable 1.1.05 u otros)
    r11_otros_activos = sal("1.1.05")
    
    # Renglón 12: Total Activos (1 + 2 + 3 + 7 + 10 + 11)
    r12_total_activos = round(r1_efectivo + r2_cuentas_cobrar + r3_inventarios + r7_total_inmobiliario + r10_total_mobiliarios + r11_otros_activos, 2)

    # Pasivos
    r13_cuentas_pagar = round(sal("2.1.01") + sal("2.1.02"), 2) # Proveedores + Doc. por pagar
    r14_dividendos_pagados_res = 0.00
    r15_dividendos_por_pagar_res = 0.00
    r16_inst_financieras_desarrollo = 0.00
    r17_resto_inst_financieras = 0.00
    r18_casa_matriz_sucursales = 0.00
    # Otros agentes no financieros (IVA por pagar 2.1.03, sueldos 2.1.04, serv 2.1.05, retenciones 2.1.06 y 2.1.07, provisiones 2.1.08)
    r19_otros_agentes_no_fin = round(
        sal("2.1.03") + sal("2.1.04") + sal("2.1.05") + sal("2.1.06") + sal("2.1.07") + sal("2.1.08") + sal("2.1.10"), 2
    )
    # Renglón 20: Pasivo Fijo Nacional (15 + 16 + 17 + 18 + 19)
    r20_pasivo_fijo_nacional = round(r15_dividendos_por_pagar_res + r16_inst_financieras_desarrollo + r17_resto_inst_financieras + r18_casa_matriz_sucursales + r19_otros_agentes_no_fin, 2)

    r21_dividendos_pagados_no_res = 0.00
    r22_dividendos_por_pagar_no_res = 0.00
    r23_inst_financieras_desarrollo_ext = 0.00
    
    total_pasivos = round(r13_cuentas_pagar + r20_pasivo_fijo_nacional + r22_dividendos_por_pagar_no_res + r23_inst_financieras_desarrollo_ext, 2)
    capital_social = sal("3.1.01")
    utilidades_acumuladas = sal("3.1.02")

    renglones_balance = [
        {"renglon": 1, "descripcion": "Efectivo en caja y bancos", "importe": r1_efectivo, "cuentas": "1.1.01, 1.1.02", "tipo": "Contable"},
        {"renglon": 2, "descripcion": "Cuentas y documentos por cobrar", "importe": r2_cuentas_cobrar, "cuentas": "1.1.03", "tipo": "Contable"},
        {"renglon": 3, "descripcion": "Inventarios", "importe": r3_inventarios, "cuentas": "1.1.04", "tipo": "Contable"},
        {"renglon": 4, "descripcion": "Terrenos", "importe": r4_terrenos, "cuentas": "", "tipo": "Manual"},
        {"renglon": 5, "descripcion": "Edificios", "importe": r5_edificios, "cuentas": "", "tipo": "Manual"},
        {"renglon": 6, "descripcion": "Otros Activos Inmobiliarios", "importe": r6_otros_inmobiliarios, "cuentas": "", "tipo": "Manual"},
        {"renglon": 7, "descripcion": "Total Activo Inmobiliario (Renglones 4+5+6)", "importe": r7_total_inmobiliario, "cuentas": "Calculado", "tipo": "Calculado"},
        {"renglon": 8, "descripcion": "Parque Vehicular", "importe": r8_parque_vehicular, "cuentas": "", "tipo": "Manual"},
        {"renglon": 9, "descripcion": "Otros Bienes Mobiliarios", "importe": r9_otros_mobiliarios, "cuentas": "1.2.01, 1.2.02, 1.2.03", "tipo": "Contable"},
        {"renglon": 10, "descripcion": "Total Activos Mobiliarios (Renglón 8+9)", "importe": r10_total_mobiliarios, "cuentas": "Calculado", "tipo": "Calculado"},
        {"renglon": 11, "descripcion": "Otros activos", "importe": r11_otros_activos, "cuentas": "1.1.05", "tipo": "Contable"},
        {"renglon": 12, "descripcion": "Total Activos (suma 1+2+3+7+10+11)", "importe": r12_total_activos, "cuentas": "Calculado", "tipo": "Calculado", "destacado": True},
        {"renglon": 13, "descripcion": "Cuentas y documentos por pagar", "importe": r13_cuentas_pagar, "cuentas": "2.1.01, 2.1.02", "tipo": "Contable"},
        {"renglon": 14, "descripcion": "Dividendos Pagados a Residentes en el País", "importe": r14_dividendos_pagados_res, "cuentas": "", "tipo": "Manual"},
        {"renglon": 15, "descripcion": "Dividendos por Pagar a Residentes en el País", "importe": r15_dividendos_por_pagar_res, "cuentas": "", "tipo": "Manual"},
        {"renglon": 16, "descripcion": "Instituciones Financieras de Desarrollo", "importe": r16_inst_financieras_desarrollo, "cuentas": "", "tipo": "Manual"},
        {"renglon": 17, "descripcion": "Resto de Instituciones Financieras", "importe": r17_resto_inst_financieras, "cuentas": "", "tipo": "Manual"},
        {"renglon": 18, "descripcion": "Casa Matriz u Otras Sucursales en el País", "importe": r18_casa_matriz_sucursales, "cuentas": "", "tipo": "Manual"},
        {"renglon": 19, "descripcion": "Otros Agentes no Financieros", "importe": r19_otros_agentes_no_fin, "cuentas": "2.1.03-2.1.08", "tipo": "Contable"},
        {"renglon": 20, "descripcion": "Pasivo Fijo Nacional (suma 15+16+17+18+19)", "importe": r20_pasivo_fijo_nacional, "cuentas": "Calculado", "tipo": "Calculado", "destacado": True},
        {"renglon": 21, "descripcion": "Dividendos Pagados a no residentes en el País", "importe": r21_dividendos_pagados_no_res, "cuentas": "", "tipo": "Manual"},
        {"renglon": 22, "descripcion": "Dividendos por pagar a no residentes en el País", "importe": r22_dividendos_por_pagar_no_res, "cuentas": "", "tipo": "Manual"},
        {"renglon": 23, "descripcion": "Instituciones Financieras de Desarrollo (Ext)", "importe": r23_inst_financieras_desarrollo_ext, "cuentas": "", "tipo": "Manual"}
    ]

    # =========================================================================
    # SECCIÓN D: ESTADO DE RESULTADOS (Ingresos, Costos, Gastos Deducibles)
    # =========================================================================
    ventas_repuestos = sal_res("4.1.01")
    servicios_taller = sal_res("4.1.02")
    total_ingresos_brutos = round(ventas_repuestos + servicios_taller, 2)
    devoluciones_descuentos = 0.00
    ingresos_netos = round(total_ingresos_brutos - devoluciones_descuentos, 2)

    costo_ventas = sal_res("5.1.01")
    utilidad_bruta = round(ingresos_netos - costo_ventas, 2)

    gastos_publicidad = sal_res("6.1.06")
    gastos_sueldos = sal_res("6.1.01")
    gastos_alquiler = sal_res("6.1.02")
    gastos_energia = sal_res("6.1.03")
    gastos_agua = sal_res("6.1.04")
    gastos_internet = sal_res("6.1.05")
    gastos_mantenimiento = sal_res("6.1.07")
    gastos_papeleria = sal_res("6.1.08")
    gastos_depreciacion = sal_res("6.1.09")
    gastos_cargas_pat = sal_res("6.1.11")
    gastos_prestaciones = sal_res("6.1.12")
    gastos_financieros = sal_res("6.1.10")

    total_gastos_operativos = round(
        gastos_publicidad + gastos_sueldos + gastos_alquiler + gastos_energia +
        gastos_agua + gastos_internet + gastos_mantenimiento + gastos_papeleria +
        gastos_depreciacion + gastos_cargas_pat + gastos_prestaciones + gastos_financieros, 2
    )

    utilidad_neta_contable = round(utilidad_bruta - total_gastos_operativos, 2)
    patrimonio_total = round(capital_social + utilidades_acumuladas + utilidad_neta_contable, 2)

    renglones_resultados = [
        {"renglon": 30, "descripcion": "Ventas de repuestos y accesorios", "importe": ventas_repuestos, "cuentas": "4.1.01"},
        {"renglon": 31, "descripcion": "Ingresos por servicios de taller", "importe": servicios_taller, "cuentas": "4.1.02"},
        {"renglon": 32, "descripcion": "Total Ingresos Brutos de Actividades Económicas", "importe": total_ingresos_brutos, "destacado": True},
        {"renglon": 33, "descripcion": "Costo de Ventas de Repuestos", "importe": costo_ventas, "cuentas": "5.1.01"},
        {"renglon": 34, "descripcion": "Utilidad Bruta Contable", "importe": utilidad_bruta, "destacado": True},
        {"renglon": 35, "descripcion": "Gastos de Sueldos y Salarios", "importe": gastos_sueldos, "cuentas": "6.1.01"},
        {"renglon": 36, "descripcion": "Cargas Sociales Patronales (INSS e INATEC)", "importe": gastos_cargas_pat, "cuentas": "6.1.11"},
        {"renglon": 37, "descripcion": "Prestaciones Sociales (Vacaciones y Aguinaldo)", "importe": gastos_prestaciones, "cuentas": "6.1.12"},
        {"renglon": 38, "descripcion": "Alquiler, Servicios Básicos y Mantenimiento", "importe": round(gastos_alquiler + gastos_energia + gastos_agua + gastos_internet + gastos_mantenimiento, 2), "cuentas": "6.1.02-6.1.07"},
        {"renglon": 39, "descripcion": "Publicidad, Papelería y Depreciación", "importe": round(gastos_publicidad + gastos_papeleria + gastos_depreciacion, 2), "cuentas": "6.1.06, 6.1.08, 6.1.09"},
        {"renglon": 40, "descripcion": "Gastos Financieros y Comisiones", "importe": gastos_financieros, "cuentas": "6.1.10"},
        {"renglon": 41, "descripcion": "Total Gastos Deducibles de Operación", "importe": total_gastos_operativos, "destacado": True},
        {"renglon": 42, "descripcion": "Utilidad Neta Contable del Ejercicio", "importe": utilidad_neta_contable, "destacado": True}
    ]

    # =========================================================================
    # SECCIÓN E: CÁLCULO DEL IR (Conciliación Fiscal)
    # =========================================================================
    ajustes = ajustes_fiscales or []
    gastos_no_deducibles = sum(float(a.get("importe", 0)) for a in ajustes if a.get("tipo_ajuste") == "Gasto No Deducible" or a.get("efecto") == "Aumenta Renta")
    ingresos_no_gravables = sum(float(a.get("importe", 0)) for a in ajustes if a.get("tipo_ajuste") == "Ingreso No Gravable" or a.get("efecto") == "Disminuye Renta")

    renta_neta_gravable = round(utilidad_neta_contable + gastos_no_deducibles - ingresos_no_gravables, 2)
    renta_gravable_positiva = max(0.00, renta_neta_gravable)

    # Reglas fiscales DGI
    tasa_ir_general = 0.30
    ir_calculado_30 = round(renta_gravable_positiva * tasa_ir_general, 2)

    tasa_pmd = 0.01
    pmd_calculado_1 = round(total_ingresos_brutos * tasa_pmd, 2)

    # Rige el mayor entre el 30% del IR o el 1% del PMD (Art. 59 Ley 822)
    ir_determinado = max(ir_calculado_30, pmd_calculado_1)
    metodo_aplicado = "IR por Actividades Económicas (30%)" if ir_calculado_30 >= pmd_calculado_1 else "Pago Mínimo Definitivo - PMD (1% de Ingresos Brutos)"

    # =========================================================================
    # SECCIÓN F: LIQUIDACIÓN DEL IMPUESTO (Acreditamientos y Saldo Final)
    # =========================================================================
    acreds = acreditamientos or []
    retenciones_sufridas = sum(float(ac.get("importe_total", 0)) for ac in acreds if ac.get("tipo") == "RETENCION_SUFRIDA")
    anticipos_mensuales = sum(float(ac.get("importe_total", 0)) for ac in acreds if ac.get("tipo") == "ANTICIPO_PAGADO")
    creditos_fiscales_ant = sum(float(ac.get("importe_total", 0)) for ac in acreds if ac.get("tipo") == "CREDITO_FISCAL")
    total_acreditamientos = round(retenciones_sufridas + anticipos_mensuales + creditos_fiscales_ant, 2)

    if ir_determinado >= total_acreditamientos:
        saldo_a_pagar = round(ir_determinado - total_acreditamientos, 2)
        saldo_a_favor = 0.00
    else:
        saldo_a_pagar = 0.00
        saldo_a_favor = round(total_acreditamientos - ir_determinado, 2)

    # Validaciones técnicas
    diferencia_cuadre = round(r12_total_activos - (total_pasivos + patrimonio_total), 2)
    balance_cuadrado = abs(diferencia_cuadre) < 0.05

    validaciones = []
    if not balance_cuadrado:
        validaciones.append({
            "tipo": "Advertencia",
            "codigo": "VAL_DESCUADRE_BALANCE",
            "renglon": 12,
            "motivo": f"El Balance General presenta una diferencia de C$ {diferencia_cuadre:,.2f} entre Activos ({r12_total_activos:,.2f}) y Pasivo + Patrimonio ({(total_pasivos + patrimonio_total):,.2f})."
        })
    if total_ingresos_brutos <= 0:
        validaciones.append({
            "tipo": "Advertencia",
            "codigo": "VAL_SIN_INGRESOS",
            "renglon": 32,
            "motivo": "No se registran ingresos por ventas en el ejercicio fiscal seleccionado."
        })
    if pmd_calculado_1 > ir_calculado_30:
        validaciones.append({
            "tipo": "Informativo",
            "codigo": "VAL_PMD_APLICADO",
            "renglon": 50,
            "motivo": f"Aplica el Pago Mínimo Definitivo (1% sobre ingresos: C$ {pmd_calculado_1:,.2f}) por ser superior al IR sobre renta neta (C$ {ir_calculado_30:,.2f})."
        })

    return {
        "anio": datos_contables["anio"],
        "fecha_corte": datos_contables["fecha_fin"],
        "balance": {
            "renglones": renglones_balance,
            "total_activos": r12_total_activos,
            "total_pasivos": total_pasivos,
            "patrimonio_total": patrimonio_total,
            "balance_cuadrado": balance_cuadrado,
            "diferencia_cuadre": diferencia_cuadre
        },
        "resultados": {
            "renglones": renglones_resultados,
            "total_ingresos_brutos": total_ingresos_brutos,
            "total_costos": costo_ventas,
            "utilidad_bruta": utilidad_bruta,
            "total_gastos": total_gastos_operativos,
            "utilidad_neta_contable": utilidad_neta_contable
        },
        "calculo_ir": {
            "utilidad_neta_contable": utilidad_neta_contable,
            "gastos_no_deducibles": gastos_no_deducibles,
            "ingresos_no_gravables": ingresos_no_gravables,
            "renta_neta_gravable": renta_neta_gravable,
            "ir_calculado_30": ir_calculado_30,
            "pmd_calculado_1": pmd_calculado_1,
            "ir_determinado": ir_determinado,
            "metodo_aplicado": metodo_aplicado
        },
        "liquidacion": {
            "ir_determinado": ir_determinado,
            "retenciones_sufridas": retenciones_sufridas,
            "anticipos_mensuales": anticipos_mensuales,
            "creditos_fiscales_ant": creditos_fiscales_ant,
            "total_acreditamientos": total_acreditamientos,
            "saldo_a_pagar": saldo_a_pagar,
            "saldo_a_favor": saldo_a_favor
        },
        "ajustes": ajustes,
        "acreditamientos": acreds,
        "validaciones": validaciones,
        "cuentas_balance": {k: float(v["saldo"]) for k, v in cb.items()},
        "cuentas_resultados": {k: float(v["saldo"]) for k, v in cr.items()}
    }

def obtener_acreditamientos_ejercicio(cursor, anio):
    cursor.execute("""
        SELECT id, tipo, concepto, ejercicio_fiscal, periodo_mes, fecha,
               numero_referencia, agente_retenedor_ruc, agente_retenedor_nombre,
               monto_base, porcentaje_aplicado, importe_total, importe_aplicado,
               documento_respaldo_url, estado, usuario_id, created_at
        FROM acreditamientos_tributarios
        WHERE ejercicio_fiscal = ?
        ORDER BY fecha DESC, id DESC
    """, (anio,))
    filas = []
    for r in cursor.fetchall():
        filas.append({
            "id": r.id,
            "tipo": r.tipo,
            "concepto": r.concepto,
            "ejercicio_fiscal": r.ejercicio_fiscal,
            "periodo_mes": r.periodo_mes,
            "fecha": str(r.fecha),
            "numero_referencia": r.numero_referencia,
            "agente_retenedor_ruc": r.agente_retenedor_ruc or "",
            "agente_retenedor_nombre": r.agente_retenedor_nombre or "",
            "monto_base": float(r.monto_base or 0),
            "porcentaje_aplicado": float(r.porcentaje_aplicado or 0),
            "importe_total": float(r.importe_total or 0),
            "importe_aplicado": float(r.importe_aplicado or 0),
            "documento_respaldo_url": r.documento_respaldo_url or "",
            "estado": r.estado
        })
    return filas

def guardar_acreditamiento(cursor, data, usuario_id):
    tipo = data.get("tipo", "RETENCION_SUFRIDA")
    concepto = data.get("concepto", "").strip()
    ejercicio_fiscal = int(data.get("ejercicio_fiscal", 2026))
    periodo_mes = int(data.get("periodo_mes", 1)) if data.get("periodo_mes") else None
    fecha = data.get("fecha") or fecha_hoy_nicaragua()
    numero_referencia = data.get("numero_referencia", "").strip()
    agente_ruc = data.get("agente_retenedor_ruc", "").strip()
    agente_nombre = data.get("agente_retenedor_nombre", "").strip()
    monto_base = float(data.get("monto_base", 0.0))
    porcentaje = float(data.get("porcentaje_aplicado", 0.0))
    importe_total = float(data.get("importe_total", 0.0))
    doc_url = data.get("documento_respaldo_url", "")

    if not concepto or not numero_referencia:
        raise ValueError("El concepto y el número de referencia/constancia son obligatorios.")
    if importe_total <= 0 and monto_base > 0 and porcentaje > 0:
        importe_total = round(monto_base * (porcentaje / 100.0), 2)
    if importe_total <= 0:
        raise ValueError("El importe retenido o anticipado debe ser mayor a cero.")

    cursor.execute("""
        INSERT INTO acreditamientos_tributarios (
            tipo, concepto, ejercicio_fiscal, periodo_mes, fecha,
            numero_referencia, agente_retenedor_ruc, agente_retenedor_nombre,
            monto_base, porcentaje_aplicado, importe_total, importe_aplicado,
            documento_respaldo_url, estado, usuario_id
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0.00, ?, 'Disponible', ?)
    """, (tipo, concepto, ejercicio_fiscal, periodo_mes, fecha,
          numero_referencia, agente_ruc, agente_nombre,
          monto_base, porcentaje, importe_total, doc_url, usuario_id))
    
    cursor.execute("SELECT @@IDENTITY AS id")
    return cursor.fetchone()[0]

def eliminar_acreditamiento(cursor, ac_id):
    cursor.execute("SELECT estado FROM acreditamientos_tributarios WHERE id = ?", (ac_id,))
    row = cursor.fetchone()
    if not row:
        raise ValueError("Acreditamiento no encontrado.")
    if row[0] == 'Aplicado Total':
        raise ValueError("No se puede eliminar un acreditamiento que ya fue aplicado en una declaración aprobada.")
    cursor.execute("DELETE FROM acreditamientos_tributarios WHERE id = ?", (ac_id,))

def obtener_ajustes_ejercicio(cursor, anio, declaracion_id=None):
    if declaracion_id:
        cursor.execute("""
            SELECT id, declaracion_id, ejercicio_fiscal, numero_renglon, concepto,
                   tipo_ajuste, efecto, importe, justificacion, referencia_normativa
            FROM declaracion_ajustes_fiscales
            WHERE declaracion_id = ?
            ORDER BY id
        """, (declaracion_id,))
    else:
        cursor.execute("""
            SELECT id, declaracion_id, ejercicio_fiscal, numero_renglon, concepto,
                   tipo_ajuste, efecto, importe, justificacion, referencia_normativa
            FROM declaracion_ajustes_fiscales
            WHERE ejercicio_fiscal = ?
            ORDER BY id
        """, (anio,))
    ajustes = []
    for r in cursor.fetchall():
        ajustes.append({
            "id": r.id,
            "declaracion_id": r.declaracion_id,
            "ejercicio_fiscal": r.ejercicio_fiscal,
            "numero_renglon": r.numero_renglon,
            "concepto": r.concepto,
            "tipo_ajuste": r.tipo_ajuste,
            "efecto": r.efecto,
            "importe": float(r.importe),
            "justificacion": r.justificacion,
            "referencia_normativa": r.referencia_normativa or ""
        })
    return ajustes

def guardar_ajuste_fiscal(cursor, data, usuario_id):
    declaracion_id = data.get("declaracion_id")
    ejercicio_fiscal = int(data.get("ejercicio_fiscal", 2026))
    numero_renglon = int(data.get("numero_renglon", 50))
    concepto = data.get("concepto", "").strip()
    tipo_ajuste = data.get("tipo_ajuste", "Gasto No Deducible")
    efecto = data.get("efecto", "Aumenta Renta")
    importe = float(data.get("importe", 0.0))
    justificacion = data.get("justificacion", "").strip()
    ref_normativa = data.get("referencia_normativa", "Ley 822 Art. 43").strip()

    if not concepto or importe <= 0:
        raise ValueError("El concepto y un importe positivo son requeridos para el ajuste.")
    if not justificacion:
        justificacion = "Ajuste de conciliación fiscal según normativa tributaria vigente."

    if declaracion_id:
        cursor.execute("""
            INSERT INTO declaracion_ajustes_fiscales (
                declaracion_id, ejercicio_fiscal, numero_renglon, concepto,
                tipo_ajuste, efecto, importe, justificacion, referencia_normativa, usuario_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (declaracion_id, ejercicio_fiscal, numero_renglon, concepto,
              tipo_ajuste, efecto, importe, justificacion, ref_normativa, usuario_id))
    else:
        # Ajuste en borrador sin ID de declaración aún
        pass
    
    return True

def guardar_declaracion_completa(cursor, simulacion, usuario_id, es_aprobada=False):
    """
    Persiste la declaración en la tabla declaraciones_ir y sus renglones en declaracion_renglones_detalle.
    """
    anio = simulacion["anio"]
    estado = "Aprobada" if es_aprobada else "Borrador"
    
    calc = simulacion["calculo_ir"]
    liq = simulacion["liquidacion"]
    res = simulacion["resultados"]
    
    # Verificar si ya existe una versión previa para este año
    cursor.execute("""
        SELECT id, version FROM declaraciones_ir
        WHERE ejercicio_fiscal = ?
        ORDER BY version DESC
    """, (anio,))
    row_prev = cursor.fetchone()
    version = (row_prev.version + 1) if (row_prev and es_aprobada) else (row_prev.version if row_prev else 1)
    decl_ant_id = row_prev.id if (row_prev and es_aprobada) else None
    es_sustitutiva = 1 if (row_prev and es_aprobada) else 0

    # Insertar o actualizar cabecera
    cursor.execute("""
        INSERT INTO declaraciones_ir (
            ejercicio_fiscal, version, es_sustitutiva, declaracion_anterior_id,
            estado, regimen_tributario_aplicado,
            total_ingresos_brutos, total_costos, total_gastos_deducibles,
            renta_neta_gravable, ir_calculado, pago_minimo_definitivo, ir_determinado,
            total_acreditamientos, saldo_a_pagar, saldo_a_favor,
            tiene_errores_bloqueantes, observaciones, usuario_elaboro_id, usuario_aprobo_id,
            fecha_aprobacion
        ) VALUES (
            ?, ?, ?, ?,
            ?, 'Régimen General',
            ?, ?, ?,
            ?, ?, ?, ?,
            ?, ?, ?,
            0, ?, ?, ?,
            ?
        )
    """, (
        anio, version, es_sustitutiva, decl_ant_id,
        estado,
        res["total_ingresos_brutos"], res["total_costos"], res["total_gastos"],
        calc["renta_neta_gravable"], calc["ir_calculado_30"], calc["pmd_calculado_1"], calc["ir_determinado"],
        liq["total_acreditamientos"], liq["saldo_a_pagar"], liq["saldo_a_favor"],
        f"Simulación generada automáticamente desde contabilidad. Método: {calc['metodo_aplicado']}",
        usuario_id, (usuario_id if es_aprobada else None),
        (datetime.now() if es_aprobada else None)
    ))
    cursor.execute("SELECT @@IDENTITY AS id")
    declaracion_id = cursor.fetchone()[0]

    # Insertar renglones de Balance General
    for r in simulacion["balance"]["renglones"]:
        cursor.execute("""
            INSERT INTO declaracion_renglones_detalle (
                declaracion_id, seccion, numero_renglon, descripcion_renglon,
                tipo_renglon, importe_base_contable, importe_ajustes, importe_declarado,
                cuentas_asociadas
            ) VALUES (?, 'BALANCE_GENERAL', ?, ?, ?, ?, 0.00, ?, ?)
        """, (declaracion_id, r["renglon"], r["descripcion"], r["tipo"], r["importe"], r["importe"], r.get("cuentas", "")))

    # Insertar renglones de Estado de Resultados
    for r in simulacion["resultados"]["renglones"]:
        cursor.execute("""
            INSERT INTO declaracion_renglones_detalle (
                declaracion_id, seccion, numero_renglon, descripcion_renglon,
                tipo_renglon, importe_base_contable, importe_ajustes, importe_declarado,
                cuentas_asociadas
            ) VALUES (?, 'ESTADO_RESULTADOS', ?, ?, 'Contable', ?, 0.00, ?, ?)
        """, (declaracion_id, r["renglon"], r["descripcion"], r["importe"], r["importe"], r.get("cuentas", "")))

    # Insertar validaciones detectadas
    for v in simulacion.get("validaciones", []):
        cursor.execute("""
            INSERT INTO declaracion_validaciones (
                declaracion_id, tipo, codigo_validacion, renglon_afectado,
                modulo_origen, motivo, resuelto
            ) VALUES (?, ?, ?, ?, 'FISCAL', ?, 0)
        """, (declaracion_id, v["tipo"], v["codigo"], v.get("renglon"), v["motivo"]))

    # Si es aprobada, marcar acreditamientos como aplicados
    if es_aprobada and simulacion.get("acreditamientos"):
        for ac in simulacion["acreditamientos"]:
            cursor.execute("""
                UPDATE acreditamientos_tributarios
                SET estado = 'Aplicado Total', importe_aplicado = importe_total
                WHERE id = ?
            """, (ac["id"],))

    return declaracion_id

def listar_declaraciones_guardadas(cursor):
    cursor.execute("""
        SELECT d.id, d.ejercicio_fiscal, d.version, d.es_sustitutiva, d.estado,
               d.regimen_tributario_aplicado, d.total_ingresos_brutos, d.renta_neta_gravable,
               d.ir_determinado, d.total_acreditamientos, d.saldo_a_pagar, d.saldo_a_favor,
               d.created_at, d.fecha_aprobacion, u.nombre_completo AS usuario_elaboro
        FROM declaraciones_ir d
        LEFT JOIN usuarios u ON d.usuario_elaboro_id = u.id
        ORDER BY d.ejercicio_fiscal DESC, d.version DESC
    """)
    filas = []
    for r in cursor.fetchall():
        filas.append({
            "id": r.id,
            "ejercicio_fiscal": r.ejercicio_fiscal,
            "version": r.version,
            "es_sustitutiva": bool(r.es_sustitutiva),
            "estado": r.estado,
            "regimen": r.regimen_tributario_aplicado,
            "ingresos_brutos": float(r.total_ingresos_brutos or 0),
            "renta_gravable": float(r.renta_neta_gravable or 0),
            "ir_determinado": float(r.ir_determinado or 0),
            "acreditamientos": float(r.total_acreditamientos or 0),
            "saldo_a_pagar": float(r.saldo_a_pagar or 0),
            "saldo_a_favor": float(r.saldo_a_favor or 0),
            "fecha_creacion": str(r.created_at)[:19] if r.created_at else "",
            "usuario_elaboro": r.usuario_elaboro or "Sistema"
        })
    return filas

def registrar_presentacion_dgi(cursor, data, usuario_id):
    decl_id = int(data.get("declaracion_id"))
    cursor.execute("SELECT id FROM declaraciones_ir WHERE id = ?", (decl_id,))
    declaration = cursor.fetchone()
    if not declaration:
        raise ValueError('No se encontró la declaración especificada.')
    num_referencia = data.get("numero_referencia_dgi", "").strip()
    fecha_evento = data.get("fecha_evento") or fecha_hoy_nicaragua()
    importe_pagado = float(data.get("importe_pagado", 0.0))
    banco = data.get("banco_caja", "Ventanilla DGI").strip()
    medio_pago = data.get("medio_pago", "Transferencia / Débito Bancario").strip()
    obs = data.get("observaciones", "").strip()

    if not num_referencia:
        raise ValueError("El número de referencia o confirmación de la DGI es obligatorio.")

    cursor.execute("""
        INSERT INTO declaracion_presentacion_pagos (
            declaracion_id, tipo_evento, fecha_evento, numero_referencia_dgi,
            importe_pagado, banco_caja, medio_pago, observaciones, usuario_id
        ) VALUES (?, 'Presentacion_DGI', ?, ?, ?, ?, ?, ?, ?)
    """, (decl_id, fecha_evento, num_referencia, importe_pagado, banco, medio_pago, obs, usuario_id))

    cursor.execute("""
        UPDATE declaraciones_ir
        SET estado = 'Presentada', updated_at = GETDATE()
        WHERE id = ?
    """, (decl_id,))

    return True
