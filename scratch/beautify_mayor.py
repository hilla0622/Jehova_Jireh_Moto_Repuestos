import os

main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'
index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'

# 1. FIX MAIN.JS
with open(main_path, 'r', encoding='utf-8') as f:
    main_content = f.read()

def num_format(val):
    return val + ".toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})"

# Replace .toFixed(2) with formatting logic
js_target = """        document.getElementById('mayor-saldo-inicial').innerText = `C$ ${data.saldo_inicial.toFixed(2)}`;
        
        const tbody = document.getElementById('tbody-mayor');
        if (data.movimientos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No hay movimientos en este periodo.</td></tr>`;
        } else {
            tbody.innerHTML = data.movimientos.map(m => `
                <tr>
                    <td>${m.fecha.substring(0, 16).replace('T', ' ')}</td>
                    <td><strong>#${m.asiento_id}</strong></td>
                    <td>${m.concepto}</td>
                    <td class="text-accent-green">C$ ${m.debe.toFixed(2)}</td>
                    <td class="text-accent-red">C$ ${m.haber.toFixed(2)}</td>
                    <td style="font-weight:bold; color:var(--primary);">C$ ${m.saldo.toFixed(2)}</td>
                </tr>
            `).join('');
        }
        
        document.getElementById('tfoot-mayor').style.display = 'table-footer-group';
        document.getElementById('mayor-saldo-final').innerText = `C$ ${data.saldo_final.toFixed(2)}`;"""

js_replace = """        const formatNum = (num) => num.toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        document.getElementById('mayor-saldo-inicial').innerText = `C$ ${formatNum(data.saldo_inicial)}`;
        
        const tbody = document.getElementById('tbody-mayor');
        if (data.movimientos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted" style="padding:20px;">No hay movimientos en este periodo.</td></tr>`;
        } else {
            tbody.innerHTML = data.movimientos.map(m => `
                <tr style="border-bottom: 1px solid rgba(255,255,255,0.05); transition: background 0.3s;">
                    <td style="padding: 12px 15px;">${m.fecha.substring(0, 16).replace('T', ' ')}</td>
                    <td style="padding: 12px 15px;"><strong>#${m.asiento_id}</strong></td>
                    <td style="padding: 12px 15px;">${m.concepto}</td>
                    <td class="text-accent-green" style="padding: 12px 15px; text-align: right;">C$ ${formatNum(m.debe)}</td>
                    <td class="text-accent-red" style="padding: 12px 15px; text-align: right;">C$ ${formatNum(m.haber)}</td>
                    <td style="font-weight:bold; color:var(--primary); padding: 12px 15px; text-align: right;">C$ ${formatNum(m.saldo)}</td>
                </tr>
            `).join('');
        }
        
        document.getElementById('tfoot-mayor').style.display = 'table-footer-group';
        document.getElementById('mayor-saldo-final').innerText = `C$ ${formatNum(data.saldo_final)}`;"""

if "formatNum" not in main_content:
    main_content = main_content.replace(js_target, js_replace)

# 2. FIX INDEX.HTML (Scroll and spacing)
with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

html_target = """                                <div class="table-responsive">
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
                                </div>"""

html_replace = """                                <div class="table-responsive" style="max-height: 500px; overflow-y: auto; border-radius: 8px; border: 1px solid rgba(255,255,255,0.1);">
                                    <table class="table" style="width: 100%; border-collapse: collapse;">
                                        <thead style="position: sticky; top: 0; background: #1a1e2d; z-index: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.2);">
                                            <tr>
                                                <th style="padding: 15px; text-align: left; border-bottom: 2px solid rgba(255,255,255,0.1);">Fecha</th>
                                                <th style="padding: 15px; text-align: left; border-bottom: 2px solid rgba(255,255,255,0.1);">Asiento #</th>
                                                <th style="padding: 15px; text-align: left; border-bottom: 2px solid rgba(255,255,255,0.1);">Concepto</th>
                                                <th style="padding: 15px; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.1);">Debe</th>
                                                <th style="padding: 15px; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.1);">Haber</th>
                                                <th style="padding: 15px; text-align: right; border-bottom: 2px solid rgba(255,255,255,0.1);">Saldo</th>
                                            </tr>
                                        </thead>
                                        <tbody id="tbody-mayor">
                                            <tr><td colspan="6" class="text-center text-muted" style="padding:20px;">Seleccione una cuenta para consultar el Libro Mayor.</td></tr>
                                        </tbody>
                                        <tfoot id="tfoot-mayor" style="display:none; position: sticky; bottom: 0; background: #1a1e2d; z-index: 1; box-shadow: 0 -2px 4px rgba(0,0,0,0.2);">
                                            <tr style="font-weight:bold;">
                                                <td colspan="5" class="text-right" style="padding: 15px;">Saldo Final:</td>
                                                <td id="mayor-saldo-final" style="padding: 15px; text-align: right; color: var(--primary);">C$ 0.00</td>
                                            </tr>
                                        </tfoot>
                                    </table>
                                </div>"""

if 'style="max-height: 500px;' not in index_content:
    index_content = index_content.replace(html_target, html_replace)

# Cache busting to 1.4
index_content = index_content.replace('js/main.js\') }}?v=1.3', 'js/main.js\') }}?v=1.4')

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_content)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_content)

print("Actualizacion de diseno completada")
