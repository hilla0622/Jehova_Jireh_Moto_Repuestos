import os

# --- APP.PY ---
app_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\app.py'

route_code = """
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
                "fecha": m['fecha'],
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

"""

with open(app_path, 'r', encoding='utf-8') as f:
    app_content = f.read()

if "def api_libro_mayor():" not in app_content:
    app_content = app_content.replace("@app.route('/api/finanzas/balance_comprobacion', methods=['GET'])", route_code + "\n@app.route('/api/finanzas/balance_comprobacion', methods=['GET'])")
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(app_content)


# --- INDEX.HTML ---
index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

# Add button
target_buttons = """<button class="subnav-btn" onclick="switchFinanzasSubtab('fin-asientos', this)">
                            <i class="ph-bold ph-book-open"></i> Libro Diario (Asientos)
                        </button>"""
replace_buttons = """<button class="subnav-btn" onclick="switchFinanzasSubtab('fin-asientos', this)">
                            <i class="ph-bold ph-book-open"></i> Libro Diario (Asientos)
                        </button>
                        <button class="subnav-btn" onclick="switchFinanzasSubtab('fin-mayor', this)">
                            <i class="ph-bold ph-books"></i> Libro Mayor (Cuentas T)
                        </button>"""

if "fin-mayor" not in index_content:
    index_content = index_content.replace(target_buttons, replace_buttons)

# Add view
target_view = """<!-- VISTA: BALANCE DE COMPROBACION -->
                    <div id="subtab-fin-balance" class="subtab-view">"""

replace_view = """<!-- VISTA: LIBRO MAYOR -->
                    <div id="subtab-fin-mayor" class="subtab-view">
                        <div class="card">
                            <div class="card-header" style="display:flex; gap:10px; align-items:center;">
                                <div style="flex:1;">
                                    <label>Seleccionar Cuenta Contable:</label>
                                    <select id="mayor-cuenta" class="form-control" style="max-width:400px;"></select>
                                </div>
                                <div>
                                    <button class="btn btn-primary" onclick="cargarLibroMayor()">
                                        <i class="ph-bold ph-magnifying-glass"></i> Consultar
                                    </button>
                                </div>
                            </div>
                            <div class="card-body">
                                <div id="mayor-info" style="display:none; margin-bottom:15px; padding:10px; background:rgba(0,0,0,0.2); border-radius:8px;">
                                    <h3 id="mayor-titulo-cuenta" style="margin:0; color:var(--primary);"></h3>
                                    <p style="margin:5px 0 0 0;">Saldo Inicial: <strong id="mayor-saldo-inicial">C$ 0.00</strong></p>
                                </div>
                                <div class="table-responsive">
                                    <table class="table">
                                        <thead>
                                            <tr>
                                                <th>Fecha</th>
                                                <th>Asiento #</th>
                                                <th>Concepto</th>
                                                <th>Debe</th>
                                                <th>Haber</th>
                                                <th>Saldo</th>
                                            </tr>
                                        </thead>
                                        <tbody id="tbody-mayor">
                                            <tr><td colspan="6" class="text-center text-muted">Seleccione una cuenta para consultar el Libro Mayor.</td></tr>
                                        </tbody>
                                        <tfoot id="tfoot-mayor" style="display:none;">
                                            <tr style="background: rgba(0,0,0,0.3); font-weight:bold;">
                                                <td colspan="5" class="text-right">Saldo Final:</td>
                                                <td id="mayor-saldo-final">C$ 0.00</td>
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- VISTA: BALANCE DE COMPROBACION -->
                    <div id="subtab-fin-balance" class="subtab-view">"""

if "subtab-fin-mayor" not in index_content:
    index_content = index_content.replace(target_view, replace_view)
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

print("Backend y UI modificados.")
