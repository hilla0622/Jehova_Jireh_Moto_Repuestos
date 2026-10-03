import os
import pyodbc
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from calculos_rrhh import calcular_nomina_empleado

app = Flask(__name__, template_folder='Fronted/templates', static_folder='Fronted/static')
app.secret_key = os.environ.get('SECRET_KEY', 'jehova_jireh_secret_key_2026_super_secure')

# ==============================================================================
# CONFIGURACIÃ“N DE BASE DE DATOS SQL SERVER
# ==============================================================================
# Cambia 'LAPTOP-CNR3S3I3' por tu nombre de servidor SQL Server.
DB_SERVER = os.environ.get('DB_SERVER', r'HILLARY')
DB_NAME = 'jehova_jireh_db'

def get_db_connection():
    conn_str = (
        r'DRIVER={ODBC Driver 17 for SQL Server};'
        fr'SERVER={DB_SERVER};'
        fr'DATABASE={DB_NAME};'
        r'Trusted_Connection=yes;'
    )
    conn = pyodbc.connect(conn_str)
    return conn

def execute_query(query, params=(), fetchone=False, fetchall=False, commit=False):
    """FunciÃ³n de ayuda para ejecutar consultas y retornar diccionarios"""
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
                return jsonify({"error": "Acceso denegado: Tu rol no tiene permisos para esta acciÃ³n."}), 403
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

    # Obtener las categorÃ­as que tienen al menos un producto activo
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

        # Verificar si el correo ya estÃ¡ registrado
        check_query = "SELECT id FROM clientes WHERE email = ?"
        user_exists = execute_query(check_query, params=(email,), fetchall=True)

        if user_exists:
            return render_template('registro.html', error='Ese correo electrÃ³nico ya estÃ¡ registrado.')

        # Encriptar la contraseÃ±a
        password_hash = generate_password_hash(password)

        # Insertar el nuevo cliente
        insert_query = """
            INSERT INTO clientes (nombre_completo, email, password_hash, telefono, direccion, tipo_cliente)
            VALUES (?, ?, ?, ?, ?, 'General')
        """
        try:
            execute_query(insert_query, params=(nombre_completo, email, password_hash, telefono, direccion), commit=True)
            # Redirigir al login con Ã©xito (podrÃ­amos usar flash messages, pero por ahora en la URL o render)
            return render_template('login.html', error='Â¡Registro exitoso! Por favor inicia sesiÃ³n con tu nueva cuenta.')
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

        # 1. ValidaciÃ³n como Empleado/Admin en la base de datos SQL Server
        query = """
            SELECT u.id, u.username, u.nombre_completo AS nombre, r.nombre AS rol
            FROM usuarios u
            INNER JOIN roles r ON u.rol_id = r.id
            WHERE u.username = ? AND u.password_hash = ? AND u.activo = 1
        """
        usuario = execute_query(query, (username, password), fetchone=True)
        
        if usuario:
            session['user'] = {
                'id': usuario['id'],
                'username': usuario['username'],
                'nombre': usuario['nombre'],
                'rol': usuario['rol']
            }
            if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"success": True, "redirect": url_for('inicio')})
            return redirect(url_for('inicio'))
            
        # 2. ValidaciÃ³n como Cliente Web
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
        error_msg = "Usuario o contraseÃ±a incorrectos."
        if request.is_json or request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"success": False, "error": error_msg}), 401
        return render_template('login.html', error=error_msg)

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('tienda'))

# ==============================================================================
# ENDPOINTS API (JSON) - CONECTADOS A SQL SERVER
# ==============================================================================

# --- USUARIOS ---
@app.route('/api/usuarios', methods=['GET', 'POST'])
@login_required
def api_usuarios():
    if request.method == 'GET':
        query = """
            SELECT u.id, u.username, u.nombre_completo AS nombre, u.email, u.telefono, r.nombre AS rol 
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
            return jsonify({"error": "Rol no vÃ¡lido."}), 400

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
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
            return jsonify({"error": "No tienes permiso para registrar categorÃ­as."}), 403
        
        data = request.json or {}
        nombre = data.get('nombre', '').strip()
        descripcion = data.get('descripcion', '').strip()

        if not nombre:
            return jsonify({"error": "El nombre de la categorÃ­a es obligatorio."}), 400

        existente = execute_query("SELECT id FROM categorias WHERE nombre = ?", (nombre,), fetchone=True)
        if existente:
            return jsonify({"error": "El nombre de la categorÃ­a ya existe."}), 400

        try:
            execute_query("INSERT INTO categorias (nombre, descripcion) VALUES (?, ?)", (nombre, descripcion), commit=True)
            return jsonify({"success": True, "mensaje": "CategorÃ­a registrada exitosamente."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500

@app.route('/api/categorias/<int:cat_id>', methods=['PUT'])
@login_required
def api_categoria_editar(cat_id):
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
        return jsonify({"error": "No tienes permiso para modificar categorÃ­as."}), 403
    
    data = request.json or {}
    nombre = data.get('nombre', '').strip()
    descripcion = data.get('descripcion', '').strip()

    if not nombre:
        return jsonify({"error": "El nombre de la categorÃ­a es obligatorio."}), 400

    existente = execute_query("SELECT id FROM categorias WHERE nombre = ? AND id != ?", (nombre, cat_id), fetchone=True)
    if existente:
        return jsonify({"error": "El nombre de la categorÃ­a ya existe."}), 400

    try:
        execute_query("UPDATE categorias SET nombre = ?, descripcion = ? WHERE id = ?", (nombre, descripcion, cat_id), commit=True)
        return jsonify({"success": True, "mensaje": "CategorÃ­a actualizada exitosamente."})
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
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
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
            return jsonify({"error": "Nombre, CÃ³digo y Precio vÃ¡lidos son obligatorios."}), 400

        query_insert = """
            INSERT INTO productos (codigo_sku, categoria_id, nombre, costo, precio_venta, stock_actual, stock_minimo)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            # Buscar o crear categorÃ­a
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
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
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
                    VALUES (?, ?, ?, ?, ?, 'Ajuste por ediciÃ³n de producto', ?)
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
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
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
            return jsonify({"error": "SesiÃ³n de caja invÃ¡lida o ya estÃ¡ cerrada."}), 400
            
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
        return jsonify({"error": "SesiÃ³n no encontrada"}), 404
        
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
        if session['user']['rol'] not in ['Administrador', 'Vendedor']:
            return jsonify({"error": "No tienes permiso para procesar ventas."}), 403
        
        data = request.json or {}
        cliente_nombre = data.get('cliente', 'Cliente General').strip()
        forma_pago = data.get('forma_pago', 'Efectivo').strip()
        items = data.get('items', []) 

        if not items:
            return jsonify({"error": "El carrito de compra estÃ¡ vacÃ­o."}), 400

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

            # --- ASIENTO CONTABLE AUTOMÃTICO DE VENTA ---
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
        return jsonify({"error": "El carrito de compra estÃ¡ vacÃ­o."}), 400

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

        # Buscar un admin genÃ©rico para los movimientos que exigen usuario_id NO NULL
        cursor.execute("SELECT TOP 1 u.id FROM usuarios u INNER JOIN roles r ON u.rol_id = r.id WHERE r.nombre = 'Administrador'")
        admin_row = cursor.fetchone()
        admin_id = admin_row[0] if admin_row else 1

        # usuario_id = NULL para ventas web (o pasamos None)
        cursor.execute("""
            INSERT INTO ventas (codigo_venta, cliente_id, nombre_cliente_invitado, usuario_id, fecha_venta, subtotal, descuento, total, forma_pago, estado)
            VALUES (?, ?, ?, NULL, GETDATE(), ?, 0, ?, 'Efectivo', 'Completada')
        """, (codigo_v, cliente_id, nombre_cliente, total_venta, total_venta))
        
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
            """, (p_id, cant, stock_ant, stock_post, f"Venta Web {codigo_v}", 'Venta desde la tienda online', admin_id))

        # --- ASIENTO CONTABLE AUTOMÃTICO DE VENTA WEB ---
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
            VALUES (GETDATE(), ?, 'VENTAS_WEB', ?, ?)
        """, (f"Venta Web {codigo_v}", venta_id, admin_id))
        
        cursor.execute("SELECT @@IDENTITY AS id")
        asiento_v_id = cursor.fetchone()[0]

        cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_v_id, cta_caja, total_venta))
        cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_v_id, cta_ventas, total_venta))
        
        if total_costo_venta > 0:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_v_id, cta_costo, total_costo_venta))
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_v_id, cta_inv, total_costo_venta))

        conn.commit()
        return jsonify({"success": True, "mensaje": f"Venta {codigo_v} procesada con Ã©xito."}), 201

    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
        return jsonify({"error": str(e)}), 500


@app.route('/api/ventas/<int:v_id>', methods=['GET'])
@login_required
def api_venta_detalle(v_id):
    return jsonify({"error": "Detalle Ãºnico no implementado (la vista general ya los incluye)."}), 501



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


# --- COMPRAS Y PROVEEDORES ---
@app.route('/api/proveedores', methods=['GET', 'POST'])
@login_required
def api_proveedores():
    if request.method == 'GET':
        provs = execute_query("SELECT id, nombre_empresa AS nombre, contacto_nombre AS contacto, telefono, email, activo FROM proveedores", fetchall=True)
        return jsonify(provs)

    if request.method == 'POST':
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
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

@app.route('/api/proveedores/<int:prov_id>/estado', methods=['PUT'])
@login_required
def api_proveedor_estado(prov_id):
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
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
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
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

            # --- ASIENTO CONTABLE AUTOMÃTICO DE COMPRA ---
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
    if session['user']['rol'] not in ['Administrador', 'Contador']:
        return jsonify({"error": "Acceso reservado."}), 403

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        resumen = {}
        
        cursor.execute("SELECT COUNT(id) AS cant, SUM(total) as monto FROM ventas WHERE estado='Completada'")
        v = cursor.fetchone()
        resumen['ventas_totales_conteo'] = v.cant if v.cant else 0
        resumen['ventas_totales_monto'] = float(v.monto) if v.monto else 0.0

        cursor.execute("SELECT COUNT(id) AS cant, SUM(total) as monto FROM compras WHERE estado='Completada'")
        c = cursor.fetchone()
        resumen['compras_totales_conteo'] = c.cant if c.cant else 0
        resumen['compras_totales_monto'] = float(c.monto) if c.monto else 0.0

        cursor.execute("SELECT * FROM vista_balance_inventario")
        b = cursor.fetchone()
        resumen['valor_inventario_costo'] = float(b.valor_total_costo) if b and b.valor_total_costo else 0.0
        resumen['margen_bruto_estimado'] = float(b.ganancia_proyectada) if b and b.ganancia_proyectada else 0.0

        cursor.execute("SELECT id, repuesto AS nombre, stock_actual AS stock, stock_minimo AS min_stock FROM vista_stock_bajo")
        sb_rows = cursor.fetchall()
        productos_bajo_stock = []
        for r in sb_rows:
            productos_bajo_stock.append({"id": r.id, "nombre": r.nombre, "stock": r.stock, "min_stock": r.min_stock})
        resumen['alerta_stock_bajo_conteo'] = len(productos_bajo_stock)
        resumen['productos_bajo_stock'] = productos_bajo_stock

        cursor.execute("SELECT producto_id AS id, repuesto AS nombre, total_unidades_vendidas AS cantidad_vendida, ingreso_total_generado AS monto_total FROM vista_top_productos_vendidos ORDER BY total_unidades_vendidas DESC")
        top_rows = cursor.fetchall()
        top_productos = []
        for r in top_rows:
            top_productos.append({"id": r.id, "nombre": r.nombre, "cantidad_vendida": r.cantidad_vendida, "monto_total": float(r.monto_total)})
        resumen['top_productos'] = top_productos

        cursor.execute("SELECT CONVERT(varchar, fecha_venta, 23) as f, SUM(total) as t FROM ventas WHERE estado='Completada' GROUP BY CONVERT(varchar, fecha_venta, 23)")
        vf_rows = cursor.fetchall()
        ventas_por_fecha = {}
        for r in vf_rows:
            ventas_por_fecha[r.f] = float(r.t)
        resumen['ventas_por_fecha'] = ventas_por_fecha
        
        resumen['unidades_vendidas_total'] = sum(p['cantidad_vendida'] for p in top_productos)
        
        stock_total_actual = b.total_unidades_fisicas if b and b.total_unidades_fisicas else 0
        resumen['rotacion_inventario'] = round(resumen['unidades_vendidas_total'] / (stock_total_actual if stock_total_actual > 0 else 1), 2)

        return jsonify(resumen)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals():
            conn.close()

# ==============================================================================
# MÃ“DULO CONTABLE Y ESTADOS FINANCIEROS
# ==============================================================================

@app.route('/api/finanzas/cuentas', methods=['GET', 'POST'])
@login_required
def api_cuentas_contables():
    if session['user']['rol'] not in ['Administrador', 'Contador']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403
    
    if request.method == 'GET':
        try:
            cuentas = execute_query("SELECT * FROM cuentas_contables ORDER BY codigo ASC", fetchall=True)
            return jsonify(cuentas)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    if request.method == 'POST':
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
    if session['user']['rol'] not in ['Administrador', 'Contador']:
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
    if session['user']['rol'] not in ['Administrador', 'Contador']:
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

@app.route('/api/finanzas/balance_comprobacion', methods=['GET'])
@login_required
def api_balance_comprobacion():
    if session['user']['rol'] not in ['Administrador', 'Contador']:
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
    if session['user']['rol'] not in ['Administrador', 'Contador']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403
    try:
        start_date = request.args.get('start')
        end_date = request.args.get('end')
        
        where_clause = ""
        params = []
        if start_date and end_date:
            where_clause = "AND CAST(a.fecha AS DATE) >= ? AND CAST(a.fecha AS DATE) <= ?"
            params.extend([start_date, end_date])
        elif start_date:
            where_clause = "AND CAST(a.fecha AS DATE) >= ?"
            params.append(start_date)
        elif end_date:
            where_clause = "AND CAST(a.fecha AS DATE) <= ?"
            params.append(end_date)

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
    if session['user']['rol'] not in ['Administrador', 'Contador']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403
    try:
        end_date = request.args.get('end')
        
        where_clause_a = ""
        params_a = []
        if end_date:
            where_clause_a = "AND CAST(a.fecha AS DATE) <= ?"
            params_a.append(end_date)

        # Calcular Utilidad Neta primero (para agregarla al Patrimonio)
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
        total_patrimonio = utilidad_neta # Inicializamos con la utilidad del ejercicio
        
        for f in filas_bg:
            debe = float(f['d'] or 0)
            haber = float(f['h'] or 0)
            saldo = (haber - debe) if f['naturaleza'] == 'Acreedora' else (debe - haber)
            
            # Ajuste para cuentas contra-activo (ej. DepreciaciÃ³n acumulada) que son naturaleza Acreedora pero van en Activos
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

        patrimonio.append({"cuenta": "Utilidad neta del perÃ­odo", "saldo": utilidad_neta})

        return jsonify({
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
# RECURSOS HUMANOS Y NÃ“MINA
# Roles permitidos: Administrador, Responsable de Recursos Humanos
# ==============================================================================
ROLES_RRHH = ['Administrador', 'Responsable de Recursos Humanos']


@app.route('/api/empleados', methods=['GET', 'POST'])
@login_required
def api_empleados():
    """GET: Lista empleados activos. POST: Registrar nuevo empleado."""
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
            return jsonify({"error": "Nombre y Salario base vÃ¡lidos son obligatorios."}), 400

        try:
            execute_query(
                """INSERT INTO empleados
                   (nombre_completo, identificacion, num_inss, cargo, salario_base,
                    fecha_ingreso, telefono, email, observaciones)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (nombre, identificacion, num_inss, cargo, salario_base,
                 fecha_ingreso, telefono, email, observaciones),
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
                SELECT ml.id, e.nombre_completo AS empleado, ml.tipo,
                       ml.fecha_inicio, ml.fecha_fin, ml.dias_tomados, ml.observacion, ml.created_at
                FROM movimientos_laborales ml
                JOIN empleados e ON ml.empleado_id = e.id
                WHERE ml.empleado_id = ?
                ORDER BY ml.fecha_inicio DESC
            """
            movimientos = execute_query(query, (emp_id,), fetchall=True)
        else:
            query = """
                SELECT ml.id, e.nombre_completo AS empleado, ml.tipo,
                       ml.fecha_inicio, ml.fecha_fin, ml.dias_tomados, ml.observacion, ml.created_at
                FROM movimientos_laborales ml
                JOIN empleados e ON ml.empleado_id = e.id
                ORDER BY ml.created_at DESC
            """
            movimientos = execute_query(query, fetchall=True)
        # Serializar fechas
        for m in movimientos:
            if m.get('fecha_inicio'): m['fecha_inicio'] = str(m['fecha_inicio'])
            if m.get('fecha_fin'):    m['fecha_fin']    = str(m['fecha_fin'])
            if m.get('created_at'):   m['created_at']   = str(m['created_at'])
        return jsonify(movimientos)

    if request.method == 'POST':
        data = request.json or {}
        empleado_id  = data.get('empleado_id')
        tipo         = data.get('tipo', '')
        fecha_inicio = data.get('fecha_inicio', '')
        fecha_fin    = data.get('fecha_fin', '')
        dias_tomados = float(data.get('dias_tomados', 0))
        observacion  = data.get('observacion', '').strip()

        if not empleado_id or not tipo or not fecha_inicio or not fecha_fin or dias_tomados <= 0:
            return jsonify({"error": "Todos los campos son obligatorios y los dÃ­as deben ser mayores a 0."}), 400

        tipos_validos = ['VACACIONES', 'PERMISO_CON_GOCE', 'PERMISO_SIN_GOCE', 'FALTA']
        if tipo not in tipos_validos:
            return jsonify({"error": f"Tipo invÃ¡lido. Use: {tipos_validos}"}), 400

        try:
            execute_query(
                """INSERT INTO movimientos_laborales
                   (empleado_id, tipo, fecha_inicio, fecha_fin, dias_tomados, observacion)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (empleado_id, tipo, fecha_inicio, fecha_fin, dias_tomados, observacion),
                commit=True
            )
            # Si es vacaciones, descontar dÃ­as disponibles del empleado
            if tipo == 'VACACIONES':
                execute_query(
                    "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles - ? WHERE id = ?",
                    (dias_tomados, empleado_id), commit=True
                )
            return jsonify({"success": True, "mensaje": "Movimiento registrado exitosamente."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500


# --- GENERACIÃ“N DE NÃ“MINA ---
@app.route('/api/nomina/generar', methods=['POST'])
@login_required
def api_nomina_generar():
    """Genera la nÃ³mina mensual para todos los empleados activos con cÃ¡lculos correctos Ley 822 + Ley 185."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos para generar nÃ³minas."}), 403

    data = request.json or {}
    mes  = int(data.get('mes', 1))
    anio = int(data.get('anio', 2026))

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        # Validar duplicado o recuperar cabecera
        cursor.execute("SELECT id FROM nomina WHERE periodo_mes = ? AND periodo_anio = ?", (mes, anio))
        row = cursor.fetchone()
        if row:
            nomina_id = int(row[0])
            es_complemento = True
        else:
            cursor.execute("INSERT INTO nomina (periodo_mes, periodo_anio) VALUES (?, ?)", (mes, anio))
            cursor.execute("SELECT @@IDENTITY AS id")
            nomina_id = int(cursor.fetchone()[0])
            es_complemento = False

        empleado_id_param = data.get('empleado_id', 'all')
        if empleado_id_param != 'all':
            cursor.execute("""
                SELECT id, salario_base FROM empleados 
                WHERE activo=1 AND id=? 
                AND id NOT IN (SELECT empleado_id FROM detalle_nomina WHERE nomina_id = ?)
            """, (empleado_id_param, nomina_id))
        else:
            cursor.execute("""
                SELECT id, salario_base FROM empleados 
                WHERE activo=1 
                AND id NOT IN (SELECT empleado_id FROM detalle_nomina WHERE nomina_id = ?)
            """, (nomina_id,))

        empleados = cursor.fetchall()
        
        if not empleados:
            conn.close()
            return jsonify({"error": f"La nÃ³mina {mes}/{anio} ya fue generada para el/los empleado(s) seleccionado(s)."}), 400

        t_bruto       = 0.0
        t_deducciones = 0.0
        t_inss_lab    = 0.0
        t_ir          = 0.0
        t_neto        = 0.0
        t_patronal    = 0.0
        t_vac         = 0.0
        t_agui        = 0.0

        for emp in empleados:
            e_id   = emp[0]
            salario = float(emp[1])

            # Usar mÃ³dulo de cÃ¡lculos con lÃ³gica correcta
            calc = calcular_nomina_empleado(salario)

            cursor.execute(
                """INSERT INTO detalle_nomina
                   (nomina_id, empleado_id, salario_base, ingresos_extra, ir,
                    inss_laboral, neto_pagar, inss_patronal,
                    provision_vacaciones, provision_aguinaldo)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (nomina_id, e_id,
                 calc['salario_ordinario'],
                 calc['ingresos_extra'],
                 calc['ir_retencion'],
                 calc['inss_laboral'],
                 calc['salario_neto'],
                 calc['inss_patronal'],
                 calc['provision_vacaciones'],
                 calc['provision_aguinaldo'])
            )

            # Acumular dÃ­as de vacaciones ganados este mes (1.25 dÃ­as = 15 dÃ­as / 12 meses)
            cursor.execute(
                "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles + 1.25 WHERE id = ?",
                (e_id,)
            )

            t_bruto       += calc['salario_bruto']
            t_deducciones += calc['total_deducciones']
            t_inss_lab    += calc['inss_laboral']
            t_ir          += calc['ir_retencion']
            t_neto        += calc['salario_neto']
            t_patronal    += calc['inss_patronal']
            t_vac         += calc['provision_vacaciones']
            t_agui        += calc['provision_aguinaldo']

        # Actualizar totales en cabecera
        cursor.execute(
            """UPDATE nomina
               SET total_ingresos=total_ingresos+?, total_deducciones=total_deducciones+?, total_neto=total_neto+?,
                   inss_patronal_total=inss_patronal_total+?, provision_vac_total=provision_vac_total+?, provision_agui_total=provision_agui_total+?
               WHERE id=?""",
            (round(t_bruto, 2), round(t_deducciones, 2), round(t_neto, 2),
             round(t_patronal, 2), round(t_vac, 2), round(t_agui, 2), nomina_id)
        )

        # --- ASIENTO CONTABLE AUTOMÃTICO DE NÃ“MINA ---
        def get_cta(codigo):
            cursor.execute("SELECT id FROM cuentas_contables WHERE codigo = ?", (codigo,))
            row = cursor.fetchone()
            return row[0] if row else None
            
        cta_sueldos_gasto = get_cta('6.1.01')
        cta_cargas_patronales = get_cta('6.1.11')
        cta_prestaciones_gasto = get_cta('6.1.12')
        
        cta_retenciones_inss = get_cta('2.1.06')
        cta_retenciones_ir = get_cta('2.1.07')
        cta_provisiones = get_cta('2.1.08')
        cta_sueldos_pagar = get_cta('2.1.04')
        
        concepto_asiento = f"Registro de nÃ³mina mes {mes:02d}/{anio}"
        if es_complemento:
            concepto_asiento = f"Registro de nÃ³mina mes {mes:02d}/{anio} (Complemento)"
        cursor.execute("""
            INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
            VALUES (GETDATE(), ?, 'RRHH', ?, ?)
        """, (concepto_asiento, nomina_id, session['user']['id']))
        cursor.execute("SELECT @@IDENTITY AS id")
        asiento_id = cursor.fetchone()[0]
        
        # DÃ©bitos (Gastos)
        if t_bruto > 0 and cta_sueldos_gasto:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_id, cta_sueldos_gasto, round(t_bruto, 2)))
        if t_patronal > 0 and cta_cargas_patronales:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_id, cta_cargas_patronales, round(t_patronal, 2)))
        t_prestaciones = t_vac + t_agui
        if t_prestaciones > 0 and cta_prestaciones_gasto:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, ?, 0)", (asiento_id, cta_prestaciones_gasto, round(t_prestaciones, 2)))
            
        # CrÃ©ditos (Pasivos)
        t_inss_total = t_inss_lab + t_patronal
        if t_inss_total > 0 and cta_retenciones_inss:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_retenciones_inss, round(t_inss_total, 2)))
        if t_ir > 0 and cta_retenciones_ir:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_retenciones_ir, round(t_ir, 2)))
        if t_prestaciones > 0 and cta_provisiones:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_provisiones, round(t_prestaciones, 2)))
        if t_neto > 0 and cta_sueldos_pagar:
            cursor.execute("INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber) VALUES (?, ?, 0, ?)", (asiento_id, cta_sueldos_pagar, round(t_neto, 2)))

        conn.commit()
        conn.close()
        return jsonify({
            "success"   : True,
            "mensaje"   : f"NÃ³mina {mes:02d}/{anio} generada con Ã©xito para {len(empleados)} empleados.",
            "nomina_id" : nomina_id,
            "resumen"   : {
                "total_bruto"      : round(t_bruto, 2),
                "total_deducciones": round(t_deducciones, 2),
                "total_neto"       : round(t_neto, 2),
                "inss_patronal"    : round(t_patronal, 2),
                "provision_vac"    : round(t_vac, 2),
                "provision_agui"   : round(t_agui, 2)
            }
        }), 201

    except Exception as e:
        if 'conn' in locals() and conn:
            conn.rollback()
            conn.close()
        return jsonify({"error": str(e)}), 500


@app.route('/api/nomina/historial', methods=['GET'])
@login_required
def api_nomina_historial():
    """Lista el historial de todas las nÃ³minas generadas."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403
    query2 = """
        SELECT id, periodo_mes AS mes, periodo_anio AS anio, fecha_generacion,
               total_ingresos, total_deducciones, total_neto,
               ISNULL(inss_patronal_total, 0) AS inss_patronal_total,
               ISNULL(provision_vac_total, 0) AS provision_vac_total,
               ISNULL(provision_agui_total, 0) AS provision_agui_total,
               ISNULL(estado, 'CERRADA') AS estado
        FROM nomina
        ORDER BY periodo_anio DESC, periodo_mes DESC
    """
    nominas = execute_query(query2, fetchall=True)
    for n in nominas:
        for campo in ['total_ingresos', 'total_deducciones', 'total_neto',
                      'inss_patronal_total', 'provision_vac_total', 'provision_agui_total']:
            if campo in n and n[campo] is not None:
                n[campo] = float(n[campo])
        if n.get('fecha_generacion'):
            n['fecha_generacion'] = str(n['fecha_generacion'])
    return jsonify(nominas)


@app.route('/api/nomina/<int:nomina_id>/detalle', methods=['GET'])
@login_required
def api_nomina_detalle(nomina_id):
    """Obtiene el detalle completo de una nÃ³mina: cabecera + lÃ­neas por empleado."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403
    cabecera = execute_query(
        """SELECT id, periodo_mes AS mes, periodo_anio AS anio, fecha_generacion,
                  total_ingresos, total_deducciones, total_neto,
                  ISNULL(inss_patronal_total,0) AS inss_patronal_total,
                  ISNULL(provision_vac_total,0) AS provision_vac_total,
                  ISNULL(provision_agui_total,0) AS provision_agui_total,
                  ISNULL(estado,'CERRADA') AS estado
           FROM nomina WHERE id=?""",
        (nomina_id,), fetchone=True
    )
    if not cabecera:
        return jsonify({"error": "NÃ³mina no encontrada."}), 404

    detalles = execute_query(
        """SELECT dn.id, e.id AS empleado_id, e.nombre_completo AS empleado, e.identificacion, e.cargo,
                  dn.salario_base, ISNULL(dn.ingresos_extra,0) AS ingresos_extra,
                  dn.inss_laboral, dn.ir,
                  ISNULL(dn.inss_patronal,0) AS inss_patronal,
                  ISNULL(dn.provision_vacaciones,0) AS provision_vacaciones,
                  ISNULL(dn.provision_aguinaldo,0) AS provision_aguinaldo,
                  dn.neto_pagar
           FROM detalle_nomina dn
           JOIN empleados e ON dn.empleado_id = e.id
           WHERE dn.nomina_id=?
           ORDER BY e.nombre_completo""",
        (nomina_id,), fetchall=True
    )
    campos_float = ['salario_base', 'ingresos_extra', 'inss_laboral', 'ir',
                    'inss_patronal', 'provision_vacaciones', 'provision_aguinaldo', 'neto_pagar']
    for d in detalles:
        for c in campos_float:
            if c in d and d[c] is not None:
                d[c] = float(d[c])
    for c in ['total_ingresos', 'total_deducciones', 'total_neto',
               'inss_patronal_total', 'provision_vac_total', 'provision_agui_total']:
        if cabecera.get(c) is not None:
            cabecera[c] = float(cabecera[c])
    if cabecera.get('fecha_generacion'):
        cabecera['fecha_generacion'] = str(cabecera['fecha_generacion'])
    return jsonify({"cabecera": cabecera, "detalles": detalles})


@app.route('/api/nomina/<int:nomina_id>/empleado/<int:emp_id>', methods=['GET'])
@login_required
def api_colilla_individual(nomina_id, emp_id):
    """Obtiene la colilla (recibo) individual de pago de un empleado en una nÃ³mina."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403
    nomina = execute_query(
        "SELECT id, periodo_mes AS mes, periodo_anio AS anio, fecha_generacion FROM nomina WHERE id=?",
        (nomina_id,), fetchone=True
    )
    if not nomina:
        return jsonify({"error": "NÃ³mina no encontrada."}), 404
    if nomina.get('fecha_generacion'):
        nomina['fecha_generacion'] = str(nomina['fecha_generacion'])

    detalle = execute_query(
        """SELECT e.nombre_completo AS empleado, e.identificacion, e.num_inss, e.cargo,
                  dn.salario_base, ISNULL(dn.ingresos_extra,0) AS ingresos_extra,
                  dn.inss_laboral, dn.ir,
                  ISNULL(dn.inss_patronal,0) AS inss_patronal,
                  ISNULL(dn.provision_vacaciones,0) AS provision_vacaciones,
                  ISNULL(dn.provision_aguinaldo,0) AS provision_aguinaldo,
                  dn.neto_pagar
           FROM detalle_nomina dn
           JOIN empleados e ON dn.empleado_id = e.id
           WHERE dn.nomina_id=? AND dn.empleado_id=?""",
        (nomina_id, emp_id), fetchone=True
    )
    if not detalle:
        return jsonify({"error": "Detalle de empleado no encontrado en esta nÃ³mina."}), 404
    campos_float = ['salario_base', 'ingresos_extra', 'inss_laboral', 'ir',
                    'inss_patronal', 'provision_vacaciones', 'provision_aguinaldo', 'neto_pagar']
    for c in campos_float:
        if detalle.get(c) is not None:
            detalle[c] = float(detalle[c])
    detalle['salario_bruto'] = round(
        detalle['salario_base'] + detalle['ingresos_extra'], 2
    )
    detalle['total_deducciones'] = round(
        detalle['inss_laboral'] + detalle['ir'], 2
    )
    return jsonify({"nomina": nomina, "colilla": detalle})


@app.route('/api/nomina/<int:nomina_id>', methods=['DELETE'])
@login_required
def api_nomina_delete(nomina_id):
    """Elimina una nÃ³mina completa y revierte las vacaciones acumuladas."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Verificar que existe
        cursor.execute("SELECT id FROM nomina WHERE id=?", (nomina_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "NÃ³mina no encontrada."}), 404

        # Revertir vacaciones (restar los 1.25 que se sumaron a cada empleado en esta nÃ³mina)
        cursor.execute("SELECT empleado_id FROM detalle_nomina WHERE nomina_id=?", (nomina_id,))
        empleados_en_nomina = cursor.fetchall()
        for emp in empleados_en_nomina:
            cursor.execute(
                "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles - 1.25 WHERE id = ?",
                (emp[0],)
            )

        # Eliminar la nÃ³mina (ON DELETE CASCADE debe borrar detalle_nomina)
        cursor.execute("DELETE FROM nomina WHERE id=?", (nomina_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ==============================================================================
# RECURSOS HUMANOS - COLILLA DE PAGO (vista imprimible)
# ==============================================================================
@app.route('/rrhh/colilla/<int:id_detalle>')
@login_required
@role_required('Administrador', 'Responsable de Recursos Humanos')
def ver_colilla(id_detalle):
    query = """
        SELECT
            e.nombre_completo as empleado,
            e.identificacion as cedula,
            e.cargo,
            e.num_inss as inss,
            e.salario_base as salario_contrato,
            e.fecha_ingreso,
            n.periodo_mes as periodo_mes,
            n.periodo_anio as periodo_anio,
            d.salario_base as salario_devengado,
            ISNULL(d.ingresos_extra,0) as kpi_meta,
            (d.salario_base + ISNULL(d.ingresos_extra,0)) as total_percepciones,
            d.inss_laboral,
            d.ir,
            (d.inss_laboral + d.ir) as total_deducciones,
            d.neto_pagar as neto_a_recibir,
            ISNULL(e.dias_vacaciones_disponibles, 0) as vac_saldo
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
    mes_nombre = meses_es[datos.get('periodo_mes', 0)] if datos.get('periodo_mes') else 'â€”'
    periodo = f"{mes_nombre} {datos.get('periodo_anio', '')}"

    c = {
        "empresa": "JehovÃ¡ Jireh Moto Repuestos",
        "periodo": periodo,
        "empleado": datos['empleado'],
        "cedula": datos.get('cedula') or 'N/A',
        "cargo": datos.get('cargo') or 'Empleado',
        "departamento": 'General',
        "inss": datos.get('inss') or 'N/A',
        "salario_contrato": float(datos.get('salario_contrato') or 0),
        "fecha_ingreso": str(datos.get('fecha_ingreso', ''))[:10] if datos.get('fecha_ingreso') else 'â€”',
        "dias_trabajados": 30,
        "vac_acumulado": float(datos.get('vac_saldo') or 0),
        "vac_mes": 1.25,
        "vac_descansados": 0.0,
        "vac_saldo": float(datos.get('vac_saldo') or 0),
        "salario_devengado": float(datos.get('salario_devengado') or 0),
        "kpi_meta": float(datos.get('kpi_meta') or 0),
        "total_percepciones": float(datos.get('total_percepciones') or 0),
        "inss_laboral": float(datos.get('inss_laboral') or 0),
        "ir": float(datos.get('ir') or 0),
        "adelanto": 0.0,
        "total_deducciones": float(datos.get('total_deducciones') or 0),
        "neto_a_recibir": float(datos.get('neto_a_recibir') or 0)
    }

    return render_template('colilla.html', c=c)


# ==============================================================================
# ==============================================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)