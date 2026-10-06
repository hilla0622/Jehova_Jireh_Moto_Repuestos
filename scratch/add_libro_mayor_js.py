import os

main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'

with open(main_path, 'r', encoding='utf-8') as f:
    main_content = f.read()

js_code = """
// ==============================================================================
// LIBRO MAYOR
// ==============================================================================
async function cargarLibroMayor() {
    const cuentaId = document.getElementById('mayor-cuenta').value;
    if (!cuentaId) {
        alert("Seleccione una cuenta contable");
        return;
    }
    
    const desde = document.getElementById('fin-fecha-desde').value;
    const hasta = document.getElementById('fin-fecha-hasta').value;
    
    let url = `/api/finanzas/libro_mayor?cuenta_id=${cuentaId}`;
    if (desde) url += `&fecha_inicio=${desde}`;
    if (hasta) url += `&fecha_fin=${hasta}`;
    
    try {
        const res = await fetch(url);
        const data = await res.json();
        
        if (!res.ok) {
            alert(data.error || "Error al cargar el libro mayor");
            return;
        }
        
        document.getElementById('mayor-info').style.display = 'block';
        document.getElementById('mayor-titulo-cuenta').innerText = `Cuenta: ${data.cuenta.codigo} - ${data.cuenta.nombre} (${data.cuenta.naturaleza})`;
        document.getElementById('mayor-saldo-inicial').innerText = `C$ ${data.saldo_inicial.toFixed(2)}`;
        
        const tbody = document.getElementById('tbody-mayor');
        if (data.movimientos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted">No hay movimientos en este periodo.</td></tr>`;
        } else {
            tbody.innerHTML = data.movimientos.map(m => `
                <tr>
                    <td>${formatDateToLocal(m.fecha)}</td>
                    <td><strong>#${m.asiento_id}</strong></td>
                    <td>${m.concepto}</td>
                    <td class="text-accent-green">C$ ${m.debe.toFixed(2)}</td>
                    <td class="text-accent-red">C$ ${m.haber.toFixed(2)}</td>
                    <td style="font-weight:bold; color:var(--primary);">C$ ${m.saldo.toFixed(2)}</td>
                </tr>
            `).join('');
        }
        
        document.getElementById('tfoot-mayor').style.display = 'table-footer-group';
        document.getElementById('mayor-saldo-final').innerText = `C$ ${data.saldo_final.toFixed(2)}`;
        
    } catch (e) {
        console.error(e);
        alert("Error de conexiÃ³n");
    }
}
"""

if "cargarLibroMayor()" not in main_content:
    main_content += "\n" + js_code
    
# We need to populate the select 'mayor-cuenta'. The best place is where 'window.cuentasDisponibles' is updated.
target_populate = "window.cuentasDisponibles = data;"
replace_populate = """window.cuentasDisponibles = data;
        
        // Populate Libro Mayor select
        const mayorSelect = document.getElementById('mayor-cuenta');
        if (mayorSelect) {
            mayorSelect.innerHTML = '<option value="">-- Seleccione una cuenta --</option>' + 
                data.map(c => `<option value="${c.id}">${c.codigo} - ${c.nombre}</option>`).join('');
        }"""

main_content = main_content.replace(target_populate, replace_populate)

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_content)
    
print("JS modificado.")
