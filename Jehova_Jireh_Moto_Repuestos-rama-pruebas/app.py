import os
import pyodbc
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from calculos_rrhh import calcular_nomina_empleado

app = Flask(__name__, template_folder='Fronted/templates', static_folder='Fronted/static')
app.secret_key = os.environ.get('SECRET_KEY', 'jehova_jireh_secret_key_2026_super_secure')

# ==============================================================================
# CONFIGURACIÓN DE BASE DE DATOS SQL SERVER
# ==============================================================================
# Cambia 'LAPTOP-CNR3S3I3' por tu nombre de servidor SQL Server.
DB_SERVER = os.environ.get('DB_SERVER', r'LAPTOP-CNR3S3I3')
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
        cliente_id = int(data.get('cliente_id', 1)) 
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

            conn.commit()
            return jsonify({"success": True, "mensaje": f"Venta {codigo_v} procesada."}), 201

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
# RECURSOS HUMANOS Y NÓMINA
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
            return jsonify({"error": "Nombre y Salario base válidos son obligatorios."}), 400

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
            return jsonify({"error": "Todos los campos son obligatorios y los días deben ser mayores a 0."}), 400

        tipos_validos = ['VACACIONES', 'PERMISO_CON_GOCE', 'PERMISO_SIN_GOCE', 'FALTA']
        if tipo not in tipos_validos:
            return jsonify({"error": f"Tipo inválido. Use: {tipos_validos}"}), 400

        try:
            execute_query(
                """INSERT INTO movimientos_laborales
                   (empleado_id, tipo, fecha_inicio, fecha_fin, dias_tomados, observacion)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (empleado_id, tipo, fecha_inicio, fecha_fin, dias_tomados, observacion),
                commit=True
            )
            # Si es vacaciones, descontar días disponibles del empleado
            if tipo == 'VACACIONES':
                execute_query(
                    "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles - ? WHERE id = ?",
                    (dias_tomados, empleado_id), commit=True
                )
            return jsonify({"success": True, "mensaje": "Movimiento registrado exitosamente."}), 201
        except Exception as e:
            return jsonify({"error": str(e)}), 500


# --- GENERACIÓN DE NÓMINA ---
@app.route('/api/nomina/generar', methods=['POST'])
@login_required
def api_nomina_generar():
    """Genera la nómina mensual para todos los empleados activos con cálculos correctos Ley 822 + Ley 185."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos para generar nóminas."}), 403

    data = request.json or {}
    mes  = int(data.get('mes', 1))
    anio = int(data.get('anio', 2026))

    try:
        conn   = get_db_connection()
        cursor = conn.cursor()

        # Validar duplicado
        cursor.execute("SELECT id FROM nomina WHERE periodo_mes = ? AND periodo_anio = ?", (mes, anio))
        if cursor.fetchone():
            conn.close()
            return jsonify({"error": f"La nómina {mes}/{anio} ya fue generada anteriormente."}), 400

        # Crear cabecera
        cursor.execute("INSERT INTO nomina (periodo_mes, periodo_anio) VALUES (?, ?)", (mes, anio))
        cursor.execute("SELECT @@IDENTITY AS id")
        nomina_id = int(cursor.fetchone()[0])

        empleado_id_param = data.get('empleado_id', 'all')
        if empleado_id_param != 'all':
            cursor.execute("SELECT id, salario_base FROM empleados WHERE activo=1 AND id=?", (empleado_id_param,))
        else:
            cursor.execute("SELECT id, salario_base FROM empleados WHERE activo=1")

        empleados = cursor.fetchall()

        t_bruto       = 0.0
        t_deducciones = 0.0
        t_neto        = 0.0
        t_patronal    = 0.0
        t_vac         = 0.0
        t_agui        = 0.0

        for emp in empleados:
            e_id   = emp[0]
            salario = float(emp[1])

            # Usar módulo de cálculos con lógica correcta
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

            # Acumular días de vacaciones ganados este mes (1.25 días = 15 días / 12 meses)
            cursor.execute(
                "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles + 1.25 WHERE id = ?",
                (e_id,)
            )

            t_bruto       += calc['salario_bruto']
            t_deducciones += calc['total_deducciones']
            t_neto        += calc['salario_neto']
            t_patronal    += calc['inss_patronal']
            t_vac         += calc['provision_vacaciones']
            t_agui        += calc['provision_aguinaldo']

        # Actualizar totales en cabecera
        cursor.execute(
            """UPDATE nomina
               SET total_ingresos=?, total_deducciones=?, total_neto=?,
                   inss_patronal_total=?, provision_vac_total=?, provision_agui_total=?
               WHERE id=?""",
            (round(t_bruto, 2), round(t_deducciones, 2), round(t_neto, 2),
             round(t_patronal, 2), round(t_vac, 2), round(t_agui, 2), nomina_id)
        )

        # Nota: El asiento contable se omite si la tabla no existe aún.
        # Para habilitarlo, crear la tabla asientos_contables primero.

        conn.commit()
        conn.close()
        return jsonify({
            "success"   : True,
            "mensaje"   : f"Nómina {mes:02d}/{anio} generada con éxito para {len(empleados)} empleados.",
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
    """Lista el historial de todas las nóminas generadas."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403
    query = """
        SELECT id, periodo_mes, periodo_anio, fecha_generacion,
               total_ingresos, total_deducciones, total_neto,
               ISNULL(inss_patronal_total, 0) AS inss_patronal_total,
               ISNULL(provision_vac_total, 0) AS provision_vac_total,
               ISNULL(provision_agui_total, 0) AS provision_agui_total,
               ISNULL(estado, 'CERRADA') AS estado
        FROM nomina
        ORDER BY anio DESC, mes DESC
    """
    # Alias de columnas compatibles con tabla original
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
    """Obtiene el detalle completo de una nómina: cabecera + líneas por empleado."""
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
        return jsonify({"error": "Nómina no encontrada."}), 404

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
        return jsonify({"error": "Detalle de empleado no encontrado en esta nómina."}), 404
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
    """Elimina una nómina completa y revierte las vacaciones acumuladas."""
    if session['user']['rol'] not in ROLES_RRHH:
        return jsonify({"error": "No tienes permisos."}), 403
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar que existe
        cursor.execute("SELECT id FROM nomina WHERE id=?", (nomina_id,))
        if not cursor.fetchone():
            conn.close()
            return jsonify({"error": "Nómina no encontrada."}), 404
            
        # Revertir vacaciones (restar los 1.25 que se sumaron a cada empleado en esta nómina)
        cursor.execute("SELECT empleado_id FROM detalle_nomina WHERE nomina_id=?", (nomina_id,))
        empleados_en_nomina = cursor.fetchall()
        for emp in empleados_en_nomina:
            cursor.execute(
                "UPDATE empleados SET dias_vacaciones_disponibles = dias_vacaciones_disponibles - 1.25 WHERE id = ?",
                (emp[0],)
            )
            
        # Eliminar la nómina (ON DELETE CASCADE debe borrar detalle_nomina)
        cursor.execute("DELETE FROM nomina WHERE id=?", (nomina_id,))
        conn.commit()
        conn.close()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# CONTABILIDAD Y ESTADOS FINANCIEROS
# ==============================================================================
@app.route('/api/contabilidad/balance', methods=['GET'])
@login_required
def api_contabilidad_balance():
    # Estructura simplificada del balance general
    return jsonify({
        "activo": {"Caja y Bancos": 150000.0, "Inventario": 350000.0, "Total Activo": 500000.0},
        "pasivo": {"Cuentas por Pagar": 50000.0, "Impuestos por Pagar": 15000.0, "Total Pasivo": 65000.0},
        "capital": {"Capital Social": 300000.0, "Utilidades Retenidas": 135000.0, "Total Capital": 435000.0}
    })

@app.route('/api/contabilidad/resultados', methods=['GET'])
@login_required
def api_contabilidad_resultados():
    # Generar de las ventas
    try:
        ventas_info = execute_query("SELECT SUM(total) as ingresos FROM ventas WHERE estado='Completada'", fetchone=True)
        compras_info = execute_query("SELECT SUM(total) as costos FROM compras WHERE estado='Completada'", fetchone=True)
        
        ingresos = float(ventas_info['ingresos'] or 0) if ventas_info else 0.0
        costo_ventas = float(compras_info['costos'] or 0) if compras_info else 0.0
        utilidad_bruta = ingresos - costo_ventas
        gastos = 15000.0 # Gastos operativos simulados (alquiler, nomina base)
        utilidad_neta = utilidad_bruta - gastos
        
        return jsonify({
            "ingresos": ingresos,
            "costo_ventas": costo_ventas,
            "utilidad_bruta": utilidad_bruta,
            "gastos_operativos": gastos,
            "utilidad_neta": utilidad_neta
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ==============================================================================
# RECURSOS HUMANOS - COLILLA
# ==============================================================================
@app.route('/rrhh/colilla/<int:id_detalle>')
@login_required
@role_required('Administrador', 'Responsable de Recursos Humanos')
def ver_colilla(id_detalle):
    query = """
        SELECT 
            e.nombres as empleado,
            e.cedula,
            e.cargo,
            e.departamento,
            e.num_inss as inss,
            e.salario_base as salario_contrato,
            CONVERT(varchar, e.fecha_contratacion, 106) as fecha_ingreso,
            
            n.fecha_inicio as periodo_inicio,
            n.fecha_fin as periodo_fin,
            
            d.dias_trabajados,
            d.vac_acumulada as vac_acumulado,
            d.vac_mes,
            d.vac_descansados,
            d.vac_saldo_final as vac_saldo,
            
            d.salario_base as salario_devengado,
            d.kpi_comision as kpi_meta,
            (d.salario_base + d.kpi_comision + d.ingresos_extra) as total_percepciones,
            d.inss_laboral,
            d.ir_retencion as ir,
            d.adelanto_salarial as adelanto,
            (d.inss_laboral + d.ir_retencion + d.adelanto_salarial) as total_deducciones,
            d.salario_neto as neto_a_recibir
        FROM detalle_nomina d
        INNER JOIN nomina n ON d.nomina_id = n.id
        INNER JOIN empleados e ON d.empleado_id = e.id
        WHERE d.id = ?
    """
    datos = execute_query(query, (id_detalle,), fetchone=True)
    
    if not datos:
        return "Colilla no encontrada", 404
        
    c = {
        "empresa": "Jehová Jireh Moto Repuestos",
        "periodo": f"{datos['periodo_inicio']} al {datos['periodo_fin']}",
        "empleado": datos['empleado'],
        "cedula": datos['cedula'],
        "cargo": datos['cargo'] or 'Vendedor',
        "departamento": datos['departamento'] or 'Ventas',
        "inss": datos['inss'] or 'N/A',
        "salario_contrato": float(datos['salario_contrato'] or 0),
        "fecha_ingreso": datos['fecha_ingreso'],
        "dias_trabajados": float(datos['dias_trabajados'] or 15),
        
        "vac_acumulado": float(datos['vac_acumulado'] or 0),
        "vac_mes": float(datos['vac_mes'] or 0),
        "vac_descansados": float(datos['vac_descansados'] or 0),
        "vac_saldo": float(datos['vac_saldo'] or 0),
        
        "salario_devengado": float(datos['salario_devengado'] or 0),
        "kpi_meta": float(datos['kpi_meta'] or 0),
        "total_percepciones": float(datos['total_percepciones'] or 0),
        "inss_laboral": float(datos['inss_laboral'] or 0),
        "ir": float(datos['ir'] or 0),
        "adelanto": float(datos['adelanto'] or 0),
        "total_deducciones": float(datos['total_deducciones'] or 0),
        "neto_a_recibir": float(datos['neto_a_recibir'] or 0)
    }
    
    return render_template('colilla.html', c=c)

# ==============================================================================
# EJECUCIÓN DEL SERVIDOR
# ==============================================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)