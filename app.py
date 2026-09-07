import os
import pyodbc
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from werkzeug.security import generate_password_hash

app = Flask(__name__, template_folder='Fronted/templates', static_folder='Fronted/static')
app.secret_key = os.environ.get('SECRET_KEY', 'jehova_jireh_secret_key_2026_super_secure')

# ==============================================================================
# CONFIGURACIÓN DE BASE DE DATOS SQL SERVER
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

@app.route('/')
def tienda():
    # Obtener los productos reales de la base de datos
    query_productos = """
        SELECT p.id, p.nombre, p.precio_venta, c.nombre AS categoria 
        FROM productos p 
        LEFT JOIN categorias c ON p.categoria_id = c.id 
        WHERE p.activo = 1 AND p.stock_actual > 0
    """
    productos = execute_query(query_productos, fetchall=True)

    # Obtener las categorías que tienen al menos un producto activo
    query_categorias = """
        SELECT DISTINCT c.nombre AS nombre
        FROM productos p
        INNER JOIN categorias c ON p.categoria_id = c.id
        WHERE p.activo = 1 AND p.stock_actual > 0
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

        # Validación en la base de datos SQL Server
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
        else:
            error_msg = "Usuario o contraseña incorrectos."
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
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
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
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
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

# --- VENTAS (POS) ---
@app.route('/api/ventas', methods=['GET', 'POST'])
@login_required
def api_ventas():
    if request.method == 'GET':
        query_v = """
            SELECT v.id, v.codigo_venta, c.nombre_completo AS cliente, v.fecha_venta AS fecha,
                   u.nombre_completo AS vendedor, v.total, v.forma_pago
            FROM ventas v
            LEFT JOIN clientes c ON v.cliente_id = c.id
            INNER JOIN usuarios u ON v.usuario_id = u.id
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
        cliente_id_raw = data.get('cliente_id')
        cliente_id = int(cliente_id_raw) if cliente_id_raw else None
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

            cursor.execute("""
                INSERT INTO ventas (codigo_venta, cliente_id, usuario_id, fecha_venta, subtotal, descuento, total, forma_pago, estado)
                VALUES (?, ?, ?, GETDATE(), ?, 0, ?, ?, 'Completada')
            """, (codigo_v, cliente_id, session['user']['id'], total_venta, total_venta, forma_pago))
            
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
                       u.nombre_completo AS vendedor, v.total, v.forma_pago
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


@app.route('/api/ventas/<int:v_id>', methods=['GET'])
@login_required
def api_venta_detalle(v_id):
    return jsonify({"error": "Detalle único no implementado (la vista general ya los incluye)."}), 501


# --- COMPRAS Y PROVEEDORES ---
@app.route('/api/proveedores', methods=['GET', 'POST'])
@login_required
def api_proveedores():
    if request.method == 'GET':
        provs = execute_query("SELECT id, nombre_empresa AS nombre, contacto_nombre AS contacto, telefono, email FROM proveedores WHERE activo=1", fetchall=True)
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
# MÓDULO CONTABLE Y ESTADOS FINANCIEROS
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

        patrimonio.append({"cuenta": "Utilidad neta del período", "saldo": utilidad_neta})

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
# ==============================================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)