import os
import pyodbc
from datetime import datetime, date, timedelta
import math
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__, template_folder='Fronted/templates', static_folder='Fronted/static')
app.secret_key = os.environ.get('SECRET_KEY', 'jehova_jireh_secret_key_2026_super_secure')

# ==============================================================================
# CONFIGURACIÓN DE BASE DE DATOS SQL SERVER
# ==============================================================================
# Cambia 'LAPTOP-CNR3S3I3' por tu nombre de servidor SQL Server.
DB_SERVER = os.environ.get('DB_SERVER', r'localhost')
DB_NAME = 'jehova_jireh_db'

def get_db_connection():
    servers = [DB_SERVER, 'localhost', r'NELLA', r'.', r'HILLARY']
    seen = set()
    unique_servers = [s for s in servers if s and not (s in seen or seen.add(s))]
    
    last_err = None
    for srv in unique_servers:
        try:
            conn_str = (
                r'DRIVER={ODBC Driver 17 for SQL Server};'
                fr'SERVER={srv};'
                fr'DATABASE={DB_NAME};'
                r'Trusted_Connection=yes;'
            )
            return pyodbc.connect(conn_str, timeout=3)
        except Exception as e:
            last_err = e
            continue
    raise last_err

def check_or_update_db_schema():
    """Verifica y actualiza columnas necesarias de forma segura si no existen."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            IF NOT EXISTS (
                SELECT * FROM sys.columns 
                WHERE object_id = OBJECT_ID('ventas') AND name = 'canal_venta'
            )
            BEGIN
                ALTER TABLE ventas ADD canal_venta VARCHAR(50) DEFAULT 'Tienda Física';
            END
        """)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Nota en actualización de esquema: {e}")

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
@app.route('/')
@login_required
def inicio():
    return render_template('index.html', usuario=session.get('user'))

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
    return redirect(url_for('login'))

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

# --- CATEGORÍAS ---
@app.route('/api/categorias', methods=['GET'])
@login_required
def api_categorias():
    categorias = execute_query("SELECT id, nombre, descripcion FROM categorias ORDER BY nombre", fetchall=True)
    return jsonify(categorias)

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
                   u.nombre_completo AS vendedor, v.total, v.forma_pago,
                   ISNULL(v.canal_venta, 'Tienda Física') AS canal_venta
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
        cliente_id = int(data.get('cliente_id', 1)) 
        forma_pago = data.get('forma_pago', 'Efectivo').strip()
        canal_venta = data.get('canal_venta', 'Tienda Física').strip()
        items = data.get('items', []) 

        if not items:
            return jsonify({"error": "El carrito de compra está vacío."}), 400

        try:
            check_or_update_db_schema()
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
                INSERT INTO ventas (codigo_venta, cliente_id, usuario_id, fecha_venta, subtotal, descuento, total, forma_pago, canal_venta, estado)
                VALUES (?, ?, ?, GETDATE(), ?, 0, ?, ?, ?, 'Completada')
            """, (codigo_v, cliente_id, session['user']['id'], total_venta, total_venta, forma_pago, canal_venta))
            
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

            conn.commit()
            
            # Recuperar venta completa para retornar al ticket
            venta_creada = {
                "id": venta_id,
                "codigo_venta": codigo_v,
                "cliente": "Cliente General",
                "vendedor": session['user']['nombre'],
                "fecha": date.today().strftime('%Y-%m-%d'),
                "total": total_venta,
                "forma_pago": forma_pago,
                "canal_venta": canal_venta,
                "detalles": [
                    {"producto_nombre": execute_query("SELECT nombre FROM productos WHERE id=?", (item[0],), fetchone=True)['nombre'],
                     "cantidad": item[1], "precio_unitario": item[2], "subtotal": item[4]}
                    for item in detalles_a_insertar
                ]
            }
            return jsonify({"success": True, "mensaje": f"Venta {codigo_v} procesada.", "venta": venta_creada}), 201

        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            return jsonify({"error": str(e)}), 500


@app.route('/api/ventas/<int:v_id>', methods=['GET'])
@login_required
def api_venta_detalle(v_id):
    q = """
        SELECT v.id, v.codigo_venta, c.nombre_completo AS cliente, v.fecha_venta AS fecha,
               u.nombre_completo AS vendedor, v.total, v.forma_pago,
               ISNULL(v.canal_venta, 'Tienda Física') AS canal_venta
        FROM ventas v
        LEFT JOIN clientes c ON v.cliente_id = c.id
        INNER JOIN usuarios u ON v.usuario_id = u.id
        WHERE v.id = ?
    """
    venta = execute_query(q, (v_id,), fetchone=True)
    if not venta:
        return jsonify({"error": "Venta no encontrada."}), 404
        
    if hasattr(venta['fecha'], 'strftime'):
        venta['fecha'] = venta['fecha'].strftime('%Y-%m-%d')
    venta['total'] = float(venta['total'])
    
    detalles = execute_query("""
        SELECT p.id AS producto_id, p.nombre AS producto_nombre, d.cantidad, d.precio_unitario, d.subtotal 
        FROM detalle_ventas d
        INNER JOIN productos p ON d.producto_id = p.id
        WHERE d.venta_id = ?
    """, (v_id,), fetchall=True)
    for d in detalles:
        d['precio_unitario'] = float(d['precio_unitario'])
        d['subtotal'] = float(d['subtotal'])
    venta['detalles'] = detalles
    
    return jsonify(venta)


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

            conn.commit()
            return jsonify({"success": True, "mensaje": "Compra registrada."}), 201

        except Exception as e:
            if 'conn' in locals():
                conn.rollback()
            return jsonify({"error": str(e)}), 500

# --- REPORTES Y CONTABILIDAD AVANZADA ---
@app.route('/api/reportes', methods=['GET'])
@login_required
def api_reportes():
    if session['user']['rol'] not in ['Administrador', 'Contador']:
        return jsonify({"error": "Acceso reservado a Administrador y Contador."}), 403

    try:
        check_or_update_db_schema()
        conn = get_db_connection()
        cursor = conn.cursor()

        # Parámetros recibidos
        periodo = request.args.get('periodo', 'mes').strip().lower() # hoy, 7_dias, mes, año, historico, personalizado
        param_fecha_inicio = request.args.get('fecha_inicio', '').strip()
        param_fecha_fin = request.args.get('fecha_fin', '').strip()
        comparar = request.args.get('comparar', 'false').lower() == 'true'
        categoria_id = request.args.get('categoria_id', 'all').strip()
        producto_id = request.args.get('producto_id', 'all').strip()
        canal_venta = request.args.get('canal_venta', 'all').strip()
        agrupacion_tiempo = request.args.get('agrupacion', 'dia').strip().lower() # dia, semana, mes
        top_n = int(request.args.get('top_n', 10))

        today = date.today()

        # 1. Determinación de rangos de fechas (Período actual y previo)
        if periodo == 'hoy':
            dt_inicio = today
            dt_fin = today
            prev_inicio = today - timedelta(days=1)
            prev_fin = today - timedelta(days=1)
            nombre_periodo = f"Hoy ({today.strftime('%d/%m/%Y')})"
            nombre_periodo_ant = f"Ayer ({prev_inicio.strftime('%d/%m/%Y')})"
        elif periodo == '7_dias':
            dt_inicio = today - timedelta(days=6)
            dt_fin = today
            prev_inicio = today - timedelta(days=13)
            prev_fin = today - timedelta(days=7)
            nombre_periodo = f"Últimos 7 Días ({dt_inicio.strftime('%d/%m')} - {dt_fin.strftime('%d/%m/%Y')})"
            nombre_periodo_ant = f"7 Días Previos ({prev_inicio.strftime('%d/%m')} - {prev_fin.strftime('%d/%m/%Y')})"
        elif periodo == 'mes':
            dt_inicio = date(today.year, today.month, 1)
            dt_fin = today
            first_day_curr = dt_inicio
            last_day_prev = first_day_curr - timedelta(days=1)
            prev_inicio = date(last_day_prev.year, last_day_prev.month, 1)
            prev_fin = last_day_prev
            nombre_periodo = f"Mes en Curso ({dt_inicio.strftime('%d/%m')} - {dt_fin.strftime('%d/%m/%Y')})"
            nombre_periodo_ant = f"Mes Anterior ({prev_inicio.strftime('%B %Y')})"
        elif periodo == 'año':
            dt_inicio = date(today.year, 1, 1)
            dt_fin = today
            prev_inicio = date(today.year - 1, 1, 1)
            prev_fin = date(today.year - 1, 12, 31)
            nombre_periodo = f"Año en Curso ({today.year})"
            nombre_periodo_ant = f"Año Anterior ({today.year - 1})"
        elif periodo == 'personalizado':
            try:
                dt_inicio = datetime.strptime(param_fecha_inicio, '%Y-%m-%d').date()
            except Exception:
                dt_inicio = today - timedelta(days=30)
            try:
                dt_fin = datetime.strptime(param_fecha_fin, '%Y-%m-%d').date()
            except Exception:
                dt_fin = today
            if dt_inicio > dt_fin:
                dt_inicio, dt_fin = dt_fin, dt_inicio
            duracion = (dt_fin - dt_inicio).days
            prev_fin = dt_inicio - timedelta(days=1)
            prev_inicio = prev_fin - timedelta(days=duracion)
            nombre_periodo = f"Personalizado ({dt_inicio.strftime('%d/%m/%Y')} al {dt_fin.strftime('%d/%m/%Y')})"
            nombre_periodo_ant = f"Período Previo ({prev_inicio.strftime('%d/%m/%Y')} al {prev_fin.strftime('%d/%m/%Y')})"
        else: # historico
            dt_inicio = date(2000, 1, 1)
            dt_fin = date(2099, 12, 31)
            prev_inicio = None
            prev_fin = None
            nombre_periodo = "Histórico Total"
            nombre_periodo_ant = "N/A"

        # Función de consulta de detalle de ventas en rango
        def consultar_ventas_rango(ini, fin):
            where_clauses = ["v.estado = 'Completada'", "CAST(v.fecha_venta AS DATE) >= ?", "CAST(v.fecha_venta AS DATE) <= ?"]
            params = [ini.strftime('%Y-%m-%d'), fin.strftime('%Y-%m-%d')]

            if categoria_id != 'all':
                where_clauses.append("p.categoria_id = ?")
                params.append(int(categoria_id))
            if producto_id != 'all':
                where_clauses.append("p.id = ?")
                params.append(int(producto_id))
            if canal_venta != 'all':
                where_clauses.append("(v.canal_venta = ? OR (? = 'Tienda Física' AND v.canal_venta IS NULL))")
                params.extend([canal_venta, canal_venta])

            q = f"""
                SELECT dv.id, dv.venta_id, dv.producto_id, dv.cantidad, dv.precio_unitario, dv.costo_historico, dv.subtotal,
                       v.codigo_venta, v.fecha_venta, v.total as venta_total, v.forma_pago,
                       ISNULL(v.canal_venta, 'Tienda Física') as canal_venta,
                       p.codigo_sku, p.nombre as producto_nombre, p.categoria_id, c.nombre as categoria_nombre,
                       p.stock_actual, p.stock_minimo, p.costo as costo_actual, p.precio_venta as precio_actual
                FROM detalle_ventas dv
                INNER JOIN ventas v ON dv.venta_id = v.id
                INNER JOIN productos p ON dv.producto_id = p.id
                INNER JOIN categorias c ON p.categoria_id = c.id
                WHERE {' AND '.join(where_clauses)}
                ORDER BY v.fecha_venta ASC, v.id ASC
            """
            cursor.execute(q, tuple(params))
            if cursor.description is None: return []
            cols = [col[0] for col in cursor.description]
            rows = cursor.fetchall()
            return [dict(zip(cols, r)) for r in rows]

        ventas_actual = consultar_ventas_rango(dt_inicio, dt_fin)

        # -------------------------------------------------------------
        # 1. CÁLCULO DE KPIS PRINCIPALES (Métricas cuánticas)
        # -------------------------------------------------------------
        ventas_netas = sum(float(r['subtotal']) for r in ventas_actual)
        unidades_vendidas = sum(int(r['cantidad']) for r in ventas_actual)
        ventas_unicas_ids = set(r['venta_id'] for r in ventas_actual)
        transacciones_conteo = len(ventas_unicas_ids)
        ticket_promedio = round(ventas_netas / transacciones_conteo, 2) if transacciones_conteo > 0 else 0.0
        costo_ventas = sum(float(r['costo_historico']) * int(r['cantidad']) for r in ventas_actual)
        utilidad_bruta = round(ventas_netas - costo_ventas, 2)
        margen_bruto_pct = round((utilidad_bruta / ventas_netas * 100), 2) if ventas_netas > 0 else 0.0

        dias_periodo = max((dt_fin - dt_inicio).days + 1, 1) if periodo != 'historico' else max(len(set(str(r['fecha_venta']) for r in ventas_actual)), 1)
        promedio_diario = round(ventas_netas / dias_periodo, 2)

        kpis = {
            "ventas_netas": round(ventas_netas, 2),
            "unidades_vendidas": unidades_vendidas,
            "transacciones": transacciones_conteo,
            "ticket_promedio": ticket_promedio,
            "costo_ventas": round(costo_ventas, 2),
            "utilidad_bruta": utilidad_bruta,
            "margen_bruto_pct": margen_bruto_pct,
            "promedio_diario": promedio_diario,
            "dias_periodo": dias_periodo,
            "periodo_nombre": nombre_periodo,
            "fecha_inicio": dt_inicio.strftime('%Y-%m-%d'),
            "fecha_fin": dt_fin.strftime('%Y-%m-%d')
        }

        # Comparación si se solicitó
        comparacion = {}
        if comparar and prev_inicio and prev_fin:
            ventas_prev = consultar_ventas_rango(prev_inicio, prev_fin)
            p_ventas_netas = sum(float(r['subtotal']) for r in ventas_prev)
            p_unidades = sum(int(r['cantidad']) for r in ventas_prev)
            p_transacciones = len(set(r['venta_id'] for r in ventas_prev))
            p_ticket = round(p_ventas_netas / p_transacciones, 2) if p_transacciones > 0 else 0.0
            p_costo = sum(float(r['costo_historico']) * int(r['cantidad']) for r in ventas_prev)
            p_utilidad = round(p_ventas_netas - p_costo, 2)
            p_margen = round((p_utilidad / p_ventas_netas * 100), 2) if p_ventas_netas > 0 else 0.0

            def calc_var(actual, previo):
                diff = round(actual - previo, 2)
                pct = round((diff / previo * 100), 1) if previo > 0 else (100.0 if actual > 0 else 0.0)
                return {"previo": previo, "diff_monto": diff, "diff_pct": pct}

            comparacion = {
                "periodo_previo_nombre": nombre_periodo_ant,
                "fecha_inicio_prev": prev_inicio.strftime('%Y-%m-%d'),
                "fecha_fin_prev": prev_fin.strftime('%Y-%m-%d'),
                "ventas_netas": calc_var(ventas_netas, p_ventas_netas),
                "unidades_vendidas": calc_var(unidades_vendidas, p_unidades),
                "transacciones": calc_var(transacciones_conteo, p_transacciones),
                "ticket_promedio": calc_var(ticket_promedio, p_ticket),
                "utilidad_bruta": calc_var(utilidad_bruta, p_utilidad),
                "margen_bruto_pct": calc_var(margen_bruto_pct, p_margen)
            }

        # -------------------------------------------------------------
        # 2. TENDENCIA CRONOLÓGICA (Series de tiempo y picos)
        # -------------------------------------------------------------
        series_tiempo = {}
        ventas_por_fecha_dict = {}
        for r in ventas_actual:
            f_str = str(r['fecha_venta'])[:10]
            subt = float(r['subtotal'])
            ventas_por_fecha_dict[f_str] = ventas_por_fecha_dict.get(f_str, 0.0) + subt

            try:
                dt_v = datetime.strptime(f_str, '%Y-%m-%d').date()
            except Exception:
                dt_v = dt_inicio

            if agrupacion_tiempo == 'mes':
                key = dt_v.strftime('%Y-%m')
            elif agrupacion_tiempo == 'semana':
                key = f"Sem {dt_v.isocalendar()[1]} ({dt_v.year})"
            else: # dia
                key = dt_v.strftime('%Y-%m-%d')

            if key not in series_tiempo:
                series_tiempo[key] = {"monto": 0.0, "unidades": 0, "transacciones_set": set()}
            series_tiempo[key]["monto"] += subt
            series_tiempo[key]["unidades"] += int(r['cantidad'])
            series_tiempo[key]["transacciones_set"].add(r['venta_id'])

        pico_maximo = {"intervalo": None, "monto": 0.0}
        pico_minimo = {"intervalo": None, "monto": 999999999.0}

        tendencia_labels = []
        tendencia_valores = []
        tendencia_unidades = []
        for k in sorted(series_tiempo.keys()):
            v = series_tiempo[k]
            monto_f = round(v["monto"], 2)
            tendencia_labels.append(k)
            tendencia_valores.append(monto_f)
            tendencia_unidades.append(v["unidades"])
            if monto_f > pico_maximo["monto"]:
                pico_maximo = {"intervalo": k, "monto": monto_f}
            if monto_f < pico_minimo["monto"]:
                pico_minimo = {"intervalo": k, "monto": monto_f}

        if pico_minimo["monto"] == 999999999.0:
            pico_minimo = {"intervalo": None, "monto": 0.0}

        # -------------------------------------------------------------
        # 3. DISTRIBUCIÓN Y RENTABILIDAD POR CATEGORÍA
        # -------------------------------------------------------------
        cat_map = {}
        for r in ventas_actual:
            c_nom = r['categoria_nombre']
            if c_nom not in cat_map:
                cat_map[c_nom] = {"categoria": c_nom, "unidades": 0, "ingresos": 0.0, "costos": 0.0}
            cant = int(r['cantidad'])
            subt = float(r['subtotal'])
            cost = float(r['costo_historico']) * cant
            cat_map[c_nom]["unidades"] += cant
            cat_map[c_nom]["ingresos"] += subt
            cat_map[c_nom]["costos"] += cost

        categorias_analisis = []
        for c_nom, data in cat_map.items():
            ing = round(data["ingresos"], 2)
            cos = round(data["costos"], 2)
            util = round(ing - cos, 2)
            part_pct = round((ing / ventas_netas * 100), 2) if ventas_netas > 0 else 0.0
            marg_pct = round((util / ing * 100), 2) if ing > 0 else 0.0
            categorias_analisis.append({
                "categoria": c_nom,
                "unidades_vendidas": data["unidades"],
                "ingresos_netos": ing,
                "costo_ventas": cos,
                "utilidad_bruta": util,
                "margen_bruto_pct": marg_pct,
                "participacion_pct": part_pct
            })
        categorias_analisis.sort(key=lambda x: x["utilidad_bruta"], reverse=True)

        # -------------------------------------------------------------
        # 4. MÉTODOS DE PAGO Y CANALES DE VENTA
        # -------------------------------------------------------------
        ventas_unicas_dict = {}
        for r in ventas_actual:
            v_id = r['venta_id']
            if v_id not in ventas_unicas_dict:
                ventas_unicas_dict[v_id] = {
                    "total": float(r['venta_total']),
                    "forma_pago": r['forma_pago'] or 'Efectivo',
                    "canal_venta": r['canal_venta'] or 'Tienda Física'
                }

        pagos_map = {}
        canales_map = {}
        for v_id, v_data in ventas_unicas_dict.items():
            fp = v_data["forma_pago"]
            cv = v_data["canal_venta"]
            tot = v_data["total"]

            if fp not in pagos_map:
                pagos_map[fp] = {"metodo": fp, "transacciones": 0, "monto": 0.0}
            pagos_map[fp]["transacciones"] += 1
            pagos_map[fp]["monto"] += tot

            if cv not in canales_map:
                canales_map[cv] = {"canal": cv, "transacciones": 0, "monto": 0.0}
            canales_map[cv]["transacciones"] += 1
            canales_map[cv]["monto"] += tot

        total_cobrado = sum(p["monto"] for p in pagos_map.values())
        metodos_pago = []
        for fp, p in pagos_map.items():
            m_f = round(p["monto"], 2)
            part = round((m_f / total_cobrado * 100), 1) if total_cobrado > 0 else 0.0
            metodos_pago.append({
                "metodo": fp,
                "transacciones": p["transacciones"],
                "monto": m_f,
                "participacion_pct": part
            })
        metodos_pago.sort(key=lambda x: x["monto"], reverse=True)

        canales_venta = []
        for cv, c in canales_map.items():
            m_f = round(c["monto"], 2)
            part = round((m_f / total_cobrado * 100), 1) if total_cobrado > 0 else 0.0
            canales_venta.append({
                "canal": cv,
                "transacciones": c["transacciones"],
                "monto": m_f,
                "participacion_pct": part
            })

        # -------------------------------------------------------------
        # 5. RANKING DE PRODUCTOS: MÁS Y MENOS VENDIDOS
        # -------------------------------------------------------------
        prods_sold_map = {}
        for r in ventas_actual:
            p_id = r['producto_id']
            if p_id not in prods_sold_map:
                prods_sold_map[p_id] = {
                    "id": p_id,
                    "codigo": r['codigo_sku'],
                    "nombre": r['producto_nombre'],
                    "categoria": r['categoria_nombre'],
                    "cantidad_vendida": 0,
                    "monto_total": 0.0,
                    "costo_total": 0.0,
                    "stock_actual": r['stock_actual'],
                    "costo_unitario": float(r['costo_actual'])
                }
            cant = int(r['cantidad'])
            subt = float(r['subtotal'])
            cos = float(r['costo_historico']) * cant
            prods_sold_map[p_id]["cantidad_vendida"] += cant
            prods_sold_map[p_id]["monto_total"] += subt
            prods_sold_map[p_id]["costo_total"] += cos

        prods_sold_list = list(prods_sold_map.values())
        for p in prods_sold_list:
            p["monto_total"] = round(p["monto_total"], 2)
            p["costo_total"] = round(p["costo_total"], 2)
            p["utilidad"] = round(p["monto_total"] - p["costo_total"], 2)

        mas_vendidos_cant = sorted(prods_sold_list, key=lambda x: x['cantidad_vendida'], reverse=True)[:top_n]
        mas_vendidos_monto = sorted(prods_sold_list, key=lambda x: x['monto_total'], reverse=True)[:top_n]
        menos_vendidos_cant = sorted(prods_sold_list, key=lambda x: x['cantidad_vendida'])[:top_n]

        # -------------------------------------------------------------
        # 6. CLASIFICACIÓN ABC (PARETO 80-15-5) Y ROTACIÓN DE INVENTARIO
        # -------------------------------------------------------------
        cursor.execute("SELECT COUNT(id) as total_tipos, SUM(stock_actual) as stock_fisico, SUM(stock_actual * costo) as valor_costo FROM productos WHERE activo = 1")
        inv_stat = cursor.fetchone()
        stock_fisico_total = inv_stat[1] if inv_stat and inv_stat[1] else 0
        valor_inventario_costo = float(inv_stat[2]) if inv_stat and inv_stat[2] else 0.0

        rotacion_inventario = round(unidades_vendidas / (stock_fisico_total if stock_fisico_total > 0 else 1), 2)

        abc_items = sorted(prods_sold_list, key=lambda x: x['monto_total'], reverse=True)
        valor_consumo_total = sum(p['monto_total'] for p in abc_items)

        acumulado = 0.0
        for p in abc_items:
            acumulado += p['monto_total']
            pct_acum = round((acumulado / valor_consumo_total * 100), 2) if valor_consumo_total > 0 else 0.0
            p['pct_acumulado'] = pct_acum
            if pct_acum <= 80.0:
                p['clase_abc'] = 'A'
            elif pct_acum <= 95.0:
                p['clase_abc'] = 'B'
            else:
                p['clase_abc'] = 'C'

        conteo_a = sum(1 for p in abc_items if p['clase_abc'] == 'A')
        conteo_b = sum(1 for p in abc_items if p['clase_abc'] == 'B')
        conteo_c = sum(1 for p in abc_items if p['clase_abc'] == 'C')

        # -------------------------------------------------------------
        # 7. REPUESTOS SIN VENTAS (MERCANCÍA ESTANCADA / "HUESO")
        # -------------------------------------------------------------
        prods_sold_ids = tuple(prods_sold_map.keys()) if prods_sold_map else (0,)
        cursor.execute(f"""
            SELECT p.id, p.codigo_sku as codigo, p.nombre, c.nombre as categoria,
                   p.stock_actual as stock, p.costo, (p.stock_actual * p.costo) as valor_estancado,
                   (SELECT MAX(v2.fecha_venta) FROM detalle_ventas dv2 INNER JOIN ventas v2 ON dv2.venta_id = v2.id WHERE dv2.producto_id = p.id AND v2.estado = 'Completada') as ultima_venta
            FROM productos p
            INNER JOIN categorias c ON p.categoria_id = c.id
            WHERE p.activo = 1 AND p.stock_actual > 0 AND p.id NOT IN ({','.join(['?']*len(prods_sold_ids))})
            ORDER BY valor_estancado DESC
        """, prods_sold_ids)
        sin_ventas_rows = cursor.fetchall()
        repuestos_sin_ventas = []
        capital_estancado_total = 0.0
        for r in sin_ventas_rows:
            v_est = float(r[6]) if r[6] else 0.0
            capital_estancado_total += v_est
            u_v = r[7].strftime('%Y-%m-%d') if r[7] and hasattr(r[7], 'strftime') else (str(r[7])[:10] if r[7] else 'Nunca vendido')
            repuestos_sin_ventas.append({
                "id": r[0],
                "codigo": r[1],
                "nombre": r[2],
                "categoria": r[3],
                "stock": r[4],
                "costo": float(r[5]),
                "valor_estancado": round(v_est, 2),
                "ultima_venta": u_v
            })

        # -------------------------------------------------------------
        # 8. MONITOREO DE ALERTA DE EXISTENCIAS CRÍTICAS
        # -------------------------------------------------------------
        cursor.execute("""
            SELECT p.id, p.codigo_sku as codigo, p.nombre, c.nombre as categoria,
                   p.stock_actual as stock, p.stock_minimo as min_stock, p.costo, p.precio_venta
            FROM productos p
            INNER JOIN categorias c ON p.categoria_id = c.id
            WHERE p.activo = 1 AND p.stock_actual <= p.stock_minimo
            ORDER BY (p.stock_minimo - p.stock_actual) DESC
        """)
        criticos_rows = cursor.fetchall()
        alertas_criticas = []
        for r in criticos_rows:
            p_id = r[0]
            stk = r[4]
            min_s = r[5]
            cant_periodo = prods_sold_map.get(p_id, {}).get('cantidad_vendida', 0)
            prom_dia = round(cant_periodo / dias_periodo, 2)
            dias_cob = round(stk / prom_dia, 1) if prom_dia > 0 else None
            sug_reponer = max((min_s * 2) - stk, min_s)
            alertas_criticas.append({
                "id": p_id,
                "codigo": r[1],
                "nombre": r[2],
                "categoria": r[3],
                "stock": stk,
                "min_stock": min_s,
                "promedio_diario_ventas": prom_dia,
                "dias_cobertura": dias_cob,
                "sugerencia_reponer": sug_reponer
            })

        # -------------------------------------------------------------
        # 9. ANÁLISIS DE DEVOLUCIONES DE VENTAS
        # -------------------------------------------------------------
        cursor.execute("""
            SELECT m.id, m.fecha, m.cantidad, m.motivo, m.tipo_movimiento,
                   p.codigo_sku, p.nombre as producto_nombre, p.precio_venta,
                   c.nombre as categoria_nombre
            FROM movimientos_inventario m
            INNER JOIN productos p ON m.producto_id = p.id
            INNER JOIN categorias c ON p.categoria_id = c.id
            WHERE (m.tipo_movimiento IN ('DEVOLUCION_CLIENTE', 'DEFECTUOSO_GARANTIA')
                   OR m.motivo LIKE '%devoluc%'
                   OR m.motivo LIKE '%defectu%'
                   OR m.motivo LIKE '%garant%')
              AND CAST(m.fecha AS DATE) >= ? AND CAST(m.fecha AS DATE) <= ?
            ORDER BY m.fecha DESC
        """, (dt_inicio.strftime('%Y-%m-%d'), dt_fin.strftime('%Y-%m-%d')))
        dev_rows = cursor.fetchall()
        devoluciones_lista = []
        dev_cant_total = 0
        dev_monto_total = 0.0
        motivos_map = {}
        cats_dev_map = {}

        for r in dev_rows:
            cant = int(r[2])
            pu = float(r[7])
            monto = cant * pu
            dev_cant_total += cant
            dev_monto_total += monto

            motivo_txt = r[3] or ''
            if 'defectu' in motivo_txt.lower() or 'dañ' in motivo_txt.lower():
                tipo_m = 'Producto Defectuoso / Dañado'
            elif 'devoluc' in motivo_txt.lower() or 'cambio' in motivo_txt.lower():
                tipo_m = 'Devolución de Cliente'
            else:
                tipo_m = 'Ajuste / Otro Motivo'
            motivos_map[tipo_m] = motivos_map.get(tipo_m, 0) + cant

            cat_n = r[8]
            cats_dev_map[cat_n] = cats_dev_map.get(cat_n, 0) + cant

            devoluciones_lista.append({
                "id": r[0],
                "fecha": r[1].strftime('%Y-%m-%d %H:%M') if hasattr(r[1], 'strftime') else str(r[1]),
                "codigo": r[5],
                "producto": r[6],
                "categoria": cat_n,
                "cantidad": cant,
                "motivo": motivo_txt,
                "monto_estimado": round(monto, 2)
            })

        devoluciones_resumen = {
            "total_operaciones": len(dev_rows),
            "unidades_devueltas": dev_cant_total,
            "monto_estimado": round(dev_monto_total, 2),
            "motivos": [{"motivo": k, "cantidad": v} for k, v in motivos_map.items()],
            "categorias_afectadas": [{"categoria": k, "cantidad": v} for k, v in sorted(cats_dev_map.items(), key=lambda x: x[1], reverse=True)],
            "lista_recientes": devoluciones_lista[:10]
        }

        # -------------------------------------------------------------
        # 10. COMPRAS Y EGRESOS EN EL PERÍODO
        # -------------------------------------------------------------
        cursor.execute("""
            SELECT COUNT(id) as cant, SUM(total) as monto
            FROM compras
            WHERE estado = 'Completada'
              AND CAST(fecha_compra AS DATE) >= ? AND CAST(fecha_compra AS DATE) <= ?
        """, (dt_inicio.strftime('%Y-%m-%d'), dt_fin.strftime('%Y-%m-%d')))
        c_row = cursor.fetchone()
        compras_monto = float(c_row[1]) if c_row and c_row[1] else 0.0
        compras_conteo = c_row[0] if c_row and c_row[0] else 0

        # Respuesta estructurada integral y retrocompatible
        response_data = {
            "kpis": kpis,
            "comparacion": comparacion,
            "tendencia": {
                "labels": tendencia_labels,
                "valores": tendencia_valores,
                "unidades": tendencia_unidades,
                "pico_maximo": pico_maximo,
                "pico_minimo": pico_minimo
            },
            "categorias": categorias_analisis,
            "metodos_pago": metodos_pago,
            "canales_venta": canales_venta,
            "ranking": {
                "mas_vendidos_cantidad": mas_vendidos_cant,
                "mas_vendidos_monto": mas_vendidos_monto,
                "menos_vendidos_cantidad": menos_vendidos_cant
            },
            "inventario_abc": {
                "rotacion_inventario": rotacion_inventario,
                "stock_fisico_total": stock_fisico_total,
                "valor_inventario_costo": valor_inventario_costo,
                "capital_estancado_total": round(capital_estancado_total, 2),
                "conteo_clase_a": conteo_a,
                "conteo_clase_b": conteo_b,
                "conteo_clase_c": conteo_c,
                "items_abc": abc_items[:30],
                "repuestos_sin_ventas": repuestos_sin_ventas[:25]
            },
            "alertas_criticas": alertas_criticas,
            "devoluciones": devoluciones_resumen,
            "compras": {
                "total_monto": round(compras_monto, 2),
                "total_conteo": compras_conteo
            },
            # Campos retrocompatibles con versión anterior
            "ventas_totales_monto": round(ventas_netas, 2),
            "ventas_totales_conteo": transacciones_conteo,
            "compras_totales_monto": round(compras_monto, 2),
            "compras_totales_conteo": compras_conteo,
            "valor_inventario_costo": valor_inventario_costo,
            "margen_bruto_estimado": utilidad_bruta,
            "rotacion_inventario": rotacion_inventario,
            "unidades_vendidas_total": unidades_vendidas,
            "top_productos": mas_vendidos_cant,
            "productos_bajo_stock": alertas_criticas,
            "ventas_por_fecha": ventas_por_fecha_dict,
            "alerta_stock_bajo_conteo": len(alertas_criticas),
            "generado_en": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            "generado_por": session['user']['nombre']
        }

        return jsonify(response_data)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500
    finally:
        if 'conn' in locals() and conn:
            conn.close()

# ==============================================================================
# EJECUCIÓN DEL SERVIDOR
# ==============================================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)