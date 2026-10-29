/**
 * ==============================================================================
 *  fiscal.js — Controlador Frontend Oficial del Formulario 106 (Renta Anual IR)
 *  Ventanilla Electrónica Tributaria (VET) - DGI Nicaragua
 *  Sistema Jehová Jireh Moto Repuestos
 * ==============================================================================
 */

let anioFiscalSeleccionado = 2026;
let simulacionFiscalActual = null;
let declaracionGuardadaId = null;

function tasaIrAnual(ingresos, renta) {
    if (ingresos > 12000000) return 30;
    if (renta <= 100000) return 10;
    if (renta <= 200000) return 15;
    if (renta <= 350000) return 20;
    if (renta <= 500000) return 25;
    return 30;
}

function escaparFiscal(value) {
    return String(value).replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[ch]);
}

document.addEventListener('DOMContentLoaded', () => {
    const anioSelect = document.getElementById('fiscal-select-anio');
    if (anioSelect) {
        anioSelect.value = anioFiscalSeleccionado;
    }
});

/**
 * Punto de entrada llamado por main.js al abrir la pestaña #tab-fiscal
 */
function cargarModuloFiscal() {
    const anioSelect = document.getElementById('fiscal-select-anio');
    if (anioSelect) anioFiscalSeleccionado = parseInt(anioSelect.value) || 2026;
    
    // Cargar datos de negocio y simulación oficial
    cargarInfoTributaria();
    cargarSimulacionFiscal(false);
}

function cambiarAnioFiscal() {
    const anioSelect = document.getElementById('fiscal-select-anio');
    if (anioSelect) anioFiscalSeleccionado = parseInt(anioSelect.value) || 2026;
    cargarSimulacionFiscal(true);
}

/**
 * Carga RUC, Razón Social y Actividad desde el backend
 */
async function cargarInfoTributaria() {
    try {
        const res = await fetch('/api/fiscal/info');
        const data = await res.json();
        if (data.negocio) {
            const n = data.negocio;
            // Vista Cuentas
            const inRucCta = document.getElementById('vet-cta-ruc');
            const inRazonCta = document.getElementById('vet-cta-razon');
            const inActCta = document.getElementById('vet-cta-actividad');
            if (inRucCta) inRucCta.value = n.ruc;
            if (inRazonCta) inRazonCta.value = n.razon_social;
            if (inActCta) inActCta.value = n.actividad_economica;

            // Vista Resumen
            setVal('vet-resumen-ruc', n.ruc);
            setVal('vet-resumen-razon', n.razon_social);
            setVal('vet-resumen-actividad', n.actividad_economica);
        }
    } catch (err) {
        console.warn('Error cargando info tributaria:', err);
    }
}

/**
 * Carga y mapea los saldos contables reales en el Formulario 106
 */
async function cargarSimulacionFiscal(mostrarNotif = false) {
    const anioSolicitado = anioFiscalSeleccionado;
    simulacionFiscalActual = null;
    declaracionGuardadaId = null;
    const loadingState = document.getElementById('fiscal-loading-state');
    if (loadingState) loadingState.style.display = 'block';

    try {
        const res = await fetch(`/api/fiscal/simulacion/${anioSolicitado}`);
        if (!res.ok) throw new Error('Error al generar la liquidación contable.');
        const sim = await res.json();
        if (anioSolicitado !== anioFiscalSeleccionado) return;
        simulacionFiscalActual = sim;
        if (sim.negocio) {
            for (const [campo, id] of [['ruc', 'ruc'], ['razon_social', 'razon'], ['actividad_economica', 'actividad']]) {
                const input = document.getElementById(`vet-cta-${id}`);
                if (input) input.value = sim.negocio[campo] || '';
                setVal(`vet-resumen-${id}`, sim.negocio[campo] || '');
            }
        }
        const avisoDemo = document.getElementById('fiscal-demo-aviso');
        if (avisoDemo) avisoDemo.style.display = sim.datos_demostracion ? 'block' : 'none';

        // Actualizar fecha y periodo
        const hoy = new Date().toLocaleDateString('es-NI', { day: '2-digit', month: '2-digit', year: 'numeric' });
        setVal('vet-cta-fecha', hoy);
        setVal('vet-resumen-fecha', hoy);
        setVal('vet-cta-periodo', '12');
        setVal('vet-resumen-periodo', '12');
        setVal('vet-resumen-no-decl', `SIM-${anioFiscalSeleccionado}`);

        const cb = sim.cuentas_balance || {};
        const cr = sim.cuentas_resultados || {};

        // 1. Llenar inputs de cuentas individuales de Jehová Jireh (Activos)
        setIn('cta-1101', cb['1.1.01'] ?? 0);
        setIn('cta-1102', cb['1.1.02'] ?? 0);
        setIn('cta-1103', cb['1.1.03'] ?? 0);
        setIn('cta-1104', cb['1.1.04'] ?? 0);
        setIn('cta-1105', cb['1.1.05'] ?? 0);

        setIn('cta-1201', cb['1.2.01'] ?? 0);
        setIn('cta-1202', cb['1.2.02'] ?? 0);
        setIn('cta-1203', -Math.abs(cb['1.2.03'] ?? 0));
        setIn('cta-otros-act', cb['1.1.06'] ?? 0);

        // 2. Pasivos individuales
        setIn('cta-2101', cb['2.1.01'] ?? 0);
        setIn('cta-2102', cb['2.1.02'] ?? 0);
        setIn('cta-2103', cb['2.1.03'] ?? 0);
        setIn('cta-2104', cb['2.1.04'] ?? 0);
        setIn('cta-2105', cb['2.1.05'] ?? 0);
        setIn('cta-2106', cb['2.1.06'] ?? 0);
        setIn('cta-2107', cb['2.1.07'] ?? 0);
        setIn('cta-2108', cb['2.1.08'] ?? 0);
        setIn('cta-2110', cb['2.1.10'] ?? 0);

        // 3. Patrimonio
        setIn('cta-3101', cb['3.1.01'] ?? 0);
        setIn('cta-3102', sim.utilidades_acumuladas ?? cb['3.1.02'] ?? 0);

        // 4. Resultados (Ingresos, Costos, Gastos)
        setIn('cta-4101', cr['4.1.01'] ?? 0);
        setIn('cta-4102', cr['4.1.02'] ?? 0);
        setIn('cta-5101', cr['5.1.01'] ?? 0);

        setIn('cta-6101', cr['6.1.01'] ?? 0);
        setIn('cta-6102', cr['6.1.02'] ?? 0);
        setIn('cta-6103', cr['6.1.03'] ?? 0);
        setIn('cta-6104', cr['6.1.04'] ?? 0);
        setIn('cta-6105', cr['6.1.05'] ?? 0);
        setIn('cta-6106', cr['6.1.06'] ?? 0);
        setIn('cta-6107', cr['6.1.07'] ?? 0);
        setIn('cta-6108', cr['6.1.08'] ?? 0);
        setIn('cta-6109', cr['6.1.09'] ?? 0);
        setIn('cta-6110', cr['6.1.10'] ?? 0);
        setIn('cta-6111', cr['6.1.11'] ?? 0);
        setIn('cta-6112', cr['6.1.12'] ?? 0);

        // 5. Ajustes y Conciliación Fiscal
        if (sim.calculo_ir) {
            setIn('ir-gastos-no-ded', sim.calculo_ir.gastos_no_deducibles || 0);
            setIn('ir-rentas-no-grav', sim.calculo_ir.ingresos_no_gravables || 0);
        }

        // 6. Liquidación y Acreditamientos
        if (sim.liquidacion) {
            setIn('liq-anticipos-1', sim.liquidacion.anticipos_mensuales ?? 0);
            setIn('liq-retenciones-sufridas', sim.liquidacion.retenciones_sufridas || 0);
            setIn('liq-creditos-anteriores', sim.liquidacion.creditos_fiscales_ant || 0);
        }

        // Ejecutar recálculo aritmético oficial
        recalcularFormularioCuentas();

        if (mostrarNotif && typeof mostrarNotificacion === 'function') {
            mostrarNotificacion(`Formulario 106 cargado con las cuentas de Jehová Jireh (Ejercicio ${anioFiscalSeleccionado}).`, 'success');
        }
    } catch (err) {
        console.error('Error fiscal:', err);
        if (typeof mostrarNotificacion === 'function') {
            mostrarNotificacion(`Error al cargar datos fiscales: ${err.message}`, 'error');
        }
    } finally {
        if (loadingState) loadingState.style.display = 'none';
    }
}

/**
 * Recalcula matemáticamente las sumas de subtotales, totales y cuadre de Balance por cuentas
 */
function recalcularFormularioCuentas() {
    const val = (id) => {
        const el = document.getElementById(id);
        if (!el) return 0.0;
        const clean = String(el.value).replace(/,/g, '').trim();
        return parseFloat(clean) || 0.0;
    };

    const setR = (id, monto) => {
        const el = document.getElementById(id);
        if (el) el.value = fmt(monto);
    };

    // =========================================================================
    // 1. ACTIVOS
    // =========================================================================
    const c1101 = val('cta-1101'); // Caja
    const c1102 = val('cta-1102'); // Bancos
    const c1103 = val('cta-1103'); // Clientes
    const c1104 = val('cta-1104'); // Inventarios
    const c1105 = val('cta-1105'); // IVA Acreditable

    // Renglón 6: Total Activo Circulante (1 + 2 + 3 + 4 + 5)
    const totActCirc = round2(c1101 + c1102 + c1103 + c1104 + c1105);
    setR('tot-act-circ', totActCirc);

    const c1201 = val('cta-1201'); // Mobiliario
    const c1202 = val('cta-1202'); // Cómputo
    const c1203 = Math.abs(val('cta-1203')); // Depreciación Acumulada

    // Renglón 10: Total Activos Mobiliarios (7 + 8 - 9)
    const totActFijo = round2(c1201 + c1202 - c1203);
    setR('tot-act-fijo', totActFijo);

    const otrosAct = val('cta-otros-act'); // Otros activos inmobiliarios / diferidos

    // Renglón 12: Total Activos (6 + 10 + 11)
    const totActivos = round2(totActCirc + totActFijo + otrosAct);
    setR('tot-activos', totActivos);

    // =========================================================================
    // 2. PASIVOS
    // =========================================================================
    const c2101 = val('cta-2101'); // Proveedores
    const c2102 = val('cta-2102'); // Doc por pagar
    const c2103 = val('cta-2103'); // IVA por pagar
    const c2104 = val('cta-2104'); // Sueldos por pagar
    const c2105 = val('cta-2105'); // Servicios básicos por pagar
    const c2106 = val('cta-2106'); // Ret. INSS
    const c2107 = val('cta-2107'); // Ret. IR
    const c2108 = val('cta-2108'); // Provisiones sociales
    const c2110 = val('cta-2110'); // INATEC

    // Renglón 22: Total Pasivos (suma renglones 13 al 21)
    const totPasivos = round2(c2101 + c2102 + c2103 + c2104 + c2105 + c2106 + c2107 + c2108 + c2110);
    setR('tot-pasivos', totPasivos);

    // =========================================================================
    // 3. ESTADO DE RESULTADOS
    // =========================================================================
    const c4101 = val('cta-4101'); // Ventas repuestos
    const c4102 = val('cta-4102'); // Servicios taller

    // Renglón 32: Total Ingresos Brutos (30 + 31)
    const totIngresos = round2(c4101 + c4102);
    setR('tot-ingresos', totIngresos);

    const c5101 = val('cta-5101'); // Costo de ventas

    // Renglón 34: Utilidad Bruta Contable (32 - 33)
    const totUtilBruta = round2(totIngresos - c5101);
    setR('tot-util-bruta', totUtilBruta);

    // Gastos Operativos (Renglones 35 al 46)
    const c6101 = val('cta-6101'); // Sueldos
    const c6102 = val('cta-6102'); // Alquiler
    const c6103 = val('cta-6103'); // Energía
    const c6104 = val('cta-6104'); // Agua
    const c6105 = val('cta-6105'); // Internet
    const c6106 = val('cta-6106'); // Publicidad
    const c6107 = val('cta-6107'); // Mantenimiento
    const c6108 = val('cta-6108'); // Papelería
    const c6109 = val('cta-6109'); // Depreciación período
    const c6110 = val('cta-6110'); // Comisiones bancarias
    const c6111 = val('cta-6111'); // Cargas patronales
    const c6112 = val('cta-6112'); // Prestaciones sociales

    // Renglón 47: Total Gastos Deducibles de Operación
    const totGastosOp = round2(c6101 + c6102 + c6103 + c6104 + c6105 + c6106 + c6107 + c6108 + c6109 + c6110 + c6111 + c6112);
    setR('tot-gastos-op', totGastosOp);

    // Renglón 48: Utilidad Neta Contable del Ejercicio (34 - 47)
    const totUtilNeta = round2(totUtilBruta - totGastosOp);
    setR('tot-util-neta', totUtilNeta);

    // =========================================================================
    // 4. PATRIMONIO NETO
    // =========================================================================
    const c3101 = val('cta-3101'); // Capital
    const c3102 = val('cta-3102'); // Utilidades acumuladas
    setR('cta-util-ejercicio', totUtilNeta); // Renglón 25: Utilidad del ejercicio

    // Renglón 26: Total Patrimonio (23 + 24 + 25)
    const totPatrimonio = round2(c3101 + c3102 + totUtilNeta);
    setR('tot-patrimonio', totPatrimonio);

    // Renglón 27: Total Pasivo y Patrimonio (22 + 26)
    const totPasivoPatrimonio = round2(totPasivos + totPatrimonio);
    setR('tot-pasivo-patrimonio', totPasivoPatrimonio);

    // Verificación de Cuadre
    const difCuadre = round2(totActivos - totPasivoPatrimonio);
    setVal('lbl-cta-cuadre-activos', `C$ ${fmt(totActivos)}`);
    setVal('lbl-cta-cuadre-pasivos', `C$ ${fmt(totPasivos)}`);
    setVal('lbl-cta-cuadre-patrimonio', `C$ ${fmt(totPatrimonio)}`);

    const lblCuadre = document.getElementById('lbl-cta-cuadre-estado');
    if (lblCuadre) {
        if (Math.abs(difCuadre) < 0.05) {
            lblCuadre.innerHTML = '<i class="ph-bold ph-check-circle"></i> Balance Cuadrado: Diferencia C$ 0.00 (Activo = Pasivo + Capital)';
            lblCuadre.style.color = '#16a34a';
        } else {
            lblCuadre.innerHTML = `<i class="ph-bold ph-warning-circle"></i> Descuadre en Balance: C$ ${fmt(difCuadre)}`;
            lblCuadre.style.color = '#dc2626';
        }
    }

    // =========================================================================
    // 5. CÁLCULO DEL IR (CONCILIACIÓN FISCAL LEY 822)
    // =========================================================================
    setR('ir-util-contable', totUtilNeta); // Renglón 49
    const irGastosNoDed = val('ir-gastos-no-ded'); // Renglón 50
    const irRentasNoGrav = val('ir-rentas-no-grav'); // Renglón 51

    // Renglón 52: Renta Neta Gravable (49 + 50 - 51)
    const rentaGravable = round2(Math.max(0, totUtilNeta + irGastosNoDed - irRentasNoGrav));
    setR('ir-renta-gravable', rentaGravable);

    // Renglón 53: IR 30%
    const tasaIr = tasaIrAnual(totIngresos, rentaGravable);
    const ir30 = round2(rentaGravable * tasaIr / 100);
    setR('ir-calculado-30', ir30);

    // Renglón 54: PMD 1% sobre Ingresos Brutos (R32)
    const pmd1 = round2(Math.max(0, totIngresos) * 0.01);
    setR('ir-pmd-1', pmd1);

    // Renglón 55: IR Determinado Oficial (El mayor entre 53 y 54)
    const irDeterminado = round2(Math.max(ir30, pmd1));
    setR('ir-determinado', irDeterminado);

    const lblMetodo = document.getElementById('ir-lbl-metodo-cta');
    if (lblMetodo) {
        if (ir30 >= pmd1) {
            lblMetodo.textContent = `Aplica IR ${tasaIr}% sobre Renta Neta (Art. 52 Ley 822)`;
        } else {
            lblMetodo.textContent = 'Aplica Pago Mínimo Definitivo 1% sobre Ingresos Brutos (Art. 59 Ley 822)';
        }
    }

    // =========================================================================
    // 6. LIQUIDACIÓN DEL IMPUESTO
    // =========================================================================
    setR('liq-ir-determinado', irDeterminado); // Renglón 56
    const anticipos = val('liq-anticipos-1'); // Renglón 57
    const retenciones = val('liq-retenciones-sufridas'); // Renglón 58
    const creditosAnt = val('liq-creditos-anteriores'); // Renglón 59

    // Renglón 60: Total Acreditamientos
    const totAcred = round2(anticipos + retenciones + creditosAnt);
    setR('liq-total-acreditamientos', totAcred);

    let saldoPagar = 0.0;
    let saldoFavor = 0.0;

    if (irDeterminado >= totAcred) {
        saldoPagar = round2(irDeterminado - totAcred);
        saldoFavor = 0.0;
    } else {
        saldoPagar = 0.0;
        saldoFavor = round2(totAcred - irDeterminado);
    }

    setR('liq-saldo-pagar', saldoPagar); // Renglón 61
    setR('liq-saldo-favor', saldoFavor); // Renglón 62

    // =========================================================================
    // 7. SINCRONIZAR CON LA VISTA RESUMEN (IMAGEN 1)
    // =========================================================================
    setVal('kpi-res-activos', `C$ ${fmt(totActivos)}`);
    setVal('kpi-res-pasivos', `C$ ${fmt(totPasivos)}`);
    setVal('kpi-res-patrimonio', `C$ ${fmt(totPatrimonio)}`);
    
    const kpiCuadre = document.getElementById('kpi-res-cuadre');
    if (kpiCuadre) {
        if (Math.abs(difCuadre) < 0.05) {
            kpiCuadre.textContent = 'Cuadrado ✓';
            kpiCuadre.style.color = '#16a34a';
        } else {
            kpiCuadre.textContent = `Descuadre: C$ ${fmt(difCuadre)}`;
            kpiCuadre.style.color = '#dc2626';
        }
    }

    setVal('kpi-res-ingresos', `C$ ${fmt(totIngresos)}`);
    setVal('kpi-res-costos', `C$ ${fmt(c5101)}`);
    setVal('kpi-res-gastos', `C$ ${fmt(totGastosOp)}`);
    setVal('kpi-res-utilidad', `C$ ${fmt(totUtilNeta)}`);
    setVal('kpi-res-renta-neta', `C$ ${fmt(rentaGravable)}`);
    setVal('kpi-res-ir30', `C$ ${fmt(ir30)}`);
    setVal('kpi-res-pmd1', `C$ ${fmt(pmd1)}`);
    setVal('kpi-res-ir-determinado', `C$ ${fmt(irDeterminado)}`);
    setVal('kpi-res-liq-irdet', `C$ ${fmt(irDeterminado)}`);
    setVal('kpi-res-acreditamientos', `- C$ ${fmt(totAcred)}`);
    setVal('kpi-res-saldo-pagar', `C$ ${fmt(saldoPagar)}`);
    setVal('kpi-res-saldo-favor', `C$ ${fmt(saldoFavor)}`);

    const cardPagar = document.getElementById('card-saldo-final-pagar');
    const cardFavor = document.getElementById('card-saldo-final-favor');
    if (cardPagar && cardFavor) {
        if (saldoPagar > 0 || (saldoPagar === 0 && saldoFavor === 0)) {
            cardPagar.style.display = 'block';
            cardFavor.style.display = 'none';
        } else {
            cardPagar.style.display = 'none';
            cardFavor.style.display = 'block';
        }
    }

}

/**
 * Control de vistas (Modo Cuentas vs Modo Resumen)
 */
function activarModoCuentas() {
    const vCta = document.getElementById('dgi-vista-cuentas');
    const vRes = document.getElementById('dgi-vista-resumen');

    const btnCta = document.getElementById('btn-mode-cuentas');
    const btnRes = document.getElementById('btn-mode-resumen');

    if (vCta) vCta.style.display = 'block';
    if (vRes) vRes.style.display = 'none';

    if (btnCta) btnCta.classList.add('active');
    if (btnRes) btnRes.classList.remove('active');

    recalcularFormularioCuentas();
}

function activarModoDGI() {
    // Redirige al modo principal por compatibilidad
    activarModoCuentas();
}

function activarModoResumen() {
    recalcularFormularioCuentas();

    const vCta = document.getElementById('dgi-vista-cuentas');
    const vRes = document.getElementById('dgi-vista-resumen');

    const btnCta = document.getElementById('btn-mode-cuentas');
    const btnRes = document.getElementById('btn-mode-resumen');

    if (vCta) vCta.style.display = 'none';
    if (vRes) vRes.style.display = 'block';

    if (btnCta) btnCta.classList.remove('active');
    if (btnRes) btnRes.classList.add('active');
}

function toggleTipoDeclaracionCta() {
    const radioSust = document.getElementById('dgi-tipo-sust-cta');
    const inputNumSust = document.getElementById('dgi-num-sustituir-cta');
    const lblTipoRes = document.getElementById('vet-resumen-tipo-decl');
    if (radioSust && radioSust.checked) {
        if (inputNumSust) inputNumSust.style.display = 'inline-block';
        if (lblTipoRes) lblTipoRes.textContent = 'Sustitutiva';
    } else {
        if (inputNumSust) inputNumSust.style.display = 'none';
        if (lblTipoRes) lblTipoRes.textContent = 'Original';
    }
}

/**
 * Pestañas auxiliares del módulo fiscal
 */
function switchFiscalTab(tabName, btn) {
    const tabs = ['vet', 'acreditamientos', 'ajustes', 'historial'];
    tabs.forEach(t => {
        const pane = document.getElementById(`fiscal-view-${t}`);
        if (pane) pane.style.display = (t === tabName) ? 'block' : 'none';
    });
    document.querySelectorAll('.dgi-nav-tab-btn').forEach(b => b.classList.remove('active'));
    if (btn) btn.classList.add('active');

    if (tabName === 'acreditamientos') cargarAcreditamientos();
    if (tabName === 'ajustes') cargarAjustesFiscales();
    if (tabName === 'historial') cargarHistorialDeclaraciones();
}

/**
 * Recopila todos los datos del formulario para guardar en backend
 */
function recopilarPayloadSimulacion() {
    const val = (id) => {
        const el = document.getElementById(id);
        if (!el) return 0.0;
        const clean = String(el.value).replace(/,/g, '').trim();
        return parseFloat(clean) || 0.0;
    };

    const c1101 = val('cta-1101');
    const c1102 = val('cta-1102');
    const c1103 = val('cta-1103');
    const c1104 = val('cta-1104');
    const c1105 = val('cta-1105');
    const totActCirc = val('tot-act-circ');

    const c1201 = val('cta-1201');
    const c1202 = val('cta-1202');
    const c1203 = val('cta-1203');
    const totActFijo = val('tot-act-fijo');
    const otrosAct = val('cta-otros-act');
    const totActivos = val('tot-activos');

    const c2101 = val('cta-2101');
    const c2102 = val('cta-2102');
    const c2103 = val('cta-2103');
    const c2104 = val('cta-2104');
    const c2105 = val('cta-2105');
    const c2106 = val('cta-2106');
    const c2107 = val('cta-2107');
    const c2108 = val('cta-2108');
    const c2110 = val('cta-2110');
    const totPasivos = val('tot-pasivos');

    const c3101 = val('cta-3101');
    const c3102 = val('cta-3102');
    const totPatrimonio = val('tot-patrimonio');

    const c4101 = val('cta-4101');
    const c4102 = val('cta-4102');
    const totIngresos = val('tot-ingresos');
    const c5101 = val('cta-5101');
    const totUtilBruta = val('tot-util-bruta');

    const totGastosOp = val('tot-gastos-op');
    const totUtilNeta = val('tot-util-neta');

    const rentaGravable = val('ir-renta-gravable');
    const ir30 = val('ir-calculado-30');
    const pmd1 = val('ir-pmd-1');
    const irDeterminado = val('ir-determinado');

    const totAcred = val('liq-total-acreditamientos');
    const saldoPagar = val('liq-saldo-pagar');
    const saldoFavor = val('liq-saldo-favor');

    const renglonesBalance = [
        { renglon: 1, descripcion: "Efectivo en caja y bancos", importe: round2(c1101 + c1102), tipo: "Contable" },
        { renglon: 2, descripcion: "Cuentas y documentos por cobrar", importe: c1103, tipo: "Contable" },
        { renglon: 3, descripcion: "Inventarios", importe: c1104, tipo: "Contable" },
        { renglon: 4, descripcion: "Terrenos", importe: 0.0, tipo: "Manual" },
        { renglon: 5, descripcion: "Edificios", importe: 0.0, tipo: "Manual" },
        { renglon: 6, descripcion: "Otros Activos Inmobiliarios", importe: otrosAct, tipo: "Manual" },
        { renglon: 7, descripcion: "Total Activo Inmobiliario (Renglones 4+5+6)", importe: otrosAct, tipo: "Calculado" },
        { renglon: 8, descripcion: "Parque Vehicular", importe: 0.0, tipo: "Manual" },
        { renglon: 9, descripcion: "Otros Bienes Mobiliarios", importe: totActFijo, tipo: "Contable" },
        { renglon: 10, descripcion: "Total Activos Mobiliarios (Renglón 8+9)", importe: totActFijo, tipo: "Calculado" },
        { renglon: 11, descripcion: "Otros activos", importe: c1105, tipo: "Contable" },
        { renglon: 12, descripcion: "Total Activos (suma 1+2+3+7+10+11)", importe: totActivos, tipo: "Calculado", destacado: true },
        { renglon: 13, descripcion: "Cuentas y documentos por pagar", importe: round2(c2101 + c2102), tipo: "Contable" },
        { renglon: 14, descripcion: "Dividendos Pagados a Residentes", importe: 0.0, tipo: "Manual" },
        { renglon: 15, descripcion: "Dividendos por Pagar a Residentes", importe: 0.0, tipo: "Manual" },
        { renglon: 16, descripcion: "Instituciones Financieras de Desarrollo", importe: 0.0, tipo: "Manual" },
        { renglon: 17, descripcion: "Resto de Instituciones Financieras", importe: 0.0, tipo: "Manual" },
        { renglon: 18, descripcion: "Casa Matriz u Otras Sucursales", importe: 0.0, tipo: "Manual" },
        { renglon: 19, descripcion: "Otros Agentes no Financieros", importe: round2(c2103 + c2104 + c2105 + c2106 + c2107 + c2108 + c2110), tipo: "Contable" },
        { renglon: 20, descripcion: "Pasivo Fijo Nacional (suma 15+16+17+18+19)", importe: round2(c2103 + c2104 + c2105 + c2106 + c2107 + c2108 + c2110), tipo: "Calculado", destacado: true },
        { renglon: 21, descripcion: "Dividendos Pagados no Residentes", importe: 0.0, tipo: "Manual" },
        { renglon: 22, descripcion: "Dividendos por pagar no Residentes", importe: 0.0, tipo: "Manual" },
        { renglon: 23, descripcion: "Instituciones Financieras Ext", importe: 0.0, tipo: "Manual" }
    ];

    const renglonesResultados = [
        { renglon: 30, descripcion: "Ventas de repuestos y accesorios", importe: c4101, tipo: "Contable" },
        { renglon: 31, descripcion: "Ingresos por servicios de taller", importe: c4102, tipo: "Contable" },
        { renglon: 32, descripcion: "Total Ingresos Brutos de Actividades Económicas", importe: totIngresos, tipo: "Calculado" },
        { renglon: 33, descripcion: "Costo de Ventas de Repuestos", importe: c5101, tipo: "Contable" },
        { renglon: 34, descripcion: "Utilidad Bruta Contable", importe: totUtilBruta, tipo: "Calculado" },
        { renglon: 35, descripcion: "Gastos de Sueldos y Salarios", importe: val('cta-6101'), tipo: "Contable" },
        { renglon: 36, descripcion: "Cargas Sociales Patronales (INSS e INATEC)", importe: val('cta-6111'), tipo: "Contable" },
        { renglon: 37, descripcion: "Prestaciones Sociales (Vacaciones y Aguinaldo)", importe: val('cta-6112'), tipo: "Contable" },
        { renglon: 38, descripcion: "Alquiler, Servicios Básicos y Mantenimiento", importe: round2(val('cta-6102') + val('cta-6103') + val('cta-6104') + val('cta-6105') + val('cta-6107')), tipo: "Contable" },
        { renglon: 39, descripcion: "Publicidad, Papelería y Depreciación", importe: round2(val('cta-6106') + val('cta-6108') + val('cta-6109')), tipo: "Contable" },
        { renglon: 40, descripcion: "Gastos Financieros y Comisiones Bancarias", importe: val('cta-6110'), tipo: "Contable" },
        { renglon: 41, descripcion: "Total Gastos Deducibles de Operación", importe: totGastosOp, tipo: "Calculado" },
        { renglon: 42, descripcion: "Utilidad Neta Contable del Ejercicio", importe: totUtilNeta, tipo: "Calculado" }
    ];

    return {
        anio: anioFiscalSeleccionado,
        balance: {
            renglones: renglonesBalance,
            total_activos: totActivos,
            total_pasivos: totPasivos,
            patrimonio_total: totPatrimonio,
            balance_cuadrado: Math.abs(totActivos - (totPasivos + totPatrimonio)) < 0.05,
            diferencia_cuadre: round2(totActivos - (totPasivos + totPatrimonio))
        },
        resultados: {
            renglones: renglonesResultados,
            total_ingresos_brutos: totIngresos,
            total_costos: c5101,
            utilidad_bruta: totUtilBruta,
            total_gastos: totGastosOp,
            utilidad_neta_contable: totUtilNeta
        },
        calculo_ir: {
            utilidad_neta_contable: totUtilNeta,
            gastos_no_deducibles: val('ir-gastos-no-ded'),
            ingresos_no_gravables: val('ir-rentas-no-grav'),
            renta_neta_gravable: rentaGravable,
            ir_calculado_30: ir30,
            pmd_calculado_1: pmd1,
            ir_determinado: irDeterminado,
            metodo_aplicado: ir30 >= pmd1 ? `IR por Actividades Económicas (${tasaIrAnual(totIngresos, rentaGravable)}%)` : "Pago Mínimo Definitivo - PMD (1% de Ingresos Brutos)"
        },
        liquidacion: {
            ir_determinado: irDeterminado,
            anticipos_mensuales: val('liq-anticipos-1'),
            retenciones_sufridas: val('liq-retenciones-sufridas'),
            creditos_fiscales_ant: val('liq-creditos-anteriores'),
            total_acreditamientos: totAcred,
            saldo_a_pagar: saldoPagar,
            saldo_a_favor: saldoFavor
        }
    };
}

/**
 * Guarda el formulario como Borrador en base de datos
 */
async function guardarDeclaracionBorrador() {
    if (!simulacionFiscalActual) {
        alert('Espere a que cargue Contabilidad antes de guardar.');
        return;
    }
    recalcularFormularioCuentas();
    const payload = recopilarPayloadSimulacion();

    try {
        const res = await fetch('/api/fiscal/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ simulacion: payload, es_aprobada: false })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al guardar el borrador.');

        declaracionGuardadaId = data.declaracion_id;
        if (typeof mostrarNotificacion === 'function') {
            mostrarNotificacion(data.mensaje || 'Borrador de Declaración Anual IR guardado exitosamente.', 'success');
        } else {
            alert(data.mensaje || 'Borrador guardado exitosamente.');
        }
    } catch (err) {
        console.error('Error guardando borrador:', err);
        if (typeof mostrarNotificacion === 'function') {
            mostrarNotificacion(err.message, 'error');
        } else {
            alert(err.message);
        }
    }
}

/**
 * Abre el modal para registrar confirmación oficial VET
 */
function abrirModalPresentacion() {
    recalcularFormularioCuentas();
    const saldoPagar = parseFloat(String(document.getElementById('liq-saldo-pagar')?.value || '0').replace(/,/g, '')) || 0.0;

    const inputMonto = document.getElementById('pres-monto');
    const inputFecha = document.getElementById('pres-fecha');
    if (inputMonto) inputMonto.value = saldoPagar.toFixed(2);
    if (inputFecha) inputFecha.value = new Date().toISOString().split('T')[0];

    const modal = document.getElementById('modal-presentacion-dgi');
    if (modal) modal.classList.add('active');
}

/**
 * Registra la presentación oficial en VET y aprueba la declaración
 */
async function guardarPresentacionDGI(e) {
    if (e) e.preventDefault();
    if (!simulacionFiscalActual) {
        alert('Espere a que cargue Contabilidad antes de guardar.');
        return;
    }
    recalcularFormularioCuentas();
    const payload = recopilarPayloadSimulacion();

    const ref = document.getElementById('pres-referencia')?.value.trim();
    const fecha = document.getElementById('pres-fecha')?.value;
    const monto = parseFloat(document.getElementById('pres-monto')?.value || 0);
    const banco = document.getElementById('pres-banco')?.value;
    const medio = document.getElementById('pres-medio-pago')?.value;
    const obs = document.getElementById('pres-observaciones')?.value.trim();

    try {
        const resPago = await fetch('/api/fiscal/presentar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                simulacion: payload,
                numero_referencia_dgi: ref,
                fecha_evento: fecha,
                banco_caja: banco,
                medio_pago: medio,
                importe_pagado: monto,
                observaciones: obs
            })
        });
        const dataPago = await resPago.json();
        if (!resPago.ok) throw new Error(dataPago.error || 'Error al registrar presentación en VET.');

        closeModal('modal-presentacion-dgi');
        if (typeof mostrarNotificacion === 'function') {
            mostrarNotificacion('Constancia de presentación ante la DGI registrada en el sistema.', 'success');
        } else {
            alert('Constancia de presentación ante la DGI registrada en el sistema.');
        }
        cargarHistorialDeclaraciones();
    } catch (err) {
        console.error('Error presentando:', err);
        if (typeof mostrarNotificacion === 'function') {
            mostrarNotificacion(err.message, 'error');
        } else {
            alert(err.message);
        }
    }
}

/**
 * Pestaña 2: Cargar Acreditamientos
 */
async function cargarAcreditamientos() {
    const tbody = document.getElementById('tbody-acreditamientos');
    if (!tbody) return;

    try {
        const res = await fetch(`/api/fiscal/acreditamientos/${anioFiscalSeleccionado}`);
        const data = await res.json();
        const lista = data.acreditamientos || [];

        if (lista.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted" style="padding: 2rem;">No hay constancias registradas para este año fiscal.</td></tr>';
            return;
        }

        tbody.innerHTML = lista.map(a => `
            <tr>
                <td><span class="badge ${a.tipo === 'ANTICIPO_PAGADO' ? 'badge-primary' : (a.tipo === 'CREDITO_FISCAL' ? 'badge-info' : 'badge-success')}">${a.tipo}</span></td>
                <td><strong>${a.numero_referencia}</strong></td>
                <td>${a.fecha || '--'}</td>
                <td>${a.agente_retenedor_nombre || 'N/A'}</td>
                <td style="text-align: right; font-family: monospace;">C$ ${fmt(a.monto_base)}</td>
                <td style="text-align: center;">${a.porcentaje_aplicado ? a.porcentaje_aplicado + '%' : '--'}</td>
                <td style="text-align: right; font-weight: bold; color: #005fa8; font-family: monospace;">C$ ${fmt(a.importe_total)}</td>
                <td style="text-align: center;">
                    <button class="btn btn-outline btn-sm" onclick="eliminarAcreditamientoFiscal(${a.id})" title="Eliminar"><i class="ph-bold ph-trash" style="color: #dc2626;"></i></button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error cargando acreditamientos:', err);
    }
}

function actualizarCamposAcreditamiento() {
    const tipo = document.getElementById('acred-tipo')?.value || 'RETENCION_SUFRIDA';
    const groupTasa = document.getElementById('group-tasa');
    const retenedorLabel = document.getElementById('acred-retenedor-label');
    const retenedorInput = document.getElementById('acred-retenedor-nombre');
    const baseInput = document.getElementById('acred-base');
    const baseLabel = document.getElementById('acred-base-label');
    const importeInput = document.getElementById('acred-importe');
    const notaSpan = document.getElementById('acred-calculo-nota');
    const infoBox = document.getElementById('acred-info-box');
    const pctSelect = document.getElementById('acred-porcentaje-select');
    const pctCustom = document.getElementById('acred-porcentaje-custom');

    if (pctCustom) pctCustom.style.display = 'none';

    if (tipo === 'RETENCION_SUFRIDA') {
        if (groupTasa) groupTasa.style.display = 'block';
        if (retenedorLabel) retenedorLabel.textContent = 'Agente Retenedor (Cliente o Banco):';
        if (retenedorInput) {
            retenedorInput.placeholder = 'Ej: Distribuidora Central S.A. o BAC';
            if (retenedorInput.value === 'DGI - Administración de Rentas' || retenedorInput.value === 'DGI - Declaración Anual IR Anterior') {
                retenedorInput.value = '';
            }
        }
        if (baseLabel) baseLabel.textContent = 'Base Gravable / Subtotal Factura (C$):';
        if (baseInput) {
            baseInput.disabled = false;
            baseInput.style.opacity = '1';
            baseInput.style.cursor = 'default';
        }
        if (pctSelect) pctSelect.value = '2.00';
        if (notaSpan) notaSpan.textContent = 'Cálculo sugerido: Base × 2% según Art. 132 LCT (puede ajustar los centavos si la constancia física difiere).';
        if (infoBox) infoBox.style.display = 'flex';
    } else if (tipo === 'ANTICIPO_PAGADO') {
        if (groupTasa) groupTasa.style.display = 'none';
        if (retenedorLabel) retenedorLabel.textContent = 'Administración Tributaria:';
        if (retenedorInput && !retenedorInput.value) {
            retenedorInput.value = 'DGI - Administración de Rentas';
        }
        if (baseLabel) baseLabel.textContent = 'Ingresos Brutos del Mes (C$):';
        if (baseInput) {
            baseInput.disabled = false;
            baseInput.style.opacity = '1';
            baseInput.style.cursor = 'default';
        }
        if (notaSpan) notaSpan.textContent = 'Cálculo de ley: Ingresos Brutos × 1% de Anticipo Mensual PMD (Art. 61 LCT).';
        if (infoBox) infoBox.style.display = 'flex';
    } else if (tipo === 'CREDITO_FISCAL') {
        if (groupTasa) groupTasa.style.display = 'none';
        if (retenedorLabel) retenedorLabel.textContent = 'Origen del Crédito Fiscal:';
        if (retenedorInput && !retenedorInput.value) {
            retenedorInput.value = 'DGI - Saldo a Favor Declaración Anterior';
        }
        if (baseLabel) baseLabel.textContent = 'Base Gravable (No aplica):';
        if (baseInput) {
            baseInput.value = '0.00';
            baseInput.disabled = true;
            baseInput.style.opacity = '0.5';
            baseInput.style.cursor = 'not-allowed';
        }
        if (notaSpan) notaSpan.textContent = 'Ingrese directamente el saldo a favor aprobado por DGI en el importe acreditable.';
        if (infoBox) infoBox.style.display = 'flex';
        if (importeInput) importeInput.focus();
    }
    calcularImporteRetenido();
}
window.actualizarCamposAcreditamiento = actualizarCamposAcreditamiento;

function actualizarTasaAcreditamiento() {
    const pctSelect = document.getElementById('acred-porcentaje-select');
    const pctCustom = document.getElementById('acred-porcentaje-custom');
    const notaSpan = document.getElementById('acred-calculo-nota');
    if (pctSelect && pctCustom) {
        if (pctSelect.value === 'custom') {
            pctCustom.style.display = 'block';
            pctCustom.focus();
            if (notaSpan) notaSpan.textContent = 'Porcentaje personalizado ingresado por el usuario.';
        } else {
            pctCustom.style.display = 'none';
            if (notaSpan) {
                if (pctSelect.value === '2.00') {
                    notaSpan.textContent = 'Cálculo sugerido: Base × 2% según Art. 132 LCT (Venta de Repuestos y Servicios).';
                } else if (pctSelect.value === '1.50') {
                    notaSpan.textContent = 'Cálculo sugerido: Base × 1.5% (Retención por cobros con tarjeta en POS).';
                } else if (pctSelect.value === '10.00') {
                    notaSpan.textContent = 'Cálculo sugerido: Base × 10% (Servicios Profesionales / Honorarios).';
                }
            }
        }
    }
    calcularImporteRetenido();
}
window.actualizarTasaAcreditamiento = actualizarTasaAcreditamiento;

function calcularImporteRetenido() {
    const tipo = document.getElementById('acred-tipo')?.value || 'RETENCION_SUFRIDA';
    const baseInput = document.getElementById('acred-base');
    const importeInput = document.getElementById('acred-importe');
    if (!baseInput || !importeInput) return;

    if (tipo === 'CREDITO_FISCAL') {
        return;
    }

    const base = parseFloat(baseInput.value) || 0;
    let pct = 0;

    if (tipo === 'ANTICIPO_PAGADO') {
        pct = 1.0;
    } else {
        const pctSelect = document.getElementById('acred-porcentaje-select');
        if (pctSelect && pctSelect.value === 'custom') {
            pct = parseFloat(document.getElementById('acred-porcentaje-custom')?.value) || 0;
        } else if (pctSelect) {
            pct = parseFloat(pctSelect.value) || 2.0;
        } else {
            pct = 2.0;
        }
    }

    if (base > 0 && pct > 0) {
        const calc = Math.round(base * (pct / 100.0) * 100) / 100;
        importeInput.value = calc.toFixed(2);
    } else if (base <= 0) {
        importeInput.value = '0.00';
    }
}
window.calcularImporteRetenido = calcularImporteRetenido;

function abrirModalAcreditamiento() {
    const f = document.getElementById('form-acreditamiento');
    if (f) f.reset();
    const inF = document.getElementById('acred-fecha');
    if (inF) inF.value = new Date().toISOString().split('T')[0];
    const tipoSel = document.getElementById('acred-tipo');
    if (tipoSel) tipoSel.value = 'RETENCION_SUFRIDA';
    actualizarCamposAcreditamiento();
    const modal = document.getElementById('modal-acreditamiento');
    if (modal) modal.classList.add('active');
}

async function guardarAcreditamientoFiscal(e) {
    if (e) e.preventDefault();
    const tipo = document.getElementById('acred-tipo').value;
    const ref = document.getElementById('acred-referencia').value.trim();
    const base = parseFloat(document.getElementById('acred-base').value || 0);
    const importe = parseFloat(document.getElementById('acred-importe').value || 0);

    let pct = 0;
    if (tipo === 'ANTICIPO_PAGADO') {
        pct = 1.0;
    } else if (tipo === 'RETENCION_SUFRIDA') {
        const pctSelect = document.getElementById('acred-porcentaje-select');
        pct = (pctSelect && pctSelect.value === 'custom')
            ? (parseFloat(document.getElementById('acred-porcentaje-custom')?.value) || 0)
            : (parseFloat(pctSelect?.value) || 2.0);
    }

    let concepto = '';
    if (tipo === 'RETENCION_SUFRIDA') {
        concepto = `Retención IR ${pct}% Ref: ${ref}`;
    } else if (tipo === 'ANTICIPO_PAGADO') {
        concepto = `Anticipo IR 1% Ref: ${ref}`;
    } else {
        concepto = `Saldo a Favor Ref: ${ref}`;
    }

    const payload = {
        ejercicio_fiscal: anioFiscalSeleccionado,
        tipo: tipo,
        concepto: concepto,
        numero_referencia: ref,
        fecha: document.getElementById('acred-fecha').value,
        agente_retenedor_nombre: document.getElementById('acred-retenedor-nombre').value.trim(),
        monto_base: base,
        porcentaje_aplicado: pct,
        importe_total: importe
    };

    try {
        const res = await fetch('/api/fiscal/acreditamiento', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al guardar acreditamiento.');
        closeModal('modal-acreditamiento');
        if (typeof mostrarNotificacion === 'function') mostrarNotificacion('Constancia registrada exitosamente.', 'success');
        cargarAcreditamientos();
        cargarSimulacionFiscal(false);
    } catch (err) {
        alert(err.message);
    }
}

async function eliminarAcreditamientoFiscal(id) {
    if (!confirm('¿Desea eliminar esta constancia de acreditamiento?')) return;
    try {
        const res = await fetch(`/api/fiscal/acreditamiento/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al eliminar.');
        cargarAcreditamientos();
        cargarSimulacionFiscal(false);
    } catch (err) {
        alert(err.message);
    }
}

/**
 * Pestaña 3: Cargar Ajustes Fiscales
 */
async function cargarAjustesFiscales() {
    const tbody = document.getElementById('tbody-ajustes-fiscales');
    if (!tbody) return;

    try {
        const res = await fetch(`/api/fiscal/ajustes/${anioFiscalSeleccionado}`);
        const data = await res.json();
        const lista = data.ajustes || [];

        if (lista.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding: 2rem;">Sin ajustes fiscales manuales registrados.</td></tr>';
            return;
        }

        tbody.innerHTML = lista.map(a => `
            <tr>
                <td><strong>${a.concepto}</strong></td>
                <td><span class="badge ${a.tipo_ajuste.includes('No Deducible') ? 'badge-warning' : 'badge-info'}">${a.tipo_ajuste}</span></td>
                <td><span style="font-weight: bold; color: ${a.efecto.includes('Aumenta') ? '#dc2626' : '#16a34a'};">${a.efecto}</span></td>
                <td>${a.referencia_normativa || 'Ley 822'}</td>
                <td style="text-align: right; font-weight: bold; font-family: monospace;">C$ ${fmt(a.importe)}</td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error cargando ajustes:', err);
    }
}

function abrirModalAjusteFiscal() {
    const f = document.getElementById('form-ajuste-fiscal');
    if (f) f.reset();
    const modal = document.getElementById('modal-ajuste-fiscal');
    if (modal) modal.classList.add('active');
}

async function guardarAjusteFiscal(e) {
    if (e) e.preventDefault();
    const tipo = document.getElementById('ajuste-tipo').value;
    const payload = {
        ejercicio_fiscal: anioFiscalSeleccionado,
        concepto: document.getElementById('ajuste-concepto').value.trim(),
        tipo_ajuste: tipo,
        efecto: tipo.includes('No Deducible') ? 'Aumenta Renta' : 'Disminuye Renta',
        importe: parseFloat(document.getElementById('ajuste-importe').value || 0),
        referencia_normativa: document.getElementById('ajuste-normativa').value.trim(),
        justificacion: document.getElementById('ajuste-justificacion').value.trim()
    };

    try {
        const res = await fetch('/api/fiscal/ajuste', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al aplicar ajuste.');
        closeModal('modal-ajuste-fiscal');
        if (typeof mostrarNotificacion === 'function') mostrarNotificacion('Ajuste fiscal aplicado.', 'success');
        cargarAjustesFiscales();
        cargarSimulacionFiscal(false);
    } catch (err) {
        alert(err.message);
    }
}

/**
 * Pestaña 4: Historial de Declaraciones
 */
async function cargarHistorialDeclaraciones() {
    const tbody = document.getElementById('tbody-historial-fiscal');
    if (!tbody) return;

    try {
        const res = await fetch('/api/fiscal/historial');
        const data = await res.json();
        const lista = data.declaraciones || [];

        if (lista.length === 0) {
            tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted" style="padding: 2rem;">No hay declaraciones guardadas o presentadas en el historial.</td></tr>';
            return;
        }

        tbody.innerHTML = lista.map(d => {
            const rawFecha = d.created_at || d.fecha_creacion || '';
            let fechaStr = '--';
            if (rawFecha) {
                const s = rawFecha.replace('T', ' ');
                const [fDate, fTime] = s.split(' ');
                const ymd = fDate.split('-');
                if (ymd.length === 3) {
                    const dma = `${ymd[2]}/${ymd[1]}/${ymd[0]}`;
                    const hhmm = fTime ? fTime.slice(0, 5) : '';
                    fechaStr = hhmm ? `${dma} <span style="font-size:0.75rem; opacity:0.75;">${hhmm}</span>` : dma;
                } else {
                    fechaStr = fDate;
                }
            }

            return `
            <tr>
                <td><strong>${d.ejercicio_fiscal}</strong></td>
                <td>v${d.version}</td>
                <td>${d.es_sustitutiva ? '<span class="badge badge-warning">Sustitutiva</span>' : '<span class="badge badge-primary">Original</span>'}</td>
                <td>${fechaStr}</td>
                <td><span class="badge ${d.estado === 'Aprobada' || d.estado === 'Presentada' ? 'badge-success' : 'badge-secondary'}">${d.estado}</span></td>
                <td style="text-align: right; font-family: monospace;">C$ ${fmt(d.ir_determinado)}</td>
                <td style="text-align: right; font-family: monospace; color: #16a34a;">- C$ ${fmt(d.acreditamientos !== undefined ? d.acreditamientos : (d.total_acreditamientos || 0))}</td>
                <td style="text-align: right; font-weight: bold; font-family: monospace; color: ${d.saldo_a_pagar > 0 ? '#dc2626' : '#16a34a'};">
                    C$ ${fmt(d.saldo_a_pagar > 0 ? d.saldo_a_pagar : d.saldo_a_favor)}
                </td>
                <td style="text-align: center;">
                    <div style="display: inline-flex; gap: 5px; align-items: center; justify-content: center; flex-wrap: wrap;">
                        <button type="button" class="btn btn-secondary btn-sm" style="padding: 4px 8px; font-size: 0.75rem;" onclick="imprimirDeclaracionEspecifica(${d.id})" title="Imprimir Formulario 106 de este borrador">
                            <i class="ph-bold ph-printer"></i> Imprimir
                        </button>
                        ${d.estado === 'Borrador' ? `
                            <button type="button" class="btn btn-secondary btn-sm" style="padding: 4px 8px; font-size: 0.75rem; color: #ef4444; border-color: rgba(239,68,68,0.3);" onclick="eliminarDeclaracionBorrador(${d.id})" title="Eliminar borrador">
                                <i class="ph-bold ph-trash"></i> Borrar
                            </button>
                        ` : `
                            <button type="button" class="btn btn-secondary btn-sm" disabled style="padding: 4px 8px; font-size: 0.75rem; opacity: 0.4; cursor: not-allowed;" title="Las declaraciones aprobadas/presentadas no se pueden borrar">
                                <i class="ph-bold ph-lock"></i>
                            </button>
                        `}
                    </div>
                </td>
            </tr>
            `;
        }).join('');
    } catch (err) {
        console.error('Error cargando historial:', err);
    }
}

async function eliminarDeclaracionBorrador(id) {
    let confirmacion = false;
    if (typeof Swal !== 'undefined') {
        const res = await Swal.fire({
            title: '¿Eliminar este borrador?',
            text: 'Esta acción eliminará el borrador guardado del historial. No se afectarán los movimientos contables.',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ef4444',
            cancelButtonColor: '#64748b',
            confirmButtonText: 'Sí, eliminar',
            cancelButtonText: 'Cancelar'
        });
        confirmacion = res.isConfirmed;
    } else {
        confirmacion = confirm('¿Está seguro de eliminar este borrador de declaración?');
    }
    if (!confirmacion) return;

    try {
        const res = await fetch(`/api/fiscal/declaracion/${id}`, { method: 'DELETE' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al eliminar el borrador.');
        if (typeof mostrarNotificacion === 'function') {
            mostrarNotificacion('Borrador eliminado correctamente.', 'success');
        } else if (typeof Swal !== 'undefined') {
            Swal.fire('Eliminado', 'El borrador ha sido eliminado.', 'success');
        }
        cargarHistorialDeclaraciones();
    } catch (err) {
        if (typeof Swal !== 'undefined') {
            Swal.fire('Error', err.message, 'error');
        } else {
            alert(err.message);
        }
    }
}
window.eliminarDeclaracionBorrador = eliminarDeclaracionBorrador;

async function imprimirDeclaracionEspecifica(id) {
    try {
        const res = await fetch(`/api/fiscal/declaracion/${id}`);
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al obtener la declaración.');
        const d = data.declaracion;
        if (!d) throw new Error('Declaración no encontrada.');

        const printWin = window.open('', '_blank', 'width=950,height=1050');
        if (!printWin) {
            alert('Por favor permita ventanas emergentes para imprimir.');
            return;
        }

        const renglonesBalance = (d.renglones || []).filter(r => r.seccion === 'BALANCE_GENERAL');
        const renglonesResultados = (d.renglones || []).filter(r => r.seccion === 'ESTADO_RESULTADOS');

        const rawFecha = d.created_at || d.fecha_creacion || '';
        const fechaFmt = rawFecha ? rawFecha.replace('T', ' ').slice(0, 16) : '--';

        const rowsBalanceHtml = renglonesBalance.length > 0
            ? renglonesBalance.map(r => {
                const esTotal = r.descripcion.toLowerCase().includes('total');
                return `<tr class="${esTotal ? 'total-row' : ''}">
                    <td class="text-center" style="width: 40px;">${r.renglon}</td>
                    <td>${r.cuentas ? `<code>${r.cuentas}</code> ` : ''}${r.descripcion}</td>
                    <td class="text-right" style="width: 140px;">${fmt(r.importe)}</td>
                </tr>`;
            }).join('')
            : `<tr><td colspan="3" class="text-center text-muted">Sin detalle de balance registrado.</td></tr>`;

        const rowsResultadosHtml = renglonesResultados.length > 0
            ? renglonesResultados.map(r => {
                const esTotal = r.descripcion.toLowerCase().includes('total') || r.descripcion.toLowerCase().includes('utilidad');
                return `<tr class="${esTotal ? 'total-row' : ''}">
                    <td class="text-center" style="width: 40px;">${r.renglon}</td>
                    <td>${r.cuentas ? `<code>${r.cuentas}</code> ` : ''}${r.descripcion}</td>
                    <td class="text-right" style="width: 140px;">${fmt(r.importe)}</td>
                </tr>`;
            }).join('')
            : `<tr><td colspan="3" class="text-center text-muted">Sin detalle de resultados registrado.</td></tr>`;

        const docContent = `
            <!DOCTYPE html>
            <html lang="es">
            <head>
                <meta charset="UTF-8">
                <title>Declaración Anual IR ${d.ejercicio_fiscal} - Formulario 106 DGI (#${d.id})</title>
                <style>
                    body { font-family: Arial, sans-serif; font-size: 11px; color: #000; margin: 20px; }
                    table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
                    th, td { border: 1px solid #94a3b8; padding: 4px 6px; }
                    .dgi-hdr { display: flex; justify-content: space-between; align-items: center; border: 1px solid #005fa8; padding: 10px; margin-bottom: 8px; }
                    .title-box { display: flex; border: 1px solid #005fa8; margin-bottom: 10px; }
                    .code-106 { font-size: 26px; font-weight: bold; color: #005fa8; padding: 8px 15px; border-right: 1px solid #005fa8; display: flex; align-items: center; }
                    .sec-head { background: #005fa8; color: #fff; font-weight: bold; padding: 4px 8px; text-transform: uppercase; font-size: 11px; }
                    .total-row { background: #f1f5f9; font-weight: bold; }
                    .total-row td { border-top: 2px solid #000; border-bottom: 2px solid #000; }
                    .text-right { text-align: right; }
                    .text-center { text-align: center; }
                    @media print {
                        body { margin: 10px; }
                        .no-print { display: none !important; }
                    }
                </style>
            </head>
            <body>
                ${d.observaciones?.includes('[DEMO-FISCAL]') ? '<p><strong>DEMOSTRACIÓN — Sin validez oficial.</strong></p>' : ''}
                <div class="no-print" style="margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; background: #f8fafc; padding: 8px 12px; border: 1px solid #cbd5e1; border-radius: 4px;">
                    <div><strong>Declaración #${d.id} (${d.estado})</strong> · Registrada: ${fechaFmt} · Versión: v${d.version}</div>
                    <button onclick="window.print()" style="background: #005fa8; color: #fff; border: none; padding: 6px 14px; border-radius: 4px; font-weight: bold; cursor: pointer;">
                        Imprimir Formulario
                    </button>
                </div>

                <div class="dgi-hdr">
                    <div>
                        <strong>Gobierno de Reconciliación y Unidad Nacional</strong><br>
                        <span>Ministerio de Hacienda y Crédito Público • Dirección General de Ingresos (DGI)</span>
                    </div>
                    <div style="text-align: right;">
                        <strong>Ventanilla Electrónica Tributaria (VET)</strong><br>
                        <span>Ejercicio Fiscal: <strong>${d.ejercicio_fiscal}</strong></span>
                    </div>
                </div>

                <div class="title-box">
                    <div class="code-106">106</div>
                    <div style="flex: 1; text-align: center; padding: 6px;">
                        <strong style="font-size: 14px; color: #005fa8;">DECLARACION ANUAL DEL IMPUESTO SOBRE LA RENTA (IR)</strong><br>
                        <span style="font-weight: bold;">RENTA ANUAL IR 106 · VERSIÓN ${d.version} (${d.estado.toUpperCase()})</span>
                    </div>
                    <div style="padding: 6px 12px; text-align: right; border-left: 1px solid #005fa8; font-size: 10px;">
                        <strong>Período:</strong> 12<br>
                        <strong>Tipo:</strong> ${d.es_sustitutiva ? 'Sustitutiva' : 'Original'}<br>
                        <strong>Fecha:</strong> ${fechaFmt.slice(0, 10)}
                    </div>
                </div>

                <div class="sec-head">A. DATOS GENERALES</div>
                <table>
                    <tr>
                        <td style="width: 20%; font-weight: bold;">Número RUC:</td>
                        <td style="width: 30%;">${escaparFiscal(d.negocio?.ruc || 'SIN CONFIGURAR')}</td>
                        <td style="width: 25%; font-weight: bold;">Razón Social:</td>
                        <td>Jehová Jireh Moto Repuestos y Servicios</td>
                    </tr>
                    <tr>
                        <td style="font-weight: bold;">Actividad Económica:</td>
                        <td>Comercio al por menor de repuestos y mantenimiento</td>
                        <td style="font-weight: bold;">Elaborado por:</td>
                        <td>${d.usuario_elaboro || 'Sistema'}</td>
                    </tr>
                </table>

                <div class="sec-head">B. BALANCE GENERAL (ESTADO DE SITUACIÓN FINANCIERA)</div>
                <table>
                    <thead>
                        <tr style="background: #e2e8f0;">
                            <th style="width: 40px;">No.</th>
                            <th>Cuenta / Concepto Contable</th>
                            <th class="text-right" style="width: 140px;">Importe (C$)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsBalanceHtml}
                    </tbody>
                </table>

                <div class="sec-head">D. ESTADO DE RESULTADOS</div>
                <table>
                    <thead>
                        <tr style="background: #e2e8f0;">
                            <th style="width: 40px;">No.</th>
                            <th>Concepto Económico</th>
                            <th class="text-right" style="width: 140px;">Importe (C$)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rowsResultadosHtml}
                    </tbody>
                </table>

                <div class="sec-head">E. CÁLCULO DEL IR Y F. LIQUIDACIÓN DEL IMPUESTO</div>
                <table>
                    <tr>
                        <td style="width: 70%;"><strong>Renta Neta Gravable Oficial</strong></td>
                        <td class="text-right" style="font-weight: bold; width: 30%;">C$ ${fmt(d.renta_neta_gravable)}</td>
                    </tr>
                    <tr>
                        <td>IR por Actividades Económicas (tarifa Art. 52)</td>
                        <td class="text-right">C$ ${fmt(d.ir_calculado)}</td>
                    </tr>
                    <tr>
                        <td>Pago Mínimo Definitivo (1% de Ingresos Brutos)</td>
                        <td class="text-right">C$ ${fmt(d.pago_minimo_definitivo)}</td>
                    </tr>
                    <tr class="total-row" style="background: #e0f2fe;">
                        <td><strong>56. IR DETERMINADO OFICIAL (Rige el mayor)</strong></td>
                        <td class="text-right"><strong>C$ ${fmt(d.ir_determinado)}</strong></td>
                    </tr>
                    <tr>
                        <td>60. (-) Total Pagos Anticipados y Acreditamientos</td>
                        <td class="text-right" style="color: #16a34a; font-weight: bold;">- C$ ${fmt(d.total_acreditamientos)}</td>
                    </tr>
                    ${d.saldo_a_pagar > 0 ? `
                        <tr class="total-row" style="background: #fee2e2;">
                            <td><strong style="color: #dc2626; font-size: 13px;">61. SALDO A PAGAR A LA DGI</strong></td>
                            <td class="text-right"><strong style="color: #dc2626; font-size: 13px;">C$ ${fmt(d.saldo_a_pagar)}</strong></td>
                        </tr>
                    ` : `
                        <tr class="total-row" style="background: #dcfce7;">
                            <td><strong style="color: #16a34a; font-size: 13px;">62. SALDO A FAVOR DEL CONTRIBUYENTE</strong></td>
                            <td class="text-right"><strong style="color: #16a34a; font-size: 13px;">C$ ${fmt(d.saldo_a_favor)}</strong></td>
                        </tr>
                    `}
                </table>

                <div style="margin-top: 40px; display: flex; justify-content: space-around; text-align: center;">
                    <div style="width: 220px; border-top: 1px solid #000; padding-top: 5px;">Contador General</div>
                    <div style="width: 220px; border-top: 1px solid #000; padding-top: 5px;">Gerente Administrativo</div>
                </div>
            </body>
            </html>
        `;

        printWin.document.open();
        printWin.document.write(docContent);
        printWin.document.close();
    } catch (err) {
        alert('Error al generar la impresión: ' + err.message);
    }
}
window.imprimirDeclaracionEspecifica = imprimirDeclaracionEspecifica;

/**
 * Imprimir Formulario Oficial 106
 */
function imprimirFormulario106() {
    if (!simulacionFiscalActual) {
        alert('Cargue Contabilidad antes de imprimir.');
        return;
    }
    if (!simulacionFiscalActual) {
        alert('Espere a que cargue Contabilidad antes de guardar.');
        return;
    }
    recalcularFormularioCuentas();
    const payload = recopilarPayloadSimulacion();
    const printWin = window.open('', '_blank', 'width=950,height=1050');
    if (!printWin) return;

    const val = (id) => {
        const el = document.getElementById(id);
        if (!el) return 0.0;
        const clean = String(el.value).replace(/,/g, '').trim();
        return parseFloat(clean) || 0.0;
    };

    const docContent = `
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Declaración Anual IR - Formulario 106 DGI - Jehová Jireh</title>
            <style>
                body { font-family: Arial, sans-serif; font-size: 11px; color: #000; margin: 20px; }
                table { width: 100%; border-collapse: collapse; margin-bottom: 15px; }
                th, td { border: 1px solid #94a3b8; padding: 4px 6px; }
                .dgi-hdr { display: flex; justify-content: space-between; align-items: center; border: 1px solid #005fa8; padding: 10px; margin-bottom: 8px; }
                .title-box { display: flex; border: 1px solid #005fa8; margin-bottom: 10px; }
                .code-106 { font-size: 26px; font-weight: bold; color: #005fa8; padding: 8px 15px; border-right: 1px solid #005fa8; display: flex; align-items: center; }
                .sec-head { background: #005fa8; color: #fff; font-weight: bold; padding: 4px 8px; text-transform: uppercase; font-size: 11px; }
                .total-row { background: #f1f5f9; font-weight: bold; }
                .total-row td { border-top: 2px solid #000; border-bottom: 2px solid #000; }
                .text-right { text-align: right; }
                .text-center { text-align: center; }
            </style>
        </head>
        <body>
            ${simulacionFiscalActual?.datos_demostracion ? '<p><strong>DEMOSTRACIÓN — Sin validez oficial.</strong></p>' : ''}
            <div class="dgi-hdr">
                <div>
                    <strong>Gobierno de Reconciliación y Unidad Nacional</strong><br>
                    <span>Ministerio de Hacienda y Crédito Público • Dirección General de Ingresos (DGI)</span>
                </div>
                <div style="text-align: right;">
                    <strong>Ventanilla Electrónica Tributaria (VET)</strong><br>
                    <span>Ejercicio Fiscal: <strong>${anioFiscalSeleccionado}</strong></span>
                </div>
            </div>

            <div class="title-box">
                <div class="code-106">106</div>
                <div style="flex: 1; text-align: center; padding: 6px;">
                    <strong style="font-size: 14px; color: #005fa8;">DECLARACION ANUAL DEL IMPUESTO SOBRE LA RENTA (IR)</strong><br>
                    <span style="font-weight: bold;">RENTA ANUAL IR 106</span>
                </div>
                <div style="padding: 6px 12px; text-align: right; border-left: 1px solid #005fa8; font-size: 10px;">
                    <strong>Período:</strong> 12<br>
                    <strong>Tipo:</strong> Original
                </div>
            </div>

            <div class="sec-head">A. DATOS GENERALES</div>
            <table>
                <tr>
                    <td style="width: 20%; font-weight: bold;">Número RUC:</td>
                    <td style="width: 30%;">${escaparFiscal(document.getElementById('vet-cta-ruc')?.value || 'SIN CONFIGURAR')}</td>
                    <td style="width: 25%; font-weight: bold;">Razón Social:</td>
                    <td>Jehová Jireh Moto Repuestos y Servicios</td>
                </tr>
                <tr>
                    <td style="font-weight: bold;">Actividad Económica:</td>
                    <td colspan="3">Comercio al por menor de repuestos, lubricantes y mantenimiento de motocicletas</td>
                </tr>
            </table>

            <div class="sec-head">B. BALANCE GENERAL (CUENTAS DETALLADAS DE JEHOVÁ JIREH)</div>
            <table>
                <thead>
                    <tr style="background: #e2e8f0;">
                        <th style="width: 40px;">No.</th>
                        <th>Cuenta / Concepto Contable</th>
                        <th class="text-right" style="width: 140px;">Importe (C$)</th>
                    </tr>
                </thead>
                <tbody>
                    <tr><td class="text-center">1</td><td>1.1.01 Caja General</td><td class="text-right">${fmt(val('cta-1101'))}</td></tr>
                    <tr><td class="text-center">2</td><td>1.1.02 Bancos e Instituciones Financieras</td><td class="text-right">${fmt(val('cta-1102'))}</td></tr>
                    <tr><td class="text-center">3</td><td>1.1.03 Clientes y Cuentas por Cobrar Comerciales</td><td class="text-right">${fmt(val('cta-1103'))}</td></tr>
                    <tr><td class="text-center">4</td><td>1.1.04 Inventarios de Repuestos y Accesorios</td><td class="text-right">${fmt(val('cta-1104'))}</td></tr>
                    <tr><td class="text-center">5</td><td>1.1.05 IVA Acreditable Fiscal</td><td class="text-right">${fmt(val('cta-1105'))}</td></tr>
                    <tr class="total-row"><td class="text-center"><strong>6</strong></td><td><strong>Total Activo Circulante (1 al 5)</strong></td><td class="text-right"><strong>${fmt(val('tot-act-circ'))}</strong></td></tr>
                    <tr><td class="text-center">7</td><td>1.2.01 Mobiliario y Equipo de Oficina y Taller</td><td class="text-right">${fmt(val('cta-1201'))}</td></tr>
                    <tr><td class="text-center">8</td><td>1.2.02 Equipo de Cómputo y Sistemas</td><td class="text-right">${fmt(val('cta-1202'))}</td></tr>
                    <tr><td class="text-center">9</td><td>1.2.03 (-) Depreciación Acumulada de Activos</td><td class="text-right">${fmt(val('cta-1203'))}</td></tr>
                    <tr class="total-row"><td class="text-center"><strong>10</strong></td><td><strong>Total Activos Mobiliarios Netos (7 + 8 - 9)</strong></td><td class="text-right"><strong>${fmt(val('tot-act-fijo'))}</strong></td></tr>
                    <tr class="total-row" style="background: #e0f2fe;"><td class="text-center"><strong>12</strong></td><td><strong style="color: #005fa8;">TOTAL ACTIVOS (6 + 10 + 11)</strong></td><td class="text-right"><strong style="color: #005fa8;">${fmt(val('tot-activos'))}</strong></td></tr>
                    <tr><td class="text-center">13</td><td>2.1.01 Proveedores Comerciales</td><td class="text-right">${fmt(val('cta-2101'))}</td></tr>
                    <tr><td class="text-center">14</td><td>2.1.02 Documentos por Pagar</td><td class="text-right">${fmt(val('cta-2102'))}</td></tr>
                    <tr><td class="text-center">15</td><td>2.1.03 IVA Débito Fiscal por Pagar</td><td class="text-right">${fmt(val('cta-2103'))}</td></tr>
                    <tr><td class="text-center">16</td><td>2.1.04 Sueldos y Salarios por Pagar</td><td class="text-right">${fmt(val('cta-2104'))}</td></tr>
                    <tr><td class="text-center">17</td><td>2.1.05 Servicios Básicos por Pagar</td><td class="text-right">${fmt(val('cta-2105'))}</td></tr>
                    <tr><td class="text-center">18</td><td>2.1.06 Retenciones INSS por Pagar</td><td class="text-right">${fmt(val('cta-2106'))}</td></tr>
                    <tr><td class="text-center">19</td><td>2.1.07 Retenciones IR por Pagar</td><td class="text-right">${fmt(val('cta-2107'))}</td></tr>
                    <tr><td class="text-center">20</td><td>2.1.08 Provisiones Sociales por Pagar (Aguinaldo)</td><td class="text-right">${fmt(val('cta-2108'))}</td></tr>
                    <tr><td class="text-center">21</td><td>2.1.10 INATEC por Pagar</td><td class="text-right">${fmt(val('cta-2110'))}</td></tr>
                    <tr class="total-row" style="background: #e0f2fe;"><td class="text-center"><strong>22</strong></td><td><strong style="color: #005fa8;">TOTAL PASIVOS (13 al 21)</strong></td><td class="text-right"><strong style="color: #005fa8;">${fmt(val('tot-pasivos'))}</strong></td></tr>
                    <tr><td class="text-center">23</td><td>3.1.01 Capital del Propietario</td><td class="text-right">${fmt(val('cta-3101'))}</td></tr>
                    <tr><td class="text-center">24</td><td>3.1.02 Utilidades Acumuladas</td><td class="text-right">${fmt(val('cta-3102'))}</td></tr>
                    <tr><td class="text-center">25</td><td>Utilidad Neta del Ejercicio Actual</td><td class="text-right">${fmt(val('cta-util-ejercicio'))}</td></tr>
                    <tr class="total-row"><td class="text-center"><strong>26</strong></td><td><strong>Total Patrimonio Neto (23 + 24 + 25)</strong></td><td class="text-right"><strong>${fmt(val('tot-patrimonio'))}</strong></td></tr>
                    <tr class="total-row" style="background: #dcfce7;"><td class="text-center"><strong>27</strong></td><td><strong style="color: #16a34a;">TOTAL PASIVO + PATRIMONIO (Debe igualar R12)</strong></td><td class="text-right"><strong style="color: #16a34a;">${fmt(val('tot-pasivo-patrimonio'))}</strong></td></tr>
                </tbody>
            </table>

            <div class="sec-head">D. ESTADO DE RESULTADOS</div>
            <table>
                <tr><td class="text-center" style="width: 40px;">30</td><td>4.1.01 Ventas de Repuestos y Accesorios</td><td class="text-right" style="width: 140px;">${fmt(val('cta-4101'))}</td></tr>
                <tr><td class="text-center">31</td><td>4.1.02 Ingresos por Servicios de Taller</td><td class="text-right">${fmt(val('cta-4102'))}</td></tr>
                <tr class="total-row"><td><strong>32</strong></td><td><strong>Total Ingresos Brutos (30 + 31)</strong></td><td class="text-right"><strong>${fmt(val('tot-ingresos'))}</strong></td></tr>
                <tr><td class="text-center">33</td><td>5.1.01 Costo de Ventas</td><td class="text-right">${fmt(val('cta-5101'))}</td></tr>
                <tr class="total-row"><td><strong>34</strong></td><td><strong>Utilidad Bruta Contable (32 - 33)</strong></td><td class="text-right"><strong>${fmt(val('tot-util-bruta'))}</strong></td></tr>
                <tr><td class="text-center">47</td><td>Total Gastos Deducibles de Operación</td><td class="text-right">${fmt(val('tot-gastos-op'))}</td></tr>
                <tr class="total-row" style="background: #e0f2fe;"><td><strong>48</strong></td><td><strong>Utilidad Neta Contable del Ejercicio (34 - 47)</strong></td><td class="text-right"><strong>${fmt(val('tot-util-neta'))}</strong></td></tr>
            </table>

            <div class="sec-head">E. CÁLCULO DEL IR Y F. LIQUIDACIÓN</div>
            <table>
                <tr><td style="width: 70%;">Renta Neta Gravable Oficial</td><td class="text-right" style="font-weight: bold;">C$ ${fmt(val('ir-renta-gravable'))}</td></tr>
                <tr><td>IR Actividades Económicas (tarifa Art. 52)</td><td class="text-right">C$ ${fmt(val('ir-calculado-30'))}</td></tr>
                <tr><td>Pago Mínimo Definitivo (1% de Ingresos)</td><td class="text-right">C$ ${fmt(val('ir-pmd-1'))}</td></tr>
                <tr class="total-row" style="background: #e0f2fe;"><td><strong>IR DETERMINADO OFICIAL (El Mayor)</strong></td><td class="text-right"><strong>C$ ${fmt(val('ir-determinado'))}</strong></td></tr>
                <tr><td>(-) Anticipos Mensuales Pagados del 1% PMD</td><td class="text-right" style="color: #16a34a;">- C$ ${fmt(val('liq-anticipos-1'))}</td></tr>
                <tr class="total-row" style="background: #fee2e2;"><td><strong style="color: #dc2626; font-size: 13px;">SALDO A PAGAR A LA DGI</strong></td><td class="text-right"><strong style="color: #dc2626; font-size: 13px;">C$ ${fmt(val('liq-saldo-pagar'))}</strong></td></tr>
            </table>

            <div style="margin-top: 40px; display: flex; justify-content: space-around; text-align: center;">
                <div style="width: 220px; border-top: 1px solid #000; padding-top: 5px;">Contador General</div>
                <div style="width: 220px; border-top: 1px solid #000; padding-top: 5px;">Gerente Administrativo</div>
            </div>
        </body>
        </html>
    `;

    printWin.document.open();
    printWin.document.write(docContent);
    printWin.document.close();
}
window.imprimirFormulario106 = imprimirFormulario106;

/**
 * Imprimir Vista Resumen Ejecutivo (Formato Imagen 1)
 */
function imprimirResumenEjecutivo() {
    if (!simulacionFiscalActual) {
        alert('Cargue Contabilidad antes de imprimir.');
        return;
    }
    recalcularFormularioCuentas();

    const anio = anioFiscalSeleccionado || 2026;
    const fecha = document.getElementById('vet-resumen-fecha')?.textContent || new Date().toISOString().slice(0, 10);
    const noDecl = document.getElementById('vet-resumen-no-decl')?.textContent || `IR106-${anio}-SIM`;
    const tipoDecl = document.getElementById('vet-resumen-tipo-decl')?.textContent || 'Original';

    const activos = document.getElementById('kpi-res-activos')?.textContent || 'C$ 0.00';
    const pasivos = document.getElementById('kpi-res-pasivos')?.textContent || 'C$ 0.00';
    const patrimonio = document.getElementById('kpi-res-patrimonio')?.textContent || 'C$ 0.00';
    const cuadre = document.getElementById('kpi-res-cuadre')?.textContent || 'Cuadrado ✓';

    const ingresos = document.getElementById('kpi-res-ingresos')?.textContent || 'C$ 0.00';
    const costos = document.getElementById('kpi-res-costos')?.textContent || 'C$ 0.00';
    const gastos = document.getElementById('kpi-res-gastos')?.textContent || 'C$ 0.00';
    const utilidad = document.getElementById('kpi-res-utilidad')?.textContent || 'C$ 0.00';

    const rentaNeta = document.getElementById('kpi-res-renta-neta')?.textContent || 'C$ 0.00';
    const ir30 = document.getElementById('kpi-res-ir30')?.textContent || 'C$ 0.00';
    const pmd1 = document.getElementById('kpi-res-pmd1')?.textContent || 'C$ 0.00';
    const irDeterminado = document.getElementById('kpi-res-ir-determinado')?.textContent || 'C$ 0.00';

    const acreditamientos = document.getElementById('kpi-res-acreditamientos')?.textContent || 'C$ 0.00';
    const saldoPagar = document.getElementById('kpi-res-saldo-pagar')?.textContent || 'C$ 0.00';
    const saldoFavor = document.getElementById('kpi-res-saldo-favor')?.textContent || 'C$ 0.00';
    const tienePagar = (document.getElementById('card-saldo-final-pagar')?.style.display !== 'none');

    const printWin = window.open('', '_blank', 'width=950,height=1050');
    if (!printWin) {
        alert('Por favor permita ventanas emergentes para imprimir.');
        return;
    }

    const docContent = `
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Resumen Ejecutivo - Declaración Anual IR ${anio} - Jehová Jireh</title>
            <style>
                body { font-family: Arial, sans-serif; font-size: 11px; color: #1e293b; margin: 25px; background: #fff; }
                .dgi-hdr { display: flex; justify-content: space-between; align-items: center; border: 1px solid #005fa8; padding: 10px 14px; margin-bottom: 10px; border-radius: 4px; }
                .title-box { display: flex; border: 2px solid #005fa8; margin-bottom: 12px; border-radius: 4px; background: #f8fafc; }
                .code-106 { font-size: 28px; font-weight: 900; color: #005fa8; padding: 10px 18px; border-right: 2px solid #005fa8; display: flex; align-items: center; background: #e0f2fe; }
                .sec-banner { background: #005fa8; color: #fff; font-weight: bold; padding: 5px 10px; font-size: 11px; text-transform: uppercase; margin-top: 14px; margin-bottom: 6px; border-radius: 3px; letter-spacing: 0.5px; }
                .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-bottom: 8px; }
                .kpi-box { border: 1px solid #cbd5e1; border-radius: 5px; padding: 8px 10px; background: #f8fafc; }
                .kpi-box .kpi-label { font-size: 10px; color: #64748b; font-weight: bold; margin-bottom: 4px; text-transform: uppercase; }
                .kpi-box .kpi-val { font-size: 13px; font-weight: 800; font-family: monospace; color: #0f172a; }
                .highlight-blue { border: 2px solid #005fa8; background: #f0f9ff; }
                .highlight-blue .kpi-val { color: #005fa8; font-size: 14px; }
                .highlight-red { border: 2px solid #dc2626; background: #fef2f2; }
                .highlight-red .kpi-val { color: #dc2626; font-size: 15px; }
                .highlight-green { border: 2px solid #16a34a; background: #f0fdf4; }
                .highlight-green .kpi-val { color: #16a34a; font-size: 15px; }
                .general-table { width: 100%; border-collapse: collapse; margin-bottom: 8px; font-size: 11px; }
                .general-table td { padding: 5px 8px; border: 1px solid #cbd5e1; }
                .no-print { display: flex; justify-content: space-between; align-items: center; background: #f1f5f9; padding: 8px 14px; margin-bottom: 16px; border-radius: 6px; border: 1px solid #cbd5e1; }
                @media print {
                    body { margin: 10px; }
                    .no-print { display: none !important; }
                }
            </style>
        </head>
        <body>
            ${simulacionFiscalActual?.datos_demostracion ? '<p><strong>DEMOSTRACIÓN — Sin validez oficial.</strong></p>' : ''}
            <div class="no-print">
                <div><strong>Vista Resumen Ejecutivo — Declaración Anual IR ${anio}</strong></div>
                <button onclick="window.print()" style="background: #005fa8; color: #fff; border: none; padding: 6px 16px; border-radius: 4px; font-weight: bold; cursor: pointer;">
                    Imprimir Resumen
                </button>
            </div>

            <div class="dgi-hdr">
                <div>
                    <strong style="font-size: 12px;">Gobierno de Reconciliación y Unidad Nacional</strong><br>
                    <span style="font-size: 10px; color: #475569;">Ministerio de Hacienda y Crédito Público • Dirección General de Ingresos (DGI)</span>
                </div>
                <div style="text-align: right;">
                    <strong>Ventanilla Electrónica Tributaria (VET)</strong><br>
                    <span>Ejercicio Fiscal: <strong>${anio}</strong></span>
                </div>
            </div>

            <div class="title-box">
                <div class="code-106">106</div>
                <div style="flex: 1; text-align: center; padding: 8px;">
                    <strong style="font-size: 14px; color: #005fa8; letter-spacing: 0.5px;">DECLARACION ANUAL DEL IMPUESTO SOBRE LA RENTA (IR)</strong><br>
                    <span style="font-weight: 800; font-size: 12px; color: #334155;">RENTA ANUAL IR 106 · VISTA RESUMEN EJECUTIVO</span>
                </div>
                <div style="padding: 8px 14px; text-align: right; border-left: 2px solid #005fa8; font-size: 10px; background: #fff;">
                    <strong>No. Declaración:</strong> ${noDecl}<br>
                    <strong>Tipo:</strong> ${tipoDecl}<br>
                    <strong>Fecha:</strong> ${fecha}
                </div>
            </div>

            <div class="sec-banner">A. Datos Generales del Contribuyente</div>
            <table class="general-table">
                <tr>
                    <td style="width: 20%; font-weight: bold; background: #f8fafc;">Número RUC:</td>
                    <td style="width: 30%; font-family: monospace; font-weight: bold; color: #005fa8;">${escaparFiscal(document.getElementById('vet-cta-ruc')?.value || 'SIN CONFIGURAR')}</td>
                    <td style="width: 25%; font-weight: bold; background: #f8fafc;">Razón Social:</td>
                    <td style="font-weight: bold;">Jehová Jireh Moto Repuestos y Servicios</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; background: #f8fafc;">Actividad Económica:</td>
                    <td colspan="3">Comercio al por menor de repuestos, lubricantes y mantenimiento de motocicletas</td>
                </tr>
            </table>

            <div class="sec-banner">B. Balance General — Situación Financiera</div>
            <div class="kpi-grid">
                <div class="kpi-box">
                    <div class="kpi-label">Total Activo (Renglón 12)</div>
                    <div class="kpi-val">${activos}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">Total Pasivo (Renglón 22)</div>
                    <div class="kpi-val">${pasivos}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">Patrimonio Neto (Renglón 26)</div>
                    <div class="kpi-val">${patrimonio}</div>
                </div>
                <div class="kpi-box highlight-green">
                    <div class="kpi-label" style="color: #16a34a;">Estado de Cuadre</div>
                    <div class="kpi-val" style="color: #16a34a; font-size: 12px;">${cuadre}</div>
                </div>
            </div>

            <div class="sec-banner">D. Estado de Resultados — Rendimiento Operativo</div>
            <div class="kpi-grid">
                <div class="kpi-box">
                    <div class="kpi-label">Ingresos Brutos (R32)</div>
                    <div class="kpi-val">${ingresos}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">Costo de Ventas (R33)</div>
                    <div class="kpi-val">${costos}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">Gastos Operativos (R47)</div>
                    <div class="kpi-val">${gastos}</div>
                </div>
                <div class="kpi-box highlight-blue">
                    <div class="kpi-label" style="color: #005fa8;">Utilidad Neta (R48)</div>
                    <div class="kpi-val" style="color: #005fa8;">${utilidad}</div>
                </div>
            </div>

            <div class="sec-banner">E. Cálculo del Impuesto sobre la Renta (IR)</div>
            <div class="kpi-grid">
                <div class="kpi-box">
                    <div class="kpi-label">Renta Neta Gravable</div>
                    <div class="kpi-val">${rentaNeta}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">IR según tarifa (Art. 52 Ley 822)</div>
                    <div class="kpi-val">${ir30}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">Pago Mínimo Definitivo 1%</div>
                    <div class="kpi-val">${pmd1}</div>
                </div>
                <div class="kpi-box highlight-blue">
                    <div class="kpi-label" style="color: #005fa8;">IR Determinado Oficial</div>
                    <div class="kpi-val" style="color: #005fa8;">${irDeterminado}</div>
                </div>
            </div>

            <div class="sec-banner">F. Liquidación Final del Impuesto y Acreditamientos</div>
            <div class="kpi-grid">
                <div class="kpi-box">
                    <div class="kpi-label">IR Determinado</div>
                    <div class="kpi-val">${irDeterminado}</div>
                </div>
                <div class="kpi-box">
                    <div class="kpi-label">Total Acreditamientos</div>
                    <div class="kpi-val" style="color: #16a34a;">${acreditamientos}</div>
                </div>
                ${tienePagar ? `
                    <div class="kpi-box highlight-red" style="grid-column: span 2;">
                        <div class="kpi-label" style="color: #dc2626;">Saldo a Pagar a la DGI (Renglón 61)</div>
                        <div class="kpi-val" style="color: #dc2626; font-size: 16px;">${saldoPagar}</div>
                    </div>
                ` : `
                    <div class="kpi-box highlight-green" style="grid-column: span 2;">
                        <div class="kpi-label" style="color: #16a34a;">Saldo a Favor del Contribuyente (Renglón 62)</div>
                        <div class="kpi-val" style="color: #16a34a; font-size: 16px;">${saldoFavor}</div>
                    </div>
                `}
            </div>

            <div style="margin-top: 45px; display: flex; justify-content: space-around; text-align: center;">
                <div style="width: 220px; border-top: 1px solid #334155; padding-top: 6px; font-size: 11px; font-weight: bold;">
                    Contador General<br><small style="font-weight: normal; color: #64748b;">Firma y Sello</small>
                </div>
                <div style="width: 220px; border-top: 1px solid #334155; padding-top: 6px; font-size: 11px; font-weight: bold;">
                    Gerente Administrativo<br><small style="font-weight: normal; color: #64748b;">Representante Legal</small>
                </div>
            </div>
        </body>
        </html>
    `;

    printWin.document.open();
    printWin.document.write(docContent);
    printWin.document.close();
}
window.imprimirResumenEjecutivo = imprimirResumenEjecutivo;

/**
 * Helpers auxiliares
 */
function fmt(val) {
    if (val === null || val === undefined) return '0.00';
    let num = (typeof val === 'number') ? val : (parseFloat(String(val).replace(/,/g, '').trim()) || 0);
    if (isNaN(num)) num = 0;
    if (Math.abs(num) < 0.000001) num = 0;
    return num.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function round2(val) {
    const num = (typeof val === 'number') ? val : (parseFloat(String(val).replace(/,/g, '').trim()) || 0);
    return Math.round(num * 100) / 100;
}

function setVal(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function setIn(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = fmt(val);
}

function closeModal(id) {
    const m = document.getElementById(id);
    if (m) {
        m.classList.remove('active');
        m.style.display = 'none';
    }
}

// Formateo automático de comas y punto decimal para todos los campos al enfocar y desenfocar
document.addEventListener('focusin', (e) => {
    if (e.target && e.target.classList && e.target.classList.contains('dgi-input-renglon') && !e.target.readOnly) {
        e.target.select();
    }
});

document.addEventListener('focusout', (e) => {
    if (e.target && e.target.classList && e.target.classList.contains('dgi-input-renglon') && !e.target.readOnly) {
        const raw = e.target.value;
        if (e.target.id === 'cta-1203') {
            const n = Math.abs(parseFloat(String(raw).replace(/,/g, '').trim()) || 0);
            e.target.value = fmt(-n);
        } else {
            const n = parseFloat(String(raw).replace(/,/g, '').trim()) || 0;
            e.target.value = fmt(n);
        }
        recalcularFormularioCuentas();
    }
});
