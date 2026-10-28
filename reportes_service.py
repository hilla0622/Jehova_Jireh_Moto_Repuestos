import statistics
from io import BytesIO
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

MESES_NOMBRES = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 
                 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']

def construir_filtro_periodo(rango=None, mes=None, anio=None, fecha_inicio=None, fecha_fin=None):
    """
    Construye las cláusulas WHERE y parámetros para ventas y compras.
    """
    condiciones_v = ["v.estado = 'Completada'"]
    params_v = []
    condiciones_c = ["c.estado = 'Completada'"]
    params_c = []

    mes_int = int(mes) if (mes and str(mes).isdigit() and 1 <= int(mes) <= 12) else None
    anio_int = int(anio) if (anio and str(anio).isdigit() and int(anio) > 2000) else None

    if rango == 'hoy':
        condiciones_v.append("CAST(v.fecha_venta AS DATE) = CAST(GETDATE() AS DATE)")
        condiciones_c.append("CAST(c.fecha_compra AS DATE) = CAST(GETDATE() AS DATE)")
        texto = "Hoy"
    elif rango == '7dias':
        condiciones_v.append("v.fecha_venta >= DATEADD(day, -7, GETDATE())")
        condiciones_c.append("c.fecha_compra >= DATEADD(day, -7, GETDATE())")
        texto = "Últimos 7 días"
    elif rango == 'mes':
        condiciones_v.append("YEAR(v.fecha_venta) = YEAR(GETDATE()) AND MONTH(v.fecha_venta) = MONTH(GETDATE())")
        condiciones_c.append("YEAR(c.fecha_compra) = YEAR(GETDATE()) AND MONTH(c.fecha_compra) = MONTH(GETDATE())")
        texto = f"{MESES_NOMBRES[10]} (Mes Actual)"  # Dinámico según BD o GETDATE
    elif rango == 'anio':
        condiciones_v.append("YEAR(v.fecha_venta) = YEAR(GETDATE())")
        condiciones_c.append("YEAR(c.fecha_compra) = YEAR(GETDATE())")
        texto = "Año en curso"
    elif fecha_inicio and fecha_fin:
        condiciones_v.append("CAST(v.fecha_venta AS DATE) >= ? AND CAST(v.fecha_venta AS DATE) <= ?")
        params_v.extend([fecha_inicio, fecha_fin])
        condiciones_c.append("CAST(c.fecha_compra AS DATE) >= ? AND CAST(c.fecha_compra AS DATE) <= ?")
        params_c.extend([fecha_inicio, fecha_fin])
        texto = f"Del {fecha_inicio} al {fecha_fin}"
    elif anio_int and mes_int:
        condiciones_v.append("YEAR(v.fecha_venta) = ? AND MONTH(v.fecha_venta) = ?")
        params_v.extend([anio_int, mes_int])
        condiciones_c.append("YEAR(c.fecha_compra) = ? AND MONTH(c.fecha_compra) = ?")
        params_c.extend([anio_int, mes_int])
        texto = f"{MESES_NOMBRES[mes_int]} {anio_int}"
    elif anio_int:
        condiciones_v.append("YEAR(v.fecha_venta) = ?")
        params_v.append(anio_int)
        condiciones_c.append("YEAR(c.fecha_compra) = ?")
        params_c.append(anio_int)
        texto = f"Año {anio_int}"
    elif mes_int:
        condiciones_v.append("MONTH(v.fecha_venta) = ?")
        params_v.append(mes_int)
        condiciones_c.append("MONTH(c.fecha_compra) = ?")
        params_c.append(mes_int)
        texto = f"Mes de {MESES_NOMBRES[mes_int]} (Histórico)"
    else:
        texto = "Histórico Completo"

    where_v = "WHERE " + " AND ".join(condiciones_v)
    where_c = "WHERE " + " AND ".join(condiciones_c)

    return {
        "where_v": where_v,
        "params_v": params_v,
        "where_c": where_c,
        "params_c": params_c,
        "texto": texto,
        "rango": rango,
        "mes": mes_int,
        "anio": anio_int,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin
    }

def calcular_medidas_descriptivas(montos):
    """
    Calcula Media, Mediana, Máximo, Mínimo, Rango, Varianza, Desviación Estándar y Coeficiente de Variación.
    """
    n = len(montos)
    if n == 0:
        return {
            "n": 0,
            "media": 0.0,
            "mediana": 0.0,
            "maximo": 0.0,
            "minimo": 0.0,
            "rango": 0.0,
            "varianza": 0.0,
            "desviacion_estandar": 0.0,
            "coeficiente_variacion": 0.0,
            "interpretacion": "Sin transacciones registradas en el período para cálculo estadístico."
        }
    
    val_min = min(montos)
    val_max = max(montos)
    val_rango = round(val_max - val_min, 2)
    val_media = round(statistics.mean(montos), 2)
    val_mediana = round(statistics.median(montos), 2)
    
    val_var = round(statistics.variance(montos), 2) if n > 1 else 0.0
    val_std = round(statistics.stdev(montos), 2) if n > 1 else 0.0
    val_cv = round((val_std / val_media * 100), 2) if val_media > 0 else 0.0

    if val_cv <= 15:
        interp = "Muy baja dispersión (ventas homogéneas y consistentes)."
    elif val_cv <= 30:
        interp = "Dispersión moderada estándar en comercialización de repuestos."
    else:
        interp = "Alta dispersión / heterogeneidad en importes (compras mixtas de accesorios pequeños y repuestos mayores)."

    return {
        "n": n,
        "media": val_media,
        "mediana": val_mediana,
        "maximo": val_max,
        "minimo": val_min,
        "rango": val_rango,
        "varianza": val_var,
        "desviacion_estandar": val_std,
        "coeficiente_variacion": val_cv,
        "interpretacion": interp
    }

def procesar_reporte_completo(cursor, filtro, criterio_abc='inversion', agrupar_meses=False):
    """
    Ejecuta todas las consultas para un período y construye el diccionario completo de datos.
    """
    where_v = filtro["where_v"]
    params_v = tuple(filtro["params_v"])
    where_c = filtro["where_c"]
    params_c = tuple(filtro["params_c"])

    # 1. KPIs Ventas
    q_vk = f"SELECT COUNT(v.id) AS cant, ISNULL(SUM(v.total), 0) AS monto FROM ventas v {where_v}"
    cursor.execute(q_vk, params_v)
    vk = cursor.fetchone()
    ventas_conteo = int(vk.cant) if vk and vk.cant else 0
    ventas_monto = float(vk.monto) if vk and vk.monto else 0.0

    # 2. Lista de montos para medidas estadísticas descriptivas
    q_montos = f"SELECT v.total FROM ventas v {where_v} ORDER BY v.total ASC"
    cursor.execute(q_montos, params_v)
    montos_ventas = [float(r.total) for r in cursor.fetchall() if r.total is not None]
    medidas_estadisticas = calcular_medidas_descriptivas(montos_ventas)

    # 3. KPIs Compras
    q_ck = f"SELECT COUNT(c.id) AS cant, ISNULL(SUM(c.total), 0) AS monto FROM compras c {where_c}"
    cursor.execute(q_ck, params_c)
    ck = cursor.fetchone()
    compras_conteo = int(ck.cant) if ck and ck.cant else 0
    compras_monto = float(ck.monto) if ck and ck.monto else 0.0

    # 4. Costo de Ventas Real (sum(cantidad * costo_historico)) y Unidades
    q_detalles = f"""
        SELECT 
            ISNULL(SUM(dv.cantidad), 0) AS unidades,
            ISNULL(SUM(dv.cantidad * dv.costo_historico), 0) AS costo_ventas
        FROM detalle_ventas dv
        INNER JOIN ventas v ON dv.venta_id = v.id
        {where_v}
    """
    cursor.execute(q_detalles, params_v)
    dk = cursor.fetchone()
    unidades_vendidas = int(dk.unidades) if dk and dk.unidades else 0
    costo_ventas = float(dk.costo_ventas) if dk and dk.costo_ventas else 0.0

    utilidad_bruta = round(ventas_monto - costo_ventas, 2)
    margen_bruto_pct = round((utilidad_bruta / ventas_monto * 100), 2) if ventas_monto > 0 else 0.0
    ticket_promedio = round(ventas_monto / ventas_conteo, 2) if ventas_conteo > 0 else 0.0

    # 5. Inventario Global Actual
    valor_inventario_costo = 0.0
    valor_inventario_venta = 0.0
    stock_total_actual = 0
    try:
        cursor.execute("SELECT * FROM vista_balance_inventario")
        b = cursor.fetchone()
        if b:
            valor_inventario_costo = float(b.valor_total_costo) if b.valor_total_costo else 0.0
            valor_inventario_venta = float(b.valor_total_venta) if b.valor_total_venta else 0.0
            stock_total_actual = int(b.total_unidades_fisicas) if b.total_unidades_fisicas else 0
    except Exception:
        cursor.execute("SELECT ISNULL(SUM(stock_actual * costo), 0) AS val_costo, ISNULL(SUM(stock_actual * precio_venta), 0) AS val_venta, ISNULL(SUM(stock_actual), 0) AS tot_stock FROM productos WHERE activo = 1")
        b = cursor.fetchone()
        if b:
            valor_inventario_costo = float(b.val_costo) if b.val_costo else 0.0
            valor_inventario_venta = float(b.val_venta) if b.val_venta else 0.0
            stock_total_actual = int(b.tot_stock) if b.tot_stock else 0

    # Rotación Financiera (Monetaria): Costo de Ventas / Inventario al Costo
    rotacion_monetaria = round(costo_ventas / valor_inventario_costo, 4) if valor_inventario_costo > 0 else 0.0
    dias_inventario = round(365 / rotacion_monetaria, 1) if rotacion_monetaria > 0 else 0.0

    # Rotación Física: Unidades Vendidas / Stock Físico Actual
    rotacion_unidades = round(unidades_vendidas / stock_total_actual, 4) if stock_total_actual > 0 else 0.0

    # 6. Tendencia Cronológica
    q_tendencia = f"""
        SELECT CONVERT(varchar, v.fecha_venta, 23) AS fecha, 
               COUNT(v.id) AS transacciones,
               ISNULL(SUM(v.total), 0) AS monto
        FROM ventas v
        {where_v}
        GROUP BY CONVERT(varchar, v.fecha_venta, 23)
        ORDER BY fecha ASC
    """
    cursor.execute(q_tendencia, params_v)
    tendencia_lista = [{"fecha": r.fecha, "monto": float(r.monto), "transacciones": int(r.transacciones)} for r in cursor.fetchall()]

    # 7. Desglose Anual por Meses (si se evalúa un año completo o agrupado)
    desglose_mensual_anio = []
    anio_eval = filtro.get("anio")
    if not anio_eval and filtro.get("rango") == 'anio':
        cursor.execute("SELECT YEAR(GETDATE())")
        row_y = cursor.fetchone()
        anio_eval = row_y[0] if row_y else 2026

    if anio_eval:
        q_meses = """
            SELECT 
                MONTH(v.fecha_venta) AS mes,
                COUNT(v.id) AS transacciones,
                ISNULL(SUM(v.total), 0) AS ventas,
                ISNULL(SUM(dv.costo), 0) AS costo,
                ISNULL(SUM(dv.unidades), 0) AS unidades
            FROM ventas v
            LEFT JOIN (
                SELECT venta_id, SUM(cantidad * costo_historico) AS costo,
                       SUM(cantidad) AS unidades
                FROM detalle_ventas GROUP BY venta_id
            ) dv ON v.id = dv.venta_id
            WHERE v.estado = 'Completada' AND YEAR(v.fecha_venta) = ?
            GROUP BY MONTH(v.fecha_venta)
            ORDER BY mes ASC
        """
        cursor.execute(q_meses, (anio_eval,))
        meses_dict = {int(r.mes): {
            "transacciones": int(r.transacciones),
            "ventas": float(r.ventas),
            "costo": float(r.costo),
            "utilidad": round(float(r.ventas) - float(r.costo), 2),
            "margen_pct": round(((float(r.ventas) - float(r.costo)) / float(r.ventas) * 100), 2) if float(r.ventas) > 0 else 0.0,
            "unidades": int(r.unidades)
        } for r in cursor.fetchall()}

        for m_idx in range(1, 13):
            m_data = meses_dict.get(m_idx, {
                "transacciones": 0, "ventas": 0.0, "costo": 0.0, "utilidad": 0.0, "margen_pct": 0.0, "unidades": 0
            })
            desglose_mensual_anio.append({
                "mes_numero": m_idx,
                "mes_nombre": MESES_NOMBRES[m_idx],
                "transacciones": m_data["transacciones"],
                "ventas": m_data["ventas"],
                "costo": m_data["costo"],
                "utilidad": m_data["utilidad"],
                "margen_pct": m_data["margen_pct"],
                "unidades": m_data["unidades"]
            })

    # 8. Rendimiento por Categoría de Repuestos
    q_cat = f"""
        SELECT 
            c.id AS categoria_id,
            c.nombre AS categoria,
            ISNULL(SUM(dv.cantidad), 0) AS unidades,
            ISNULL(SUM(dv.subtotal), 0) AS total_ventas,
            ISNULL(SUM(dv.cantidad * dv.costo_historico), 0) AS costo_ventas
        FROM detalle_ventas dv
        INNER JOIN ventas v ON dv.venta_id = v.id
        INNER JOIN productos p ON dv.producto_id = p.id
        INNER JOIN categorias c ON p.categoria_id = c.id
        {where_v}
        GROUP BY c.id, c.nombre
        ORDER BY total_ventas DESC
    """
    cursor.execute(q_cat, params_v)
    categorias_analisis = []
    for cr in cursor.fetchall():
        t_v = float(cr.total_ventas)
        c_v = float(cr.costo_ventas)
        m_v = round(t_v - c_v, 2)
        pct_v = round((t_v / ventas_monto * 100), 2) if ventas_monto > 0 else 0.0
        pct_m = round((m_v / t_v * 100), 2) if t_v > 0 else 0.0
        categorias_analisis.append({
            "categoria_id": cr.categoria_id,
            "categoria": cr.categoria,
            "unidades": int(cr.unidades),
            "total_ventas": t_v,
            "costo_ventas": c_v,
            "margen": m_v,
            "margen_porcentaje": pct_m,
            "participacion_porcentaje": pct_v
        })

    # 9. Métodos de Pago
    q_metodos = f"""
        SELECT 
            ISNULL(v.forma_pago, 'Efectivo') AS metodo,
            COUNT(v.id) AS transacciones,
            ISNULL(SUM(v.total), 0) AS total
        FROM ventas v
        {where_v}
        GROUP BY v.forma_pago
        ORDER BY total DESC
    """
    cursor.execute(q_metodos, params_v)
    metodos_pago = []
    for mr in cursor.fetchall():
        m_tot = float(mr.total)
        pct_p = round((m_tot / ventas_monto * 100), 2) if ventas_monto > 0 else 0.0
        metodos_pago.append({
            "metodo": mr.metodo,
            "transacciones": int(mr.transacciones),
            "total": m_tot,
            "porcentaje": pct_p
        })

    # 10. Catálogo Completo para Evaluación ABC y Alertas Universales
    cursor.execute("""
        SELECT p.id, p.codigo_sku AS codigo, p.nombre, c.nombre AS categoria,
               p.precio_venta AS precio, p.costo, p.stock_actual AS stock, p.stock_minimo AS min_stock
        FROM productos p
        INNER JOIN categorias c ON p.categoria_id = c.id
        WHERE p.activo = 1
    """)
    all_prods_rows = cursor.fetchall()

    # Ventas por producto en el período
    q_prods_per = f"""
        SELECT dv.producto_id,
               ISNULL(SUM(dv.cantidad), 0) AS unidades,
               ISNULL(SUM(dv.subtotal), 0) AS ingreso,
               ISNULL(SUM(dv.subtotal - (dv.cantidad * dv.costo_historico)), 0) AS utilidad
        FROM detalle_ventas dv
        INNER JOIN ventas v ON dv.venta_id = v.id
        {where_v}
        GROUP BY dv.producto_id
    """
    cursor.execute(q_prods_per, params_v)
    ventas_prod_map = {r.producto_id: {
        "unidades": int(r.unidades),
        "ingreso": float(r.ingreso),
        "utilidad": float(r.utilidad)
    } for r in cursor.fetchall()}

    prods_evaluados = []
    for pr in all_prods_rows:
        pid = pr.id
        p_sales = ventas_prod_map.get(pid, {"unidades": 0, "ingreso": 0.0, "utilidad": 0.0})
        stk = int(pr.stock)
        cst = float(pr.costo)
        prc = float(pr.precio)
        val_inv = round(stk * cst, 2)

        prods_evaluados.append({
            "id": pid,
            "codigo": pr.codigo,
            "nombre": pr.nombre,
            "categoria": pr.categoria,
            "precio": prc,
            "costo": cst,
            "stock": stk,
            "min_stock": int(pr.min_stock),
            "valor_inmovilizado": val_inv,
            "unidades_vendidas": p_sales["unidades"],
            "ingreso_generado": p_sales["ingreso"],
            "utilidad_generada": p_sales["utilidad"]
        })

    # CLASIFICACIÓN ABC (Dos criterios seleccionables según requerimiento)
    conteo_a = 0
    conteo_b = 0
    conteo_c = 0
    conteo_sin_ventas = 0

    if criterio_abc == 'consumo':
        # Criterio: Ventas / Demanda del período
        prods_evaluados.sort(key=lambda x: (x["ingreso_generado"], x["unidades_vendidas"]), reverse=True)
        total_ingresos = sum(p["ingreso_generado"] for p in prods_evaluados)
        acum_ing = 0.0

        for p in prods_evaluados:
            if p["unidades_vendidas"] > 0 and total_ingresos > 0:
                acum_ing += p["ingreso_generado"]
                pct_acum = (acum_ing / total_ingresos * 100)
                if pct_acum <= 75.0 or conteo_a < 3:
                    p["clase_abc"] = "A"
                    p["clase_nombre"] = "Alta Demanda (Clase A)"
                    conteo_a += 1
                elif pct_acum <= 95.0 or conteo_b < 5:
                    p["clase_abc"] = "B"
                    p["clase_nombre"] = "Demanda Media (Clase B)"
                    conteo_b += 1
                else:
                    p["clase_abc"] = "C"
                    p["clase_nombre"] = "Demanda Baja (Clase C)"
                    conteo_c += 1
            else:
                p["clase_abc"] = "Sin Rotación"
                p["clase_nombre"] = "Sin Ventas en Período"
                conteo_sin_ventas += 1
    else:
        # Criterio: Inversión de Inventario (Capital en bodega: stock * costo)
        # Funciona con rigor matemático SIEMPRE, incluso sin ventas
        prods_evaluados.sort(key=lambda x: x["valor_inmovilizado"], reverse=True)
        total_inversion = sum(p["valor_inmovilizado"] for p in prods_evaluados)
        acum_inv = 0.0

        for p in prods_evaluados:
            if total_inversion > 0 and p["valor_inmovilizado"] > 0:
                acum_inv += p["valor_inmovilizado"]
                pct_acum = (acum_inv / total_inversion * 100)
                if pct_acum <= 75.0 or conteo_a < 5:
                    p["clase_abc"] = "A"
                    p["clase_nombre"] = "Alta Inversión (Clase A - ~75% Capital)"
                    conteo_a += 1
                elif pct_acum <= 95.0 or conteo_b < 10:
                    p["clase_abc"] = "B"
                    p["clase_nombre"] = "Inversión Media (Clase B - ~20% Capital)"
                    conteo_b += 1
                else:
                    p["clase_abc"] = "C"
                    p["clase_nombre"] = "Inversión Baja (Clase C - ~5% Capital)"
                    conteo_c += 1
            else:
                p["clase_abc"] = "C"
                p["clase_nombre"] = "Sin Existencias Físicas"
                conteo_c += 1

    # 11. ALERTA UNIVERSAL DE STOCK MÍNIMO (Audita TODOS los 235 repuestos sin importar clase)
    alertas_stock_minimo = []
    for p in prods_evaluados:
        if p["stock"] <= p["min_stock"]:
            if p["stock"] == 0:
                nivel = "Agotado"
                badge_color = "#dc2626"
            elif p["stock"] <= (p["min_stock"] / 2):
                nivel = "Crítico"
                badge_color = "#ea580c"
            else:
                nivel = "Bajo Mínimo"
                badge_color = "#d97706"

            alertas_stock_minimo.append({
                "id": p["id"],
                "codigo": p["codigo"],
                "nombre": p["nombre"],
                "categoria": p["categoria"],
                "stock": p["stock"],
                "min_stock": p["min_stock"],
                "costo": p["costo"],
                "precio": p["precio"],
                "nivel": nivel,
                "color": badge_color,
                "clase_abc": p["clase_abc"]
            })

    # Ordenar alertas de stock: primero agotados, luego más críticos
    alertas_stock_minimo.sort(key=lambda x: (x["stock"], x["min_stock"]))

    # 12. Ranking por Unidades Vendidas
    top_por_unidades = sorted([p for p in prods_evaluados if p["unidades_vendidas"] > 0], 
                              key=lambda x: x["unidades_vendidas"], reverse=True)[:15]

    # 13. Repuestos Sin Movimiento (0 ventas en el período)
    repuestos_sin_movimiento = [p for p in prods_evaluados if p["unidades_vendidas"] == 0]

    # 14. Devoluciones
    try:
        cursor.execute("""
            SELECT COUNT(DISTINCT dv.id) as ops,
                   ISNULL(SUM(dv.total_devuelto), 0) as monto,
                   ISNULL(SUM(dd.cantidad), 0) as unids
            FROM devoluciones_ventas dv
            LEFT JOIN detalle_devoluciones dd ON dv.id = dd.devolucion_id
        """)
        d_row = cursor.fetchone()
        devoluciones_resumen = {
            "operaciones": int(d_row[0]) if d_row and d_row[0] else 0,
            "monto": float(d_row[1]) if d_row and d_row[1] else 0.0,
            "unidades": int(d_row[2]) if d_row and d_row[2] else 0
        }
    except Exception:
        devoluciones_resumen = {"operaciones": 0, "monto": 0.0, "unidades": 0}

    # Períodos disponibles en la BD
    cursor.execute("""
        SELECT DISTINCT YEAR(fecha_venta) AS anio, MONTH(fecha_venta) AS mes
        FROM ventas
        WHERE estado = 'Completada'
        ORDER BY anio DESC, mes DESC
    """)
    periodos_db = [{"anio": int(r.anio), "mes": int(r.mes), "nombre_mes": MESES_NOMBRES[int(r.mes)]} for r in cursor.fetchall()]

    return {
        "periodo": {
            "texto": filtro["texto"],
            "rango": filtro.get("rango"),
            "mes": filtro.get("mes"),
            "anio": filtro.get("anio"),
            "fecha_inicio": filtro.get("fecha_inicio"),
            "fecha_fin": filtro.get("fecha_fin")
        },
        "criterio_abc": criterio_abc,
        "kpis": {
            "ventas_totales_monto": ventas_monto,
            "ventas_totales_conteo": ventas_conteo,
            "ticket_promedio": ticket_promedio,
            "costo_ventas_monto": costo_ventas,
            "utilidad_bruta": utilidad_bruta,
            "margen_bruto_porcentaje": margen_bruto_pct,
            "compras_totales_monto": compras_monto,
            "compras_totales_conteo": compras_conteo,
            "unidades_vendidas_total": unidades_vendidas,
            "rotacion_monetaria_costo": rotacion_monetaria,
            "dias_inventario": dias_inventario,
            "rotacion_unidades_fisicas": rotacion_unidades,
            "valor_inventario_costo": valor_inventario_costo,
            "valor_inventario_venta": valor_inventario_venta,
            "stock_total_actual": stock_total_actual
        },
        "medidas_estadisticas": medidas_estadisticas,
        "tendencia_lista": tendencia_lista,
        "desglose_mensual_anio": desglose_mensual_anio,
        "categorias_analisis": categorias_analisis,
        "metodos_pago": metodos_pago,
        "rotacion_abc": {
            "criterio": criterio_abc,
            "conteo_clase_a": conteo_a,
            "conteo_clase_b": conteo_b,
            "conteo_clase_c": conteo_c,
            "conteo_sin_ventas": conteo_sin_ventas,
            "total_productos": len(prods_evaluados),
            "productos": prods_evaluados
        },
        "ranking_unidades": top_por_unidades,
        "repuestos_sin_movimiento_conteo": len(repuestos_sin_movimiento),
        "alertas_stock_minimo": alertas_stock_minimo,
        "devoluciones_resumen": devoluciones_resumen,
        "periodos_disponibles": periodos_db
    }

def comparar_dos_periodos(cursor, filtro_a, filtro_b, criterio_abc='inversion'):
    """
    Ejecuta el análisis de dos períodos y calcula las variaciones absolutas y porcentuales.
    """
    data_a = procesar_reporte_completo(cursor, filtro_a, criterio_abc)
    data_b = procesar_reporte_completo(cursor, filtro_b, criterio_abc)

    ka = data_a["kpis"]
    kb = data_b["kpis"]

    def calc_variacion(val_b, val_a):
        diff = round(val_b - val_a, 2)
        pct = round((diff / val_a * 100), 2) if val_a > 0 else (100.0 if val_b > 0 else 0.0)
        return {"diff": diff, "pct": pct}

    variaciones = {
        "ventas": calc_variacion(kb["ventas_totales_monto"], ka["ventas_totales_monto"]),
        "costo": calc_variacion(kb["costo_ventas_monto"], ka["costo_ventas_monto"]),
        "utilidad": calc_variacion(kb["utilidad_bruta"], ka["utilidad_bruta"]),
        "margen_pct": round(kb["margen_bruto_porcentaje"] - ka["margen_bruto_porcentaje"], 2),
        "unidades": calc_variacion(kb["unidades_vendidas_total"], ka["unidades_vendidas_total"]),
        "transacciones": calc_variacion(kb["ventas_totales_conteo"], ka["ventas_totales_conteo"]),
        "ticket": calc_variacion(kb["ticket_promedio"], ka["ticket_promedio"])
    }

    return {
        "periodo_a": data_a,
        "periodo_b": data_b,
        "variaciones": variaciones
    }

def generar_excel_informe_workbook(datos_reporte):
    """
    Genera un archivo Excel (.xlsx) real con estilo corporativo y pestañas estructuradas.
    Retorna un objeto BytesIO listo para descargar.
    """
    wb = openpyxl.Workbook()
    # Eliminar hoja por defecto
    wb.remove(wb.active)

    # Estilos Corporativos (Dorado/Naranja Jehová Jireh)
    font_titulo = Font(name='Segoe UI', size=14, bold=True, color='1E293B')
    font_subtitulo = Font(name='Segoe UI', size=10, italic=True, color='64748B')
    font_header = Font(name='Segoe UI', size=10, bold=True, color='FFFFFF')
    fill_header = PatternFill(start_color='1E293B', end_color='1E293B', fill_type='solid') # Azul pizarra
    fill_gold = PatternFill(start_color='F59E0B', end_color='F59E0B', fill_type='solid')   # Dorado/Naranja
    fill_alt = PatternFill(start_color='F8FAFC', end_color='F8FAFC', fill_type='solid')    # Gris muy claro
    border_thin = Border(left=Side(style='thin', color='E2E8F0'),
                         right=Side(style='thin', color='E2E8F0'),
                         top=Side(style='thin', color='E2E8F0'),
                         bottom=Side(style='thin', color='E2E8F0'))

    k = datos_reporte.get("kpis", {})
    p_text = datos_reporte.get("periodo", {}).get("texto", "Período")

    # =========================================================================
    # HOJA 1: RESUMEN EJECUTIVO Y KPIS
    # =========================================================================
    ws1 = wb.create_sheet(title="Resumen Ejecutivo")
    ws1.views.sheetView[0].showGridLines = True

    ws1.append(["JEHOVÁ JIREH MOTO REPUESTOS - INFORME EJECUTIVO"])
    ws1["A1"].font = font_titulo
    ws1.append([f"Período Evaluado: {p_text} | Generado por Sistema de Gestión"])
    ws1["A2"].font = font_subtitulo
    ws1.append([])

    ws1.append(["INDICADOR FINANCIERO / COMERCIAL", "VALOR", "NOTAS TÉCNICAS"])
    for col_idx in range(1, 4):
        c = ws1.cell(row=4, column=col_idx)
        c.font = font_header
        c.fill = fill_header
        c.alignment = Alignment(horizontal="center" if col_idx > 1 else "left")

    kpis_filas = [
        ("Ventas Netas Totales", f"C$ {k.get('ventas_totales_monto', 0):,.2f}", "Ingresos brutos por facturación comercial"),
        ("Costo de Ventas (COGS)", f"C$ {k.get('costo_ventas_monto', 0):,.2f}", "Costo histórico real de repuestos vendidos"),
        ("Utilidad Bruta Monetaria", f"C$ {k.get('utilidad_bruta', 0):,.2f}", "Ventas Netas menos Costo de Ventas"),
        ("Margen Bruto Porcentual", f"{k.get('margen_bruto_porcentaje', 0):.2f}%", "Margen comercial de rentabilidad bruta"),
        ("Unidades de Repuestos Vendidas", f"{k.get('unidades_vendidas_total', 0):,}", "Unidades físicas despachadas"),
        ("Comprobantes Emitidos (Transacciones)", f"{k.get('ventas_totales_conteo', 0):,}", "Cantidad de ventas completadas"),
        ("Ticket Promedio por Venta", f"C$ {k.get('ticket_promedio', 0):,.2f}", "Ventas totales entre transacciones"),
        ("Rotación Monetaria del Inventario", f"{k.get('rotacion_monetaria_costo', 0):.4f}x", "Costo de Ventas / Inventario al Costo"),
        ("Días de Inventario Promedio", f"{k.get('dias_inventario', 0):.1f} días", "Plazo estimado de rotación completa"),
        ("Rotación Física en Unidades", f"{k.get('rotacion_unidades_fisicas', 0):.4f}x", "Unidades Vendidas / Stock Físico Actual"),
        ("Valor Actual del Inventario a Costo", f"C$ {k.get('valor_inventario_costo', 0):,.2f}", "Capital inmovilizado en bodega"),
        ("Valor Actual del Inventario a Venta", f"C$ {k.get('valor_inventario_venta', 0):,.2f}", "Precio catálogo total"),
        ("Stock Físico Global en Bodega", f"{k.get('stock_total_actual', 0):,} repuestos", "Unidades en almacén activo")
    ]

    r_idx = 5
    for nombre, val, nota in kpis_filas:
        ws1.append([nombre, val, nota])
        for c_idx in range(1, 4):
            c = ws1.cell(row=r_idx, column=c_idx)
            c.border = border_thin
            if r_idx % 2 == 0:
                c.fill = fill_alt
            if c_idx == 2:
                c.alignment = Alignment(horizontal="right")
        r_idx += 1

    # Medidas Estadísticas Descriptivas en Hoja 1
    m = datos_reporte.get("medidas_estadisticas", {})
    ws1.append([])
    ws1.append(["MEDIDAS ESTADÍSTICAS DESCRIPTIVAS DE LAS VENTAS", "VALOR", "INTERPRETACIÓN"])
    r_stat_hdr = ws1.max_row
    for c_idx in range(1, 4):
        c = ws1.cell(row=r_stat_hdr, column=c_idx)
        c.font = font_header
        c.fill = fill_gold
        c.alignment = Alignment(horizontal="center" if c_idx > 1 else "left")

    stats_filas = [
        ("Muestra de Transacciones (N)", f"{m.get('n', 0)}", "Comprobantes analizados"),
        ("Media Aritmética (Ticket Promedio)", f"C$ {m.get('media', 0):,.2f}", "Promedio por transacción"),
        ("Mediana", f"C$ {m.get('mediana', 0):,.2f}", "Punto medio de la serie de ventas"),
        ("Venta Máxima", f"C$ {m.get('maximo', 0):,.2f}", "Mayor importe registrado en el período"),
        ("Venta Mínima", f"C$ {m.get('minimo', 0):,.2f}", "Menor importe registrado en el período"),
        ("Rango Estadístico", f"C$ {m.get('rango', 0):,.2f}", "Amplitud (Máximo - Mínimo)"),
        ("Varianza Muestral (s²)", f"{m.get('varianza', 0):,.2f}", "Dispersión cuadrática de los montos"),
        ("Desviación Estándar (s)", f"C$ {m.get('desviacion_estandar', 0):,.2f}", "Dispersión promedio respecto a la media"),
        ("Coeficiente de Variación (CV)", f"{m.get('coeficiente_variacion', 0):.2f}%", m.get('interpretacion', ''))
    ]

    for nombre, val, nota in stats_filas:
        ws1.append([nombre, val, nota])
        curr_r = ws1.max_row
        for c_idx in range(1, 4):
            c = ws1.cell(row=curr_r, column=c_idx)
            c.border = border_thin
            if c_idx == 2:
                c.alignment = Alignment(horizontal="right")

    # =========================================================================
    # HOJA 2: RENDIMIENTO POR CATEGORÍAS
    # =========================================================================
    ws2 = wb.create_sheet(title="Categorías")
    ws2.views.sheetView[0].showGridLines = True
    ws2.append(["RENDIMIENTO COMERCIAL POR CATEGORÍA DE REPUESTOS"])
    ws2["A1"].font = font_titulo
    ws2.append([f"Período: {p_text}"])
    ws2.append([])

    headers_cat = ["Categoría de Repuestos", "Unidades Vendidas", "Ventas Totales (C$)", "Costo de Ventas (C$)", "Utilidad Bruta (C$)", "Margen Bruto (%)", "Participación (%)"]
    ws2.append(headers_cat)
    for c_idx in range(1, len(headers_cat) + 1):
        c = ws2.cell(row=4, column=c_idx)
        c.font = font_header
        c.fill = fill_header
        c.alignment = Alignment(horizontal="center")

    cats = datos_reporte.get("categorias_analisis", [])
    r_cat = 5
    for item in cats:
        ws2.append([
            item["categoria"],
            item["unidades"],
            item["total_ventas"],
            item["costo_ventas"],
            item["margen"],
            f"{item['margen_porcentaje']:.2f}%",
            f"{item['participacion_porcentaje']:.2f}%"
        ])
        for c_idx in range(1, len(headers_cat) + 1):
            c = ws2.cell(row=r_cat, column=c_idx)
            c.border = border_thin
            if c_idx in [3, 4, 5]:
                c.number_format = '"C$" #,##0.00'
            elif c_idx == 2:
                c.number_format = '#,##0'
        r_cat += 1

    # =========================================================================
    # HOJA 3: CLASIFICACIÓN ABC DE REPUESTOS
    # =========================================================================
    ws3 = wb.create_sheet(title="Clasificación ABC")
    ws3.views.sheetView[0].showGridLines = True
    crit = datos_reporte.get("criterio_abc", "inversion")
    crit_nombre = "Inversión de Inventario (Capital en Bodega)" if crit == 'inversion' else "Valor de Consumo (Ventas del Período)"
    ws3.append(["CLASIFICACIÓN ABC DE REPUESTOS DE MOTOCICLETAS"])
    ws3["A1"].font = font_titulo
    ws3.append([f"Criterio Activo: {crit_nombre} | Período: {p_text}"])
    ws3.append([])

    headers_abc = ["Clase ABC", "Código SKU", "Repuesto", "Categoría", "Stock Físico", "Costo Unid. (C$)", "Capital en Bodega (C$)", "Unid. Vendidas", "Ingresos Ventas (C$)"]
    ws3.append(headers_abc)
    for c_idx in range(1, len(headers_abc) + 1):
        c = ws3.cell(row=4, column=c_idx)
        c.font = font_header
        c.fill = fill_header
        c.alignment = Alignment(horizontal="center")

    prods_abc = datos_reporte.get("rotacion_abc", {}).get("productos", [])
    r_abc = 5
    for p in prods_abc:
        ws3.append([
            p.get("clase_abc", "C"),
            p.get("codigo", ""),
            p.get("nombre", ""),
            p.get("categoria", ""),
            p.get("stock", 0),
            p.get("costo", 0.0),
            p.get("valor_inmovilizado", 0.0),
            p.get("unidades_vendidas", 0),
            p.get("ingreso_generado", 0.0)
        ])
        for c_idx in range(1, len(headers_abc) + 1):
            c = ws3.cell(row=r_abc, column=c_idx)
            c.border = border_thin
            if c_idx in [6, 7, 9]:
                c.number_format = '"C$" #,##0.00'
            elif c_idx in [5, 8]:
                c.number_format = '#,##0'
        r_abc += 1

    # =========================================================================
    # HOJA 4: ALERTAS DE STOCK MÍNIMO UNIVERSALES
    # =========================================================================
    ws4 = wb.create_sheet(title="Alertas Stock Mínimo")
    ws4.views.sheetView[0].showGridLines = True
    ws4.append(["AUDITORÍA INTEGRAL DE EXISTENCIAS BAJO STOCK MÍNIMO"])
    ws4["A1"].font = font_titulo
    ws4.append([f"Total Repuestos con Alerta: {len(datos_reporte.get('alertas_stock_minimo', []))}"])
    ws4.append([])

    headers_alt = ["Nivel de Alerta", "Código SKU", "Repuesto", "Categoría", "Stock Actual", "Stock Mínimo", "Déficit Unidades", "Costo Reposición (C$)"]
    ws4.append(headers_alt)
    for c_idx in range(1, len(headers_alt) + 1):
        c = ws4.cell(row=4, column=c_idx)
        c.font = font_header
        c.fill = fill_header
        c.alignment = Alignment(horizontal="center")

    alt_prods = datos_reporte.get("alertas_stock_minimo", [])
    r_alt = 5
    for a in alt_prods:
        deficit = max(0, a["min_stock"] - a["stock"])
        costo_rep = round(deficit * a["costo"], 2)
        ws4.append([
            a.get("nivel", "Bajo Mínimo"),
            a.get("codigo", ""),
            a.get("nombre", ""),
            a.get("categoria", ""),
            a.get("stock", 0),
            a.get("min_stock", 0),
            deficit,
            costo_rep
        ])
        for c_idx in range(1, len(headers_alt) + 1):
            c = ws4.cell(row=r_alt, column=c_idx)
            c.border = border_thin
            if c_idx == 8:
                c.number_format = '"C$" #,##0.00'
            elif c_idx in [5, 6, 7]:
                c.number_format = '#,##0'
        r_alt += 1

    # Ajuste automático del ancho de columnas en todas las hojas
    for ws in wb.worksheets:
        for col in ws.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if len(val_str) > max_len:
                    max_len = len(val_str)
            ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return output
