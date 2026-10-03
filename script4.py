import codecs

with codecs.open("Fronted/static/js/main.js", "r", "utf-8") as f:
    content = f.read()

replacement = """
            <td>
                <button class="btn btn-secondary icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem; margin-right: 5px;" onclick="verComprobanteVenta(${v.id})">
                    <i class="ph-bold ph-receipt"></i> Ticket
                </button>
                ${v.estado === "Anulada" ? "<span class=\"text-accent-red font-bold\" style=\"font-size:0.8rem;\"><i class=\"ph-bold ph-x-circle\"></i> Anulada</span>" : `<button class="btn btn-danger icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="anularVenta(${v.id})"><i class="ph-bold ph-trash"></i> Anular</button>`}
            </td>
"""

content = content.replace("""            <td>
                <button class="btn btn-secondary icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="verComprobanteVenta(${v.id})">
                    <i class="ph-bold ph-receipt"></i> Ver Ticket
                </button>
            </td>""", replacement.strip())

js_func = """
async function anularVenta(v_id) {
    if (!confirm("�Estás seguro de que deseas anular esta venta? Esta acción regresará el stock y no se puede deshacer.")) return;
    try {
        const response = await fetch(`/api-ventas/${v_id}/anular`, { method: "POST" });
        const data = await response.json();
        if (data.error) {
            alert(data.error);
        } else {
            alert(data.mensaje);
            loadVentasHistory();
            loadInventario();
            loadDashboardStats();
        }
    } catch(e) {
        alert("Error al intentar anular la venta.");
        console.error(e);
    }
}
"""

content = content + "\n" + js_func

with codecs.open("Fronted/static/js/main.js", "w", "utf-8") as f:
    f.write(content)
