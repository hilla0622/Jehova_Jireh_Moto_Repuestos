import re

index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'

with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

target_view = """                    <!-- CONTENIDO: BALANCE GENERAL -->
                    <div id="fin-balance" class="fin-tab-content" style="display: none;">"""

replace_view = """                    <!-- CONTENIDO: LIBRO MAYOR -->
                    <div id="fin-mayor" class="fin-tab-content" style="display: none;">
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

                    <!-- CONTENIDO: BALANCE GENERAL -->
                    <div id="fin-balance" class="fin-tab-content" style="display: none;">"""

if '<div id="fin-mayor"' not in index_content:
    index_content = index_content.replace(target_view, replace_view)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_content)
    
print("Vista insertada correctamente.")
