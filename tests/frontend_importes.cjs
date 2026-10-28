const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const nodes = new Map();
const element = id => {
    if (!nodes.has(id)) nodes.set(id, { textContent: '', innerHTML: '', style: {} });
    return nodes.get(id);
};
const errors = [];
const fixtures = {
    '/api/compras': [{ id: 42, fecha: '2025-01-01', proveedor_nombre: 'Proveedor de prueba', total: 12345.67 }],
    '/api/proveedores': [{ id: 7, nombre: 'Proveedor de prueba', contacto: 'Contacto', telefono: '00000000', activo: true }],
    '/api/ventas': [{ id: 1, codigo_venta: 'VENTA-PRUEBA', fecha: '2025-01-01', total: 2460000 }],
    '/api/productos': [],
};
const ctx = vm.createContext({
    URLSearchParams,
    console: { log() {}, error: (...args) => errors.push(args) },
    window: { alert() {}, addEventListener() {} },
    document: { addEventListener() {}, getElementById: element, querySelectorAll() { return []; } },
    fetch: async url => ({ ok: true, json: async () => fixtures[url] }),
});
vm.runInContext(fs.readFileSync('Fronted/static/js/main.js', 'utf8'), ctx);
const reportsSource = fs.readFileSync('Fronted/static/js/corte_v.js', 'utf8');
vm.runInContext(reportsSource.slice(reportsSource.indexOf('function renderDesgloseMeses('),
    reportsSource.indexOf('function renderTablaCategoriasReportes(')), ctx);

(async () => {
    await ctx.loadComprasYProveedores();
    assert.deepEqual(errors, [], 'La carga no debe ocultar errores de renderizado');
    assert.match(element('tbody-compras').innerHTML, /12,345\.67/);
    assert.match(element('tbody-proveedores').innerHTML, /Proveedor de prueba/);
    await ctx.loadDashboardStats();
    assert.equal(element('stat-total-ventas').textContent, '$2,460,000.00');
    assert.match(element('recent-sales-list').innerHTML, /2,460,000\.00/);
    vm.runInContext('cartPOS=[{producto_id:1,precio:1234.5,cantidad:2,stock_max:10,nombre:"Prueba"}];renderCartPOS()', ctx);
    assert.equal(element('pos-cart-total').textContent, '$2,469.00');
    assert.equal(vm.runInContext('cartPOS[0].precio', ctx), 1234.5);
    assert.equal(ctx.formatMoneda(-1234.5, ''), '-1,234.50');
    ctx.renderDesgloseMeses([{mes_numero: 1, mes_nombre: 'Enero', transacciones: 1,
        unidades: 101, ventas: 90000, costo: 45000, utilidad: 45000, margen_pct: 50}]);
    const monthly = element('tbody-desglose-meses').innerHTML;
    assert.match(monthly, /Enero/);
    assert.match(monthly, /50\.00%/);
    assert.doesNotMatch(monthly, /undefined/);
    console.log('OK: compras y proveedores visibles; separadores en panel y POS; valores numéricos conservados.');
    console.log('OK: desglose mensual usa los nombres y márgenes devueltos por el servidor.');
    // Una respuesta anterior lenta no debe reemplazar el año que se acaba de elegir.
    vm.runInContext(reportsSource.slice(reportsSource.indexOf('async function ejecutarConsultaReportes('),
        reportsSource.indexOf('function renderReportesCompleto(')), ctx);
    ctx._filtroPresetActivo = 'mes_anio_directo';
    ctx._criterioABCActual = 'inversion';
    ctx._ultimaConsultaReporte = 0;
    element('rep-select-mes').value = '';
    const pending = [];
    const rendered = [];
    ctx.fetch = () => new Promise(resolve => pending.push(resolve));
    ctx.renderReportesCompleto = data => rendered.push(data.periodo.anio);
    ctx.cargarEstadisticasDevoluciones = () => {};
    element('rep-select-anio').value = '2026';
    const older = ctx.ejecutarConsultaReportes();
    element('rep-select-anio').value = '2024';
    const newer = ctx.ejecutarConsultaReportes();
    pending[1]({json: async () => ({periodo: {anio: 2024}, alertas: {}})});
    await newer;
    pending[0]({json: async () => ({periodo: {anio: 2026}, alertas: {}})});
    await older;
    assert.deepEqual(rendered, [2024]);
    console.log('OK: respuestas fuera de orden conservan el último año seleccionado.');
})().catch(error => { console.error(error); process.exitCode = 1; });
