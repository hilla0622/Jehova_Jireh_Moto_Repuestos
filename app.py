import os
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session

app = Flask(__name__, template_folder='Fronted/templates', static_folder='Fronted/static')
app.secret_key = os.environ.get('SECRET_KEY', 'jehova_jireh_secret_key_2026_super_secure')

# ==============================================================================
# ALMACENAMIENTO DE DATOS EN MEMORIA (Base de Datos Simulada para Prototipo)
# ==============================================================================

# Jerarquía de usuarios y cuentas de prueba
# Roles: 'Administrador', 'Vendedor', 'Encargado de Inventario', 'Contador'
USUARIOS = [
    {
        "id": 1,
        "username": "admin",
        "password": "123",
        "nombre": "Gilda Pérez",
        "rol": "Administrador"
    },
    {
        "id": 2,
        "username": "vendedor",
        "password": "123",
        "nombre": "Ana Gómez",
        "rol": "Vendedor"
    },
    {
        "id": 3,
        "username": "inventario",
        "password": "123",
        "nombre": "Roberto Silva",
        "rol": "Encargado de Inventario"
    },
    {
        "id": 4,
        "username": "contador",
        "password": "123",
        "nombre": "Lic. Fernando Rivas (Granada)",
        "rol": "Contador"
    }
]

# Catálogo Inicial de Productos / Repuestos de Moto
PRODUCTOS = [
    {
        "id": 1,
        "codigo": "REP-001",
        "nombre": "Pastillas de Freno Delanteras Yamaha YBR 125",
        "categoria": "Frenos",
        "precio": 15.50,
        "costo": 9.00,
        "stock": 18,
        "min_stock": 5
    },
    {
        "id": 2,
        "codigo": "REP-002",
        "nombre": "Kit de Arrastre Cadena y Piñón Pulsar 200 NS",
        "categoria": "Transmisión",
        "precio": 45.00,
        "costo": 30.00,
        "stock": 3,  # Alerta stock bajo
        "min_stock": 5
    },
    {
        "id": 3,
        "codigo": "REP-003",
        "nombre": "Aceite 4T 20W50 Mineral Motul 1L",
        "categoria": "Lubricantes",
        "precio": 12.00,
        "costo": 7.50,
        "stock": 40,
        "min_stock": 10
    },
    {
        "id": 4,
        "codigo": "REP-004",
        "nombre": "Bujía NGK C7HSA para pasola/motos 125cc",
        "categoria": "Motor / Encendido",
        "precio": 4.50,
        "costo": 2.20,
        "stock": 25,
        "min_stock": 8
    },
    {
        "id": 5,
        "codigo": "REP-005",
        "nombre": "Batería de Gel 12V 7Ah Moto Scooter",
        "categoria": "Eléctrico",
        "precio": 35.00,
        "costo": 22.00,
        "stock": 2, # Stock bajo
        "min_stock": 4
    }
]

# Catalogo de Proveedores
PROVEEDORES = [
    {
        "id": 1,
        "nombre": "Distribuidora Repuestos del Pacífico",
        "contacto": "Mario López",
        "telefono": "+505 8899-1122",
        "email": "ventas@pacificomotos.com"
    },
    {
        "id": 2,
        "nombre": "Importadora Global Moto Parts",
        "contacto": "Elena Morales",
        "telefono": "+505 7766-3344",
        "email": "contacto@globalmotoparts.com"
    }
]

# Registro de Compras (Aumenta stock)
COMPRAS = [
    {
        "id": 1,
        "proveedor_id": 1,
        "proveedor_nombre": "Distribuidora Repuestos del Pacífico",
        "fecha": "2026-08-05",
        "total": 180.00,
        "detalles": [
            {"producto_id": 1, "producto_nombre": "Pastillas de Freno Delanteras", "cantidad": 20, "precio_unitario": 9.00}
        ]
    }
]

# Registro de Ventas (Disminuye stock)
VENTAS = [
    {
        "id": 1,
        "codigo_venta": "VEN-0001",
        "cliente": "Cliente General",
        "fecha": "2026-08-09",
        "vendedor": "Ana Gómez",
        "total": 27.50,
        "forma_pago": "Efectivo",
        "detalles": [
            {"producto_id": 1, "producto_nombre": "Pastillas de Freno Delanteras Yamaha YBR 125", "cantidad": 1, "precio_unitario": 15.50, "subtotal": 15.50},
            {"producto_id": 3, "producto_nombre": "Aceite 4T 20W50 Mineral Motul 1L", "cantidad": 1, "precio_unitario": 12.00, "subtotal": 12.00}
        ]
    }
]

# Historial de Movimientos de Inventario (Entradas / Salidas / Ajustes)
MOVIMIENTOS = [
    {"id": 1, "fecha": "2026-08-01", "producto_id": 1, "producto_codigo": "REP-001", "producto_nombre": "Pastillas de Freno Delanteras Yamaha YBR 125", "tipo": "ENTRADA_INICIAL", "cantidad": 20, "motivo": "Carga inicial de inventario", "usuario": "Gilda Pérez"},
    {"id": 2, "fecha": "2026-08-05", "producto_id": 1, "producto_codigo": "REP-001", "producto_nombre": "Pastillas de Freno Delanteras Yamaha YBR 125", "tipo": "ENTRADA_COMPRA", "cantidad": 20, "motivo": "Compra COM-#1 - Distribuidora Repuestos del Pacífico", "usuario": "Roberto Silva"},
    {"id": 3, "fecha": "2026-08-09", "producto_id": 1, "producto_codigo": "REP-001", "producto_nombre": "Pastillas de Freno Delanteras Yamaha YBR 125", "tipo": "SALIDA_VENTA", "cantidad": 1, "motivo": "Venta VEN-0001", "usuario": "Ana Gómez"},
    {"id": 4, "fecha": "2026-08-09", "producto_id": 3, "producto_codigo": "REP-003", "producto_nombre": "Aceite 4T 20W50 Mineral Motul 1L", "tipo": "SALIDA_VENTA", "cantidad": 1, "motivo": "Venta VEN-0001", "usuario": "Ana Gómez"}
]

# Contador de IDs automáticos
NEXT_USER_ID = 5
NEXT_PRODUCT_ID = 6
NEXT_PURCHASE_ID = 2
NEXT_SALE_ID = 2
NEXT_PROV_ID = 3
NEXT_MOV_ID = 5


def registrar_movimiento(prod, tipo, cantidad, motivo, usuario):
    global NEXT_MOV_ID
    import datetime
    fecha_actual = datetime.date.today().strftime('%Y-%m-%d')
    mov = {
        "id": NEXT_MOV_ID,
        "fecha": fecha_actual,
        "producto_id": prod['id'],
        "producto_codigo": prod['codigo'],
        "producto_nombre": prod['nombre'],
        "tipo": tipo,
        "cantidad": cantidad,
        "motivo": motivo,
        "usuario": usuario
    }
    MOVIMIENTOS.append(mov)
    NEXT_MOV_ID += 1
    return mov


# ==============================================================================
# DECORADORES Y DELEGACIÓN DE SEGURIDAD Y SESIONES
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

        usuario_encontrado = next((u for u in USUARIOS if u['username'].lower() == username.lower() and u['password'] == password), None)
        
        if usuario_encontrado:
            session['user'] = {
                'id': usuario_encontrado['id'],
                'username': usuario_encontrado['username'],
                'nombre': usuario_encontrado['nombre'],
                'rol': usuario_encontrado['rol']
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
# ENDPOINTS API (JSON)
# ==============================================================================

# --- USUARIOS ---
@app.route('/api/usuarios', methods=['GET', 'POST'])
@login_required
def api_usuarios():
    global NEXT_USER_ID
    if request.method == 'GET':
        # Retornar lista sin exponer passwords
        usuarios_safe = [{k: v for k, v in u.items() if k != 'password'} for u in USUARIOS]
        return jsonify(usuarios_safe)

    if request.method == 'POST':
        # Solo administrador puede crear usuarios
        if session['user']['rol'] != 'Administrador':
            return jsonify({"error": "Solo el Administrador puede registrar nuevos usuarios."}), 403
        
        data = request.json or {}
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        nombre = data.get('nombre', '').strip()
        rol = data.get('rol', '').strip()

        if not username or not password or not nombre or not rol:
            return jsonify({"error": "Todos los campos son obligatorios."}), 400

        if any(u['username'].lower() == username.lower() for u in USUARIOS):
            return jsonify({"error": "El nombre de usuario ya existe."}), 400

        nuevo_usuario = {
            "id": NEXT_USER_ID,
            "username": username,
            "password": password,
            "nombre": nombre,
            "rol": rol
        }
        USUARIOS.append(nuevo_usuario)
        NEXT_USER_ID += 1

        return jsonify({"success": True, "mensaje": "Usuario registrado exitosamente.", "usuario": {k: v for k, v in nuevo_usuario.items() if k != 'password'}}), 201


# --- PRODUCTOS / INVENTARIO ---
@app.route('/api/productos', methods=['GET', 'POST'])
@login_required
def api_productos():
    global NEXT_PRODUCT_ID
    if request.method == 'GET':
        return jsonify(PRODUCTOS)

    if request.method == 'POST':
        # Permiso: Administrador y Encargado de Inventario
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
            return jsonify({"error": "No tienes permiso para registrar productos."}), 403
        
        data = request.json or {}
        codigo = data.get('codigo', f"REP-00{NEXT_PRODUCT_ID}").strip()
        nombre = data.get('nombre', '').strip()
        categoria = data.get('categoria', 'General').strip()
        precio = float(data.get('precio', 0))
        costo = float(data.get('costo', 0))
        stock = int(data.get('stock', 0))
        min_stock = int(data.get('min_stock', 5))

        if not nombre or precio <= 0:
            return jsonify({"error": "Nombre y Precio válidos son obligatorios."}), 400

        nuevo_prod = {
            "id": NEXT_PRODUCT_ID,
            "codigo": codigo,
            "nombre": nombre,
            "categoria": categoria,
            "precio": precio,
            "costo": costo,
            "stock": stock,
            "min_stock": min_stock
        }
        PRODUCTOS.append(nuevo_prod)
        
        if stock > 0:
            registrar_movimiento(nuevo_prod, "ENTRADA_INICIAL", stock, "Registro de producto nuevo", session['user']['nombre'])

        NEXT_PRODUCT_ID += 1
        return jsonify({"success": True, "producto": nuevo_prod}), 201

@app.route('/api/productos/<int:prod_id>', methods=['PUT'])
@login_required
def api_producto_editar(prod_id):
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
        return jsonify({"error": "No tienes permiso para modificar productos."}), 403
    
    prod = next((p for p in PRODUCTOS if p['id'] == prod_id), None)
    if not prod:
        return jsonify({"error": "Producto no encontrado."}), 404
        
    data = request.json or {}
    prod['codigo'] = data.get('codigo', prod['codigo']).strip()
    prod['nombre'] = data.get('nombre', prod['nombre']).strip()
    prod['categoria'] = data.get('categoria', prod['categoria']).strip()
    prod['precio'] = float(data.get('precio', prod['precio']))
    prod['costo'] = float(data.get('costo', prod['costo']))
    prod['min_stock'] = int(data.get('min_stock', prod['min_stock']))
    
    # Manejar si se ajusta stock directamente en edición
    if 'stock' in data:
        nuevo_stock = int(data['stock'])
        if nuevo_stock != prod['stock']:
            diff = nuevo_stock - prod['stock']
            prod['stock'] = nuevo_stock
            tipo_mov = "AJUSTE_ENTRADA" if diff > 0 else "AJUSTE_SALIDA"
            registrar_movimiento(prod, tipo_mov, abs(diff), "Ajuste por edición de producto", session['user']['nombre'])

    return jsonify({"success": True, "mensaje": "Producto actualizado exitosamente.", "producto": prod})


# --- MOVIMIENTOS DE INVENTARIO (KARDEX) ---
@app.route('/api/movimientos', methods=['GET', 'POST'])
@login_required
def api_movimientos():
    if request.method == 'GET':
        return jsonify(MOVIMIENTOS)

    if request.method == 'POST':
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
            return jsonify({"error": "No tienes permiso para registrar movimientos de inventario."}), 403

        data = request.json or {}
        p_id = int(data.get('producto_id', 0))
        tipo_accion = data.get('tipo', 'ENTRADA').upper() # ENTRADA o SALIDA
        cantidad = int(data.get('cantidad', 0))
        motivo = data.get('motivo', 'Ajuste manual de inventario').strip()

        if cantidad <= 0:
            return jsonify({"error": "La cantidad debe ser mayor a 0."}), 400

        prod = next((p for p in PRODUCTOS if p['id'] == p_id), None)
        if not prod:
            return jsonify({"error": "Producto no encontrado."}), 404

        if tipo_accion == 'SALIDA':
            if prod['stock'] < cantidad:
                return jsonify({"error": f"Stock insuficiente para '{prod['nombre']}'. Disponible: {prod['stock']}"}), 400
            prod['stock'] -= cantidad
            tipo_mov = "AJUSTE_SALIDA"
        else:
            prod['stock'] += cantidad
            tipo_mov = "AJUSTE_ENTRADA"

        mov = registrar_movimiento(prod, tipo_mov, cantidad, motivo, session['user']['nombre'])
        return jsonify({"success": True, "mensaje": f"Movimiento de {tipo_accion} registrado.", "movimiento": mov, "stock_actual": prod['stock']}), 201

@app.route('/api/movimientos/<int:mov_id>', methods=['PUT'])
@login_required
def api_movimiento_editar(mov_id):
    if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
        return jsonify({"error": "No tienes permiso para modificar movimientos de inventario."}), 403

    mov = next((m for m in MOVIMIENTOS if m['id'] == mov_id), None)
    if not mov:
        return jsonify({"error": "Movimiento no encontrado."}), 404

    data = request.json or {}
    nueva_cantidad = int(data.get('cantidad', mov['cantidad']))
    nuevo_motivo = data.get('motivo', mov['motivo']).strip()
    nuevo_tipo = data.get('tipo', mov['tipo']).strip()
    motivo_tipo = data.get('motivo_tipo', 'AJUSTE_STOCK').upper()
    actualizar_stock = data.get('actualizar_stock', True)

    if nueva_cantidad <= 0:
        return jsonify({"error": "La cantidad debe ser un número entero mayor a 0."}), 400

    prod = next((p for p in PRODUCTOS if p['id'] == mov['producto_id']), None)
    if not prod:
        return jsonify({"error": "Producto asociado al movimiento no encontrado."}), 404

    # Regla de Negocio: Si el motivo es DEFECTUOSO, NO SE ACTUALIZA EL STOCK del catálogo
    es_defectuoso = (motivo_tipo == 'DEFECTUOSO') or ('DEFECTUOS' in nuevo_motivo.upper()) or (not actualizar_stock)

    if es_defectuoso:
        motivo_final = nuevo_motivo if nuevo_motivo.startswith('[DEFECTUOSO]') else f"[DEFECTUOSO] {nuevo_motivo}"
        mov['cantidad'] = nueva_cantidad
        mov['motivo'] = motivo_final
        mov['tipo'] = nuevo_tipo
        mov['usuario_edicion'] = session['user']['nombre']

        return jsonify({
            "success": True,
            "mensaje": f"Movimiento #MOV-{mov_id} registrado como DEFECTUOSO. El registro en Kardex fue guardado y el stock en inventario se mantuvo intacto en {prod['stock']} unidades.",
            "movimiento": mov,
            "stock_actual": prod['stock']
        })

    # Si es "Producto agregado de más / Ajuste de cantidad": SÍ se recalcula y actualiza el stock
    tipo_antiguo = mov['tipo'].upper()
    cant_antigua = mov['cantidad']
    
    es_entrada_antigua = any(k in tipo_antiguo for k in ['ENTRADA', 'COMPRA', 'INICIAL'])
    efecto_antiguo = cant_antigua if es_entrada_antigua else -cant_antigua

    tipo_nuevo = nuevo_tipo.upper()
    es_entrada_nueva = any(k in tipo_nuevo for k in ['ENTRADA', 'COMPRA', 'INICIAL'])
    efecto_nuevo = nueva_cantidad if es_entrada_nueva else -nueva_cantidad

    diferencia_stock = efecto_nuevo - efecto_antiguo

    if prod['stock'] + diferencia_stock < 0:
        return jsonify({
            "error": f"No hay suficiente existencia en inventario para realizar esta reducción. Stock actual: {prod['stock']} unidades."
        }), 400

    prod['stock'] += diferencia_stock

    mov['cantidad'] = nueva_cantidad
    mov['motivo'] = nuevo_motivo
    mov['tipo'] = nuevo_tipo
    mov['usuario_edicion'] = session['user']['nombre']

    return jsonify({
        "success": True,
        "mensaje": f"Movimiento #MOV-{mov_id} actualizado por producto de más/ajuste. Inventario de '{prod['nombre']}' ajustado a {prod['stock']} unidades.",
        "movimiento": mov,
        "stock_actual": prod['stock']
    })


# --- VENTAS (POS) ---
@app.route('/api/ventas', methods=['GET', 'POST'])
@login_required
def api_ventas():
    global NEXT_SALE_ID
    if request.method == 'GET':
        return jsonify(VENTAS)

    if request.method == 'POST':
        # Permiso: Administrador y Vendedor
        if session['user']['rol'] not in ['Administrador', 'Vendedor']:
            return jsonify({"error": "No tienes permiso para procesar ventas."}), 403
        
        data = request.json or {}
        cliente = data.get('cliente', 'Cliente General').strip()
        forma_pago = data.get('forma_pago', 'Efectivo').strip()
        items = data.get('items', []) # [{"producto_id": 1, "cantidad": 2}, ...]

        if not items:
            return jsonify({"error": "El carrito de compra está vacío."}), 400

        # Validar existencia y stock disponible
        total_venta = 0.0
        detalles_venta = []

        for item in items:
            p_id = int(item.get('producto_id'))
            cant = int(item.get('cantidad', 1))
            
            prod = next((p for p in PRODUCTOS if p['id'] == p_id), None)
            if not prod:
                return jsonify({"error": f"Producto ID {p_id} no existe."}), 400
            
            if prod['stock'] < cant:
                return jsonify({"error": f"Stock insuficiente para '{prod['nombre']}'. Disponible: {prod['stock']}"}), 400

        import datetime
        fecha_actual = datetime.date.today().strftime('%Y-%m-%d')
        codigo_v = f"VEN-{NEXT_SALE_ID:04d}"

        # Descontar stock, registrar movimiento y guardar venta
        for item in items:
            p_id = int(item.get('producto_id'))
            cant = int(item.get('cantidad', 1))
            prod = next(p for p in PRODUCTOS if p['id'] == p_id)
            
            prod['stock'] -= cant # Salida de inventario
            subtotal = prod['precio'] * cant
            total_venta += subtotal
            
            registrar_movimiento(prod, "SALIDA_VENTA", cant, f"Venta {codigo_v}", session['user']['nombre'])

            detalles_venta.append({
                "producto_id": prod['id'],
                "producto_codigo": prod['codigo'],
                "producto_nombre": prod['nombre'],
                "cantidad": cant,
                "precio_unitario": prod['precio'],
                "subtotal": round(subtotal, 2)
            })

        nueva_venta = {
            "id": NEXT_SALE_ID,
            "codigo_venta": codigo_v,
            "cliente": cliente if cliente else "Cliente General",
            "fecha": fecha_actual,
            "vendedor": session['user']['nombre'],
            "total": round(total_venta, 2),
            "forma_pago": forma_pago,
            "detalles": detalles_venta
        }

        VENTAS.append(nueva_venta)
        NEXT_SALE_ID += 1

        return jsonify({"success": True, "mensaje": "Venta procesada y stock actualizado.", "venta": nueva_venta}), 201

@app.route('/api/ventas/<int:v_id>', methods=['GET'])
@login_required
def api_venta_detalle(v_id):
    v = next((item for item in VENTAS if item['id'] == v_id), None)
    if not v:
        return jsonify({"error": "Venta no encontrada."}), 404
    return jsonify(v)


# --- COMPRAS Y PROVEEDORES ---
@app.route('/api/proveedores', methods=['GET', 'POST'])
@login_required
def api_proveedores():
    global NEXT_PROV_ID
    if request.method == 'GET':
        return jsonify(PROVEEDORES)
    if request.method == 'POST':
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
            return jsonify({"error": "No tienes permisos para agregar proveedores."}), 403
        data = request.json or {}
        nombre = data.get('nombre', '').strip()
        contacto = data.get('contacto', '').strip()
        telefono = data.get('telefono', '').strip()
        email = data.get('email', '').strip()

        if not nombre:
            return jsonify({"error": "Nombre del proveedor es obligatorio."}), 400

        prov = {
            "id": NEXT_PROV_ID,
            "nombre": nombre,
            "contacto": contacto,
            "telefono": telefono,
            "email": email
        }
        PROVEEDORES.append(prov)
        NEXT_PROV_ID += 1
        return jsonify({"success": True, "proveedor": prov}), 201

@app.route('/api/compras', methods=['GET', 'POST'])
@login_required
def api_compras():
    global NEXT_PURCHASE_ID
    if request.method == 'GET':
        return jsonify(COMPRAS)

    if request.method == 'POST':
        # Permiso: Administrador y Encargado de Inventario
        if session['user']['rol'] not in ['Administrador', 'Encargado de Inventario']:
            return jsonify({"error": "No tienes permiso para registrar compras."}), 403
        
        data = request.json or {}
        prov_id = int(data.get('proveedor_id', 1))
        items = data.get('items', []) # [{"producto_id": 1, "cantidad": 10, "costo_unitario": 9.00}]

        prov = next((p for p in PROVEEDORES if p['id'] == prov_id), None)
        prov_nombre = prov['nombre'] if prov else "Proveedor General"

        if not items:
            return jsonify({"error": "Debe incluir al menos un producto recibido."}), 400

        total_compra = 0.0
        detalles_compra = []

        import datetime
        fecha_actual = datetime.date.today().strftime('%Y-%m-%d')
        compra_code = f"COM-#{NEXT_PURCHASE_ID}"

        for item in items:
            p_id = int(item.get('producto_id'))
            cant = int(item.get('cantidad', 1))
            costo_u = float(item.get('costo_unitario', 0.0))

            prod = next((p for p in PRODUCTOS if p['id'] == p_id), None)
            if prod:
                prod['stock'] += cant # Incremento automático de existencia
                if costo_u > 0:
                    prod['costo'] = costo_u
                subt = (costo_u if costo_u > 0 else prod['costo']) * cant
                total_compra += subt
                
                registrar_movimiento(prod, "ENTRADA_COMPRA", cant, f"Compra {compra_code} - {prov_nombre}", session['user']['nombre'])

                detalles_compra.append({
                    "producto_id": prod['id'],
                    "producto_nombre": prod['nombre'],
                    "cantidad": cant,
                    "costo_unitario": costo_u if costo_u > 0 else prod['costo'],
                    "subtotal": round(subt, 2)
                })

        nueva_compra = {
            "id": NEXT_PURCHASE_ID,
            "proveedor_id": prov_id,
            "proveedor_nombre": prov_nombre,
            "fecha": fecha_actual,
            "total": round(total_compra, 2),
            "detalles": detalles_compra
        }
        COMPRAS.append(nueva_compra)
        NEXT_PURCHASE_ID += 1

        return jsonify({"success": True, "mensaje": "Compra registrada e inventario actualizado.", "compra": nueva_compra}), 201


# --- REPORTES Y CONTABILIDAD ---
@app.route('/api/reportes', methods=['GET'])
@login_required
def api_reportes():
    # Accesible para Administrador y Contador
    if session['user']['rol'] not in ['Administrador', 'Contador']:
        return jsonify({"error": "Acceso reservado para Administrador y Consulta / Contador."}), 403

    total_ventas_monto = sum(v['total'] for v in VENTAS)
    total_ventas_cantidad = len(VENTAS)
    total_compras_monto = sum(c['total'] for c in COMPRAS)
    total_compras_cantidad = len(COMPRAS)

    valor_inventario = sum(p['stock'] * p['costo'] for p in PRODUCTOS)
    productos_bajo_stock = [p for p in PRODUCTOS if p['stock'] <= p['min_stock']]

    # Cantidad total de productos/unidades sold
    unidades_vendidas_total = sum(
        sum(item['cantidad'] for item in v['detalles'])
        for v in VENTAS
    )

    # Top productos vendidos (agrupados por ID)
    conteo_prods = {}
    for v in VENTAS:
        for item in v['detalles']:
            pid = item['producto_id']
            if pid not in conteo_prods:
                conteo_prods[pid] = {
                    "id": pid,
                    "nombre": item['producto_nombre'],
                    "cantidad_vendida": 0,
                    "monto_total": 0.0
                }
            conteo_prods[pid]["cantidad_vendida"] += item['cantidad']
            conteo_prods[pid]["monto_total"] += item.get('subtotal', item['precio_unitario'] * item['cantidad'])

    top_productos = sorted(list(conteo_prods.values()), key=lambda x: x['cantidad_vendida'], reverse=True)

    # Ventas agrupadas por fecha (para gráfico de tendencia)
    ventas_por_fecha = {}
    for v in VENTAS:
        f = v['fecha']
        ventas_por_fecha[f] = ventas_por_fecha.get(f, 0.0) + v['total']

    # Ganancia bruta estimada
    ganancia_estimada = sum(
        sum((item['precio_unitario'] - next((p['costo'] for p in PRODUCTOS if p['id'] == item['producto_id']), 0)) * item['cantidad'] for item in v['detalles'])
        for v in VENTAS
    )

    # Rotación de inventario estimada (Unidades vendidas / Stock total promedio)
    stock_total_actual = sum(p['stock'] for p in PRODUCTOS)
    rotacion_ratio = round(unidades_vendidas_total / (stock_total_actual if stock_total_actual > 0 else 1), 2)

    resumen = {
        "ventas_totales_monto": round(total_ventas_monto, 2),
        "ventas_totales_conteo": total_ventas_cantidad,
        "unidades_vendidas_total": unidades_vendidas_total,
        "compras_totales_monto": round(total_compras_monto, 2),
        "compras_totales_conteo": total_compras_cantidad,
        "valor_inventario_costo": round(valor_inventario, 2),
        "margen_bruto_estimado": round(ganancia_estimada, 2),
        "rotacion_inventario": rotacion_ratio,
        "alerta_stock_bajo_conteo": len(productos_bajo_stock),
        "productos_bajo_stock": productos_bajo_stock,
        "top_productos": top_productos,
        "ventas_por_fecha": ventas_por_fecha
    }

    return jsonify(resumen)


# ==============================================================================
# EJECUCIÓN DEL SERVIDOR
# ==============================================================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)