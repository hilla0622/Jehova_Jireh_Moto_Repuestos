# ==============================================================================
# calculos_rrhh.py — Lógica de Nómina (Nicaragua)
# Jehová Jireh Moto Repuestos
#
# Leyes aplicadas:
#   - Ley 185 (Código del Trabajo): Vacaciones y Aguinaldo
#   - Ley 822 (Ley de Concertación Tributaria): IR Salarios
#   - INSS: Ley 539 (Laboral 7%, Patronal 22.5%)
# ==============================================================================


def calcular_inss_laboral(salario_bruto: float) -> float:
    """
    INSS Laboral: 7% sobre el salario bruto.
    El trabajador aporta este porcentaje de su salario al INSS.
    """
    return round(salario_bruto * 0.07, 2)


def calcular_inss_patronal(salario_bruto: float) -> float:
    """
    INSS Patronal: 22.5% sobre el salario bruto.
    El empleador paga este porcentaje adicional al INSS (no se descuenta del empleado).
    Nota: Actualmente en Nicaragua la tasa patronal es 22.5%.
    """
    return round(salario_bruto * 0.225, 2)


def calcular_ir_nicaragua(salario_bruto: float, inss_laboral: float, es_quincenal: bool = False) -> float:
    """
    Cálculo de Retención en la Fuente del IR (Rentas del Trabajo).
    Ley 822 — Artículos 20, 21 y 23 (tabla de rentas del trabajo).

    Metodología:
    1. Base imponible mensual = salario_bruto - inss_laboral
    2. Se proyecta anualmente: base_anual = base_mensual * 12
    3. Se aplica la tabla progresiva anual
    4. El IR mensual = IR anual / 12

    Tabla progresiva vigente (C$ córdobas):
    - Hasta       C$ 100,000    → exento
    - C$ 100,001 a C$ 200,000   → 15% sobre exceso de C$100,000
    - C$ 200,001 a C$ 350,000   → C$15,000 + 20% sobre exceso de C$200,000
    - C$ 350,001 a C$ 500,000   → C$45,000 + 25% sobre exceso de C$350,000
    - Más de      C$ 500,000    → C$82,500 + 30% sobre exceso de C$500,000
    """
    base_periodo = salario_bruto - inss_laboral
    factor_anual = 24 if es_quincenal else 12
    base_anual = base_periodo * factor_anual

    if base_anual <= 100_000:
        ir_anual = 0.0
    elif base_anual <= 200_000:
        ir_anual = (base_anual - 100_000) * 0.15
    elif base_anual <= 350_000:
        ir_anual = 15_000 + (base_anual - 200_000) * 0.20
    elif base_anual <= 500_000:
        ir_anual = 45_000 + (base_anual - 350_000) * 0.25
    else:
        ir_anual = 82_500 + (base_anual - 500_000) * 0.30

    ir_periodo = round(ir_anual / factor_anual, 2)
    return ir_periodo


def calcular_provisiones(salario_bruto: float) -> tuple:
    """
    Provisiones laborales según Ley 185 (Código del Trabajo de Nicaragua):
    - Vacaciones:  1/12 del salario bruto mensual (el trabajador gana 15 días/año = 1.25 días/mes)
    - Aguinaldo:   1/12 del salario bruto mensual (equivale al 13° mes de salario)

    Ambas son provisiones que el empleador debe reservar mensualmente como pasivos laborales.
    """
    provision_vacaciones = round(salario_bruto / 12, 2)
    provision_aguinaldo = round(salario_bruto / 12, 2)
    return provision_vacaciones, provision_aguinaldo


def calcular_nomina_empleado(salario_base: float, ingresos_extra: float = 0.0) -> dict:
    """
    Función principal que calcula todos los componentes de nómina para un empleado.

    Args:
        salario_base: Salario base mensual del empleado
        ingresos_extra: Bonos, horas extra u otros ingresos adicionales

    Returns:
        dict con todos los campos de nómina calculados
    """
    salario_bruto = salario_base + ingresos_extra

    # Deducciones del trabajador
    inss_laboral = calcular_inss_laboral(salario_bruto)
    ir_retencion = calcular_ir_nicaragua(salario_bruto, inss_laboral)
    total_deducciones = round(inss_laboral + ir_retencion, 2)
    salario_neto = round(salario_bruto - total_deducciones, 2)

    # Cargas patronales (no se descuentan del empleado)
    inss_patronal = calcular_inss_patronal(salario_bruto)
    provision_vacaciones, provision_aguinaldo = calcular_provisiones(salario_bruto)

    return {
        'salario_ordinario': round(salario_base, 2),
        'ingresos_extra': round(ingresos_extra, 2),
        'salario_bruto': round(salario_bruto, 2),
        'inss_laboral': inss_laboral,
        'ir_retencion': ir_retencion,
        'total_deducciones': total_deducciones,
        'salario_neto': salario_neto,
        # Cargas patronales (costos del empleador)
        'inss_patronal': inss_patronal,
        'provision_vacaciones': provision_vacaciones,
        'provision_aguinaldo': provision_aguinaldo,
        # Costo total real para el empleador
        'costo_total_patronal': round(
            salario_bruto + inss_patronal + provision_vacaciones + provision_aguinaldo, 2
        )
    }

def procesar_detalle_empleado(salario_base_mensual: float, kpi_meta: float = 0.0, adelanto: float = 0.0, dias_trabajados: float = 15.0) -> dict:
    """Genera todos los valores numéricos para un registro de nómina (especialmente para la colilla)."""
    salario_devengado = round((salario_base_mensual / 30.0) * dias_trabajados, 2)
    total_percepciones = round(salario_devengado + kpi_meta, 2)
    
    inss_lab = calcular_inss_laboral(total_percepciones)
    es_quincenal = dias_trabajados <= 15.0
    ir = calcular_ir_nicaragua(total_percepciones, inss_lab, es_quincenal=es_quincenal)
    
    total_deducciones = round(inss_lab + ir + adelanto, 2)
    neto_a_recibir = round(total_percepciones - total_deducciones, 2)
    
    return {
        "salario_devengado": salario_devengado,
        "total_percepciones": total_percepciones,
        "inss_laboral": inss_lab,
        "ir": ir,
        "total_deducciones": total_deducciones,
        "neto_a_recibir": neto_a_recibir
    }
