// ==============================================================================
// Jehová Jireh Moto Repuestos - Lógica Frontend SPA & Conexión con API Flask
// ==============================================================================

// =========================================================================
// SISTEMA DE ALERTAS Y CONFIRMACIONES MODERNAS (SWEETALERT2)
// Elimina diálogos nativos del navegador ("192.168.0.7 dice") con interfaz estética
// =========================================================================

function getSwalTheme() {
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    return {
        background: isLight ? '#ffffff' : '#1e293b',
        color: isLight ? '#0f172a' : '#f8fafc',
        confirmButtonColor: '#dc2626',
        cancelButtonColor: isLight ? '#94a3b8' : '#475569'
    };
}

// Diálogo de Confirmación Moderno (Reemplazo estético de confirm())
async function confirmarAccion({
    titulo = '¿Estás seguro?',
    texto = '',
    icono = 'warning',
    textoConfirmar = 'Sí, continuar',
    textoCancelar = 'Cancelar',
    esPeligroso = false
} = {}) {
    if (typeof Swal === 'undefined') {
        return window._nativeConfirm ? window._nativeConfirm(texto || titulo) : true;
    }
    const theme = getSwalTheme();
    const result = await Swal.fire({
        title: titulo,
        html: texto ? `<span style="font-size:0.95rem; line-height:1.5;">${texto.replace(/\n/g, '<br>')}</span>` : undefined,
        icon: icono,
        showCancelButton: true,
        confirmButtonText: textoConfirmar,
        cancelButtonText: textoCancelar,
        reverseButtons: true,
        background: theme.background,
        color: theme.color,
        customClass: {
            popup: 'jj-swal-popup',
            confirmButton: esPeligroso ? 'btn btn-danger jj-swal-btn' : 'btn btn-primary jj-swal-btn',
            cancelButton: 'btn btn-secondary jj-swal-btn'
        },
        buttonsStyling: false
    });
    return result.isConfirmed;
}

// Alerta Moderna (Reemplazo estético de alert())
function mostrarMensaje({
    titulo = '',
    texto = '',
    icono = 'info',
    temporizador = null
} = {}) {
    if (typeof Swal === 'undefined') {
        console.log(titulo, texto);
        return Promise.resolve();
    }
    const theme = getSwalTheme();
    return Swal.fire({
        title: titulo || (icono === 'success' ? '¡Éxito!' : icono === 'error' ? 'Atención' : 'Notificación'),
        html: `<span style="font-size:0.95rem; line-height:1.5;">${texto.replace(/\n/g, '<br>')}</span>`,
        icon: icono,
        confirmButtonText: 'Entendido',
        timer: temporizador,
        timerProgressBar: !!temporizador,
        background: theme.background,
        color: theme.color,
        customClass: {
            popup: 'jj-swal-popup',
            confirmButton: 'btn btn-primary jj-swal-btn'
        },
        buttonsStyling: false
    });
}

// Toast notification moderno y discreto
function mostrarToast(mensaje, tipo = 'success') {
    if (typeof Swal === 'undefined') return;
    const theme = getSwalTheme();
    const Toast = Swal.mixin({
        toast: true,
        position: 'top-end',
        showConfirmButton: false,
        timer: 3500,
        timerProgressBar: true,
        background: theme.background,
        color: theme.color,
        didOpen: (toast) => {
            toast.addEventListener('mouseenter', Swal.stopTimer);
            toast.addEventListener('mouseleave', Swal.resumeTimer);
        }
    });
    Toast.fire({
        icon: tipo === 'error' ? 'error' : (tipo === 'warning' ? 'warning' : 'success'),
        title: mensaje
    });
}

window.confirmarAccion = confirmarAccion;
window.mostrarMensaje = mostrarMensaje;
window.mostrarToast = mostrarToast;
window.showToast = mostrarToast;

// =========================================================================
// FORMATEADORES NUMÉRICOS ESTANDARIZADOS (Punto decimal y comas de miles)
// =========================================================================
function formatMoneda(val, simbolo = '$ ') {
    if (val === null || val === undefined || isNaN(val)) return `${simbolo}0.00`;
    return `${simbolo}` + Number(val).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

function formatCantidad(val, sufijo = '') {
    if (val === null || val === undefined || isNaN(val)) return `0${sufijo ? ' ' + sufijo : ''}`;
    return Number(val).toLocaleString('en-US') + (sufijo ? ' ' + sufijo : '');
}

function formatPorcentaje(val) {
    if (val === null || val === undefined || isNaN(val)) return '0.0%';
    return Number(val).toLocaleString('en-US', { minimumFractionDigits: 1, maximumFractionDigits: 2 }) + '%';
}

window.formatMoneda = formatMoneda;
window.formatCantidad = formatCantidad;
window.formatPorcentaje = formatPorcentaje;

// INTERCEPTOR UNIVERSAL DE ALERT:
// Nunca más saldrá la ventana nativa "192.168.0.7 dice"
if (!window._nativeAlert) {
    window._nativeAlert = window.alert;
    window.alert = function(msg) {
        let icon = 'info';
        let cleanMsg = String(msg || '');
        if (cleanMsg.includes('✅') || cleanMsg.toLowerCase().includes('éxito') || cleanMsg.toLowerCase().includes('exito') || cleanMsg.toLowerCase().includes('guardado') || cleanMsg.toLowerCase().includes('registrado') || cleanMsg.toLowerCase().includes('exitosa') || cleanMsg.toLowerCase().includes('exitosamente')) {
            icon = 'success';
        } else if (cleanMsg.includes('❌') || cleanMsg.toLowerCase().includes('error') || cleanMsg.toLowerCase().includes('superado') || cleanMsg.toLowerCase().includes('no hay') || cleanMsg.toLowerCase().includes('no puedes')) {
            icon = 'error';
        } else if (cleanMsg.includes('⚠️') || cleanMsg.toLowerCase().includes('advertencia') || cleanMsg.toLowerCase().includes('cuidado') || cleanMsg.toLowerCase().includes('debes')) {
            icon = 'warning';
        }
        
        let title = icon === 'success' ? 'Operación Exitosa' : (icon === 'error' ? 'Atención' : 'Notificación');
        if (cleanMsg.includes('¡') && cleanMsg.includes('!')) {
            const match = cleanMsg.match(/¡([^!]+)!/);
            if (match) title = match[1];
        }

        mostrarMensaje({
            titulo: title,
            texto: cleanMsg,
            icono: icon
        });
    };
}

let productosCache = [];
let proveedoresCache = [];
let movimientosCache = [];
let ventasCache = [];
let cartPOS = []; // [{"producto_id": 1, "nombre": "...", "precio": 15.50, "cantidad": 1, "stock_max": 18}]

// Instancias de Chart.js
var chartTendenciaInstance = window.chartTendenciaInstance || null;
var chartTopProdsInstance = window.chartTopProdsInstance || null;
var chartCategoriaInstance = window.chartCategoriaInstance || null;
var chartMetodosPagoInstance = window.chartMetodosPagoInstance || null;
var _reporteDataCache = window._reporteDataCache || null;
var _filtroABCActual = window._filtroABCActual || 'todos';
var ventaSeleccionadaActual = window.ventaSeleccionadaActual || null;

document.addEventListener('DOMContentLoaded', () => {
    console.log('⚡ Inicializando Sistema Jehová Jireh Moto Repuestos...');

    initNavigation();
    loadDashboardStats();

    // Event listeners para filtros de búsqueda
    const filterInv = document.getElementById('filter-inventario');
    if (filterInv) {
        filterInv.addEventListener('input', (e) => filterInventarioTable(e.target.value));
    }

    const filterMov = document.getElementById('filter-movimientos');
    if (filterMov) {
        filterMov.addEventListener('input', (e) => filterMovimientosTable(e.target.value));
    }

    const searchPOS = document.getElementById('pos-search');
    if (searchPOS) {
        searchPOS.addEventListener('input', (e) => filterPOSProductsGrid(e.target.value));
    }

    const filterVentas = document.getElementById('filter-historial-ventas');
    if (filterVentas) {
        filterVentas.addEventListener('input', (e) => filterHistorialVentasTable(e.target.value));
    }

    const filterPedidosWeb = document.getElementById('filter-pedidos-web');
    if (filterPedidosWeb) {
        filterPedidosWeb.addEventListener('input', (e) => filterPedidosWebTable(e.target.value));
    }
});

// ==============================================================================
// NAVEGACIÓN Y PESTAÑAS (TABS & SUBTABS)
// ==============================================================================

function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const tabId = item.getAttribute('data-tab');
            if (tabId) {
                switchTab(tabId);
            }
        });
    });
}

function switchTab(tabId) {
    document.querySelectorAll('.nav-item').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));

    const navLink = document.querySelector(`.nav-item[data-tab="${tabId}"]`);
    if (navLink) navLink.classList.add('active');

    const tabSection = document.getElementById(tabId);
    if (tabSection) {
        tabSection.classList.add('active');
        window.dispatchEvent(new CustomEvent('workspace:tab-change', { detail: { tabId } }));

        // Cargar datos según la pestaña activa
        if (tabId === 'tab-inventario') loadInventario();
        if (tabId === 'tab-ventas') {
            loadPOSProducts();
            loadHistorialVentas();
            loadPedidosWeb();
            verificarEstadoCaja();
        }
        if (tabId === 'tab-compras') loadComprasYProveedores();
        if (tabId === 'tab-reportes') {
            if (typeof ejecutarConsultaReportes === 'function') {
                ejecutarConsultaReportes();
            } else if (typeof loadReportesContabilidad === 'function') {
                loadReportesContabilidad();
            }
        }
        if (tabId === 'tab-usuarios') loadUsuarios();
        if (tabId === 'tab-panel') loadDashboardStats();
        if (tabId === 'tab-finanzas') cargarDatosFinanzas();
        if (tabId === 'tab-fiscal' && typeof cargarModuloFiscal === 'function') cargarModuloFiscal();
    }
}

function switchInventarioSubtab(subtab, btn) {
    const section = document.getElementById('tab-inventario');
    if (!section) return;

    section.querySelectorAll('.subnav-btn').forEach(b => b.classList.remove('active'));
    section.querySelectorAll('.subtab-view').forEach(v => v.classList.remove('active'));

    btn.classList.add('active');
    const view = document.getElementById(`subtab-${subtab}`);
    if (view) view.classList.add('active');

    if (subtab === 'kardex') loadMovimientos();
    if (subtab === 'existencias') loadInventario();
}

// ==============================================================================
// CAJA / APERTURA Y CIERRE
// ==============================================================================

async function verificarEstadoCaja() {
    try {
        const response = await fetch('/api/caja/estado');
        const data = await response.json();
        const bannerApertura = document.getElementById('caja-apertura-banner');
        const botonCierreDiscreto = document.getElementById('caja-cierre-discreto');
        const infoActiva = document.getElementById('caja-info-activa');
        
        if(!bannerApertura) return; // Si no está en el DOM
        
        if (data.estado === 'Abierta') {
            // Ocultar banner grande
            bannerApertura.style.display = 'none';
            // Mostrar botón discreto
            botonCierreDiscreto.style.display = 'block';
            infoActiva.innerHTML = `<strong>CAJA ACTIVA</strong> | Abierta: ${data.fecha_apertura}`;
        } else {
            // Mostrar banner grande
            bannerApertura.style.display = 'block';
            // Ocultar botón discreto
            botonCierreDiscreto.style.display = 'none';
        }
    } catch (e) {
        console.error("Error al verificar estado de caja", e);
    }
}

function abrirModalAperturaCaja() {
    const form = document.getElementById('form-apertura-caja');
    if (form) form.reset();
    
    // Obtener fecha actual formateada
    const now = new Date();
    const formattedDate = now.toLocaleDateString('es-ES') + ' ' + now.toLocaleTimeString('es-ES');
    
    const fechaInput = document.getElementById('caja-fecha-apertura');
    if (fechaInput) {
        fechaInput.value = formattedDate;
    }
    
    openModal('modal-apertura-caja');
    setTimeout(() => {
        const montoInput = document.getElementById('caja-monto-inicial');
        if (montoInput) montoInput.focus();
    }, 100);
}

function cerrarModalAperturaCaja() {
    closeModal('modal-apertura-caja');
}

async function submitAperturaCaja() {
    const inputMonto = document.getElementById('caja-monto-inicial');
    if (!inputMonto) return;
    const rawVal = inputMonto.value.trim();
    if (rawVal === '' || isNaN(parseFloat(rawVal))) {
        alert("Por favor ingrese el monto inicial de apertura.");
        inputMonto.focus();
        return;
    }
    const monto = parseFloat(rawVal);
    try {
        const response = await fetch('/api/caja/apertura', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({monto_inicial: monto})
        });
        const data = await response.json();
        if (data.error) {
            alert("Error: " + data.error);
        } else {
            alert(data.mensaje);
            cerrarModalAperturaCaja();
            verificarEstadoCaja();
        }
    } catch(e) {
        alert("Error de red al intentar abrir la caja.");
    }
}

function abrirModalCierreCaja() {
    const form = document.getElementById('form-cierre-caja');
    if (form) form.reset();
    openModal('modal-cierre-caja');
    setTimeout(() => {
        const montoInput = document.getElementById('caja-monto-final');
        if (montoInput) montoInput.focus();
    }, 100);
}

function cerrarModalCierreCaja() {
    closeModal('modal-cierre-caja');
}

async function submitCierreCaja() {
    const inputMonto = document.getElementById('caja-monto-final');
    if (!inputMonto) return;
    
    const rawVal = inputMonto.value.trim();
    if (rawVal === '' || isNaN(parseFloat(rawVal))) {
        if (typeof mostrarMensaje === 'function') {
            mostrarMensaje({ titulo: 'Monto requerido', texto: 'Por favor ingrese el monto de efectivo total en caja.', icono: 'warning' });
        } else {
            alert('Por favor ingrese el monto de efectivo total en caja.');
        }
        inputMonto.focus();
        return;
    }
    
    const montoFinal = parseFloat(rawVal);
    if (montoFinal < 0) {
        if (typeof mostrarMensaje === 'function') {
            mostrarMensaje({ titulo: 'Monto inválido', texto: 'El monto en caja no puede ser negativo.', icono: 'warning' });
        } else {
            alert('El monto en caja no puede ser negativo.');
        }
        inputMonto.focus();
        return;
    }

    const obsInput = document.getElementById('caja-observaciones');
    const obs = obsInput ? obsInput.value.trim() : '';

    const btnSubmit = document.getElementById('btn-submit-cierre-caja') || document.querySelector('#form-cierre-caja button[type="submit"]');
    if (btnSubmit) {
        btnSubmit.disabled = true;
        btnSubmit.innerHTML = '<i class="ph-bold ph-spinner ph-spin"></i> Cerrando Caja...';
    }

    try {
        const responseEstado = await fetch('/api/caja/estado');
        const cajaAct = await responseEstado.json();
        if (cajaAct.estado !== 'Abierta') {
            if (typeof mostrarMensaje === 'function') {
                mostrarMensaje({ titulo: 'Atención', texto: 'No hay ninguna caja abierta actualmente.', icono: 'info' });
            } else {
                alert('No hay caja abierta');
            }
            cerrarModalCierreCaja();
            verificarEstadoCaja();
            return;
        }

        const response = await fetch('/api/caja/cierre', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                sesion_caja_id: cajaAct.sesion_caja_id,
                monto_final_real: montoFinal,
                observaciones: obs
            })
        });
        const data = await response.json();
        if (data.error) {
            if (typeof mostrarMensaje === 'function') {
                mostrarMensaje({ titulo: 'Error al cerrar caja', texto: data.error, icono: 'error' });
            } else {
                alert("Error: " + data.error);
            }
        } else {
            let dif = Number(data.diferencia !== undefined ? data.diferencia : 0);
            let msg = `Diferencia encontrada: <strong>C$ ${formatMoneda(dif, '')}</strong>`;
            if (dif < 0) {
                msg += "<br><br><span style='color: #ef4444; font-weight: 600;'><i class='ph-bold ph-warning'></i> ¡FALTANTE DE DINERO! Debes reportarlo.</span>";
            } else if (dif > 0) {
                msg += "<br><br><span style='color: #f59e0b; font-weight: 600;'><i class='ph-bold ph-warning'></i> ¡SOBRANTE DE DINERO!</span>";
            } else {
                msg += "<br><br><span style='color: #10b981; font-weight: 600;'><i class='ph-bold ph-check-circle'></i> CAJA CUADRADA EXACTAMENTE.</span>";
            }
            
            const msgEl = document.getElementById('msg-caja-cerrada-exito-text');
            if (msgEl) msgEl.innerHTML = msg;
            
            cerrarModalCierreCaja();
            verificarEstadoCaja();
            openModal('modal-caja-cerrada-exito');
            
            const tabReportes = document.getElementById('tab-reportes');
            if (tabReportes && tabReportes.classList.contains('active') && typeof cargarSesionesCaja === 'function') {
                cargarSesionesCaja();
            }
        }
    } catch(e) {
        console.error('Error al cerrar caja:', e);
        if (typeof mostrarMensaje === 'function') {
            mostrarMensaje({ titulo: 'Error de red', texto: 'No se pudo conectar con el servidor para cerrar la caja.', icono: 'error' });
        } else {
            alert("Error de red al procesar el cierre de caja.");
        }
    } finally {
        if (btnSubmit) {
            btnSubmit.disabled = false;
            btnSubmit.innerHTML = '<i class="ph-bold ph-check-circle"></i> Cerrar Caja';
        }
    }
}

function switchVentasSubtab(subtab, btn) {
    const section = document.getElementById('tab-ventas');
    if (!section) return;

    section.querySelectorAll('.subnav-btn').forEach(b => b.classList.remove('active'));
    section.querySelectorAll('.subtab-view').forEach(v => v.classList.remove('active'));

    btn.classList.add('active');
    const view = document.getElementById(`subtab-${subtab}`);
    if (view) view.classList.add('active');

    if (subtab === 'historial-ventas') loadHistorialVentas();
    if (subtab === 'pedidos-web') loadPedidosWeb();
    if (subtab === 'pos') loadPOSProducts();
}

// ==============================================================================
// MODALES
// ==============================================================================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        modal.style.display = 'flex';
        if (modalId === 'modal-asiento' && typeof prepareAsientoModal === 'function') {
            prepareAsientoModal();
        }
        if (modalId === 'modal-compra') populateCompraSelects();
        if (modalId === 'modal-movimiento') populateMovimientoSelects();
    }
}

async function guardarCuenta(e) {
    e.preventDefault();
    const data = {
        codigo: document.getElementById('cta-codigo').value,
        nombre: document.getElementById('cta-nombre').value,
        clasificacion: document.getElementById('cta-clasificacion').value,
        naturaleza: document.getElementById('cta-naturaleza').value,
        descripcion: document.getElementById('cta-descripcion').value
    };

    try {
        const resp = await fetch('/api/finanzas/cuentas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const result = await resp.json();
        
        if (resp.ok) {
            closeModal('modal-cuenta');
            document.getElementById('form-cuenta').reset();
            cargarDatosFinanzas();
        } else {
            alert("Error: " + result.error);
        }
    } catch (err) {
        console.error(err);
        alert("Error al guardar la cuenta.");
    }
}

async function eliminarCuenta(id) {
    const confirmado = await confirmarAccion({
        titulo: '¿Eliminar cuenta?',
        texto: '¿Estás seguro de que deseas eliminar esta cuenta financiera?',
        icono: 'warning',
        textoConfirmar: 'Sí, eliminar',
        textoCancelar: 'Cancelar',
        esPeligroso: true
    });
    if (!confirmado) return;
    
    try {
        const resp = await fetch(`/api/finanzas/cuentas/${id}`, {
            method: 'DELETE'
        });
        const result = await resp.json();
        
        if (resp.ok) {
            mostrarToast('Cuenta eliminada exitosamente.', 'success');
            cargarDatosFinanzas();
        } else {
            mostrarMensaje({ titulo: 'Error al eliminar', texto: result.error || 'No se pudo eliminar la cuenta.', icono: 'error' });
        }
    } catch (err) {
        console.error(err);
        mostrarMensaje({ titulo: 'Error de red', texto: 'Error al eliminar la cuenta.', icono: 'error' });
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.remove('active');
        modal.style.display = 'none';
    }
}

// Cerrar cualquier modal al hacer clic en el fondo oscuro (backdrop)
document.addEventListener('click', (e) => {
    if (e.target && e.target.classList && e.target.classList.contains('modal')) {
        if (e.target.classList.contains('active') || e.target.style.display === 'flex') {
            closeModal(e.target.id);
        }
    }
});

// Cerrar modal al presionar la tecla Escape
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const activeModal = document.querySelector('.modal.active') || document.querySelector('.modal[style*="display: flex"]');
        if (activeModal && activeModal.id) {
            closeModal(activeModal.id);
        }
    }
});

// ==============================================================================
// CARGA Y RENDERS DE DATOS: DASHBOARD & STATS
// ==============================================================================

async function loadDashboardStats() {
    // Cada fuente puede fallar sin impedir que se muestren las demás.
    const status = document.getElementById('dashboard-load-status');
    if (status) { status.hidden = false; status.textContent = 'Actualizando datos…'; }
    const results = await Promise.allSettled(
        ['/api/productos', '/api/ventas', '/api/proveedores', '/api/movimientos'].map(async url => {
            const response = await fetch(url);
            if (!response.ok) throw new Error(`No se pudo consultar ${url}`);
            const data = await response.json();
            if (!Array.isArray(data)) throw new Error(`Respuesta inválida: ${url}`);
            return data;
        })
    );
    const [productos, ventas, proveedores, movimientos] = results.map(r => r.status === 'fulfilled' ? r.value : null);
    const put = (id, value) => { const el = document.getElementById(id); if (el) el.textContent = value; };
    if (productos) {
        productosCache = productos;
        put('stat-total-productos', formatCantidad(productos.length));
        put('stat-stock-bajo', formatCantidad(productos.filter(p => Number(p.stock) <= Number(p.min_stock)).length));
    } else {
        put('stat-total-productos', '—'); put('stat-stock-bajo', '—');
    }
    if (ventas) {
        ventasCache = ventas;
        const completadas = ventas.filter(v => v.estado === 'Completada');
        put('stat-total-ventas', `$${formatMoneda(completadas.reduce((sum, v) => sum + Number(v.total || 0), 0), '')}`);
        put('stat-conteo-ventas', `${formatCantidad(completadas.length)} ventas completadas`);
    } else {
        put('stat-total-ventas', '—'); put('stat-conteo-ventas', 'No disponible');
    }
    if (proveedores) proveedoresCache = proveedores;
    put('stat-proveedores', proveedores ? formatCantidad(proveedores.length) : '—');
    renderDashboardStock(productos);
    renderRecentSalesList(ventas);
    renderDashboardActivity(ventas, movimientos);
    if (status) {
        const failed = results.some(r => r.status === 'rejected');
        status.textContent = failed ? 'No se pudieron cargar algunos datos. Usa Actualizar para intentarlo de nuevo.' : '';
        status.hidden = !failed;
    }
}

function dashboardEscape(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;'}[char]));
}

function dashboardNewest(rows) {
    // Las fechas locales ISO se ordenan sin convertirlas a UTC ni cambiar el día.
    return [...rows].sort((a, b) => String(b.fecha || '').localeCompare(String(a.fecha || '')) || Number(b.id) - Number(a.id));
}

function dashboardDate(value) {
    const match = String(value || '').match(/^(\d{4})-(\d{2})-(\d{2})/);
    return match ? `${match[3]}/${match[2]}/${match[1]}` : 'Sin fecha';
}

function renderDashboardStock(productos) {
    const tbody = document.getElementById('dashboard-low-stock');
    if (!tbody) return;
    const bajos = productos ? productos.filter(p => Number(p.stock) <= Number(p.min_stock))
        .sort((a, b) => Number(a.stock) - Number(b.stock) || String(a.nombre).localeCompare(String(b.nombre), 'es')) : [];
    tbody.innerHTML = bajos.length ? bajos.slice(0, 6).map(p => `<tr>
        <td class="dashboard-code">${dashboardEscape(p.codigo)}</td><td>${dashboardEscape(p.nombre)}</td>
        <td class="dashboard-number dashboard-stock-count">${formatCantidad(p.stock)}</td>
        <td class="dashboard-number">${formatCantidad(p.min_stock)}</td></tr>`).join('')
        : `<tr><td colspan="4" class="dashboard-empty">${productos ? 'No hay repuestos bajo el mínimo.' : 'No se pudo cargar el inventario.'}</td></tr>`;
    const note = document.getElementById('dashboard-stock-note');
    if (note) note.textContent = bajos.length ? `Mostrando ${Math.min(bajos.length, 6)} de ${formatCantidad(bajos.length)} repuestos que requieren reposición.` : '';
}

function renderDashboardActivity(ventas, movimientos) {
    const tbody = document.getElementById('dashboard-activity');
    if (!tbody) return;
    const events = [
        ...(ventas || []).map(v => ({...v, tipo: 'Venta', icon: 'shopping-cart', usuario: v.vendedor,
            descripcion: `${v.codigo_venta} · ${v.estado || 'Registrada'}`})),
        ...(movimientos || []).filter(m => m.tipo !== 'SALIDA_VENTA').map(m => ({...m,
            tipo: String(m.tipo).startsWith('ENTRADA') ? 'Entrada' : 'Ajuste', icon: 'package',
            descripcion: `${m.producto_codigo} · ${m.producto_nombre}`}))
    ];
    tbody.innerHTML = events.length ? dashboardNewest(events).slice(0, 6).map(e => `<tr>
        <td><span class="dashboard-type"><i class="ph-bold ph-${e.icon}" aria-hidden="true"></i>${e.tipo}</span></td>
        <td><span class="dashboard-description" title="${dashboardEscape(e.descripcion)}">${dashboardEscape(e.descripcion)}</span></td><td>${dashboardEscape(e.usuario || 'Sin asignar')}</td>
        <td class="dashboard-code">${dashboardDate(e.fecha)}</td></tr>`).join('')
        : `<tr><td colspan="4" class="dashboard-empty">${ventas && movimientos ? 'No hay actividades registradas.' : 'No se pudieron cargar las actividades.'}</td></tr>`;
}

function renderRecentSalesList(ventas) {
    const container = document.getElementById('recent-sales-list');
    if (!container) return;

    if (!Array.isArray(ventas) || ventas.length === 0) {
        container.innerHTML = `<tr><td colspan="5" class="dashboard-empty">${ventas ? 'No hay ventas registradas aún.' : 'No se pudieron cargar las ventas.'}</td></tr>`;
        return;
    }

    container.innerHTML = dashboardNewest(ventas).slice(0, 6).map(v => `<tr>
        <td class="dashboard-code">${dashboardEscape(v.codigo_venta)}<small>${dashboardDate(v.fecha)}</small></td>
        <td>${dashboardEscape(v.cliente || 'Cliente de mostrador')}</td>
        <td class="dashboard-number">$${formatMoneda(v.total, '')}</td>
        <td><span class="dashboard-sale-status ${v.estado === 'Completada' ? 'is-complete' : ''}">${dashboardEscape(v.estado || 'Registrada')}</span></td>
        <td><button type="button" class="dashboard-ticket" onclick="verComprobanteVenta(${Number(v.id)})" aria-label="Ver ticket ${dashboardEscape(v.codigo_venta)}"><i class="ph-bold ph-receipt" aria-hidden="true"></i></button></td>
        </tr>`).join('');
}

// ==============================================================================
// MÁ"DULO 1: INVENTARIO & KARDEX
// ==============================================================================

async function loadInventario() {
    try {
        const res = await fetch('/api/productos');
        const productos = await res.json();
        productosCache = productos;
        renderInventarioTable(productos);
    } catch (err) {
        console.error('Error al cargar inventario:', err);
    }
}

function renderInventarioTable(productos) {
    const tbody = document.getElementById('tbody-inventario');
    if (!tbody) return;

    const userRole = window.CURRENT_USER_ROLE || '';
    const canEdit = ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones'].includes(userRole);
    const colSpanCount = canEdit ? 8 : 7;

    if (!Array.isArray(productos) || productos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${colSpanCount}" class="text-center text-muted">No hay repuestos registrados.</td></tr>`;
        return;
    }

    tbody.innerHTML = productos.map(p => {
        const isLow = p.stock <= p.min_stock;
        const badgeClass = isLow ? 'stock-low' : 'stock-ok';
        const badgeText = isLow ? `¡Bajo! (${p.stock})` : `Disponible (${p.stock})`;

        const actionTd = canEdit ? `
            <td style="display: flex; gap: 0.5rem; justify-content: flex-start; align-items: center; border: none; height: 100%;">
                <button class="btn btn-secondary icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="openEditarProducto(${p.id})">
                    <i class="ph-bold ph-pencil"></i> Editar
                </button>
                <button class="btn btn-secondary icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem; background-color: var(--danger-color, #ff4d4f); border-color: var(--danger-color, #ff4d4f); color: white;" onclick="borrarProducto(${p.id})">
                    <i class="ph-bold ph-trash"></i> Borrar
                </button>
            </td>
        ` : '';

        return `
            <tr>
                <td><strong>${p.codigo}</strong></td>
                <td><strong>${p.nombre}</strong></td>
                <td><span class="badge-categoria" style="font-size: 0.70rem; font-weight: 500; line-height: 1.2; background: rgba(100, 116, 139, 0.1); color: var(--text-muted); border: 1px solid rgba(148, 163, 184, 0.25); padding: 2px 7px; border-radius: 4px; display: inline-block; white-space: nowrap;">${p.categoria}</span></td>
                <td style="font-weight: 700; color: var(--accent-green);">$${formatMoneda(p.precio, '')}</td>
                <td style="color: var(--text-muted);">$${formatMoneda(p.costo, '')}</td>
                <td><strong>${p.stock}</strong> unid</td>
                <td><span class="stock-badge ${badgeClass}">${badgeText}</span></td>
                ${actionTd}
            </tr>
        `;
    }).join('');
}

function filterInventarioTable(query) {
    const q = query.toLowerCase();
    const filtrados = productosCache.filter(p => 
        p.codigo.toLowerCase().includes(q) || 
        p.nombre.toLowerCase().includes(q) || 
        p.categoria.toLowerCase().includes(q)
    );
    renderInventarioTable(filtrados);
}

// --- EDICIÓN Y BORRADO DE PRODUCTO ---
async function borrarProducto(prodId) {
    const confirmado = await confirmarAccion({
        titulo: '¿Eliminar repuesto?',
        texto: '¿Estás seguro de que deseas eliminar este repuesto? (Los registros históricos se mantendrán por integridad)',
        icono: 'warning',
        textoConfirmar: 'Sí, eliminar repuesto',
        textoCancelar: 'Cancelar',
        esPeligroso: true
    });
    if (!confirmado) return;

    try {
        const res = await fetch(`/api/productos/${prodId}`, { method: 'DELETE' });
        const data = await res.json();
        if(res.ok && data.success) {
            mostrarToast("Producto eliminado exitosamente.", "success");
            loadInventario();
        } else {
            mostrarMensaje({ titulo: "Atención", texto: data.error || "Error al eliminar producto", icono: "error" });
        }
    } catch(e) {
        console.error(e);
        mostrarMensaje({ titulo: "Error de red", texto: "Error de conexión al eliminar producto", icono: "error" });
    }
}

function openEditarProducto(prodId) {
    const p = productosCache.find(item => item.id === prodId);
    if (!p) return;

    document.getElementById('edit-prod-id').value = p.id;
    document.getElementById('edit-prod-codigo').value = p.codigo;
    document.getElementById('edit-prod-nombre').value = p.nombre;
    document.getElementById('edit-prod-categoria').value = p.categoria;
    document.getElementById('edit-prod-precio').value = p.precio;
    document.getElementById('edit-prod-costo').value = p.costo;
    document.getElementById('edit-prod-stock').value = p.stock;
    document.getElementById('edit-prod-min-stock').value = p.min_stock;

    openModal('modal-editar-producto');
}

async function guardarEdicionProducto(e) {
    e.preventDefault();
    const id = document.getElementById('edit-prod-id').value;
    const codigo = document.getElementById('edit-prod-codigo').value;
    const nombre = document.getElementById('edit-prod-nombre').value;
    const categoria = document.getElementById('edit-prod-categoria').value;
    const precio = parseFloat(document.getElementById('edit-prod-precio').value);
    const costo = parseFloat(document.getElementById('edit-prod-costo').value);
    const stock = parseInt(document.getElementById('edit-prod-stock').value);
    const min_stock = parseInt(document.getElementById('edit-prod-min-stock').value);

    try {
        const res = await fetch(`/api/productos/${id}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo, nombre, categoria, precio, costo, stock, min_stock })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert('¡Repuesto actualizado con éxito!');
            closeModal('modal-editar-producto');
            loadInventario();
            loadDashboardStats();
        } else {
            alert(data.error || 'Error al actualizar repuesto.');
        }
    } catch (err) {
        console.error('Error:', err);
    }
}

// --- KARDEX / MOVIMIENTOS ---
async function loadMovimientos() {
    try {
        const res = await fetch('/api/movimientos');
        const movimientos = await res.json();
        movimientosCache = movimientos;
        renderMovimientosTable(movimientos);
    } catch (err) {
        console.error('Error al cargar movimientos:', err);
    }
}

function renderMovimientosTable(movs) {
    const tbody = document.getElementById('tbody-movimientos');
    if (!tbody) return;

    const userRole = window.CURRENT_USER_ROLE || '';
    const canEdit = ['Administrador', 'Encargado de Inventario', 'Gerente de Operaciones'].includes(userRole);
    const colSpanCount = canEdit ? 8 : 7;

    if (!Array.isArray(movs) || movs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${colSpanCount}" class="text-center text-muted">No hay movimientos registrados.</td></tr>`;
        return;
    }

    const reversed = [...movs].reverse();
    tbody.innerHTML = reversed.map(m => {
        const isEntrada = ['ENTRADA', 'COMPRA', 'INICIAL'].some(k => m.tipo.toUpperCase().includes(k));
        const badgeColor = isEntrada ? 'background: rgba(16, 185, 129, 0.15); color: var(--accent-green);' : 'background: rgba(239, 68, 68, 0.15); color: var(--accent-red);';
        const sign = isEntrada ? '+' : '-';

        const actionTd = canEdit ? `
            <td>
                <button class="btn btn-secondary icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="openEditarMovimiento(${m.id})">
                    <i class="ph-bold ph-pencil"></i> Editar
                </button>
            </td>
        ` : '';

        return `
            <tr>
                <td><strong>#MOV-${m.id}</strong></td>
                <td>${m.fecha}</td>
                <td><strong>${m.producto_codigo}</strong> - ${m.producto_nombre}</td>
                <td><span style="font-size: 0.78rem; font-weight: 700; padding: 0.25rem 0.5rem; border-radius: 6px; ${badgeColor}">${m.tipo}</span></td>
                <td><strong style="font-size: 1rem; color: ${isEntrada ? 'var(--accent-green)' : 'var(--accent-red)'};">${sign}${m.cantidad}</strong></td>
                <td style="color: var(--text-muted); font-size: 0.85rem;">${m.motivo}</td>
                <td><span style="font-size: 0.8rem; color: var(--text-dim);">${m.usuario}</span></td>
                ${actionTd}
            </tr>
        `;
    }).join('');
}

function filterMovimientosTable(query) {
    const q = query.toLowerCase();
    const filtrados = movimientosCache.filter(m => 
        m.producto_codigo.toLowerCase().includes(q) || 
        m.producto_nombre.toLowerCase().includes(q) || 
        m.tipo.toLowerCase().includes(q) || 
        m.motivo.toLowerCase().includes(q)
    );
    renderMovimientosTable(filtrados);
}

function toggleMotivoStockAlert() {
    const sel = document.getElementById('edit-mov-motivo-tipo');
    const alertBox = document.getElementById('alert-edit-mov-info');
    if (!sel || !alertBox) return;

    if (sel.value === 'DEFECTUOSO') {
        alertBox.className = 'alert alert-warning';
        alertBox.style.background = 'rgba(239, 68, 68, 0.15)';
        alertBox.style.color = 'var(--accent-red)';
        alertBox.style.border = '1px solid rgba(239, 68, 68, 0.3)';
        alertBox.innerHTML = `<i class="ph-bold ph-warning"></i> <strong>Modo Producto Defectuoso / Dañado:</strong> El registro en Kardex se actualizará con esta devolución, pero el stock disponible en catálogo <strong>NO se incrementará</strong> (el repuesto defectuoso no vuelve a estar a la venta).`;
    } else {
        alertBox.className = 'alert alert-info';
        alertBox.style.background = 'rgba(245, 158, 11, 0.12)';
        alertBox.style.color = 'var(--primary)';
        alertBox.style.border = '1px solid rgba(245, 158, 11, 0.3)';
        alertBox.innerHTML = `<i class="ph-bold ph-info"></i> <strong>Modo Ajuste por Producto de Más / Cantidad:</strong> Las existencias en el inventario actual <strong>SÁ se recalcularán y actualizarán</strong> en tiempo real.`;
    }
}

function openEditarMovimiento(movId) {
    const m = movimientosCache.find(item => item.id === movId);
    if (!m) return;

    const elId = document.getElementById('edit-mov-id');
    const elLbl = document.getElementById('lbl-edit-mov-id');
    const elNombre = document.getElementById('edit-mov-producto-nombre');
    const elTipo = document.getElementById('edit-mov-tipo');
    const elCant = document.getElementById('edit-mov-cantidad');
    const elMotivoTipo = document.getElementById('edit-mov-motivo-tipo');
    const elMotivo = document.getElementById('edit-mov-motivo');

    if (elId) elId.value = m.id;
    if (elLbl) elLbl.textContent = m.id;
    if (elNombre) elNombre.value = `${m.producto_codigo} - ${m.producto_nombre}`;
    if (elTipo) elTipo.value = m.tipo;
    if (elCant) elCant.value = m.cantidad;

    let textoLimpioMotivo = m.motivo || '';
    if (textoLimpioMotivo.toUpperCase().includes('DEFECTUOS')) {
        if (elMotivoTipo) elMotivoTipo.value = 'DEFECTUOSO';
        textoLimpioMotivo = textoLimpioMotivo.replace('[DEFECTUOSO]', '').trim();
    } else {
        if (elMotivoTipo) elMotivoTipo.value = 'AJUSTE_STOCK';
    }

    if (elMotivo) elMotivo.value = textoLimpioMotivo;

    toggleMotivoStockAlert();
    openModal('modal-editar-movimiento');
}

async function guardarEdicionMovimiento(e) {
    e.preventDefault();
    const movId = document.getElementById('edit-mov-id').value;
    const tipo = document.getElementById('edit-mov-tipo').value;
    const cantidad = parseInt(document.getElementById('edit-mov-cantidad').value);
    const motivo_tipo = document.getElementById('edit-mov-motivo-tipo').value;
    const motivoText = document.getElementById('edit-mov-motivo').value;

    const actualizar_stock = (motivo_tipo !== 'DEFECTUOSO');

    try {
        const res = await fetch(`/api/movimientos/${movId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                tipo,
                cantidad,
                motivo: motivoText,
                motivo_tipo: motivo_tipo,
                actualizar_stock: actualizar_stock
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert(`¡Movimiento #MOV-${movId} guardado con éxito!\n${data.mensaje}`);
            closeModal('modal-editar-movimiento');
            loadMovimientos();
            loadInventario();
            loadDashboardStats();
        } else {
            alert(data.error || 'Error al actualizar movimiento.');
        }
    } catch (err) {
        console.error('Error al editar movimiento:', err);
    }
}

async function guardarProducto(e) {
    e.preventDefault();
    const codigo = document.getElementById('prod-codigo').value;
    const nombre = document.getElementById('prod-nombre').value;
    const categoria = document.getElementById('prod-categoria').value;
    const precio = parseFloat(document.getElementById('prod-precio').value);
    const costo = parseFloat(document.getElementById('prod-costo').value);
    const stock = parseInt(document.getElementById('prod-stock').value);
    const min_stock = parseInt(document.getElementById('prod-min-stock').value);

    try {
        const res = await fetch('/api/productos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ codigo, nombre, categoria, precio, costo, stock, min_stock })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert('¡Repuesto guardado con éxito!');
            closeModal('modal-producto');
            document.getElementById('form-producto').reset();
            loadInventario();
            loadDashboardStats();
        } else {
            alert(data.error || 'Error al guardar repuesto.');
        }
    } catch (err) {
        console.error('Error:', err);
    }
}

// ==============================================================================
// MÁ"DULO 2: VENTAS (POS, HISTORIAL & COMPROBANTES)
// ==============================================================================

async function loadPOSProducts() {
    try {
        const res = await fetch('/api/productos');
        const productos = await res.json();
        productosCache = productos;
        renderPOSProductsGrid(productos);
    } catch (err) {
        console.error('Error al cargar catálogo POS:', err);
    }
}

function renderPOSProductsGrid(productos) {
    const grid = document.getElementById('pos-products-grid');
    if (!grid) return;

    if (!Array.isArray(productos) || productos.length === 0) {
        grid.innerHTML = `<div class="empty-state"><p>No hay repuestos disponibles.</p></div>`;
        return;
    }

    grid.innerHTML = productos.map(p => {
        const itemEnCarrito = cartPOS.find(i => i.producto_id === p.id);
        const qtyEnCarrito = itemEnCarrito ? itemEnCarrito.cantidad : 0;
        const stockDisponible = p.stock - qtyEnCarrito;
        const sinStock = stockDisponible <= 0;
        
        const clickAttr = sinStock ? '' : `onclick="addToCartPOS(${p.id})"`;
        const styleAttr = sinStock ? 'opacity: 0.4; cursor: not-allowed; filter: grayscale(100%);' : '';

        return `
            <div class="pos-product-card" style="${styleAttr}" ${clickAttr}>
                <div>
                    <span class="pos-prod-code">${p.codigo}</span>
                    <h4 class="pos-prod-name">${p.nombre}</h4>
                </div>
                <div>
                    <div class="pos-prod-price">$${formatMoneda(p.precio, '')}</div>
                    <div class="pos-prod-stock" style="${sinStock ? 'color: #ef4444; font-weight: bold;' : ''}">${sinStock ? '❌ AGOTADO' : `Stock: ${stockDisponible}`}</div>
                </div>
            </div>
        `;
    }).join('');
}

function refreshPOSProductsGrid() {
    const searchInput = document.getElementById('pos-search');
    if (searchInput && searchInput.value) {
        filterPOSProductsGrid(searchInput.value);
    } else {
        renderPOSProductsGrid(productosCache);
    }
}

function filterPOSProductsGrid(query) {
    const q = query.toLowerCase();
    const filtrados = productosCache.filter(p => 
        p.codigo.toLowerCase().includes(q) || 
        p.nombre.toLowerCase().includes(q)
    );
    renderPOSProductsGrid(filtrados);
}

function addToCartPOS(prodId) {
    const prod = productosCache.find(p => p.id === prodId);
    if (!prod) return;

    const itemEnCarrito = cartPOS.find(i => i.producto_id === prodId);

    if (itemEnCarrito) {
        if (itemEnCarrito.cantidad < prod.stock) {
            itemEnCarrito.cantidad++;
        } else {
            alert(`No puedes agregar más unidades de '${prod.nombre}'. Stock disponible: ${prod.stock}`);
        }
    } else {
        cartPOS.push({
            producto_id: prod.id,
            nombre: prod.nombre,
            precio: prod.precio,
            cantidad: 1,
            stock_max: prod.stock
        });
    }

    renderCartPOS();
    refreshPOSProductsGrid();
}

function updateCartQtyPOS(prodId, nuevaCantidad) {
    const cant = parseInt(nuevaCantidad);
    const item = cartPOS.find(i => i.producto_id === prodId);
    if (!item) return;

    if (isNaN(cant) || cant <= 0) {
        removeFromCartPOS(prodId);
        return;
    }

    if (cant > item.stock_max) {
        alert(`Stock disponible superado (${item.stock_max} unid).`);
        item.cantidad = item.stock_max;
    } else {
        item.cantidad = cant;
    }
    renderCartPOS();
    refreshPOSProductsGrid();
}

function removeFromCartPOS(prodId) {
    cartPOS = cartPOS.filter(i => i.producto_id !== prodId);
    renderCartPOS();
    refreshPOSProductsGrid();
}

function renderCartPOS() {
    const tbody = document.getElementById('pos-cart-tbody');
    const totalEl = document.getElementById('pos-cart-total');
    if (!tbody || !totalEl) return;

    if (cartPOS.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">El carrito está vacío.</td></tr>`;
        totalEl.textContent = '$0.00';
        return;
    }

    let totalSum = 0;

    tbody.innerHTML = cartPOS.map(item => {
        const subtotal = item.precio * item.cantidad;
        totalSum += subtotal;

        return `
            <tr>
                <td style="font-size: 0.8rem;">${item.nombre}</td>
                <td>
                    <input type="number" class="cart-qty-input" value="${item.cantidad}" min="1" max="${item.stock_max}" onchange="updateCartQtyPOS(${item.producto_id}, this.value)">
                </td>
                <td>$${formatMoneda(item.precio, '')}</td>
                <td style="font-weight: 700; color: var(--accent-green);">$${formatMoneda(subtotal, '')}</td>
                <td>
                    <button class="btn-remove-item" onclick="removeFromCartPOS(${item.producto_id})" title="Eliminar">&times;</button>
                </td>
            </tr>
        `;
    }).join('');

    totalEl.textContent = `$${formatMoneda(totalSum, '')}`;
}

async function procesarVentaPOS() {
    if (cartPOS.length === 0) {
        alert('Por favor agrega repuestos al carrito antes de procesar la venta.');
        return;
    }

    const cliente = document.getElementById('pos-cliente').value || 'Cliente General';
    const forma_pago = document.getElementById('pos-forma-pago').value || 'Efectivo';

    const itemsPayload = cartPOS.map(i => ({
        producto_id: i.producto_id,
        cantidad: i.cantidad
    }));

    try {
        const res = await fetch('/api/ventas', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ cliente, forma_pago, items: itemsPayload })
        });
        const data = await res.json();

        if (res.ok && data.success) {
            cartPOS = [];
            renderCartPOS();
            loadPOSProducts();
            loadDashboardStats();
            loadMovimientos();
            
            // Mostrar Comprobante marcando esNuevaVenta = true
            renderTicketComprobante(data.venta, true);
            openModal('modal-comprobante');
        } else {
            alert(data.error || 'Error al procesar la venta.');
        }
    } catch (err) {
        console.error('Error al procesar venta:', err);
    }
}

// --- HISTORIAL DE VENTAS (POS) ---
async function loadHistorialVentas() {
    try {
        const res = await fetch('/api/ventas');
        const ventas = await res.json();
        ventasCache = ventas;
        
        const ventasFisicas = ventas.filter(v => !v.codigo_venta || !v.codigo_venta.startsWith('WEB-'));
        renderHistorialVentasTable(ventasFisicas);
    } catch (err) {
        console.error('Error al cargar ventas:', err);
    }
}

function renderHistorialVentasTable(ventas) {
    const tbody = document.getElementById('tbody-historial-ventas');
    if (!tbody) return;

    if (!Array.isArray(ventas) || ventas.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No hay ventas registradas.</td></tr>`;
        return;
    }

    // Ordenar de más reciente a más antigua (ID descendente) para que las recientes salgan de primero
    const ordenadas = [...ventas].sort((a, b) => Number(b.id || 0) - Number(a.id || 0));
    tbody.innerHTML = ordenadas.map(v => `
        <tr>
            <td><strong>${v.codigo_venta}</strong></td>
            <td>${v.fecha}</td>
            <td>${v.cliente || 'Invitado'}</td>
            <td>${v.vendedor || 'Sistema Automático'}</td>
            <td><span style="font-size: 0.8rem; background: var(--bg-dark); padding: 0.2rem 0.5rem; border-radius: 4px;">${v.forma_pago}</span></td>
            <td style="font-weight: 700; color: var(--accent-green);">$${formatMoneda(v.total, '')}</td>
            <td style="display: flex; gap: 5px; align-items: center; flex-wrap: wrap;">
                <button class="btn btn-secondary icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="verComprobanteVenta(${v.id})">
                    <i class="ph-bold ph-receipt"></i> Ticket
                </button>
                ${v.estado === 'Anulada' ? '<span class="text-accent-red font-bold" style="font-size:0.8rem;"><i class="ph-bold ph-x-circle"></i> Anulada</span>' : `<button class="btn icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem; background: #f59e0b; border-color: #f59e0b; color: #000;" onclick="abrirModalDevolucion(${v.id})"><i class="ph-bold ph-arrow-counter-clockwise"></i> Devolución</button><button class="btn btn-danger icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="anularVenta(${v.id})"><i class="ph-bold ph-trash"></i> Anular</button>`}
            </td>
        </tr>
    `).join('');
}

function filterHistorialVentasTable(query) {
    const q = query.toLowerCase();
    const fisicas = ventasCache.filter(v => !v.codigo_venta || !v.codigo_venta.startsWith('WEB-'));
    const filtrados = fisicas.filter(v => 
        (v.codigo_venta && v.codigo_venta.toLowerCase().includes(q)) || 
        (v.cliente && v.cliente.toLowerCase().includes(q)) || 
        (v.vendedor && v.vendedor.toLowerCase().includes(q))
    );
    renderHistorialVentasTable(filtrados);
}

// --- GESTIÓN DE PEDIDOS WEB (TABLA pedidos_web) ---
let pedidosWebCache = [];

async function loadPedidosWeb() {
    try {
        const res = await fetch('/api/pedidos_web');
        const pedidos = await res.json();
        pedidosWebCache = pedidos;
        renderPedidosWebTable(pedidos);
    } catch (err) {
        console.error('Error al cargar pedidos web:', err);
    }
}

function renderPedidosWebTable(pedidos) {
    const tbody = document.getElementById('tbody-pedidos-web');
    if (!tbody) return;

    if (!Array.isArray(pedidos) || pedidos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted">No hay pedidos web registrados en el sistema.</td></tr>`;
        return;
    }

    tbody.innerHTML = pedidos.map(p => {
        const estadoBadge = p.estado === 'Anulado' 
            ? '<span class="text-accent-red font-bold" style="font-size:0.8rem;"><i class="ph-bold ph-x-circle"></i> Anulado</span>'
            : '<span style="font-size: 0.8rem; background: rgba(16, 185, 129, 0.2); color: #10b981; padding: 0.2rem 0.5rem; border-radius: 4px; font-weight: 600;">' + (p.estado || 'Completado') + '</span>';
        
        const formaEntregaBadge = p.formaEntrega === 'Retiro en Tienda'
            ? `<span style="font-size: 0.78rem; background: rgba(59, 130, 246, 0.15); color: #60a5fa; padding: 0.2rem 0.45rem; border-radius: 4px;"><i class="ph-bold ph-storefront"></i> ${p.formaEntrega}</span>`
            : `<span style="font-size: 0.78rem; background: rgba(245, 158, 11, 0.15); color: #fbbf24; padding: 0.2rem 0.45rem; border-radius: 4px;"><i class="ph-bold ph-truck"></i> ${p.formaEntrega || 'Envío a Domicilio'}</span>`;

        const direccionTexto = p.direccion_entrega ? `<div style="font-size: 0.75rem; color: #94a3b8; margin-top: 3px;" title="${p.direccion_entrega}"><i class="ph-bold ph-map-pin"></i> ${p.direccion_entrega}</div>` : '';
        const contactoTexto = (p.telefono ? `<div><i class="ph-bold ph-phone"></i> ${p.telefono}</div>` : '') + (p.email ? `<div style="font-size: 0.75rem; color: #94a3b8;"><i class="ph-bold ph-envelope"></i> ${p.email}</div>` : '');

        return `
            <tr>
                <td><strong style="color: #f97316;">${p.codigo}</strong></td>
                <td style="font-size: 0.82rem;">${p.fecha}</td>
                <td><strong>${p.cliente || 'Invitado'}</strong></td>
                <td style="font-size: 0.82rem;">${contactoTexto || '<span class="text-muted">N/D</span>'}</td>
                <td>
                    ${formaEntregaBadge}
                    ${direccionTexto}
                </td>
                <td><span style="font-size: 0.8rem; background: var(--bg-dark); padding: 0.2rem 0.5rem; border-radius: 4px;">${p.metodo || 'Efectivo'}</span></td>
                <td style="font-weight: 700; color: var(--accent-green); font-size: 0.95rem;">$${formatMoneda(p.total, '')}</td>
                <td>${estadoBadge}</td>
                <td style="display: flex; gap: 5px; align-items: center; flex-wrap: wrap;">
                    <button class="btn btn-secondary icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="verComprobantePedidoWeb(${p.id})">
                        <i class="ph-bold ph-receipt"></i> Ver Factura
                    </button>
                    ${p.estado === 'Anulado' ? '' : `
                    <button class="btn btn-danger icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="anularPedidoWeb(${p.id})">
                        <i class="ph-bold ph-trash"></i> Anular
                    </button>
                    `}
                </td>
            </tr>
        `;
    }).join('');
}

function filterPedidosWebTable(query) {
    const q = query.toLowerCase();
    const filtrados = pedidosWebCache.filter(p => 
        (p.codigo && p.codigo.toLowerCase().includes(q)) || 
        (p.cliente && p.cliente.toLowerCase().includes(q)) ||
        (p.email && p.email.toLowerCase().includes(q)) ||
        (p.telefono && p.telefono.toLowerCase().includes(q)) ||
        (p.direccion_entrega && p.direccion_entrega.toLowerCase().includes(q)) ||
        (p.formaEntrega && p.formaEntrega.toLowerCase().includes(q))
    );
    renderPedidosWebTable(filtrados);
}

function verComprobantePedidoWeb(pedidoId) {
    const pedido = pedidosWebCache.find(p => p.id === pedidoId);
    if (!pedido) {
        alert('Pedido web no encontrado en memoria.');
        return;
    }

    const adaptada = {
        id: pedido.id,
        codigo_venta: pedido.codigo,
        fecha: pedido.fecha,
        cliente: `${pedido.cliente || 'Invitado'}${pedido.telefono ? ' (Tel: ' + pedido.telefono + ')' : ''}`,
        vendedor: 'Tienda Online (Portal Web)',
        forma_pago: `${pedido.metodo || 'Efectivo'} | ${pedido.formaEntrega || 'Envío'}`,
        total: pedido.total,
        detalles: (pedido.detalles || []).map(d => ({
            producto_nombre: d.producto_nombre,
            cantidad: d.cantidad,
            precio_unitario: d.precioUnitario || d.precio_unitario || 0,
            subtotal: d.subtotal || 0
        }))
    };

    renderTicketComprobante(adaptada, false);
    openModal('modal-comprobante');
}

async function anularPedidoWeb(pedidoId) {
    const pedido = pedidosWebCache.find(p => p.id === pedidoId);
    const codigo = pedido ? pedido.codigo : `#${pedidoId}`;
    
    if (!confirm(`¿Estás seguro de que deseas anular el Pedido Web ${codigo}?\nSe restituirá el inventario de los productos y se registrará la reversión contable correspondiente.`)) {
        return;
    }

    try {
        const res = await fetch(`/api/pedidos_web/${pedidoId}/anular`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (data.success) {
            alert('✅ ' + data.mensaje);
            loadPedidosWeb();
            if (typeof loadPOSProducts === 'function') loadPOSProducts();
            if (typeof loadInventario === 'function') loadInventario();
            if (typeof loadDashboardStats === 'function') loadDashboardStats();
        } else {
            alert('❌ ' + (data.error || 'Error al anular el pedido web.'));
        }
    } catch (err) {
        console.error('Error al anular pedido web:', err);
        alert('Error de conexión al procesar la anulación.');
    }
}

function loadHistorialYWeb() {
    loadHistorialVentas();
    loadPedidosWeb();
}

// --- DEVOLUCION DE PRODUCTOS ---
async function abrirModalDevolucion(ventaId) {
    const venta = ventasCache.find(v => v.id === ventaId);
    if (!venta) {
        alert('Venta no encontrada en caché.');
        return;
    }

    document.getElementById('dev-venta-id').value = ventaId;
    document.getElementById('dev-codigo-venta').textContent = venta.codigo_venta;
    document.getElementById('dev-cliente').textContent = venta.cliente || 'Invitado';
    document.getElementById('dev-total-original').textContent = `$${formatMoneda(venta.total, '')}`;
    document.getElementById('dev-motivo-select').value = '';
    document.getElementById('dev-motivo-texto').value = '';
    document.getElementById('dev-actualiza-stock-check').checked = true;
    document.getElementById('dev-otro-container').style.display = 'none';
    document.getElementById('dev-alerta-defectuoso').style.display = 'none';
    document.getElementById('dev-select-all').checked = false;

    // Fetch already returned items for this sale
    let yaDevueltos = {};
    try {
        const resDev = await fetch(`/api/ventas/${ventaId}/productos_devueltos`);
        if (resDev.ok) {
            yaDevueltos = await resDev.json();
        }
    } catch (e) {
        console.error("Error fetching yaDevueltos:", e);
    }

    const detalles = venta.detalles || [];
    const tbody = document.getElementById('tbody-devolucion-items');
    
    if (detalles.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No hay detalles disponibles para esta venta.</td></tr>`;
        openModal('modal-devolucion');
        return;
    }

    tbody.innerHTML = detalles.map(d => {
        const yaDevuelto = yaDevueltos[d.producto_id] || 0;
        const disponible = d.cantidad - yaDevuelto;
        
        if (disponible <= 0) {
            return `
                <tr style="opacity: 0.6; background: rgba(0,0,0,0.05);">
                    <td><input type="checkbox" disabled></td>
                    <td><strong style="text-decoration: line-through;">${d.producto_nombre}</strong></td>
                    <td style="text-align: center;">${d.cantidad}</td>
                    <td style="text-align: center; color: var(--accent-red); font-weight: bold;">${yaDevuelto}</td>
                    <td style="text-align: center;">0</td>
                    <td><input type="number" class="form-control" disabled value="0" style="width: 65px; padding: 0.2rem 0.4rem; text-align: center; font-size: 0.85rem;"></td>
                    <td style="font-weight: 600; color: var(--text-muted);">$0.00</td>
                </tr>
            `;
        }

        return `
            <tr>
                <td><input type="checkbox" class="dev-item-check" data-producto-id="${d.producto_id}" data-precio="${d.precio_unitario}" data-max="${disponible}" onchange="calcularTotalDevolucion()"></td>
                <td><strong>${d.producto_nombre}</strong></td>
                <td style="text-align: center;">${d.cantidad}</td>
                <td style="text-align: center; color: ${yaDevuelto > 0 ? 'var(--warning)' : 'var(--text-muted)'};">${yaDevuelto > 0 ? yaDevuelto : '-'}</td>
                <td style="text-align: center; font-weight: 600;">${disponible}</td>
                <td><input type="number" class="form-control dev-item-qty" min="1" max="${disponible}" value="${disponible}" style="width: 65px; padding: 0.2rem 0.4rem; text-align: center; font-size: 0.85rem;" onchange="calcularTotalDevolucion()" oninput="calcularTotalDevolucion()"></td>
                <td class="dev-item-subtotal" style="font-weight: 600; color: var(--warning, #f59e0b);">$0.00</td>
            </tr>
        `;
    }).join('');

    calcularTotalDevolucion();
    openModal('modal-devolucion');
}

function cambiarMotivoDevolucion() {
    const sel = document.getElementById('dev-motivo-select').value;
    const otroContainer = document.getElementById('dev-otro-container');
    const alertaDefectuoso = document.getElementById('dev-alerta-defectuoso');
    const txt = document.getElementById('dev-motivo-texto');

    otroContainer.style.display = 'none';
    alertaDefectuoso.style.display = 'none';
    txt.required = false;

    if (sel === 'otro') {
        otroContainer.style.display = 'block';
        txt.required = true;
    } else if (sel === 'defectuoso') {
        alertaDefectuoso.style.display = 'block';
    }
}

function toggleSelectAllDevolucion(masterCheckbox) {
    const checks = document.querySelectorAll('.dev-item-check');
    checks.forEach(cb => { cb.checked = masterCheckbox.checked; });
    calcularTotalDevolucion();
}

function calcularTotalDevolucion() {
    const rows = document.querySelectorAll('#tbody-devolucion-items tr');
    let total = 0;
    rows.forEach(row => {
        const cb = row.querySelector('.dev-item-check');
        const qtyInput = row.querySelector('.dev-item-qty');
        const subtotalCell = row.querySelector('.dev-item-subtotal');
        if (!cb || !qtyInput || !subtotalCell) return;

        if (cb.checked) {
            const precio = parseFloat(cb.dataset.precio) || 0;
            const maxQty = parseInt(cb.dataset.max) || 0;
            let qty = parseInt(qtyInput.value) || 0;
            if (qty > maxQty) { qty = maxQty; qtyInput.value = maxQty; }
            if (qty < 1) { qty = 1; qtyInput.value = 1; }
            const subtotal = precio * qty;
            subtotalCell.textContent = `$${formatMoneda(subtotal, '')}`;
            total += subtotal;
        } else {
            subtotalCell.textContent = '$0.00';
        }
    });
    document.getElementById('dev-total-devolver').textContent = `$${formatMoneda(total, '')}`;
}

async function procesarDevolucion() {
    const ventaId = document.getElementById('dev-venta-id').value;
    const select = document.getElementById('dev-motivo-select').value;
    const textoOtro = document.getElementById('dev-motivo-texto').value.trim();
    
    if (!select) {
        alert('Debes seleccionar la causa / motivo de la devolución.');
        return;
    }

    let motivoFinal = '';
    let actualizaStock = true;

    if (select === 'exceso') {
        motivoFinal = 'Producto agregado de más / Ajuste de cantidad';
        actualizaStock = true;
    } else if (select === 'defectuoso') {
        motivoFinal = 'Producto Defectuoso / Dañado';
        actualizaStock = false;
    } else if (select === 'otro') {
        if (!textoOtro) {
            alert('Debes especificar la justificación para este motivo.');
            return;
        }
        motivoFinal = 'Otro motivo: ' + textoOtro;
        actualizaStock = document.getElementById('dev-actualiza-stock-check').checked;
    }

    const items = [];
    const rows = document.querySelectorAll('#tbody-devolucion-items tr');
    rows.forEach(row => {
        const cb = row.querySelector('.dev-item-check');
        const qtyInput = row.querySelector('.dev-item-qty');
        if (cb && cb.checked && qtyInput) {
            items.push({
                producto_id: parseInt(cb.dataset.productoId),
                cantidad: parseInt(qtyInput.value) || 0
            });
        }
    });

    if (items.length === 0) {
        alert('Debes seleccionar al menos un producto para devolver.');
        return;
    }

    const mnsjStock = actualizaStock ? "(SÍ volverán al stock del catálogo)" : "(NO volverán al stock del catálogo)";
    const confirmado = await confirmarAccion({
        titulo: '¿Procesar Devolución?',
        texto: `Productos a devolver: ${items.length} ${mnsjStock}\nTotal a descontar: ${document.getElementById('dev-total-devolver').textContent}\nMotivo: ${motivoFinal}`,
        icono: 'question',
        textoConfirmar: 'Confirmar Devolución',
        textoCancelar: 'Cancelar'
    });
    if (!confirmado) return;

    try {
        const res = await fetch(`/api/ventas/${ventaId}/devolucion`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ motivo: motivoFinal, items: items, actualiza_stock: actualizaStock })
        });
        const data = await res.json();

        if (data.success) {
            alert('✅ ' + data.mensaje);
            closeModal('modal-devolucion');
            loadHistorialVentas();
            if (typeof loadInventario === 'function') loadInventario();
        } else {
            alert('❌ Error: ' + data.error);
        }
    } catch (err) {
        alert('Error de conexión al procesar la devolución.');
        console.error(err);
    }
}

function verComprobanteVenta(ventaId) {
    const venta = ventasCache.find(v => v.id === ventaId);
    if (venta) {
        renderTicketComprobante(venta, false);
        openModal('modal-comprobante');
    } else {
        console.error('Error: Venta no encontrada en caché.');
        alert('No se pudo cargar el comprobante.');
    }
}

function renderTicketComprobante(v, esNuevaVenta = false) {
    ventaSeleccionadaActual = v;
    const container = document.getElementById('ticket-print-area');
    const footer = document.getElementById('footer-modal-comprobante');
    if (!container) return;

    let bannerExito = '';
    if (esNuevaVenta) {
        bannerExito = `
            <div class="ticket-no-print" style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); font-weight: 700; padding: 0.8rem 1rem; border-radius: 8px; margin-bottom: 1.25rem; text-align: center; font-size: 0.92rem;">
                <i class="ph-bold ph-check-circle" style="font-size: 1.2rem; vertical-align: middle;"></i> ¡Venta ${v.codigo_venta} procesada exitosamente por un total de $${formatMoneda(v.total, '')}!
            </div>
        `;
    }

    let itemsHtml = '';
    v.detalles.forEach(d => {
        const pu = formatMoneda(d.precio_unitario, '');
        const st = formatMoneda(d.subtotal, '');
        itemsHtml += `
            <tr style="border-bottom: 1px dashed #cbd5e1;">
                <td style="padding: 0.4rem 0; font-size: 0.85rem; color: #1e293b;">
                    <strong>${d.producto_nombre}</strong>
                </td>
                <td style="padding: 0.4rem 0; text-align: center; font-size: 0.85rem; color: #1e293b;">${d.cantidad}</td>
                <td style="padding: 0.4rem 0; text-align: right; font-size: 0.85rem; color: #1e293b;">$${pu}</td>
                <td style="padding: 0.4rem 0; text-align: right; font-size: 0.85rem; font-weight: 700; color: #0f172a;">$${st}</td>
            </tr>
        `;
    });

    container.innerHTML = `
        ${bannerExito}
        <div id="ticket-receipt-card" style="font-family: monospace, sans-serif; background: #ffffff; color: #0f172a; padding: 1.5rem; border-radius: 8px; max-width: 750px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.15); max-height: 55vh; overflow-y: auto;">
            <div style="text-align: center; border-bottom: 2px dashed #94a3b8; padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                <h2 style="font-size: 1.3rem; margin-bottom: 0.2rem; color: #0f172a;">JEHOVÁ  JIREH</h2>
                <div style="font-size: 0.8rem; font-weight: 700; color: #475569;">MOTO REPUESTOS - MASATEPE</div>
                <div style="font-size: 0.75rem; color: #64748b;">Atención de Calidad y Repuestos Originales</div>
                <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.2rem;">Tel: +505 8899-0000 | Masatepe, Masaya</div>
            </div>

            <div style="font-size: 0.8rem; margin-bottom: 0.75rem; line-height: 1.4;">
                <div><strong>COMPROBANTE DE VENTA:</strong> ${v.codigo_venta}</div>
                <div><strong>Fecha:</strong> ${v.fecha}</div>
                <div><strong>Cliente:</strong> ${v.cliente || 'Cliente General'}</div>
                <div><strong>Vendedor:</strong> ${v.vendedor || 'Sistema'}</div>
                <div><strong>Forma de Pago:</strong> ${v.forma_pago || 'Efectivo'}</div>
            </div>

            <table style="width: 100%; border-collapse: collapse; margin-bottom: 0.75rem;">
                <thead>
                    <tr style="border-bottom: 1px solid #0f172a; text-align: left; font-size: 0.75rem; color: #475569;">
                        <th>DETALLE</th>
                        <th style="text-align: center;">CANT</th>
                        <th style="text-align: right;">P.U</th>
                        <th style="text-align: right;">TOTAL</th>
                    </tr>
                </thead>
                <tbody>
                    ${itemsHtml}
                </tbody>
            </table>

            <div style="border-top: 2px dashed #94a3b8; padding-top: 0.5rem; text-align: right; font-size: 1.1rem; font-weight: 800; color: #0f172a;">
                TOTAL TOTAL: $${formatMoneda(v.total, '')}
            </div>

            <div style="text-align: center; font-size: 0.75rem; color: #64748b; margin-top: 1rem; border-top: 1px solid #e2e8f0; padding-top: 0.5rem;">
                ¡Gracias por su compra en Jehová Jireh! 🙏 <br>
                Conserve este comprobante para cualquier reclamo.
            </div>
        </div>
    `;

    if (footer) {
        if (esNuevaVenta) {
            footer.innerHTML = `
                <button type="button" class="btn btn-secondary" onclick="concluirSinImprimirTicket('${v.codigo_venta}')">
                    <i class="ph-bold ph-x-circle"></i> No Imprimir Ticket
                </button>
                <button type="button" class="btn btn-primary" onclick="imprimirTicketActual()">
                    <i class="ph-bold ph-printer"></i> Imprimir Ticket
                </button>
            `;
        } else {
            footer.innerHTML = `
                <button type="button" class="btn btn-secondary" onclick="closeModal('modal-comprobante')">Cerrar</button>
                <button type="button" class="btn btn-primary" onclick="imprimirTicketActual()">
                    <i class="ph-bold ph-printer"></i> Imprimir Ticket
                </button>
            `;
        }
    }
}

function concluirSinImprimirTicket(codigoVenta) {
    alert(`🎉 ¡Venta ${codigoVenta} realizada exitosamente!`);
    closeModal('modal-comprobante');
}

function imprimirTicketActual() {
    const v = ventaSeleccionadaActual;
    const printArea = document.getElementById('ticket-print-area');

    let ticketHtml = '';

    if (v && v.detalles && Array.isArray(v.detalles) && v.detalles.length > 0) {
        let itemsRows = '';
        v.detalles.forEach(d => {
            const pu = formatMoneda(d.precio_unitario, '');
            const st = formatMoneda(d.subtotal, '');
            itemsRows += `
                <tr>
                    <td style="padding: 4px 2px; font-size: 11px; text-align: left; vertical-align: top; word-break: break-word;">
                        <strong>${d.producto_nombre || 'Producto'}</strong>
                    </td>
                    <td style="padding: 4px 2px; text-align: center; font-size: 11px; vertical-align: top; white-space: nowrap;">${d.cantidad}</td>
                    <td style="padding: 4px 2px; text-align: right; font-size: 11px; vertical-align: top; white-space: nowrap;">$${pu}</td>
                    <td style="padding: 4px 2px; text-align: right; font-size: 11px; font-weight: bold; vertical-align: top; white-space: nowrap;">$${st}</td>
                </tr>
            `;
        });

        const totalFormatted = formatMoneda(v.total, '');

        ticketHtml = `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Ticket - ${v.codigo_venta}</title>
    <style>
        @page {
            size: auto;
            margin: 4mm;
        }
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Courier New', Courier, monospace, monospace;
            color: #000;
            background: #fff;
            width: 100%;
            max-width: 320px;
            margin: 0 auto;
            padding: 10px 4px;
        }
        .header {
            text-align: center;
            border-bottom: 2px dashed #000;
            padding-bottom: 8px;
            margin-bottom: 8px;
        }
        .header h2 {
            font-size: 16px;
            font-weight: 900;
            margin-bottom: 2px;
            letter-spacing: 0.5px;
        }
        .header .sub {
            font-size: 11px;
            font-weight: 700;
        }
        .header .contact {
            font-size: 10px;
            color: #222;
            margin-top: 2px;
        }
        .meta-info {
            font-size: 11px;
            margin-bottom: 8px;
            line-height: 1.45;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 8px;
        }
        th {
            border-bottom: 1px solid #000;
            font-size: 10px;
            font-weight: bold;
            padding: 4px 2px;
            color: #000;
        }
        td {
            border-bottom: 1px dashed #bbb;
        }
        .total-box {
            border-top: 2px dashed #000;
            border-bottom: 2px dashed #000;
            padding: 6px 0;
            text-align: right;
            font-size: 14px;
            font-weight: 900;
            margin-top: 4px;
        }
        .footer {
            text-align: center;
            font-size: 10px;
            color: #333;
            margin-top: 10px;
            padding-top: 6px;
            border-top: 1px dashed #aaa;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <div class="header">
        <h2>JEHOVÁ JIREH</h2>
        <div class="sub">MOTO REPUESTOS - MASATEPE</div>
        <div class="contact">Atención de Calidad y Repuestos Originales</div>
        <div class="contact">Tel: +505 8899-0000 | Masatepe, Masaya</div>
    </div>

    <div class="meta-info">
        <div><strong>COMPROBANTE DE VENTA:</strong> ${v.codigo_venta}</div>
        <div><strong>Fecha:</strong> ${v.fecha}</div>
        <div><strong>Cliente:</strong> ${v.cliente || 'Cliente General'}</div>
        <div><strong>Vendedor:</strong> ${v.vendedor || 'Sistema'}</div>
        <div><strong>Forma de Pago:</strong> ${v.forma_pago || 'Efectivo'}</div>
    </div>

    <table>
        <thead>
            <tr>
                <th style="text-align: left;">DETALLE</th>
                <th style="text-align: center; width: 38px;">CANT</th>
                <th style="text-align: right; width: 62px;">P.U</th>
                <th style="text-align: right; width: 68px;">TOTAL</th>
            </tr>
        </thead>
        <tbody>
            ${itemsRows}
        </tbody>
    </table>

    <div class="total-box">
        TOTAL TOTAL: $${totalFormatted}
    </div>

    <div class="footer">
        ¡Gracias por su compra en Jehová Jireh! 🙏<br>
        Conserve este comprobante para cualquier reclamo.
    </div>
</body>
</html>`;
    } else if (printArea) {
        const clon = printArea.cloneNode(true);
        const elementosNoPrint = clon.querySelectorAll('.ticket-no-print, button, .modal-close');
        elementosNoPrint.forEach(el => el.remove());
        ticketHtml = `<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Ticket de Venta</title>
    <style>
        @page { size: auto; margin: 4mm; }
        body { font-family: monospace, sans-serif; color: #000; background: #fff; width: 100%; max-width: 320px; margin: 0 auto; padding: 10px 4px; }
        div[style*="overflow"] { max-height: none !important; overflow: visible !important; box-shadow: none !important; }
    </style>
</head>
<body>
    ${clon.innerHTML}
</body>
</html>`;
    }

    if (ticketHtml) {
        let printIframe = document.getElementById('ticket-print-iframe');
        if (!printIframe) {
            printIframe = document.createElement('iframe');
            printIframe.id = 'ticket-print-iframe';
            printIframe.style.position = 'fixed';
            printIframe.style.right = '0';
            printIframe.style.bottom = '0';
            printIframe.style.width = '0';
            printIframe.style.height = '0';
            printIframe.style.border = '0';
            printIframe.style.visibility = 'hidden';
            document.body.appendChild(printIframe);
        }

        const doc = printIframe.contentWindow.document;
        doc.open();
        doc.write(ticketHtml);
        doc.close();

        setTimeout(() => {
            try {
                printIframe.contentWindow.focus();
                printIframe.contentWindow.print();
            } catch (err) {
                console.warn('Fallback a window.print() debido a restricción de iframe:', err);
                window.print();
            }
        }, 250);
    } else {
        window.print();
    }
}

// ==============================================================================
// MÁ"DULO 3: COMPRAS Y PROVEEDORES
// ==============================================================================

async function toggleProveedorEstado(id, activar) {
    const accion = activar ? 'activar' : 'inactivar';
    const confirmado = await confirmarAccion({
        titulo: `¿Deseas ${accion} este proveedor?`,
        texto: `¿Estás seguro de que deseas ${accion} este proveedor en el catálogo?`,
        icono: 'question',
        textoConfirmar: `Sí, ${accion}`,
        textoCancelar: 'Cancelar',
        esPeligroso: !activar
    });
    if (!confirmado) return;

    try {
        const res = await fetch(`/api/proveedores/${id}/estado`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ activo: activar })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            mostrarToast(`Proveedor ${activar ? 'activado' : 'inactivado'} correctamente.`, 'success');
            loadComprasYProveedores();
        } else {
            mostrarMensaje({ titulo: 'Error', texto: data.error || 'Error al cambiar estado del proveedor.', icono: 'error' });
        }
    } catch(err) {
        console.error(err);
        mostrarMensaje({ titulo: 'Error de red', texto: 'Error de conexión.', icono: 'error' });
    }
}

let comprasCache = [];
let compraActualSeleccionada = null;
let plantillaFacturaActual = 'vini';
let compraItemsActuales = [];

async function loadComprasYProveedores() {
    try {
        const [resCompras, resProvs] = await Promise.all([
            fetch('/api/compras').then(r => r.json()),
            fetch('/api/proveedores').then(r => r.json())
        ]);

        if (Array.isArray(resProvs)) proveedoresCache = resProvs;
        if (Array.isArray(resCompras)) comprasCache = resCompras;

        // Render Compras
        const tbodyCompras = document.getElementById('tbody-compras');
        if (tbodyCompras) {
            if (!Array.isArray(resCompras) || resCompras.length === 0) {
                tbodyCompras.innerHTML = `<tr><td colspan="5" class="text-center text-muted" style="padding: 1.5rem;">No hay compras registradas.</td></tr>`;
            } else {
                tbodyCompras.innerHTML = resCompras.map(c => {
                    const isVini = (c.proveedor_nombre || '').toUpperCase().includes('VINI');
                    const badgeProv = isVini 
                        ? `<span class="badge" style="background: rgba(220, 38, 38, 0.1); color: #dc2626; border: 1px solid rgba(220, 38, 38, 0.25); font-weight: 600; font-size: 0.72rem; padding: 2px 6px; border-radius: 4px; margin-left: 6px;">VINI</span>`
                        : '';
                    const numFactura = c.numero_factura_proveedor 
                        ? `<span style="font-size:0.75rem; color:var(--text-muted); display:block; font-family: monospace;">Fac: ${c.numero_factura_proveedor}</span>` 
                        : '';
                    const codigoVisual = c.codigo_compra || `COM-#${c.id}`;
                    return `
                    <tr>
                        <td><strong>${codigoVisual}</strong>${numFactura}</td>
                        <td>${c.fecha_formateada || c.fecha}</td>
                        <td><strong>${c.proveedor_nombre}</strong>${badgeProv}</td>
                        <td style="font-weight: 700; color: var(--primary);">$${formatMoneda(c.total, '')}</td>
                        <td style="text-align: center; white-space: nowrap;">
                            <button class="btn btn-secondary btn-sm" onclick="verFacturaCompra(${c.id})" title="Ver factura oficial desglosada" style="padding: 0.3rem 0.65rem; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 5px;">
                                <i class="ph-bold ph-receipt"></i> Ver Factura
                            </button>
                            <button class="btn btn-danger btn-sm" onclick="eliminarCompra(${c.id}, '${codigoVisual}')" title="Eliminar compra registrada por error y revertir stock" style="padding: 0.3rem 0.65rem; font-size: 0.8rem; display: inline-flex; align-items: center; gap: 5px; margin-left: 5px;">
                                <i class="ph-bold ph-trash"></i> Eliminar
                            </button>
                        </td>
                    </tr>
                `}).join('');
            }
        }

        // Render Proveedores
        const tbodyProvs = document.getElementById('tbody-proveedores');
        if (tbodyProvs) {
            if (!Array.isArray(resProvs) || resProvs.length === 0) {
                tbodyProvs.innerHTML = `<tr><td colspan="4" class="text-center text-muted" style="padding: 1.5rem;">No hay proveedores.</td></tr>`;
            } else {
                tbodyProvs.innerHTML = resProvs.map(p => {
                    const rowStyle = p.activo ? '' : 'style="opacity: 0.5; filter: grayscale(100%);"';
                    const btnClass = p.activo ? 'btn-danger' : 'btn-success';
                    const btnIcon = p.activo ? 'ph-x-circle' : 'ph-check-circle';
                    const btnText = p.activo ? 'Inactivar' : 'Activar';
                    return `
                    <tr ${rowStyle}>
                        <td><strong>${p.nombre}</strong> ${!p.activo ? '<span class="badge" style="background:#dc3545;color:white;font-size:10px;padding:2px 4px;border-radius:4px;margin-left:5px;">Inactivo</span>' : ''}</td>
                        <td>${p.contacto || 'N/A'}</td>
                        <td>${p.telefono || 'N/A'}</td>
                        <td style="display: flex; gap: 5px;">
                            <button class="btn btn-secondary btn-sm" onclick="editarProveedor(${p.id})" style="padding: 0.25rem 0.5rem; font-size: 0.875rem;">
                                <i class="ph-bold ph-pencil-simple"></i> Editar
                            </button>
                            <button class="btn ${btnClass} btn-sm" onclick="toggleProveedorEstado(${p.id}, ${!p.activo})" style="padding: 0.25rem 0.5rem; font-size: 0.875rem;">
                                <i class="ph-bold ${btnIcon}"></i> ${btnText}
                            </button>
                        </td>
                    </tr>
                `}).join('');
            }
        }

        // Actualizar badges de conteo
        const badgeCompras = document.getElementById('compras-badge-conteo');
        if (badgeCompras) {
            const n = Array.isArray(resCompras) ? resCompras.length : 0;
            badgeCompras.textContent = `${n} compra${n === 1 ? '' : 's'}`;
        }
        const badgeProvs = document.getElementById('proveedores-badge-conteo');
        if (badgeProvs) {
            const m = Array.isArray(resProvs) ? resProvs.length : 0;
            badgeProvs.textContent = `${m} proveedor${m === 1 ? '' : 'es'}`;
        }

    } catch (err) {
        console.error('Error compras y proveedores:', err);
    }
}

async function eliminarCompra(compraId, codigoCompra) {
    const cod = codigoCompra || `COM-#${compraId}`;
    const confirmado = await confirmarAccion({
        titulo: '¿Eliminar compra?',
        texto: `¿Estás seguro de que deseas eliminar la compra <b>${cod}</b>?<br><br><span style="color:#dc2626;">⚠️ Esta acción descontará automáticamente del inventario el stock de todos los repuestos que ingresaron en esta compra y cancelará el asiento contable asociado.</span>`,
        icono: 'warning',
        textoConfirmar: 'Sí, eliminar y revertir',
        textoCancelar: 'Cancelar',
        esPeligroso: true
    });

    if (!confirmado) return;

    try {
        const res = await fetch(`/api/compras/${compraId}`, {
            method: 'DELETE',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await res.json();
        if (res.ok && data.success) {
            if (typeof mostrarToast === 'function') {
                mostrarToast(`Compra ${cod} eliminada y stock revertido correctamente.`, 'success');
            } else {
                alert(`Compra ${cod} eliminada y stock revertido correctamente.`);
            }
            loadComprasYProveedores();
            if (typeof loadDashboardStats === 'function') loadDashboardStats();
            if (typeof loadMovimientos === 'function') loadMovimientos();
            if (typeof loadProductos === 'function') loadProductos();
            if (typeof loadInventario === 'function') loadInventario();
        } else {
            if (typeof mostrarMensaje === 'function') {
                mostrarMensaje({ titulo: 'No se pudo eliminar la compra', texto: data.error || 'Ocurrió un error inesperado al eliminar.', icono: 'error' });
            } else {
                alert(data.error || 'Error al eliminar la compra.');
            }
        }
    } catch (err) {
        console.error('Error al eliminar compra:', err);
        if (typeof mostrarMensaje === 'function') {
            mostrarMensaje({ titulo: 'Error de red', texto: 'No se pudo conectar con el servidor para eliminar la compra.', icono: 'error' });
        } else {
            alert('Error de red al eliminar la compra.');
        }
    }
}

function verificarProveedorSeleccionado(provId) {
    const prov = (proveedoresCache || []).find(p => p.id === parseInt(provId));
    const aviso = document.getElementById('compra-proveedor-aviso');
    const inputFactura = document.getElementById('compra-numero-factura');
    if (prov && (prov.nombre || '').toUpperCase().includes('VINI')) {
        if (aviso) aviso.style.display = 'flex';
        if (inputFactura && !inputFactura.value) inputFactura.placeholder = 'Ej: A-00045946';
    } else {
        if (aviso) aviso.style.display = 'none';
        if (inputFactura) inputFactura.placeholder = 'Ej: F-10294';
    }
}

function onCompraProductoSeleccionado(prodId) {
    const selProd = document.getElementById('compra-producto-id');
    const inputCosto = document.getElementById('compra-costo-unitario');
    if (!selProd || !inputCosto) return;

    const opt = selProd.selectedOptions && selProd.selectedOptions[0];
    if (opt && opt.dataset && opt.dataset.costo !== undefined) {
        const costo = parseFloat(opt.dataset.costo);
        inputCosto.value = (!isNaN(costo) && costo > 0) ? costo.toFixed(2) : '';
    } else {
        const prod = (productosCache || []).find(p => p.id === parseInt(prodId));
        if (prod && prod.costo !== undefined) {
            const costo = parseFloat(prod.costo);
            inputCosto.value = (!isNaN(costo) && costo > 0) ? costo.toFixed(2) : '';
        }
    }
}

function populateCompraSelects() {
    const selProv = document.getElementById('compra-proveedor-id');
    const selProd = document.getElementById('compra-producto-id');

    if (selProv) {
        selProv.innerHTML = proveedoresCache.filter(p => p.activo).map(p => `<option value="${p.id}">${p.nombre}</option>`).join('');
        if (selProv.value) verificarProveedorSeleccionado(selProv.value);
    }

    const llenarSelectProductos = (lista) => {
        if (!selProd) return;
        if (!Array.isArray(lista) || lista.length === 0) {
            selProd.innerHTML = '<option value="">No hay repuestos disponibles</option>';
            return;
        }
        selProd.innerHTML = lista.map(p => {
            const costoRef = typeof p.costo === 'number' ? p.costo : (parseFloat(p.costo) || 0);
            return `<option value="${p.id}" data-costo="${costoRef}" data-stock="${p.stock}" data-codigo="${p.codigo || ''}" data-nombre="${p.nombre}">${p.codigo ? p.codigo + ' - ' : ''}${p.nombre} (Stock actual: ${p.stock})</option>`;
        }).join('');
        if (selProd.value) {
            onCompraProductoSeleccionado(selProd.value);
        }
    };

    if (productosCache && productosCache.length > 0) {
        llenarSelectProductos(productosCache);
    } else {
        fetch('/api/productos')
            .then(r => r.json())
            .then(prods => {
                if (Array.isArray(prods)) {
                    productosCache = prods;
                    llenarSelectProductos(prods);
                }
            })
            .catch(e => console.error('Error al cargar repuestos para modal de compra:', e));
    }

    // Reiniciar lista de repuestos seleccionados al abrir
    compraItemsActuales = [];
    renderTablaCompraItems();
}

function agregarItemACompra() {
    const selProd = document.getElementById('compra-producto-id');
    const inputCant = document.getElementById('compra-cantidad');
    const inputCosto = document.getElementById('compra-costo-unitario');

    if (!selProd || !selProd.value) {
        if (typeof mostrarToast === 'function') {
            mostrarToast('Por favor selecciona un repuesto válido.', 'warning');
        } else {
            alert('Por favor selecciona un repuesto válido.');
        }
        return;
    }

    const prodId = parseInt(selProd.value);
    const cantidad = parseInt(inputCant.value);
    if (isNaN(cantidad) || cantidad <= 0) {
        if (typeof mostrarToast === 'function') {
            mostrarToast('La cantidad debe ser mayor a 0.', 'warning');
        } else {
            alert('La cantidad debe ser mayor a 0.');
        }
        if (inputCant) inputCant.focus();
        return;
    }

    let costo_unitario = parseFloat(inputCosto.value);
    const prodInfo = (productosCache || []).find(p => p.id === prodId);
    const prodNombre = prodInfo ? prodInfo.nombre : (selProd.options[selProd.selectedIndex]?.text || 'Repuesto');
    const prodCodigo = prodInfo ? (prodInfo.codigo || '') : '';
    const stockActual = prodInfo ? parseInt(prodInfo.stock || 0) : 0;

    if (isNaN(costo_unitario) || costo_unitario < 0) {
        costo_unitario = prodInfo && prodInfo.costo ? parseFloat(prodInfo.costo) : 0;
    }

    // Si ya existe en la lista, sumar la cantidad
    const itemExistente = compraItemsActuales.find(item => item.producto_id === prodId);
    if (itemExistente) {
        itemExistente.cantidad += cantidad;
        if (costo_unitario > 0) itemExistente.costo_unitario = costo_unitario;
        itemExistente.subtotal = itemExistente.cantidad * itemExistente.costo_unitario;
        if (typeof mostrarToast === 'function') {
            mostrarToast(`Se sumaron +${cantidad} unidades a ${prodNombre}.`, 'info');
        }
    } else {
        compraItemsActuales.push({
            producto_id: prodId,
            codigo: prodCodigo,
            nombre: prodNombre,
            stock_actual: stockActual,
            cantidad: cantidad,
            costo_unitario: costo_unitario,
            subtotal: cantidad * costo_unitario
        });
        if (typeof mostrarToast === 'function') {
            mostrarToast(`Añadido: ${prodNombre}`, 'success');
        }
    }

    renderTablaCompraItems();

    // Mantener cantidad en 1 para la siguiente selección
    if (inputCant) inputCant.value = 1;
}

function eliminarItemDeCompra(index) {
    if (index >= 0 && index < compraItemsActuales.length) {
        const item = compraItemsActuales[index];
        compraItemsActuales.splice(index, 1);
        renderTablaCompraItems();
        if (typeof mostrarToast === 'function') {
            mostrarToast(`Se quitó ${item.nombre} de la compra.`, 'info');
        }
    }
}

function actualizarCantidadItemCompra(index, nuevaCantidad) {
    const cant = parseInt(nuevaCantidad);
    if (index >= 0 && index < compraItemsActuales.length && !isNaN(cant) && cant > 0) {
        compraItemsActuales[index].cantidad = cant;
        compraItemsActuales[index].subtotal = cant * compraItemsActuales[index].costo_unitario;
        renderTablaCompraItems();
    }
}

function actualizarCostoItemCompra(index, nuevoCosto) {
    const costo = parseFloat(nuevoCosto);
    if (index >= 0 && index < compraItemsActuales.length && !isNaN(costo) && costo >= 0) {
        compraItemsActuales[index].costo_unitario = costo;
        compraItemsActuales[index].subtotal = compraItemsActuales[index].cantidad * costo;
        renderTablaCompraItems();
    }
}

function renderTablaCompraItems() {
    const tbody = document.getElementById('tbody-compra-items');
    const totalEl = document.getElementById('compra-total-calculado');
    const badgeCantEl = document.getElementById('compra-articulos-conteo');

    let totalCompra = 0;
    let totalUnidades = 0;

    if (!tbody) return;

    if (compraItemsActuales.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="text-center text-muted" style="padding: 1.5rem;">
                    <i class="ph-bold ph-shopping-bag-open" style="font-size: 1.5rem; display: block; margin-bottom: 6px; opacity: 0.5;"></i>
                    No hay repuestos agregados a esta compra todavía.<br>
                    <span style="font-size: 0.8rem; color: var(--text-muted);">Selecciona un repuesto arriba, define la cantidad y haz clic en <strong>Añadir a la Lista</strong>.</span>
                </td>
            </tr>
        `;
    } else {
        tbody.innerHTML = compraItemsActuales.map((item, idx) => {
            const subt = item.cantidad * item.costo_unitario;
            totalCompra += subt;
            totalUnidades += item.cantidad;
            const stockNuevo = item.stock_actual + item.cantidad;
            return `
                <tr>
                    <td>
                        <strong>${item.codigo ? `[${item.codigo}] ` : ''}${item.nombre}</strong>
                        <div style="font-size: 0.74rem; color: var(--text-muted); margin-top: 2px;">
                            Stock actual: ${item.stock_actual} &rarr; <span style="color: #16a34a; font-weight: 600;">Nuevo stock: ${stockNuevo}</span>
                        </div>
                    </td>
                    <td style="text-align: center; width: 65px;">
                        <input type="number" min="1" class="form-control form-control-sm" value="${item.cantidad}" onchange="actualizarCantidadItemCompra(${idx}, this.value)" style="width: 58px; display: inline-block; text-align: center; padding: 4px 2px;">
                    </td>
                    <td style="text-align: right; width: 85px;">
                        <input type="number" step="0.01" min="0" class="form-control form-control-sm" value="${item.costo_unitario.toFixed(2)}" onchange="actualizarCostoItemCompra(${idx}, this.value)" style="width: 78px; display: inline-block; text-align: right; padding: 4px 2px;">
                    </td>
                    <td style="text-align: right; font-weight: 700; color: var(--primary); vertical-align: middle; width: 90px; white-space: nowrap;">
                        $${formatMoneda(subt, '')}
                    </td>
                    <td style="text-align: center; vertical-align: middle; width: 45px;">
                        <button type="button" class="btn btn-danger btn-sm" onclick="eliminarItemDeCompra(${idx})" title="Quitar repuesto de la lista" style="padding: 4px 7px; font-size: 0.8rem;">
                            <i class="ph-bold ph-trash"></i>
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    }

    if (totalEl) totalEl.textContent = `$${formatMoneda(totalCompra, '')}`;
    if (badgeCantEl) badgeCantEl.textContent = `${compraItemsActuales.length} ítem(s) (${totalUnidades} piezas)`;
}

async function guardarCompra(e) {
    if (e) e.preventDefault();

    if (compraItemsActuales.length === 0) {
        if (typeof mostrarMensaje === 'function') {
            mostrarMensaje({
                titulo: 'Lista vacía',
                texto: 'Debes añadir al menos un repuesto a la lista de compra antes de registrarla.',
                icono: 'warning'
            });
        } else {
            alert('Debes añadir al menos un repuesto a la lista de compra antes de registrarla.');
        }
        return;
    }

    const selProv = document.getElementById('compra-proveedor-id');
    const proveedor_id = selProv ? parseInt(selProv.value) : 1;
    const num_factura_input = document.getElementById('compra-numero-factura');
    const numero_factura_proveedor = num_factura_input ? num_factura_input.value.trim() : '';

    const items = compraItemsActuales.map(item => ({
        producto_id: item.producto_id,
        cantidad: item.cantidad,
        costo_unitario: item.costo_unitario
    }));

    try {
        const res = await fetch('/api/compras', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                proveedor_id,
                numero_factura_proveedor,
                items
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            const numItems = items.length;
            if (typeof mostrarToast === 'function') {
                mostrarToast(`¡Compra registrada! Se incrementó el inventario de ${numItems} repuesto(s).`, 'success');
            } else {
                alert(`¡Compra registrada! Se incrementó el inventario de ${numItems} repuesto(s).`);
            }
            if (num_factura_input) num_factura_input.value = '';
            compraItemsActuales = [];
            renderTablaCompraItems();
            closeModal('modal-compra');
            loadComprasYProveedores();
            if (typeof loadDashboardStats === 'function') loadDashboardStats();
            if (typeof loadMovimientos === 'function') loadMovimientos();
            if (typeof loadProductos === 'function') loadProductos();
            if (typeof loadInventario === 'function') loadInventario();
        } else {
            if (typeof mostrarMensaje === 'function') {
                mostrarMensaje({ titulo: 'Error al registrar la compra', texto: data.error || 'Ocurrió un error inesperado al registrar.', icono: 'error' });
            } else {
                alert(data.error || 'Error al registrar la compra.');
            }
        }
    } catch (err) {
        console.error('Error al guardar compra:', err);
        if (typeof mostrarMensaje === 'function') {
            mostrarMensaje({ titulo: 'Error de red', texto: 'No se pudo conectar con el servidor para registrar la compra.', icono: 'error' });
        } else {
            alert('Error de conexión al registrar la compra.');
        }
    }
}

// Exponer funciones en window para invocación desde HTML
window.eliminarCompra = eliminarCompra;
window.agregarItemACompra = agregarItemACompra;
window.eliminarItemDeCompra = eliminarItemDeCompra;
window.actualizarCantidadItemCompra = actualizarCantidadItemCompra;
window.actualizarCostoItemCompra = actualizarCostoItemCompra;
window.onCompraProductoSeleccionado = onCompraProductoSeleccionado;
window.renderTablaCompraItems = renderTablaCompraItems;

/* ==============================================================================
   FACTURA DESGLOSADA DE COMPRAS (PLANTILLAS VINI Y PROVEEDORES)
   ============================================================================== */

async function verFacturaCompra(compraId) {
    let compra = (comprasCache || []).find(c => c.id === compraId);
    
    // Si no está en caché o no tiene detalles, consultar al endpoint específico
    if (!compra || !compra.detalles || compra.detalles.length === 0) {
        try {
            const resp = await fetch(`/api/compras/${compraId}`);
            if (resp.ok) {
                compra = await resp.json();
            }
        } catch(e) {
            console.error('Error al cargar detalle de compra:', e);
        }
    }

    if (!compra) {
        if (typeof mostrarMensaje === 'function') {
            mostrarMensaje({ titulo: 'Error', texto: 'No se pudo cargar la información de la compra.', icono: 'error' });
        } else {
            alert('No se pudo cargar la información de la compra.');
        }
        return;
    }

    compraActualSeleccionada = compra;
    const isVini = (compra.proveedor_nombre || '').toUpperCase().includes('VINI');
    plantillaFacturaActual = isVini ? 'vini' : 'estandar';

    const selPlantilla = document.getElementById('select-plantilla-factura');
    if (selPlantilla) {
        selPlantilla.value = plantillaFacturaActual;
    }

    const badgeProv = document.getElementById('factura-badge-proveedor');
    if (badgeProv) {
        badgeProv.textContent = compra.proveedor_nombre || 'Proveedor';
        if (isVini) {
            badgeProv.style.background = 'rgba(220, 38, 38, 0.12)';
            badgeProv.style.color = '#dc2626';
            badgeProv.style.border = '1px solid rgba(220, 38, 38, 0.25)';
        } else {
            badgeProv.style.background = 'rgba(37, 99, 235, 0.1)';
            badgeProv.style.color = '#2563eb';
            badgeProv.style.border = '1px solid rgba(37, 99, 235, 0.25)';
        }
    }

    renderizarFacturaCompra(compra, plantillaFacturaActual);
    openModal('modal-factura-compra');
}

function cambiarPlantillaFactura(tipo) {
    plantillaFacturaActual = tipo;
    if (compraActualSeleccionada) {
        renderizarFacturaCompra(compraActualSeleccionada, tipo);
    }
}

function renderizarFacturaCompra(compra, tipo) {
    const contenedor = document.getElementById('contenedor-factura-render');
    if (!contenedor) return;

    if (tipo === 'vini') {
        contenedor.innerHTML = renderPlantillaVini(compra);
    } else {
        contenedor.innerHTML = renderPlantillaEstandar(compra);
    }
}

function renderPlantillaVini(c) {
    const numeroFactura = c.numero_factura_proveedor || `A-000459${(40 + c.id).toString().slice(-2)}`;
    const fechaEmision = c.fecha_hora || `${c.fecha_formateada || c.fecha} 08:49 AM`;
    const detalles = Array.isArray(c.detalles) && c.detalles.length > 0 ? c.detalles : [
        {
            producto_codigo: 'MAN037',
            producto_nombre: 'AMORTIGUADOR AKT TT150-180 - GENESIS SX200 VINI',
            cantidad: 10,
            costo_unitario: c.total > 0 ? c.total / 10 : 833.00,
            subtotal: c.total > 0 ? c.total : 8330.00
        }
    ];

    const filasHtml = detalles.map(d => `
        <tr>
            <td class="vini-code-cell">${d.producto_codigo || ('REP-' + (d.producto_id || '01'))}</td>
            <td class="vini-desc-cell">${d.producto_nombre || 'REPUESTO VINI OEM'}</td>
            <td style="text-align: center; font-weight: 700;">${d.cantidad}</td>
            <td style="text-align: right; font-family: Consolas, monospace;">$${Number(d.costo_unitario).toFixed(2)}</td>
            <td style="text-align: right; font-weight: 700; font-family: Consolas, monospace;">$${Number(d.subtotal).toFixed(2)}</td>
        </tr>
    `).join('');

    return `
    <div class="factura-sheet vini-sheet">
        <!-- ENCABEZADO VINI OEM PARTS / MOTORES LEÓN -->
        <div class="vini-factura-header">
            <div class="vini-header-left">
                <div class="vini-brand-row">
                    <img src="/static/img/vini_logo.png" 
                         onerror="this.src='https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSp6HGdSWc5zxa5ug1gOy5OhpIJ_Qn4TxCRq_W5qT1d5A&s=10'" 
                         alt="Vini OEM Parts" class="vini-logo-img">
                    <div class="vini-corp-meta">
                        <h2 class="vini-corp-title">MOTORES LEON</h2>
                        <div class="vini-corp-slogan">¡Pasión en dos Ruedas!</div>
                        <div class="vini-corp-telf">Telf: 2268-5544 / 8855-9922</div>
                    </div>
                </div>

                <div class="vini-client-box">
                    <div class="vini-field-row">
                        <span class="vini-label">Cliente:</span>
                        <span class="vini-val">JEHOVA JIREH/ MASATEPE/ GILDA PEREZ/ MASATEPE</span>
                    </div>
                    <div class="vini-field-row">
                        <span class="vini-label">Dirección:</span>
                        <span class="vini-val">DE LA GASOLINERA UNO MASATEPE 1C AL ESTE 1/2C AL NORTE, FRENTE A</span>
                    </div>
                    <div class="vini-field-row">
                        <span class="vini-label">Teléfonos:</span>
                        <span class="vini-val">82118929</span>
                    </div>
                </div>
            </div>

            <div class="vini-header-right">
                <div class="vini-invoice-badge-wrap">
                    <div class="vini-stamp-impreso">Impreso</div>
                    <div class="vini-numero-factura">
                        <span class="vini-no-label">Nº</span> ${numeroFactura}
                    </div>
                </div>

                <div class="vini-meta-table">
                    <div class="vini-meta-row">
                        <span class="vini-meta-label">Vendedor:</span>
                        <span class="vini-meta-val">VINI</span>
                    </div>
                    <div class="vini-meta-row">
                        <span class="vini-meta-label">Pedido:</span>
                        <span class="vini-meta-val">01</span>
                    </div>
                    <div class="vini-meta-row">
                        <span class="vini-meta-label">Emisión:</span>
                        <span class="vini-meta-val">${fechaEmision}</span>
                    </div>
                    <div class="vini-meta-row">
                        <span class="vini-meta-label">Sucursal:</span>
                        <span class="vini-meta-val">BODEGA PRINCIPAL MTLEON</span>
                    </div>
                </div>
            </div>
        </div>

        <!-- TABLA DESGLOSADA DE PRODUCTOS -->
        <div class="vini-table-wrap">
            <table class="vini-items-table">
                <thead>
                    <tr>
                        <th style="width: 15%; text-align: left;">Código</th>
                        <th style="width: 47%; text-align: left;">Descripción del producto</th>
                        <th style="width: 12%; text-align: center;">Cant.</th>
                        <th style="width: 13%; text-align: right;">P. Unit</th>
                        <th style="width: 13%; text-align: right;">Total</th>
                    </tr>
                </thead>
                <tbody>
                    ${filasHtml}
                </tbody>
            </table>
        </div>

        <!-- TOTALES Y PIE DE PÁGINA -->
        <div class="vini-footer-grid">
            <div class="vini-footer-legal">
                <div class="vini-legal-notes">
                    <p><strong>Observaciones:</strong> Mercadería original VINI OEM Parts recibida conforme y sujeta a garantía de fábrica.</p>
                    <div class="vini-code-ref" style="margin-top: 6px;">
                        <span>Registro de Entrada: <code>${c.codigo_compra || 'COM-#' + c.id}</code></span>
                        <span style="margin-left: 10px;">Estado: <strong style="color: #16a34a;">${c.estado || 'Completada'}</strong></span>
                    </div>
                </div>

                <div class="vini-signatures-row">
                    <div class="vini-sign-col">
                        <div class="vini-sign-line"></div>
                        <div class="vini-sign-name">Entregado por: VINI</div>
                        <div class="vini-sign-role">MOTORES LEON - Distribución Mayorista</div>
                    </div>
                    <div class="vini-sign-col">
                        <div class="vini-sign-line"></div>
                        <div class="vini-sign-name">Recibido Conforme</div>
                        <div class="vini-sign-role">JEHOVA JIREH MOTO REPUESTOS</div>
                    </div>
                </div>
            </div>

            <div class="vini-totals-card">
                <div class="vini-total-row">
                    <span>Subtotal:</span>
                    <span class="vini-total-num">$${c.total.toFixed(2)}</span>
                </div>
                <div class="vini-total-row">
                    <span>Descuento:</span>
                    <span class="vini-total-num">$0.00</span>
                </div>
                <div class="vini-total-row">
                    <span>I.V.A. (Exento):</span>
                    <span class="vini-total-num">$0.00</span>
                </div>
                <div class="vini-total-row vini-grand-total">
                    <span>Total Factura:</span>
                    <span class="vini-total-num">$${c.total.toFixed(2)}</span>
                </div>
            </div>
        </div>
    </div>
    `;
}

function renderPlantillaEstandar(c) {
    const numeroFactura = c.numero_factura_proveedor || `FAC-${c.id.toString().padStart(6, '0')}`;
    const fechaEmision = c.fecha_hora || `${c.fecha_formateada || c.fecha} 09:00 AM`;
    const detalles = Array.isArray(c.detalles) && c.detalles.length > 0 ? c.detalles : [
        {
            producto_codigo: 'REP-01',
            producto_nombre: 'Repuesto de Motocicleta General',
            cantidad: 1,
            costo_unitario: c.total,
            subtotal: c.total
        }
    ];

    const filasHtml = detalles.map(d => `
        <tr>
            <td style="font-family: Consolas, monospace; font-weight: 700; color: #2563eb;">${d.producto_codigo || ('REP-' + (d.producto_id || '01'))}</td>
            <td style="font-weight: 600;">${d.producto_nombre || 'Repuesto de Mercancía'}</td>
            <td style="text-align: center; font-weight: 700;">${d.cantidad}</td>
            <td style="text-align: right; font-family: Consolas, monospace;">$${Number(d.costo_unitario).toFixed(2)}</td>
            <td style="text-align: right; font-weight: 700; font-family: Consolas, monospace;">$${Number(d.subtotal).toFixed(2)}</td>
        </tr>
    `).join('');

    return `
    <div class="factura-sheet estandar-sheet">
        <div class="estandar-header">
            <div>
                <h2 class="estandar-prov-title">${c.proveedor_nombre || 'Proveedor de Repuestos'}</h2>
                <div style="font-size: 0.85rem; color: #64748b; line-height: 1.4;">
                    <div><strong>Contacto:</strong> ${c.proveedor_contacto || 'Atención al Cliente'}</div>
                    <div><strong>Teléfono:</strong> ${c.proveedor_telefono || 'N/A'} | <strong>Email:</strong> ${c.proveedor_email || 'contacto@proveedor.com'}</div>
                    <div><strong>Dirección:</strong> ${c.proveedor_direccion || 'Nicaragua'}</div>
                </div>
            </div>
            <div style="text-align: right;">
                <div style="font-size: 0.8rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase;">Factura Comercial</div>
                <div style="font-size: 1.35rem; font-weight: 900; color: var(--primary); font-family: Consolas, monospace;">${numeroFactura}</div>
                <div style="font-size: 0.82rem; color: #64748b; margin-top: 4px;"><strong>Fecha:</strong> ${fechaEmision}</div>
                <div style="font-size: 0.82rem; color: #64748b;"><strong>Registro:</strong> <code>${c.codigo_compra || 'COM-#' + c.id}</code></div>
            </div>
        </div>

        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 1.25rem; font-size: 0.85rem; line-height: 1.45;">
            <div><strong>Cliente / Comprador:</strong> JEHOVA JIREH MOTO REPUESTOS</div>
            <div><strong>Ubicación:</strong> Masatepe, Masaya - De la Gasolinera Uno 1c al Este, 1/2c al Norte</div>
            <div><strong>Teléfono:</strong> 82118929</div>
        </div>

        <div class="vini-table-wrap">
            <table class="vini-items-table">
                <thead>
                    <tr>
                        <th style="width: 15%; text-align: left;">Código SKU</th>
                        <th style="width: 47%; text-align: left;">Descripción del Repuesto</th>
                        <th style="width: 12%; text-align: center;">Cantidad</th>
                        <th style="width: 13%; text-align: right;">Costo Unit.</th>
                        <th style="width: 13%; text-align: right;">Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    ${filasHtml}
                </tbody>
            </table>
        </div>

        <div class="vini-footer-grid">
            <div class="vini-footer-legal">
                <div class="vini-legal-notes">
                    <p>Factura de compra registrada para control de inventario y costos de Jehova Jireh Moto Repuestos.</p>
                </div>
                <div class="vini-signatures-row" style="margin-top: 1.5rem;">
                    <div class="vini-sign-col">
                        <div class="vini-sign-line"></div>
                        <div class="vini-sign-name">Entregado por</div>
                        <div class="vini-sign-role">${c.proveedor_nombre}</div>
                    </div>
                    <div class="vini-sign-col">
                        <div class="vini-sign-line"></div>
                        <div class="vini-sign-name">Recibido Conforme</div>
                        <div class="vini-sign-role">Jehova Jireh Moto Repuestos</div>
                    </div>
                </div>
            </div>

            <div class="vini-totals-card">
                <div class="vini-total-row">
                    <span>Subtotal:</span>
                    <span class="vini-total-num">$${c.total.toFixed(2)}</span>
                </div>
                <div class="vini-total-row">
                    <span>I.V.A. (0%):</span>
                    <span class="vini-total-num">$0.00</span>
                </div>
                <div class="vini-total-row vini-grand-total">
                    <span>Total Compra:</span>
                    <span class="vini-total-num">$${c.total.toFixed(2)}</span>
                </div>
            </div>
        </div>
    </div>
    `;
}

function imprimirFacturaCompra() {
    document.body.classList.add('modo-impresion-factura');
    window.print();
    setTimeout(() => {
        document.body.classList.remove('modo-impresion-factura');
    }, 1000);
}


async function guardarProveedor(e) {
    e.preventDefault();
    const id = document.getElementById('prov-id').value;
    const nombre = document.getElementById('prov-nombre').value;
    const contacto = document.getElementById('prov-contacto').value;
    const telefono = document.getElementById('prov-telefono').value;

    const method = id ? 'PUT' : 'POST';
    const url = id ? `/api/proveedores/${id}` : '/api/proveedores';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, contacto, telefono })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert(id ? '¡Proveedor actualizado!' : '¡Proveedor registrado!');
            closeModal('modal-proveedor');
            document.getElementById('form-proveedor').reset();
            document.getElementById('prov-id').value = '';
            document.getElementById('modal-proveedor-title').innerHTML = '<i class="ph-bold ph-user-plus"></i> Registrar / Editar Proveedor';
            loadComprasYProveedores();
        } else {
            alert(data.error || 'Error al guardar proveedor.');
        }
    } catch (err) {
        console.error('Error:', err);
    }
}

function editarProveedor(id) {
    const p = proveedoresCache.find(prov => prov.id === id);
    if (!p) return;
    document.getElementById('prov-id').value = p.id;
    document.getElementById('prov-nombre').value = p.nombre;
    document.getElementById('prov-contacto').value = p.contacto;
    document.getElementById('prov-telefono').value = p.telefono;
    
    const title = document.getElementById('modal-proveedor-title');
    if (title) {
        title.innerHTML = '<i class="ph-bold ph-pencil-simple"></i> Editar Proveedor';
    }
    
    openModal('modal-proveedor');
}

// ==============================================================================
// MÁ"DULO 4: REPORTES Y ANÁLISIS CON CHART.JS
// ==============================================================================

function aplicarFiltroReportes() {
    const mesEl = document.getElementById('rep-filtro-mes');
    const anioEl = document.getElementById('rep-filtro-anio');
    const mes = mesEl ? mesEl.value : 'todos';
    const anio = anioEl ? anioEl.value : '2026';
    loadReportesContabilidad(mes, anio);
}

async function loadReportesContabilidad(mes = null, anio = null) {
    if (typeof ejecutarConsultaReportes === 'function') {
        if (mes && mes !== 'todos') {
            const mSel = document.getElementById('rep-select-mes');
            if (mSel) mSel.value = mes;
        }
        if (anio && anio !== 'todos') {
            const aSel = document.getElementById('rep-select-anio');
            if (aSel) aSel.value = anio;
        }
        return ejecutarConsultaReportes();
    }
    try {
        const mesSelect = document.getElementById('rep-filtro-mes');
        const anioSelect = document.getElementById('rep-filtro-anio');

        if (mes === null && mesSelect) mes = mesSelect.value;
        if (anio === null && anioSelect) anio = anioSelect.value;

        // Construir query string con filtro mensual y anual
        let queryParams = [];
        if (mes && mes !== 'todos') queryParams.push(`mes=${encodeURIComponent(mes)}`);
        if (anio && anio !== 'todos') queryParams.push(`anio=${encodeURIComponent(anio)}`);
        const url = '/api/reportes' + (queryParams.length > 0 ? `?${queryParams.join('&')}` : '');

        const res = await fetch(url);
        const data = await res.json();

        if (!res.ok) {
            mostrarMensaje({ titulo: 'Error en Estadísticas', texto: data.error || 'No tienes permisos o no se pudieron cargar los datos.', icono: 'error' });
            return;
        }

        _reporteDataCache = data;

        // 1. Período Activo
        const periodoTexto = (data.periodo && data.periodo.texto) ? data.periodo.texto : 'Histórico Completo';
        const elPeriodoTexto = document.getElementById('rep-periodo-activo-texto');
        if (elPeriodoTexto) elPeriodoTexto.textContent = periodoTexto;

        // 2. Indicadores Clave de Rendimiento (KPIs) formateados con comas y puntos
        const kpis = data.kpis || {};

        const elIngresos = document.getElementById('rep-ingresos');
        if (elIngresos) elIngresos.textContent = formatMoneda(kpis.ventas_totales_monto ?? data.ventas_totales_monto);

        const elUnidades = document.getElementById('rep-unidades-vendidas');
        if (elUnidades) {
            const uTot = kpis.unidades_vendidas_total ?? data.unidades_vendidas_total ?? 0;
            const cTot = kpis.ventas_totales_conteo ?? data.ventas_totales_conteo ?? 0;
            elUnidades.textContent = `${formatCantidad(uTot, 'unidades')} | ${formatCantidad(cTot, 'ventas')}`;
        }

        const elCosto = document.getElementById('rep-costo-ventas');
        if (elCosto) elCosto.textContent = formatMoneda(kpis.costo_ventas_monto ?? 0);

        const elCompras = document.getElementById('rep-egresos-compras');
        if (elCompras) {
            const comMonto = kpis.compras_totales_monto ?? data.compras_totales_monto ?? 0;
            elCompras.textContent = `Compras del período: ${formatMoneda(comMonto)}`;
        }

        const elMargen = document.getElementById('rep-margen');
        if (elMargen) elMargen.textContent = formatMoneda(kpis.margen_bruto_monto ?? data.margen_bruto_estimado ?? 0);

        const elMargenPct = document.getElementById('rep-margen-pct');
        if (elMargenPct) {
            const mPct = kpis.margen_bruto_porcentaje ?? 0;
            elMargenPct.textContent = `Margen: ${formatPorcentaje(mPct)}`;
        }

        const elTicket = document.getElementById('rep-ticket-promedio');
        if (elTicket) elTicket.textContent = formatMoneda(kpis.ticket_promedio ?? 0);

        const elTicketConteo = document.getElementById('rep-ticket-conteo');
        if (elTicketConteo) {
            const vConteo = kpis.ventas_totales_conteo ?? data.ventas_totales_conteo ?? 0;
            elTicketConteo.textContent = `Ticket medio (${formatCantidad(vConteo)} comprobantes)`;
        }

        const elRotacion = document.getElementById('rep-rotacion');
        if (elRotacion) {
            const rotVal = Number(kpis.rotacion_inventario ?? data.rotacion_inventario ?? 0);
            elRotacion.textContent = `${rotVal.toFixed(2)}x`;
        }

        const elRotacionSub = document.getElementById('rep-rotacion-subtext');
        if (elRotacionSub) {
            const valInv = kpis.valor_inventario_costo ?? 0;
            elRotacionSub.textContent = `Inv. al costo: ${formatMoneda(valInv)}`;
        }

        // Alertas en el KPI
        const desabastList = (data.alertas && data.alertas.desabastecimiento) ? data.alertas.desabastecimiento : [];
        const sobrestockList = (data.alertas && data.alertas.sobrestock) ? data.alertas.sobrestock : [];
        const totalAlertas = desabastList.length + sobrestockList.length;

        const elAlertasTot = document.getElementById('rep-alertas-total');
        if (elAlertasTot) elAlertasTot.textContent = formatCantidad(totalAlertas);

        const elAlertasDet = document.getElementById('rep-alertas-detalle');
        if (elAlertasDet) {
            elAlertasDet.textContent = `${formatCantidad(desabastList.length)} desabast. | ${formatCantidad(sobrestockList.length)} sobre-stock`;
        }

        // 3. Renderizar Gráficos Chart.js
        renderChartsEstadisticas(data);

        // 4. Renderizar Matriz de Rotación ABC
        renderTablaRotacionABC(data.rotacion_abc);

        // 5. Renderizar Alertas de Existencias
        renderAlertasExistencias(data.alertas);

        // 6. Renderizar Rendimiento por Categoría
        renderTablaCategorias(data.categorias_analisis);

        // 7. Cargar Sesiones de Caja operativas
        if (typeof cargarSesionesCaja === 'function') cargarSesionesCaja();

    } catch (err) {
        console.error('Error al cargar reportes y estadísticas:', err);
    }
}

// ------------------------------------------------------------------------------
// RENDERIZADO DE GRÁFICOS DINÁMICOS CON CHART.JS
// ------------------------------------------------------------------------------
function renderChartsEstadisticas(data) {
    if (typeof Chart === 'undefined') return;

    // 1. Gráfico de Tendencia Cronológica de Ventas (Línea)
    const ctxTendencia = document.getElementById('chart-ventas-tendencia');
    if (ctxTendencia) {
        if (chartTendenciaInstance) chartTendenciaInstance.destroy();

        const listaTendencia = data.tendencia_lista || [];
        const labels = listaTendencia.length > 0 
            ? listaTendencia.map(item => item.fecha)
            : Object.keys(data.ventas_por_fecha || {});
        const montos = listaTendencia.length > 0
            ? listaTendencia.map(item => item.monto)
            : Object.values(data.ventas_por_fecha || {});

        chartTendenciaInstance = new Chart(ctxTendencia, {
            type: 'line',
            data: {
                labels: labels.length > 0 ? labels : ['Sin ventas en período'],
                datasets: [{
                    label: 'Ventas ($)',
                    data: montos.length > 0 ? montos : [0],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#f59e0b',
                    pointBorderColor: '#ffffff',
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` Ventas: ${formatMoneda(ctx.raw)}`
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: { color: '#94a3b8', font: { size: 10 } },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    },
                    y: {
                        ticks: {
                            color: '#94a3b8',
                            font: { size: 10 },
                            callback: (val) => formatMoneda(val)
                        },
                        grid: { color: 'rgba(148, 163, 184, 0.1)' }
                    }
                }
            }
        });
    }

    // 2. Gráfico de Distribución por Categoría (Doughnut)
    const ctxCategoria = document.getElementById('chart-ventas-categoria');
    if (ctxCategoria) {
        if (chartCategoriaInstance) chartCategoriaInstance.destroy();

        const cats = data.categorias_analisis || [];
        const catLabels = cats.map(c => c.categoria);
        const catValores = cats.map(c => c.total_ventas);

        chartCategoriaInstance = new Chart(ctxCategoria, {
            type: 'doughnut',
            data: {
                labels: catLabels.length > 0 ? catLabels : ['Sin registros'],
                datasets: [{
                    data: catValores.length > 0 ? catValores : [1],
                    backgroundColor: [
                        '#38bdf8', '#10b981', '#f59e0b', '#a855f7',
                        '#ec4899', '#6366f1', '#14b8a6', '#f97316'
                    ],
                    borderWidth: 2,
                    borderColor: '#1e293b'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#cbd5e1', font: { size: 11 }, boxWidth: 12 }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.label}: ${formatMoneda(ctx.raw)}`
                        }
                    }
                }
            }
        });
    }

    // 3. Gráfico de Métodos de Pago (Bar / Doughnut)
    const ctxMetodos = document.getElementById('chart-metodos-pago');
    if (ctxMetodos) {
        if (chartMetodosPagoInstance) chartMetodosPagoInstance.destroy();

        const metodos = data.metodos_pago || [];
        const metLabels = metodos.map(m => m.metodo);
        const metTotales = metodos.map(m => m.total);

        chartMetodosPagoInstance = new Chart(ctxMetodos, {
            type: 'doughnut',
            data: {
                labels: metLabels.length > 0 ? metLabels : ['Sin datos'],
                datasets: [{
                    data: metTotales.length > 0 ? metTotales : [1],
                    backgroundColor: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b'],
                    borderWidth: 2,
                    borderColor: '#1e293b'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#cbd5e1', font: { size: 11 }, boxWidth: 12 }
                    },
                    tooltip: {
                        callbacks: {
                            label: (ctx) => ` ${ctx.label}: ${formatMoneda(ctx.raw)}`
                        }
                    }
                }
            }
        });
    }
}

// ------------------------------------------------------------------------------
// TABLA Y FILTROS DE EVALUACIÓN DE ROTACIÓN DE INVENTARIO (ABC)
// ------------------------------------------------------------------------------
function renderTablaRotacionABC(rotacionData) {
    if (!rotacionData) return;

    const conteoA = rotacionData.conteo_clase_a || 0;
    const conteoB = rotacionData.conteo_clase_b || 0;
    const conteoC = rotacionData.conteo_clase_c || 0;
    const total = rotacionData.total_productos || (conteoA + conteoB + conteoC);

    const elTotal = document.getElementById('count-abc-todos');
    const elA = document.getElementById('count-abc-a');
    const elB = document.getElementById('count-abc-b');
    const elC = document.getElementById('count-abc-c');

    if (elTotal) elTotal.textContent = formatCantidad(total);
    if (elA) elA.textContent = formatCantidad(conteoA);
    if (elB) elB.textContent = formatCantidad(conteoB);
    if (elC) elC.textContent = formatCantidad(conteoC);

    const prods = rotacionData.productos || [];
    renderFilasTablaABC(prods);
}

function renderFilasTablaABC(productos) {
    const tbody = document.getElementById('tbody-rotacion-abc');
    if (!tbody) return;

    if (!productos || productos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted" style="padding: 2rem;">No se encontraron repuestos con los criterios seleccionados.</td></tr>`;
        return;
    }

    tbody.innerHTML = productos.map(p => {
        let badgeClase = '';
        if (p.clase_abc === 'A') {
            badgeClase = `<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: var(--accent-green); font-weight: 800; border: 1px solid rgba(16, 185, 129, 0.4); padding: 3px 8px; border-radius: 4px;">A - Alta</span>`;
        } else if (p.clase_abc === 'B') {
            badgeClase = `<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: var(--warning); font-weight: 800; border: 1px solid rgba(245, 158, 11, 0.4); padding: 3px 8px; border-radius: 4px;">B - Media</span>`;
        } else {
            badgeClase = `<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: var(--accent-red); font-weight: 800; border: 1px solid rgba(239, 68, 68, 0.4); padding: 3px 8px; border-radius: 4px;">C - Estancado</span>`;
        }

        const stockCritico = p.stock <= p.min_stock;
        const stockStyle = stockCritico ? 'color: var(--accent-red); font-weight: 700;' : 'font-weight: 600;';

        return `
            <tr>
                <td>${badgeClase}</td>
                <td><code style="font-size: 0.82rem;">${p.codigo || '-'}</code></td>
                <td><strong>${p.nombre}</strong></td>
                <td><span class="badge-categoria" style="font-size: 0.70rem; font-weight: 500; line-height: 1.2; background: rgba(100, 116, 139, 0.1); color: var(--text-muted); border: 1px solid rgba(148, 163, 184, 0.25); padding: 2px 7px; border-radius: 4px; display: inline-block; white-space: nowrap;">${p.categoria || '-'}</span></td>
                <td style="text-align: right; ${stockStyle}">${formatCantidad(p.stock)} ${stockCritico ? '⚠️' : ''}</td>
                <td style="text-align: right; color: var(--text-muted);">${formatCantidad(p.min_stock)}</td>
                <td style="text-align: right; font-weight: 700; color: var(--primary);">${formatCantidad(p.unidades_vendidas, 'unid')}</td>
                <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${formatMoneda(p.ingreso_generado)}</td>
                <td style="text-align: center; font-weight: 600;">${(p.rotacion || 0).toFixed(2)}x</td>
            </tr>
        `;
    }).join('');
}

function filtrarTablaABC(clase) {
    _filtroABCActual = clase;

    // Actualizar botones de filtro
    const botones = ['todos', 'a', 'b', 'c'];
    botones.forEach(b => {
        const btn = document.getElementById(`btn-filtro-abc-${b}`);
        if (btn) {
            if (b === clase.toLowerCase() || (b === 'todos' && clase === 'todos')) {
                btn.classList.add('active');
            } else {
                btn.classList.remove('active');
            }
        }
    });

    aplicarFiltroLocalTablaABC();
}

function filtrarTablaABCPorTexto(texto) {
    aplicarFiltroLocalTablaABC();
}

function aplicarFiltroLocalTablaABC() {
    if (!_reporteDataCache || !_reporteDataCache.rotacion_abc) return;

    let prods = _reporteDataCache.rotacion_abc.productos || [];

    // Filtro por clase A, B, C
    if (_filtroABCActual !== 'todos') {
        prods = prods.filter(p => p.clase_abc === _filtroABCActual);
    }

    // Filtro por texto de búsqueda
    const busqInput = document.getElementById('busqueda-tabla-abc');
    const busq = busqInput ? busqInput.value.trim().toLowerCase() : '';

    if (busq) {
        prods = prods.filter(p =>
            (p.nombre && p.nombre.toLowerCase().includes(busq)) ||
            (p.codigo && p.codigo.toLowerCase().includes(busq)) ||
            (p.categoria && p.categoria.toLowerCase().includes(busq))
        );
    }

    renderFilasTablaABC(prods);
}

// ------------------------------------------------------------------------------
// ALERTAS CONSOLIDADAS: DESABASTECIMIENTO Y SOBRE-STOCK
// ------------------------------------------------------------------------------
function renderAlertasExistencias(alertas) {
    if (!alertas) return;

    // 1. Alertas Críticas por Desabastecimiento
    const desabastList = alertas.desabastecimiento || [];
    const elBadgeDesabast = document.getElementById('badge-conteo-desabastecimiento');
    if (elBadgeDesabast) elBadgeDesabast.textContent = `${formatCantidad(desabastList.length)} productos`;

    const tbodyDesabast = document.getElementById('tbody-alertas-desabastecimiento');
    if (tbodyDesabast) {
        if (desabastList.length === 0) {
            tbodyDesabast.innerHTML = `<tr><td colspan="4" class="text-center text-accent-green" style="padding: 1.25rem;">¡Excelente! Ningún repuesto de alta/media rotación está desabastecido.</td></tr>`;
        } else {
            tbodyDesabast.innerHTML = desabastList.map(a => {
                const esAgotado = a.stock_actual <= 0;
                const badgeEstado = esAgotado
                    ? `<span class="badge" style="background: #dc2626; color: #ffffff; font-weight: 700;">Agotado (0)</span>`
                    : `<span class="badge" style="background: #ea580c; color: #ffffff; font-weight: 700;">Bajo Mínimo</span>`;
                const claseColor = a.clase_abc === 'A' ? 'var(--accent-green)' : 'var(--warning)';

                return `
                    <tr>
                        <td>
                            <strong>${a.nombre}</strong><br>
                            <small class="text-muted">SKU: ${a.codigo} | Cat: ${a.categoria}</small>
                        </td>
                        <td><span style="font-weight: 800; color: ${claseColor};">Clase ${a.clase_abc}</span></td>
                        <td style="text-align: center; font-weight: 800; color: var(--accent-red);">${formatCantidad(a.stock_actual)}</td>
                        <td style="text-align: center; color: var(--text-muted);">${formatCantidad(a.stock_minimo)}</td>
                        <td>${badgeEstado}</td>
                    </tr>
                `;
            }).join('');
        }
    }

    // 2. Advertencias de Sobre-Stock / Inventario Obsoleto
    const sobrestockList = alertas.sobrestock || [];
    const elBadgeSobrestock = document.getElementById('badge-conteo-sobrestock');
    if (elBadgeSobrestock) elBadgeSobrestock.textContent = `${formatCantidad(sobrestockList.length)} productos`;

    const tbodySobrestock = document.getElementById('tbody-alertas-sobrestock');
    if (tbodySobrestock) {
        if (sobrestockList.length === 0) {
            tbodySobrestock.innerHTML = `<tr><td colspan="5" class="text-center text-muted" style="padding: 1.25rem;">No se detectó acumulación de inventario ocioso en el período.</td></tr>`;
        } else {
            tbodySobrestock.innerHTML = sobrestockList.map(s => {
                return `
                    <tr>
                        <td>
                            <strong>${s.nombre}</strong><br>
                            <small class="text-muted">SKU: ${s.codigo} | Cat: ${s.categoria}</small>
                        </td>
                        <td style="text-align: center; font-weight: 700; color: var(--warning);">${formatCantidad(s.stock_actual)}</td>
                        <td style="text-align: right;">${formatMoneda(s.costo)}</td>
                        <td style="text-align: right; font-weight: 800; color: var(--accent-red);">${formatMoneda(s.valor_inmovilizado)}</td>
                        <td><span class="badge" style="background: rgba(245, 158, 11, 0.2); color: var(--warning); border: 1px solid rgba(245, 158, 11, 0.4); font-weight: 700;">Capital Inmovilizado</span></td>
                    </tr>
                `;
            }).join('');
        }
    }
}

// ------------------------------------------------------------------------------
// RENDIMIENTO POR CATEGORÍAS
// ------------------------------------------------------------------------------
function renderTablaCategorias(categorias) {
    const tbody = document.getElementById('tbody-rendimiento-categorias');
    if (!tbody) return;

    if (!categorias || categorias.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">Sin datos de ventas por categoría en el período.</td></tr>`;
        return;
    }

    tbody.innerHTML = categorias.map(c => `
        <tr>
            <td><strong>${c.categoria}</strong></td>
            <td style="text-align: center; font-weight: 600;">${formatCantidad(c.unidades)}</td>
            <td style="text-align: right; font-weight: 700; color: var(--primary);">${formatMoneda(c.total_ventas)}</td>
            <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${formatMoneda(c.margen)}</td>
            <td style="text-align: right; font-weight: 600; color: var(--accent-green);">${formatPorcentaje(c.margen_porcentaje)}</td>
        </tr>
    `).join('');
}

// ------------------------------------------------------------------------------
// COMPILACIÓN DEL INFORME EJECUTIVO ESTADÍSTICO CONSOLIDADO
// ------------------------------------------------------------------------------
function compilarInformeEjecutivo() {
    if (!_reporteDataCache) {
        mostrarToast('Primero cargue los datos del informe seleccionando un período.', 'warning');
        return;
    }

    const d = _reporteDataCache;
    const k = d.kpis || {};
    const ahora = new Date();
    const fechaEmision = ahora.toLocaleDateString('es-ES', { day: '2-digit', month: 'long', year: 'numeric' }) + ' ' + ahora.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });

    // 1. Encabezado y Período
    const elFecha = document.getElementById('inf-fecha-emision');
    if (elFecha) elFecha.textContent = fechaEmision;

    const elPeriodo = document.getElementById('inf-periodo-texto');
    if (elPeriodo) elPeriodo.textContent = (d.periodo && d.periodo.texto) ? d.periodo.texto : 'Histórico Completo';

    // 2. KPIs Ejecutivos
    const elVentas = document.getElementById('inf-kpi-ventas');
    if (elVentas) elVentas.textContent = formatMoneda(k.ventas_totales_monto || 0);

    const elTrans = document.getElementById('inf-kpi-transacciones');
    if (elTrans) elTrans.textContent = `${formatCantidad(k.ventas_totales_conteo || 0)} comprobantes | ${formatCantidad(k.unidades_vendidas_total || 0)} unidades`;

    const elCosto = document.getElementById('inf-kpi-costo');
    if (elCosto) elCosto.textContent = formatMoneda(k.costo_ventas_monto || 0);

    const elCompras = document.getElementById('inf-kpi-compras');
    if (elCompras) elCompras.textContent = `Compras en período: ${formatMoneda(k.compras_totales_monto || 0)}`;

    const elMargen = document.getElementById('inf-kpi-margen');
    if (elMargen) elMargen.textContent = formatMoneda(k.margen_bruto_monto || 0);

    const elMargenPct = document.getElementById('inf-kpi-margen-pct');
    if (elMargenPct) elMargenPct.textContent = `Margen Bruto: ${formatPorcentaje(k.margen_bruto_porcentaje || 0)}`;

    const elTicket = document.getElementById('inf-kpi-ticket');
    if (elTicket) elTicket.textContent = formatMoneda(k.ticket_promedio || 0);

    const elRotacion = document.getElementById('inf-kpi-rotacion');
    if (elRotacion) elRotacion.textContent = `${(Number(k.rotacion_inventario) || 0).toFixed(2)}x`;

    const elInv = document.getElementById('inf-kpi-inventario');
    if (elInv) elInv.textContent = formatMoneda(k.valor_inventario_costo || 0);

    const elStockTot = document.getElementById('inf-kpi-stock-total');
    if (elStockTot) elStockTot.textContent = `${formatCantidad(k.stock_total_actual || 0)} unidades en stock físico`;

    // 3. Tabla Categorías del Informe
    const tbodyCat = document.getElementById('inf-tbody-categorias');
    if (tbodyCat) {
        const cats = d.categorias_analisis || [];
        if (cats.length === 0) {
            tbodyCat.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 10px;">Sin transacciones por categoría.</td></tr>`;
        } else {
            tbodyCat.innerHTML = cats.map(c => `
                <tr style="border-bottom: 1px solid #e2e8f0;">
                    <td style="padding: 5px 8px; font-weight: 700;">${c.categoria}</td>
                    <td style="padding: 5px 8px; text-align: center;">${formatCantidad(c.unidades)}</td>
                    <td style="padding: 5px 8px; text-align: right; font-weight: 700;">${formatMoneda(c.total_ventas)}</td>
                    <td style="padding: 5px 8px; text-align: right;">${formatMoneda(c.costo_ventas)}</td>
                    <td style="padding: 5px 8px; text-align: right; font-weight: 700; color: #059669;">${formatMoneda(c.margen)}</td>
                    <td style="padding: 5px 8px; text-align: right; font-weight: 700; color: #059669;">${formatPorcentaje(c.margen_porcentaje)}</td>
                    <td style="padding: 5px 8px; text-align: right; color: #475569;">${formatPorcentaje(c.participacion_porcentaje)}</td>
                </tr>
            `).join('');
        }
    }

    // 4. Métodos de Pago del Informe
    const contMet = document.getElementById('inf-metodos-container');
    if (contMet) {
        const metodos = d.metodos_pago || [];
        if (metodos.length === 0) {
            contMet.innerHTML = `<span style="font-size: 0.8rem; color: #64748b;">Sin movimientos de pago registrados.</span>`;
        } else {
            contMet.innerHTML = metodos.map(m => `
                <div style="flex: 1; min-width: 140px; background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 0.6rem 0.8rem;">
                    <div style="font-size: 0.72rem; color: #64748b; font-weight: 600;">${m.metodo}</div>
                    <div style="font-size: 1.05rem; font-weight: 800; color: #0f172a;">${formatMoneda(m.total)}</div>
                    <div style="font-size: 0.7rem; color: #475569;">${formatCantidad(m.transacciones)} ventas (${formatPorcentaje(m.porcentaje)})</div>
                </div>
            `).join('');
        }
    }

    // 5. Contadores de Rotación ABC
    const rABC = d.rotacion_abc || {};
    const elCntA = document.getElementById('inf-abc-count-a');
    const elCntB = document.getElementById('inf-abc-count-b');
    const elCntC = document.getElementById('inf-abc-count-c');
    if (elCntA) elCntA.textContent = formatCantidad(rABC.conteo_clase_a || 0);
    if (elCntB) elCntB.textContent = formatCantidad(rABC.conteo_clase_b || 0);
    if (elCntC) elCntC.textContent = formatCantidad(rABC.conteo_clase_c || 0);

    // 6. Alertas Tempranas en el Informe
    const tbodyDes = document.getElementById('inf-tbody-desabastecimiento');
    if (tbodyDes) {
        const desList = (d.alertas && d.alertas.desabastecimiento) ? d.alertas.desabastecimiento : [];
        if (desList.length === 0) {
            tbodyDes.innerHTML = `<tr><td colspan="4" style="color: #059669; padding: 8px;">Sin alertas críticas. Stock balanceado.</td></tr>`;
        } else {
            tbodyDes.innerHTML = desList.map(item => `
                <tr style="border-bottom: 1px solid #fee2e2;">
                    <td style="padding: 4px 6px;"><strong>${item.nombre}</strong> (${item.codigo})</td>
                    <td style="padding: 4px 6px; color: #dc2626; font-weight: 700;">${formatCantidad(item.stock_actual)}</td>
                    <td style="padding: 4px 6px;">${formatCantidad(item.stock_minimo)}</td>
                    <td style="padding: 4px 6px; color: #dc2626; font-weight: 700;">${item.severidad}</td>
                </tr>
            `).join('');
        }
    }

    const tbodySob = document.getElementById('inf-tbody-sobrestock');
    if (tbodySob) {
        const sobList = (d.alertas && d.alertas.sobrestock) ? d.alertas.sobrestock : [];
        if (sobList.length === 0) {
            tbodySob.innerHTML = `<tr><td colspan="3" style="color: #059669; padding: 8px;">Sin advertencias de capital inmovilizado.</td></tr>`;
        } else {
            tbodySob.innerHTML = sobList.map(item => `
                <tr style="border-bottom: 1px solid #fef3c7;">
                    <td style="padding: 4px 6px;"><strong>${item.nombre}</strong> (${item.codigo})</td>
                    <td style="padding: 4px 6px; font-weight: 700;">${formatCantidad(item.stock_actual)}</td>
                    <td style="padding: 4px 6px; font-weight: 700; color: #d97706;">${formatMoneda(item.valor_inmovilizado)}</td>
                </tr>
            `).join('');
        }
    }

    // 7. Diagnóstico Gerencial Dinámico
    const elRec = document.getElementById('inf-recomendaciones');
    if (elRec) {
        const margenVal = k.margen_bruto_porcentaje || 0;
        const desabastCnt = (d.alertas && d.alertas.desabastecimiento) ? d.alertas.desabastecimiento.length : 0;
        const sobList = (d.alertas && d.alertas.sobrestock) ? d.alertas.sobrestock : [];
        const capitalParado = sobList.reduce((acc, x) => acc + (x.valor_inmovilizado || 0), 0);

        let diagnosticoHTML = `<ul style="margin: 0; padding-left: 1.25rem;">`;

        if (margenVal >= 30) {
            diagnosticoHTML += `<li><strong>Rentabilidad Saludable:</strong> El margen bruto del ${formatPorcentaje(margenVal)} supera el estándar comercial del sector de repuestos automotrices.</li>`;
        } else if (margenVal > 0) {
            diagnosticoHTML += `<li><strong>Margen Ajustado (${formatPorcentaje(margenVal)}):</strong> Se recomienda revisar los costos de adquisición con proveedores y ponderar los precios de venta de ítems Clase A.</li>`;
        } else {
            diagnosticoHTML += `<li><strong>Atención en Margen:</strong> No se han consolidado márgenes positivos en este período. Verificar registro de costos de compra.</li>`;
        }

        if (desabastCnt > 0) {
            diagnosticoHTML += `<li><strong>Riesgo Crítico de Pérdida de Ventas:</strong> Se identificaron <strong>${formatCantidad(desabastCnt)} repuestos clave (Clase A o B)</strong> con existencias agotadas o bajo mínimo. Se requiere emitir órdenes de compra prioritarias inmediatas para evitar quiebre de stock.</li>`;
        } else {
            diagnosticoHTML += `<li><strong>Abastecimiento Óptimo:</strong> Los productos de mayor rotación disponen de existencias suficientes para cubrir la demanda comercial inmediata.</li>`;
        }

        if (capitalParado > 0) {
            diagnosticoHTML += `<li><strong>Optimización de Capital de Trabajo:</strong> Existen <strong>${formatMoneda(capitalParado)}</strong> inmovilizados en ${formatCantidad(sobList.length)} productos Clase C sin rotación activa. Se recomienda implementar combos promocionales o liquidación selectiva para recuperar liquidez inmediata.</li>`;
        }

        diagnosticoHTML += `</ul>`;
        elRec.innerHTML = diagnosticoHTML;
    }

    // Abrir modal con informe consolidado
    openModal('modal-informe-ejecutivo');
}

// ------------------------------------------------------------------------------
// IMPRESIÓN Y EXPORTACIÓN DEL INFORME
// ------------------------------------------------------------------------------
function imprimirInformeEjecutivo() {
    const printArea = document.getElementById('informe-ejecutivo-print-area');
    if (!printArea) return;

    const printWindow = window.open('', '_blank', 'width=950,height=800');
    if (!printWindow) {
        window.print();
        return;
    }

    printWindow.document.write(`
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>Informe Ejecutivo - Jehová Jireh Moto Repuestos</title>
            <style>
                @page { size: portrait; margin: 10mm; }
                body {
                    font-family: Arial, Helvetica, sans-serif;
                    color: #0f172a;
                    background: #ffffff;
                    margin: 0;
                    padding: 10px;
                    -webkit-print-color-adjust: exact;
                    print-color-adjust: exact;
                }
                table { width: 100%; border-collapse: collapse; margin-bottom: 12px; }
                th, td { padding: 6px 8px; border-bottom: 1px solid #e2e8f0; font-size: 11px; }
                th { background: #f1f5f9; font-weight: 700; text-align: left; }
                .text-right { text-align: right; }
                .text-center { text-align: center; }
            </style>
        </head>
        <body>
            ${printArea.innerHTML}
            <script>
                window.onload = function() {
                    window.print();
                    setTimeout(function() { window.close(); }, 500);
                };
            <\/script>
        </body>
        </html>
    `);
    printWindow.document.close();
}

function exportarReporteEstadisticoCSV() {
    if (!_reporteDataCache) {
        mostrarToast('Primero cargue los datos de reportes', 'warning');
        return;
    }

    const d = _reporteDataCache;
    const k = d.kpis || {};
    const periodo = (d.periodo && d.periodo.texto) ? d.periodo.texto : 'Histórico';

    let csv = '\uFEFF'; // UTF-8 BOM
    csv += `JEHOVÁ JIREH MOTO REPUESTOS - INFORME ESTADÍSTICO Y COMERCIAL\n`;
    csv += `Período Evaluado:;${periodo}\n`;
    csv += `Fecha de Emisión:;${new Date().toLocaleString('es-ES')}\n\n`;

    csv += `1. RESUMEN DE INDICADORES CLAVE (KPIS)\n`;
    csv += `Indicador;Valor\n`;
    csv += `Ventas Totales ($);${(k.ventas_totales_monto || 0).toFixed(2)}\n`;
    csv += `Conteo de Ventas;${k.ventas_totales_conteo || 0}\n`;
    csv += `Unidades Vendidas;${k.unidades_vendidas_total || 0}\n`;
    csv += `Costo de Mercadería ($);${(k.costo_ventas_monto || 0).toFixed(2)}\n`;
    csv += `Compras del Período ($);${(k.compras_totales_monto || 0).toFixed(2)}\n`;
    csv += `Margen Bruto ($);${(k.margen_bruto_monto || 0).toFixed(2)}\n`;
    csv += `Margen Bruto (%);${(k.margen_bruto_porcentaje || 0).toFixed(2)}%\n`;
    csv += `Ticket Promedio ($);${(k.ticket_promedio || 0).toFixed(2)}\n`;
    csv += `Rotación de Inventario;${(k.rotacion_inventario || 0).toFixed(2)}x\n`;
    csv += `Valor Inventario al Costo ($);${(k.valor_inventario_costo || 0).toFixed(2)}\n\n`;

    csv += `2. DISTRIBUCIÓN POR CATEGORÍAS DE REPUESTOS\n`;
    csv += `Categoría;Unidades;Ventas ($);Costo ($);Margen ($);Rentabilidad (%);Cuota en Ventas (%)\n`;
    (d.categorias_analisis || []).forEach(c => {
        csv += `"${c.categoria}";${c.unidades};${c.total_ventas.toFixed(2)};${c.costo_ventas.toFixed(2)};${c.margen.toFixed(2)};${c.margen_porcentaje}%;${c.participacion_porcentaje}%\n`;
    });
    csv += `\n`;

    csv += `3. MÉTODOS DE PAGO\n`;
    csv += `Método de Pago;Transacciones;Total ($);Participación (%)\n`;
    (d.metodos_pago || []).forEach(m => {
        csv += `"${m.metodo}";${m.transacciones};${m.total.toFixed(2)};${m.porcentaje}%\n`;
    });
    csv += `\n`;

    csv += `4. EVALUACIÓN DE ROTACIÓN DE INVENTARIO (ABC)\n`;
    csv += `Clase ABC;Código SKU;Repuesto;Categoría;Stock Actual;Stock Mínimo;Unidades Vendidas;Ingresos Generados ($);Rotación\n`;
    const prods = (d.rotacion_abc && d.rotacion_abc.productos) ? d.rotacion_abc.productos : [];
    prods.forEach(p => {
        csv += `"${p.clase_abc}";"${p.codigo}";"${p.nombre.replace(/"/g, '""')}";"${p.categoria}";${p.stock};${p.min_stock};${p.unidades_vendidas};${p.ingreso_generado.toFixed(2)};${p.rotacion}x\n`;
    });
    csv += `\n`;

    csv += `5. ALERTAS CRÍTICAS: RIESGO DE DESABASTECIMIENTO\n`;
    csv += `Código SKU;Repuesto;Categoría;Clase ABC;Stock Actual;Stock Mínimo;Severidad\n`;
    ((d.alertas && d.alertas.desabastecimiento) || []).forEach(a => {
        csv += `"${a.codigo}";"${a.nombre.replace(/"/g, '""')}";"${a.categoria}";"${a.clase_abc}";${a.stock_actual};${a.stock_minimo};"${a.severidad}"\n`;
    });
    csv += `\n`;

    csv += `6. ADVERTENCIAS: SOBRE-STOCK / CAPITAL INMOVILIZADO\n`;
    csv += `Código SKU;Repuesto;Categoría;Stock Actual;Costo Unitario ($);Capital Inmovilizado ($)\n`;
    ((d.alertas && d.alertas.sobrestock) || []).forEach(s => {
        csv += `"${s.codigo}";"${s.nombre.replace(/"/g, '""')}";"${s.categoria}";${s.stock_actual};${s.costo.toFixed(2)};${s.valor_inmovilizado.toFixed(2)}\n`;
    });

    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const cleanPeriodo = periodo.replace(/[^a-zA-Z0-9]/g, '_');
    link.href = URL.createObjectURL(blob);
    link.download = `Informe_Estadistico_Jehova_Jireh_${cleanPeriodo}.csv`;
    link.click();
}

window.aplicarFiltroReportes = aplicarFiltroReportes;
window.loadReportesContabilidad = loadReportesContabilidad;
window.filtrarTablaABC = filtrarTablaABC;
window.filtrarTablaABCPorTexto = filtrarTablaABCPorTexto;
window.compilarInformeEjecutivo = compilarInformeEjecutivo;
window.imprimirInformeEjecutivo = imprimirInformeEjecutivo;
window.exportarReporteEstadisticoCSV = exportarReporteEstadisticoCSV;

// ==============================================================================
// USUARIOS Y ROLES (ADMIN)
// ==============================================================================

async function loadUsuarios() {
    try {
        const res = await fetch('/api/usuarios');
        const usuarios = await res.json();
        
        const tbody = document.getElementById('tbody-usuarios');
        if (!tbody) return;

        tbody.innerHTML = usuarios.map(u => `
            <tr>
                <td><strong>#${u.id}</strong></td>
                <td>${u.nombre}</td>
                <td><code>${u.username}</code></td>
                <td>
                    <span class="badge-role role-${u.rol.lower ? u.rol.lower().replace(/\s+/g, '-') : u.rol.toLowerCase().replace(/\s+/g, '-')}">
                        ${u.rol}
                    </span>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error usuarios:', err);
    }
}

async function guardarUsuario(e) {
    e.preventDefault();
    const nombre = document.getElementById('usr-nombre').value;
    const username = document.getElementById('usr-username').value;
    const password = document.getElementById('usr-password').value;
    const rol = document.getElementById('usr-rol').value;

    try {
        const res = await fetch('/api/usuarios', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, username, password, rol })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert(`¡Usuario '${username}' registrado con rol '${rol}'!`);
            closeModal('modal-usuario');
            document.getElementById('form-usuario').reset();
            loadUsuarios();
        } else {
            alert(data.error || 'Error al crear usuario.');
        }
    } catch (err) {
        console.error('Error:', err);
    }
}

// ==============================================================================
// GESTION DE CATEGORIAS
// ==============================================================================

async function loadCategorias() {
    try {
        const res = await fetch('/api/categorias');
        const categorias = await res.json();
        
        const tbody = document.getElementById('tbody-categorias');
        if (!tbody) return;

        if (categorias.length === 0) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No hay categorías registradas.</td></tr>`;
            return;
        }

        tbody.innerHTML = categorias.map(c => `
            <tr>
                <td><strong>#${c.id}</strong></td>
                <td>${c.nombre}</td>
                <td>${c.descripcion || '-'}</td>
                <td>
                    <button class="btn btn-secondary icon-btn-text" style="padding: 0.25rem 0.5rem; font-size: 0.85rem;" 
                        onclick="openCategoriaForm(${c.id}, '${c.nombre.replace(/'/g, "\\'")}', '${(c.descripcion || '').replace(/'/g, "\\'")}')">
                        <i class="ph-bold ph-pencil-simple"></i> Editar
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (err) {
        console.error('Error al cargar categorías:', err);
    }
}

function openModalCategorias() {
    loadCategorias();
    openModal('modal-categorias');
}

function openCategoriaForm(id = null, nombre = '', descripcion = '') {
    closeModal('modal-categorias'); // Cerramos la lista temporalmente
    
    document.getElementById('cat-id').value = id || '';
    document.getElementById('cat-nombre').value = nombre;
    document.getElementById('cat-descripcion').value = descripcion;
    
    document.getElementById('cat-form-title').innerHTML = id 
        ? '<i class="ph-bold ph-pencil-simple"></i> Editar Categoría'
        : '<i class="ph-bold ph-plus"></i> Registrar Categoría';
        
    openModal('modal-categoria-form');
}

async function guardarCategoria(e) {
    e.preventDefault();
    
    const id = document.getElementById('cat-id').value;
    const nombre = document.getElementById('cat-nombre').value.trim();
    const descripcion = document.getElementById('cat-descripcion').value.trim();
    
    const url = id ? `/api/categorias/${id}` : '/api/categorias';
    const method = id ? 'PUT' : 'POST';
    
    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, descripcion })
        });
        const data = await res.json();
        
        if (res.ok && data.success) {
            alert(data.mensaje);
            closeModal('modal-categoria-form');
            document.getElementById('form-categoria').reset();
            if(typeof loadInventario === 'function') loadInventario();
            openModalCategorias();
        } else {
            alert(data.error || 'Error al guardar la categoría.');
        }
    } catch (err) {
        console.error('Error al guardar categoría:', err);
        alert('Ocurrió un error inesperado al guardar la categoría.');
    }
}

// ==============================================================================
// MÓDULO DE ESTADOS FINANCIEROS Y CONTABILIDAD
// ==============================================================================

function obtenerFechaHoyLocal() {
    const d = new Date();
    const anio = d.getFullYear();
    const mes = String(d.getMonth() + 1).padStart(2, '0');
    const dia = String(d.getDate()).padStart(2, '0');
    return `${anio}-${mes}-${dia}`;
}

function inicializarFechasFinanzas(forzar = false) {
    const inputInicio = document.getElementById('fin-fecha-inicio');
    const inputFin = document.getElementById('fin-fecha-fin');
    if (!inputInicio || !inputFin) return;

    if (inputInicio.dataset.iniciado && !forzar) return;

    const hoy = obtenerFechaHoyLocal();
    const inicioMes = hoy.substring(0, 7) + '-01';

    if (forzar || !inputInicio.value) inputInicio.value = inicioMes;
    if (forzar || !inputFin.value) inputFin.value = hoy;
    inputInicio.dataset.iniciado = 'true';

    // Sincronizar selectores de conciliación si están disponibles
    const d = new Date();
    const selectMes = document.getElementById('conc-mes');
    const inputAnio = document.getElementById('conc-anio');
    if (selectMes && (!selectMes.value || forzar)) {
        selectMes.value = String(d.getMonth() + 1);
    }
    if (inputAnio && (!inputAnio.value || forzar)) {
        inputAnio.value = String(d.getFullYear());
    }
}

function sincronizarConciliacionConFechas(anio, mes) {
    const selectMes = document.getElementById('conc-mes');
    const inputAnio = document.getElementById('conc-anio');
    if (selectMes && mes) selectMes.value = String(mes);
    if (inputAnio && anio) inputAnio.value = String(anio);
}

function aplicarPeriodoFinanzas(preset) {
    const inputInicio = document.getElementById('fin-fecha-inicio');
    const inputFin = document.getElementById('fin-fecha-fin');
    if (!inputInicio || !inputFin) return;

    const ahora = new Date();
    const anioActual = ahora.getFullYear();
    const mesActual = ahora.getMonth(); // 0-indexed

    if (preset === 'este-mes') {
        const hoy = obtenerFechaHoyLocal();
        inputInicio.value = hoy.substring(0, 7) + '-01';
        inputFin.value = hoy;
        inputInicio.dataset.iniciado = 'true';
        window.balanceModoPreferencia = 'periodo';
        sincronizarConciliacionConFechas(anioActual, mesActual + 1);
    } else if (preset === 'mes-anterior') {
        const primerDiaAnt = new Date(anioActual, mesActual - 1, 1);
        const ultimoDiaAnt = new Date(anioActual, mesActual, 0);
        const fAnio = primerDiaAnt.getFullYear();
        const fMes = String(primerDiaAnt.getMonth() + 1).padStart(2, '0');
        const fDiaFin = String(ultimoDiaAnt.getDate()).padStart(2, '0');
        inputInicio.value = `${fAnio}-${fMes}-01`;
        inputFin.value = `${fAnio}-${fMes}-${fDiaFin}`;
        inputInicio.dataset.iniciado = 'true';
        window.balanceModoPreferencia = 'periodo';
        sincronizarConciliacionConFechas(fAnio, primerDiaAnt.getMonth() + 1);
    } else if (preset === 'este-anio') {
        const hoy = obtenerFechaHoyLocal();
        inputInicio.value = `${anioActual}-01-01`;
        inputFin.value = hoy;
        inputInicio.dataset.iniciado = 'true';
        window.balanceModoPreferencia = 'periodo';
        sincronizarConciliacionConFechas(anioActual, mesActual + 1);
    } else if (preset === 'general' || preset === 'historico-general') {
        const hoy = obtenerFechaHoyLocal();
        inputInicio.value = '';
        inputFin.value = hoy;
        inputInicio.dataset.iniciado = 'true';
        window.balanceModoPreferencia = 'general';
        sincronizarConciliacionConFechas(anioActual, mesActual + 1);
    }

    cargarDatosFinanzas();
}

function switchFinanzasTab(subtab, btn) {
    const section = document.getElementById('tab-finanzas');
    if (!section) return;

    section.querySelectorAll('.btn-outline').forEach(b => b.classList.remove('active'));
    section.querySelectorAll('.fin-tab-content').forEach(v => {
        v.style.display = 'none';
        v.classList.remove('active');
    });

    btn.classList.add('active');
    const view = document.getElementById(subtab);
    if (view) {
        view.style.display = 'block';
        view.classList.add('active');
    }

    if (subtab === 'fin-flujo' && typeof loadFlujoEfectivo === 'function') {
        loadFlujoEfectivo();
    } else if (subtab === 'fin-conciliacion' && typeof cargarDatosConciliacion === 'function') {
        cargarDatosConciliacion();
    } else if (subtab === 'fin-resultados' && typeof loadEstadoResultados === 'function') {
        loadEstadoResultados();
    } else if (subtab === 'fin-balance' && typeof loadBalanceGeneral === 'function') {
        loadBalanceGeneral();
    } else if (subtab === 'fin-asientos' && typeof loadAsientosContables === 'function') {
        loadAsientosContables();
    }
}

async function cargarDatosFinanzas() {
    try {
        inicializarFechasFinanzas(false);
        const tareas = [
            loadCatalogoCuentas(),
            loadAsientosContables(),
            loadEstadoResultados(),
            loadBalanceGeneral()
        ];
        if (typeof loadFlujoEfectivo === 'function') tareas.push(loadFlujoEfectivo());
        if (typeof cargarDatosConciliacion === 'function') tareas.push(cargarDatosConciliacion());
        await Promise.all(tareas);
    } catch (e) {
        console.error("Error al cargar datos financieros:", e);
    }
}

async function loadCatalogoCuentas() {
    try {
        const resp = await fetch('/api/finanzas/cuentas');
        const data = await resp.json();
        
        const tbody = document.getElementById('tbody-cuentas');
        if (!tbody) return;
        
        tbody.innerHTML = '';
        if (data.error) {
            tbody.innerHTML = `<tr><td colspan="4" class="text-center text-red-500">${data.error}</td></tr>`;
            return;
        }
        
        data.forEach(cta => {
            tbody.innerHTML += `
                <tr>
                    <td style="font-weight:600;">${cta.codigo}</td>
                    <td>${cta.nombre}</td>
                    <td><span class="badge ${cta.clasificacion.includes('Activo') ? 'bg-blue' : cta.clasificacion.includes('Pasivo') ? 'bg-red' : cta.clasificacion.includes('Patrimonio') ? 'bg-orange' : 'bg-green'}">${cta.clasificacion}</span></td>
                    <td>${cta.naturaleza}</td>
                    ${window.usuarioRol === 'Contador' ? '' : `<td>
                        <button class="btn" style="background-color: #ef4444; color: white; padding: 0.25rem 0.5rem; border: none; border-radius: 4px;" onclick="eliminarCuenta(${cta.id})">
                            <i class="ph-bold ph-trash"></i>
                        </button>
                    </td>`}
                </tr>
            `;
        });
        
        // Cargar para el select del modal de asiento
        window.cuentasDisponibles = data;
        
        // Populate Libro Mayor select
        const mayorSelect = document.getElementById('mayor-cuenta');
        if (mayorSelect) {
            mayorSelect.innerHTML = '<option value="">-- Seleccione una cuenta --</option>' + 
                data.map(c => `<option value="${c.id}">${c.codigo} - ${c.nombre}</option>`).join('');
        }
    } catch (e) {
        console.error(e);
    }
}

async function loadAsientosContables() {
    try {
        let finInicio = document.getElementById('fin-fecha-inicio');
        let finFin = document.getElementById('fin-fecha-fin');
        const start = finInicio ? finInicio.value : '';
        const end = finFin ? finFin.value : '';
        let url = '/api/finanzas/asientos';
        let queryParams = [];
        if (start) queryParams.push(`start=${start}`);
        if (end) queryParams.push(`end=${end}`);
        if (queryParams.length > 0) url += '?' + queryParams.join('&');

        const resp = await fetch(url);
        const data = await resp.json();
        
        const container = document.getElementById('container-asientos');
        if (!container) return;
        
        container.innerHTML = '';
        if (data.error) {
            container.innerHTML = `<p class="text-red-500">${data.error}</p>`;
            return;
        }
        
        if (data.length === 0) {
            container.innerHTML = `<p>No hay asientos contables registrados.</p>`;
            return;
        }
        
        data.forEach(a => {
            let movsHtml = '';
            let totalDebe = 0;
            let totalHaber = 0;
            
            let formatNum = (val) => parseFloat(val).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
            
            a.movimientos.forEach(m => {
                totalDebe += m.debe;
                totalHaber += m.haber;
                movsHtml += `
                    <tr>
                        <td style="padding-left: ${m.haber > 0 ? '2rem' : '0.5rem'}; font-family: monospace;">${m.codigo}</td>
                        <td>${m.cuenta}</td>
                        <td class="text-right">${m.debe > 0 ? '$' + formatNum(m.debe) : ''}</td>
                        <td class="text-right">${m.haber > 0 ? '$' + formatNum(m.haber) : ''}</td>
                    </tr>
                `;
            });
            
            container.innerHTML += `
                <div style="border: 1px solid var(--border-color); border-radius: 8px; padding: 1rem; background: var(--bg-color);">
                    <div style="display:flex; justify-content:space-between; margin-bottom: 0.5rem;">
                        <strong>Asiento #${a.id} | ${a.fecha}</strong>
                        <span class="badge bg-gray">${a.modulo_origen}</span>
                    </div>
                    <p style="margin-bottom: 1rem; color: var(--text-muted); font-style: italic;">"${a.concepto}"</p>
                    <table class="data-table" style="font-size: 0.9rem;">
                        <thead style="background: var(--bg-dark);">
                            <tr><th>Código</th><th>Cuenta</th><th class="text-right">Debe</th><th class="text-right">Haber</th></tr>
                        </thead>
                        <tbody>${movsHtml}</tbody>
                        <tfoot>
                            <tr style="font-weight: bold;">
                                <td colspan="2" class="text-right">Sumas Iguales:</td>
                                <td class="text-right">$${formatNum(totalDebe)}</td>
                                <td class="text-right">$${formatNum(totalHaber)}</td>
                            </tr>
                        </tfoot>
                    </table>
                </div>
            `;
        });
    } catch (e) {
        console.error(e);
    }
}

async function loadEstadoResultados() {
    try {
        let finInicio = document.getElementById('fin-fecha-inicio');
        let finFin = document.getElementById('fin-fecha-fin');
        const start = finInicio ? finInicio.value : '';
        const end = finFin ? finFin.value : '';
        let url = '/api/finanzas/estado_resultados';
        let queryParams = [];
        if (start) queryParams.push(`start=${start}`);
        if (end) queryParams.push(`end=${end}`);
        if (queryParams.length > 0) url += '?' + queryParams.join('&');

        const resp = await fetch(url);
        const data = await resp.json();
        const container = document.getElementById('reporte-estado-resultados');
        if (!container) return;
        
        if (data.error) {
            container.innerHTML = `<p class="text-red-500">${data.error}</p>`;
            return;
        }

        let formatC = (val) => '$' + parseFloat(val || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        const pStart = (data.periodo && data.periodo.start) || start;
        const pEnd = (data.periodo && data.periodo.end) || end;
        let subtitle = (pStart && pEnd && pStart !== 'Inicio histórico') 
            ? `Del ${pStart} al ${pEnd}` 
            : (pEnd ? `Histórico acumulado hasta el ${pEnd}` : "Período actual");
        
        let html = `<div style="max-width: 850px; margin: 0 auto; background: var(--bg-color); padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">`;
        html += `<h2 style="text-align: center; margin-bottom: 0;">JEHOVÁ  JIREH MOTO REPUESTOS</h2>`;
        html += `<h4 style="text-align: center; color: var(--text-muted); margin-top: 0.5rem; margin-bottom: 2rem;">ESTADO DE RESULTADOS INTEGRAL<br><span style="font-size: 0.9rem; font-weight: normal;">${subtitle}</span></h4>`;
        
        html += `<table style="width: 100%; border-collapse: collapse;"><tbody>`;
        
        // INGRESOS
        html += `<tr><td colspan="2" style="font-weight: bold; font-size: 1.1rem; padding-bottom: 0.5rem;">Ingresos Operativos</td></tr>`;
        (data.ingresos || []).forEach(i => {
            html += `<tr><td style="padding-left: 2rem;">${i.cuenta}</td><td class="text-right">${formatC(i.saldo)}</td></tr>`;
        });
        html += `<tr style="border-bottom: 1px solid var(--border-color);"><td style="font-weight: bold; padding-top: 0.5rem;">Total Ingresos</td><td class="text-right" style="font-weight: bold; padding-top: 0.5rem;">${formatC(data.total_ingresos)}</td></tr>`;
        
        // COSTOS
        html += `<tr><td colspan="2" style="font-weight: bold; font-size: 1.1rem; padding-top: 1.5rem; padding-bottom: 0.5rem;">Costo de Ventas</td></tr>`;
        (data.costos || []).forEach(c => {
            html += `<tr><td style="padding-left: 2rem;">${c.cuenta}</td><td class="text-right">${formatC(c.saldo)}</td></tr>`;
        });
        html += `<tr style="border-bottom: 1px solid var(--border-color);"><td style="font-weight: bold; padding-top: 0.5rem;">Total Costo de Ventas</td><td class="text-right" style="font-weight: bold; padding-top: 0.5rem;">${formatC(data.total_costos)}</td></tr>`;
        
        // UTILIDAD BRUTA
        html += `<tr style="background: rgba(30, 60, 114, 0.1);"><td style="font-weight: bold; padding: 0.75rem;">Utilidad Bruta</td><td class="text-right" style="font-weight: bold; padding: 0.75rem;">${formatC(data.utilidad_bruta)}</td></tr>`;

        // GASTOS
        html += `<tr><td colspan="2" style="font-weight: bold; font-size: 1.1rem; padding-top: 1.5rem; padding-bottom: 0.5rem;">Gastos Operativos</td></tr>`;
        (data.gastos || []).forEach(g => {
            html += `<tr><td style="padding-left: 2rem;">${g.cuenta}</td><td class="text-right">${formatC(g.saldo)}</td></tr>`;
        });
        html += `<tr style="border-bottom: 1px solid var(--border-color);"><td style="font-weight: bold; padding-top: 0.5rem;">Total Gastos Operativos</td><td class="text-right" style="font-weight: bold; padding-top: 0.5rem;">${formatC(data.total_gastos)}</td></tr>`;
        
        // UTILIDAD NETA
        let isProfit = (data.utilidad_neta || 0) >= 0;
        let color = isProfit ? '#10b981' : '#ef4444';
        html += `<tr style="background: ${isProfit ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)'}; color: ${color};"><td style="font-weight: bold; font-size: 1.15rem; padding: 0.85rem 1rem;">UTILIDAD NETA DEL EJERCICIO</td><td class="text-right" style="font-weight: bold; font-size: 1.15rem; padding: 0.85rem 1rem;">${formatC(data.utilidad_neta)}</td></tr>`;
        
        html += `</tbody></table></div>`;
        container.innerHTML = html;
    } catch (e) { console.error(e); }
}

async function loadBalanceGeneral(modoForzado = null) {
    try {
        let finInicio = document.getElementById('fin-fecha-inicio');
        let finFin3 = document.getElementById('fin-fecha-fin');
        const start = finInicio ? finInicio.value : '';
        const end = finFin3 ? finFin3.value : '';

        if (modoForzado) {
            window.balanceModoPreferencia = modoForzado;
        }
        const modo = window.balanceModoPreferencia || (start ? 'periodo' : 'general');

        let url = '/api/finanzas/balance_general';
        let queryParams = [];
        if (start) queryParams.push(`start=${start}`);
        if (end) queryParams.push(`end=${end}`);
        if (modo) queryParams.push(`modo=${modo}`);
        if (queryParams.length > 0) url += '?' + queryParams.join('&');

        const resp = await fetch(url);
        const data = await resp.json();
        const container = document.getElementById('reporte-balance-general');
        if (!container) return;
        
        if (data.error) {
            container.innerHTML = `<p class="text-red-500">${data.error}</p>`;
            return;
        }

        let formatC = (val) => '$' + parseFloat(val || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        const corte = data.fecha_corte || end;
        const pStart = (data.periodo && data.periodo.start) || start;
        const pEnd = (data.periodo && data.periodo.end) || end;
        const esPeriodo = (data.modo === 'periodo');
        const anioTexto = pStart ? pStart.substring(0, 4) : '';

        let subtitle = esPeriodo 
            ? `EJERCICIO ${anioTexto ? anioTexto + ' ' : ''}(Del ${pStart} al ${pEnd})` 
            : (pStart ? `Al ${corte} (Histórico Acumulado con Desglose ${anioTexto})` : `Al ${corte} (Histórico Acumulado General)`);
        
        let html = `<div style="max-width: 900px; margin: 0 auto; background: var(--bg-color); padding: 2rem; border-radius: 8px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">`;
        html += `<h2 style="text-align: center; margin-bottom: 0;">JEHOVÁ  JIREH MOTO REPUESTOS</h2>`;
        html += `<h4 style="text-align: center; color: var(--text-muted); margin-top: 0.5rem; margin-bottom: 2rem;">ESTADO DE SITUACIÓN FINANCIERA<br><span style="font-size: 0.9rem; font-weight: normal;">${subtitle}</span></h4>`;
        
        html += `<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 2rem;">`;
        
        // COLUMNA IZQUIERDA: ACTIVOS
        html += `<div>`;
        html += `<h3 style="border-bottom: 2px solid var(--primary); padding-bottom: 0.5rem;">ACTIVOS</h3>`;
        html += `<table style="width: 100%; border-collapse: collapse;"><tbody>`;
        
        html += `<tr><td colspan="2" style="font-weight: bold; padding-top: 0.5rem; color: var(--text-muted);">Activos Corrientes</td></tr>`;
        (data.activos && data.activos.corrientes || []).forEach(c => { html += `<tr><td style="padding-left: 1rem;">${c.cuenta}</td><td class="text-right">${formatC(c.saldo)}</td></tr>`; });
        
        html += `<tr><td colspan="2" style="font-weight: bold; padding-top: 1rem; color: var(--text-muted);">Activos No Corrientes</td></tr>`;
        (data.activos && data.activos.no_corrientes || []).forEach(c => { html += `<tr><td style="padding-left: 1rem;">${c.cuenta}</td><td class="text-right">${formatC(c.saldo)}</td></tr>`; });
        
        html += `</tbody></table>`;
        html += `<div style="margin-top: 2rem; padding: 1rem; background: rgba(15, 32, 39, 0.05); border-radius: 4px; display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1rem;">
                    <span>TOTAL ACTIVOS</span><span>${formatC(data.activos && data.activos.total)}</span>
                 </div>`;
        html += `</div>`;

        // COLUMNA DERECHA: PASIVO Y PATRIMONIO
        html += `<div>`;
        html += `<h3 style="border-bottom: 2px solid var(--primary); padding-bottom: 0.5rem;">PASIVOS Y PATRIMONIO</h3>`;
        html += `<table style="width: 100%; border-collapse: collapse;"><tbody>`;
        
        html += `<tr><td colspan="2" style="font-weight: bold; padding-top: 0.5rem; color: var(--text-muted);">Pasivos Corrientes</td></tr>`;
        (data.pasivos && data.pasivos.corrientes || []).forEach(c => { html += `<tr><td style="padding-left: 1rem;">${c.cuenta}</td><td class="text-right">${formatC(c.saldo)}</td></tr>`; });
        
        if (data.pasivos && data.pasivos.no_corrientes && data.pasivos.no_corrientes.length > 0) {
            html += `<tr><td colspan="2" style="font-weight: bold; padding-top: 1rem; color: var(--text-muted);">Pasivos No Corrientes</td></tr>`;
            data.pasivos.no_corrientes.forEach(c => { html += `<tr><td style="padding-left: 1rem;">${c.cuenta}</td><td class="text-right">${formatC(c.saldo)}</td></tr>`; });
        }
        
        html += `<tr><td colspan="2" style="font-weight: bold; padding-top: 1.5rem; color: var(--text-muted);">Patrimonio</td></tr>`;
        (data.patrimonio && data.patrimonio.cuentas || []).forEach(c => { 
            html += `<tr><td style="padding-left: 1rem;">${c.cuenta}</td><td class="text-right">${formatC(c.saldo)}</td></tr>`; 
        });

        html += `</tbody></table>`;
        html += `<div style="margin-top: 2rem; padding: 1rem; background: rgba(15, 32, 39, 0.05); border-radius: 4px; display: flex; justify-content: space-between; font-weight: bold; font-size: 1.1rem;">
                    <span>TOTAL PASIVO Y PATR.</span><span>${formatC(data.total_pasivo_patrimonio)}</span>
                 </div>`;
        
        let cuadra = data.cuadra !== undefined ? data.cuadra : (Math.abs((data.activos && data.activos.total || 0) - (data.total_pasivo_patrimonio || 0)) < 0.01);
        html += `<div style="margin-top: 1rem; text-align: right;">
            ${cuadra ? '<span style="color: #10b981; font-weight: bold;"><i class="ph-bold ph-check-circle"></i> Balance Cuadrado</span>' : '<span style="color: #ef4444; font-weight: bold;"><i class="ph-bold ph-warning"></i> Diferencia detectada</span>'}
        </div>`;

        html += `</div>`; // Fin col derecha
        html += `</div>`; // Fin grid
        html += `</div>`;
        container.innerHTML = html;
    } catch (e) { console.error(e); }
}

window.loadBalanceGeneral = loadBalanceGeneral;
window.aplicarPeriodoFinanzas = aplicarPeriodoFinanzas;

// LOGICA MODAL NUEVO ASIENTO
function agregarFilaAsiento() {
    const tbody = document.querySelector('#tabla-asiento-movimientos tbody');
    let options = '<option value="">Seleccione cuenta...</option>';
    if (window.cuentasDisponibles) {
        window.cuentasDisponibles.forEach(c => {
            options += `<option value="${c.id}">${c.codigo} - ${c.nombre}</option>`;
        });
    }

    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><select class="form-control" name="asiento-cta" required>${options}</select></td>
        <td><input type="number" step="0.01" min="0" class="form-control calc-asiento" name="asiento-debe" value="0.00" oninput="calcularTotalAsiento()"></td>
        <td><input type="number" step="0.01" min="0" class="form-control calc-asiento" name="asiento-haber" value="0.00" oninput="calcularTotalAsiento()"></td>
        <td><button type="button" class="btn btn-outline" style="color: #ef4444; border-color: #ef4444; padding: 0.25rem 0.5rem;" onclick="this.closest('tr').remove(); calcularTotalAsiento()"><i class="ph-bold ph-trash"></i></button></td>
    `;
    tbody.appendChild(tr);
}

function calcularTotalAsiento() {
    let tDebe = 0;
    let tHaber = 0;
    document.querySelectorAll('input[name="asiento-debe"]').forEach(i => tDebe += parseFloat(i.value || 0));
    document.querySelectorAll('input[name="asiento-haber"]').forEach(i => tHaber += parseFloat(i.value || 0));
    
    document.getElementById('asiento-total-debe').innerText = '$' + formatMoneda(tDebe, '');
    document.getElementById('asiento-total-haber').innerText = '$' + formatMoneda(tHaber, '');
    
    const errDiv = document.getElementById('asiento-error');
    if (Math.abs(tDebe - tHaber) > 0.01) {
        errDiv.style.display = 'block';
        errDiv.innerText = `El asiento no cuadra. Diferencia: $${formatMoneda(Math.abs(tDebe - tHaber), '')}`;
    } else {
        errDiv.style.display = 'none';
    }
}

// Evento cuando se abre el modal (interceptar openModal si se puede o llamar directo)
function prepareAsientoModal() {
    document.getElementById('asiento-fecha').valueAsDate = new Date();
    document.querySelector('#tabla-asiento-movimientos tbody').innerHTML = '';
    agregarFilaAsiento();
    agregarFilaAsiento(); // 2 filas por defecto
    calcularTotalAsiento();
}

async function guardarAsiento(e) {
    e.preventDefault();
    const btn = document.getElementById('btn-guardar-asiento');
    btn.disabled = true;
    
    let tDebe = 0, tHaber = 0;
    const movimientos = [];
    
    const rows = document.querySelectorAll('#tabla-asiento-movimientos tbody tr');
    rows.forEach(tr => {
        const ctaId = tr.querySelector('select[name="asiento-cta"]').value;
        const debe = parseFloat(tr.querySelector('input[name="asiento-debe"]').value || 0);
        const haber = parseFloat(tr.querySelector('input[name="asiento-haber"]').value || 0);
        
        if (ctaId && (debe > 0 || haber > 0)) {
            movimientos.push({ cuenta_id: ctaId, debe: debe, haber: haber });
            tDebe += debe;
            tHaber += haber;
        }
    });
    
    if (Math.abs(tDebe - tHaber) > 0.01) {
        alert("El asiento no está cuadrado. Debe y Haber deben sumar lo mismo.");
        btn.disabled = false;
        return;
    }
    
    if (movimientos.length < 2) {
        alert("Debe incluir al menos 2 movimientos válidos.");
        btn.disabled = false;
        return;
    }

    const payload = {
        fecha: document.getElementById('asiento-fecha').value,
        concepto: document.getElementById('asiento-concepto').value,
        movimientos: movimientos
    };

    try {
        const resp = await fetch('/api/finanzas/asientos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const res = await resp.json();
        if (res.success) {
            closeModal('modal-asiento');
            document.getElementById('form-asiento').reset();
            cargarDatosFinanzas();
        } else {
            alert(res.error || 'Error al guardar asiento');
        }
    } catch (err) {
        console.error(err);
        alert("Ocurrió un error en la solicitud.");
    } finally {
        btn.disabled = false;
    }
}


// ==============================================================================
// REPORTES OPERATIVOS: SESIONES DE CAJA
// ==============================================================================

async function cargarSesionesCaja() {
    try {
        const response = await fetch('/api/caja/sesiones');
        const sesiones = await response.json();
        const tbody = document.getElementById('tbody-sesiones-caja');
        if (!tbody) return;

        if (sesiones.error) {
            console.error(sesiones.error);
            return;
        }

        if (sesiones.length === 0) {
            tbody.innerHTML = `<tr><td colspan="2" class="text-center">No hay sesiones de caja registradas.</td></tr>`;
            return;
        }

        tbody.innerHTML = sesiones.map(s => {
            return `
            <tr>
                <td><strong>Sesión ${s.id}</strong></td>
                <td style="text-align: right;">
                    ${s.estado === 'Cerrada' ? `<button class="btn btn-sm btn-primary" onclick="verReporteCaja(${s.id})" title="Ver Reporte"><i class="ph-bold ph-eye"></i> Ver Reporte</button>` : `<span class="text-muted text-sm" style="display: inline-block; padding: 0.3rem 0.6rem;">En curso</span>`}
                </td>
            </tr>
            `;
        }).join('');
    } catch (e) {
        console.error("Error al cargar sesiones de caja:", e);
    }
}

async function verReporteCaja(id) {
    try {
        const response = await fetch(`/api/caja/sesion/${id}`);
        const data = await response.json();

        if (data.error) {
            alert(data.error);
            return;
        }

        document.getElementById('rep-caja-id').textContent = data.id;
        document.getElementById('rep-caja-estado').textContent = data.estado;
        document.getElementById('rep-caja-usuario').textContent = data.usuario;
        document.getElementById('rep-caja-apertura').textContent = data.fecha_apertura;
        document.getElementById('rep-caja-cierre').textContent = data.fecha_cierre || 'N/A';
        
        document.getElementById('rep-caja-monto-inicial').textContent = `C$ ${formatMoneda(parseFloat(data.monto_inicial), '')}`;
        document.getElementById('rep-caja-ventas-efectivo').textContent = `C$ ${formatMoneda(parseFloat(data.ventas_efectivo), '')}`;
        document.getElementById('rep-caja-monto-esperado').textContent = `C$ ${formatMoneda(parseFloat(data.monto_final_esperado), '')}`;
        document.getElementById('rep-caja-monto-real').textContent = `C$ ${formatMoneda(parseFloat(data.monto_final_real), '')}`;
        
        let difColor = data.diferencia < 0 ? '#ef4444' : (data.diferencia > 0 ? '#f59e0b' : '#10b981');
        document.getElementById('rep-caja-diferencia').innerHTML = `<span style="color: ${difColor};">C$ ${formatMoneda(parseFloat(data.diferencia), '')}</span>`;
        
        document.getElementById('rep-caja-obs').textContent = data.observaciones || 'Sin observaciones.';
        
        const now = new Date();
        document.getElementById('rep-caja-fecha-gen').textContent = now.toLocaleDateString() + ' ' + now.toLocaleTimeString();

        openModal('modal-reporte-caja');
    } catch (e) {
        console.error("Error al cargar reporte de caja:", e);
        alert("Ocurrió un error al cargar el reporte.");
    }
}

function imprimirReporteCaja() {
    const printContent = document.getElementById('area-impresion-reporte-caja').innerHTML;
    const originalContent = document.body.innerHTML;

    document.body.innerHTML = `
        <div id="ticket-print-area" style="padding: 20px; font-family: sans-serif;">
            ${printContent}
        </div>
    `;

    window.print();
    document.body.innerHTML = originalContent;
    location.reload();
}



function anularVenta(v_id) {
    document.getElementById('anular-venta-id').value = v_id;
    openModal('modal-anular-venta');
}

async function procesarAnulacionVenta() {
    const v_id = document.getElementById('anular-venta-id').value;
    if (!v_id) return;
    
    try {
        const response = await fetch(`/api/ventas/${v_id}/anular`, { method: 'POST' });
        const data = await response.json();
        if (data.error) {
            alert(data.error);
        } else {
            alert('✅ ' + data.mensaje);
            closeModal('modal-anular-venta');
            loadHistorialYWeb();
            if (typeof loadInventario === 'function') loadInventario();
            if (typeof loadDashboardStats === 'function') loadDashboardStats();
        }
    } catch(e) {
        alert('Error al intentar anular la venta.');
        console.error(e);
    }
}



// ==============================================================================
// LIBRO MAYOR
// ==============================================================================
async function cargarLibroMayor() {
    const cuentaId = document.getElementById('mayor-cuenta').value;
    if (!cuentaId) {
        alert("Seleccione una cuenta contable");
        return;
    }
    
    const desde = document.getElementById('fin-fecha-inicio').value;
    const hasta = document.getElementById('fin-fecha-fin').value;
    
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
        
        const formatNum = (num) => parseFloat(num).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2});
        
        document.getElementById('mayor-info').style.display = 'block';
        document.getElementById('mayor-titulo-cuenta').innerText = `Cuenta: ${data.cuenta.codigo} - ${data.cuenta.nombre} (${data.cuenta.naturaleza})`;
        document.getElementById('mayor-saldo-inicial').innerText = `C$ ${formatNum(data.saldo_inicial)}`;
        
        const tbody = document.getElementById('tbody-mayor');
        if (data.movimientos.length === 0) {
            tbody.innerHTML = `<tr><td colspan="6" class="text-center text-muted" style="padding: 20px;">No hay movimientos en este periodo.</td></tr>`;
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
        document.getElementById('mayor-saldo-final').innerText = `C$ ${formatNum(data.saldo_final)}`;
        
    } catch (e) {
        console.error(e);
        alert("Error de conexión");
    }
}
