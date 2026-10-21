import os
import pyodbc
from datetime import datetime, timezone, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, send_file
from werkzeug.security import generate_password_hash, check_password_hash
from calculos_rrhh import calcular_nomina_empleado
from rrhh_service import ROLES_RRHH, limites_periodo, dias_en_periodo, fecha, parametros_calculo
from reportes_service import (
    construir_filtro_periodo,
    procesar_reporte_completo,
    comparar_dos_periodos,
    generar_excel_informe_workbook
)

def obtener_fecha_hoy_nicaragua():
    return datetime.now(timezone(timedelta(hours=-6))).date().isoformat()

app = Flask(__name__, template_folder='Fronted/templates', static_folder='Fronted/static')
app.secret_key = os.environ.get('SECRET_KEY', 'jehova_jireh_secret_key_2026_super_secure')

# ==============================================================================
# CONFIGURACIÓN DE BASE DE DATOS SQL SERVER
# ==============================================================================
# Cambia 'DB_SERVER' según tu servidor SQL Server o usa el nombre local automáticamente.
DB_SERVER = os.environ.get('DB_SERVER', os.environ.get('COMPUTERNAME', r'.'))
DB_NAME = 'jehova_jireh_db'

def get_db_connection():
    # Intenta con el servidor configurado y realiza fallback automático si es necesario
    servidores = [DB_SERVER]
    comp_name = os.environ.get('COMPUTERNAME')
    for srv in [comp_name, '.', 'localhost', 'HILLARY', 'LAPTOP-CNR3S3I3']:
        if srv and srv not in servidores:
            servidores.append(srv)

    ultimo_error = None
    for srv in servidores:
        try:
            conn_str = (
                r'DRIVER={ODBC Driver 17 for SQL Server};'
                fr'SERVER={srv};'
                fr'DATABASE={DB_NAME};'
                r'Trusted_Connection=yes;'
            )
            return pyodbc.connect(conn_str, timeout=3)
        except Exception as e:
            ultimo_error = e
            continue
    raise ultimo_error

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """Función de ayuda para ejecutar consultas y retornar diccionarios"""
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        if commit:
            conn.commit()
            
        if fetchone:
            if cursor.description is None: return None
            columns = [column[0] for column in cursor.description]
            row = cursor.fetchone()
            if row:
                return dict(zip(columns, row))
            return None
            
        if fetchall:
            if cursor.description is None: return []
            columns = [column[0] for column in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(columns, row)) for row in rows]
            
        return cursor.rowcount
    finally:
        cursor.close()
        conn.close()

# ==============================================================================
# DECORADORES DE SEGURIDAD
# ==============================================================================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles_permitidos):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user' not in session:
                return redirect(url_for('login'))
            user_rol = session['user'].get('rol')
            if user_rol not in roles_permitidos:
                return jsonify({"error": "Acceso denegado: Tu rol no tiene permisos para esta acción."}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# ==============================================================================
# RUTAS DE VISTAS (RENDER TEMPLATES)
# ==============================================================================
@app.route('/dashboard')
@login_required
def inicio():
    return render_template('index.html', usuario=session.get('user'))

@app.route('/perfil')
@login_required
def perfil():
    return render_template('perfil.html', usuario=session.get('user'))

@app.route('/')
def tienda():
    # Obtener los productos reales de la base de datos
    query_productos = """
        SELECT p.id, p.nombre, p.precio_venta, p.stock_actual, c.nombre AS categoria 
        FROM productos p 
        LEFT JOIN categorias c ON p.categoria_id = c.id 
        WHERE (p.activo = 1 OR p.activo IS NULL) AND p.stock_actual > 0
    """
    productos = execute_query(query_productos, fetchall=True)

    # Obtener las categorías que tienen al menos un producto activo
    query_categorias = """
        SELECT DISTINCT c.nombre AS nombre
        FROM productos p
        INNER JOIN categorias c ON p.categoria_id = c.id
        WHERE (p.activo = 1 OR p.activo IS NULL) AND p.stock_actual > 0
    """
    categorias = execute_query(query_categorias, fetchall=True)

    return render_template('tienda.html', productos=productos, categorias=categorias)

@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre_completo = request.form.get('nombre_completo')
        email = request.form.get('email')
        password = request.form.get('password')
        telefono = request.form.get('telefono', '')
        direccion = request.form.get('direccion', '')

        # Verificar si el correo ya está registrado
        check_query = "SELECT id FROM clientes WHERE email = ?"
        user_exists = execute_query(check_query, params=(email,), fetchall=True)

        if user_exists:
            return render_template('registro.html', error='Ese correo electrónico ya está registrado.')

        # Encriptar la contraseña
        password_hash = generate_password_hash(password)

        # Insertar el nuevo cliente
        insert_query = """
            INSERT INTO clientes (nombre_completo, email, password_hash, telefono, direccion, tipo_cliente)
            VALUES (?, ?, ?, ?, ?, 'General')
        """
        try:
            execute_query(insert_query, params=(nombre_completo, email, password_hash, telefono, direccion), commit=True)
            # Redirigir al login con éxito (podríamos usar flash messages, pero por ahora en la URL o render)
            return render_template('login.html', error='¡Registro exitoso! Por favor inicia sesión con tu nueva cuenta.')
        except Exception as e:
            return render_template('registro.html', error='Error al registrar. Por favor intenta de nuevo.')

    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.form if request.form else request.get_json(silent=True)
        if not data:
            data = {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()

        # 1. Validación como Empleado/Admin en la base de datos SQL Server
        query = """
            SELECT u.id, u.username, u.nombre_completo AS nombre, r.nombre AS rol, u.rol_id
            FROM usuarios u
            INNER JOIN roles r ON u.rol_id = r.id
            WHERE u.username = ? AND u.password_hash = ? AND u.activo = 1
        """
        usuario = execute_query(query, (username, password), fetchone=True)
        
        if usuario:
            # Consultar permisos asignados al rol en la tabla permisos (si existe)
            user_permisos = []
            try:
                perm_rows = execute_query(
                    "SELECT nombre FROM permisos WHERE rol_id = ?",
                    params=(usuario.get('rol_id') or 1,),
                    fetchall=True
                )
                if perm_rows:
                    user_permisos = [p['nombre'] for p in perm_rows]
            except Exception as e:
                print(f"[Fase 1] Advertencia al leer permisos: {e}")

            session['user'] = {
                'id': usuario['id'],
                'username': usuario['username'],
                'nombre': usuario['nombre'],
                'rol': usuario['rol'],
                'rol_id': usuario.get('rol_id'),
                'permisos': user_permisos
            }

            # --- REGISTRO AUDITORÍA FASE 1: Tabla sesiones y ultimo_acceso ---
            try:
                ip_cliente = request.remote_addr or '127.0.0.1'
                conn_s = get_db_connection()
                cur_s = conn_s.cursor()
                cur_s.execute(
                    "INSERT INTO sesiones (usuario_id, fechaInicio, estado, ip) VALUES (?, GETDATE(), 'Activa', ?)",
                    (usuario['id'], ip_cliente)
                )
                cur_s.execute("SELECT @@IDENTITY")
                ses_row = cur_s.fetchone()
                if ses_row and ses_row[0]:
                    session['db_session_id'] = int(ses_row[0])

                # Actualizar también el campo ultimo_acceso en la tabla usuarios
                cur_s.execute(
                    "UPDATE usuarios SET ultimo_acceso = GETDATE() WHERE id = ?",
                    (usuario['id'],)
                )

                conn_s.commit()
                cur_s.close()
                conn_s.close()
            except Exception as e:
                print(f"[Fase 1] Advertencia al registrar sesión / ultimo_acceso: {e}")

            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": True, "redirect": url_for('inicio')})
            return redirect(url_for('inicio'))
            
        # 2. Validación como Cliente Web
        query_cliente = "SELECT id, email, nombre_completo, password_hash, direccion FROM clientes WHERE email = ?"
        cliente = execute_query(query_cliente, (username,), fetchone=True)
        
        if cliente and check_password_hash(cliente['password_hash'], password):
            session['user'] = {
                'id': cliente['id'],
                'username': cliente['email'],
                'nombre': cliente['nombre_completo'],
                'rol': 'Cliente',
                'direccion': cliente.get('direccion', '') or ''
            }
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": True, "redirect": url_for('tienda')})
            return redirect(url_for('tienda'))

        # Si falla en ambas tablas
        error_msg = "Usuario o contraseña incorrectos."
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": error_msg}), 401
        return render_template('login.html', error=error_msg)

    return render_template('login.html')

@app.route('/logout')
def logout():
    # --- REGISTRO AUDITORÍA FASE 1: Cerrar sesión en tabla sesiones ---
    db_session_id = session.get('db_session_id')
    if db_session_id:
        try:
            conn_s = get_db_connection()
            cur_s = conn_s.cursor()
            cur_s.execute("UPDATE sesiones SET estado = 'Cerrada' WHERE id = ?", (db_session_id,))
            conn_s.commit()
            cur_s.close()
            conn_s.close()
        except Exception as e:
            print(f"[Fase 1] Advertencia al cerrar sesión: {e}")

    session.clear()
    return redirect(url_for('tienda'))

# --- SEGURIDAD Y AUDITORÍA (FASE 1: PERMISOS Y SESIONES) ---
@app.route('/api/permisos', methods=['GET'])
@login_required
def api_permisos():
    """Consulta de permisos del usuario actual o de todos los roles (para Admin)"""
    user_rol = session['user'].get('rol')
    user_rol_id = session['user'].get('rol_id')
    try:
        if user_rol == 'Administrador' and request.args.get('todos') == 'true':
            query = """
                SELECT p.id, p.rol_id, r.nombre AS rol, p.nombre AS permiso, p.descripcion
                FROM permisos p
                INNER JOIN roles r ON p.rol_id = r.id
                ORDER BY p.rol_id, p.nombre
            """
            permisos = execute_query(query, fetchall=True)
            return jsonify(permisos)
        else:
            query = """
                SELECT p.id, p.nombre AS permiso, p.descripcion
                FROM permisos p
                WHERE p.rol_id = ?
            """
            permisos = execute_query(query, params=(user_rol_id,), fetchall=True) if user_rol_id else []
            return jsonify({"rol": user_rol, "permisos": permisos})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/sesiones/historial', methods=['GET'])
@login_required
def api_sesiones_historial():
    """Historial de auditoría de sesiones para el Administrador"""
    if session['user'].get('rol') != 'Administrador':
        return jsonify({"error": "Acceso denegado: solo Administrador."}), 403
    try:
        query = """
            SELECT TOP 50 s.id, s.usuario_id, u.username, u.nombre_completo, s.fechaInicio, s.estado, s.ip
            FROM sesiones s
            INNER JOIN usuarios u ON s.usuario_id = u.id
            ORDER BY s.fechaInicio DESC
        """
        sesiones = execute_query(query, fetchall=True)
        return jsonify(sesiones)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# ENDPOINTS API (JSON) - CONECTADOS A SQL SERVER
# ==============================================================================

# --- USUARIOS ---
@app.route('/api/usuarios', methods=['GET', 'POST'])
@login_required
def api_usuarios():
    if request.method == 'GET':
        query = """
            SELECT u.id, u.username, u.nombre_completo AS nombre, u.email, u.telefono, r.nombre AS rol, u.ultimo_acceso 
            FROM usuarios u
            INNER JOIN roles r ON u.rol_id = r.id
            WHERE u.activo = 1
        """
        usuarios = execute_query(query, fetchall=True)
        return jsonify(usuarios)

    if request.method == 'POST':
        if session['user']['rol'] != 'Administrador':
            return jsonify({"error": "Solo el Administrador puede registrar nuevos usuarios."}), 403
        
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        nombre = data.get('nombre', '').strip()
        rol = data.get('rol', '').strip()

        if not username or not password or not nombre or not rol:
            return jsonify({"error": "Todos los campos son obligatorios."}), 400

        rol_info = execute_query("SELECT id FROM roles WHERE nombre = ?", (rol,), fetchone=True)
        if not rol_info:
            return jsonify({"error": "Rol no válido."}), 400

        existente = execute_query("SELECT id FROM usuarios WHERE username = ?", (username,), fetchone=True)
        if existente:
            return jsonify({"error": "El nombre de usuario ya existe."}), 400

        query_insert = """
            INSERT INTO usuarios (rol_id, username, password_hash, nombre_completo, activo)
            VALUES (?, ?, ?, ?, 1)
        """
        try:
            execute_query(query_insert, (rol_info['id'], username, password, nombre), commit=True)
            return jsonify({"success": True, "mensaje": "Usuario registrado exitosamente."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

# --- CATEGORIAS ---
@app.route('/api/categorias', methods=['GET', 'POST'])
@login_required
def api_categorias():
    if request.method == 'GET':
        categorias = execute_query("SELECT id, nombre, descripcion FROM categorias ORDER BY nombre ASC", fetchall=True)
        return jsonify(categorias)

    if request.method == 'POST':
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones']:
            return jsonify({"error": "No tienes permiso para registrar categorías."}), 403
        
        data = request.json or {}
        nombre = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '').strip()

        if not nombre:
            return jsonify({"error": "El nombre de la categoría es obligatorio."}), 400

        existente = execute_query("SELECT id FROM categorias WHERE nombre = ?", (nombre,), fetchone=True)
        if existente:
            return jsonify({"error": "El nombre de la categoría ya existe."}), 400

        try:
            execute_query("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion), commit=True)
            return jsonify({"success": True, "mensaje": "Categoría registrada exitosamente."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/categorias/<int:cat_id>', methods=['PUT'])
@login_required
def api_categoria_editar(cat_id):
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones']:
        return jsonify({"error": "No tienes permiso para modificar categorías."}), 403
    
    data = request.json or {}
    nombre = data.get('nombre', '').strip()
    descripcion = data.get('descripcion', '').strip()

    if not nombre:
        return jsonify({"error": "El nombre de la categoría es obligatorio."}), 400

    existente = execute_query("SELECT id FROM categorias WHERE nombre = ? AND id != ?", (nombre, cat_id), fetchone=True)
    if existente:
        return jsonify({"error": "El nombre de la categoría ya existe."}), 400

    try:
        execute_query("UPDATE categorias SET nombre = ?, descripcion = ? WHERE id = ?", (nombre, descripcion, cat_id), commit=True)
        return jsonify({"success": True, "mensaje": "Categoría actualizada exitosamente."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- PRODUCTOS / INVENTARIO ---
@app.route('/api/productos', methods=['GET', 'POST'])
@login_required
def api_productos():
    if request.method == 'GET':
        query = """
            SELECT p.id, p.codigo_sku AS codigo, p.nombre, c.nombre AS categoria,
                   p.precio_venta AS precio, p.costo, p.stock_actual AS stock, p.stock_minimo AS min_stock
            FROM productos p
            INNER JOIN categorias c ON p.categoria_id = c.id
            WHERE p.activo = 1
        """
        productos = execute_query(query, fetchall=True)
        for p in productos:
            p['precio'] = float(p['precio'])
            p['costo'] = float(p['costo'])
        return jsonify(productos)

    if request.method == 'POST':
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones']:
            return jsonify({"error": "No tienes permiso para registrar productos."}), 403
        
        data = request.json or {}
        codigo = data.get('codigo', '').strip()
        nombre = data.get('nombre', '').strip()
        categoria = data.get('categoria', 'General').strip()
        precio = float(data.get('precio', 0))
        costo = float(data.get('costo', 0))
        stock = int(data.get('stock', 0))
        min_stock = int(data.get('min_stock', 5))

        if not nombre or precio <= 0 or not codigo:
            return jsonify({"error": "Nombre, Código y Precio válidos son obligatorios."}), 400

        query_insert = """
            INSERT INTO productos (codigo_sku, categoria_id, nombre, costo, precio_venta, stock_actual, stock_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Buscar o crear categoría
            cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (categoria,))
            cat_row = cursor.fetchone()
            if cat_row:
                cat_id = cat_row[0]
            else:
                cursor.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, '')", (categoria,))
                cursor.execute("SELECT @@IDENTITY AS id")
                cat_id = cursor.fetchone()[0]
            cursor.execute(query_insert, (codigo, cat_id, nombre, costo, precio, stock, min_stock))
            cursor.execute("SELECT @@IDENTITY AS id")
            new_id = cursor.fetchone()[0]
            
            if stock > 0:
                mov_query = """
                    INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, motivo, usuario_id)
                    VALUES (?, 'ENTRADA_INICIAL', ?, 0, ?, 'Registro de producto nuevo', ?)
                """
                cursor.execute(mov_query, (new_id, stock, stock, session['user']['id']))
            conn.commit()
            return jsonify({"success": True, "mensaje": "Producto registrado"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/productos/<int:prod_id>', methods=['PUT', 'DELETE'])
@login_required
def api_producto_editar(prod_id):
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones']:
        return jsonify({"error": "No tienes permiso para modificar productos."}), 403
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        prod = execute_query("SELECT * FROM productos WHERE id = ?", (prod_id,), fetchone=True)
        if not prod:
            return jsonify({"error": "Producto no encontrado."}), 404

        if request.method == 'DELETE':
            cursor.execute("UPDATE productos SET activo = 0 WHERE id = ?", (prod_id,))
            conn.commit()
            return jsonify({"success": True, "mensaje": "Producto eliminado exitosamente."})
            
        # Si es PUT
        data = request.json or {}
        codigo = data.get('codigo', prod['codigo_sku']).strip()
        nombre = data.get('nombre', prod['nombre']).strip()
        categoria = data.get('categoria', '').strip()
        precio = float(data.get('precio', prod['precio_venta']))
        costo = float(data.get('costo', prod['costo']))
        min_stock = int(data.get('min_stock', prod['stock_minimo']))
        
        cat_id = prod['categoria_id']
        if categoria:
            cursor.execute("SELECT id FROM categorias WHERE nombre = ?", (categoria,))
            cat_row = cursor.fetchone()
            if cat_row:
                cat_id = cat_row[0]
            else:
                cursor.execute("INSERT INTO categorias (nombre, descripcion) VALUES (?, '')", (categoria,))
                cursor.execute("SELECT @@IDENTITY AS id")
                cat_id = cursor.fetchone()[0]
        
        update_query = """
            UPDATE productos 
            SET codigo_sku=?, nombre=?, categoria_id=?, precio_venta=?, costo=?, stock_minimo=?
            WHERE id=?
        """
        cursor.execute(update_query, (codigo, nombre, cat_id, precio, costo, min_stock, prod_id))
        
        if 'stock' in data:
            nuevo_stock = int(data['stock'])
            if nuevo_stock != prod['stock_actual']:
                diff = nuevo_stock - prod['stock_actual']
                tipo_mov = 'AJUSTE_ENTRADA' if diff > 0 else 'AJUSTE_SALIDA'
                
                cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (nuevo_stock, prod_id))
                mov_query = """
                    INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, motivo, usuario_id)
                    VALUES (?, ?, ?, ?, ?, 'Ajuste por edición de producto', ?)
                """
                cursor.execute(mov_query, (prod_id, tipo_mov, abs(diff), prod['stock_actual'], nuevo_stock, session['user']['id']))
        
        conn.commit()
        return jsonify({"success": True, "mensaje": "Producto actualizado exitosamente."})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- MOVIMIENTOS DE INVENTARIO (KARDEX) ---
@app.route('/api/movimientos', methods=['GET', 'POST'])
@login_required
def api_movimientos():
    if request.method == 'GET':
        query = """
            SELECT m.id, m.fecha, p.codigo_sku AS producto_codigo, p.nombre AS producto_nombre,
                   m.tipo_movimiento AS tipo, m.cantidad, m.motivo, u.nombre_completo AS usuario
            FROM movimientos_inventario m
            INNER JOIN productos p ON m.producto_id = p.id
            INNER JOIN usuarios u ON m.usuario_id = u.id
            ORDER BY m.fecha DESC
        """
        movs = execute_query(query, fetchall=True)
        for m in movs:
            if hasattr(m['fecha'], 'strftime'):
                m['fecha'] = m['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        return jsonify(movs)

    if request.method == 'POST':
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones']:
            return jsonify({"error": "No tienes permiso para registrar movimientos de inventario."}), 403

        data = request.json or {}
        p_id = int(data.get('producto_id', 0))
        tipo_accion = data.get('tipo', 'ENTRADA').upper()
        cantidad = int(data.get('cantidad', 0))
        motivo = data.get('motivo', 'Ajuste manual de inventario').strip()

        if cantidad <= 0:
            return jsonify({"error": "La cantidad debe ser mayor a 0."}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            prod = execute_query("SELECT id, nombre, stock_actual FROM productos WHERE id = ?", (p_id,), fetchone=True)
            if not prod:
                return jsonify({"error": "Producto no encontrado."}), 404

            stock_anterior = prod['stock_actual']
            if tipo_accion == 'SALIDA':
                if stock_anterior < cantidad:
                    return jsonify({"error": f"Stock insuficiente. Disponible: {stock_anterior}"}), 400
                stock_posterior = stock_anterior - cantidad
                tipo_mov = 'AJUSTE_SALIDA'
            else:
                stock_posterior = stock_anterior + cantidad
                tipo_mov = 'AJUSTE_ENTRADA'

            cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (stock_posterior, p_id))
            cursor.execute("""
                INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, motivo, usuario_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (p_id, tipo_mov, cantidad, stock_anterior, stock_posterior, motivo, session['user']['id']))
            
            conn.commit()
            return jsonify({"success": True, "mensaje": f"Movimiento registrado. Stock actual: {stock_posterior}"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/movimientos/<int:mov_id>', methods=['PUT'])
@login_required
def api_movimiento_editar(mov_id):
    return jsonify({"error": "Por integridad contable (SQL), edita el stock con un nuevo movimiento o ajuste, no alterando el historial pasado."}), 400

# --- CAJA ---
@app.route('/api/caja/estado', methods=['GET'])
@login_required
def api_caja_estado():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT TOP 1 id, fecha_apertura, monto_inicial FROM sesiones_caja WHERE usuario_id = ? AND estado = 'Abierta' ORDER BY id DESC", (session['user']['id'],))
        caja = cursor.fetchone()
        
        if caja:
            return jsonify({
                "estado": "Abierta",
                "sesion_caja_id": caja.id,
                "fecha_apertura": caja.fecha_apertura.strftime('%Y-%m-%d %H:%M:%S'),
                "monto_inicial": float(caja.monto_inicial)
            })
        else:
            return jsonify({"estado": "Cerrada"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/caja/apertura', methods=['POST'])
@login_required
def api_caja_apertura():
    data = request.json or {}
    monto_inicial = data.get('monto_inicial', 0.0)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM sesiones_caja WHERE usuario_id = ? AND estado = 'Abierta'", (session['user']['id'],))
        if cursor.fetchone():
            return jsonify({"error": "Ya tienes un turno de caja abierto."}), 400
            
        cursor.execute('''
            INSERT INTO sesiones_caja (usuario_id, monto_inicial, estado)
            OUTPUT INSERTED.id
            VALUES (?, ?, 'Abierta')
        ''', (session['user']['id'], monto_inicial))
        
        sesion_id = cursor.fetchone()[0]
        conn.commit()
        
        return jsonify({"success": True, "sesion_caja_id": sesion_id, "mensaje": "Caja abierta exitosamente."})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/caja/cierre', methods=['POST'])
@login_required
def api_caja_cierre():
    data = request.json or {}
    sesion_id = data.get('sesion_caja_id')
    monto_final_real = data.get('monto_final_real', 0.0)
    observaciones = data.get('observaciones', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT monto_inicial, estado FROM sesiones_caja WHERE id = ? AND usuario_id = ?", 
                       (sesion_id, session['user']['id']))
        caja = cursor.fetchone()
        if not caja or caja.estado != 'Abierta':
            return jsonify({"error": "Sesión de caja inválida o ya está cerrada."}), 400
            
        monto_inicial = caja.monto_inicial
        
        cursor.execute("SELECT ISNULL(SUM(total), 0) FROM ventas WHERE sesion_caja_id = ? AND estado != 'Anulada' AND forma_pago = 'Efectivo'", (sesion_id,))
        ventas_efectivo = cursor.fetchone()[0]
        
        monto_final_esperado = float(monto_inicial) + float(ventas_efectivo)
        diferencia = float(monto_final_real) - monto_final_esperado
        
        cursor.execute('''
            UPDATE sesiones_caja 
            SET fecha_cierre = GETDATE(),
                monto_final_esperado = ?,
                monto_final_real = ?,
                diferencia = ?,
                estado = 'Cerrada',
                observaciones = ?
            WHERE id = ?
        ''', (monto_final_esperado, monto_final_real, diferencia, observaciones, sesion_id))
        
        conn.commit()
        return jsonify({"success": True, "mensaje": "Caja cerrada correctamente.", "diferencia": diferencia})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/caja/sesiones', methods=['GET'])
@role_required('Administrador', 'Contador')
def api_caja_sesiones():
    query = """
        SELECT s.id, u.nombre_completo AS usuario, 
               FORMAT(s.fecha_apertura, 'yyyy-MM-dd HH:mm:ss') as fecha_apertura,
               FORMAT(s.fecha_cierre, 'yyyy-MM-dd HH:mm:ss') as fecha_cierre,
               s.estado, s.diferencia
        FROM sesiones_caja s
        INNER JOIN usuarios u ON s.usuario_id = u.id
        ORDER BY s.fecha_apertura DESC
    """
    sesiones = execute_query(query, fetchall=True)
    return jsonify(sesiones)

@app.route('/api/caja/sesion/<int:id>', methods=['GET'])
@login_required
def api_caja_sesion(id):
    query = """
        SELECT s.id, u.nombre_completo AS usuario, 
               FORMAT(s.fecha_apertura, 'yyyy-MM-dd HH:mm:ss') as fecha_apertura,
               FORMAT(s.fecha_cierre, 'yyyy-MM-dd HH:mm:ss') as fecha_cierre,
               s.monto_inicial, s.monto_final_esperado, s.monto_final_real,
               s.diferencia, s.estado, s.observaciones
        FROM sesiones_caja s
        INNER JOIN usuarios u ON s.usuario_id = u.id
        WHERE s.id = ?
    """
    sesion = execute_query(query, (id,), fetchone=True)
    
    if not sesion:
        return jsonify({"error": "Sesión no encontrada"}), 404
        
    query_ventas = "SELECT ISNULL(SUM(total), 0) FROM ventas WHERE sesion_caja_id = ? AND estado != 'Anulada' AND forma_pago = 'Efectivo'"
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(query_ventas, (id,))
        ventas_efectivo = cursor.fetchone()[0]
        sesion['ventas_efectivo'] = float(ventas_efectivo)
    except:
        sesion['ventas_efectivo'] = 0.0
    finally:
        cursor.close()
        conn.close()

    return jsonify(sesion)

# --- VENTAS (POS) ---
@app.route('/api/ventas', methods=['GET', 'POST'])
@login_required
def api_ventas():
    if request.method == 'GET':
        query_v = """
            SELECT v.id, v.codigo_venta, 
                   COALESCE(c.nombre_completo, v.nombre_cliente_invitado) AS cliente, 
                   v.fecha_venta AS fecha,
                   u.nombre_completo AS vendedor, v.total, v.forma_pago, v.estado
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            LEFT JOIN usuarios u ON v.usuario_id = u.id
            ORDER BY v.id DESC
        """
        ventas = execute_query(query_v, fetchall=True)
        for v in ventas:
            if hasattr(v['fecha'], 'strftime'):
                v['fecha'] = v['fecha'].strftime('%Y-%m-%d')
            v['total'] = float(v['total'])
            
            detalles = execute_query("""
                SELECT p.id AS producto_id, p.nombre AS producto_nombre, d.cantidad, d.precio_unitario, d.subtotal 
                FROM detalle_ventas d
                INNER JOIN productos p ON d.producto_id = p.id
                WHERE d.venta_id = ?
            """, (v['id'],), fetchall=True)
            for d in detalles:
                d['precio_unitario'] = float(d['precio_unitario'])
                d['subtotal'] = float(d['subtotal'])
            v['detalles'] = detalles
            
        return jsonify(ventas)

    if request.method == 'POST':
        if session['user']['rol'] not in ['Administrador', 'Vendedor', 'Gerente de Operaciones']:
            return jsonify({"error": "No tienes permiso para procesar ventas."}), 403
        
        data = request.json or {}
        cliente_nombre = data.get('cliente', 'Cliente General').strip()
        forma_pago = data.get('forma_pago', 'Efectivo').strip()
        items = data.get('items', []) 

        if not items:
            return jsonify({"error": "El carrito de compra está vacío."}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            import random, string
            random_str = ''.join(random.choices(string.digits, k=4))
            codigo_v = f"VEN-{random_str}"
            
            total_venta = 0.0
            detalles_a_insertar = []

            for item in items:
                p_id = int(item.get('producto_id'))
                cant = int(item.get('cantidad', 1))
                
                cursor.execute("SELECT id, nombre, stock_actual, precio_venta, costo FROM productos WHERE id = ?", (p_id,))
                prod = cursor.fetchone()
                
                if not prod:
                    conn.rollback()
                    return jsonify({"error": f"Producto ID {p_id} no existe."}), 400
                
                if prod.stock_actual < cant:
                    conn.rollback()
                    return jsonify({"error": f"Stock insuficiente para '{prod.nombre}'. Disponible: {prod.stock_actual}"}), 400

                subtotal = float(prod.precio_venta) * cant
                total_venta += subtotal
                
                detalles_a_insertar.append((
                    p_id, cant, float(prod.precio_venta), float(prod.costo), subtotal, prod.stock_actual
                ))

            cursor.execute("SELECT id FROM sesiones_caja WHERE usuario_id = ? AND estado = 'Abierta'", (session['user']['id'],))
            sesion_row = cursor.fetchone()
            if not sesion_row:
                conn.rollback()
                return jsonify({"error": "Debe abrir un turno de caja antes de realizar ventas."}), 400
            sesion_id = sesion_row.id

            cursor.execute("""
                INSERT INTO ventas (codigo_venta, cliente_id, nombre_cliente_invitado, usuario_id, sesion_caja_id, fecha_venta, subtotal, descuento, total, forma_pago, estado)
                VALUES (?, NULL, ?, ?, ?, GETDATE(), ?, 0, ?, ?, 'Completada')
            """, (codigo_v, cliente_nombre, session['user']['id'], sesion_id, total_venta, total_venta, forma_pago))
            
            cursor.execute("SELECT @@IDENTITY AS id")
            venta_id = cursor.fetchone()[0]
            
            for (p_id, cant, precio, costo, subtotal, stock_ant) in detalles_a_insertar:
                cursor.execute("""
                    INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio_unitario, costo_historico, subtotal)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (venta_id, p_id, cant, precio, costo, subtotal))
                
                stock_post = stock_ant - cant
                cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (stock_post, p_id))
                
                cursor.execute("""
                    INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, referencia_origen, motivo, usuario_id)
                    VALUES (?, 'SALIDA_VENTA', ?, ?, ?, ?, ?, ?)
                """, (p_id, cant, stock_ant, stock_post, f"Venta {codigo_v}", 'Venta desde caja', session['user']['id']))

            # --- FASE 2: REGISTRO DE PAGO Y COMPROBANTE EN POS ---
            try:
                cursor.execute("""
                    INSERT INTO pagos (venta_id, pedido_web_id, origen, metodo, monto, referencia, fecha)
                    VALUES (?, NULL, 'VENTA_POS', ?, ?, ?, GETDATE())
                """, (venta_id, forma_pago, total_venta, f"Cobro en caja {codigo_v}"))

                numero_comp = f"TICK-{codigo_v}"
                cursor.execute("""
                    INSERT INTO comprobantes (venta_id, pedido_web_id, origen, numero, fechaEmision, total)
                    VALUES (?, NULL, 'VENTA_POS', ?, GETDATE(), ?)
                """, (venta_id, numero_comp, total_venta))
            except Exception as e_pago:
                print(f"[Fase 2] Nota al registrar pago/comprobante POS: {e_pago}")

            # --- ASIENTO CONTABLE AUTOMÁTICO DE VENTA ---
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '1.1.01'") # Caja
            cta_caja = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '4.1.01'") # Ventas
            cta_ventas = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '5.1.01'") # Costo Ventas
            cta_costo = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '1.1.04'") # Inventario
            cta_inv = cursor.fetchone()[0]

            total_costo_venta = sum(c[3] * c[1] for c in detalles_a_insertar) # costo * cant

            cursor.execute("""
                INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
                VALUES (GETDATE(), ?, 'VENTAS', ?, ?)
            """, (f"Venta {codigo_v}", venta_id, session['user']['id']))
            cursor.execute("SELECT @@IDENTITY AS id")
            asiento_v_id = cursor.fetchone()[0]

            # Por el ingreso
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_v_id, cta_caja, total_venta))
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_v_id, cta_ventas, total_venta))
            # Por el costo
            if total_costo_venta > 0:
                cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_v_id, cta_costo, total_costo_venta))
                cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_v_id, cta_inv, total_costo_venta))

            cursor.execute("""
                SELECT v.id, v.codigo_venta, c.nombre_completo AS cliente, v.fecha_venta AS fecha,
                       u.nombre_completo AS vendedor, v.total, v.forma_pago, v.estado
                FROM ventas v
                LEFT JOIN clientes c ON v.cliente_id = c.id
                INNER JOIN usuarios u ON v.usuario_id = u.id
                WHERE v.id = ?
            """, (venta_id,))
            v_row = cursor.fetchone()
            
            venta_obj = {
                "id": v_row.id,
                "codigo_venta": v_row.codigo_venta,
                "cliente": v_row.cliente,
                "fecha": v_row.fecha.strftime('%Y-%m-%d') if hasattr(v_row.fecha, 'strftime') else str(v_row.fecha),
                "vendedor": v_row.vendedor,
                "total": float(v_row.total),
                "forma_pago": v_row.forma_pago,
                "detalles": []
            }
            
            cursor.execute("""
                SELECT p.nombre AS producto_nombre, d.cantidad, d.precio_unitario, d.subtotal 
                FROM detalle_ventas d
                INNER JOIN productos p ON d.producto_id = p.id
                WHERE d.venta_id = ?
            """, (venta_id,))
            detalles_rows = cursor.fetchall()
            for d in detalles_rows:
                venta_obj["detalles"].append({
                    "producto_nombre": d.producto_nombre,
                    "cantidad": d.cantidad,
                    "precio_unitario": float(d.precio_unitario),
                    "subtotal": float(d.subtotal)
                })

            conn.commit()
            return jsonify({"success": True, "mensaje": f"Venta {codigo_v} procesada.", "venta": venta_obj}), 201

        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            return jsonify({"error": str(e)}), 500


@app.route('/api/ventas_web', methods=['POST'])
def api_ventas_web():
    """ Endpoint abierto para ventas de la tienda online (clientes o invitados) """
    data = request.json or {}
    nombre_cliente = data.get('nombre_cliente', 'Invitado').strip()
    email = data.get('email', '').strip()
    items = data.get('items', []) 

    if not items:
        return jsonify({"error": "El carrito de compra está vacío."}), 400

    cliente_id = None
    if 'user' in session and session['user']['rol'] == 'Cliente':
        cliente_id = session['user']['id']

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        import random, string
        random_str = ''.join(random.choices(string.digits, k=4))
        codigo_v = f"WEB-{random_str}"
        
        total_venta = 0.0
        detalles_a_insertar = []

        for item in items:
            p_id = int(item.get('producto_id'))
            cant = int(item.get('cantidad', 1))
            
            cursor.execute("SELECT id, nombre, stock_actual, precio_venta, costo FROM productos WHERE id = ?", (p_id,))
            prod = cursor.fetchone()
            
            if not prod:
                conn.rollback()
                return jsonify({"error": f"Producto ID {p_id} no existe."}), 400
            
            if prod.stock_actual < cant:
                conn.rollback()
                return jsonify({"error": f"Stock insuficiente para '{prod.nombre}'. Disponible: {prod.stock_actual}"}), 400

            subtotal = float(prod.precio_venta) * cant
            total_venta += subtotal
            
            detalles_a_insertar.append((
                p_id, cant, float(prod.precio_venta), float(prod.costo), subtotal, prod.stock_actual
            ))

        # Buscar un admin genérico para los movimientos que exigen usuario_id NO NULL
        cursor.execute("SELECT TOP 1 u.id FROM usuarios u INNER JOIN roles r ON u.rol_id = r.id WHERE r.nombre = 'Administrador'")
        admin_row = cursor.fetchone()
        admin_id = admin_row[0] if admin_row else 1

        # Extraer datos de contacto y entrega enviados desde la tienda web
        forma_entrega = data.get('forma_entrega', 'Envío a Domicilio').strip()
        metodo_pago = data.get('metodo', 'Efectivo').strip()
        telefono = data.get('telefono', '').strip()
        direccion = data.get('direccion', '').strip() or data.get('address', '').strip()

        # --- FASE 2: FLUJO EXCLUSIVO DEL PORTAL WEB (UML) ---
        # 1. Registrar Carrito formal y su detalle
        cursor.execute("""
            INSERT INTO carritos (cliente_id, subtotal, estado)
            VALUES (?, ?, 'Completado')
        """, (cliente_id, total_venta))
        cursor.execute("SELECT @@IDENTITY AS id")
        carrito_id = cursor.fetchone()[0]

        for (p_id, cant, precio, costo, subtotal, stock_ant) in detalles_a_insertar:
            cursor.execute("""
                INSERT INTO detalle_carritos (carrito_id, producto_id, cantidad, precioUnitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (carrito_id, p_id, cant, precio, subtotal))

        # 2. Registrar Pedido Web formal y su detalle (sin tocar la tabla ventas)
        cursor.execute("""
            INSERT INTO pedidos_web (codigo, cliente_id, fecha, subtotal, total, formaEntrega, metodo, estado, nombre_cliente, telefono, email, direccion_entrega)
            VALUES (?, ?, GETDATE(), ?, ?, ?, ?, 'Completado', ?, ?, ?, ?)
        """, (codigo_v, cliente_id, total_venta, total_venta, forma_entrega, metodo_pago, nombre_cliente, telefono, email, direccion))
        cursor.execute("SELECT @@IDENTITY AS id")
        pedido_id = cursor.fetchone()[0]

        for (p_id, cant, precio, costo, subtotal, stock_ant) in detalles_a_insertar:
            cursor.execute("""
                INSERT INTO detalle_pedidos_web (pedido_id, producto_id, cantidad, precioUnitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (pedido_id, p_id, cant, precio, subtotal))
            
            # Descontar stock y registrar movimiento en Kardex
            stock_post = stock_ant - cant
            cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (stock_post, p_id))
            cursor.execute("""
                INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, referencia_origen, motivo, usuario_id)
                VALUES (?, 'SALIDA_VENTA', ?, ?, ?, ?, ?, ?)
            """, (p_id, cant, stock_ant, stock_post, f"Pedido Web {codigo_v}", 'Venta desde la tienda online', admin_id))

        # 3. Registrar Pago formal con discriminador 'PEDIDO_WEB'
        cursor.execute("""
            INSERT INTO pagos (venta_id, pedido_web_id, origen, metodo, monto, referencia, fecha)
            VALUES (NULL, ?, 'PEDIDO_WEB', ?, ?, ?, GETDATE())
        """, (pedido_id, metodo_pago, total_venta, f"Pago Online {codigo_v}"))

        # 4. Registrar Comprobante digital con discriminador 'PEDIDO_WEB'
        numero_comp_web = f"COMP-{codigo_v}"
        cursor.execute("""
            INSERT INTO comprobantes (venta_id, pedido_web_id, origen, numero, fechaEmision, total)
            VALUES (NULL, ?, 'PEDIDO_WEB', ?, GETDATE(), ?)
        """, (pedido_id, numero_comp_web, total_venta))

        # --- ASIENTO CONTABLE AUTOMÁTICO DE VENTA WEB ---
        cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '1.1.01'") # Caja
        cta_caja = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '4.1.01'") # Ventas
        cta_ventas = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '5.1.01'") # Costo Ventas
        cta_costo = cursor.fetchone()[0]
        cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '1.1.04'") # Inventario
        cta_inv = cursor.fetchone()[0]

        total_costo_venta = sum(c[3] * c[1] for c in detalles_a_insertar)

        cursor.execute("""
            INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
            VALUES (GETDATE(), ?, 'PEDIDOS_WEB', ?, ?)
        """, (f"Pedido Web {codigo_v}", pedido_id, admin_id))
        
        cursor.execute("SELECT @@IDENTITY AS id")
        asiento_v_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_v_id, cta_caja, total_venta))
        cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_v_id, cta_ventas, total_venta))
        
        if total_costo_venta > 0:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_v_id, cta_costo, total_costo_venta))
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_v_id, cta_inv, total_costo_venta))

        conn.commit()
        return jsonify({
            "success": True, 
            "mensaje": f"Venta {codigo_v} procesada con éxito.",
            "codigo": codigo_v,
            "comprobante": f"COMP-{codigo_v}"
        }), 201

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"error": str(e)}), 500

# --- CONSULTAS FASE 2: PEDIDOS WEB, PAGOS Y COMPROBANTES ---
@app.route('/api/pedidos_web', methods=['GET'])
@login_required
def api_pedidos_web():
    """Consulta de pedidos web con sus detalles para el panel administrativo"""
    query = """
        SELECT p.id, p.codigo, p.cliente_id, 
               COALESCE(c.nombre_completo, p.nombre_cliente, 'Cliente Invitado') AS cliente,
               p.fecha, p.subtotal, p.total, p.formaEntrega, p.metodo, p.estado,
               p.telefono, p.email, p.direccion_entrega
        FROM pedidos_web p
        LEFT JOIN clientes c ON p.cliente_id = c.id
        ORDER BY p.id DESC
    """
    pedidos = execute_query(query, fetchall=True)
    for ped in pedidos:
        if hasattr(ped['fecha'], 'strftime'):
            ped['fecha'] = ped['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        ped['total'] = float(ped['total'])
        ped['subtotal'] = float(ped['subtotal'])
        
        # Obtener detalle de productos del pedido web
        detalles = execute_query("""
            SELECT dp.id, dp.producto_id, prod.nombre AS producto_nombre, prod.codigo_sku,
                   dp.cantidad, dp.precioUnitario, dp.subtotal
            FROM detalle_pedidos_web dp
            INNER JOIN productos prod ON dp.producto_id = prod.id
            WHERE dp.pedido_id = ?
        """, (ped['id'],), fetchall=True)
        for d in detalles:
            d['precioUnitario'] = float(d['precioUnitario'])
            d['precio_unitario'] = float(d['precioUnitario'])
            d['subtotal'] = float(d['subtotal'])
        ped['detalles'] = detalles
        ped['codigo_venta'] = ped['codigo']
        ped['forma_pago'] = ped['metodo']
        ped['vendedor'] = 'Tienda Online'
        
    return jsonify(pedidos)

@app.route('/api/pedidos_web/<int:p_id>/anular', methods=['POST'])
@login_required
def api_pedido_web_anular(p_id):
    """Anula un pedido web, retorna el stock al kardex e inserta la reversión contable"""
    if session.get('user', {}).get('rol') not in ['Administrador', 'Vendedor', 'Gerente de Operaciones']:
        return jsonify({"error": "No tienes permiso para anular pedidos web."}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT estado, codigo FROM pedidos_web WHERE id = ?", (p_id,))
        pedido = cursor.fetchone()
        if not pedido:
            return jsonify({"error": "Pedido web no encontrado."}), 404
        if pedido.estado == 'Anulado':
            return jsonify({"error": "Este pedido ya se encuentra anulado."}), 400

        cursor.execute("UPDATE pedidos_web SET estado = 'Anulado' WHERE id = ?", (p_id,))

        cursor.execute("SELECT producto_id, cantidad FROM detalle_pedidos_web WHERE pedido_id = ?", (p_id,))
        detalles = cursor.fetchall()
        user_id = session.get('user', {}).get('id', 1)

        for det in detalles:
            cursor.execute("SELECT stock_actual FROM productos WHERE id = ?", (det.producto_id,))
            prod = cursor.fetchone()
            if prod:
                stock_ant = prod.stock_actual
                stock_post = stock_ant + det.cantidad
                cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (stock_post, det.producto_id))
                cursor.execute("""
                    INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, motivo, usuario_id)
                    VALUES (?, 'DEVOLUCION_CLIENTE', ?, ?, ?, ?, ?)
                """, (det.producto_id, det.cantidad, stock_ant, stock_post, f"Anulacion de Pedido Web {pedido.codigo}", user_id))

        # Reversión contable
        cursor.execute("SELECT id FROM asientos_contables WHERE referencia_id = ? AND modulo_origen = 'PEDIDOS_WEB'", (p_id,))
        asiento = cursor.fetchone()
        if asiento:
            cursor.execute("""
                INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
                VALUES (GETDATE(), ?, 'REVERSION_PEDIDO_WEB', ?, ?)
            """, (f"Anulacion Pedido Web {pedido.codigo}", p_id, user_id))
            cursor.execute("SELECT @@IDENTITY AS id")
            new_asiento_id = cursor.fetchone()[0]

            cursor.execute("SELECT cuenta_id, debe, haber FROM movimientos_contables WHERE asiento_id = ?", (asiento.id,))
            for m in cursor.fetchall():
                cursor.execute("""
                    INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber)
                    VALUES (?, ?, ?, ?)
                """, (new_asiento_id, m.cuenta_id, m.haber, m.debe))

        conn.commit()
        return jsonify({"success": True, "mensaje": f"Pedido Web {pedido.codigo} anulado exitosamente. Stock retornado."})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        conn.close()

@app.route('/api/pagos', methods=['GET'])
@login_required
def api_pagos():
    """Consulta consolidada de pagos (POS y Web)"""
    origen = request.args.get('origen')
    if origen:
        query = """
            SELECT p.id, p.venta_id, p.pedido_web_id, p.origen, p.metodo, p.monto, p.referencia, p.fecha
            FROM pagos p
            WHERE p.origen = ?
            ORDER BY p.id DESC
        """
        pagos = execute_query(query, (origen,), fetchall=True)
    else:
        query = """
            SELECT p.id, p.venta_id, p.pedido_web_id, p.origen, p.metodo, p.monto, p.referencia, p.fecha
            FROM pagos p
            ORDER BY p.id DESC
        """
        pagos = execute_query(query, fetchall=True)
        
    for p in pagos:
        if hasattr(p['fecha'], 'strftime'):
            p['fecha'] = p['fecha'].strftime('%Y-%m-%d %H:%M:%S')
        p['monto'] = float(p['monto'])
    return jsonify(pagos)

@app.route('/api/comprobantes', methods=['GET'])
@login_required
def api_comprobantes():
    """Consulta consolidada de comprobantes emitidos (POS y Web)"""
    query = """
        SELECT c.id, c.venta_id, c.pedido_web_id, c.origen, c.numero, c.fechaEmision, c.total
        FROM comprobantes c
        ORDER BY c.id DESC
    """
    comps = execute_query(query, fetchall=True)
    for c in comps:
        if hasattr(c['fechaEmision'], 'strftime'):
            c['fechaEmision'] = c['fechaEmision'].strftime('%Y-%m-%d %H:%M:%S')
        c['total'] = float(c['total'])
    return jsonify(comps)


@app.route('/api/ventas/<int:v_id>', methods=['GET'])
@login_required
def api_venta_detalle(v_id):
    return jsonify({"error": "Detalle único no implementado (la vista general ya los incluye)."}), 501



@app.route('/api/ventas/<int:v_id>/anular', methods=['POST'])
@role_required('Administrador', 'Vendedor')
def api_venta_anular(v_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT estado, codigo_venta FROM ventas WHERE id = ?", (v_id,))
        venta = cursor.fetchone()
        if not venta:
            return jsonify({"error": "Venta no encontrada."}), 404
        if venta.estado == 'Anulada':
            return jsonify({"error": "Esta venta ya se encuentra anulada."}), 400

        cursor.execute("UPDATE ventas SET estado = 'Anulada' WHERE id = ?", (v_id,))
        
        cursor.execute("SELECT producto_id, cantidad FROM detalle_ventas WHERE venta_id = ?", (v_id,))
        detalles = cursor.fetchall()
        
        for det in detalles:
            cursor.execute("SELECT stock_actual AS stock FROM productos WHERE id = ?", (det.producto_id,))
            prod = cursor.fetchone()
            if prod:
                stock_anterior = prod.stock
                stock_posterior = stock_anterior + det.cantidad
                cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (stock_posterior, det.producto_id))
                
                cursor.execute("""
                    INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, motivo, usuario_id)
                    VALUES (?, 'DEVOLUCION_CLIENTE', ?, ?, ?, ?, ?)
                """, (det.producto_id, det.cantidad, stock_anterior, stock_posterior, f"Anulacion de venta {venta.codigo_venta}", session['user']['id']))
        
        # --- REVERSION CONTABLE ---
        cursor.execute("SELECT id FROM asientos_contables WHERE referencia_id = ? AND modulo_origen IN ('VENTAS', 'VENTAS_WEB')", (v_id,))
        asiento = cursor.fetchone()
        if asiento:
            cursor.execute("""
                INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
                VALUES (GETDATE(), ?, 'REVERSION_VENTA', ?, ?)
            """, (f"Anulacion Venta {venta.codigo_venta}", v_id, session['user']['id']))
            cursor.execute("SELECT @@IDENTITY AS id")
            new_asiento_id = cursor.fetchone().id
            
            cursor.execute("SELECT cuenta_id, debe, haber FROM movimientos_contables WHERE asiento_id = ?", (asiento.id,))
            movimientos = cursor.fetchall()
            for mov in movimientos:
                cursor.execute("""
                    INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber)
                    VALUES (?, ?, ?, ?)
                """, (new_asiento_id, mov.cuenta_id, mov.haber, mov.debe))
        # --------------------------
        
        conn.commit()
        return jsonify({"success": True, "mensaje": f"Venta {venta.codigo_venta} anulada correctamente. Stock retornado."})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# --- DEVOLUCIONES PARCIALES ---
@app.route('/api/ventas/<int:v_id>/devolucion', methods=['POST'])
@role_required('Administrador', 'Vendedor', 'Gerente de Operaciones')
def api_venta_devolucion(v_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        data = request.json or {}
        motivo = (data.get('motivo') or '').strip()
        items = data.get('items', [])

        if not motivo:
            return jsonify({"error": "Debes ingresar un motivo para la devolución."}), 400
        if not items:
            return jsonify({"error": "Debes seleccionar al menos un producto a devolver."}), 400

        # Validate venta exists and is not anulada
        cursor.execute("SELECT id, estado, codigo_venta FROM ventas WHERE id = ?", (v_id,))
        venta = cursor.fetchone()
        if not venta:
            return jsonify({"error": "Venta no encontrada."}), 404
        if venta.estado == 'Anulada':
            return jsonify({"error": "No se puede devolver productos de una venta anulada."}), 400

        # Get original sale details
        cursor.execute("""
            SELECT d.producto_id, d.cantidad, d.precio_unitario, p.costo
            FROM detalle_ventas d
            INNER JOIN productos p ON d.producto_id = p.id
            WHERE d.venta_id = ?
        """, (v_id,))
        detalles_originales = {row.producto_id: {'cantidad_vendida': row.cantidad, 'precio': float(row.precio_unitario), 'costo': float(row.costo)} for row in cursor.fetchall()}

        # Get already returned quantities for this sale
        cursor.execute("""
            SELECT dd.producto_id, SUM(dd.cantidad) AS ya_devuelto
            FROM detalle_devoluciones dd
            INNER JOIN devoluciones dev ON dd.devolucion_id = dev.id
            WHERE dev.venta_id = ?
            GROUP BY dd.producto_id
        """, (v_id,))
        ya_devueltos = {row.producto_id: row.ya_devuelto for row in cursor.fetchall()}

        actualiza_stock = data.get('actualiza_stock', True)

        # Validate each item
        total_devuelto = 0.0
        detalles_a_devolver = []
        for item in items:
            p_id = int(item.get('producto_id'))
            cant = int(item.get('cantidad', 0))

            if cant <= 0:
                continue

            if p_id not in detalles_originales:
                return jsonify({"error": f"El producto ID {p_id} no pertenece a esta venta."}), 400

            disponible = detalles_originales[p_id]['cantidad_vendida'] - ya_devueltos.get(p_id, 0)
            if cant > disponible:
                return jsonify({"error": f"Solo puedes devolver {disponible} unidades del producto ID {p_id}. Ya se devolvieron {ya_devueltos.get(p_id, 0)} anteriormente."}), 400

            precio = detalles_originales[p_id]['precio']
            costo = detalles_originales[p_id]['costo']
            subtotal = precio * cant
            total_devuelto += subtotal
            detalles_a_devolver.append((p_id, cant, precio, costo, subtotal))

        if not detalles_a_devolver:
            return jsonify({"error": "No se seleccionaron cantidades válidas para devolver."}), 400

        # Generate devolucion code
        import random, string
        random_str = ''.join(random.choices(string.digits, k=4))
        codigo_dev = f"DEV-{random_str}"

        # Insert devolucion header
        cursor.execute("""
            INSERT INTO devoluciones (venta_id, codigo_devolucion, motivo, total_devuelto, usuario_id)
            VALUES (?, ?, ?, ?, ?)
        """, (v_id, codigo_dev, motivo, total_devuelto, session['user']['id']))
        cursor.execute("SELECT @@IDENTITY AS id")
        dev_id = cursor.fetchone().id

        # Insert details, return stock, log inventory movements
        total_costo_devuelto = 0.0
        for (p_id, cant, precio, costo, subtotal) in detalles_a_devolver:
            cursor.execute("""
                INSERT INTO detalle_devoluciones (devolucion_id, producto_id, cantidad, precio_unitario, subtotal)
                VALUES (?, ?, ?, ?, ?)
            """, (dev_id, p_id, cant, precio, subtotal))

            # Return stock
            cursor.execute("SELECT stock_actual FROM productos WHERE id = ?", (p_id,))
            prod = cursor.fetchone()
            stock_anterior = prod.stock_actual
            
            if actualiza_stock:
                stock_posterior = stock_anterior + cant
                cursor.execute("UPDATE productos SET stock_actual = ? WHERE id = ?", (stock_posterior, p_id))
            else:
                stock_posterior = stock_anterior

            # Log inventory movement
            cursor.execute("""
                INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, motivo, usuario_id)
                VALUES (?, 'DEVOLUCION_CLIENTE', ?, ?, ?, ?, ?)
            """, (p_id, cant, stock_anterior, stock_posterior, f"Devolucion {codigo_dev} de venta {venta.codigo_venta}: {motivo}", session['user']['id']))

            total_costo_devuelto += costo * cant

        # --- ASIENTO CONTABLE DE REVERSION PARCIAL ---
        try:
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '1.1.01'")
            cta_caja = cursor.fetchone()
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '4.1.01'")
            cta_ventas = cursor.fetchone()
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '5.1.01'")
            cta_costo = cursor.fetchone()
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '1.1.04'")
            cta_inv = cursor.fetchone()

            if cta_caja and cta_ventas:
                cursor.execute("""
                    INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
                    VALUES (GETDATE(), ?, 'DEVOLUCION', ?, ?)
                """, (f"Devolucion {codigo_dev} de Venta {venta.codigo_venta}", v_id, session['user']['id']))
                cursor.execute("SELECT @@IDENTITY AS id")
                asiento_id = cursor.fetchone().id

                # Reverse the sale amount: Debit Ventas, Credit Caja
                cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_id, cta_ventas.id, total_devuelto))
                cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_caja.id, total_devuelto))

                # Reverse the cost: Debit Inventario, Credit Costo de Ventas
                if total_costo_devuelto > 0 and cta_costo and cta_inv:
                    cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_id, cta_inv.id, total_costo_devuelto))
                    cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_costo.id, total_costo_devuelto))
        except Exception:
            pass  # Don't fail the entire devolucion if accounting entries fail

        conn.commit()
        return jsonify({"success": True, "mensaje": f"Devolución {codigo_dev} procesada correctamente. {len(detalles_a_devolver)} producto(s) devuelto(s). Total: ${total_devuelto:.2f}", "codigo": codigo_dev})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# Get devoluciones for a specific sale
@app.route('/api/ventas/<int:v_id>/devoluciones', methods=['GET'])
@login_required
def api_venta_devoluciones(v_id):
    devoluciones = execute_query("""
        SELECT d.id, d.codigo_devolucion, d.fecha, d.motivo, d.total_devuelto, u.nombre_completo AS usuario
        FROM devoluciones d
        LEFT JOIN usuarios u ON d.usuario_id = u.id
        WHERE d.venta_id = ?
        ORDER BY d.fecha DESC
    """, (v_id,), fetchall=True)
    for dev in devoluciones:
        if hasattr(dev['fecha'], 'strftime'):
            dev['fecha'] = dev['fecha'].strftime('%Y-%m-%d %H:%M')
        dev['total_devuelto'] = float(dev['total_devuelto'])
    return jsonify(devoluciones)


@app.route('/api/ventas/<int:v_id>/productos_devueltos', methods=['GET'])
@login_required
def api_venta_productos_devueltos(v_id):
    # Returns a map of producto_id -> total_cantidad_devuelta
    devueltos = execute_query("""
        SELECT dd.producto_id, SUM(dd.cantidad) as total_devuelto
        FROM detalle_devoluciones dd
        INNER JOIN devoluciones d ON dd.devolucion_id = d.id
        WHERE d.venta_id = ?
        GROUP BY dd.producto_id
    """, (v_id,), fetchall=True)
    
    resultado = {}
    for item in devueltos:
        resultado[item['producto_id']] = item['total_devuelto']
        
    return jsonify(resultado)


# --- COMPRAS Y PROVEEDORES ---
@app.route('/api/proveedores', methods=['GET', 'POST'])
@login_required
def api_proveedores():
    if request.method == 'GET':
        provs = execute_query("SELECT id, nombre_empresa AS nombre, contacto_nombre AS contacto, telefono, email, activo FROM proveedores", fetchall=True)
        return jsonify(provs)

    if request.method == 'POST':
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones', 'Encargado de Compras y Proveedores']:
            return jsonify({"error": "No tienes permisos."}), 403
            
        data = request.json or {}
        nombre = data.get('nombre', '').strip()
        contacto = data.get('contacto', '').strip()
        telefono = data.get('telefono', '').strip()
        email = data.get('email', '').strip()

        if not nombre:
            return jsonify({"error": "Nombre del proveedor es obligatorio."}), 400

        try:
            execute_query("INSERT INTO proveedores (nombre_empresa, contacto_nombre, telefono, email) VALUES (?, ?, ?, ?)", 
                          (nombre, contacto, telefono, email), commit=True)
            return jsonify({"success": True, "mensaje": "Proveedor agregado"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/proveedores/<int:prov_id>', methods=['PUT'])
@login_required
def api_proveedor_update(prov_id):
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones', 'Encargado de Compras y Proveedores']:
        return jsonify({"error": "No tienes permisos."}), 403
        
    data = request.json or {}
    nombre = data.get('nombre', '').strip()
    contacto = data.get('contacto', '').strip()
    telefono = data.get('telefono', '').strip()
    email = data.get('email', '').strip()

    if not nombre:
        return jsonify({"error": "Nombre del proveedor es obligatorio."}), 400

    try:
        execute_query("UPDATE proveedores SET nombre_empresa = ?, contacto_nombre = ?, telefono = ?, email = ? WHERE id = ?", 
                      (nombre, contacto, telefono, email, prov_id), commit=True)
        return jsonify({"success": True, "mensaje": "Proveedor actualizado"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/proveedores/<int:prov_id>/estado', methods=['PUT'])
@login_required
def api_proveedor_estado(prov_id):
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones', 'Encargado de Compras y Proveedores']:
        return jsonify({"error": "No tienes permisos."}), 403
    
    data = request.json or {}
    nuevo_estado = 1 if data.get('activo') else 0
    
    try:
        execute_query("UPDATE proveedores SET activo = ? WHERE id = ?", (nuevo_estado, prov_id), commit=True)
        mensaje = "Proveedor activado" if nuevo_estado else "Proveedor inactivado"
        return jsonify({"success": True, "mensaje": mensaje})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/compras', methods=['GET', 'POST'])
@login_required
def api_compras():
    if request.method == 'GET':
        query_c = """
            SELECT c.id, c.codigo_compra, p.nombre_empresa AS proveedor_nombre, c.fecha_compra AS fecha, c.total
            FROM compras c
            INNER JOIN proveedores p ON c.proveedor_id = p.id
            ORDER BY c.id DESC
        """
        compras = execute_query(query_c, fetchall=True)
        for c in compras:
            if hasattr(c['fecha'], 'strftime'):
                c['fecha'] = c['fecha'].strftime('%Y-%m-%d')
            c['total'] = float(c['total'])
            
            detalles = execute_query("""
                SELECT p.id AS producto_id, p.nombre AS producto_nombre, d.cantidad, d.costo_unitario, d.subtotal
                FROM detalle_compras d
                INNER JOIN productos p ON d.producto_id = p.id
                WHERE d.compra_id = ?
            """, (c['id'],), fetchall=True)
            for d in detalles:
                d['costo_unitario'] = float(d['costo_unitario'])
                d['subtotal'] = float(d['subtotal'])
            c['detalles'] = detalles
            
        return jsonify(compras)

    if request.method == 'POST':
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones', 'Encargado de Compras y Proveedores']:
            return jsonify({"error": "No tienes permiso para registrar compras."}), 403
        
        data = request.json or {}
        prov_id = int(data.get('proveedor_id', 1))
        items = data.get('items', []) 

        if not items:
            return jsonify({"error": "Debe incluir al menos un producto recibido."}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            import random, string
            random_str = ''.join(random.choices(string.digits, k=4))
            compra_code = f"COM-#{random_str}"
            total_compra = 0.0
            
            cursor.execute("""
                INSERT INTO compras (codigo_compra, proveedor_id, usuario_id, fecha_compra, total)
                VALUES (?, ?, ?, GETDATE(), 0)
            """, (compra_code, prov_id, session['user']['id']))
            
            cursor.execute("SELECT @@IDENTITY AS id")
            compra_id = cursor.fetchone()[0]

            for item in items:
                p_id = int(item.get('producto_id'))
                cant = int(item.get('cantidad', 1))
                costo_u = float(item.get('costo_unitario', 0.0))

                cursor.execute("SELECT stock_actual, costo FROM productos WHERE id = ?", (p_id,))
                prod = cursor.fetchone()
                if not prod: continue
                
                real_costo = costo_u if costo_u > 0 else float(prod.costo)
                subt = real_costo * cant
                total_compra += subt
                
                cursor.execute("""
                    INSERT INTO detalle_compras (compra_id, producto_id, cantidad, costo_unitario, subtotal)
                    VALUES (?, ?, ?, ?, ?)
                """, (compra_id, p_id, cant, real_costo, subt))
                
                stock_post = prod.stock_actual + cant
                cursor.execute("UPDATE productos SET stock_actual = ?, costo = ? WHERE id = ?", (stock_post, real_costo, p_id))
                
                cursor.execute("""
                    INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, referencia_origen, motivo, usuario_id)
                    VALUES (?, 'ENTRADA_COMPRA', ?, ?, ?, ?, ?, ?)
                """, (p_id, cant, prod.stock_actual, stock_post, f"Compra {compra_code}", 'Entrada por compra a proveedor', session['user']['id']))

            cursor.execute("UPDATE compras SET total = ? WHERE id = ?", (total_compra, compra_id))

            # --- ASIENTO CONTABLE AUTOMÁTICO DE COMPRA ---
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '1.1.04'") # Inventario
            cta_inv = cursor.fetchone()[0]
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = '2.1.01'") # Proveedores
            cta_prov = cursor.fetchone()[0]

            cursor.execute("""
                INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
                VALUES (GETDATE(), ?, 'COMPRAS', ?, ?)
            """, (f"Compra {compra_code}", compra_id, session['user']['id']))
            cursor.execute("SELECT @@IDENTITY AS id")
            asiento_c_id = cursor.fetchone()[0]

            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_c_id, cta_inv, total_compra))
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_c_id, cta_prov, total_compra))

            conn.commit()
            return jsonify({"success": True, "mensaje": "Compra registrada."}), 201

        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            return jsonify({"error": str(e)}), 500

# --- REPORTES Y CONTABILIDAD ---
@app.route('/api/reportes', methods=['GET'])
@login_required
def api_reportes():
    if session['user']['rol'] not in ['Administrador', 'Contador', 'Gerente Administrativo y Financiero']:
        return jsonify({"error": "Acceso reservado a Administrador, Gerencia y Contabilidad."}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        rango_param = request.args.get('rango')
        fecha_inicio_param = request.args.get('fecha_inicio')
        fecha_fin_param = request.args.get('fecha_fin')
        mes_param = request.args.get('mes')
        anio_param = request.args.get('anio')
        criterio_abc = request.args.get('criterio_abc', 'inversion')
        comparar_modo = request.args.get('comparar') in ['1', 'true', 'si']

        filtro_a = construir_filtro_periodo(
            rango=rango_param,
            mes=mes_param,
            anio=anio_param,
            fecha_inicio=fecha_inicio_param,
            fecha_fin=fecha_fin_param
        )

        if comparar_modo:
            rango_b = request.args.get('rango2')
            mes_b = request.args.get('mes2')
            anio_b = request.args.get('anio2')
            fecha_ini_b = request.args.get('fecha_inicio2')
            fecha_fin_b = request.args.get('fecha_fin2')
            filtro_b = construir_filtro_periodo(
                rango=rango_b,
                mes=mes_b,
                anio=anio_b,
                fecha_inicio=fecha_ini_b,
                fecha_fin=fecha_fin_b
            )
            resultado = comparar_dos_periodos(cursor, filtro_a, filtro_b, criterio_abc=criterio_abc)
            return jsonify(resultado)

        agrupar_meses = (rango_param == 'anio' or anio_param is not None or request.args.get('agrupar_meses') == '1')
        resultado = procesar_reporte_completo(cursor, filtro_a, criterio_abc=criterio_abc, agrupar_meses=agrupar_meses)

        # Campos de retrocompatibilidad
        k = resultado["kpis"]
        resultado["ventas_totales_monto"] = k["ventas_totales_monto"]
        resultado["ventas_totales_conteo"] = k["ventas_totales_conteo"]
        resultado["compras_totales_monto"] = k["compras_totales_monto"]
        resultado["margen_bruto_estimado"] = k["utilidad_bruta"]
        resultado["rotacion_inventario"] = k["rotacion_monetaria_costo"]
        resultado["unidades_vendidas_total"] = k["unidades_vendidas_total"]
        resultado["productos_bajo_stock"] = resultado["alertas_stock_minimo"]
        resultado["alerta_stock_bajo_conteo"] = len(resultado["alertas_stock_minimo"])
        resultado["top_productos"] = resultado["ranking_unidades"]
        resultado["bottom_productos"] = [p for p in resultado["rotacion_abc"]["productos"] if p["unidades_vendidas"] == 0][:20]

        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

@app.route('/api/reportes/exportar/excel', methods=['GET'])
@login_required
def api_exportar_reporte_excel():
    if session['user']['rol'] not in ['Administrador', 'Contador', 'Gerente Administrativo y Financiero']:
        return jsonify({"error": "Acceso reservado a Administrador, Gerencia y Contabilidad."}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        rango_param = request.args.get('rango')
        fecha_inicio_param = request.args.get('fecha_inicio')
        fecha_fin_param = request.args.get('fecha_fin')
        mes_param = request.args.get('mes')
        anio_param = request.args.get('anio')
        criterio_abc = request.args.get('criterio_abc', 'inversion')

        filtro = construir_filtro_periodo(
            rango=rango_param,
            mes=mes_param,
            anio=anio_param,
            fecha_inicio=fecha_inicio_param,
            fecha_fin=fecha_fin_param
        )
        datos = procesar_reporte_completo(cursor, filtro, criterio_abc=criterio_abc, agrupar_meses=True)
        excel_buf = generar_excel_informe_workbook(datos)

        periodo_limpio = filtro["texto"].replace(" ", "_").replace("/", "-")
        nombre_archivo = f"Reporte_Comercial_{periodo_limpio}.xlsx"

        return send_file(
            excel_buf,
            as_attachment=True,
            download_name=nombre_archivo,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()


# ==============================================================================
# MÓDULO CONTABLE Y ESTADOS FINANCIEROS
# ==============================================================================

@app.route('/api/finanzas/cuentas', methods=['GET', 'POST'])
@login_required
def api_cuentas_contables():
    if session['user']['rol'] not in ['Administrador', 'Contador', 'Gerente Administrativo y Financiero']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403
    
    if request.method == 'GET':
        try:
            cuentas = execute_query("SELECT * FROM cuentas_contables ORDER BY codigo ASC", fetchall=True)
            return jsonify(cuentas)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
        if session['user']['rol'] == 'Contador':
            return jsonify({"error": "No tienes permiso para crear cuentas."}), 403
        data = request.json or {}
        codigo = data.get('codigo')
        nombre = data.get('nombre')
        clasificacion = data.get('clasificacion')
        naturaleza = data.get('naturaleza')
        descripcion = data.get('descripcion', '')
        
        if not codigo or not nombre or not clasificacion or not naturaleza:
            return jsonify({"error": "Faltan campos obligatorios"}), 400
            
        try:
            query = "INSERT INTO cuentas_contables (codigo, nombre, clasificacion, naturaleza, descripcion) VALUES (?, ?, ?, ?, ?)"
            execute_query(query, params=(codigo, nombre, clasificacion, naturaleza, descripcion), commit=True)
            return jsonify({"success": True, "mensaje": "Cuenta creada exitosamente"}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/finanzas/cuentas/<int:id>', methods=['DELETE'])
@login_required
def api_cuentas_contables_delete(id):
    if session['user']['rol'] not in ['Administrador', 'Contador', 'Gerente Administrativo y Financiero']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403
    try:
        movs = execute_query("SELECT TOP 1 id FROM movimientos_contables WHERE cuenta_id = ?", (id,), fetchall=True)
        if movs:
            return jsonify({"error": "No se puede eliminar la cuenta porque tiene movimientos contables asociados."}), 400
            
        execute_query("DELETE FROM cuentas_contables WHERE id = ?", (id,), commit=True)
        return jsonify({"success": True, "mensaje": "Cuenta eliminada exitosamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/finanzas/asientos', methods=['GET', 'POST'])
@login_required
def api_asientos_contables():
    if session['user']['rol'] not in ['Administrador', 'Contador', 'Gerente Administrativo y Financiero']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403
    
    if request.method == 'GET':
        try:
            start_date = request.args.get('start')
            end_date = request.args.get('end')
            
            where_clause = ""
            params = []
            
            if start_date and end_date:
                where_clause = "WHERE CAST(fecha AS DATE) >= ? AND CAST(fecha AS DATE) <= ?"
                params.extend([start_date, end_date])
            elif start_date:
                where_clause = "WHERE CAST(fecha AS DATE) >= ?"
                params.append(start_date)
            elif end_date:
                where_clause = "WHERE CAST(fecha AS DATE) <= ?"
                params.append(end_date)
                
            query_a = f"SELECT id, fecha, concepto, modulo_origen, usuario_id, created_at FROM asientos_contables {where_clause} ORDER BY fecha DESC, id DESC"
            asientos = execute_query(query_a, params=tuple(params), fetchall=True)
            for a in asientos:
                if hasattr(a['fecha'], 'strftime'):
                    a['fecha'] = a['fecha'].strftime('%Y-%m-%d')
                if hasattr(a['created_at'], 'strftime'):
                    a['created_at'] = a['created_at'].strftime('%Y-%m-%d %H:%M:%S')
                
                movs = execute_query("""
                    SELECT m.id, c.codigo, c.nombre AS cuenta, m.debe, m.haber 
                    FROM movimientos_contables m
                    INNER JOIN cuentas_contables c ON m.cuenta_id = c.id
                    WHERE m.asiento_id = ?
                """, (a['id'],), fetchall=True)
                for m in movs:
                    m['debe'] = float(m['debe'])
                    m['haber'] = float(m['haber'])
                a['movimientos'] = movs
            return jsonify(asientos)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
        data = request.json or {}
        fecha = data.get('fecha')
        concepto = data.get('concepto')
        movimientos = data.get('movimientos', [])
        
        if not fecha or not concepto or not movimientos:
            return jsonify({"error": "Faltan datos obligatorios para el asiento."}), 400

        total_debe = sum(float(m.get('debe', 0)) for m in movimientos)
        total_haber = sum(float(m.get('haber', 0)) for m in movimientos)
        
        if round(total_debe, 2) != round(total_haber, 2):
            return jsonify({"error": "El asiento no cuadra. Debe y Haber deben ser iguales."}), 400

        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Insertar Asiento
            cursor.execute("""
                INSERT INTO asientos_contables (fecha, concepto, modulo_origen, usuario_id) 
                VALUES (?, ?, 'MANUAL', ?)
            """, (fecha, concepto, session['user']['id']))
            
            cursor.execute("SELECT @@IDENTITY AS id")
            asiento_id = cursor.fetchone()[0]
            
            # Insertar Movimientos
            for m in movimientos:
                cuenta_id = int(m['cuenta_id'])
                debe = float(m.get('debe', 0))
                haber = float(m.get('haber', 0))
                if debe > 0 or haber > 0:
                    cursor.execute("""
                        INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber)
                        VALUES (?, ?, ?, ?)
                    """, (asiento_id, cuenta_id, debe, haber))
                    
            conn.commit()
            return jsonify({"success": True, "mensaje": "Asiento contable registrado exitosamente."}), 201
        except Exception as e:
            if 'conn' in locals(): conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            if 'conn' in locals(): conn.close()


@app.route('/api/finanzas/libro_mayor', methods=['GET'])
@login_required
@role_required('Administrador', 'Gerente Administrativo y Financiero', 'Contador')
def api_libro_mayor():
    cuenta_id = request.args.get('cuenta_id')
    fecha_inicio = request.args.get('fecha_inicio')
    fecha_fin = request.args.get('fecha_fin')
    
    if not cuenta_id:
        return jsonify({"error": "Debe especificar una cuenta."}), 400
        
    try:
        # Get account details
        cta = execute_query("SELECT id, codigo, nombre, naturaleza FROM cuentas_contables WHERE id = ?", (cuenta_id,), fetchone=True)
        if not cta:
            return jsonify({"error": "Cuenta no encontrada."}), 404
            
        naturaleza = cta['naturaleza']
        
        # Calculate initial balance before fecha_inicio
        saldo_inicial = 0.0
        if fecha_inicio:
            query_inicial = '''
                SELECT ISNULL(SUM(m.debe), 0) as total_debe, ISNULL(SUM(m.haber), 0) as total_haber 
                FROM movimientos_contables m
                INNER JOIN asientos_contables a ON a.id = m.asiento_id
                WHERE m.cuenta_id = ? AND a.fecha < ?
            '''
            inicial_result = execute_query(query_inicial, (cuenta_id, fecha_inicio), fetchone=True)
            if naturaleza == 'Deudora':
                saldo_inicial = float(inicial_result['total_debe']) - float(inicial_result['total_haber'])
            else:
                saldo_inicial = float(inicial_result['total_haber']) - float(inicial_result['total_debe'])
                
        # Get movements in range
        where_clause = "m.cuenta_id = ?"
        params = [cuenta_id]
        if fecha_inicio:
            where_clause += " AND a.fecha >= ?"
            params.append(fecha_inicio)
        if fecha_fin:
            where_clause += " AND a.fecha <= ?"
            params.append(fecha_fin)
            
        query_movs = f'''
            SELECT a.id as asiento_id, a.fecha, a.concepto, m.debe, m.haber
            FROM movimientos_contables m
            INNER JOIN asientos_contables a ON a.id = m.asiento_id
            WHERE {where_clause}
            ORDER BY a.fecha ASC, a.id ASC
        '''
        movimientos = execute_query(query_movs, tuple(params), fetchall=True)
        
        saldo_actual = saldo_inicial
        movs_list = []
        for m in movimientos:
            debe = float(m['debe'])
            haber = float(m['haber'])
            if naturaleza == 'Deudora':
                saldo_actual += (debe - haber)
            else:
                saldo_actual += (haber - debe)
                
            movs_list.append({
                "asiento_id": m['asiento_id'],
                "fecha": m['fecha'].isoformat() if hasattr(m['fecha'], 'isoformat') else str(m['fecha']),
                "concepto": m['concepto'],
                "debe": debe,
                "haber": haber,
                "saldo": saldo_actual
            })
            
        return jsonify({
            "cuenta": {
                "codigo": cta['codigo'],
                "nombre": cta['nombre'],
                "naturaleza": naturaleza
            },
            "saldo_inicial": saldo_inicial,
            "movimientos": movs_list,
            "saldo_final": saldo_actual
        })
    except Exception as e:
        print("Error en libro mayor:", e)
        return jsonify({"error": str(e)}), 500


@app.route('/api/finanzas/balance_comprobacion', methods=['GET'])
@login_required
def api_balance_comprobacion():
    if session['user']['rol'] not in ['Administrador', 'Contador', 'Gerente Administrativo y Financiero']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403
    try:
        query = """
            SELECT c.codigo, c.nombre, c.clasificacion, c.naturaleza,
                   SUM(m.debe) AS total_debe, SUM(m.haber) AS total_haber
            FROM cuentas_contables c
            LEFT JOIN movimientos_contables m ON c.id = m.cuenta_id
            GROUP BY c.codigo, c.nombre, c.clasificacion, c.naturaleza
            HAVING SUM(m.debe) > 0 OR SUM(m.haber) > 0
            ORDER BY c.codigo ASC
        """
        filas = execute_query(query, fetchall=True)
        resultados = []
        suma_debe = 0
        suma_haber = 0
        for f in filas:
            debe = float(f['total_debe'] or 0)
            haber = float(f['total_haber'] or 0)
            
            saldo_deudor = 0
            saldo_acreedor = 0
            
            if f['naturaleza'] == 'Deudora':
                saldo_deudor = debe - haber
                if saldo_deudor < 0:
                    saldo_acreedor = abs(saldo_deudor)
                    saldo_deudor = 0
            else:
                saldo_acreedor = haber - debe
                if saldo_acreedor < 0:
                    saldo_deudor = abs(saldo_acreedor)
                    saldo_acreedor = 0
                    
            resultados.append({
                "codigo": f['codigo'],
                "cuenta": f['nombre'],
                "clasificacion": f['clasificacion'],
                "debe": saldo_deudor,
                "haber": saldo_acreedor
            })
            suma_debe += saldo_deudor
            suma_haber += saldo_acreedor

        return jsonify({
            "cuentas": resultados,
            "totales": {
                "debe": suma_debe,
                "haber": suma_haber
            }
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/finanzas/estado_resultados', methods=['GET'])
@login_required
def api_estado_resultados():
    if session['user']['rol'] not in ['Administrador', 'Contador', 'Gerente Administrativo y Financiero']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403
    try:
        hoy = obtener_fecha_hoy_nicaragua()
        end_date = request.args.get('end') or hoy
        start_date = request.args.get('start') or f"{end_date[:7]}-01"
        if start_date > end_date:
            start_date = min(start_date, end_date)
        
        where_clause = "AND CAST(a.fecha AS DATE) >= ? AND CAST(a.fecha AS DATE) <= ?"
        params = [start_date, end_date]

        query = f"""
            SELECT c.codigo, c.nombre, c.clasificacion, c.naturaleza,
                   SUM(m.debe) AS total_debe, SUM(m.haber) AS total_haber
            FROM cuentas_contables c
            INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
            INNER JOIN asientos_contables a ON a.id = m.asiento_id
            WHERE c.clasificacion IN ('Ingresos', 'Costo', 'Gasto') {where_clause}
            GROUP BY c.codigo, c.nombre, c.clasificacion, c.naturaleza
            ORDER BY c.clasificacion DESC, c.codigo ASC
        """
        filas = execute_query(query, params=tuple(params), fetchall=True)
        
        ingresos = []
        total_ingresos = 0
        costos = []
        total_costos = 0
        gastos = []
        total_gastos = 0
        
        for f in filas:
            debe = float(f['total_debe'] or 0)
            haber = float(f['total_haber'] or 0)
            saldo = (haber - debe) if f['naturaleza'] == 'Acreedora' else (debe - haber)
            
            if f['clasificacion'] == 'Ingresos':
                ingresos.append({"cuenta": f['nombre'], "saldo": saldo})
                total_ingresos += saldo
            elif f['clasificacion'] == 'Costo':
                costos.append({"cuenta": f['nombre'], "saldo": saldo})
                total_costos += saldo
            elif f['clasificacion'] == 'Gasto':
                gastos.append({"cuenta": f['nombre'], "saldo": saldo})
                total_gastos += saldo

        utilidad_bruta = total_ingresos - total_costos
        utilidad_neta = utilidad_bruta - total_gastos

        return jsonify({
            "periodo": {
                "start": start_date,
                "end": end_date
            },
            "ingresos": ingresos,
            "total_ingresos": total_ingresos,
            "costos": costos,
            "total_costos": total_costos,
            "utilidad_bruta": utilidad_bruta,
            "gastos": gastos,
            "total_gastos": total_gastos,
            "utilidad_neta": utilidad_neta
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/finanzas/balance_general', methods=['GET'])
@login_required
def api_balance_general():
    if session['user']['rol'] not in ['Administrador', 'Contador', 'Gerente Administrativo y Financiero']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403
    try:
        hoy = obtener_fecha_hoy_nicaragua()
        end_date = request.args.get('end') or hoy
        
        where_clause_a = "AND CAST(a.fecha AS DATE) <= ?"
        params_a = [end_date]

        # Calcular Utilidad Neta acumulada hasta la fecha de corte (para integrarla en Patrimonio)
        query_er = f"""
            SELECT c.clasificacion, c.naturaleza, SUM(m.debe) AS d, SUM(m.haber) AS h
            FROM cuentas_contables c
            INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
            INNER JOIN asientos_contables a ON a.id = m.asiento_id
            WHERE c.clasificacion IN ('Ingresos', 'Costo', 'Gasto') {where_clause_a}
            GROUP BY c.clasificacion, c.naturaleza
        """
        filas_er = execute_query(query_er, params=tuple(params_a), fetchall=True)
        utilidad_neta = 0
        for f in filas_er:
            saldo = (float(f['h'])-float(f['d'])) if f['naturaleza'] == 'Acreedora' else (float(f['d'])-float(f['h']))
            if f['clasificacion'] == 'Ingresos': utilidad_neta += saldo
            else: utilidad_neta -= saldo

        # Obtener cuentas de balance
        query_bg = f"""
            SELECT c.codigo, c.nombre, c.clasificacion, c.naturaleza,
                   SUM(m.debe) AS d, SUM(m.haber) AS h
            FROM cuentas_contables c
            INNER JOIN movimientos_contables m ON c.id = m.cuenta_id
            INNER JOIN asientos_contables a ON a.id = m.asiento_id
            WHERE c.clasificacion NOT IN ('Ingresos', 'Costo', 'Gasto') {where_clause_a}
            GROUP BY c.codigo, c.nombre, c.clasificacion, c.naturaleza
            ORDER BY c.clasificacion ASC, c.codigo ASC
        """
        filas_bg = execute_query(query_bg, params=tuple(params_a), fetchall=True)
        
        activos_corrientes = []
        activos_no_corrientes = []
        pasivos_corrientes = []
        pasivos_no_corrientes = []
        patrimonio = []
        
        total_activos = 0
        total_pasivos = 0
        total_patrimonio = utilidad_neta # Inicializamos con la utilidad acumulada
        
        for f in filas_bg:
            debe = float(f['d'] or 0)
            haber = float(f['h'] or 0)
            saldo = (haber - debe) if f['naturaleza'] == 'Acreedora' else (debe - haber)
            
            # Ajuste para cuentas contra-activo (ej. Depreciación acumulada) que son naturaleza Acreedora pero van en Activos
            if f['clasificacion'] == 'Activo no corriente - contraactivo':
                saldo = -abs(saldo) # Se resta del activo
                
            obj = {"cuenta": f['nombre'], "saldo": saldo}
            
            if 'Activo corriente' in f['clasificacion']:
                activos_corrientes.append(obj)
                total_activos += saldo
            elif 'Activo no corriente' in f['clasificacion']:
                activos_no_corrientes.append(obj)
                total_activos += saldo
            elif 'Pasivo corriente' in f['clasificacion']:
                pasivos_corrientes.append(obj)
                total_pasivos += saldo
            elif 'Pasivo no corriente' in f['clasificacion']:
                pasivos_no_corrientes.append(obj)
                total_pasivos += saldo
            elif 'Patrimonio' in f['clasificacion']:
                patrimonio.append(obj)
                total_patrimonio += saldo

        patrimonio.append({"cuenta": "Utilidad neta acumulada a la fecha", "saldo": utilidad_neta})

        return jsonify({
            "fecha_corte": end_date,
            "activos": {
                "corrientes": activos_corrientes,
                "no_corrientes": activos_no_corrientes,
                "total": total_activos
            },
            "pasivos": {
                "corrientes": pasivos_corrientes,
                "no_corrientes": pasivos_no_corrientes,
                "total": total_pasivos
            },
            "patrimonio": {
                "cuentas": patrimonio,
                "total": total_patrimonio
            },
            "total_pasivo_patrimonio": total_pasivos + total_patrimonio
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# RECURSOS HUMANOS Y NÓMINA
# Roles permitidos: Administrador, Responsable de Recursos Humanos
# ==============================================================================
# ROLES_RRHH se comparte con las rutas complementarias.


# --- GESTIÓN DE CARGOS (RF63) ---
@app.route('/api/cargos', methods=['GET', 'POST'])
@login_required
def api_cargos():
    """GET: Lista cargos disponibles. POST: Registrar nuevo cargo."""
    if request.method == 'GET':
        query = """
            SELECT id, nombre_cargo, ISNULL(descripcion, '') AS descripcion,
                   ISNULL(salario_base_sugerido, 0.00) AS salario_base_sugerido,
                   activo
            FROM cargos
            ORDER BY nombre_cargo ASC
        """
        cargos = execute_query(query, fetchall=True)
        for c in cargos:
            c['salario_base_sugerido'] = float(c['salario_base_sugerido'])
            c['activo'] = bool(c['activo'])
        return jsonify(cargos)

    if request.method == 'POST':
        if session['user']['rol'] not in ROLES_RRHH:
            return jsonify({"error": "No tienes permisos para gestionar cargos."}), 403

        data = request.json or {}
        nombre_cargo = data.get('nombre_cargo', '').strip()
        descripcion = data.get('descripcion', '').strip()
        salario = float(data.get('salario_base_sugerido', 0))

        if not nombre_cargo:
            return jsonify({"error": "El nombre del cargo es obligatorio."}), 400

        try:
            execute_query(
                "INSERT INTO cargos (nombre_cargo, descripcion, salario_base_sugerido, activo) VALUES (?, ?, ?, 1)",
                (nombre_cargo, descripcion, salario),
                commit=True
            )
            return jsonify({"success": True, "mensaje": f"Cargo '{nombre_cargo}' registrado exitosamente."}), 201
        except Exception as e:
            return jsonify({"error": f"Error registrando cargo: {str(e)}"}), 500


@app.route('/api/cargos/<int:cargo_id>', methods=['PUT', 'PATCH'])
@login_required
def api_cargo_editar(cargo_id):
    """PUT: Actualizar cargo. PATCH: Cambiar estado activo/inactivo."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403

    if request.method == 'PUT':
        data = request.json or {}
        nombre_cargo = data.get('nombre_cargo', '').strip()
        descripcion = data.get('descripcion', '').strip()
        salario = float(data.get('salario_base_sugerido', 0))

        if not nombre_cargo:
            return jsonify({"error": "El nombre del cargo es obligatorio."}), 400

        try:
            rows = execute_query(
                "UPDATE cargos SET nombre_cargo=?, descripcion=?, salario_base_sugerido=? WHERE id=?",
                (nombre_cargo, descripcion, salario, cargo_id),
                commit=True
            )
            if rows == 0:
                return jsonify({"error": "Cargo no encontrado."}), 404
            return jsonify({"success": True, "mensaje": "Cargo actualizado exitosamente."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == 'PATCH':
        data = request.json or {}
        nuevo_estado = 1 if data.get('activo', True) else 0
        try:
            execute_query("UPDATE cargos SET activo=? WHERE id=?", (nuevo_estado, cargo_id), commit=True)
            estado_txt = 'activado' if nuevo_estado else 'desactivado'
            return jsonify({"success": True, "mensaje": f"Cargo {estado_txt} correctamente."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/api/empleados', methods=['GET', 'POST'])
@login_required
def api_empleados():
    """GET: Lista empleados activos. POST: Registrar nuevo empleado."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos para consultar empleados."}), 403
    if request.method == 'GET':
        query = """
            SELECT id, nombre_completo, identificacion, num_inss, cargo,
                   salario_base, fecha_ingreso, activo,
                   ISNULL(dias_vacaciones_disponibles, 0) AS dias_vacaciones_disponibles,
                   ISNULL(telefono, '') AS telefono,
                   ISNULL(email, '') AS email,
                   ISNULL(observaciones, '') AS observaciones
            FROM empleados
            ORDER BY id ASC
        """
        empleados = execute_query(query, fetchall=True)
        for e in empleados:
            e['salario_base'] = float(e['salario_base'])
            e['dias_vacaciones_disponibles'] = float(e['dias_vacaciones_disponibles'])
            if e.get('fecha_ingreso'):
                e['fecha_ingreso'] = str(e['fecha_ingreso'])[:10]  # YYYY-MM-DD
        return jsonify(empleados)

    if request.method == 'POST':
        if session['user']['rol'] not in ROLES_RRHH:
            return jsonify({"error": "No tienes permisos para registrar empleados."}), 403

        data = request.json or {}
        nombre = data.get('nombre_completo', '').strip()
        identificacion = data.get('identificacion', '').strip()
        num_inss = data.get('num_inss', '').strip()
        cargo = data.get('cargo', '').strip()
        salario_base = float(data.get('salario_base', 0))
        fecha_ingreso = data.get('fecha_ingreso', '')
        telefono = data.get('telefono', '').strip()
        email = data.get('email', '').strip()
        observaciones = data.get('observaciones', '').strip()

        if not nombre or salario_base <= 0:
            return jsonify({"error": "Nombre y Salario base válidos son obligatorios."}), 400

        dias_vac = float(data.get('dias_vacaciones_disponibles', 0) or 0)

        try:
            execute_query(
                """INSERT INTO empleados
                   (nombre_completo, identificacion, num_inss, cargo, salario_base,
                    fecha_ingreso, telefono, email, observaciones, dias_vacaciones_disponibles)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (nombre, identificacion, num_inss, cargo, salario_base,
                 fecha_ingreso, telefono, email, observaciones, dias_vac),
                commit=True
            )
            return jsonify({"success": True, "mensaje": "Empleado registrado exitosamente."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/api/empleados/<int:emp_id>', methods=['PUT', 'PATCH'])
@login_required
def api_empleado_editar(emp_id):
    """PUT: Editar datos de empleado. PATCH: Cambiar estado activo/inactivo."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403

    if request.method == 'PUT':
        data = request.json or {}
        nombre = data.get('nombre_completo', '').strip()
        identificacion = data.get('identificacion', '').strip()
        num_inss = data.get('num_inss', '').strip()
        cargo = data.get('cargo', '').strip()
        salario_base = float(data.get('salario_base', 0))
        fecha_ingreso = data.get('fecha_ingreso', '')
        telefono = data.get('telefono', '').strip()
        email = data.get('email', '').strip()
        observaciones = data.get('observaciones', '').strip()

        if not nombre or salario_base <= 0:
            return jsonify({"error": "Nombre y Salario base son obligatorios."}), 400

        try:
            rows = execute_query(
                """UPDATE empleados
                   SET nombre_completo=?, identificacion=?, num_inss=?, cargo=?,
                       salario_base=?, fecha_ingreso=?, telefono=?, email=?, observaciones=?
                   WHERE id=?""",
                (nombre, identificacion, num_inss, cargo, salario_base,
                 fecha_ingreso, telefono, email, observaciones, emp_id),
                commit=True
            )
            if rows == 0:
                return jsonify({"error": "Empleado no encontrado."}), 404

            # Actualizar saldo de vacaciones si viene en la petición
            dias_vac_val = data.get('dias_vacaciones_disponibles')
            if dias_vac_val is not None:
                try:
                    dias_vac = round(float(dias_vac_val), 2)
                    execute_query(
                        "UPDATE empleados SET dias_vacaciones_disponibles = ? WHERE id = ?",
                        (dias_vac, emp_id), commit=True
                    )
                except (ValueError, TypeError):
                    pass

            return jsonify({"success": True, "mensaje": "Empleado actualizado."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == 'PATCH':
        # Cambiar estado activo <-> inactivo
        data = request.json or {}
        nuevo_estado = 1 if data.get('activo', True) else 0
        try:
            execute_query(
                "UPDATE empleados SET activo=? WHERE id=?",
                (nuevo_estado, emp_id), commit=True
            )
            estado_txt = 'activado' if nuevo_estado else 'inactivado'
            return jsonify({"success": True, "mensaje": f"Empleado {estado_txt} correctamente."})
        except Exception as e:
            return jsonify({"error": str(e)}), 500


# --- MOVIMIENTOS LABORALES (vacaciones, permisos, faltas) ---
@app.route('/api/movimientos-laborales', methods=['GET', 'POST'])
@login_required
def api_movimientos_laborales():
    """GET: Listar movimientos (opcionalmente por empleado). POST: Registrar uno nuevo."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403

    if request.method == 'GET':
        emp_id = request.args.get('empleado_id')
        if emp_id:
            query = """
                SELECT ml.id, ml.empleado_id, e.nombre_completo AS empleado, ml.tipo,
                       ml.fecha_inicio, ml.fecha_fin, ml.dias_tomados, ml.observacion, ml.created_at,
                       ISNULL(ml.afecta_septimo_dia, 0) AS afecta_septimo_dia
                FROM movimientos_laborales ml
                JOIN empleados e ON ml.empleado_id = e.id
                WHERE ml.empleado_id = ?
                ORDER BY ml.fecha_inicio DESC
            """
            movimientos = execute_query(query, (emp_id,), fetchall=True)
        else:
            query = """
                SELECT ml.id, ml.empleado_id, e.nombre_completo AS empleado, ml.tipo,
                       ml.fecha_inicio, ml.fecha_fin, ml.dias_tomados, ml.observacion, ml.created_at,
                       ISNULL(ml.afecta_septimo_dia, 0) AS afecta_septimo_dia
                FROM movimientos_laborales ml
                JOIN empleados e ON ml.empleado_id = e.id
                ORDER BY ml.created_at DESC
            """
            movimientos = execute_query(query, fetchall=True)
        # Serializar fechas y números
        for m in movimientos:
            if m.get('fecha_inicio'): m['fecha_inicio'] = str(m['fecha_inicio'])[:10]
            if m.get('fecha_fin'):    m['fecha_fin']    = str(m['fecha_fin'])[:10]
            if m.get('created_at'):   m['created_at']   = str(m['created_at'])
            if m.get('dias_tomados') is not None: m['dias_tomados'] = float(m['dias_tomados'])
            m['afecta_septimo_dia'] = bool(m.get('afecta_septimo_dia', False))
        return jsonify(movimientos)

    if request.method == 'POST':
        if session['user']['rol'] not in ROLES_RRHH:
            return jsonify({"error": "No tienes permisos para registrar movimientos laborales."}), 403

        data = request.json or {}
        empleado_id  = data.get('empleado_id')
        tipo         = data.get('tipo', '')
        fecha_inicio = data.get('fecha_inicio', '')
        fecha_fin    = data.get('fecha_fin', '')
        dias_tomados = float(data.get('dias_tomados', 0))
        observacion  = data.get('observacion', '').strip()
        afecta_septimo_dia = 1 if (tipo == 'FALTA' and bool(data.get('afecta_septimo_dia', False))) else 0

        if not empleado_id or not tipo or not fecha_inicio or not fecha_fin or dias_tomados <= 0:
            return jsonify({"error": "Todos los campos son obligatorios y los días deben ser mayores a 0."}), 400

        tipos_validos = ['VACACIONES', 'PERMISO_CON_GOCE', 'PERMISO_SIN_GOCE', 'FALTA']
        if tipo not in tipos_validos:
            return jsonify({"error": f"Tipo inválido. Use: {tipos_validos}"}), 400

        try:
            # Control de saldo de vacaciones (RF68)
            if tipo == 'VACACIONES':
                emp = execute_query(
                    "SELECT nombre_completo, ISNULL(dias_vacaciones_disponibles, 0) AS saldo FROM empleados WHERE id = ?",
                    (empleado_id,), fetchone=True
                )
                if not emp:
                    return jsonify({"error": "Empleado no encontrado."}), 404
                saldo_actual = float(emp['saldo'])
                if dias_tomados > saldo_actual:
                    return jsonify({
                        "error": f"Saldo insuficiente: {emp['nombre_completo']} solo tiene {saldo_actual:.2f} días de vacaciones disponibles (solicitó {dias_tomados:.1f} días)."
                    }), 400

            execute_query(
                """INSERT INTO movimientos_laborales
                   (empleado_id, tipo, fecha_inicio, fecha_fin, dias_tomados, observacion, afecta_septimo_dia)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (empleado_id, tipo, fecha_inicio, fecha_fin, dias_tomados, observacion, afecta_septimo_dia),
                commit=True
            )

            # Si es vacaciones, descontar días disponibles del empleado
            if tipo == 'VACACIONES':
                execute_query(
                    "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles - ? WHERE id = ?",
                    (dias_tomados, empleado_id), commit=True
                )
            return jsonify({"success": True, "mensaje": "Movimiento laboral registrado exitosamente."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500


@app.route('/api/movimientos-laborales/<int:mov_id>', methods=['PUT', 'DELETE'])
@login_required
def api_movimiento_laboral_detalle(mov_id):
    """PUT: Actualizar movimiento laboral. DELETE: Eliminar movimiento laboral (reintegrando días si fue vacaciones)."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id, empleado_id, tipo, dias_tomados FROM movimientos_laborales WHERE id = ?", (mov_id,))
        mov = cursor.fetchone()
        if not mov:
            conn.close()
            return jsonify({"error": "Movimiento laboral no encontrado."}), 404

        m_id, emp_id, tipo, dias_tomados = mov[0], mov[1], mov[2], float(mov[3])

        if request.method == 'DELETE':
            # Si era tipo VACACIONES, reintegrar los días al saldo disponible del empleado
            if tipo == 'VACACIONES':
                cursor.execute(
                    "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles + ? WHERE id = ?",
                    (dias_tomados, emp_id)
                )
            cursor.execute("DELETE FROM movimientos_laborales WHERE id = ?", (mov_id,))
            conn.commit()
            conn.close()
            return jsonify({"success": True, "mensaje": "Movimiento laboral eliminado exitosamente."})

        if request.method == 'PUT':
            data = request.json or {}
            nuevo_emp_id = int(data.get('empleado_id', emp_id))
            nuevo_tipo = data.get('tipo', tipo)
            nueva_fecha_inicio = data.get('fecha_inicio')
            nueva_fecha_fin = data.get('fecha_fin')
            nuevos_dias = float(data.get('dias_tomados', dias_tomados))
            nueva_obs = data.get('observacion', '').strip()
            afecta_septimo_dia = 1 if (nuevo_tipo == 'FALTA' and bool(data.get('afecta_septimo_dia', False))) else 0

            if nuevos_dias <= 0 or not nueva_fecha_inicio or not nueva_fecha_fin:
                conn.close()
                return jsonify({"error": "Fechas válidas y días mayores a 0 son obligatorios."}), 400

            tipos_validos = ['VACACIONES', 'PERMISO_CON_GOCE', 'PERMISO_SIN_GOCE', 'FALTA']
            if nuevo_tipo not in tipos_validos:
                conn.close()
                return jsonify({"error": f"Tipo inválido. Use: {tipos_validos}"}), 400

            # 1. Si el movimiento anterior era VACACIONES, reintegrar días al empleado original
            if tipo == 'VACACIONES':
                cursor.execute(
                    "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles + ? WHERE id = ?",
                    (dias_tomados, emp_id)
                )

            # 2. Si el nuevo tipo es VACACIONES, verificar saldo disponible y descontar del empleado correspondiente
            if nuevo_tipo == 'VACACIONES':
                cursor.execute(
                    "SELECT nombre_completo, ISNULL(dias_vacaciones_disponibles, 0) FROM empleados WHERE id = ?",
                    (nuevo_emp_id,)
                )
                emp_row = cursor.fetchone()
                if not emp_row:
                    conn.rollback()
                    conn.close()
                    return jsonify({"error": "Empleado no encontrado."}), 404

                emp_nom = emp_row[0]
                saldo_disponible = float(emp_row[1])

                if nuevos_dias > saldo_disponible:
                    conn.rollback()
                    conn.close()
                    return jsonify({
                        "error": f"Saldo insuficiente: {emp_nom} cuenta con {saldo_disponible:.2f} días disponibles y solicitó {nuevos_dias:.1f} días."
                    }), 400

                cursor.execute(
                    "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles - ? WHERE id = ?",
                    (nuevos_dias, nuevo_emp_id)
                )

            # 3. Actualizar registro en movimientos_laborales
            cursor.execute("""
                UPDATE movimientos_laborales
                SET empleado_id = ?, tipo = ?, fecha_inicio = ?, fecha_fin = ?, dias_tomados = ?, observacion = ?, afecta_septimo_dia = ?
                WHERE id = ?
            """, (nuevo_emp_id, nuevo_tipo, nueva_fecha_inicio, nueva_fecha_fin, nuevos_dias, nueva_obs, afecta_septimo_dia, mov_id))

            conn.commit()
            conn.close()
            return jsonify({"success": True, "mensaje": "Movimiento laboral actualizado exitosamente."})

    except Exception as e:
        if conn:
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500


# --- GENERACIÓN DE NÓMINA ---
@app.route('/api/nomina/previsualizar', methods=['GET'])
@login_required
@role_required(*ROLES_RRHH)
def api_nomina_previsualizar():
    try:
        salario = float(request.args.get('salario', 0))
        parametros = parametros_calculo(execute_query('SELECT * FROM parametros_laborales', fetchall=True))
        return jsonify(calcular_nomina_empleado(salario, parametros=parametros))
    except (ValueError, TypeError) as exc:
        return jsonify({'error': str(exc)}), 400


@app.route('/api/nomina/generar', methods=['POST'])
@login_required
def api_nomina_generar():
    """Genera la nómina mensual para todos los empleados activos con cálculos correctos Ley 822 + Ley 185."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos para generar nóminas."}), 403

    data = request.json or {}
    try:
        mes = int(data.get('mes', 0))
        anio = int(data.get('anio', 0))
        inicio_periodo, fin_periodo = limites_periodo(mes, anio)
    except (TypeError, ValueError):
        return jsonify({"error": "Mes o año inválido."}), 400
    # 'all' para toda la planilla, o un int para un empleado específico
    empleado_id_param = data.get('empleado_id', 'all')

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        # Validar duplicado o recuperar cabecera
        cursor.execute("SELECT id FROM nomina WITH (UPDLOCK, HOLDLOCK) WHERE periodo_mes = ? AND periodo_anio = ?", (mes, anio))
        row = cursor.fetchone()
        if row:
            nomina_id = int(row[0])
            es_complemento = True
        else:
            cursor.execute("INSERT INTO nomina (periodo_mes, periodo_anio) VALUES (?, ?)", (mes, anio))
            cursor.execute("SELECT @@IDENTITY AS id")
            nomina_id = int(cursor.fetchone()[0])
            es_complemento = False

        # Blindaje anti-duplicidad por período (mes/año):
        # Evita que un empleado sea reprocesado o acumule vacaciones más de una vez en el mismo mes.
        if empleado_id_param != 'all':
            cursor.execute("""
                SELECT id, salario_base, fecha_ingreso, ISNULL(dias_vacaciones_disponibles, 0), nombre_completo, identificacion, cargo, num_inss FROM empleados
                WHERE activo=1 AND id=? 
                AND id NOT IN (
                    SELECT dn.empleado_id FROM detalle_nomina dn
                    JOIN nomina n ON dn.nomina_id = n.id
                    WHERE n.periodo_mes = ? AND n.periodo_anio = ?
                )
            """, (empleado_id_param, mes, anio))
        else:
            cursor.execute("""
                SELECT id, salario_base, fecha_ingreso, ISNULL(dias_vacaciones_disponibles, 0), nombre_completo, identificacion, cargo, num_inss FROM empleados
                WHERE activo=1 
                AND id NOT IN (
                    SELECT dn.empleado_id FROM detalle_nomina dn
                    JOIN nomina n ON dn.nomina_id = n.id
                    WHERE n.periodo_mes = ? AND n.periodo_anio = ?
                )
            """, (mes, anio))

        empleados = cursor.fetchall()
        
        if not empleados:
            conn.close()
            return jsonify({"error": f"La nómina {mes}/{anio} ya fue generada para el/los empleado(s) seleccionado(s)."}), 400

        t_bruto       = 0.0
        t_deducciones = 0.0
        t_inss_lab    = 0.0
        t_ir          = 0.0
        t_neto        = 0.0
        t_patronal    = 0.0
        t_inatec      = 0.0
        t_vac         = 0.0
        t_agui        = 0.0

        cursor.execute("SELECT * FROM parametros_laborales")
        columnas = [c[0] for c in cursor.description]
        parametros = parametros_calculo(dict(zip(columnas, r)) for r in cursor.fetchall())
        procesados = 0
        from datetime import datetime as dt_mod

        for emp in empleados:
            e_id                  = emp[0]
            salario_base_contrato = float(emp[1])
            fecha_ingreso_val     = emp[2]
            saldo_vac_actual      = float(emp[3])

            # Valor diario (criterio MITRAB y jurisprudencia: salario mensual ÷ 30)
            valor_diario = round(salario_base_contrato / 30.0, 2)

            # Cálculo de días computables según fecha de ingreso
            dias_computables = 30.0
            if fecha_ingreso_val:
                try:
                    if isinstance(fecha_ingreso_val, str):
                        f_ing = dt_mod.strptime(fecha_ingreso_val[:10], '%Y-%m-%d').date()
                    else:
                        f_ing = fecha_ingreso_val

                    if f_ing.year > anio or (f_ing.year == anio and f_ing.month > mes):
                        # Ingresó después del período de nómina: se omite
                        continue
                    elif f_ing.year == anio and f_ing.month == mes:
                        dia_ing = f_ing.day
                        dias_computables = max(1.0, min(30.0, float(30 - dia_ing + 1)))
                    else:
                        dias_computables = 30.0
                except Exception:
                    dias_computables = 30.0

            # Consultar ausencias y permisos del mes en movimientos_laborales
            cursor.execute("""
                SELECT tipo, ISNULL(dias_tomados, 0), ISNULL(afecta_septimo_dia, 0), fecha_inicio, fecha_fin
                FROM movimientos_laborales
                WHERE empleado_id = ?
                  AND fecha_inicio <= ? AND fecha_fin >= ?
            """, (e_id, fin_periodo, inicio_periodo))
            movs_rows = cursor.fetchall()

            dias_falta = 0.0
            dias_septimo_dia = 0.0
            dias_permiso_sin_goce = 0.0

            for r in movs_rows:
                t_mov = r[0]
                d_mov = dias_en_periodo(r[3], r[4], r[1], inicio_periodo, fin_periodo)
                af_sep = bool(r[2])
                if t_mov == 'FALTA':
                    dias_falta += d_mov
                    if af_sep and inicio_periodo <= fecha(r[4]) <= fin_periodo:
                        # Si afecta séptimo día según Art. 64 Ley 185 (por jornada semanal incompleta)
                        dias_septimo_dia += 1.0
                elif t_mov == 'PERMISO_SIN_GOCE':
                    dias_permiso_sin_goce += d_mov

            # Montos de ajustes por tiempo no trabajado
            monto_falta = round(dias_falta * valor_diario, 2)
            monto_septimo_dia = round(dias_septimo_dia * valor_diario, 2)
            monto_permiso_sin_goce = round(dias_permiso_sin_goce * valor_diario, 2)

            # Si ingresó a mitad de mes, el tiempo previo no laborado
            dias_no_ingreso = max(0.0, 30.0 - dias_computables)
            monto_no_ingreso = round(dias_no_ingreso * valor_diario, 2)

            total_ajustes_tiempo = monto_falta + monto_septimo_dia + monto_permiso_sin_goce + monto_no_ingreso
            salario_devengado = max(0.0, round(salario_base_contrato - total_ajustes_tiempo, 2))

            # Días computables efectivamente trabajados
            dias_trabajados_mes = max(0.0, round(dias_computables - dias_falta - dias_septimo_dia - dias_permiso_sin_goce, 1))

            # Vacaciones ganadas en el período:
            # Art. 76 Ley 185: 15 días por cada 6 meses = 2.5 días/mes (factor: 2.5/30 por día computable).
            # Art. 79 Ley 185: faltas injustificadas NO son causa protegida → reducen días computables.
            # IMPORTANTE: siempre usar días efectivamente trabajados, nunca forzar 2.5 si hubo ausencias.
            if dias_trabajados_mes >= 30.0:
                vac_ganadas = parametros.get('VACACIONES_MES', 2.5)
            else:
                vac_ganadas = round(dias_trabajados_mes * (parametros.get('VACACIONES_MES', 2.5) / 30.0), 4)
                vac_ganadas = round(vac_ganadas, 2)  # redondear a 2 decimales para mostrar

            # Cálculos de nómina (Ley 822 y Ley 185) sobre salario devengado real
            cursor.execute("""SELECT ISNULL(SUM(monto_total), 0) FROM horas_extras WITH (UPDLOCK, HOLDLOCK)
                WHERE empleado_id=? AND fecha >= ? AND fecha <= ? AND estado='Aprobada' AND nomina_id IS NULL""",
                (e_id, inicio_periodo, fin_periodo))
            ingresos_extra = float(cursor.fetchone()[0])
            calc = calcular_nomina_empleado(salario_devengado, ingresos_extra, parametros)
            procesados += 1

            cursor.execute(
                """INSERT INTO detalle_nomina
                   (nomina_id, empleado_id, salario_base, ingresos_extra, ir,
                    inss_laboral, neto_pagar, inss_patronal,
                    provision_vacaciones, provision_aguinaldo,
                    dias_trabajados, vac_acumulada, vac_mes, vac_saldo_final,
                    dias_falta, monto_falta, dias_permiso_sin_goce, monto_permiso_sin_goce,
                    dias_septimo_dia, monto_septimo_dia, inatec_patronal,
                    historico_salario, historico_nombre, historico_identificacion, historico_cargo, historico_inss, historico_ingreso)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (nomina_id, e_id,
                 calc['salario_ordinario'],
                 calc['ingresos_extra'],
                 calc['ir_retencion'],
                 calc['inss_laboral'],
                 calc['salario_neto'],
                 calc['inss_patronal'],
                 calc['provision_vacaciones'],
                 calc['provision_aguinaldo'],
                 dias_trabajados_mes,
                 saldo_vac_actual,
                 vac_ganadas,
                 round(saldo_vac_actual + vac_ganadas, 2),
                 dias_falta,
                 monto_falta,
                 dias_permiso_sin_goce,
                 monto_permiso_sin_goce,
                 dias_septimo_dia,
                 monto_septimo_dia,
                 calc['inatec_patronal'], salario_base_contrato, emp[4], emp[5], emp[6], emp[7], fecha_ingreso_val)
            )
            cursor.execute("""UPDATE horas_extras SET nomina_id=?, estado='Incluida en nómina'
                WHERE empleado_id=? AND fecha >= ? AND fecha <= ?
                  AND estado='Aprobada' AND nomina_id IS NULL""",
                (nomina_id, e_id, inicio_periodo, fin_periodo))

            # Acumular días de vacaciones computables correspondientes a este período
            cursor.execute(
                "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles + ? WHERE id = ?",
                (vac_ganadas, e_id)
            )

            t_bruto       += calc['salario_bruto']
            t_deducciones += calc['total_deducciones']
            t_inss_lab    += calc['inss_laboral']
            t_ir          += calc['ir_retencion']
            t_neto        += calc['salario_neto']
            t_patronal    += calc['inss_patronal']
            t_inatec      += calc['inatec_patronal']
            t_vac         += calc['provision_vacaciones']
            t_agui        += calc['provision_aguinaldo']

        if not procesados:
            conn.rollback()
            conn.close()
            return jsonify({"error": "No hay empleados con ingreso anterior al fin del período."}), 400

        # Actualizar totales en cabecera
        cursor.execute(
            """UPDATE nomina
               SET total_ingresos=total_ingresos+?, total_deducciones=total_deducciones+?, total_neto=total_neto+?,
                   inss_patronal_total=inss_patronal_total+?, provision_vac_total=provision_vac_total+?, provision_agui_total=provision_agui_total+?,
                   inatec_patronal_total=ISNULL(inatec_patronal_total, 0)+?
               WHERE id=?""",
            (round(t_bruto, 2), round(t_deducciones, 2), round(t_neto, 2),
             round(t_patronal, 2), round(t_vac, 2), round(t_agui, 2), round(t_inatec, 2), nomina_id)
        )

        # --- ASIENTO CONTABLE AUTOMÁTICO DE NÓMINA ---
        def get_cta(codigo, nombre, clasificacion, naturaleza):
            cursor.execute("SELECT id, activo, nombre FROM cuentas_contables WITH (UPDLOCK, HOLDLOCK) WHERE codigo = ?", (codigo,))
            row = cursor.fetchone()
            if row:
                if not row[1]:
                    raise ValueError(f'La cuenta {codigo} está inactiva; revise el catálogo contable.')
                if codigo == '2.1.10' and 'INATEC' not in row[2].upper():
                    raise ValueError('La cuenta 2.1.10 pertenece a otro concepto; configure INATEC por pagar antes de generar.')
                return row[0]
            cursor.execute("""INSERT INTO cuentas_contables
                (codigo, nombre, clasificacion, naturaleza, descripcion, activo)
                VALUES (?, ?, ?, ?, 'Cuenta para contabilización de nómina', 1)""",
                (codigo, nombre, clasificacion, naturaleza))
            cursor.execute('SELECT @@IDENTITY AS id')
            return cursor.fetchone()[0]
            
        cta_sueldos_gasto = get_cta('6.1.01', 'Sueldos y salarios', 'Gasto', 'Deudora')
        cta_cargas_patronales = get_cta('6.1.11', 'Cargas patronales de nómina', 'Gasto', 'Deudora')
        cta_prestaciones_gasto = get_cta('6.1.12', 'Provisiones de prestaciones laborales', 'Gasto', 'Deudora')
        
        cta_retenciones_inss = get_cta('2.1.06', 'INSS laboral y patronal por pagar', 'Pasivo corriente', 'Acreedora')
        cta_retenciones_ir = get_cta('2.1.07', 'IR laboral por pagar', 'Pasivo corriente', 'Acreedora')
        cta_provisiones = get_cta('2.1.08', 'Prestaciones laborales por pagar', 'Pasivo corriente', 'Acreedora')
        cta_sueldos_pagar = get_cta('2.1.04', 'Sueldos y salarios por pagar', 'Pasivo corriente', 'Acreedora')
        cta_inatec = get_cta('2.1.10', 'INATEC por pagar', 'Pasivo corriente', 'Acreedora')
        
        concepto_asiento = f"Registro de nómina mes {mes:02d}/{anio}"
        if es_complemento:
            concepto_asiento = f"Registro de nómina mes {mes:02d}/{anio} (Complemento)"
        cursor.execute("""
            INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
            VALUES (GETDATE(), ?, 'RRHH', ?, ?)
        """, (concepto_asiento, nomina_id, session['user']['id']))
        cursor.execute("SELECT @@IDENTITY AS id")
        asiento_id = cursor.fetchone()[0]
        
        # Débitos (Gastos)
        if t_bruto > 0 and cta_sueldos_gasto:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_id, cta_sueldos_gasto, round(t_bruto, 2)))
        t_cargas_pat = t_patronal + t_inatec
        if t_cargas_pat > 0 and cta_cargas_patronales:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_id, cta_cargas_patronales, round(t_cargas_pat, 2)))
        t_prestaciones = t_vac + t_agui
        if t_prestaciones > 0 and cta_prestaciones_gasto:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_id, cta_prestaciones_gasto, round(t_prestaciones, 2)))
            
        # Créditos (Pasivos)
        t_inss_total = t_inss_lab + t_patronal
        if t_inss_total > 0 and cta_retenciones_inss:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_retenciones_inss, round(t_inss_total, 2)))
        if t_ir > 0 and cta_retenciones_ir:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_retenciones_ir, round(t_ir, 2)))
        if t_prestaciones > 0 and cta_provisiones:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_provisiones, round(t_prestaciones, 2)))
        if t_neto > 0 and cta_sueldos_pagar:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_sueldos_pagar, round(t_neto, 2)))

        if t_inatec > 0:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_inatec, round(t_inatec, 2)))
        cursor.execute("SELECT ISNULL(SUM(debe),0)-ISNULL(SUM(haber),0) FROM movimientos_contables WHERE asiento_id=?", (asiento_id,))
        if abs(float(cursor.fetchone()[0])) >= 0.01:
            raise ValueError('El asiento de nómina no está balanceado; se canceló la operación.')

        conn.commit()
        conn.close()
        return jsonify({
            "success"   : True,
            "mensaje"   : f"Nómina {mes:02d}/{anio} generada con éxito para {procesados} empleados.",
            "nomina_id" : nomina_id,
            "resumen"   : {
                "total_bruto"      : round(t_bruto, 2),
                "total_deducciones": round(t_deducciones, 2),
                "total_neto"       : round(t_neto, 2),
                "inss_patronal"    : round(t_patronal, 2),
                "inatec_patronal"  : round(t_inatec, 2),
                "provision_vac"    : round(t_vac, 2),
                "provision_agui"   : round(t_agui, 2)
            }
        }), 201

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/api/nomina/<int:nomina_id>/incluir-horas-extras', methods=['POST'])
@login_required
def api_nomina_incluir_horas_extras(nomina_id):
    """Incorpora a la nómina horas extra aprobadas después de su generación."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""SELECT periodo_mes, periodo_anio FROM nomina WITH (UPDLOCK, HOLDLOCK)
            WHERE id=?""", (nomina_id,))
        payroll = cursor.fetchone()
        if not payroll:
            conn.rollback()
            return jsonify({"error": "Nómina no encontrada."}), 404
        mes, anio = int(payroll[0]), int(payroll[1])
        inicio_periodo, fin_periodo = limites_periodo(mes, anio)
        cursor.execute("""SELECT id, empleado_id, monto_total FROM horas_extras WITH (UPDLOCK, HOLDLOCK)
            WHERE nomina_id IS NULL AND estado='Aprobada' AND fecha>=? AND fecha<=?
            ORDER BY empleado_id, id""", (inicio_periodo, fin_periodo))
        pending = cursor.fetchall()
        if not pending:
            conn.rollback()
            return jsonify({"success": True, "mensaje": "No hay horas extras aprobadas pendientes para este período.", "incluidas": 0})

        by_employee = {}
        for extra_id, employee_id, amount in pending:
            entry = by_employee.setdefault(int(employee_id), {'ids': [], 'amount': 0.0})
            entry['ids'].append(int(extra_id))
            entry['amount'] += float(amount or 0)

        details = {}
        for employee_id in by_employee:
            cursor.execute("""SELECT id, salario_base, ISNULL(ingresos_extra,0), inss_laboral, ir,
                ISNULL(neto_pagar,0), ISNULL(inss_patronal,0), ISNULL(provision_vacaciones,0),
                ISNULL(provision_aguinaldo,0), ISNULL(inatec_patronal,0)
                FROM detalle_nomina WITH (UPDLOCK, HOLDLOCK)
                WHERE nomina_id=? AND empleado_id=?""", (nomina_id, employee_id))
            detail = cursor.fetchone()
            if not detail:
                raise ValueError(f'No existe detalle de nómina para el empleado #{employee_id}. Genere primero su nómina ordinaria.')
            cursor.execute("SELECT COUNT(*) FROM pagos_nomina WITH (UPDLOCK, HOLDLOCK) WHERE nomina_id=? AND empleado_id=?", (nomina_id, employee_id))
            if int(cursor.fetchone()[0]):
                raise ValueError(f'El empleado #{employee_id} ya tiene un pago registrado para esta nómina. Registre el ajuste como pago complementario para conservar la trazabilidad.')
            details[employee_id] = detail

        cursor.execute("SELECT * FROM parametros_laborales")
        columns = [col[0] for col in cursor.description]
        params = parametros_calculo(dict(zip(columns, row)) for row in cursor.fetchall())
        totals = {'ingresos':0.0,'deducciones':0.0,'neto':0.0,'patronal':0.0,'inatec':0.0,'vac':0.0,'agui':0.0,'ir':0.0,'inss_lab':0.0,'inss_pat':0.0}

        for employee_id, extra in by_employee.items():
            old = details[employee_id]
            calc = calcular_nomina_empleado(float(old[1] or 0), float(old[2] or 0) + extra['amount'], params)
            delta = {
                'ingresos': calc['salario_bruto'] - (float(old[1] or 0) + float(old[2] or 0)),
                'deducciones': calc['total_deducciones'] - (float(old[3] or 0) + float(old[4] or 0)),
                'neto': calc['salario_neto'] - float(old[5] or 0),
                'patronal': calc['inss_patronal'] - float(old[6] or 0),
                'inatec': calc['inatec_patronal'] - float(old[9] or 0),
                'vac': calc['provision_vacaciones'] - float(old[7] or 0),
                'agui': calc['provision_aguinaldo'] - float(old[8] or 0),
                'ir': calc['ir_retencion'] - float(old[4] or 0),
                'inss_lab': calc['inss_laboral'] - float(old[3] or 0),
                'inss_pat': calc['inss_patronal'] - float(old[6] or 0),
            }
            for key, value in delta.items():
                totals[key] += value
            cursor.execute("""UPDATE detalle_nomina SET ingresos_extra=?, ir=?, inss_laboral=?, neto_pagar=?,
                inss_patronal=?, provision_vacaciones=?, provision_aguinaldo=?, inatec_patronal=?
                WHERE id=?""", (calc['ingresos_extra'], calc['ir_retencion'], calc['inss_laboral'], calc['salario_neto'],
                    calc['inss_patronal'], calc['provision_vacaciones'], calc['provision_aguinaldo'], calc['inatec_patronal'], old[0]))
            cursor.execute("UPDATE colilla_pago SET netoRecibir=? WHERE detalle_nomina_id=?", (calc['salario_neto'], old[0]))

        cursor.execute("""UPDATE nomina SET total_ingresos=total_ingresos+?, total_deducciones=total_deducciones+?,
            total_neto=total_neto+?, inss_patronal_total=ISNULL(inss_patronal_total,0)+?,
            inatec_patronal_total=ISNULL(inatec_patronal_total,0)+?, provision_vac_total=provision_vac_total+?,
            provision_agui_total=provision_agui_total+? WHERE id=?""",
            (totals['ingresos'], totals['deducciones'], totals['neto'], totals['patronal'], totals['inatec'],
             totals['vac'], totals['agui'], nomina_id))

        account_specs = [
            ('6.1.01','Sueldos y salarios','Gasto','Deudora'),
            ('6.1.11','Cargas patronales de nómina','Gasto','Deudora'),
            ('6.1.12','Provisiones de prestaciones laborales','Gasto','Deudora'),
            ('2.1.06','INSS laboral y patronal por pagar','Pasivo corriente','Acreedora'),
            ('2.1.07','IR laboral por pagar','Pasivo corriente','Acreedora'),
            ('2.1.08','Prestaciones laborales por pagar','Pasivo corriente','Acreedora'),
            ('2.1.04','Sueldos y salarios por pagar','Pasivo corriente','Acreedora'),
            ('2.1.10','INATEC por pagar','Pasivo corriente','Acreedora'),
        ]
        accounts = {}
        for code, name, classification, nature in account_specs:
            cursor.execute("SELECT id, activo, nombre FROM cuentas_contables WITH (UPDLOCK, HOLDLOCK) WHERE codigo=?", (code,))
            account = cursor.fetchone()
            if account and (not account[1] or (code == '2.1.10' and 'INATEC' not in account[2].upper())):
                raise ValueError(f'La cuenta contable {code} requiere revisión antes de ajustar la nómina.')
            if not account:
                cursor.execute("""INSERT INTO cuentas_contables (codigo,nombre,clasificacion,naturaleza,descripcion,activo)
                    VALUES (?,?,?,?,?,1)""", (code,name,classification,nature,'Cuenta para ajuste de horas extras'))
                cursor.execute('SELECT @@IDENTITY')
                account = (cursor.fetchone()[0],1,name)
            accounts[code] = account[0]

        debits = [
            ('6.1.01', totals['ingresos']),
            ('6.1.11', totals['patronal'] + totals['inatec']),
            ('6.1.12', totals['vac'] + totals['agui']),
        ]
        credits = [
            ('2.1.06', totals['inss_lab'] + totals['inss_pat']), ('2.1.07', totals['ir']),
            ('2.1.08', totals['vac'] + totals['agui']), ('2.1.04', totals['neto']), ('2.1.10', totals['inatec']),
        ]
        if round(sum(value for _, value in debits) - sum(value for _, value in credits), 2) != 0:
            raise ValueError('El asiento del ajuste no cuadra. No se modificó la nómina.')
        cursor.execute("""INSERT INTO asientos_contables (fecha,concepto,modulo_origen,referencia_id,usuario_id)
            VALUES (GETDATE(),?,'RRHH_AJUSTE_HORAS_EXTRAS',?,?)""",
            (f'Ajuste de horas extras nómina {mes:02d}/{anio}', nomina_id, session['user']['id']))
        cursor.execute('SELECT @@IDENTITY')
        journal_id = cursor.fetchone()[0]
        for code, amount in debits:
            if abs(amount) >= 0.005:
                cursor.execute("INSERT INTO movimientos_contables (asiento_id,cuenta_id,debe,haber) VALUES (?,?,?,0)", (journal_id,accounts[code],round(amount,2)))
        for code, amount in credits:
            if abs(amount) >= 0.005:
                cursor.execute("INSERT INTO movimientos_contables (asiento_id,cuenta_id,debe,haber) VALUES (?,?,0,?)", (journal_id,accounts[code],round(amount,2)))
        for employee_id, extra in by_employee.items():
            placeholders=','.join('?' for _ in extra['ids'])
            cursor.execute(f"UPDATE horas_extras SET nomina_id=?, estado='Incluida en nómina' WHERE id IN ({placeholders}) AND nomina_id IS NULL",
                (nomina_id,*extra['ids']))
        conn.commit()
        return jsonify({"success": True, "mensaje": f"Se incluyeron C$ {sum(x['amount'] for x in by_employee.values()):,.2f} en {len(by_employee)} detalle(s) de nómina.", "empleados":len(by_employee), "nomina_id":nomina_id}), 200
    except ValueError as exc:
        conn.rollback()
        return jsonify({"error": str(exc)}), 409
    except Exception as exc:
        conn.rollback()
        app.logger.exception('Error al incluir horas extras en nómina %s', nomina_id)
        return jsonify({"error": "No se pudieron incluir las horas extras. No se modificó la nómina."}), 500
    finally:
        conn.close()


@app.route('/api/nomina/historial', methods=['GET'])
@login_required
def api_nomina_historial():
    """Lista el historial de todas las nóminas generadas."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403
    query2 = """
        SELECT id, periodo_mes AS mes, periodo_anio AS anio, fecha_generacion,
               total_ingresos, total_deducciones, total_neto,
               ISNULL(inss_patronal_total, 0) AS inss_patronal_total,
               ISNULL(inatec_patronal_total, 0) AS inatec_patronal_total,
               ISNULL(provision_vac_total, 0) AS provision_vac_total,
               ISNULL(provision_agui_total, 0) AS provision_agui_total,
               ISNULL(estado, 'CERRADA') AS estado
        FROM nomina
        ORDER BY periodo_anio DESC, periodo_mes DESC
    """
    nominas = execute_query(query2, fetchall=True)
    for n in nominas:
        for campo in ['total_ingresos', 'total_deducciones', 'total_neto',
                      'inss_patronal_total', 'inatec_patronal_total', 'provision_vac_total', 'provision_agui_total']:
            if campo in n and n[campo] is not None:
                n[campo] = float(n[campo])
        if n.get('fecha_generacion'):
            n['fecha_generacion'] = str(n['fecha_generacion'])
    return jsonify(nominas)


@app.route('/api/nomina/<int:nomina_id>/detalle', methods=['GET'])
@login_required
def api_nomina_detalle(nomina_id):
    """Obtiene el detalle completo de una nómina: cabecera + líneas por empleado."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403
    cabecera = execute_query(
        """SELECT id, periodo_mes AS mes, periodo_anio AS anio, fecha_generacion,
                  total_ingresos, total_deducciones, total_neto,
                  ISNULL(inss_patronal_total,0) AS inss_patronal_total,
                  ISNULL(inatec_patronal_total,0) AS inatec_patronal_total,
                  ISNULL(provision_vac_total,0) AS provision_vac_total,
                  ISNULL(provision_agui_total,0) AS provision_agui_total,
                  ISNULL(estado,'CERRADA') AS estado
           FROM nomina WHERE id=?""",
        (nomina_id,), fetchone=True
    )
    if not cabecera:
        return jsonify({"error": "Nómina no encontrada."}), 404

    detalles = execute_query(
        """SELECT dn.id, e.id AS empleado_id, CASE WHEN dn.historico_salario IS NULL THEN e.nombre_completo ELSE dn.historico_nombre END AS empleado, CASE WHEN dn.historico_salario IS NULL THEN e.identificacion ELSE dn.historico_identificacion END AS identificacion, CASE WHEN dn.historico_salario IS NULL THEN e.cargo ELSE dn.historico_cargo END AS cargo,
                  CASE WHEN dn.historico_salario IS NULL THEN e.salario_base ELSE dn.historico_salario END AS salario_contrato,
                  CASE WHEN dn.historico_salario IS NULL THEN 1 ELSE 0 END AS historico_incompleto,
                  dn.salario_base AS salario_devengado,
                  dn.salario_base AS salario_base,
                  ISNULL(dn.ingresos_extra,0) AS ingresos_extra,
                  dn.inss_laboral, dn.ir,
                  ISNULL(dn.inss_patronal,0) AS inss_patronal,
                  ISNULL(dn.inatec_patronal,0) AS inatec_patronal,
                  ISNULL(dn.provision_vacaciones,0) AS provision_vacaciones,
                  ISNULL(dn.provision_aguinaldo,0) AS provision_aguinaldo,
                  dn.neto_pagar,
                  ISNULL(dn.dias_trabajados, 30) AS dias_trabajados,
                  ISNULL(dn.dias_falta, 0) AS dias_falta,
                  ISNULL(dn.monto_falta, 0) AS monto_falta,
                  ISNULL(dn.dias_permiso_sin_goce, 0) AS dias_permiso_sin_goce,
                  ISNULL(dn.monto_permiso_sin_goce, 0) AS monto_permiso_sin_goce,
                  ISNULL(dn.dias_septimo_dia, 0) AS dias_septimo_dia,
                  ISNULL(dn.monto_septimo_dia, 0) AS monto_septimo_dia
           FROM detalle_nomina dn
           JOIN empleados e ON dn.empleado_id = e.id
           WHERE dn.nomina_id=?
           ORDER BY e.nombre_completo""",
        (nomina_id,), fetchall=True
    )
    campos_float = ['salario_contrato', 'salario_devengado', 'salario_base', 'ingresos_extra', 'inss_laboral', 'ir',
                    'inss_patronal', 'inatec_patronal', 'provision_vacaciones', 'provision_aguinaldo', 'neto_pagar',
                    'dias_trabajados', 'dias_falta', 'monto_falta', 'dias_permiso_sin_goce', 'monto_permiso_sin_goce',
                    'dias_septimo_dia', 'monto_septimo_dia']
    for d in detalles:
        for c in campos_float:
            if c in d and d[c] is not None:
                d[c] = float(d[c])
    for c in ['total_ingresos', 'total_deducciones', 'total_neto',
               'inss_patronal_total', 'inatec_patronal_total', 'provision_vac_total', 'provision_agui_total']:
        if cabecera.get(c) is not None:
            cabecera[c] = float(cabecera[c])
    if cabecera.get('fecha_generacion'):
        cabecera['fecha_generacion'] = str(cabecera['fecha_generacion'])
    return jsonify({"cabecera": cabecera, "detalles": detalles})


@app.route('/api/nomina/<int:nomina_id>/empleado/<int:emp_id>', methods=['GET'])
@login_required
def api_colilla_individual(nomina_id, emp_id):
    """Obtiene la colilla (recibo) individual de pago de un empleado en una nómina."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403
    nomina = execute_query(
        "SELECT id, periodo_mes AS mes, periodo_anio AS anio, fecha_generacion FROM nomina WHERE id=?",
        (nomina_id,), fetchone=True
    )
    if not nomina:
        return jsonify({"error": "Nómina no encontrada."}), 404
    if nomina.get('fecha_generacion'):
        nomina['fecha_generacion'] = str(nomina['fecha_generacion'])

    detalle = execute_query(
        """SELECT CASE WHEN dn.historico_salario IS NULL THEN e.nombre_completo ELSE dn.historico_nombre END AS empleado, CASE WHEN dn.historico_salario IS NULL THEN e.identificacion ELSE dn.historico_identificacion END AS identificacion, CASE WHEN dn.historico_salario IS NULL THEN e.num_inss ELSE dn.historico_inss END AS num_inss, CASE WHEN dn.historico_salario IS NULL THEN e.cargo ELSE dn.historico_cargo END AS cargo,
                  CASE WHEN dn.historico_salario IS NULL THEN e.fecha_ingreso ELSE dn.historico_ingreso END AS fecha_ingreso,
                  CASE WHEN dn.historico_salario IS NULL THEN e.salario_base ELSE dn.historico_salario END AS salario_contrato,
                  CASE WHEN dn.historico_salario IS NULL THEN 1 ELSE 0 END AS historico_incompleto,
                  dn.salario_base AS salario_devengado,
                  ISNULL(dn.ingresos_extra,0) AS ingresos_extra,
                  dn.inss_laboral, dn.ir,
                  ISNULL(dn.inss_patronal,0) AS inss_patronal,
                  ISNULL(dn.inatec_patronal,0) AS inatec_patronal,
                  ISNULL(dn.provision_vacaciones,0) AS provision_vacaciones,
                  ISNULL(dn.provision_aguinaldo,0) AS provision_aguinaldo,
                  dn.neto_pagar,
                  ISNULL(dn.dias_trabajados, 30) AS dias_trabajados,
                  ISNULL(dn.vac_acumulada, 0) AS vac_acumulada,
                  ISNULL(dn.vac_mes, 2.5) AS vac_mes,
                  ISNULL(dn.vac_descansados, 0) AS vac_descansados,
                  ISNULL(dn.vac_saldo_final, 0) AS vac_saldo,
                  ISNULL(dn.dias_falta, 0) AS dias_falta,
                  ISNULL(dn.monto_falta, 0) AS monto_falta,
                  ISNULL(dn.dias_permiso_sin_goce, 0) AS dias_permiso_sin_goce,
                  ISNULL(dn.monto_permiso_sin_goce, 0) AS monto_permiso_sin_goce,
                  ISNULL(dn.dias_septimo_dia, 0) AS dias_septimo_dia,
                  ISNULL(dn.monto_septimo_dia, 0) AS monto_septimo_dia,
                  ISNULL(dn.adelanto_salarial, 0) AS adelanto_salarial
           FROM detalle_nomina dn
           JOIN empleados e ON dn.empleado_id = e.id
           WHERE dn.nomina_id=? AND dn.empleado_id=?""",
        (nomina_id, emp_id), fetchone=True
    )
    if not detalle:
        return jsonify({"error": "Detalle de empleado no encontrado en esta nómina."}), 404

    campos_float = [
        'salario_contrato', 'salario_devengado', 'ingresos_extra', 'inss_laboral', 'ir',
        'inss_patronal', 'inatec_patronal', 'provision_vacaciones', 'provision_aguinaldo',
        'neto_pagar', 'dias_trabajados', 'vac_acumulada', 'vac_mes', 'vac_descansados', 'vac_saldo',
        'dias_falta', 'monto_falta', 'dias_permiso_sin_goce', 'monto_permiso_sin_goce',
        'dias_septimo_dia', 'monto_septimo_dia', 'adelanto_salarial'
    ]
    for c in campos_float:
        if detalle.get(c) is not None:
            detalle[c] = float(detalle[c])
        else:
            detalle[c] = 0.0

    if detalle.get('fecha_ingreso'):
        detalle['fecha_ingreso'] = str(detalle['fecha_ingreso'])[:10]

    # Valor diario estándar mensual ÷ 30
    detalle['valor_diario'] = round(detalle['salario_contrato'] / 30.0, 2)
    detalle['total_ajustes_tiempo'] = round(
        detalle['monto_falta'] + detalle['monto_septimo_dia'] + detalle['monto_permiso_sin_goce'], 2
    )
    detalle['salario_bruto'] = round(detalle['salario_devengado'] + detalle['ingresos_extra'], 2)
    detalle['total_deducciones'] = round(detalle['inss_laboral'] + detalle['ir'] + detalle['adelanto_salarial'], 2)

    # Costo y obligaciones patronales (a cargo del empleador)
    detalle['total_cargas_patronales'] = round(
        detalle['inss_patronal'] + detalle['inatec_patronal'] + detalle['provision_vacaciones'] + detalle['provision_aguinaldo'], 2
    )
    detalle['costo_total_patronal'] = round(detalle['salario_bruto'] + detalle['total_cargas_patronales'], 2)

    return jsonify({"nomina": nomina, "colilla": detalle})


@app.route('/api/nomina/<int:nomina_id>', methods=['GET', 'PUT', 'DELETE'])
@login_required
def api_nomina_delete(nomina_id):
    """Consulta, edición y anulación de nóminas generadas."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403

    if request.method == 'GET':
        query = """
            SELECT id, periodo_mes, periodo_anio, fecha_generacion,
                   total_ingresos, total_deducciones, total_neto,
                   ISNULL(inss_patronal_total, 0) AS inss_patronal_total,
                   ISNULL(inatec_patronal_total, 0) AS inatec_patronal_total,
                   ISNULL(provision_vac_total, 0) AS provision_vac_total,
                   ISNULL(provision_agui_total, 0) AS provision_agui_total,
                   ISNULL(estado, 'CERRADA') AS estado
            FROM nomina WHERE id = ?
        """
        nom = execute_query(query, (nomina_id,), fetchone=True)
        if not nom:
            return jsonify({"error": "Nómina no encontrada."}), 404
        for k in ['total_ingresos', 'total_deducciones', 'total_neto', 'inss_patronal_total', 'inatec_patronal_total', 'provision_vac_total', 'provision_agui_total']:
            if k in nom and nom[k] is not None:
                nom[k] = float(nom[k])
        if nom.get('fecha_generacion'):
            nom['fecha_generacion'] = str(nom['fecha_generacion'])
        return jsonify(nom)

    if request.method == 'PUT':
        data = request.json or {}
        nuevo_estado = data.get('estado')
        if not nuevo_estado:
            return jsonify({"error": "Debe especificar el nuevo estado."}), 400
        execute_query("UPDATE nomina SET estado = ? WHERE id = ?", (nuevo_estado, nomina_id), commit=True)
        return jsonify({"success": True, "mensaje": f"Nómina #{nomina_id} actualizada correctamente al estado {nuevo_estado}."})

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar que existe
        cursor.execute("SELECT id FROM nomina WITH (UPDLOCK, HOLDLOCK) WHERE id=?", (nomina_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Nómina no encontrada."}), 404

        cursor.execute("SELECT id FROM pagos_nomina WHERE nomina_id=? AND estado='Confirmado'", (nomina_id,))
        if cursor.fetchone():
            conn.rollback()
            conn.close()
            return jsonify({"error": "No se puede anular una nómina con pagos confirmados."}), 409

        # Revertir vacaciones (restar exactamente los días proporcionales que se sumaron a cada empleado en esta nómina)
        cursor.execute("SELECT empleado_id, ISNULL(vac_mes, 2.5) FROM detalle_nomina WHERE nomina_id=?", (nomina_id,))
        empleados_en_nomina = cursor.fetchall()
        for emp in empleados_en_nomina:
            emp_id = emp[0]
            vac_a_revertir = float(emp[1])
            cursor.execute(
                """UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles - ?
                   WHERE id = ? AND dias_vacaciones_disponibles >= ?""",
                (vac_a_revertir, emp_id, vac_a_revertir)
            )
            if cursor.rowcount != 1:
                raise ValueError('Las vacaciones acumuladas ya fueron utilizadas. No se puede anular la nómina.')

        # Conservar el asiento original y registrar su contrapartida para auditoría.
        cursor.execute("""SELECT id FROM asientos_contables
            WHERE modulo_origen='RRHH' AND referencia_id=?""", (nomina_id,))
        originales = cursor.fetchall()
        for original in originales:
            cursor.execute("""INSERT INTO asientos_contables
                (fecha, concepto, modulo_origen, referencia_id, usuario_id)
                VALUES (GETDATE(), ?, 'RRHH_ANULACION', ?, ?)""",
                (f'Anulación nómina #{nomina_id}, asiento #{original[0]}', nomina_id, session['user']['id']))
            cursor.execute("SELECT @@IDENTITY AS id")
            reverso_id = cursor.fetchone()[0]
            cursor.execute("""INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber)
                SELECT ?, cuenta_id, haber, debe FROM movimientos_contables WHERE asiento_id=?""",
                (reverso_id, original[0]))

        # Ambas versiones de la base funcionan, con o sin cascada.
        cursor.execute("DELETE FROM colilla_pago WHERE detalle_nomina_id IN (SELECT id FROM detalle_nomina WHERE nomina_id=?)", (nomina_id,))
        cursor.execute("DELETE FROM pagos_nomina WHERE nomina_id=?", (nomina_id,))
        cursor.execute("DELETE FROM detalle_nomina WHERE nomina_id=?", (nomina_id,))
        cursor.execute("DELETE FROM nomina WHERE id=?", (nomina_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# RECURSOS HUMANOS - COLILLA DE PAGO (vista imprimible)
# ==============================================================================
@app.route('/rrhh/colilla/<int:id_detalle>')
@login_required
@role_required(*ROLES_RRHH)
def ver_colilla(id_detalle):
    query = """
        SELECT
            CASE WHEN d.historico_salario IS NULL THEN e.nombre_completo ELSE d.historico_nombre END as empleado,
            CASE WHEN d.historico_salario IS NULL THEN e.identificacion ELSE d.historico_identificacion END as cedula,
            CASE WHEN d.historico_salario IS NULL THEN e.cargo ELSE d.historico_cargo END AS cargo,
            CASE WHEN d.historico_salario IS NULL THEN e.num_inss ELSE d.historico_inss END as inss,
            CASE WHEN d.historico_salario IS NULL THEN e.salario_base ELSE d.historico_salario END as salario_contrato,
            CASE WHEN d.historico_salario IS NULL THEN e.fecha_ingreso ELSE d.historico_ingreso END AS fecha_ingreso,
            n.periodo_mes as periodo_mes,
            n.periodo_anio as periodo_anio,
            CASE WHEN d.historico_salario IS NULL THEN 1 ELSE 0 END AS historico_incompleto,
                  d.salario_base as salario_devengado,
            ISNULL(d.ingresos_extra,0) as kpi_meta,
            (d.salario_base + ISNULL(d.ingresos_extra,0)) as total_percepciones,
            d.inss_laboral,
            d.ir,
            (d.inss_laboral + d.ir) as total_deducciones,
            d.neto_pagar as neto_a_recibir,
            ISNULL(d.dias_trabajados, 30) as dias_trabajados,
            ISNULL(d.vac_acumulada, ISNULL(e.dias_vacaciones_disponibles, 0)) as vac_acumulada,
            ISNULL(d.vac_mes, 2.5) as vac_mes,
            ISNULL(d.vac_descansados, 0) as vac_descansados,
            ISNULL(d.vac_saldo_final, ISNULL(e.dias_vacaciones_disponibles, 0)) as vac_saldo,
            ISNULL(d.dias_falta, 0) as dias_falta,
            ISNULL(d.monto_falta, 0) as monto_falta,
            ISNULL(d.dias_permiso_sin_goce, 0) as dias_permiso_sin_goce,
            ISNULL(d.monto_permiso_sin_goce, 0) as monto_permiso_sin_goce,
            ISNULL(d.dias_septimo_dia, 0) as dias_septimo_dia,
            ISNULL(d.monto_septimo_dia, 0) as monto_septimo_dia,
            ISNULL(d.inss_patronal, 0) as inss_patronal,
            ISNULL(d.inatec_patronal, 0) as inatec_patronal,
            ISNULL(d.provision_vacaciones, 0) as provision_vacaciones,
            ISNULL(d.provision_aguinaldo, 0) as provision_aguinaldo
        FROM detalle_nomina d
        INNER JOIN nomina n ON d.nomina_id = n.id
        INNER JOIN empleados e ON d.empleado_id = e.id
        WHERE d.id = ?
    """
    datos = execute_query(query, (id_detalle,), fetchone=True)

    if not datos:
        return "Colilla no encontrada", 404

    meses_es = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
    mes_nombre = meses_es[datos.get('periodo_mes', 0)] if datos.get('periodo_mes') else '—'
    periodo = f"{mes_nombre} {datos.get('periodo_anio', '')}"

    salario_contrato = float(datos.get('salario_contrato') or 0)
    valor_diario = round(salario_contrato / 30.0, 2)
    monto_falta = float(datos.get('monto_falta') or 0)
    monto_sep = float(datos.get('monto_septimo_dia') or 0)
    monto_psg = float(datos.get('monto_permiso_sin_goce') or 0)
    total_ajustes = round(monto_falta + monto_sep + monto_psg, 2)

    sal_devengado = float(datos.get('salario_devengado') or 0)
    kpi_meta = float(datos.get('kpi_meta') or 0)
    tot_percepciones = float(datos.get('total_percepciones') or sal_devengado)
    inss_lab = float(datos.get('inss_laboral') or 0)
    ir_val = float(datos.get('ir') or 0)
    tot_deducciones = float(datos.get('total_deducciones') or (inss_lab + ir_val))
    neto_recibir = float(datos.get('neto_a_recibir') or (tot_percepciones - tot_deducciones))

    inss_pat = float(datos.get('inss_patronal') or 0)
    inatec_pat = float(datos.get('inatec_patronal') or 0)
    prov_vac = float(datos.get('provision_vacaciones') or 0)
    prov_agui = float(datos.get('provision_aguinaldo') or 0)
    tot_cargas_pat = round(inss_pat + inatec_pat + prov_vac + prov_agui, 2)
    costo_tot_pat = round(tot_percepciones + tot_cargas_pat, 2)

    c = {
        "historico_incompleto": bool(datos.get("historico_incompleto")),
        "empresa": "Jehová Jireh Moto Repuestos",
        "periodo": periodo,
        "empleado": datos['empleado'],
        "cedula": datos.get('cedula') or '—',
        "cargo": datos.get('cargo') or 'Empleado',
        "departamento": 'General',
        "inss": datos.get('inss') or '—',
        "salario_contrato": salario_contrato,
        "valor_diario": valor_diario,
        "fecha_ingreso": str(datos.get('fecha_ingreso', ''))[:10] if datos.get('fecha_ingreso') else '—',
        "dias_trabajados": float(datos['dias_trabajados'] if datos.get('dias_trabajados') is not None else 30),
        # Ajustes por tiempo no trabajado
        "dias_falta": float(datos.get('dias_falta') or 0),
        "monto_falta": monto_falta,
        "dias_septimo_dia": float(datos.get('dias_septimo_dia') or 0),
        "monto_septimo_dia": monto_sep,
        "dias_permiso_sin_goce": float(datos.get('dias_permiso_sin_goce') or 0),
        "monto_permiso_sin_goce": monto_psg,
        "total_ajustes": total_ajustes,
        # Percepciones y Deducciones
        "salario_devengado": sal_devengado,
        "kpi_meta": kpi_meta,
        "total_percepciones": tot_percepciones,
        "inss_laboral": inss_lab,
        "ir": ir_val,
        "adelanto": 0.0,
        "total_deducciones": tot_deducciones,
        "neto_a_recibir": neto_recibir,
        # Vacaciones
        "vac_acumulado": float(datos.get('vac_acumulada') or 0),
        "vac_mes": float(datos['vac_mes'] if datos.get('vac_mes') is not None else 2.5),
        "vac_descansados": float(datos.get('vac_descansados') or 0),
        "vac_saldo": float(datos.get('vac_saldo') or 0),
        # Cargas Patronales
        "inss_patronal": inss_pat,
        "inatec_patronal": inatec_pat,
        "provision_vacaciones": prov_vac,
        "provision_aguinaldo": prov_agui,
        "total_cargas_patronales": tot_cargas_pat,
        "costo_total_patronal": costo_tot_pat
    }

    return render_template('colilla.html', c=c)


# ==============================================================================
# RUTAS DE CORTE V (RRHH, HIGIENE Y SEGURIDAD, REPORTES ESTADÍSTICOS)
# ==============================================================================
from routes_corte_v import register_corte_v_routes
register_corte_v_routes(app)
from routes_rrhh_control import register_rrhh_control_routes
register_rrhh_control_routes(app)

# ==============================================================================
# RUTAS DE ESTADOS FINANCIEROS: FLUJO DE EFECTIVO Y CONCILIACIÓN (RF96 - RF102)
# ==============================================================================
from routes_flujo_efectivo import register_flujo_efectivo_routes
register_flujo_efectivo_routes(app)

# ==============================================================================
# RUTAS DE MÓDULO TRIBUTARIO: DECLARACIÓN ANUAL DGI FORMULARIO 106 (RF129 - RF139)
# ==============================================================================
from routes_fiscal import register_fiscal_routes
register_fiscal_routes(app)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

