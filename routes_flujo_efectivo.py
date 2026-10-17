# ==============================================================================
# RUTAS Y SERVICIOS DEL MÓDULO DE FLUJO DE EFECTIVO Y CONCILIACIÓN BANCARIA
# Marco Normativo: NIIF para PYMES Sección 7 / NIC 7 (RF96 - RF102, RF46)
# Sistema Jehová Jireh Moto Repuestos
# ==============================================================================

import os
from datetime import datetime
from functools import wraps
from flask import Blueprint, jsonify, request, session

def register_flujo_efectivo_routes(app):
    get_db_connection = app.config.get('GET_DB_CONNECTION')
    if not get_db_connection:
        from app import get_db_connection

    def login_required_api(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session:
                return jsonify({"error": "Sesión no iniciada"}), 401
            return f(*args, **kwargs)
        return decorated

    def finanzas_required_api(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if 'user' not in session:
                return jsonify({"error": "Sesión no iniciada"}), 401
            rol = session['user'].get('rol')
            if rol not in ['Administrador', 'Gerente Administrativo y Financiero', 'Contador']:
                return jsonify({"error": "Acceso reservado a Administrador, Gerente Financiero y Contador."}), 403
            return f(*args, **kwargs)
        return decorated

    # --------------------------------------------------------------------------
    # 1. GENERACIÓN DEL ESTADO DE FLUJO DE EFECTIVO (MÉTODO DIRECTO E INDIRECTO)
    # --------------------------------------------------------------------------
    @app.route('/api/finanzas/flujo_efectivo', methods=['GET'])
    @finanzas_required_api
    def api_flujo_efectivo():
        try:
            start_date = request.args.get('start', '').strip() or None
            end_date = request.args.get('end', '').strip() or None
            metodo = request.args.get('metodo', 'Directo').capitalize()
            if metodo not in ['Directo', 'Indirecto']:
                metodo = 'Directo'

            conn = get_db_connection()
            cursor = conn.cursor()

            # Where clauses para asientos
            where_a = ""
            params_a = []
            if start_date and end_date:
                where_a = "AND CAST(a.fecha AS DATE) >= ? AND CAST(a.fecha AS DATE) <= ?"
                params_a.extend([start_date, end_date])
            elif start_date:
                where_a = "AND CAST(a.fecha AS DATE) >= ?"
                params_a.append(start_date)
            elif end_date:
                where_a = "AND CAST(a.fecha AS DATE) <= ?"
                params_a.append(end_date)

            # A. Saldo Inicial de Efectivo (Caja + Bancos antes de start_date)
            saldo_inicial = 0.0
            if start_date:
                cursor.execute("""
                    SELECT SUM(m.debe) - SUM(m.haber) AS saldo_ini
                    FROM cuentas_contables c
                    INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
                    INNER JOIN asientos_contables a ON a.id = m.asiento_id
                    WHERE c.es_efectivo_equivalente = 1 AND CAST(a.fecha AS DATE) < ?
                """, (start_date,))
                row_ini = cursor.fetchone()
                saldo_inicial = float(row_ini[0] or 0.0) if row_ini else 0.0

            # B. Saldo Final Real en Balance General (Caja + Bancos hasta end_date)
            where_bg = ""
            params_bg = []
            if end_date:
                where_bg = "AND CAST(a.fecha AS DATE) <= ?"
                params_bg.append(end_date)

            cursor.execute(f"""
                SELECT c.codigo, c.nombre, SUM(m.debe) - SUM(m.haber) AS saldo
                FROM cuentas_contables c
                INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
                INNER JOIN asientos_contables a ON a.id = m.asiento_id
                WHERE c.es_efectivo_equivalente = 1 {where_bg}
                GROUP BY c.codigo, c.nombre
                ORDER BY c.codigo
            """, tuple(params_bg))
            cuentas_efectivo = cursor.fetchall()
            desglose_efectivo = []
            saldo_final_balance = 0.0
            for ce in cuentas_efectivo:
                s = float(ce[2] or 0.0)
                desglose_efectivo.append({"codigo": ce[0], "nombre": ce[1], "saldo": s})
                saldo_final_balance += s

            # C. Cálculo según Método
            if metodo == 'Directo':
                # Analizar asientos con transacciones de efectivo y sus contrapartidas
                cursor.execute(f"""
                    SELECT a.id AS asiento_id, a.fecha, a.concepto,
                           c.codigo, c.nombre, c.clasificacion, c.flujo_categoria,
                           m.debe, m.haber, c.es_efectivo_equivalente
                    FROM asientos_contables a
                    INNER JOIN movimientos_contables m ON a.id = m.asiento_id
                    INNER JOIN cuentas_contables c ON m.cuenta_id = c.id
                    WHERE a.id IN (
                        SELECT DISTINCT m2.asiento_id 
                        FROM movimientos_contables m2
                        INNER JOIN cuentas_contables c2 ON m2.cuenta_id = c2.id
                        WHERE c2.es_efectivo_equivalente = 1
                    ) {where_a}
                    ORDER BY a.fecha, a.id
                """, tuple(params_a))
                filas_asientos = cursor.fetchall()

                asientos_dict = {}
                for f in filas_asientos:
                    aid = f[0]
                    if aid not in asientos_dict:
                        asientos_dict[aid] = {"movimientos": []}
                    asientos_dict[aid]["movimientos"].append({
                        "codigo": f[3],
                        "nombre": f[4],
                        "clasificacion": f[5],
                        "flujo_categoria": f[6] or 'Operacion',
                        "debe": float(f[7] or 0),
                        "haber": float(f[8] or 0),
                        "es_efectivo": bool(f[9])
                    })

                flujo_operacion_items = {}
                flujo_inversion_items = {}
                flujo_financiamiento_items = {}

                for aid, a_data in asientos_dict.items():
                    contra_movs = [m for m in a_data["movimientos"] if not m["es_efectivo"]]
                    if not contra_movs:
                        continue # Transferencia interna entre Caja y Bancos

                    for cm in contra_movs:
                        cat = cm["flujo_categoria"]
                        efecto = cm["haber"] - cm["debe"]
                        nombre = cm["nombre"]

                        # Normalización contable amigable para el usuario
                        if cm["clasificacion"] == 'Ingresos':
                            concepto = f"Cobros por {nombre.lower()}"
                        elif cm["clasificacion"] == 'Costo':
                            concepto = f"Pagos por {nombre.lower()}"
                        elif cm["clasificacion"] == 'Gasto':
                            concepto = f"Pagos operativos: {nombre.lower()}"
                        elif 'Activo no corriente' in cm["clasificacion"]:
                            concepto = f"Adquisición / venta de {nombre.lower()}"
                        elif 'Patrimonio' in cm["clasificacion"]:
                            concepto = f"Movimientos de patrimonio: {nombre.lower()}"
                        else:
                            concepto = f"Operaciones con {nombre.lower()}"

                        if cat == 'Inversion':
                            flujo_inversion_items[concepto] = flujo_inversion_items.get(concepto, 0.0) + efecto
                        elif cat == 'Financiamiento':
                            flujo_financiamiento_items[concepto] = flujo_financiamiento_items.get(concepto, 0.0) + efecto
                        else:
                            flujo_operacion_items[concepto] = flujo_operacion_items.get(concepto, 0.0) + efecto

                operacion_list = [{"concepto": k, "importe": round(v, 2), "tipo": "Entrada" if v >= 0 else "Salida"} 
                                  for k, v in flujo_operacion_items.items() if abs(v) > 0.001]
                inversion_list = [{"concepto": k, "importe": round(v, 2), "tipo": "Entrada" if v >= 0 else "Salida"} 
                                  for k, v in flujo_inversion_items.items() if abs(v) > 0.001]
                financiamiento_list = [{"concepto": k, "importe": round(v, 2), "tipo": "Entrada" if v >= 0 else "Salida"} 
                                       for k, v in flujo_financiamiento_items.items() if abs(v) > 0.001]

                flujo_neto_operacion = sum(i["importe"] for i in operacion_list)
                flujo_neto_inversion = sum(i["importe"] for i in inversion_list)
                flujo_neto_financiamiento = sum(i["importe"] for i in financiamiento_list)

                indirecto_data = None

            else:
                # MÉTODO INDIRECTO (RF100, RF101)
                # 1. Utilidad Neta del período
                cursor.execute(f"""
                    SELECT c.clasificacion, c.naturaleza, SUM(m.debe) AS d, SUM(m.haber) AS h
                    FROM cuentas_contables c
                    INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
                    INNER JOIN asientos_contables a ON a.id = m.asiento_id
                    WHERE c.clasificacion IN ('Ingresos', 'Costo', 'Gasto') {where_a}
                    GROUP BY c.clasificacion, c.naturaleza
                """, tuple(params_a))
                filas_er = cursor.fetchall()
                utilidad_neta = 0.0
                for f in filas_er:
                    saldo = (float(f[3])-float(f[2])) if f[1] == 'Acreedora' else (float(f[2])-float(f[3]))
                    if f[0] == 'Ingresos': utilidad_neta += saldo
                    else: utilidad_neta -= saldo

                # 2. Ajustes por partidas sin movimiento de efectivo (Depreciación, etc.)
                cursor.execute(f"""
                    SELECT c.codigo, c.nombre, SUM(m.debe) - SUM(m.haber) AS total
                    FROM cuentas_contables c
                    INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
                    INNER JOIN asientos_contables a ON a.id = m.asiento_id
                    WHERE c.codigo = '6.1.09' {where_a}
                    GROUP BY c.codigo, c.nombre
                """, tuple(params_a))
                dep_row = cursor.fetchone()
                depreciacion = float(dep_row[2] or 0.0) if dep_row else 0.0

                ajustes_no_monetarios = []
                if depreciacion > 0.001:
                    ajustes_no_monetarios.append({
                        "concepto": "Depreciación del ejercicio (gasto no monetario)",
                        "importe": round(depreciacion, 2),
                        "efecto": "Suma_a_Utilidad"
                    })

                # 3. Cambios en Capital de Trabajo
                cuentas_wk = [
                    ('1.1.03', 'Clientes', 'Activo'),
                    ('1.1.04', 'Inventario de repuestos y accesorios', 'Activo'),
                    ('1.1.05', 'IVA acreditable', 'Activo'),
                    ('2.1.01', 'Proveedores', 'Pasivo'),
                    ('2.1.03', 'IVA por pagar', 'Pasivo'),
                    ('2.1.04', 'Sueldos y salarios por pagar', 'Pasivo'),
                    ('2.1.05', 'Servicios básicos por pagar', 'Pasivo'),
                    ('2.1.06', 'Retenciones INSS por pagar', 'Pasivo'),
                    ('2.1.07', 'Retenciones IR por pagar', 'Pasivo'),
                    ('2.1.08', 'Provisiones sociales por pagar', 'Pasivo')
                ]
                cambios_wk = []
                total_cambios_wk = 0.0
                for cod, nombre, tipo in cuentas_wk:
                    s_ini = 0.0
                    if start_date:
                        cursor.execute("""
                            SELECT SUM(m.debe) AS d, SUM(m.haber) AS h
                            FROM cuentas_contables c
                            INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
                            INNER JOIN asientos_contables a ON a.id = m.asiento_id
                            WHERE c.codigo = ? AND CAST(a.fecha AS DATE) < ?
                        """, (cod, start_date))
                        r_i = cursor.fetchone()
                        d_i, h_i = float(r_i[0] or 0), float(r_i[1] or 0)
                        s_ini = (d_i - h_i) if tipo == 'Activo' else (h_i - d_i)

                    cursor.execute(f"""
                        SELECT SUM(m.debe) AS d, SUM(m.haber) AS h
                        FROM cuentas_contables c
                        INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
                        INNER JOIN asientos_contables a ON a.id = m.asiento_id
                        WHERE c.codigo = ? {where_bg}
                    """, (cod, *params_bg))
                    r_f = cursor.fetchone()
                    d_f, h_f = float(r_f[0] or 0), float(r_f[1] or 0)
                    s_fin = (d_f - h_f) if tipo == 'Activo' else (h_f - d_f)

                    var = s_fin - s_ini
                    if abs(var) > 0.001:
                        impacto = -var if tipo == 'Activo' else var
                        cambios_wk.append({
                            "cuenta": nombre,
                            "tipo": tipo,
                            "variacion": round(var, 2),
                            "impacto": round(impacto, 2),
                            "descripcion": f"{'Aumento' if var > 0 else 'Disminución'} en {nombre.lower()}"
                        })
                        total_cambios_wk += impacto

                flujo_neto_operacion = utilidad_neta + depreciacion + total_cambios_wk

                # Inversión
                cursor.execute(f"""
                    SELECT c.codigo, c.nombre, SUM(m.debe) - SUM(m.haber) AS total
                    FROM cuentas_contables c
                    INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
                    INNER JOIN asientos_contables a ON a.id = m.asiento_id
                    WHERE c.flujo_categoria = 'Inversion' AND c.clasificacion NOT LIKE '%contraactivo%' {where_a}
                    GROUP BY c.codigo, c.nombre
                """, tuple(params_a))
                inversion_list = []
                flujo_neto_inversion = 0.0
                for r in cursor.fetchall():
                    val = float(r[2] or 0.0)
                    if abs(val) > 0.001:
                        impacto = -val
                        inversion_list.append({"concepto": f"Adquisición de {r[1].lower()}", "importe": round(impacto, 2), "tipo": "Salida" if impacto < 0 else "Entrada"})
                        flujo_neto_inversion += impacto

                # Financiamiento
                cursor.execute(f"""
                    SELECT c.codigo, c.nombre, SUM(m.haber) - SUM(m.debe) AS total
                    FROM cuentas_contables c
                    INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
                    INNER JOIN asientos_contables a ON a.id = m.asiento_id
                    WHERE c.flujo_categoria = 'Financiamiento' {where_a}
                    GROUP BY c.codigo, c.nombre
                """, tuple(params_a))
                financiamiento_list = []
                flujo_neto_financiamiento = 0.0
                for r in cursor.fetchall():
                    val = float(r[2] or 0.0)
                    if abs(val) > 0.001:
                        financiamiento_list.append({"concepto": f"Aportes / variaciones de {r[1].lower()}", "importe": round(val, 2), "tipo": "Entrada" if val > 0 else "Salida"})
                        flujo_neto_financiamiento += val

                operacion_list = [] # Para el indirecto se detalla con utilidad y variaciones
                indirecto_data = {
                    "utilidad_neta": round(utilidad_neta, 2),
                    "ajustes_no_monetarios": ajustes_no_monetarios,
                    "cambios_capital_trabajo": cambios_wk,
                    "total_ajustes": round(depreciacion + total_cambios_wk, 2)
                }

            # D. Totales y Cuadratura (RF102)
            variacion_neta = flujo_neto_operacion + flujo_neto_inversion + flujo_neto_financiamiento
            saldo_final_calculado = saldo_inicial + variacion_neta
            diferencia_cuadratura = round(saldo_final_calculado - saldo_final_balance, 2)
            esta_cuadrado = abs(diferencia_cuadratura) < 0.01

            conn.close()

            return jsonify({
                "metodo": metodo,
                "periodo": {
                    "start": start_date or "Inicio",
                    "end": end_date or datetime.now().strftime("%Y-%m-%d")
                },
                "saldo_inicial": round(saldo_inicial, 2),
                "actividades_operacion": operacion_list,
                "flujo_neto_operacion": round(flujo_neto_operacion, 2),
                "actividades_inversion": inversion_list,
                "flujo_neto_inversion": round(flujo_neto_inversion, 2),
                "actividades_financiamiento": financiamiento_list,
                "flujo_neto_financiamiento": round(flujo_neto_financiamiento, 2),
                "variacion_neta_efectivo": round(variacion_neta, 2),
                "saldo_final_calculado": round(saldo_final_calculado, 2),
                "saldo_final_balance": round(saldo_final_balance, 2),
                "diferencia_cuadratura": diferencia_cuadratura,
                "esta_cuadrado": esta_cuadrado,
                "desglose_efectivo": desglose_efectivo,
                "indirecto_data": indirecto_data
            })

        except Exception as e:
            return jsonify({"error": f"Error al generar flujo de efectivo: {str(e)}"}), 500

    # --------------------------------------------------------------------------
    # 2. GUARDAR CORTE OFICIAL DEL ESTADO DE FLUJO DE EFECTIVO (RF101)
    # --------------------------------------------------------------------------
    @app.route('/api/finanzas/flujo_efectivo/guardar', methods=['POST'])
    @finanzas_required_api
    def api_flujo_efectivo_guardar():
        try:
            data = request.get_json() or {}
            ejercicio = int(data.get('ejercicio_fiscal', datetime.now().year))
            periodo_tipo = data.get('periodo_tipo', 'Mensual')
            fecha_inicio = data.get('fecha_inicio')
            fecha_fin = data.get('fecha_fin')
            metodo = data.get('metodo', 'Directo')
            saldo_ini = float(data.get('saldo_inicial_efectivo', 0.0))
            flujo_op = float(data.get('flujo_neto_operacion', 0.0))
            flujo_inv = float(data.get('flujo_neto_inversion', 0.0))
            flujo_fin = float(data.get('flujo_neto_financiamiento', 0.0))
            var_neta = float(data.get('variacion_neta_efectivo', 0.0))
            saldo_calc = float(data.get('saldo_final_calculado', 0.0))
            saldo_bg = float(data.get('saldo_final_balance_general', 0.0))
            dif = round(saldo_calc - saldo_bg, 2)
            cuadrado = 1 if abs(dif) < 0.01 else 0
            obs = data.get('observaciones', '')
            detalles = data.get('detalles', [])

            user_id = session['user'].get('id')

            conn = get_db_connection()
            cursor = conn.cursor()

            # Insert cabecera
            cursor.execute("""
                INSERT INTO estados_flujo_efectivo (
                    ejercicio_fiscal, periodo_tipo, fecha_inicio, fecha_fin, metodo,
                    saldo_inicial_efectivo, flujo_neto_operacion, flujo_neto_inversion, flujo_neto_financiamiento,
                    variacion_neta_efectivo, saldo_final_calculado, saldo_final_balance_general,
                    diferencia_cuadratura, esta_cuadrado, estado, observaciones, usuario_elaboro_id
                )
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Borrador', ?, ?)
            """, (
                ejercicio, periodo_tipo, fecha_inicio, fecha_fin, metodo,
                saldo_ini, flujo_op, flujo_inv, flujo_fin,
                var_neta, saldo_calc, saldo_bg,
                dif, cuadrado, obs, user_id
            ))
            flujo_id = cursor.fetchone()[0]

            # Insert detalles
            orden = 1
            for d in detalles:
                cursor.execute("""
                    INSERT INTO estado_flujo_efectivo_detalle (
                        flujo_id, actividad, concepto, tipo_movimiento, importe, orden_presentacion
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    flujo_id, d.get('actividad', 'Operacion'), d.get('concepto', ''),
                    d.get('tipo_movimiento', 'Entrada'), float(d.get('importe', 0.0)), orden
                ))
                orden += 1

            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "message": "Estado de Flujo de Efectivo guardado exitosamente.",
                "flujo_id": flujo_id
            })
        except Exception as e:
            return jsonify({"error": f"Error al guardar estado de flujo: {str(e)}"}), 500

    # --------------------------------------------------------------------------
    # 3. CONCILIACIÓN BANCARIA: DATOS DEL MES Y LIBROS (RF98)
    # --------------------------------------------------------------------------
    @app.route('/api/finanzas/conciliacion/datos', methods=['GET'])
    @finanzas_required_api
    def api_conciliacion_datos():
        try:
            cuenta_id = request.args.get('cuenta_id', type=int)
            anio = request.args.get('anio', default=datetime.now().year, type=int)
            mes = request.args.get('mes', default=datetime.now().month, type=int)

            conn = get_db_connection()
            cursor = conn.cursor()

            # Obtener cuenta bancaria (por defecto 1.1.02 Bancos)
            if not cuenta_id:
                cursor.execute("SELECT id, codigo, nombre FROM cuentas_contables WHERE codigo = '1.1.02'")
                row_c = cursor.fetchone()
                if row_c:
                    cuenta_id = row_c[0]
                    cuenta_info = {"id": row_c[0], "codigo": row_c[1], "nombre": row_c[2]}
                else:
                    cuenta_info = {"id": 0, "codigo": "1.1.02", "nombre": "Bancos"}
            else:
                cursor.execute("SELECT id, codigo, nombre FROM cuentas_contables WHERE id = ?", (cuenta_id,))
                row_c = cursor.fetchone()
                cuenta_info = {"id": row_c[0], "codigo": row_c[1], "nombre": row_c[2]} if row_c else {}

            # Fecha de corte: último día del mes
            import calendar
            _, ultimo_dia = calendar.monthrange(anio, mes)
            fecha_corte = f"{anio:04d}-{mes:02d}-{ultimo_dia:02d}"

            # Saldo según libros a la fecha de corte
            cursor.execute("""
                SELECT SUM(m.debe) AS t_debe, SUM(m.haber) AS t_haber,
                       SUM(m.debe) - SUM(m.haber) AS saldo_libros
                FROM movimientos_contables m
                INNER JOIN asientos_contables a ON a.id = m.asiento_id
                WHERE m.cuenta_id = ? AND CAST(a.fecha AS DATE) <= ?
            """, (cuenta_id, fecha_corte))
            row_s = cursor.fetchone()
            saldo_segun_libros = float(row_s[2] or 0.0) if row_s else 0.0

            # Movimientos contables de bancos en el mes
            cursor.execute("""
                SELECT a.id, a.fecha, a.concepto, m.debe, m.haber, m.id AS movimiento_id
                FROM movimientos_contables m
                INNER JOIN asientos_contables a ON a.id = m.asiento_id
                WHERE m.cuenta_id = ? AND YEAR(a.fecha) = ? AND MONTH(a.fecha) = ?
                ORDER BY a.fecha ASC, a.id ASC
            """, (cuenta_id, anio, mes))
            movs = []
            for r in cursor.fetchall():
                movs.append({
                    "asiento_id": r[0],
                    "fecha": r[1].strftime("%Y-%m-%d") if hasattr(r[1], 'strftime') else str(r[1]),
                    "concepto": r[2],
                    "debe": float(r[3] or 0.0),
                    "haber": float(r[4] or 0.0),
                    "movimiento_id": r[5]
                })

            # Verificar si ya existe conciliación guardada para este mes
            cursor.execute("""
                SELECT id, saldo_segun_libros, saldo_segun_banco, diferencia, estado, observaciones, fecha_corte
                FROM conciliaciones_bancarias
                WHERE cuenta_id = ? AND anio = ? AND mes = ?
            """, (cuenta_id, anio, mes))
            row_conc = cursor.fetchone()
            conciliacion_guardada = None
            partidas = []
            if row_conc:
                cid = row_conc[0]
                conciliacion_guardada = {
                    "id": cid,
                    "saldo_segun_libros": float(row_conc[1] or 0.0),
                    "saldo_segun_banco": float(row_conc[2] or 0.0),
                    "diferencia": float(row_conc[3] or 0.0),
                    "estado": row_conc[4],
                    "observaciones": row_conc[5] or '',
                    "fecha_corte": str(row_conc[6])
                }

                # Cargar partidas pendientes
                cursor.execute("""
                    SELECT id, tipo_partida, fecha, numero_documento_referencia, descripcion, monto, efecto_en_saldo, esta_conciliada
                    FROM conciliacion_partidas_pendientes
                    WHERE conciliacion_id = ?
                    ORDER BY id ASC
                """, (cid,))
                for p in cursor.fetchall():
                    partidas.append({
                        "id": p[0],
                        "tipo_partida": p[1],
                        "fecha": str(p[2]),
                        "numero_documento_referencia": p[3],
                        "descripcion": p[4],
                        "monto": float(p[5] or 0.0),
                        "efecto_en_saldo": p[6],
                        "esta_conciliada": bool(p[7])
                    })

            # Listar todas las cuentas de bancos para el dropdown
            cursor.execute("""
                SELECT id, codigo, nombre FROM cuentas_contables 
                WHERE codigo LIKE '1.1.02%' OR nombre LIKE '%banco%'
                ORDER BY codigo
            """)
            cuentas_bancos = [{"id": r[0], "codigo": r[1], "nombre": r[2]} for r in cursor.fetchall()]

            conn.close()

            return jsonify({
                "cuenta": cuenta_info,
                "cuentas_bancos": cuentas_bancos,
                "anio": anio,
                "mes": mes,
                "fecha_corte": fecha_corte,
                "saldo_segun_libros": round(saldo_segun_libros, 2),
                "movimientos_mes": movs,
                "conciliacion_guardada": conciliacion_guardada,
                "partidas_pendientes": partidas
            })
        except Exception as e:
            return jsonify({"error": f"Error al cargar datos de conciliación: {str(e)}"}), 500

    # --------------------------------------------------------------------------
    # 4. GUARDAR CONCILIACIÓN BANCARIA Y PARTIDAS PENDIENTES (RF98)
    # --------------------------------------------------------------------------
    @app.route('/api/finanzas/conciliacion/guardar', methods=['POST'])
    @finanzas_required_api
    def api_conciliacion_guardar():
        try:
            data = request.get_json() or {}
            cuenta_id = int(data.get('cuenta_id', 2))
            anio = int(data.get('anio', datetime.now().year))
            mes = int(data.get('mes', datetime.now().month))
            fecha_corte = data.get('fecha_corte')
            saldo_libros = float(data.get('saldo_segun_libros', 0.0))
            saldo_banco = float(data.get('saldo_segun_banco', 0.0))
            diferencia = float(data.get('diferencia', 0.0))
            estado = data.get('estado', 'Conciliada')
            observaciones = data.get('observaciones', '')
            partidas = data.get('partidas', [])

            user_id = session['user'].get('id')

            conn = get_db_connection()
            cursor = conn.cursor()

            # Comprobar si ya existe para actualizar o insertar
            cursor.execute("""
                SELECT id FROM conciliaciones_bancarias 
                WHERE cuenta_id = ? AND anio = ? AND mes = ?
            """, (cuenta_id, anio, mes))
            row_exist = cursor.fetchone()

            if row_exist:
                conciliacion_id = row_exist[0]
                cursor.execute("""
                    UPDATE conciliaciones_bancarias
                    SET fecha_corte = ?, saldo_segun_libros = ?, saldo_segun_banco = ?,
                        diferencia = ?, estado = ?, observaciones = ?, usuario_id = ?
                    WHERE id = ?
                """, (fecha_corte, saldo_libros, saldo_banco, diferencia, estado, observaciones, user_id, conciliacion_id))

                # Borrar partidas viejas para reemplazarlas
                cursor.execute("DELETE FROM conciliacion_partidas_pendientes WHERE conciliacion_id = ?", (conciliacion_id,))
            else:
                cursor.execute("""
                    INSERT INTO conciliaciones_bancarias (
                        cuenta_id, anio, mes, fecha_corte, saldo_segun_libros,
                        saldo_segun_banco, diferencia, estado, observaciones, usuario_id
                    )
                    OUTPUT INSERTED.id
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (cuenta_id, anio, mes, fecha_corte, saldo_libros, saldo_banco, diferencia, estado, observaciones, user_id))
                conciliacion_id = cursor.fetchone()[0]

            # Insertar partidas pendientes en tránsito
            for p in partidas:
                cursor.execute("""
                    INSERT INTO conciliacion_partidas_pendientes (
                        conciliacion_id, tipo_partida, fecha, numero_documento_referencia,
                        descripcion, monto, efecto_en_saldo, esta_conciliada
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    conciliacion_id, p.get('tipo_partida', 'Cheque en Transito'),
                    p.get('fecha', fecha_corte), p.get('numero_documento_referencia', 'S/N'),
                    p.get('descripcion', ''), float(p.get('monto', 0.0)),
                    p.get('efecto_en_saldo', 'Resta'), 1 if p.get('esta_conciliada') else 0
                ))

            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "message": f"Conciliación bancaria del período {mes:02d}/{anio} guardada exitosamente.",
                "conciliacion_id": conciliacion_id
            })
        except Exception as e:
            return jsonify({"error": f"Error al guardar conciliación bancaria: {str(e)}"}), 500

    # --------------------------------------------------------------------------
    # 5. HISTORIAL DE CONCILIACIONES BANCARIAS
    # --------------------------------------------------------------------------
    @app.route('/api/finanzas/conciliaciones', methods=['GET'])
    @finanzas_required_api
    def api_conciliaciones_listar():
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT cb.id, cb.anio, cb.mes, cb.fecha_corte, cb.saldo_segun_libros,
                       cb.saldo_segun_banco, cb.diferencia, cb.estado, cb.observaciones,
                       c.codigo AS cuenta_codigo, c.nombre AS cuenta_nombre,
                       u.nombre_completo AS usuario_nombre, cb.created_at
                FROM conciliaciones_bancarias cb
                INNER JOIN cuentas_contables c ON cb.cuenta_id = c.id
                LEFT JOIN usuarios u ON cb.usuario_id = u.id
                ORDER BY cb.anio DESC, cb.mes DESC
            """)
            rows = cursor.fetchall()
            conciliaciones = []
            for r in rows:
                conciliaciones.append({
                    "id": r[0],
                    "anio": r[1],
                    "mes": r[2],
                    "fecha_corte": str(r[3]),
                    "saldo_segun_libros": float(r[4] or 0.0),
                    "saldo_segun_banco": float(r[5] or 0.0),
                    "diferencia": float(r[6] or 0.0),
                    "estado": r[7],
                    "observaciones": r[8] or '',
                    "cuenta": f"{r[9]} - {r[10]}",
                    "usuario": r[11] or 'Sistema',
                    "created_at": str(r[12])
                })
            conn.close()
            return jsonify({"conciliaciones": conciliaciones})
        except Exception as e:
            return jsonify({"error": f"Error al listar conciliaciones: {str(e)}"}), 500

    # --------------------------------------------------------------------------
    # 6. RECLASIFICACIONES Y AUDITORÍA CONTABLE (RF97, RF99)
    # --------------------------------------------------------------------------
    @app.route('/api/finanzas/reclasificaciones', methods=['GET', 'POST'])
    @finanzas_required_api
    def api_reclasificaciones():
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if request.method == 'GET':
                cursor.execute("""
                    SELECT r.id, r.asiento_id, a.fecha, a.concepto,
                           r.origen_modulo, r.actividad_anterior, r.actividad_nueva,
                           r.motivo_reclasificacion, u.nombre_completo AS usuario_nombre, r.created_at
                    FROM flujo_reclasificaciones_auditoria r
                    LEFT JOIN asientos_contables a ON a.id = r.asiento_id
                    LEFT JOIN usuarios u ON u.id = r.usuario_id
                    ORDER BY r.created_at DESC
                """)
                filas = cursor.fetchall()
                reclass_list = []
                for f in filas:
                    reclass_list.append({
                        "id": f[0],
                        "asiento_id": f[1],
                        "asiento_fecha": str(f[2]) if f[2] else 'N/A',
                        "asiento_concepto": f[3] or 'N/A',
                        "origen_modulo": f[4],
                        "actividad_anterior": f[5] or 'Automática',
                        "actividad_nueva": f[6],
                        "motivo": f[7],
                        "usuario": f[8] or 'Auditor',
                        "created_at": str(f[9])
                    })
                return jsonify({"reclasificaciones": reclass_list})

            else:
                data = request.get_json() or {}
                asiento_id = data.get('asiento_id')
                movimiento_id = data.get('movimiento_id')
                origen_modulo = data.get('origen_modulo', 'ASIENTO_MANUAL')
                act_ant = data.get('actividad_anterior', 'Operacion')
                act_nueva = data.get('actividad_nueva', 'Inversion')
                motivo = data.get('motivo_reclasificacion', '').strip()
                user_id = session['user'].get('id')

                if not motivo:
                    return jsonify({"error": "Debe proporcionar el motivo o justificación técnica de la reclasificación."}), 400

                cursor.execute("""
                    INSERT INTO flujo_reclasificaciones_auditoria (
                        asiento_id, movimiento_id, origen_modulo, actividad_anterior,
                        actividad_nueva, motivo_reclasificacion, usuario_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (asiento_id, movimiento_id, origen_modulo, act_ant, act_nueva, motivo, user_id))

                conn.commit()
                return jsonify({"success": True, "message": "Reclasificación contable registrada y auditada."})
        except Exception as e:
            return jsonify({"error": f"Error en reclasificaciones: {str(e)}"}), 500
        finally:
            conn.close()
