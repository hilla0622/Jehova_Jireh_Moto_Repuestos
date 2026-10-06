import os

app_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\app.py'

with open(app_path, 'r', encoding='utf-8') as f:
    app_content = f.read()

# 1. Update /api/finanzas/cuentas (POST)
target_post_cuentas = """    if request.method == 'POST':
        data = request.json or {}"""
replacement_post_cuentas = """    if request.method == 'POST':
        if session['user']['rol'] == 'Contador':
            return jsonify({"error": "No tienes permiso para crear cuentas."}), 403
        data = request.json or {}"""
app_content = app_content.replace(target_post_cuentas, replacement_post_cuentas)

# 2. Update /api/finanzas/cuentas/<int:id> (DELETE)
target_delete_cuentas = """@app.route('/api/finanzas/cuentas/<int:id>', methods=['DELETE'])
@login_required
def api_finanzas_cuentas_delete(id):
    try:"""
replacement_delete_cuentas = """@app.route('/api/finanzas/cuentas/<int:id>', methods=['DELETE'])
@login_required
def api_finanzas_cuentas_delete(id):
    if session['user']['rol'] == 'Contador':
        return jsonify({"error": "No tienes permiso para borrar cuentas."}), 403
    try:"""
app_content = app_content.replace(target_delete_cuentas, replacement_delete_cuentas)

# 3. Update /api/finanzas/asientos (POST)
target_post_asientos = """    if request.method == 'POST':
        data = request.json or {}"""
replacement_post_asientos = """    if request.method == 'POST':
        if session['user']['rol'] == 'Contador':
            return jsonify({"error": "No tienes permiso para registrar nuevos asientos."}), 403
        data = request.json or {}"""
# Wait, this might match multiple times. Let's be more specific.
target_post_asientos_specific = """@app.route('/api/finanzas/asientos', methods=['GET', 'POST'])
@login_required
def api_finanzas_asientos():
    if request.method == 'GET':"""

replacement_post_asientos_specific = """@app.route('/api/finanzas/asientos', methods=['GET', 'POST'])
@login_required
def api_finanzas_asientos():
    if request.method == 'POST' and session['user']['rol'] == 'Contador':
        return jsonify({"error": "No tienes permiso para registrar nuevos asientos."}), 403
        
    if request.method == 'GET':"""
app_content = app_content.replace(target_post_asientos_specific, replacement_post_asientos_specific)

with open(app_path, 'w', encoding='utf-8') as f:
    f.write(app_content)

print("App.py updated with specific Contador restrictions.")
