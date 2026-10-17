import os
from datetime import datetime, date
from flask import request, jsonify, render_template, session
from functools import wraps
from rrhh_service import ROLES_RRHH, normalizar_parametro, parametros_calculo, validar_parametro

ROLES_ADMIN_GERENCIA = ['Administrador', 'Contador', 'Gerente Administrativo y Financiero', 'Gerente de Operaciones']

def register_corte_v_routes(app):
    from app import execute_query, get_db_connection, login_required, role_required

    @app.before_request
    def proteger_datos_rrhh():
        if request.path.startswith(('/api/rrhh/', '/rrhh/')):
            user = session.get('user')
            if not user:
                return jsonify({'error': 'Inicia sesión para acceder a Recursos Humanos.'}), 401
            if user.get('rol') not in ROLES_RRHH:
                return jsonify({'error': 'No tienes permisos para acceder a Recursos Humanos.'}), 403

    # =========================================================================
    # 1. RECLUTAMIENTO: SOLICITUDES DE EMPLEO (RF95, RF96)
    # =========================================================================
    @app.route('/api/rrhh/solicitudes', methods=['GET', 'POST'])
    @login_required
    def api_solicitudes_empleo():
        if request.method == 'GET':
            query = """
                SELECT id, codigo_solicitud, nombres_apellidos, identificacion, direccion,
                       telefono, email, puesto_solicitado, formacion_academica,
                       experiencia_laboral, referencias_laborales, disponibilidad,
                       ISNULL(salario_pretendido, 0) AS salario_pretendido,
                       estado, ISNULL(observaciones, '') AS observaciones,
                       fecha_registro
                FROM solicitudes_empleo
                ORDER BY id DESC
            """
            rows = execute_query(query, fetchall=True)
            for r in rows:
                r['salario_pretendido'] = float(r['salario_pretendido'])
                r['fecha_registro'] = str(r['fecha_registro'])[:19] if r['fecha_registro'] else ''
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos para registrar solicitudes."}), 403

            data = request.json or {}
            nombres = data.get('nombres_apellidos', '').strip()
            cedula = data.get('identificacion', '').strip()
            telefono = data.get('telefono', '').strip()
            email = data.get('email', '').strip()
            direccion = data.get('direccion', '').strip()
            puesto = data.get('puesto_solicitado', '').strip()
            formacion = data.get('formacion_academica', '').strip()
            experiencia = data.get('experiencia_laboral', '').strip()
            referencias = data.get('referencias_laborales', '').strip()
            disponibilidad = data.get('disponibilidad', 'Inmediata').strip()
            salario = float(data.get('salario_pretendido', 0) or 0)
            obs = data.get('observaciones', '').strip()

            if not nombres or not cedula or not puesto or not telefono:
                return jsonify({"error": "Nombre, cédula, puesto y teléfono son obligatorios."}), 400

            # Generar correlativo
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM solicitudes_empleo")
            next_id = cursor.fetchone()[0]
            codigo = f"SOL-2026-{next_id:03d}"

            cursor.execute("""
                INSERT INTO solicitudes_empleo 
                (codigo_solicitud, nombres_apellidos, identificacion, direccion, telefono, email,
                 puesto_solicitado, formacion_academica, experiencia_laboral, referencias_laborales,
                 disponibilidad, salario_pretendido, estado, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Recibida', ?)
            """, (codigo, nombres, cedula, direccion, telefono, email, puesto, formacion, experiencia, referencias, disponibilidad, salario, obs))
            conn.commit()
            conn.close()

            return jsonify({"success": True, "mensaje": f"Solicitud {codigo} registrada exitosamente."}), 201

    @app.route('/api/rrhh/solicitudes/<int:id>/estado', methods=['PATCH'])
    @login_required
    def api_solicitud_estado(id):
        if session['user']['rol'] not in ROLES_RRHH:
            return jsonify({"error": "No tienes permisos."}), 403

        data = request.json or {}
        nuevo_estado = data.get('estado', 'Recibida')
        obs = data.get('observaciones', '')

        execute_query("""
            UPDATE solicitudes_empleo 
            SET estado = ?, observaciones = CASE WHEN ? <> '' THEN ? ELSE observaciones END
            WHERE id = ?
        """, (nuevo_estado, obs, obs, id), commit=True)
        return jsonify({"success": True, "mensaje": f"Estado actualizado a '{nuevo_estado}'."})

    @app.route('/api/rrhh/solicitudes/<int:id>/contratar', methods=['POST'])
    @login_required
    def api_solicitud_contratar(id):
        """Convierte un aspirante seleccionado en Empleado y genera su Contrato Laboral automáticamente (RF95->RF98)."""
        if session['user']['rol'] not in ROLES_RRHH:
            return jsonify({"error": "No tienes permisos para contratar."}), 403

        data = request.json or {}
        salario_acordado = float(data.get('salario_base', 0) or 0)
        cargo_nombre = data.get('cargo', '').strip()
        tipo_contrato = data.get('tipo_contratacion', 'Tiempo Indeterminado').strip()
        fecha_ingreso = data.get('fecha_ingreso', str(date.today()))

        solicitud = execute_query("SELECT * FROM solicitudes_empleo WHERE id = ?", (id,), fetchone=True)
        if not solicitud:
            return jsonify({"error": "Solicitud no encontrada."}), 404

        salario = salario_acordado if salario_acordado > 0 else float(solicitud.get('salario_pretendido') or 9500.00)
        cargo = cargo_nombre if cargo_nombre else solicitud.get('puesto_solicitado')

        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. Crear registro en empleados
        cursor.execute("""
            INSERT INTO empleados
            (nombre_completo, identificacion, cargo, salario_base, fecha_ingreso, telefono, email,
             direccion, dias_vacaciones_disponibles, activo, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.0, 1, ?)
        """, (
            solicitud['nombres_apellidos'],
            solicitud['identificacion'],
            cargo,
            salario,
            fecha_ingreso,
            solicitud['telefono'],
            solicitud['email'],
            solicitud['direccion'],
            f"Contratado desde Solicitud {solicitud['codigo_solicitud']}"
        ))
        cursor.execute("SELECT @@IDENTITY AS id")
        emp_id = int(cursor.fetchone()[0])

        # 2. Generar contrato laboral formal
        cursor.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM contratos_laborales")
        next_ctr_id = cursor.fetchone()[0]
        num_contrato = f"CTR-2026-{next_ctr_id:03d}"

        cursor.execute("""
            INSERT INTO contratos_laborales
            (numero_contrato, empleado_id, tipo_contratacion, cargo, salario_mensual, fecha_inicio, forma_pago, estado, observaciones)
            VALUES (?, ?, ?, ?, ?, ?, 'Quincenal', 'Vigente', ?)
        """, (num_contrato, emp_id, tipo_contrato, cargo, salario, fecha_ingreso, f"Contrato de ingreso por {solicitud['codigo_solicitud']}"))

        # 3. Marcar solicitud como Seleccionada
        cursor.execute("UPDATE solicitudes_empleo SET estado = 'Seleccionada' WHERE id = ?", (id,))
        conn.commit()
        conn.close()

        return jsonify({
            "success": True, 
            "mensaje": f"¡Empleado #{emp_id} '{solicitud['nombres_apellidos']}' contratado con éxito! Se generó el contrato {num_contrato}."
        })

    # =========================================================================
    # 2. CONTRATOS LABORALES (RF98, RF99, RF100)
    # =========================================================================
    @app.route('/api/rrhh/contratos', methods=['GET', 'POST'])
    @login_required
    def api_contratos_laborales():
        if request.method == 'GET':
            query = """
                SELECT c.id, c.numero_contrato, c.empleado_id, e.nombre_completo AS empleado,
                       e.identificacion AS cedula, c.tipo_contratacion, c.cargo, c.jornada_laboral,
                       c.salario_mensual, c.forma_pago, c.fecha_inicio, c.fecha_fin, c.estado,
                       ISNULL(c.observaciones, '') AS observaciones
                FROM contratos_laborales c
                INNER JOIN empleados e ON c.empleado_id = e.id
                ORDER BY c.id DESC
            """
            rows = execute_query(query, fetchall=True)
            for r in rows:
                r['salario_mensual'] = float(r['salario_mensual'])
                r['fecha_inicio'] = str(r['fecha_inicio'])[:10] if r['fecha_inicio'] else ''
                r['fecha_fin'] = str(r['fecha_fin'])[:10] if r['fecha_fin'] else ''
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            emp_id = int(data.get('empleado_id', 0))
            tipo = data.get('tipo_contratacion', 'Tiempo Indeterminado')
            cargo = data.get('cargo', '').strip()
            salario = float(data.get('salario_mensual', 0))
            f_inicio = data.get('fecha_inicio', str(date.today()))
            f_fin = data.get('fecha_fin') or None
            jornada = data.get('jornada_laboral', 'Diurna Ordinaria (48h)')
            obs = data.get('observaciones', '')

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM contratos_laborales")
            next_id = cursor.fetchone()[0]
            num_contrato = f"CTR-2026-{next_id:03d}"

            cursor.execute("""
                INSERT INTO contratos_laborales
                (numero_contrato, empleado_id, tipo_contratacion, cargo, salario_mensual, fecha_inicio, fecha_fin, jornada_laboral, estado, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Vigente', ?)
            """, (num_contrato, emp_id, tipo, cargo, salario, f_inicio, f_fin, jornada, obs))
            conn.commit()
            conn.close()

            return jsonify({"success": True, "mensaje": f"Contrato {num_contrato} registrado exitosamente."}), 201

    @app.route('/rrhh/contrato/<int:id>/imprimir')
    @login_required
    def imprimir_contrato_laboral(id):
        query = """
            SELECT c.*, e.nombre_completo AS empleado, e.identificacion AS cedula,
                   e.direccion, e.telefono
            FROM contratos_laborales c
            INNER JOIN empleados e ON c.empleado_id = e.id
            WHERE c.id = ?
        """
        row = execute_query(query, (id,), fetchone=True)
        if not row:
            return "Contrato no encontrado", 404

        c = {
            "numero_contrato": row['numero_contrato'],
            "empleado": row['empleado'],
            "cedula": row['cedula'] or '—',
            "direccion": row.get('direccion') or 'Masatepe, Masaya',
            "cargo": row['cargo'],
            "area": 'Ventas y Operaciones',
            "lugar_trabajo": row.get('lugar_trabajo') or 'Masatepe, Masaya - Tienda Central',
            "tipo_contratacion": row['tipo_contratacion'],
            "fecha_inicio": str(row['fecha_inicio'])[:10],
            "fecha_fin": str(row['fecha_fin'])[:10] if row.get('fecha_fin') else None,
            "jornada_laboral": row.get('jornada_laboral') or 'Diurna Ordinaria (48 horas semanales)',
            "salario_mensual": float(row['salario_mensual']),
            "forma_pago": row.get('forma_pago') or 'Quincenal',
            "fecha_actual": datetime.now().strftime("%d de %B de %Y")
        }
        return render_template('contrato.html', c=c)

    # =========================================================================
    # 3. EXPEDIENTE DIGITAL (RF97)
    # =========================================================================
    @app.route('/api/rrhh/expedientes/<int:emp_id>', methods=['GET', 'POST'])
    @login_required
    def api_expediente_empleado(emp_id):
        if request.method == 'GET':
            docs = execute_query("""
                SELECT id, tipo_documento, nombre_archivo, fecha_registro, usuario_responsable, ISNULL(observaciones, '') AS observaciones
                FROM expediente_empleado
                WHERE empleado_id = ?
                ORDER BY id DESC
            """, (emp_id,), fetchall=True)
            for d in docs:
                d['fecha_registro'] = str(d['fecha_registro'])[:19] if d['fecha_registro'] else ''
            return jsonify(docs)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            tipo = data.get('tipo_documento', '').strip()
            archivo = data.get('nombre_archivo', '').strip()
            obs = data.get('observaciones', '').strip()

            if not tipo or not archivo:
                return jsonify({"error": "Tipo de documento y nombre de archivo son obligatorios."}), 400

            usuario = session.get('user', {}).get('username', 'admin')
            execute_query("""
                INSERT INTO expediente_empleado (empleado_id, tipo_documento, nombre_archivo, usuario_responsable, observaciones)
                VALUES (?, ?, ?, ?, ?)
            """, (emp_id, tipo, archivo, usuario, obs), commit=True)

            return jsonify({"success": True, "mensaje": "Documento agregado al expediente digital."}), 201

    @app.route('/api/rrhh/expedientes/doc/<int:doc_id>', methods=['DELETE'])
    @login_required
    def api_expediente_eliminar(doc_id):
        if session['user']['rol'] not in ROLES_RRHH:
            return jsonify({"error": "No tienes permisos."}), 403
        execute_query("DELETE FROM expediente_empleado WHERE id = ?", (doc_id,), commit=True)
        return jsonify({"success": True, "mensaje": "Documento eliminado."})

    # =========================================================================
    # 4. HISTORIAL DE MODIFICACIONES LABORALES (RF101)
    # =========================================================================
    @app.route('/api/rrhh/historial-laboral/<int:emp_id>', methods=['GET', 'POST'])
    @login_required
    def api_historial_laboral(emp_id):
        if request.method == 'GET':
            rows = execute_query("""
                SELECT id, fecha_vigencia, tipo_modificacion, campo_afectado, valor_anterior, valor_nuevo, motivo, usuario_responsable, created_at
                FROM historial_laboral
                WHERE empleado_id = ?
                ORDER BY fecha_vigencia DESC
            """, (emp_id,), fetchall=True)
            for r in rows:
                r['fecha_vigencia'] = str(r['fecha_vigencia'])[:10] if r['fecha_vigencia'] else ''
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            tipo = data.get('tipo_modificacion', 'Aumento Salarial')
            campo = data.get('campo_afectado', 'salario_base')
            v_ant = str(data.get('valor_anterior', ''))
            v_nue = str(data.get('valor_nuevo', ''))
            f_vig = data.get('fecha_vigencia', str(date.today()))
            motivo = data.get('motivo', '').strip()
            usuario = session.get('user', {}).get('username', 'admin')

            execute_query("""
                INSERT INTO historial_laboral
                (empleado_id, fecha_vigencia, tipo_modificacion, campo_afectado, valor_anterior, valor_nuevo, motivo, usuario_responsable)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (emp_id, f_vig, tipo, campo, v_ant, v_nue, motivo, usuario), commit=True)

            return jsonify({"success": True, "mensaje": "Cambio laboral registrado en el historial."}), 201

    # =========================================================================
    # 5. JORNADAS LABORALES (RF102)
    # =========================================================================
    @app.route('/api/rrhh/jornadas', methods=['GET', 'POST'])
    @login_required
    def api_jornadas_laborales():
        if request.method == 'GET':
            rows = execute_query("SELECT * FROM jornadas_laborales WHERE activo = 1 ORDER BY id ASC", fetchall=True)
            for r in rows:
                r['horas_semanales'] = float(r['horas_semanales'])
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            nombre = data.get('nombre', '').strip()
            entrada = data.get('hora_entrada', '08:00')
            salida = data.get('hora_salida', '17:00')
            descanso = int(data.get('minutos_descanso', 60))
            dias_lab = data.get('dias_laborables', 'Lunes a Sábado')
            dia_desc = data.get('dia_descanso', 'Domingo')
            horas_sem = float(data.get('horas_semanales', 48.0))

            execute_query("""
                INSERT INTO jornadas_laborales (nombre, hora_entrada, hora_salida, minutos_descanso, dias_laborables, dia_descanso, horas_semanales)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (nombre, entrada, salida, descanso, dias_lab, dia_desc, horas_sem), commit=True)
            return jsonify({"success": True, "mensaje": "Jornada laboral registrada exitosamente."}), 201

    # =========================================================================
    # 6. ASISTENCIA LABORAL (RF103)
    # =========================================================================
    @app.route('/api/rrhh/asistencia', methods=['GET', 'POST'])
    @login_required
    def api_asistencia_laboral():
        if request.method == 'GET':
            fecha_param = request.args.get('fecha', str(date.today()))
            query = """
                SELECT a.id, a.empleado_id, e.nombre_completo AS empleado, e.cargo,
                       a.fecha, a.hora_entrada, a.hora_salida, a.estado,
                       a.minutos_tardanza, ISNULL(a.observaciones, '') AS observaciones
                FROM asistencia_laboral a
                INNER JOIN empleados e ON a.empleado_id = e.id
                WHERE a.fecha = ?
                ORDER BY a.hora_entrada ASC
            """
            rows = execute_query(query, (fecha_param,), fetchall=True)
            for r in rows:
                r['fecha'] = str(r['fecha'])[:10]
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            emp_id = int(data.get('empleado_id', 0))
            f_asist = data.get('fecha', str(date.today()))
            h_in = data.get('hora_entrada', '08:00')
            h_out = data.get('hora_salida', '17:00')
            estado = data.get('estado', 'Completa')
            tardanza = int(data.get('minutos_tardanza', 0))
            obs = data.get('observaciones', '').strip()

            execute_query("""
                INSERT INTO asistencia_laboral (empleado_id, fecha, hora_entrada, hora_salida, estado, minutos_tardanza, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (emp_id, f_asist, h_in, h_out, estado, tardanza, obs), commit=True)
            return jsonify({"success": True, "mensaje": "Asistencia registrada correctamente."}), 201

    # =========================================================================
    # 7. HORAS EXTRAS (RF104) — Recargo legal 100% (Art. 62 Ley 185)
    # =========================================================================
    @app.route('/api/rrhh/horas-extras', methods=['GET', 'POST'])
    @login_required
    def api_horas_extras():
        if request.method == 'GET':
            query = """
                SELECT h.id, h.empleado_id, e.nombre_completo AS empleado, h.fecha,
                       h.cantidad_horas, h.motivo, h.valor_hora_ordinaria,
                       h.recargo_porcentaje, h.monto_total, h.estado,
                       ISNULL(h.autorizado_por, '') AS autorizado_por
                FROM horas_extras h
                INNER JOIN empleados e ON h.empleado_id = e.id
                ORDER BY h.fecha DESC
            """
            rows = execute_query(query, fetchall=True)
            for r in rows:
                r['cantidad_horas'] = float(r['cantidad_horas'])
                r['valor_hora_ordinaria'] = float(r['valor_hora_ordinaria'])
                r['recargo_porcentaje'] = float(r['recargo_porcentaje'])
                r['monto_total'] = float(r['monto_total'])
                r['fecha'] = str(r['fecha'])[:10]
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            emp_id = int(data.get('empleado_id', 0))
            f_he = data.get('fecha', str(date.today()))
            try:
                from math import isfinite
                cant_horas = float(data.get('cantidad_horas', 0))
                if not isfinite(cant_horas) or cant_horas <= 0:
                    raise ValueError()
            except (TypeError, ValueError):
                return jsonify({'error': 'Las horas deben ser un número positivo.'}), 400
            motivo = data.get('motivo', 'Atención por alta demanda / descarga de mercadería').strip()

            emp = execute_query("SELECT salario_base FROM empleados WHERE id = ?", (emp_id,), fetchone=True)
            if not emp:
                return jsonify({"error": "Empleado no encontrado."}), 404

            salario = float(emp['salario_base'])
            valor_hora = round(salario / 240.0, 2)  # 30 días * 8 horas = 240 horas mensuales
            # Ley 185 Art. 62: Las horas extras se remuneran con un 100% de recargo (doble del valor ordinario)
            parametros = parametros_calculo(execute_query('SELECT * FROM parametros_laborales', fetchall=True))
            recargo = parametros.get('HORAS_EXTRAS_RECARGO', 100)
            monto_total = round(cant_horas * valor_hora * (1 + recargo / 100), 2)
            autorizado = session.get('user', {}).get('username', 'admin')

            execute_query("""
                INSERT INTO horas_extras 
                (empleado_id, fecha, cantidad_horas, motivo, valor_hora_ordinaria, recargo_porcentaje, monto_total, estado, autorizado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'Aprobada', ?)
            """, (emp_id, f_he, cant_horas, motivo, valor_hora, recargo, monto_total, autorizado), commit=True)

            return jsonify({
                "success": True, 
                "mensaje": f"{cant_horas} horas extras registradas y aprobadas (C$ {monto_total:,.2f}, recargo {recargo:g}%)."
            }), 201

    # =========================================================================
    # 8. LIQUIDACIONES LABORALES / FINIQUITO (RF108) (Ley 185)
    # =========================================================================
    @app.route('/api/rrhh/liquidaciones', methods=['GET', 'POST'])
    @login_required
    def api_liquidaciones_laborales():
        if request.method == 'GET':
            query = """
                SELECT l.id, l.codigo, l.empleado_id, e.nombre_completo AS empleado, e.cargo,
                       l.fecha_ingreso, l.fecha_salida, l.motivo_salida, l.salario_base,
                       l.antiguedad_anios, l.antiguedad_meses, l.antiguedad_dias,
                       l.total_percepciones, l.deducciones_totales, l.neto_a_pagar,
                       l.estado, l.fecha_elaboracion
                FROM liquidaciones_laborales l
                INNER JOIN empleados e ON l.empleado_id = e.id
                ORDER BY l.id DESC
            """
            rows = execute_query(query, fetchall=True)
            for r in rows:
                r['salario_base'] = float(r['salario_base'])
                r['total_percepciones'] = float(r['total_percepciones'])
                r['deducciones_totales'] = float(r['deducciones_totales'])
                r['neto_a_pagar'] = float(r['neto_a_pagar'])
                r['fecha_ingreso'] = str(r['fecha_ingreso'])[:10]
                r['fecha_salida'] = str(r['fecha_salida'])[:10]
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            emp_id = int(data.get('empleado_id', 0))
            f_salida = data.get('fecha_salida', str(date.today()))
            motivo = data.get('motivo_salida', 'Renuncia Voluntaria')
            dias_pendientes = int(data.get('dias_pendientes_pago', 0) or 0)
            deducciones = float(data.get('deducciones_totales', 0) or 0)

            emp = execute_query("SELECT * FROM empleados WHERE id = ?", (emp_id,), fetchone=True)
            if not emp:
                return jsonify({"error": "Empleado no encontrado."}), 404

            f_ingreso = emp['fecha_ingreso']
            salario = float(emp['salario_base'])
            valor_dia = round(salario / 30.0, 2)

            d_ing = datetime.strptime(str(f_ingreso)[:10], '%Y-%m-%d').date() if f_ingreso else date(2022, 1, 1)
            d_egr = datetime.strptime(f_salida[:10], '%Y-%m-%d').date()

            diff_dias = max(1, (d_egr - d_ing).days)
            anios = diff_dias // 365
            meses = (diff_dias % 365) // 30
            dias = (diff_dias % 365) % 30

            # 1. Salario pendiente
            monto_pend = round(dias_pendientes * valor_dia, 2)

            # 2. Vacaciones proporcionales pendientes (Art. 76 y 77 Ley 185)
            saldo_vac = float(emp.get('dias_vacaciones_disponibles') or 0.0)
            monto_vac = round(saldo_vac * valor_dia, 2)

            # 3. Aguinaldo proporcional (Art. 93 Ley 185)
            # El período de aguinaldo computa desde el 1 de diciembre anterior
            anio_egr = d_egr.year
            d_inicio_agui = date(anio_egr - 1, 12, 1)
            base_agui = max(d_inicio_agui, d_ing)
            dias_agui = max(0, (d_egr - base_agui).days + 1)
            meses_agui = dias_agui / 30.0
            monto_agui = round((salario / 12.0) * (meses_agui if meses_agui <= 12.0 else 12.0), 2)

            # 4. Indemnización por Años de Servicio (Art. 45 Ley 185)
            # Solo aplica si es despido sin justa causa o renuncia/acuerdo con indemnización pactada
            monto_indem = 0.0
            if 'Despido Injustificado' in motivo or 'Art. 45' in motivo:
                anios_completos = anios
                meses_fraccion = meses + (dias / 30.0)
                # Art. 45: 1 mes por cada uno de los primeros 3 años; 20 días por año adicional (tope 5 meses)
                meses_indem = 0.0
                if anios_completos <= 3:
                    meses_indem = anios_completos + (meses_fraccion / 12.0)
                else:
                    meses_indem = 3.0 + ((anios_completos - 3) * (20.0 / 30.0)) + (meses_fraccion * (20.0 / 360.0))
                meses_indem = min(5.0, meses_indem)
                monto_indem = round(meses_indem * salario, 2)

            total_percepciones = round(monto_pend + monto_vac + monto_agui + monto_indem, 2)
            neto_pagar = max(0.0, round(total_percepciones - deducciones, 2))

            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM liquidaciones_laborales")
            next_id = cursor.fetchone()[0]
            codigo_liq = f"LIQ-2026-{next_id:03d}"
            elaborado = session.get('user', {}).get('username', 'admin')

            cursor.execute("""
                INSERT INTO liquidaciones_laborales
                (codigo, empleado_id, fecha_ingreso, fecha_salida, motivo_salida, salario_base,
                 antiguedad_anios, antiguedad_meses, antiguedad_dias, monto_dias_pendientes,
                 dias_vacaciones_pendientes, monto_vacaciones, monto_aguinaldo_proporcional,
                 monto_indemnizacion_antiguedad, total_percepciones, deducciones_totales,
                 neto_a_pagar, estado, elaborado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Borrador', ?)
            """, (codigo_liq, emp_id, d_ing, d_egr, motivo, salario, anios, meses, dias,
                  monto_pend, saldo_vac, monto_vac, monto_agui, monto_indem,
                  total_percepciones, deducciones, neto_pagar, elaborado))
            conn.commit()
            conn.close()

            return jsonify({
                "success": True,
                "mensaje": f"Liquidación {codigo_liq} calculada exitosamente (Neto a pagar: C$ {neto_pagar:,.2f}).",
                "id": next_id
            }), 201

    @app.route('/rrhh/liquidacion/<int:id>/imprimir')
    @login_required
    def imprimir_liquidacion_laboral(id):
        query = """
            SELECT l.*, e.nombre_completo AS empleado, e.identificacion AS cedula,
                   e.cargo, e.num_inss AS inss
            FROM liquidaciones_laborales l
            INNER JOIN empleados e ON l.empleado_id = e.id
            WHERE l.id = ?
        """
        row = execute_query(query, (id,), fetchone=True)
        if not row:
            return "Liquidación no encontrada", 404

        l = {
            "codigo": row['codigo'],
            "empleado": row['empleado'],
            "cedula": row['cedula'] or '—',
            "cargo": row['cargo'] or '—',
            "inss": row['inss'] or '—',
            "fecha_ingreso": str(row['fecha_ingreso'])[:10],
            "fecha_salida": str(row['fecha_salida'])[:10],
            "motivo_salida": row['motivo_salida'],
            "antiguedad_anios": row['antiguedad_anios'],
            "antiguedad_meses": row['antiguedad_meses'],
            "antiguedad_dias": row['antiguedad_dias'],
            "salario_base": float(row['salario_base']),
            "monto_dias_pendientes": float(row['monto_dias_pendientes']),
            "dias_vacaciones_pendientes": float(row['dias_vacaciones_pendientes']),
            "monto_vacaciones": float(row['monto_vacaciones']),
            "monto_aguinaldo_proporcional": float(row['monto_aguinaldo_proporcional']),
            "monto_indemnizacion_antiguedad": float(row['monto_indemnizacion_antiguedad']),
            "total_percepciones": float(row['total_percepciones']),
            "deducciones_totales": float(row['deducciones_totales']),
            "neto_a_pagar": float(row['neto_a_pagar']),
            "fecha_elaboracion": str(row.get('fecha_elaboracion') or date.today())[:10]
        }
        return render_template('liquidacion.html', l=l)

    # =========================================================================
    # 9. PAGOS DE NÓMINA (RF109)
    # =========================================================================
    @app.route('/api/rrhh/pagos-nomina', methods=['GET', 'POST'])
    @login_required
    def api_pagos_nomina():
        if request.method == 'GET':
            query = """
                SELECT p.id, p.nomina_id, p.empleado_id, e.nombre_completo AS empleado,
                       p.monto_pagado, p.fecha_pago, p.metodo_pago,
                       ISNULL(p.numero_referencia, '') AS numero_referencia, p.estado
                FROM pagos_nomina p
                INNER JOIN empleados e ON p.empleado_id = e.id
                ORDER BY p.fecha_pago DESC
            """
            rows = execute_query(query, fetchall=True)
            for r in rows:
                r['monto_pagado'] = float(r['monto_pagado'])
                r['fecha_pago'] = str(r['fecha_pago'])[:10]
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            nom_id = int(data.get('nomina_id', 0))
            emp_id = int(data.get('empleado_id', 0))
            monto = float(data.get('monto_pagado', 0))
            f_pago = data.get('fecha_pago', str(date.today()))
            metodo = data.get('metodo_pago', 'Efectivo - Caja POS')
            ref = data.get('numero_referencia', '').strip()
            usuario = session.get('user', {}).get('username', 'admin')

            execute_query("""
                INSERT INTO pagos_nomina
                (nomina_id, empleado_id, monto_pagado, fecha_pago, metodo_pago, numero_referencia, estado, usuario_responsable)
                VALUES (?, ?, ?, ?, ?, ?, 'Confirmado', ?)
            """, (nom_id, emp_id, monto, f_pago, metodo, ref, usuario), commit=True)

            return jsonify({"success": True, "mensaje": "Pago de nómina registrado y confirmado."}), 201

    # =========================================================================
    # 10. SEGURIDAD E HIGIENE OCUPACIONAL (LEY 618) (RF110 al RF114)
    # =========================================================================
    @app.route('/api/rrhh/higiene/riesgos', methods=['GET', 'POST'])
    @login_required
    def api_higiene_riesgos():
        if request.method == 'GET':
            rows = execute_query("SELECT * FROM higiene_riesgos ORDER BY id ASC", fetchall=True)
            for r in rows:
                if 'fecha_registro' in r and r['fecha_registro']:
                    r['fecha_registro'] = str(r['fecha_registro'])[:10]
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403
            data = request.json or {}
            execute_query("""
                INSERT INTO higiene_riesgos (area, tipo_riesgo, descripcion, nivel_riesgo, medidas_preventivas, responsable_seguimiento)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (data.get('area'), data.get('tipo_riesgo'), data.get('descripcion'), data.get('nivel_riesgo', 'Medio'), data.get('medidas_preventivas'), data.get('responsable_seguimiento')), commit=True)
            return jsonify({"success": True, "mensaje": "Riesgo laboral registrado exitosamente."}), 201

    @app.route('/api/rrhh/higiene/inspecciones', methods=['GET', 'POST'])
    @login_required
    def api_higiene_inspecciones():
        if request.method == 'GET':
            rows = execute_query("SELECT * FROM higiene_inspecciones ORDER BY id DESC", fetchall=True)
            for r in rows:
                r['fecha_inspeccion'] = str(r['fecha_inspeccion'])[:10]
                if r.get('porcentaje_cumplimiento') is not None:
                    r['porcentaje_cumplimiento'] = float(r['porcentaje_cumplimiento'])
                r['resultado'] = r.get('estado') or 'Aprobada'
                r['observaciones_detectadas'] = r.get('observaciones') or ''
                r['medidas_correctivas'] = r.get('acciones_correctivas') or ''
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            f_insp = data.get('fecha_inspeccion') or str(date.today())
            inspector = data.get('inspector') or session.get('user', {}).get('nombre', 'Inspector')
            p1 = 1 if data.get('pasillos_despejados') else 0
            p2 = 1 if data.get('estanterias_seguras') else 0
            p3 = 1 if data.get('repuestos_ordenados') else 0
            p4 = 1 if data.get('extintores_adecuados') else 0
            p5 = 1 if data.get('salidas_emergencia_libres') else 0
            p6 = 1 if data.get('area_caja_segura') else 0
            obs = data.get('observaciones', '')
            acciones = data.get('acciones_correctivas') or data.get('medidas_correctivas', '')

            puntos_aprobados = p1 + p2 + p3 + p4 + p5 + p6
            porcentaje = round((puntos_aprobados / 6.0) * 100, 1)
            estado = data.get('estado') or ('Aprobada' if puntos_aprobados == 6 else ('Observada' if puntos_aprobados >= 4 else 'Crítica'))

            execute_query("""
                INSERT INTO higiene_inspecciones
                (fecha_inspeccion, inspector, pasillos_despejados, estanterias_seguras, repuestos_ordenados,
                 extintores_adecuados, salidas_emergencia_libres, area_caja_segura, puntos_aprobados,
                 total_puntos, porcentaje_cumplimiento, observaciones, acciones_correctivas, estado)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 6, ?, ?, ?, ?)
            """, (f_insp, inspector, p1, p2, p3, p4, p5, p6, puntos_aprobados, porcentaje, obs, acciones, estado), commit=True)

            return jsonify({
                "success": True, 
                "mensaje": f"Inspección de 6 puntos guardada: {puntos_aprobados}/6 verificados ({porcentaje}% - Estado: {estado})."
            }), 201

    @app.route('/api/rrhh/higiene/inspecciones/<int:id>', methods=['GET', 'PUT', 'DELETE'])
    @login_required
    def api_higiene_inspeccion_detalle(id):
        if request.method == 'GET':
            row = execute_query("SELECT * FROM higiene_inspecciones WHERE id = ?", (id,), fetchone=True)
            if not row:
                return jsonify({"error": "Inspección no encontrada"}), 404
            row['fecha_inspeccion'] = str(row['fecha_inspeccion'])[:10]
            if row.get('porcentaje_cumplimiento') is not None:
                row['porcentaje_cumplimiento'] = float(row['porcentaje_cumplimiento'])
            row['resultado'] = row.get('estado') or 'Aprobada'
            row['observaciones_detectadas'] = row.get('observaciones') or ''
            row['medidas_correctivas'] = row.get('acciones_correctivas') or ''
            return jsonify(row)

        if session['user']['rol'] not in ROLES_RRHH:
            return jsonify({"error": "No tienes permisos."}), 403

        if request.method == 'DELETE':
            row = execute_query("SELECT id FROM higiene_inspecciones WHERE id = ?", (id,), fetchone=True)
            if not row:
                return jsonify({"error": "Inspección no encontrada"}), 404
            execute_query("DELETE FROM higiene_inspecciones WHERE id = ?", (id,), commit=True)
            return jsonify({"success": True, "mensaje": "Inspección eliminada exitosamente."})

        if request.method == 'PUT':
            row = execute_query("SELECT * FROM higiene_inspecciones WHERE id = ?", (id,), fetchone=True)
            if not row:
                return jsonify({"error": "Inspección no encontrada"}), 404

            data = request.json or {}
            f_insp = data.get('fecha_inspeccion') or str(row['fecha_inspeccion'])[:10]
            inspector = data.get('inspector') or row.get('inspector') or session.get('user', {}).get('nombre', 'Inspector')

            p1 = 1 if data.get('pasillos_despejados') else 0
            p2 = 1 if data.get('estanterias_seguras') else 0
            p3 = 1 if data.get('repuestos_ordenados') else 0
            p4 = 1 if data.get('extintores_adecuados') else 0
            p5 = 1 if data.get('salidas_emergencia_libres') else 0
            p6 = 1 if data.get('area_caja_segura') else 0
            obs = data.get('observaciones', row.get('observaciones') or '')
            acciones = data.get('acciones_correctivas') or data.get('medidas_correctivas') or row.get('acciones_correctivas') or ''

            puntos_aprobados = p1 + p2 + p3 + p4 + p5 + p6
            porcentaje = round((puntos_aprobados / 6.0) * 100, 1)
            estado = data.get('estado') or ('Aprobada' if puntos_aprobados == 6 else ('Observada' if puntos_aprobados >= 4 else 'Crítica'))

            execute_query("""
                UPDATE higiene_inspecciones
                SET fecha_inspeccion = ?, inspector = ?, pasillos_despejados = ?, estanterias_seguras = ?,
                    repuestos_ordenados = ?, extintores_adecuados = ?, salidas_emergencia_libres = ?,
                    area_caja_segura = ?, puntos_aprobados = ?, total_puntos = 6,
                    porcentaje_cumplimiento = ?, observaciones = ?, acciones_correctivas = ?, estado = ?
                WHERE id = ?
            """, (f_insp, inspector, p1, p2, p3, p4, p5, p6, puntos_aprobados, porcentaje, obs, acciones, estado, id), commit=True)

            return jsonify({
                "success": True, 
                "mensaje": f"Inspección #{id} actualizada correctamente: {puntos_aprobados}/6 verificados ({porcentaje}% - Estado: {estado})."
            })

    @app.route('/api/rrhh/higiene/incidentes', methods=['GET', 'POST'])
    @login_required
    def api_higiene_incidentes():
        if request.method == 'GET':
            query = """
                SELECT i.*, ISNULL(e.nombre_completo, 'Personal / Cliente') AS empleado
                FROM higiene_incidentes i
                LEFT JOIN empleados e ON i.empleado_id = e.id
                ORDER BY i.fecha DESC
            """
            rows = execute_query(query, fetchall=True)
            for r in rows:
                r['fecha'] = str(r['fecha'])[:10]
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT ISNULL(MAX(id), 0) + 1 FROM higiene_incidentes")
            next_id = cursor.fetchone()[0]
            cod = f"INC-2026-{next_id:03d}"
            usuario = session.get('user', {}).get('username', 'admin')

            cursor.execute("""
                INSERT INTO higiene_incidentes
                (codigo_incidente, fecha, area, empleado_id, tipo_suceso, descripcion, posibles_causas, medidas_correctivas, dias_incapacidad, estado_seguimiento, registrado_por)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'En Seguimiento', ?)
            """, (cod, data.get('fecha', str(date.today())), data.get('area', 'Almacén'),
                  data.get('empleado_id') or None, data.get('tipo_suceso', 'Incidente'),
                  data.get('descripcion', ''), data.get('posibles_causas', ''),
                  data.get('medidas_correctivas', ''), int(data.get('dias_incapacidad', 0) or 0), usuario))
            conn.commit()
            conn.close()

            return jsonify({"success": True, "mensaje": f"Evento {cod} registrado para seguimiento."}), 201

    @app.route('/api/rrhh/higiene/epp', methods=['GET', 'POST'])
    @login_required
    def api_higiene_epp():
        if request.method == 'GET':
            query = """
                SELECT p.*, e.nombre_completo AS empleado
                FROM higiene_epp p
                INNER JOIN empleados e ON p.empleado_id = e.id
                ORDER BY p.fecha_entrega DESC
            """
            rows = execute_query(query, fetchall=True)
            for r in rows:
                r['fecha_entrega'] = str(r['fecha_entrega'])[:10]
                r['fecha_reposicion_sugerida'] = str(r['fecha_reposicion_sugerida'])[:10] if r.get('fecha_reposicion_sugerida') else ''
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            data = request.json or {}
            execute_query("""
                INSERT INTO higiene_epp
                (empleado_id, tipo_equipo, fecha_entrega, cantidad, estado_equipo, fecha_reposicion_sugerida, entregado_por, observaciones)
                VALUES (?, ?, ?, ?, 'Nuevo', ?, ?, ?)
            """, (int(data.get('empleado_id')), data.get('tipo_equipo'), data.get('fecha_entrega', str(date.today())),
                  int(data.get('cantidad', 1)), data.get('fecha_reposicion_sugerida') or None,
                  session.get('user', {}).get('nombre', 'Administración'), data.get('observaciones', '')), commit=True)
            return jsonify({"success": True, "mensaje": "Entrega de EPP registrada con éxito."}), 201

    @app.route('/api/rrhh/higiene/capacitaciones', methods=['GET', 'POST'])
    @login_required
    def api_higiene_capacitaciones():
        if request.method == 'GET':
            rows = execute_query("SELECT * FROM higiene_capacitaciones ORDER BY fecha DESC", fetchall=True)
            for r in rows:
                r['fecha'] = str(r['fecha'])[:10]
                r['duracion_horas'] = float(r['duracion_horas'])
            return jsonify(rows)

        if request.method == 'POST':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403
            data = request.json or {}
            execute_query("""
                INSERT INTO higiene_capacitaciones
                (nombre_capacitacion, fecha, duracion_horas, facilitador, temas_tratados, asistentes_conteo, observaciones)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (data.get('nombre_capacitacion'), data.get('fecha', str(date.today())), float(data.get('duracion_horas', 2.0)),
                  data.get('facilitador'), data.get('temas_tratados'), int(data.get('asistentes_conteo', 1)), data.get('observaciones', '')), commit=True)
            return jsonify({"success": True, "mensaje": "Capacitación en seguridad registrada."}), 201

    # =========================================================================
    # 11. MARCO LEGAL Y PARÁMETROS LABORALES (RF115, RF116, RF119)
    # =========================================================================
    @app.route('/api/rrhh/marco-legal', methods=['GET'])
    @login_required
    def api_marco_legal():
        """Biblioteca interactiva de consulta de normativas (Ley 185, Ley 618, Ley 822, Ley 539)."""
        articulos = [
            {
                "ley": "Código del Trabajo (Ley 185)",
                "articulo": "Art. 45",
                "tema": "Indemnización por Años de Servicio",
                "resumen": "En caso de terminación por voluntad del empleador sin justa causa, se indemnizará con un mes de salario por cada uno de los primeros 3 años, y 20 días por año adicional, con un tope de 5 meses.",
                "enlace": "https://www.poderjudicial.gob.ni/cjnejapa/pdf/codigo-trabajo.pdf"
            },
            {
                "ley": "Código del Trabajo (Ley 185)",
                "articulo": "Art. 62",
                "tema": "Remuneración de Horas Extraordinarias",
                "resumen": "El trabajo en horas extraordinarias se remunerará con un cien por ciento (100%) más del valor de la hora ordinaria.",
                "enlace": "https://www.poderjudicial.gob.ni/cjnejapa/pdf/codigo-trabajo.pdf"
            },
            {
                "ley": "Código del Trabajo (Ley 185)",
                "articulo": "Art. 64",
                "tema": "Descanso Semanal (Séptimo Día)",
                "resumen": "Todo trabajador tiene derecho a un día de descanso continuo remunerado por cada seis días de trabajo. Si falta injustificadamente pierde la remuneración de ese día de descanso.",
                "enlace": "https://www.poderjudicial.gob.ni/cjnejapa/pdf/codigo-trabajo.pdf"
            },
            {
                "ley": "Código del Trabajo (Ley 185)",
                "articulo": "Art. 76",
                "tema": "Derecho a Vacaciones Continuas",
                "resumen": "Quince días de descanso continuo y remunerado por cada seis meses ininterrumpidos de trabajo (equivalente a 2.5 días ganados por mes trabajado).",
                "enlace": "https://www.poderjudicial.gob.ni/cjnejapa/pdf/codigo-trabajo.pdf"
            },
            {
                "ley": "Código del Trabajo (Ley 185)",
                "articulo": "Art. 79",
                "tema": "Permisos que no interrumpen Vacaciones",
                "resumen": "La interrupción por enfermedad, permiso u otra causa justa no interrumpe la suma de días computables para vacaciones.",
                "enlace": "https://www.poderjudicial.gob.ni/cjnejapa/pdf/codigo-trabajo.pdf"
            },
            {
                "ley": "Código del Trabajo (Ley 185)",
                "articulo": "Art. 93",
                "tema": "Décimo Tercer Mes (Aguinaldo)",
                "resumen": "Todo trabajador tiene derecho a que su empleador le pague un mes de salario adicional por cada año de trabajo continuo o proporcional.",
                "enlace": "https://www.poderjudicial.gob.ni/cjnejapa/pdf/codigo-trabajo.pdf"
            },
            {
                "ley": "Ley General de Higiene y Seguridad (Ley 618)",
                "articulo": "Art. 18",
                "tema": "Obligaciones Preventivas del Empleador",
                "resumen": "Adoptar medidas para evitar riesgos en almacenamiento, conservar salidas y extintores despejados y capacitar periódicamente al personal.",
                "enlace": "http://legislacion.asamblea.gob.ni/normaweb.nsf/b92aaea87dac762406257265005d21f7/ec658510842db144062573210065be6b?OpenDocument"
            },
            {
                "ley": "Ley de Concertación Tributaria (Ley 822)",
                "articulo": "Art. 23",
                "tema": "Tarifa Progresiva de Rentas del Trabajo (IR)",
                "resumen": "Retención en la fuente sobre base mensual proyectada anualmente: hasta C$100,000 exento; del 15% al 30% según escala.",
                "enlace": "http://legislacion.asamblea.gob.ni/normaweb.nsf/b92aaea87dac762406257265005d21f7/b39837c79f7eaf4206257afb0052c524?OpenDocument"
            },
            {
                "ley": "Ley de Seguridad Social (Ley 539)",
                "articulo": "Decreto 06-2019",
                "tema": "Tasas de Cotización INSS",
                "resumen": "Aporte laboral del 7% y patronal del 21.5% para empresas con menos de 50 trabajadores bajo Régimen Integral.",
                "enlace": "http://www.inss.gob.ni"
            }
        ]
        return jsonify(articulos)

    @app.route('/api/rrhh/parametros', methods=['GET', 'PUT'])
    @app.route('/api/rrhh/parametros/<string:codigo>', methods=['PUT'])
    @login_required
    def api_parametros_laborales(codigo=None):
        if request.method == 'GET':
            rows = execute_query("SELECT * FROM parametros_laborales ORDER BY id ASC", fetchall=True)
            return jsonify([normalizar_parametro(r) for r in rows])

        if request.method == 'PUT':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos para modificar parámetros legales."}), 403

            data = request.json or {}
            codigo = codigo or data.get('codigo') or data.get('clave')
            if not codigo:
                return jsonify({'error': 'Indique el código del parámetro.'}), 400
            rows = execute_query('SELECT * FROM parametros_laborales', fetchall=True)
            row = next((r for r in rows if codigo in (r.get('codigo'), r.get('clave'), normalizar_parametro(r)['codigo'])), None)
            if not row:
                return jsonify({'error': 'Parámetro no encontrado.'}), 404
            try:
                nuevo_valor = validar_parametro(normalizar_parametro(row)['codigo'], data.get('valor'))
            except (TypeError, ValueError) as exc:
                return jsonify({'error': str(exc)}), 400
            usuario = session.get('user', {}).get('username', 'admin')
            clave_col = 'codigo' if 'codigo' in row else 'clave'
            usuario_col = 'usuario_modificacion' if 'codigo' in row else 'usuario_modifico'
            clave = row[clave_col]
            valor_guardado = nuevo_valor
            if clave_col == 'clave':
                if clave in ('INSS_LABORAL', 'INSS_PATRONAL', 'INATEC_PATRONAL', 'AGUINALDO_PROV'):
                    valor_guardado /= 100
                elif clave == 'RECARGO_HORA_EXTRA':
                    valor_guardado = 1 + nuevo_valor / 100
            execute_query(f"""
                UPDATE parametros_laborales
                SET valor = ?, {usuario_col} = ?, fecha_vigencia = GETDATE()
                WHERE {clave_col} = ?
            """, (valor_guardado, usuario, clave), commit=True)
            return jsonify({"success": True, "mensaje": f"Parámetro {clave} actualizado a {nuevo_valor}."})

    @app.route('/api/rrhh/calendario-obligaciones', methods=['GET', 'PATCH'])
    @login_required
    def api_calendario_obligaciones():
        if request.method == 'GET':
            rows = execute_query("SELECT * FROM calendario_obligaciones ORDER BY fecha_vencimiento ASC", fetchall=True)
            for r in rows:
                r['fecha_vencimiento'] = str(r['fecha_vencimiento'])[:10]
                if r.get('fecha_cumplimiento'):
                    r['fecha_cumplimiento'] = str(r['fecha_cumplimiento'])[:10]
            return jsonify(rows)

        if request.method == 'PATCH':
            if session['user']['rol'] not in ROLES_RRHH:
                return jsonify({"error": "No tienes permisos."}), 403

            id_ob = request.json.get('id')
            comprobante = request.json.get('comprobante', '').strip()
            execute_query("""
                UPDATE calendario_obligaciones
                SET estado = 'Cumplida', fecha_cumplimiento = GETDATE(), comprobante_adjunto = ?
                WHERE id = ?
            """, (comprobante, id_ob), commit=True)
            return jsonify({"success": True, "mensaje": "Obligación marcada como cumplida con comprobante."})

    # =========================================================================
    # 12. ESTADÍSTICA: ANÁLISIS DE DEVOLUCIONES (RF68)
    # =========================================================================
    @app.route('/api/reportes/devoluciones', methods=['GET'])
    @login_required
    def api_reportes_devoluciones():
        if session['user']['rol'] not in ROLES_ADMIN_GERENCIA:
            return jsonify({"error": "Acceso restringido."}), 403

        query = """
            SELECT d.id, d.venta_id, d.fecha, d.motivo, d.total_devuelto,
                   dd.producto_id, p.nombre AS producto, p.codigo_sku AS codigo,
                   c.nombre AS categoria, dd.cantidad, dd.subtotal
            FROM devoluciones d
            LEFT JOIN detalle_devoluciones dd ON d.id = dd.devolucion_id
            LEFT JOIN productos p ON dd.producto_id = p.id
            LEFT JOIN categorias c ON p.categoria_id = c.id
            ORDER BY d.fecha DESC
        """
        rows = execute_query(query, fetchall=True)

        total_operaciones = len(set(r['id'] for r in rows))
        total_monto = sum(float(r['total_devuelto'] or 0) for r in rows)
        total_unidades = sum(int(r['cantidad'] or 0) for r in rows)

        motivos_count = {}
        categorias_count = {}
        for r in rows:
            m = r.get('motivo') or 'Defecto de Fábrica'
            motivos_count[m] = motivos_count.get(m, 0) + 1
            cat = r.get('categoria') or 'General'
            categorias_count[cat] = categorias_count.get(cat, 0) + int(r.get('cantidad') or 0)

        return jsonify({
            "total_operaciones": total_operaciones,
            "total_monto": round(total_monto, 2),
            "total_unidades": total_unidades,
            "motivos": motivos_count,
            "por_categoria": categorias_count,
            "detalle": [{
                "id": r['id'],
                "venta_id": r['venta_id'],
                "fecha": str(r['fecha'])[:10] if r['fecha'] else '',
                "motivo": r['motivo'],
                "producto": r['producto'] or '—',
                "codigo": r['codigo'] or '—',
                "cantidad": r['cantidad'] or 0,
                "subtotal": float(r['subtotal'] or 0)
            } for r in rows[:20]]
        })

    # =========================================================================
    # 13. INFORME EJECUTIVO ESTADÍSTICO (RF65) (Imprimible)
    # =========================================================================
    @app.route('/reportes/ejecutivo/imprimir')
    @login_required
    def imprimir_reporte_ejecutivo():
        if session['user']['rol'] not in ROLES_ADMIN_GERENCIA:
            return "Acceso restringido", 403

        # Traer resumen financiero y comercial
        mes = request.args.get('mes')
        anio = request.args.get('anio', '2026')
        res = api_reportes_datos_ejecutivos(mes, anio)
        return render_template('informe_ejecutivo.html', r=res)

    def api_reportes_datos_ejecutivos(mes_param, anio_param):
        # Función auxiliar para renderizar los datos del informe ejecutivo
        conn = get_db_connection()
        c = conn.cursor()
        
        c.execute("SELECT COUNT(id), ISNULL(SUM(total), 0) FROM ventas WHERE estado = 'Completada'")
        v = c.fetchone()
        ventas_tot = float(v[1])
        ventas_cnt = int(v[0])

        c.execute("SELECT COUNT(id), ISNULL(SUM(total), 0) FROM compras WHERE estado = 'Completada'")
        comp = c.fetchone()
        compras_tot = float(comp[1])

        c.execute("SELECT * FROM vista_balance_inventario")
        inv = c.fetchone()
        stock_cnt = int(inv[1]) if inv else 0
        inv_costo = float(inv[2]) if inv else 0.0
        inv_venta = float(inv[3]) if inv else 0.0

        c.execute("""
            SELECT TOP 5 p.nombre, SUM(dv.cantidad) as cant, SUM(dv.subtotal) as tot
            FROM detalle_ventas dv
            JOIN productos p ON dv.producto_id = p.id
            JOIN ventas v ON dv.venta_id = v.id
            WHERE v.estado = 'Completada'
            GROUP BY p.nombre ORDER BY tot DESC
        """)
        top_prods = [{"nombre": r[0], "cant": int(r[1]), "tot": float(r[2])} for r in c.fetchall()]

        conn.close()

        margen = round(ventas_tot - (ventas_tot * 0.72), 2)  # estimado
        ticket = round(ventas_tot / ventas_cnt, 2) if ventas_cnt > 0 else 0.0

        return {
            "empresa": "Jehová Jireh Moto Repuestos",
            "fecha_emision": datetime.now().strftime("%d de %B de %Y"),
            "periodo": f"{'Año ' + str(anio_param) if anio_param else 'Histórico 2026'}",
            "ventas_monto": ventas_tot,
            "ventas_conteo": ventas_cnt,
            "compras_monto": compras_tot,
            "margen_bruto": margen,
            "ticket_promedio": ticket,
            "stock_total": stock_cnt,
            "inventario_costo": inv_costo,
            "inventario_venta": inv_venta,
            "top_productos": top_prods
        }
