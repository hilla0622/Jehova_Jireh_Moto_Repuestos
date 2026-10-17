"""Reglas compartidas de RRHH, sin conexiones a la base de datos."""
from calendar import monthrange
from datetime import date
from math import isfinite

ROLES_RRHH = ('Administrador', 'Responsable de Recursos Humanos',
              'Gerente Administrativo y Financiero')
ALIAS_PARAMETROS = {'VACACIONES_DIAS_MES': 'VACACIONES_MES',
                    'RECARGO_HORA_EXTRA': 'HORAS_EXTRAS_RECARGO'}
TASAS = {'INSS_LABORAL', 'INSS_PATRONAL', 'INATEC_PATRONAL', 'AGUINALDO_PROV'}


def fecha(valor):
    return date.fromisoformat(str(valor)[:10])


def limites_periodo(mes, anio):
    return date(anio, mes, 1), date(anio, mes, monthrange(anio, mes)[1])


def dias_en_periodo(inicio, fin, dias, desde, hasta):
    """Distribuye los días registrados por su intervalo inclusivo, incluso fracciones."""
    inicio, fin = fecha(inicio), fecha(fin)
    if fin < inicio or not isfinite(float(dias)) or float(dias) < 0:
        raise ValueError('Movimiento laboral con fechas o días inválidos.')
    comunes = max(0, (min(fin, hasta) - max(inicio, desde)).days + 1)
    return float(dias) * comunes / ((fin - inicio).days + 1)


def normalizar_parametro(row):
    p = dict(row)
    codigo = p.get('codigo') or p.get('clave')
    valor = float(p['valor'])
    # La migración antigua utiliza fracciones y un multiplicador para horas extra.
    if 'codigo' not in p and codigo in TASAS:
        valor *= 100
    if codigo == 'RECARGO_HORA_EXTRA':
        valor = (valor - 1) * 100
    p.update(codigo=ALIAS_PARAMETROS.get(codigo, codigo), valor=round(valor, 6))
    if p['codigo'] == 'HORAS_EXTRAS_RECARGO':
        p['unidad'] = '%'
    p['fecha_vigencia'] = str(p.get('fecha_vigencia') or '')[:10]
    return p


def parametros_calculo(rows):
    return {p['codigo']: p['valor'] for p in map(normalizar_parametro, rows)}


def validar_parametro(codigo, valor):
    valor = float(valor)
    if not isfinite(valor) or valor < 0:
        raise ValueError('El valor debe ser un número finito mayor o igual a cero.')
    limite = 100 if codigo in TASAS else 30 if codigo == 'VACACIONES_MES' else None
    if limite is not None and valor > limite:
        raise ValueError(f'El valor máximo para {codigo} es {limite}.')
    return valor
