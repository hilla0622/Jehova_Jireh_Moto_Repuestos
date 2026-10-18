"""Vista de RRHH con SQLite en memoria y bloqueo explícito de conexiones reales."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from flask import render_template, render_template_string, session
from test_rrhh import RRHHTest, backend

test = RRHHTest()
test.setUp()
app = backend.app


@app.route('/__rrhh_preview')
def preview():
    session['user'] = {'id':1, 'rol':'Administrador', 'username':'prueba', 'nombre':'Prueba RRHH'}
    html = render_template('index.html', usuario=session['user'])
    start = html.index('    <div class="modal" id="modal-expediente-digital">')
    end = html.index('    <div class="modal"', start + 20)
    expediente = html[start:end]
    return render_template_string('''<!DOCTYPE html><html lang="es"><head><meta charset="utf-8">
        <meta name="viewport" content="width=device-width,initial-scale=1">
        <link rel="stylesheet" href="/static/css/styles.css">
        <link rel="stylesheet" href="/static/css/rrhh_control.css">
        <style>body{display:block;padding:24px;overflow:auto}.preview{max-width:1200px;margin:auto}.modal-body{overflow-y:auto}</style>
        </head><body><main class="preview" id="tab-rrhh"><h1>Recursos Humanos · Seguridad e higiene</h1>
        <p>Vista de prueba con datos ficticios</p>
        {% include 'rrhh_seguridad_control.html' %}
        <button onclick="abrirExpedienteDigital(1,'Empleado prueba')">Expediente de prueba</button>
        <button onclick="abrirPagoControl()">Registrar pago</button>
        <div style="overflow-x:auto"><table><tbody id="tbody-pagos-nomina"></tbody></table></div></main>
        {% include 'rrhh_control_modales.html' %}
        {{ expediente|safe }}
        <script>function openModal(id){document.getElementById(id).classList.add('active')}
        function closeModal(id){document.getElementById(id).classList.remove('active')}</script>
        <script src="/static/js/rrhh_control.js"></script>
        <script src="/static/js/corte_v.js"></script>
        <script>cargarRiesgosHigiene();cargarEppHigiene();</script></body></html>''', expediente=expediente)


if __name__ == '__main__':
    test.generar()
    app.run(host='127.0.0.1', port=5088, threaded=False, use_reloader=False)
