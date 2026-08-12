// ==============================================================================
// Jehová Jireh Moto Repuestos - Lógica Frontend SPA & Conexión con API Flask
// ==============================================================================

let productosCache = [];
let proveedoresCache = [];
let movimientosCache = [];
let ventasCache = [];
let cartPOS = []; // [{"producto_id": 1, "nombre": "...", "precio": 15.50, "cantidad": 1, "stock_max": 18}]

// Instancias de Chart.js
let chartTendenciaInstance = null;
let chartTopProdsInstance = null;
let ventaSeleccionadaActual = null;

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

        // Cargar datos según la pestaña activa
        if (tabId === 'tab-inventario') loadInventario();
        if (tabId === 'tab-ventas') {
            loadPOSProducts();
            loadHistorialVentas();
        }
        if (tabId === 'tab-compras') loadComprasYProveedores();
        if (tabId === 'tab-reportes') loadReportesContabilidad();
        if (tabId === 'tab-usuarios') loadUsuarios();
        if (tabId === 'tab-panel') loadDashboardStats();
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

function switchVentasSubtab(subtab, btn) {
    const section = document.getElementById('tab-ventas');
    if (!section) return;

    section.querySelectorAll('.subnav-btn').forEach(b => b.classList.remove('active'));
    section.querySelectorAll('.subtab-view').forEach(v => v.classList.remove('active'));

    btn.classList.add('active');
    const view = document.getElementById(`subtab-${subtab}`);
    if (view) view.classList.add('active');

    if (subtab === 'historial-ventas') loadHistorialVentas();
    if (subtab === 'pos') loadPOSProducts();
}

// ==============================================================================
// MODALES
// ==============================================================================

function openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
        modal.classList.add('active');
        if (modalId === 'modal-compra') populateCompraSelects();
        if (modalId === 'modal-movimiento') populateMovimientoSelects();
    }
}

function closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('active');
}

// ==============================================================================
// CARGA Y RENDERS DE DATOS: DASHBOARD & STATS
// ==============================================================================

async function loadDashboardStats() {
    try {
        const [resProds, resVentas, resProvs] = await Promise.all([
            fetch('/api/productos').then(r => r.json()),
            fetch('/api/ventas').then(r => r.json()),
            fetch('/api/proveedores').then(r => r.json())
        ]);

        if (Array.isArray(resProds)) productosCache = resProds;
        if (Array.isArray(resProvs)) proveedoresCache = resProvs;
        if (Array.isArray(resVentas)) ventasCache = resVentas;

        const elTotalProds = document.getElementById('stat-total-productos');
        if (elTotalProds) elTotalProds.textContent = resProds.length || 0;

        const totalVentasSum = Array.isArray(resVentas) ? resVentas.reduce((acc, v) => acc + (v.total || 0), 0) : 0;
        const elTotalVentas = document.getElementById('stat-total-ventas');
        if (elTotalVentas) elTotalVentas.textContent = `$${totalVentasSum.toFixed(2)}`;

        const elConteoVentas = document.getElementById('stat-conteo-ventas');
        if (elConteoVentas) elConteoVentas.textContent = `${resVentas.length || 0} transacciones`;

        const stockBajoCount = Array.isArray(resProds) ? resProds.filter(p => p.stock <= p.min_stock).length : 0;
        const elStockBajo = document.getElementById('stat-stock-bajo');
        if (elStockBajo) elStockBajo.textContent = stockBajoCount;

        renderRecentSalesList(resVentas);

    } catch (err) {
        console.error('Error al cargar datos del panel:', err);
    }
}

function renderRecentSalesList(ventas) {
    const container = document.getElementById('recent-sales-list');
    if (!container) return;

    if (!Array.isArray(ventas) || ventas.length === 0) {
        container.innerHTML = `<div class="empty-state"><p>No hay ventas registradas aún.</p></div>`;
        return;
    }

    const ultimas = ventas.slice(-5).reverse();
    let html = `<ul style="list-style: none; display: flex; flex-direction: column; gap: 0.75rem;">`;
    ultimas.forEach(v => {
        html += `
            <li style="display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid var(--border-color);">
                <div>
                    <strong style="color: var(--text-main);">${v.codigo_venta}</strong>
                    <div style="font-size: 0.78rem; color: var(--text-muted);">${v.cliente} | ${v.vendedor}</div>
                </div>
                <div style="text-align: right; display: flex; align-items: center; gap: 0.75rem;">
                    <div>
                        <span style="color: var(--accent-green); font-weight: 700;">$${v.total.toFixed(2)}</span>
                        <div style="font-size: 0.75rem; color: var(--text-dim);">${v.fecha}</div>
                    </div>
                    <button class="btn btn-secondary icon-btn-text" style="padding: 0.35rem 0.6rem; font-size: 0.75rem;" onclick="verComprobanteVenta(${v.id})" title="Ver Ticket">
                        <i class="ph-bold ph-receipt"></i>
                    </button>
                </div>
            </li>
        `;
    });
    html += `</ul>`;
    container.innerHTML = html;
}

// ==============================================================================
// MÓDULO 1: INVENTARIO & KARDEX
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
    const canEdit = ['Administrador', 'Encargado de Inventario'].includes(userRole);
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
            <td>
                <button class="btn btn-secondary icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="openEditarProducto(${p.id})">
                    <i class="ph-bold ph-pencil"></i> Editar
                </button>
            </td>
        ` : '';

        return `
            <tr>
                <td><strong>${p.codigo}</strong></td>
                <td><strong>${p.nombre}</strong></td>
                <td><span style="font-size: 0.8rem; background: var(--bg-dark); padding: 0.25rem 0.5rem; border-radius: 4px;">${p.categoria}</span></td>
                <td style="font-weight: 700; color: var(--accent-green);">$${p.precio.toFixed(2)}</td>
                <td style="color: var(--text-muted);">$${p.costo.toFixed(2)}</td>
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

// --- EDICIÓN DE PRODUCTO ---
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
    const canEdit = ['Administrador', 'Encargado de Inventario'].includes(userRole);
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
        alertBox.innerHTML = `<i class="ph-bold ph-info"></i> <strong>Modo Ajuste por Producto de Más / Cantidad:</strong> Las existencias en el inventario actual <strong>SÍ se recalcularán y actualizarán</strong> en tiempo real.`;
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
// MÓDULO 2: VENTAS (POS, HISTORIAL & COMPROBANTES)
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
        const sinStock = p.stock <= 0;
        const clickAttr = sinStock ? '' : `onclick="addToCartPOS(${p.id})"`;
        const styleAttr = sinStock ? 'opacity: 0.5; cursor: not-allowed;' : '';

        return `
            <div class="pos-product-card" style="${styleAttr}" ${clickAttr}>
                <div>
                    <span class="pos-prod-code">${p.codigo}</span>
                    <h4 class="pos-prod-name">${p.nombre}</h4>
                </div>
                <div>
                    <div class="pos-prod-price">$${p.precio.toFixed(2)}</div>
                    <div class="pos-prod-stock">${sinStock ? '❌ SIN STOCK' : `Stock: ${p.stock}`}</div>
                </div>
            </div>
        `;
    }).join('');
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
}

function removeFromCartPOS(prodId) {
    cartPOS = cartPOS.filter(i => i.producto_id !== prodId);
    renderCartPOS();
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
                <td>$${item.precio.toFixed(2)}</td>
                <td style="font-weight: 700; color: var(--accent-green);">$${subtotal.toFixed(2)}</td>
                <td>
                    <button class="btn-remove-item" onclick="removeFromCartPOS(${item.producto_id})" title="Eliminar">&times;</button>
                </td>
            </tr>
        `;
    }).join('');

    totalEl.textContent = `$${totalSum.toFixed(2)}`;
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

// --- HISTORIAL DE VENTAS & COMPROBANTES ---
async function loadHistorialVentas() {
    try {
        const res = await fetch('/api/ventas');
        const ventas = await res.json();
        ventasCache = ventas;
        renderHistorialVentasTable(ventas);
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

    const reversed = [...ventas].reverse();
    tbody.innerHTML = reversed.map(v => `
        <tr>
            <td><strong>${v.codigo_venta}</strong></td>
            <td>${v.fecha}</td>
            <td>${v.cliente}</td>
            <td>${v.vendedor}</td>
            <td><span style="font-size: 0.8rem; background: var(--bg-dark); padding: 0.2rem 0.5rem; border-radius: 4px;">${v.forma_pago}</span></td>
            <td style="font-weight: 700; color: var(--accent-green);">$${v.total.toFixed(2)}</td>
            <td>
                <button class="btn btn-secondary icon-btn-text" style="padding: 0.3rem 0.6rem; font-size: 0.78rem;" onclick="verComprobanteVenta(${v.id})">
                    <i class="ph-bold ph-receipt"></i> Ver Ticket
                </button>
            </td>
        </tr>
    `).join('');
}

function filterHistorialVentasTable(query) {
    const q = query.toLowerCase();
    const filtrados = ventasCache.filter(v => 
        v.codigo_venta.toLowerCase().includes(q) || 
        v.cliente.toLowerCase().includes(q) || 
        v.vendedor.toLowerCase().includes(q)
    );
    renderHistorialVentasTable(filtrados);
}

async function verComprobanteVenta(ventaId) {
    try {
        const res = await fetch(`/api/ventas/${ventaId}`);
        const venta = await res.json();
        if (res.ok) {
            renderTicketComprobante(venta, false);
            openModal('modal-comprobante');
        }
    } catch (err) {
        console.error('Error al obtener comprobante:', err);
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
            <div style="background: rgba(16, 185, 129, 0.15); color: #10b981; border: 1px solid rgba(16, 185, 129, 0.3); font-weight: 700; padding: 0.8rem 1rem; border-radius: 8px; margin-bottom: 1.25rem; text-align: center; font-size: 0.92rem;">
                <i class="ph-bold ph-check-circle" style="font-size: 1.2rem; vertical-align: middle;"></i> ¡Venta ${v.codigo_venta} procesada exitosamente por un total de $${v.total.toFixed(2)}!
            </div>
        `;
    }

    let itemsHtml = '';
    v.detalles.forEach(d => {
        itemsHtml += `
            <tr style="border-bottom: 1px dashed #cbd5e1;">
                <td style="padding: 0.4rem 0; font-size: 0.85rem; color: #1e293b;">
                    <strong>${d.producto_nombre}</strong>
                </td>
                <td style="padding: 0.4rem 0; text-align: center; font-size: 0.85rem; color: #1e293b;">${d.cantidad}</td>
                <td style="padding: 0.4rem 0; text-align: right; font-size: 0.85rem; color: #1e293b;">$${d.precio_unitario.toFixed(2)}</td>
                <td style="padding: 0.4rem 0; text-align: right; font-size: 0.85rem; font-weight: 700; color: #0f172a;">$${d.subtotal.toFixed(2)}</td>
            </tr>
        `;
    });

    container.innerHTML = `
        ${bannerExito}
        <div style="font-family: monospace, sans-serif; background: #ffffff; color: #0f172a; padding: 1.5rem; border-radius: 8px; max-width: 380px; margin: 0 auto; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
            <div style="text-align: center; border-bottom: 2px dashed #94a3b8; padding-bottom: 0.75rem; margin-bottom: 0.75rem;">
                <h2 style="font-size: 1.3rem; margin-bottom: 0.2rem; color: #0f172a;">JEHOVÁ JIREH</h2>
                <div style="font-size: 0.8rem; font-weight: 700; color: #475569;">MOTO REPUESTOS - MASATEPE</div>
                <div style="font-size: 0.75rem; color: #64748b;">Atención de Calidad y Repuestos Originales</div>
                <div style="font-size: 0.75rem; color: #64748b; margin-top: 0.2rem;">Tel: +505 8899-0000 | Masatepe, Masaya</div>
            </div>

            <div style="font-size: 0.8rem; margin-bottom: 0.75rem; line-height: 1.4;">
                <div><strong>COMPROBANTE DE VENTA:</strong> ${v.codigo_venta}</div>
                <div><strong>Fecha:</strong> ${v.fecha}</div>
                <div><strong>Cliente:</strong> ${v.cliente}</div>
                <div><strong>Vendedor:</strong> ${v.vendedor}</div>
                <div><strong>Forma de Pago:</strong> ${v.forma_pago}</div>
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
                TOTAL TOTAL: $${v.total.toFixed(2)}
            </div>

            <div style="text-align: center; font-size: 0.75rem; color: #64748b; margin-top: 1rem; border-top: 1px solid #e2e8f0; padding-top: 0.5rem;">
                ¡Gracias por su compra en Jehová Jireh! 🙏<br>
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
    window.print();
}

// ==============================================================================
// MÓDULO 3: COMPRAS Y PROVEEDORES
// ==============================================================================

async function loadComprasYProveedores() {
    try {
        const [resCompras, resProvs] = await Promise.all([
            fetch('/api/compras').then(r => r.json()),
            fetch('/api/proveedores').then(r => r.json())
        ]);

        if (Array.isArray(resProvs)) proveedoresCache = resProvs;

        // Render Compras
        const tbodyCompras = document.getElementById('tbody-compras');
        if (tbodyCompras) {
            if (resCompras.length === 0) {
                tbodyCompras.innerHTML = `<tr><td colspan="4" class="text-center text-muted">No hay compras registradas.</td></tr>`;
            } else {
                tbodyCompras.innerHTML = resCompras.map(c => `
                    <tr>
                        <td><strong>COM-#${c.id}</strong></td>
                        <td>${c.fecha}</td>
                        <td>${c.proveedor_nombre}</td>
                        <td style="font-weight: 700; color: var(--primary);">$${c.total.toFixed(2)}</td>
                    </tr>
                `).join('');
            }
        }

        // Render Proveedores
        const tbodyProvs = document.getElementById('tbody-proveedores');
        if (tbodyProvs) {
            if (resProvs.length === 0) {
                tbodyProvs.innerHTML = `<tr><td colspan="3" class="text-center text-muted">No hay proveedores.</td></tr>`;
            } else {
                tbodyProvs.innerHTML = resProvs.map(p => `
                    <tr>
                        <td><strong>${p.nombre}</strong></td>
                        <td>${p.contacto || 'N/A'}</td>
                        <td>${p.telefono || 'N/A'}</td>
                    </tr>
                `).join('');
            }
        }

    } catch (err) {
        console.error('Error compras y proveedores:', err);
    }
}

function populateCompraSelects() {
    const selProv = document.getElementById('compra-proveedor-id');
    const selProd = document.getElementById('compra-producto-id');

    if (selProv) {
        selProv.innerHTML = proveedoresCache.map(p => `<option value="${p.id}">${p.nombre}</option>`).join('');
    }
    if (selProd) {
        selProd.innerHTML = productosCache.map(p => `<option value="${p.id}">${p.codigo} - ${p.nombre} (Stock actual: ${p.stock})</option>`).join('');
    }
}

async function guardarCompra(e) {
    e.preventDefault();
    const proveedor_id = parseInt(document.getElementById('compra-proveedor-id').value);
    const producto_id = parseInt(document.getElementById('compra-producto-id').value);
    const cantidad = parseInt(document.getElementById('compra-cantidad').value);
    const costo_unitario = parseFloat(document.getElementById('compra-costo-unitario').value) || 0;

    try {
        const res = await fetch('/api/compras', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                proveedor_id,
                items: [{ producto_id, cantidad, costo_unitario }]
            })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert('¡Compra registrada! El stock del producto ha sido incrementado.');
            closeModal('modal-compra');
            loadComprasYProveedores();
            loadDashboardStats();
            loadMovimientos();
        } else {
            alert(data.error || 'Error al registrar la compra.');
        }
    } catch (err) {
        console.error('Error:', err);
    }
}

async function guardarProveedor(e) {
    e.preventDefault();
    const nombre = document.getElementById('prov-nombre').value;
    const contacto = document.getElementById('prov-contacto').value;
    const telefono = document.getElementById('prov-telefono').value;

    try {
        const res = await fetch('/api/proveedores', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ nombre, contacto, telefono })
        });
        const data = await res.json();
        if (res.ok && data.success) {
            alert('¡Proveedor registrado!');
            closeModal('modal-proveedor');
            document.getElementById('form-proveedor').reset();
            loadComprasYProveedores();
        } else {
            alert(data.error || 'Error al guardar proveedor.');
        }
    } catch (err) {
        console.error('Error:', err);
    }
}

// ==============================================================================
// MÓDULO 4: REPORTES Y ANÁLISIS CON CHART.JS
// ==============================================================================

async function loadReportesContabilidad() {
    try {
        const res = await fetch('/api/reportes');
        const data = await res.json();

        if (!res.ok) {
            alert(data.error || 'No tienes acceso a los reportes.');
            return;
        }

        document.getElementById('rep-ingresos').textContent = `$${data.ventas_totales_monto.toFixed(2)}`;
        document.getElementById('rep-unidades-vendidas').textContent = `${data.unidades_vendidas_total || 0} unidades vendidas`;
        document.getElementById('rep-egresos').textContent = `$${data.compras_totales_monto.toFixed(2)}`;
        document.getElementById('rep-margen').textContent = `$${data.margen_bruto_estimado.toFixed(2)}`;
        document.getElementById('rep-rotacion').textContent = `${data.rotacion_inventario || 0.00}x`;

        // Render Gráficos Chart.js
        renderCharts(data);

        // Render Tabla Top Productos
        const tbodyTop = document.getElementById('tbody-top-productos');
        if (tbodyTop) {
            if (!data.top_productos || data.top_productos.length === 0) {
                tbodyTop.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Sin datos de ventas.</td></tr>`;
            } else {
                tbodyTop.innerHTML = data.top_productos.slice(0, 5).map((p, idx) => `
                    <tr>
                        <td><strong>#${idx + 1}</strong></td>
                        <td>${p.nombre}</td>
                        <td><strong style="color: var(--primary);">${p.cantidad_vendida}</strong> unid</td>
                        <td style="font-weight: 700; color: var(--accent-green);">$${p.monto_total.toFixed(2)}</td>
                    </tr>
                `).join('');
            }
        }

        // Render Tabla Stock Bajo
        const tbodyStock = document.getElementById('tbody-stock-bajo-reporte');
        if (tbodyStock) {
            if (!data.productos_bajo_stock || data.productos_bajo_stock.length === 0) {
                tbodyStock.innerHTML = `<tr><td colspan="4" class="text-center text-accent-green">¡Excelente! Todo el stock está en niveles óptimos.</td></tr>`;
            } else {
                tbodyStock.innerHTML = data.productos_bajo_stock.map(p => `
                    <tr>
                        <td><strong>${p.codigo}</strong></td>
                        <td>${p.nombre}</td>
                        <td><strong style="color: var(--accent-red);">${p.stock}</strong> unid</td>
                        <td>${p.min_stock} unid</td>
                    </tr>
                `).join('');
            }
        }

        // Resumen para el Contador
        const summaryBox = document.getElementById('accounting-summary');
        if (summaryBox) {
            summaryBox.innerHTML = `
                <h4 style="color: var(--primary); margin-bottom: 0.75rem;">📋 Reporte Consolidado para el Contador Externo (Lic. Fernando Rivas - Granada)</h4>
                <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.6rem; color: var(--text-main);">
                    <li><strong>Ventas acumuladas:</strong> ${data.ventas_totales_conteo} transacciones | <strong>${data.unidades_vendidas_total}</strong> repuestos vendidos por <strong>$${data.ventas_totales_monto.toFixed(2)}</strong>.</li>
                    <li><strong>Compras de Mercancía:</strong> ${data.compras_totales_conteo} adquisiciones por <strong>$${data.compras_totales_monto.toFixed(2)}</strong>.</li>
                    <li><strong>Valoración de Inventario (al Costo):</strong> $${data.valor_inventario_costo.toFixed(2)}.</li>
                    <li><strong>Margen Bruto de Utilidad:</strong> <span style="color: var(--accent-green); font-weight: 700;">$${data.margen_bruto_estimado.toFixed(2)}</span>.</li>
                    <li><strong>Índice de Rotación de Inventario:</strong> ${data.rotacion_inventario}x.</li>
                    <li><strong>Repuestos en Nivel Crítico:</strong> ${data.alerta_stock_bajo_conteo} ítems con bajo stock.</li>
                </ul>
            `;
        }
    } catch (err) {
        console.error('Error reportes:', err);
    }
}

function renderCharts(data) {
    if (typeof Chart === 'undefined') return;

    // 1. Chart Tendencia Ventas
    const ctxTendencia = document.getElementById('chart-ventas-tendencia');
    if (ctxTendencia) {
        if (chartTendenciaInstance) chartTendenciaInstance.destroy();

        const labels = Object.keys(data.ventas_por_fecha || {});
        const values = Object.values(data.ventas_por_fecha || {});

        chartTendenciaInstance = new Chart(ctxTendencia, {
            type: 'line',
            data: {
                labels: labels.length > 0 ? labels : ['Sin datos'],
                datasets: [{
                    label: 'Ventas ($)',
                    data: values.length > 0 ? values : [0],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.15)',
                    borderWidth: 3,
                    fill: true,
                    tension: 0.35,
                    pointBackgroundColor: '#f59e0b'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#243049' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: '#243049' } }
                }
            }
        });
    }

    // 2. Chart Top Productos (Pie/Donut)
    const ctxTop = document.getElementById('chart-top-productos');
    if (ctxTop) {
        if (chartTopProdsInstance) chartTopProdsInstance.destroy();

        const topList = (data.top_productos || []).slice(0, 5);
        const labels = topList.map(p => p.nombre.length > 20 ? p.nombre.substring(0, 20) + '...' : p.nombre);
        const values = topList.map(p => p.cantidad_vendida);

        chartTopProdsInstance = new Chart(ctxTop, {
            type: 'doughnut',
            data: {
                labels: labels.length > 0 ? labels : ['Sin datos'],
                datasets: [{
                    data: values.length > 0 ? values : [1],
                    backgroundColor: [
                        '#f59e0b',
                        '#38bdf8',
                        '#10b981',
                        '#a855f7',
                        '#ef4444'
                    ],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: { color: '#f1f5f9', font: { size: 11 } }
                    }
                }
            }
        });
    }
}

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
