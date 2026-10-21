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
let chartMetodosPagoInstance = null;
let chartCategoriasRentInstance = null;
let chartCategoriasPartInstance = null;
let chartRankingProdsInstance = null;
let chartDevolucionesMotivosInstance = null;

let ventaSeleccionadaActual = null;
let reporteActualData = null; // Guarda respuesta de /api/reportes
let rankingTipoActual = 'mas'; // 'mas' o 'menos'
let agrupacionTendenciaActual = 'dia'; // 'dia', 'semana', 'mes'
let categoriaOrdenActual = 'utilidad'; // 'utilidad', 'margen', 'ingresos'

document.addEventListener('DOMContentLoaded', () => {
    console.log('⚡ Inicializando Sistema Jehová Jireh Moto Repuestos...');

    initNavigation();
    loadDashboardStats();
    loadCategoriasSelect();

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

// --- EDICIÓN Y BORRADO DE PRODUCTO ---
async function borrarProducto(prodId) {
    if(!confirm("¿Estás seguro de que deseas eliminar este repuesto? (Los registros históricos se mantendrán por integridad)")) return;
    try {
        const res = await fetch(`/api/productos/${prodId}`, { method: 'DELETE' });
        const data = await res.json();
        if(res.ok && data.success) {
            alert("Producto eliminado exitosamente.");
            loadInventario();
        } else {
            alert(data.error || "Error al eliminar producto");
        }
    } catch(e) {
        console.error(e);
        alert("Error de conexión al eliminar producto");
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
    document.body.classList.remove('print-mode-report');
    document.body.classList.add('print-mode-ticket');
    window.print();
    setTimeout(() => {
        document.body.classList.remove('print-mode-ticket');
    }, 1000);
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
// MÓDULO 4: ESTADÍSTICAS AVANZADAS, RENTABILIDAD & REPORTES GERENCIALES
// ==============================================================================

async function loadCategoriasSelect() {
    try {
        const res = await fetch('/api/categorias');
        if (!res.ok) return;
        const categorias = await res.json();
        categoriasCache = categorias;
        const sel = document.getElementById('filtro-categoria');
        if (sel) {
            sel.innerHTML = '<option value="all">Todas las Categorías</option>' +
                categorias.map(c => `<option value="${c.id}">${c.nombre}</option>`).join('');
        }
    } catch (e) {
        console.error('Error al cargar categorías:', e);
    }
}

function cambioSelectorPeriodo(val) {
    const groupFechas = document.getElementById('group-fechas-personalizadas');
    const inputIni = document.getElementById('filtro-fecha-inicio');
    const inputFin = document.getElementById('filtro-fecha-fin');
    const lblPeriodo = document.getElementById('lbl-periodo-activo');

    const today = new Date();
    const formatDate = (d) => d.toISOString().split('T')[0];

    if (val === 'personalizado') {
        if (groupFechas) groupFechas.style.display = 'flex';
        if (inputIni && !inputIni.value) {
            const hace30 = new Date();
            hace30.setDate(hace30.getDate() - 30);
            inputIni.value = formatDate(hace30);
        }
        if (inputFin && !inputFin.value) inputFin.value = formatDate(today);
        if (lblPeriodo) lblPeriodo.textContent = 'Rango Personalizado';
    } else {
        if (groupFechas) groupFechas.style.display = 'none';
        const labelsMap = {
            'hoy': 'Hoy',
            '7_dias': 'Últimos 7 Días',
            'mes': 'Mes en Curso',
            'año': 'Año en Curso',
            'historico': 'Histórico Total'
        };
        if (lblPeriodo) lblPeriodo.textContent = labelsMap[val] || val;
    }
}

function aplicarFiltrosReportes(e) {
    if (e) e.preventDefault();
    loadReportesContabilidad();
}

function switchReportSubtab(subtab, btn) {
    document.querySelectorAll('.report-subnav-pills .subnav-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.report-subtab-view').forEach(v => v.classList.remove('active'));

    if (btn) btn.classList.add('active');
    const target = document.getElementById(`subtab-rep-${subtab}`);
    if (target) target.classList.add('active');
}

async function loadReportesContabilidad() {
    try {
        const periodoSel = document.getElementById('filtro-periodo');
        const periodo = periodoSel ? periodoSel.value : 'mes';
        const fechaIni = document.getElementById('filtro-fecha-inicio')?.value || '';
        const fechaFin = document.getElementById('filtro-fecha-fin')?.value || '';
        const comparar = document.getElementById('filtro-comparar')?.checked || false;
        const categoria_id = document.getElementById('filtro-categoria')?.value || 'all';
        const canal_venta = document.getElementById('filtro-canal')?.value || 'all';
        const top_n = document.getElementById('select-ranking-top-n')?.value || 10;

        const params = new URLSearchParams({
            periodo,
            fecha_inicio: fechaIni,
            fecha_fin: fechaFin,
            comparar: comparar ? 'true' : 'false',
            categoria_id,
            canal_venta,
            agrupacion: agrupacionTendenciaActual,
            top_n
        });

        const res = await fetch(`/api/reportes?${params.toString()}`);
        const data = await res.json();

        if (!res.ok) {
            alert(data.error || 'No tienes acceso al módulo de estadísticas.');
            return;
        }

        reporteActualData = data;

        // 1. Render KPIs descriptivos
        renderKPIs(data);

        // 2. Render Gráfica de Tendencia
        renderGraficoTendencia(data);

        // 3. Render Métodos de Pago y Canales
        renderMetodosPagoYCanales(data);

        // 4. Render Categorías y Rentabilidad
        renderCategoriasRentabilidad(data);

        // 5. Render Ranking Demanda
        actualizarVistaRanking();

        // 6. Render Análisis ABC y Hueso
        renderAnalisisABC(data);

        // 7. Render Stock Crítico y Cobertura
        renderStockCritico(data);

        // 8. Render Devoluciones y Garantías
        renderDevoluciones(data);

        // 9. Resumen para Contador
        renderResumenContable(data);

    } catch (err) {
        console.error('Error al cargar estadísticas y reportes:', err);
    }
}

// --- 1. RENDER KPIS CUÁNTICOS ---
function renderKPIs(data) {
    const k = data.kpis || {};
    const cmp = data.comparacion || {};

    const elVentas = document.getElementById('kpi-ventas-netas');
    const elSubtextVentas = document.getElementById('kpi-ventas-subtext');
    const elUtilidad = document.getElementById('kpi-utilidad-bruta');
    const elMargen = document.getElementById('kpi-margen-pct');
    const elCosto = document.getElementById('kpi-costo-ventas');
    const elUnidades = document.getElementById('kpi-unidades-vendidas');
    const elTransacciones = document.getElementById('kpi-transacciones-conteo');
    const elTicket = document.getElementById('kpi-ticket-promedio');
    const elPromedio = document.getElementById('kpi-promedio-diario');
    const elDiasPeriodo = document.getElementById('kpi-dias-periodo');

    if (elVentas) elVentas.textContent = `$${(k.ventas_netas || 0).toFixed(2)}`;
    if (elSubtextVentas) elSubtextVentas.textContent = k.periodo_nombre || 'Período actual';
    if (elUtilidad) elUtilidad.textContent = `$${(k.utilidad_bruta || 0).toFixed(2)}`;
    if (elMargen) elMargen.textContent = `Margen Bruto: ${(k.margen_bruto_pct || 0).toFixed(1)}%`;
    if (elCosto) elCosto.textContent = `$${(k.costo_ventas || 0).toFixed(2)}`;
    if (elUnidades) elUnidades.textContent = (k.unidades_vendidas || 0).toLocaleString();
    if (elTransacciones) elTransacciones.textContent = `${k.transacciones || 0} transacciones`;
    if (elTicket) elTicket.textContent = `$${(k.ticket_promedio || 0).toFixed(2)}`;
    if (elPromedio) elPromedio.textContent = `$${(k.promedio_diario || 0).toFixed(2)}`;
    if (elDiasPeriodo) elDiasPeriodo.textContent = `Base: ${k.dias_periodo || 1} días evaluados`;

    // Badges de comparación si aplica
    function setComparisonBadge(badgeId, cmpData) {
        const badge = document.getElementById(badgeId);
        if (!badge) return;
        if (cmpData && typeof cmpData.diff_monto !== 'undefined') {
            badge.style.display = 'inline-block';
            const signo = cmpData.diff_monto >= 0 ? '+' : '';
            const className = cmpData.diff_monto > 0 ? 'kpi-var-up' : (cmpData.diff_monto < 0 ? 'kpi-var-down' : 'kpi-var-neutral');
            const icon = cmpData.diff_monto > 0 ? '▲' : (cmpData.diff_monto < 0 ? '▼' : '▬');
            badge.className = `kpi-comparison-badge ${className}`;
            badge.textContent = `${icon} ${signo}$${cmpData.diff_monto.toFixed(2)} (${signo}${cmpData.diff_pct.toFixed(1)}%)`;
        } else {
            badge.style.display = 'none';
        }
    }

    setComparisonBadge('badge-cmp-ventas', cmp.ventas_netas);
    setComparisonBadge('badge-cmp-utilidad', cmp.utilidad_bruta);
    setComparisonBadge('badge-cmp-ticket', cmp.ticket_promedio);
}

// --- 2. RENDER GRÁFICO DE TENDENCIA Y PICOS ---
function cambiarAgrupacionTendencia(agrup, btn) {
    agrupacionTendenciaActual = agrup;
    if (btn) {
        document.querySelectorAll('.flex-between .btn-toggle').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
    loadReportesContabilidad();
}

function renderGraficoTendencia(data) {
    const t = data.tendencia || {};
    const ctx = document.getElementById('chart-ventas-tendencia');
    if (!ctx || typeof Chart === 'undefined') return;

    if (chartTendenciaInstance) chartTendenciaInstance.destroy();

    const labels = t.labels && t.labels.length > 0 ? t.labels : ['Sin ventas en rango'];
    const valores = t.valores && t.valores.length > 0 ? t.valores : [0];

    chartTendenciaInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Ventas Netas ($)',
                data: valores,
                borderColor: '#f59e0b',
                backgroundColor: 'rgba(245, 158, 11, 0.15)',
                borderWidth: 3,
                fill: true,
                tension: 0.35,
                pointBackgroundColor: '#f59e0b',
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
                        label: (ctx) => `Venta Neta: $${Number(ctx.raw).toFixed(2)}`
                    }
                }
            },
            scales: {
                x: { ticks: { color: '#94a3b8' }, grid: { color: '#243049' } },
                y: {
                    ticks: {
                        color: '#94a3b8',
                        callback: (v) => `$${v}`
                    },
                    grid: { color: '#243049' }
                }
            }
        }
    });

    const elPicoMax = document.getElementById('lbl-pico-max');
    const elPicoMaxFecha = document.getElementById('lbl-pico-max-fecha');
    const elPicoMin = document.getElementById('lbl-pico-min');
    const elPicoMinFecha = document.getElementById('lbl-pico-min-fecha');

    if (elPicoMax) elPicoMax.textContent = `$${(t.pico_maximo?.monto || 0).toFixed(2)}`;
    if (elPicoMaxFecha) elPicoMaxFecha.textContent = t.pico_maximo?.intervalo || '--';
    if (elPicoMin) elPicoMin.textContent = `$${(t.pico_minimo?.monto || 0).toFixed(2)}`;
    if (elPicoMinFecha) elPicoMinFecha.textContent = t.pico_minimo?.intervalo || '--';
}

// --- 3. RENDER MÉTODOS DE PAGO Y CANALES ---
function renderMetodosPagoYCanales(data) {
    const metodos = data.metodos_pago || [];
    const canales = data.canales_venta || [];

    // Gráfico de Métodos de Pago (Dona)
    const ctx = document.getElementById('chart-metodos-pago');
    if (ctx && typeof Chart !== 'undefined') {
        if (chartMetodosPagoInstance) chartMetodosPagoInstance.destroy();

        const labels = metodos.map(m => m.metodo);
        const valores = metodos.map(m => m.monto);

        chartMetodosPagoInstance = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: labels.length > 0 ? labels : ['Sin cobros'],
                datasets: [{
                    data: valores.length > 0 ? valores : [1],
                    backgroundColor: ['#10b981', '#38bdf8', '#f59e0b', '#a855f7', '#ec4899'],
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

    // Tabla Métodos
    const tbodyMet = document.getElementById('tbody-metodos-pago');
    if (tbodyMet) {
        if (metodos.length === 0) {
            tbodyMet.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Sin transacciones registradas.</td></tr>`;
        } else {
            tbodyMet.innerHTML = metodos.map(m => `
                <tr>
                    <td><strong>${m.metodo}</strong></td>
                    <td>${m.transacciones} ops</td>
                    <td style="font-weight: 700; color: var(--accent-green);">$${m.monto.toFixed(2)}</td>
                    <td><span class="badge-role role-vendedor">${m.participacion_pct.toFixed(1)}%</span></td>
                </tr>
            `).join('');
        }
    }

    // Tabla Canales
    const tbodyCan = document.getElementById('tbody-canales-venta');
    if (tbodyCan) {
        if (canales.length === 0) {
            tbodyCan.innerHTML = `<tr><td colspan="4" class="text-center text-muted">Sin datos de canales.</td></tr>`;
        } else {
            tbodyCan.innerHTML = canales.map(c => `
                <tr>
                    <td><strong><i class="ph-bold ph-storefront"></i> ${c.canal}</strong></td>
                    <td>${c.transacciones} ventas</td>
                    <td style="font-weight: 700; color: var(--primary);">$${c.monto.toFixed(2)}</td>
                    <td><span class="badge-role role-admin">${c.participacion_pct.toFixed(1)}%</span></td>
                </tr>
            `).join('');
        }
    }
}

// --- 4. RENDER CATEGORÍAS Y RENTABILIDAD ---
function ordenarCategorias(criterio, btn) {
    categoriaOrdenActual = criterio;
    if (btn) {
        document.querySelectorAll('#subtab-rep-categorias .btn-toggle').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
    }
    if (reporteActualData) renderCategoriasRentabilidad(reporteActualData);
}

function renderCategoriasRentabilidad(data) {
    const cats = [...(data.categorias || [])];

    // Ordenamiento dinámico
    if (categoriaOrdenActual === 'margen') {
        cats.sort((a, b) => b.margen_bruto_pct - a.margen_bruto_pct);
    } else if (categoriaOrdenActual === 'ingresos') {
        cats.sort((a, b) => b.ingresos_netos - a.ingresos_netos);
    } else {
        cats.sort((a, b) => b.utilidad_bruta - a.utilidad_bruta);
    }

    // Gráfico de Barras Ingresos vs Costos
    const ctxRent = document.getElementById('chart-categorias-rentabilidad');
    if (ctxRent && typeof Chart !== 'undefined') {
        if (chartCategoriasRentInstance) chartCategoriasRentInstance.destroy();

        const topCats = cats.slice(0, 6);
        const labels = topCats.map(c => c.categoria.length > 18 ? c.categoria.substring(0, 18) + '...' : c.categoria);

        chartCategoriasRentInstance = new Chart(ctxRent, {
            type: 'bar',
            data: {
                labels: labels.length > 0 ? labels : ['Sin datos'],
                datasets: [
                    {
                        label: 'Ingresos Netos ($)',
                        data: topCats.map(c => c.ingresos_netos),
                        backgroundColor: '#10b981'
                    },
                    {
                        label: 'Costo de Ventas ($)',
                        data: topCats.map(c => c.costo_ventas),
                        backgroundColor: '#ef4444'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { labels: { color: '#f1f5f9' } }
                },
                scales: {
                    x: { ticks: { color: '#94a3b8' }, grid: { color: '#243049' } },
                    y: { ticks: { color: '#94a3b8' }, grid: { color: '#243049' } }
                }
            }
        });
    }

    // Gráfico de Dona Participación
    const ctxPart = document.getElementById('chart-categorias-participacion');
    if (ctxPart && typeof Chart !== 'undefined') {
        if (chartCategoriasPartInstance) chartCategoriasPartInstance.destroy();

        const topPart = cats.slice(0, 5);
        chartCategoriasPartInstance = new Chart(ctxPart, {
            type: 'doughnut',
            data: {
                labels: topPart.map(c => c.categoria),
                datasets: [{
                    data: topPart.map(c => c.ingresos_netos),
                    backgroundColor: ['#f59e0b', '#38bdf8', '#10b981', '#a855f7', '#ec4899', '#64748b'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'right', labels: { color: '#f1f5f9', font: { size: 10 } } }
                }
            }
        });
    }

    // Tabla de Categorías
    const tbody = document.getElementById('tbody-categorias-rentabilidad');
    if (tbody) {
        if (cats.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Sin movimientos para este período.</td></tr>`;
        } else {
            tbody.innerHTML = cats.map(c => {
                let badgeClass = 'badge-urgencia-alta';
                let nivelTexto = 'Bajo Margen';
                if (c.margen_bruto_pct >= 40) {
                    badgeClass = 'badge-urgencia-baja';
                    nivelTexto = 'Alta Rentabilidad 🔥';
                } else if (c.margen_bruto_pct >= 20) {
                    badgeClass = 'badge-urgencia-media';
                    nivelTexto = 'Rentabilidad Media';
                }

                return `
                    <tr>
                        <td><strong>${c.categoria}</strong></td>
                        <td>${c.unidades_vendidas} unid</td>
                        <td style="font-weight: 700; color: var(--accent-green);">$${c.ingresos_netos.toFixed(2)}</td>
                        <td>${c.participacion_pct.toFixed(1)}%</td>
                        <td style="color: var(--text-muted);">$${c.costo_ventas.toFixed(2)}</td>
                        <td style="font-weight: 700; color: var(--primary);">$${c.utilidad_bruta.toFixed(2)}</td>
                        <td><strong>${c.margen_bruto_pct.toFixed(1)}%</strong></td>
                        <td><span class="badge-urgencia ${badgeClass}">${nivelTexto}</span></td>
                    </tr>
                `;
            }).join('');
        }
    }
}

// --- 5. RENDER RANKING DEMANDA (MÁS Y MENOS VENDIDOS) ---
function cambiarTipoRanking(tipo, btn) {
    rankingTipoActual = tipo;
    const btnMas = document.getElementById('btn-rank-mas');
    const btnMenos = document.getElementById('btn-rank-menos');
    if (btnMas) btnMas.classList.toggle('active', tipo === 'mas');
    if (btnMenos) btnMenos.classList.toggle('active', tipo === 'menos');
    actualizarVistaRanking();
}

function actualizarVistaRanking() {
    if (!reporteActualData || !reporteActualData.ranking) return;

    const ranking = reporteActualData.ranking;
    const criterio = document.getElementById('select-ranking-criterio')?.value || 'cantidad';
    const topN = parseInt(document.getElementById('select-ranking-top-n')?.value || '10');

    let lista = [];
    if (rankingTipoActual === 'mas') {
        lista = (criterio === 'monto') ? ranking.mas_vendidos_monto : ranking.mas_vendidos_cantidad;
    } else {
        lista = ranking.menos_vendidos_cantidad || [];
    }

    const items = (lista || []).slice(0, topN);

    // Gráfico de Barras Ranking
    const ctx = document.getElementById('chart-ranking-productos');
    if (ctx && typeof Chart !== 'undefined') {
        if (chartRankingProdsInstance) chartRankingProdsInstance.destroy();

        const labels = items.map(p => p.nombre.length > 20 ? p.nombre.substring(0, 20) + '...' : p.nombre);
        const values = items.map(p => criterio === 'monto' ? p.monto_total : p.cantidad_vendida);

        chartRankingProdsInstance = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels.length > 0 ? labels : ['Sin datos'],
                datasets: [{
                    label: criterio === 'monto' ? 'Monto Total Facturado ($)' : 'Unidades Vendidas',
                    data: values.length > 0 ? values : [0],
                    backgroundColor: rankingTipoActual === 'mas' ? '#f59e0b' : '#38bdf8',
                    borderRadius: 4
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

    // Tabla Ranking
    const tbody = document.getElementById('tbody-ranking-productos');
    if (tbody) {
        if (items.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Sin datos de productos para este filtro.</td></tr>`;
        } else {
            const medallas = ['🥇 #1', '🥈 #2', '🥉 #3'];
            tbody.innerHTML = items.map((p, idx) => `
                <tr>
                    <td><strong>${medallas[idx] || `#${idx + 1}`}</strong></td>
                    <td><code>${p.codigo}</code></td>
                    <td><strong>${p.nombre}</strong></td>
                    <td><span style="font-size: 0.8rem; background: var(--bg-dark); padding: 0.2rem 0.5rem; border-radius: 4px;">${p.categoria}</span></td>
                    <td><strong style="color: var(--primary);">${p.cantidad_vendida}</strong> unid</td>
                    <td style="font-weight: 700; color: var(--accent-green);">$${p.monto_total.toFixed(2)}</td>
                    <td style="color: var(--text-muted);">$${(p.utilidad || 0).toFixed(2)}</td>
                    <td>${p.stock_actual} en stock</td>
                </tr>
            `).join('');
        }
    }
}

// --- 6. RENDER ANÁLISIS ABC Y HUESO ---
function renderAnalisisABC(data) {
    const inv = data.inventario_abc || {};

    const elRotacion = document.getElementById('abc-rotacion');
    const elConteoA = document.getElementById('abc-conteo-a');
    const elConteoB = document.getElementById('abc-conteo-b');
    const elConteoC = document.getElementById('abc-conteo-c');
    const elCapitalEstancado = document.getElementById('lbl-capital-estancado');

    if (elRotacion) elRotacion.textContent = `${(inv.rotacion_inventario || 0).toFixed(2)}x`;
    if (elConteoA) elConteoA.textContent = inv.conteo_clase_a || 0;
    if (elConteoB) elConteoB.textContent = inv.conteo_clase_b || 0;
    if (elConteoC) elConteoC.textContent = inv.conteo_clase_c || 0;
    if (elCapitalEstancado) elCapitalEstancado.textContent = `$${(inv.capital_estancado_total || 0).toFixed(2)}`;

    // Tabla ABC
    const tbodyABC = document.getElementById('tbody-tabla-abc');
    if (tbodyABC) {
        const items = inv.items_abc || [];
        if (items.length === 0) {
            tbodyABC.innerHTML = `<tr><td colspan="8" class="text-center text-muted">Sin datos de clasificación ABC.</td></tr>`;
        } else {
            tbodyABC.innerHTML = items.map(p => {
                let badgeClass = 'badge-abc-c';
                let prioridad = 'Baja (Variedad)';
                if (p.clase_abc === 'A') {
                    badgeClass = 'badge-abc-a';
                    prioridad = 'Crítica / Control Riguroso';
                } else if (p.clase_abc === 'B') {
                    badgeClass = 'badge-abc-b';
                    prioridad = 'Media / Control Moderado';
                }

                return `
                    <tr>
                        <td><span class="badge-abc ${badgeClass}">Clase ${p.clase_abc}</span></td>
                        <td><code>${p.codigo}</code></td>
                        <td><strong>${p.nombre}</strong></td>
                        <td>${p.categoria}</td>
                        <td>${p.cantidad_vendida} unid</td>
                        <td style="font-weight: 700; color: var(--accent-green);">$${p.monto_total.toFixed(2)}</td>
                        <td><strong>${p.pct_acumulado.toFixed(1)}%</strong></td>
                        <td style="font-size: 0.82rem; color: var(--text-muted);">${prioridad}</td>
                    </tr>
                `;
            }).join('');
        }
    }

    // Tabla Repuestos sin ventas / "Hueso"
    const tbodyHueso = document.getElementById('tbody-repuestos-hueso');
    if (tbodyHueso) {
        const sinVentas = inv.repuestos_sin_ventas || [];
        if (sinVentas.length === 0) {
            tbodyHueso.innerHTML = `<tr><td colspan="7" class="text-center text-accent-green">¡Excelente! Todos los repuestos con stock registran rotación comercial.</td></tr>`;
        } else {
            tbodyHueso.innerHTML = sinVentas.map(p => `
                <tr>
                    <td><code>${p.codigo}</code></td>
                    <td><strong>${p.nombre}</strong></td>
                    <td>${p.categoria}</td>
                    <td><strong style="color: var(--primary);">${p.stock}</strong> unid</td>
                    <td>$${p.costo.toFixed(2)}</td>
                    <td style="font-weight: 700; color: var(--accent-red);">$${p.valor_estancado.toFixed(2)}</td>
                    <td style="font-size: 0.85rem; color: var(--text-muted);">${p.ultima_venta}</td>
                </tr>
            `).join('');
        }
    }
}

// --- 7. RENDER STOCK CRÍTICO Y COBERTURA ---
function renderStockCritico(data) {
    const criticos = data.alertas_criticas || [];
    const tbody = document.getElementById('tbody-alertas-cobertura');
    if (!tbody) return;

    if (criticos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="9" class="text-center text-accent-green">¡Todo el inventario se encuentra sobre el nivel mínimo de seguridad!</td></tr>`;
        return;
    }

    tbody.innerHTML = criticos.map(p => {
        let cobTxt = p.dias_cobertura !== null ? `${p.dias_cobertura} días` : 'Sin demanda reciente';
        let badgeUrgencia = 'badge-urgencia-alta';
        let urgenciaTxt = '🚨 Reorden Urgente';

        if (p.dias_cobertura !== null) {
            if (p.dias_cobertura > 7) {
                badgeUrgencia = 'badge-urgencia-baja';
                urgenciaTxt = 'Baja Urgencia';
            } else if (p.dias_cobertura > 3) {
                badgeUrgencia = 'badge-urgencia-media';
                urgenciaTxt = 'Atención Próxima';
            }
        }

        return `
            <tr>
                <td><code>${p.codigo}</code></td>
                <td><strong>${p.nombre}</strong></td>
                <td>${p.categoria}</td>
                <td><strong style="color: var(--accent-red); font-size: 0.95rem;">${p.stock}</strong> unid</td>
                <td>${p.min_stock} unid</td>
                <td>${p.promedio_diario_ventas} unid/día</td>
                <td><strong>${cobTxt}</strong></td>
                <td><strong style="color: var(--primary);">+${p.sugerencia_reponer} unid</strong></td>
                <td><span class="badge-urgencia ${badgeUrgencia}">${urgenciaTxt}</span></td>
            </tr>
        `;
    }).join('');
}

// --- 8. RENDER DEVOLUCIONES Y GARANTÍAS ---
function renderDevoluciones(data) {
    const dev = data.devoluciones || {};

    const elOps = document.getElementById('dev-total-ops');
    const elUnid = document.getElementById('dev-total-unidades');
    const elMonto = document.getElementById('dev-total-monto');

    if (elOps) elOps.textContent = dev.total_operaciones || 0;
    if (elUnid) elUnid.textContent = dev.unidades_devueltas || 0;
    if (elMonto) elMonto.textContent = `$${(dev.monto_estimado || 0).toFixed(2)}`;

    // Gráfico de Motivos (Pie)
    const ctx = document.getElementById('chart-devoluciones-motivos');
    if (ctx && typeof Chart !== 'undefined') {
        if (chartDevolucionesMotivosInstance) chartDevolucionesMotivosInstance.destroy();

        const motivos = dev.motivos || [];
        chartDevolucionesMotivosInstance = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: motivos.map(m => m.motivo),
                datasets: [{
                    data: motivos.map(m => m.cantidad),
                    backgroundColor: ['#ef4444', '#f59e0b', '#38bdf8', '#a855f7'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { position: 'bottom', labels: { color: '#f1f5f9' } }
                }
            }
        });
    }

    // Tabla Categorías Afectadas
    const tbodyCat = document.getElementById('tbody-devoluciones-categorias');
    if (tbodyCat) {
        const cats = dev.categorias_afectadas || [];
        if (cats.length === 0) {
            tbodyCat.innerHTML = `<tr><td colspan="2" class="text-center text-muted">Sin devoluciones registradas en el período.</td></tr>`;
        } else {
            tbodyCat.innerHTML = cats.map(c => `
                <tr>
                    <td><strong>${c.categoria}</strong></td>
                    <td><strong style="color: var(--accent-red);">${c.cantidad}</strong> unidades devueltas</td>
                </tr>
            `).join('');
        }
    }

    // Tabla Historial Devoluciones
    const tbodyHist = document.getElementById('tbody-devoluciones-recientes');
    if (tbodyHist) {
        const lista = dev.lista_recientes || [];
        if (lista.length === 0) {
            tbodyHist.innerHTML = `<tr><td colspan="7" class="text-center text-muted">No se registran devoluciones en el rango seleccionado.</td></tr>`;
        } else {
            tbodyHist.innerHTML = lista.map(d => `
                <tr>
                    <td>${d.fecha}</td>
                    <td><code>${d.codigo}</code></td>
                    <td><strong>${d.producto}</strong></td>
                    <td>${d.categoria}</td>
                    <td><strong style="color: var(--accent-red);">${d.cantidad}</strong></td>
                    <td>${d.motivo}</td>
                    <td style="font-weight: 700; color: var(--accent-red);">$${d.monto_estimado.toFixed(2)}</td>
                </tr>
            `).join('');
        }
    }
}

// --- 9. RENDER RESUMEN CONTABLE ---
function renderResumenContable(data) {
    const summaryBox = document.getElementById('accounting-summary');
    if (!summaryBox) return;

    const k = data.kpis || {};
    const c = data.compras || {};
    const inv = data.inventario_abc || {};

    summaryBox.innerHTML = `
        <h4 style="color: var(--primary); margin-bottom: 0.75rem;">📋 Reporte Consolidado para el Contador Externo (Lic. Fernando Rivas - Granada)</h4>
        <ul style="list-style: none; display: flex; flex-direction: column; gap: 0.6rem; color: var(--text-main);">
            <li><strong>Período evaluado:</strong> ${k.periodo_nombre} (${k.fecha_inicio} al ${k.fecha_fin})</li>
            <li><strong>Ventas acumuladas:</strong> ${k.transacciones} transacciones | <strong>${k.unidades_vendidas}</strong> repuestos vendidos por <strong>$${(k.ventas_netas || 0).toFixed(2)}</strong>.</li>
            <li><strong>Costo de Mercadería Vendida (COGS):</strong> $${(k.costo_ventas || 0).toFixed(2)}.</li>
            <li><strong>Utilidad Bruta Real Generada:</strong> <span style="color: var(--accent-green); font-weight: 700;">$${(k.utilidad_bruta || 0).toFixed(2)}</span> (Margen: ${k.margen_bruto_pct || 0}%).</li>
            <li><strong>Compras de Mercancía a Proveedores:</strong> ${c.total_conteo} adquisiciones por <strong>$${(c.total_monto || 0).toFixed(2)}</strong>.</li>
            <li><strong>Valoración Total de Inventario en Bodega (al Costo):</strong> $${(inv.valor_inventario_costo || 0).toFixed(2)}.</li>
            <li><strong>Capital Inmovilizado en Repuestos Sin Venta ("Hueso"):</strong> <span style="color: var(--accent-red); font-weight: 700;">$${(inv.capital_estancado_total || 0).toFixed(2)}</span>.</li>
            <li><strong>Índice de Rotación de Inventario:</strong> ${inv.rotacion_inventario || 0.0}x.</li>
        </ul>
    `;
}

// ==============================================================================
// GENERACIÓN Y EXPORTACIÓN DE INFORME EJECUTIVO (PDF / IMPRIMIR / EXCEL)
// ==============================================================================

function abrirInformeEjecutivoModal() {
    if (!reporteActualData) {
        alert('Cargando datos del informe, por favor espera un momento...');
        return;
    }
    renderInformeEjecutivoDocumento(reporteActualData);
    openModal('modal-informe-ejecutivo');
}

function renderInformeEjecutivoDocumento(data) {
    const container = document.getElementById('informe-ejecutivo-print-area');
    if (!container) return;

    const k = data.kpis || {};
    const cats = data.categorias || [];
    const pagos = data.metodos_pago || [];
    const criticos = data.alertas_criticas || [];
    const inv = data.inventario_abc || {};

    let catsRows = cats.slice(0, 8).map(c => `
        <tr>
            <td><strong>${c.categoria}</strong></td>
            <td>${c.unidades_vendidas}</td>
            <td>$${c.ingresos_netos.toFixed(2)}</td>
            <td>$${c.costo_ventas.toFixed(2)}</td>
            <td style="font-weight: 700;">$${c.utilidad_bruta.toFixed(2)}</td>
            <td>${c.margen_bruto_pct.toFixed(1)}%</td>
        </tr>
    `).join('');

    let pagosRows = pagos.map(p => `
        <tr>
            <td><strong>${p.metodo}</strong></td>
            <td>${p.transacciones}</td>
            <td style="font-weight: 700;">$${p.monto.toFixed(2)}</td>
            <td>${p.participacion_pct.toFixed(1)}%</td>
        </tr>
    `).join('');

    let criticosRows = criticos.slice(0, 8).map(p => `
        <tr>
            <td><code>${p.codigo}</code></td>
            <td><strong>${p.nombre}</strong></td>
            <td>${p.stock}</td>
            <td>${p.min_stock}</td>
            <td>${p.dias_cobertura !== null ? p.dias_cobertura + ' d' : 'S/D'}</td>
            <td style="font-weight: 700; color: #b45309;">+${p.sugerencia_reponer} unid</td>
        </tr>
    `).join('');

    container.innerHTML = `
        <div class="report-header-banner">
            <div>
                <div class="report-brand-title">JEHOVÁ JIREH MOTO REPUESTOS</div>
                <div class="report-brand-sub">Sistema de Gestión Comercial e Inteligencia de Negocios</div>
                <div style="font-size: 0.78rem; color: #64748b; margin-top: 0.2rem;">Masatepe, Masaya | Tel: +505 8899-0000 | Contacto de Calidad</div>
            </div>
            <div class="report-meta-box">
                <div><strong>DOCUMENTO:</strong> INFORME EJECUTIVO GERENCIAL</div>
                <div><strong>Período:</strong> ${k.periodo_nombre}</div>
                <div><strong>Rango:</strong> ${k.fecha_inicio} al ${k.fecha_fin}</div>
                <div><strong>Emisión:</strong> ${data.generado_en}</div>
                <div><strong>Generado por:</strong> ${data.generado_por}</div>
            </div>
        </div>

        <div class="report-section-title">1. Resumen Ejecutivo de Rendimiento Comercial (KPIs)</div>
        <table class="report-table-print">
            <thead>
                <tr>
                    <th>Ventas Netas</th>
                    <th>Costo de Ventas</th>
                    <th>Utilidad Bruta</th>
                    <th>Margen %</th>
                    <th>Unidades Vendidas</th>
                    <th>Transacciones</th>
                    <th>Ticket Promedio</th>
                </tr>
            </thead>
            <tbody>
                <tr>
                    <td style="font-size: 1.05rem; font-weight: 800; color: #047857;">$${(k.ventas_netas || 0).toFixed(2)}</td>
                    <td>$${(k.costo_ventas || 0).toFixed(2)}</td>
                    <td style="font-size: 1.05rem; font-weight: 800; color: #b45309;">$${(k.utilidad_bruta || 0).toFixed(2)}</td>
                    <td><strong>${(k.margen_bruto_pct || 0).toFixed(1)}%</strong></td>
                    <td>${k.unidades_vendidas || 0}</td>
                    <td>${k.transacciones || 0}</td>
                    <td>$${(k.ticket_promedio || 0).toFixed(2)}</td>
                </tr>
            </tbody>
        </table>

        <div class="report-section-title">2. Rendimiento y Rentabilidad por Categoría de Repuestos</div>
        <table class="report-table-print">
            <thead>
                <tr>
                    <th>Línea / Categoría</th>
                    <th>Unid.</th>
                    <th>Ventas Netas ($)</th>
                    <th>Costo ($)</th>
                    <th>Utilidad ($)</th>
                    <th>Margen (%)</th>
                </tr>
            </thead>
            <tbody>
                ${catsRows || '<tr><td colspan="6">Sin datos registrados</td></tr>'}
            </tbody>
        </table>

        <div style="display: flex; gap: 1.5rem;">
            <div style="flex: 1;">
                <div class="report-section-title">3. Composición de Cobranza (Métodos de Pago)</div>
                <table class="report-table-print">
                    <thead>
                        <tr>
                            <th>Método</th>
                            <th>Transac.</th>
                            <th>Total ($)</th>
                            <th>Part. %</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${pagosRows || '<tr><td colspan="4">Sin datos registrados</td></tr>'}
                    </tbody>
                </table>
            </div>

            <div style="flex: 1.3;">
                <div class="report-section-title">4. Control Preventivo (Stock Crítico)</div>
                <table class="report-table-print">
                    <thead>
                        <tr>
                            <th>Código</th>
                            <th>Repuesto</th>
                            <th>Stock</th>
                            <th>Mín</th>
                            <th>Autonomía</th>
                            <th>Sugerido</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${criticosRows || '<tr><td colspan="6">Stock en nivel óptimo</td></tr>'}
                    </tbody>
                </table>
            </div>
        </div>

        <div class="report-section-title">5. Balances de Inventario y Mercancía Estancada</div>
        <p style="font-size: 0.85rem; color: #334155; margin-bottom: 0.5rem;">
            * Valoración de inventario en bodega al costo: <strong>$${(inv.valor_inventario_costo || 0).toFixed(2)}</strong>.<br>
            * Rotación de inventario en período: <strong>${(inv.rotacion_inventario || 0).toFixed(2)}x</strong>.<br>
            * Capital inmovilizado en repuestos sin ventas ("Hueso"): <strong style="color: #b91c1c;">$${(inv.capital_estancado_total || 0).toFixed(2)}</strong>.
        </p>

        <div class="report-signatures">
            <div class="signature-block">
                <div class="signature-line"></div>
                <div style="font-weight: 700; font-size: 0.85rem;">Gilda Pérez</div>
                <div style="font-size: 0.75rem; color: #64748b;">Administración General</div>
            </div>
            <div class="signature-block">
                <div class="signature-line"></div>
                <div style="font-weight: 700; font-size: 0.85rem;">Lic. Fernando Rivas</div>
                <div style="font-size: 0.75rem; color: #64748b;">Contador Externo (Granada)</div>
            </div>
        </div>
    `;
}

function imprimirInformeEjecutivo() {
    document.body.classList.remove('print-mode-ticket');
    document.body.classList.add('print-mode-report');
    window.print();
    setTimeout(() => {
        document.body.classList.remove('print-mode-report');
    }, 1000);
}

function exportarReportesExcel() {
    if (!reporteActualData) {
        alert('Cargando datos para exportar...');
        return;
    }

    const data = reporteActualData;
    const k = data.kpis || {};
    const cats = data.categorias || [];
    const criticos = data.alertas_criticas || [];
    const inv = data.inventario_abc || {};
    const abc = inv.items_abc || [];

    let csvContent = "\uFEFF"; // UTF-8 BOM para que Excel abra caracteres latinos y acentos correctamente

    // 1. TÍTULO Y METADATOS
    csvContent += "JEHOVA JIREH MOTO REPUESTOS - INFORME ESTADISTICO Y GERENCIAL\n";
    csvContent += `Periodo:;${k.periodo_nombre} (${k.fecha_inicio} al ${k.fecha_fin})\n`;
    csvContent += `Fecha Generacion:;${data.generado_en}\n`;
    csvContent += `Generado Por:;${data.generado_por}\n\n`;

    // 2. RESUMEN DE KPIS
    csvContent += "RESUMEN DE INDICADORES CLAVE (KPIS)\n";
    csvContent += "Indicador;Valor\n";
    csvContent += `Ventas Netas ($);${k.ventas_netas}\n`;
    csvContent += `Costo de Ventas ($);${k.costo_ventas}\n`;
    csvContent += `Utilidad Bruta ($);${k.utilidad_bruta}\n`;
    csvContent += `Margen Bruto (%);${k.margen_bruto_pct}%\n`;
    csvContent += `Unidades Vendidas;${k.unidades_vendidas}\n`;
    csvContent += `Numero de Transacciones;${k.transacciones}\n`;
    csvContent += `Ticket Promedio ($);${k.ticket_promedio}\n`;
    csvContent += `Promedio Diario de Ventas ($);${k.promedio_diario}\n`;
    csvContent += `Rotacion de Inventario;${inv.rotacion_inventario}x\n\n`;

    // 3. RENTABILIDAD POR CATEGORÍA
    csvContent += "RENTABILIDAD POR CATEGORIA DE REPUESTOS\n";
    csvContent += "Categoria;Unidades Vendidas;Ingresos Netos ($);Participacion %;Costo Ventas ($);Utilidad Bruta ($);Margen Bruto (%)\n";
    cats.forEach(c => {
        csvContent += `"${c.categoria}";${c.unidades_vendidas};${c.ingresos_netos};${c.participacion_pct}%;${c.costo_ventas};${c.utilidad_bruta};${c.margen_bruto_pct}%\n`;
    });
    csvContent += "\n";

    // 4. CLASIFICACIÓN ABC
    csvContent += "CLASIFICACION ABC DE PRODUCTOS (PARETO)\n";
    csvContent += "Clasificacion;Codigo;Nombre;Categoria;Unidades;Valor Consumo ($);% Acumulado\n";
    abc.forEach(p => {
        csvContent += `Clase ${p.clase_abc};"${p.codigo}";"${p.nombre}";"${p.categoria}";${p.cantidad_vendida};${p.monto_total};${p.pct_acumulado}%\n`;
    });
    csvContent += "\n";

    // 5. ALERTAS DE STOCK CRÍTICO
    csvContent += "ALERTAS DE STOCK CRITICO Y COBERTURA\n";
    csvContent += "Codigo;Repuesto;Categoria;Stock Actual;Stock Minimo;Venta Diaria;Dias Cobertura;Sugerencia Reponer\n";
    criticos.forEach(p => {
        csvContent += `"${p.codigo}";"${p.nombre}";"${p.categoria}";${p.stock};${p.min_stock};${p.promedio_diario_ventas};${p.dias_cobertura !== null ? p.dias_cobertura : 'S/D'};${p.sugerencia_reponer}\n`;
    });

    // Descarga automática en navegador
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', `Reporte_Estadistico_Jehova_Jireh_${k.fecha_inicio}_${k.fecha_fin}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
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
