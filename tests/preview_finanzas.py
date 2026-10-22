"""Vista de prueba con mayor sintético en memoria. No importa app.py ni conecta SQL Server."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flask import render_template, session, jsonify
from test_flujo import ApiTest, asiento
from ejemplo_conciliacion import ejemplo, EMPRESA

test = ApiTest()
test.setUp()
test.insert(asiento(2, [(2, 200, 0), (10, 0, 200)]))
test.insert(asiento(3, [(5, 1000, 0), (8, 0, 800), (2, 0, 200)]))
app = test.app
app.static_folder = str(Path(__file__).resolve().parents[1] / 'Fronted/static')
modo_conciliacion = '--conciliacion' in sys.argv
if modo_conciliacion:
    test.insert(asiento(900, [(2, 78000, 0), (9, 0, 78000)], '2018-12-31'))
    for i, (dia, concepto, debe, haber) in enumerate(EMPRESA, 901):
        movimientos = asiento(i, [(2, debe, haber), (10 if debe else 13, haber, debe)], f'2019-01-{dia}')
        for m in movimientos: m['concepto'] = concepto
        test.insert(movimientos)


@app.route('/ejemplo-conciliacion')
def datos_ejemplo():
    return jsonify(ejemplo()[0])


@app.route('/logout')
def logout():
    return 'Prueba'


@app.route('/')
def preview():
    session['user'] = {'id': 1, 'rol': 'Contador', 'nombre': 'Contador de prueba'}
    html = render_template('index.html', usuario=session['user'])
    start = html.index('<section id="tab-finanzas"')
    end = html.rfind('</section>', start, html.index('<!-- TAB FISCAL', start)) + len('</section>')
    section = html[start:end].replace('id="tab-finanzas" class="tab-content"', 'id="tab-finanzas" class="tab-content active"')
    main = (Path(app.static_folder) / 'js/main.js').read_text(encoding='utf-8')
    switch = main[main.index('function switchFinanzasTab('):main.index('async function cargarDatosFinanzas()')]
    resultado = '''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><link rel="stylesheet" href="/static/css/styles.css"><link rel="stylesheet" href="/static/css/conciliacion.css">
    <style>body{display:block;padding:20px}.tab-content{display:block!important}.section-header{flex-wrap:wrap}.subtabs-container{flex-wrap:wrap}</style></head><body>''' + section + '''
    <script src="/static/js/flujo_efectivo.js"></script><script src="/static/js/flujo_controles.js"></script><script src="/static/js/conciliacion.js"></script>
    <script>''' + switch + '''
    document.getElementById('fin-fecha-inicio').value='2026-10-01';document.getElementById('fin-fecha-fin').value='2026-10-31';
    document.getElementById('conc-mes').value='10';
    switchFinanzasTab('fin-flujo',document.querySelector('[onclick*="fin-flujo"]'));
    </script></body></html>'''
    if modo_conciliacion:
        resultado = resultado.replace("'2026-10-01'", "'2019-01-01'").replace("'2026-10-31'", "'2019-01-31'")
        resultado = resultado.replace("document.getElementById('conc-mes').value='10';", "document.getElementById('conc-mes').value='1';document.getElementById('conc-anio').value='2019';")
        resultado = resultado.replace("switchFinanzasTab('fin-flujo',document.querySelector('[onclick*=\"fin-flujo\"]'));", "switchFinanzasTab('fin-conciliacion',document.querySelector('[onclick*=\"fin-conciliacion\"]'));")
    return resultado


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5088 if modo_conciliacion else 5087, threaded=False, use_reloader=False)
