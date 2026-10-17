/**
 * JEHOVÁ JIREH MOTO REPUESTOS - CORTE V JAVASCRIPT MODULE
 * Implementación completa de requerimientos:
 * - Módulo Reportes/Estadísticas: RF58 - RF68
 * - Módulo Recursos Humanos y Nómina: RF69 - RF116
 */

// Global Safe Fallbacks
if (typeof window.cs !== 'function') {
    window.cs = function(n) {
        return 'C$ ' + (parseFloat(n) || 0).toLocaleString('es-NI', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    };
}
if (typeof window.formatMoneda !== 'function') {
    window.formatMoneda = window.cs;
}
if (typeof window.formatCantidad !== 'function') {
    window.formatCantidad = function(n) {
        return (parseInt(n) || 0).toLocaleString('es-NI');
    };
}

// =============================================================================
// 1. REPORTE Y ESTADÍSTICAS - CORTE V (RF58 - RF68)
// =============================================================================
window._filtroPresetActivo = window._filtroPresetActivo || 'mes';
window._criterioABCActual = window._criterioABCActual || 'inversion';
window._currentReportesTab = window._currentReportesTab || 'all';
window._filtroABCActual = window._filtroABCActual || 'todos';
window._demandaViewActual = window._demandaViewActual || 'top';

var _filtroPresetActivo = window._filtroPresetActivo;
var _criterioABCActual = window._criterioABCActual;
var _currentReportesTab = window._currentReportesTab;
var _demandaViewActual = window._demandaViewActual;

// Instancias globales para gráficos de Chart.js
if (typeof window.chartTendenciaInstance === 'undefined') window.chartTendenciaInstance = null;
if (typeof window.chartCategoriaInstance === 'undefined') window.chartCategoriaInstance = null;
if (typeof window.chartMetodosPagoInstance === 'undefined') window.chartMetodosPagoInstance = null;
if (typeof window.chartRentabilidadInstance === 'undefined') window.chartRentabilidadInstance = null;
if (typeof window._reporteDataCache === 'undefined') window._reporteDataCache = null;

/**
 * RF59: Pestañas internas de navegación del módulo de Reportes
 * Soporta 'all' (Vista General con todos los paneles) o vista individual por sub-panel
 */
function switchReportesTab(targetId) {
    if (targetId !== 'all' && _currentReportesTab === targetId) {
        targetId = 'all';
    }
    _currentReportesTab = targetId;

    // Actualizar botones de navegación
    document.querySelectorAll('.reportes-tab-btn').forEach(btn => {
        const btnTab = btn.getAttribute('data-rep-tab');
        const isActive = (btnTab === targetId);
        btn.classList.toggle('active', isActive);
        btn.setAttribute('aria-selected', isActive ? 'true' : 'false');
    });

    // Actualizar estilo del contenedor para separadores
    const wrapper = document.querySelector('.reportes-tabs-wrapper');
    if (wrapper) {
        wrapper.classList.toggle('mode-all', targetId === 'all');
    }

    // Mostrar u ocultar paneles correspondientes
    document.querySelectorAll('.rep-tab-panel').forEach(panel => {
        if (targetId === 'all') {
            panel.classList.add('active');
        } else {
            panel.classList.toggle('active', panel.id === targetId);
        }
    });

    // Redimensionar gráficos si se hacen visibles
    setTimeout(() => {
        if (window.chartTendenciaInstance) window.chartTendenciaInstance.resize();
        if (window.chartMetodosPagoInstance) window.chartMetodosPagoInstance.resize();
        if (window.chartCategoriaInstance) window.chartCategoriaInstance.resize();
        if (window.chartRentabilidadInstance) window.chartRentabilidadInstance.resize();
    }, 150);
}

/**
 * Desplegar / ocultar el menú de exportación
 */
function toggleMenuExportar(event) {
    if (event) {
        event.stopPropagation();
        event.preventDefault();
    }
    const menu = document.getElementById('dropdown-menu-exportar');
    if (!menu) return;
    const isVisible = (menu.style.display === 'block');
    menu.style.display = isVisible ? 'none' : 'block';
}

// Cerrar menú desplegable al hacer clic fuera
document.addEventListener('click', (e) => {
    const menu = document.getElementById('dropdown-menu-exportar');
    const btn = document.getElementById('btn-exportar-reporte');
    if (menu && menu.style.display === 'block') {
        if (!menu.contains(e.target) && (!btn || !btn.contains(e.target))) {
            menu.style.display = 'none';
        }
    }
});

/**
 * RF65: Generar Informe Ejecutivo Consolidado
 */
function generarInformeEjecutivo() {
    if (!window._reporteDataCache) {
        if (typeof Swal !== 'undefined') {
            Swal.fire('Cargando datos', 'Espere a que terminen de cargar las estadísticas antes de generar el informe.', 'info');
        } else {
            alert('Espere a que terminen de cargar las estadísticas antes de generar el informe.');
        }
        return;
    }
    if (typeof compilarInformeEjecutivo === 'function') {
        compilarInformeEjecutivo();
    } else if (typeof openModal === 'function') {
        openModal('modal-informe-ejecutivo');
    }
}

/**
 * RF65: Descarga directa del Informe Oficial en formato Excel (.xlsx)
 */
function exportarExcelReal() {
    const menu = document.getElementById('dropdown-menu-exportar');
    if (menu) menu.style.display = 'none';

    let url = '/api/reportes/exportar/excel?';
    const params = new URLSearchParams();

    if (_filtroPresetActivo === 'personalizado') {
        const d = document.getElementById('rep-fecha-inicio')?.value;
        const h = document.getElementById('rep-fecha-fin')?.value;
        if (!d || !h) {
            if (typeof Swal !== 'undefined') {
                Swal.fire('Atención', 'Selecciona ambas fechas (Desde y Hasta) para exportar el reporte.', 'warning');
            } else {
                alert('Selecciona ambas fechas (Desde y Hasta) para exportar.');
            }
            return;
        }
        params.append('fecha_inicio', d);
        params.append('fecha_fin', h);
    } else if (_filtroPresetActivo === 'mes_anio_directo') {
        const m = document.getElementById('rep-select-mes')?.value;
        const a = document.getElementById('rep-select-anio')?.value;
        if (m) params.append('mes', m);
        if (a) params.append('anio', a);
    } else if (_filtroPresetActivo && _filtroPresetActivo !== 'historico') {
        params.append('rango', _filtroPresetActivo);
    } else {
        params.append('rango', 'historico');
    }

    params.append('criterio_abc', _criterioABCActual || 'inversion');
    window.location.href = url + params.toString();
}

/**
 * RF58: Aplicar filtros temporales predeterminados (Hoy, 7 Días, Mes, Año, Histórico, Personalizado)
 */
function aplicarFiltroReportesPreset(preset) {
    _filtroPresetActivo = preset;

    // Actualizar botones visuales
    document.querySelectorAll('.btn-preset-reporte').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.preset === preset);
    });

    const fCustomContainer = document.getElementById('rep-filtro-fechas-custom');
    if (fCustomContainer) {
        fCustomContainer.style.display = (preset === 'personalizado') ? 'flex' : 'none';
        if (preset === 'personalizado') {
            const hoy = new Date().toISOString().split('T')[0];
            const dInput = document.getElementById('rep-fecha-inicio');
            const hInput = document.getElementById('rep-fecha-fin');
            if (hInput && !hInput.value) hInput.value = hoy;
            if (dInput && !dInput.value) {
                const primerDiaMes = new Date();
                primerDiaMes.setDate(1);
                dInput.value = primerDiaMes.toISOString().split('T')[0];
            }
            return; // Espera a que el usuario presione el botón de filtrar
        }
    }

    ejecutarConsultaReportes();
}

/**
 * Selección directa de Mes y Año en selectores desplegables
 */
function cambiarMesAnioDirecto() {
    _filtroPresetActivo = 'mes_anio_directo';

    // Desactivar botones de preset
    document.querySelectorAll('.btn-preset-reporte').forEach(btn => btn.classList.remove('active'));

    const fCustomContainer = document.getElementById('rep-filtro-fechas-custom');
    if (fCustomContainer) fCustomContainer.style.display = 'none';

    ejecutarConsultaReportes();
}

/**
 * RF63: Selección del Criterio ABC (Inversión en Bodega vs Ventas / Consumo)
 */
function cambiarCriterioABC(criterio) {
    _criterioABCActual = criterio;

    const btnInv = document.getElementById('btn-abc-inversion');
    const btnCons = document.getElementById('btn-abc-consumo');
    if (btnInv) btnInv.classList.toggle('active', criterio === 'inversion');
    if (btnCons) btnCons.classList.toggle('active', criterio === 'consumo');

    const badge = document.getElementById('rep-criterio-badge');
    if (badge) {
        badge.textContent = criterio === 'inversion' ? 'ABC: Inversión en Bodega' : 'ABC: Ventas / Consumo';
    }

    const desc = document.getElementById('txt-criterio-abc-desc');
    if (desc) {
        desc.textContent = criterio === 'inversion'
            ? 'Criterio actual: Inversión en Inventario (Capital en Bodega = stock * costo).'
            : 'Criterio actual: Ventas y Demanda del Período (Facturación e ingresos generados).';
    }

    ejecutarConsultaReportes();
}

/**
 * Mostrar / Ocultar panel de Modo Comparación
 */
function toggleModoComparar() {
    const panel = document.getElementById('rep-panel-comparacion');
    const btn = document.getElementById('btn-toggle-comparar');
    if (!panel) return;

    const estaAbierto = (panel.style.display === 'block');
    panel.style.display = estaAbierto ? 'none' : 'block';
    if (btn) btn.classList.toggle('active', !estaAbierto);
}

/**
 * Ejecutar comparación estadística entre dos períodos
 */
async function ejecutarComparacionPeriodos() {
    const mesA = document.getElementById('comp-mes-a')?.value || '10';
    const anioA = document.getElementById('comp-anio-a')?.value || '2025';
    const mesB = document.getElementById('comp-mes-b')?.value || '10';
    const anioB = document.getElementById('comp-anio-b')?.value || '2026';

    const url = `/api/reportes?comparar=1&mes=${mesA}&anio=${anioA}&mes2=${mesB}&anio2=${anioB}&criterio_abc=${_criterioABCActual}`;

    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data.error) {
            if (typeof Swal !== 'undefined') {
                Swal.fire('Error en Comparación', data.error, 'error');
            } else {
                alert('Error: ' + data.error);
            }
            return;
        }

        renderComparacionPeriodos(data, mesA, anioA, mesB, anioB);
    } catch (e) {
        console.error('Error al ejecutar comparación de períodos:', e);
        if (typeof Swal !== 'undefined') {
            Swal.fire('Error', 'No se pudo completar la comparación de períodos.', 'error');
        }
    }
}

function renderComparacionPeriodos(data, mesA, anioA, mesB, anioB) {
    const banner = document.getElementById('rep-banner-variaciones');
    const labelTitulos = document.getElementById('comp-label-titulos');
    const grid = document.getElementById('comp-grid-variaciones');

    if (!banner || !grid) return;

    const meses = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];
    const titA = `${meses[parseInt(mesA)] || mesA} ${anioA}`;
    const titB = `${meses[parseInt(mesB)] || mesB} ${anioB}`;

    if (labelTitulos) labelTitulos.textContent = `${titA} vs ${titB}`;

    const v = data.variaciones || {};
    const metrics = [
        { label: 'Ventas Totales', diff: v.ventas?.diff || 0, pct: v.ventas?.pct || 0, isMoney: true },
        { label: 'Utilidad Bruta', diff: v.utilidad?.diff || 0, pct: v.utilidad?.pct || 0, isMoney: true },
        { label: 'Margen Bruto', diff: v.margen_pct || 0, isPoints: true },
        { label: 'Unidades Vendidas', diff: v.unidades?.diff || 0, pct: v.unidades?.pct || 0 },
        { label: 'Comprobantes Emitidos', diff: v.transacciones?.diff || 0, pct: v.transacciones?.pct || 0 },
        { label: 'Ticket Promedio', diff: v.ticket?.diff || 0, pct: v.ticket?.pct || 0, isMoney: true }
    ];

    grid.innerHTML = metrics.map(m => {
        const esPositivo = m.diff >= 0;
        const color = esPositivo ? '#10b981' : '#ef4444';
        const icono = esPositivo ? '↑' : '↓';
        const formattedDiff = m.isPoints
            ? `${esPositivo ? '+' : ''}${m.diff}% pts`
            : (m.isMoney ? (esPositivo ? '+' : '') + formatMoneda(m.diff) : `${esPositivo ? '+' : ''}${m.diff}`);
        const formattedPct = m.pct !== undefined ? `(${esPositivo ? '+' : ''}${m.pct}%)` : '';

        return `
            <div style="background: var(--bg-card); border: 1px solid var(--border-color); border-radius: 6px; padding: 0.6rem 0.8rem;">
                <div style="font-size: 0.72rem; color: var(--text-muted); font-weight: 600;">${m.label}</div>
                <div style="font-size: 1.05rem; font-weight: 800; color: ${color}; margin: 2px 0;">
                    ${icono} ${formattedDiff}
                </div>
                <div style="font-size: 0.72rem; color: ${color}; font-weight: 600;">${formattedPct}</div>
            </div>
        `;
    }).join('');

    banner.style.display = 'block';

    // Renderizar datos del período B (el más reciente) en el resto de los componentes
    if (data.periodo_b) {
        window._reporteDataCache = data.periodo_b;
        renderReportesCompleto(data.periodo_b);
    }
}

function cerrarModoComparativo() {
    const banner = document.getElementById('rep-banner-variaciones');
    if (banner) banner.style.display = 'none';

    const panel = document.getElementById('rep-panel-comparacion');
    if (panel) panel.style.display = 'none';

    const btn = document.getElementById('btn-toggle-comparar');
    if (btn) btn.classList.remove('active');

    _filtroPresetActivo = 'mes';
    aplicarFiltroReportesPreset('mes');
}

/**
 * Consulta unificada al backend y distribución a todos los componentes
 */
async function ejecutarConsultaReportes() {
    let url = '/api/reportes?';
    const params = new URLSearchParams();

    if (_filtroPresetActivo === 'personalizado') {
        const d = document.getElementById('rep-fecha-inicio')?.value;
        const h = document.getElementById('rep-fecha-fin')?.value;
        if (!d || !h) {
            if (typeof Swal !== 'undefined') {
                Swal.fire('Atención', 'Selecciona ambas fechas (Desde y Hasta) para el filtro personalizado.', 'warning');
            } else {
                alert('Selecciona ambas fechas (Desde y Hasta) para el filtro personalizado.');
            }
            return;
        }
        params.append('fecha_inicio', d);
        params.append('fecha_fin', h);
    } else if (_filtroPresetActivo === 'mes_anio_directo') {
        const m = document.getElementById('rep-select-mes')?.value;
        const a = document.getElementById('rep-select-anio')?.value;
        if (m) params.append('mes', m);
        if (a) params.append('anio', a);
    } else if (_filtroPresetActivo && _filtroPresetActivo !== 'historico') {
        params.append('rango', _filtroPresetActivo);
    } else {
        params.append('rango', 'historico');
    }

    params.append('criterio_abc', _criterioABCActual || 'inversion');

    try {
        const res = await fetch(url + params.toString());
        const data = await res.json();
        if (data.error) {
            if (typeof Swal !== 'undefined') {
                Swal.fire('Error', data.error, 'error');
            } else {
                alert('Error: ' + data.error);
            }
            return;
        }

        // Sintetizar compatibilidad de alertas para modal si hace falta
        if (!data.alertas) {
            data.alertas = {
                desabastecimiento: (data.alertas_stock_minimo || []).map(a => ({
                    codigo: a.codigo,
                    nombre: a.nombre,
                    categoria: a.categoria,
                    stock_actual: a.stock,
                    stock_minimo: a.min_stock,
                    severidad: a.nivel,
                    clase_abc: a.clase_abc
                })),
                sobrestock: (data.rotacion_abc?.productos || [])
                    .filter(p => (p.unidades_vendidas || 0) === 0 && p.stock > 0)
                    .slice(0, 15)
                    .map(p => ({
                        codigo: p.codigo,
                        nombre: p.nombre,
                        categoria: p.categoria,
                        stock_actual: p.stock,
                        costo: p.costo,
                        valor_inmovilizado: p.valor_inmovilizado
                    }))
            };
        }

        window._reporteDataCache = data;
        renderReportesCompleto(data);

        // Devoluciones
        cargarEstadisticasDevoluciones();

    } catch (e) {
        console.error('Error cargando reportes con filtro dinámico:', e);
    }
}

/**
 * Renderizado de indicadores, tablas, gráficos y medidas descriptivas
 */
function renderReportesCompleto(data) {
    if (!data) return;

    // 1. Periodo y Badges superiores
    const pTexto = data.periodo?.texto || 'Histórico Completo';
    const elPeriodo = document.getElementById('rep-periodo-activo-texto');
    if (elPeriodo) elPeriodo.textContent = pTexto;

    const badgeABC = document.getElementById('rep-criterio-badge');
    if (badgeABC) {
        badgeABC.textContent = (_criterioABCActual === 'inversion') ? 'ABC: Inversión en Bodega' : 'ABC: Ventas / Consumo';
    }

    const k = data.kpis || {};
    const rotVal = Number(k.rotacion_monetaria_costo ?? k.rotacion_inventario ?? 0);
    const diasVal = Number(k.dias_inventario ?? 0);

    const bRot = document.getElementById('rep-badge-rotacion');
    if (bRot) bRot.textContent = `${rotVal.toFixed(2)}x`;

    const bDias = document.getElementById('rep-badge-dias');
    if (bDias) bDias.textContent = `${diasVal} días`;

    // 2. KPIs del Resumen General
    const elIngresos = document.getElementById('rep-ingresos');
    if (elIngresos) elIngresos.textContent = formatMoneda(k.ventas_totales_monto || 0);

    const elUnidades = document.getElementById('rep-unidades-vendidas');
    if (elUnidades) {
        const u = k.unidades_vendidas_total || 0;
        const v = k.ventas_totales_conteo || 0;
        elUnidades.textContent = `${formatCantidad(u)} unidades | ${formatCantidad(v)} ventas`;
    }

    const elCosto = document.getElementById('rep-costo-ventas');
    if (elCosto) elCosto.textContent = formatMoneda(k.costo_ventas_monto || 0);

    const elCogsSub = document.getElementById('rep-cogs-subtext');
    if (elCogsSub) {
        if (k.compras_totales_monto) {
            elCogsSub.textContent = `Compras período: ${formatMoneda(k.compras_totales_monto)}`;
        } else {
            elCogsSub.textContent = 'Costo histórico de productos vendidos';
        }
    }

    const elMargen = document.getElementById('rep-margen');
    if (elMargen) elMargen.textContent = formatMoneda(k.utilidad_bruta ?? k.margen_bruto_monto ?? 0);

    const elMargenPct = document.getElementById('rep-margen-pct');
    if (elMargenPct) elMargenPct.textContent = `Margen: ${(k.margen_bruto_porcentaje || 0).toFixed(2)}%`;

    const elTicket = document.getElementById('rep-ticket-promedio');
    if (elTicket) elTicket.textContent = formatMoneda(k.ticket_promedio || 0);

    const elTicketCnt = document.getElementById('rep-ticket-conteo');
    if (elTicketCnt) elTicketCnt.textContent = `Ticket medio (${formatCantidad(k.ventas_totales_conteo || 0)} comprobantes)`;

    const elRotacion = document.getElementById('rep-rotacion');
    if (elRotacion) elRotacion.textContent = `${rotVal.toFixed(4)}x`;

    const elRotSub = document.getElementById('rep-rotacion-subtext');
    if (elRotSub) elRotSub.textContent = 'Costo Ventas / Inv. al Costo';

    const elDias = document.getElementById('rep-dias-inventario');
    if (elDias) elDias.textContent = `${diasVal} días`;

    const elInvCosto = document.getElementById('rep-kpi-inv-costo');
    if (elInvCosto) elInvCosto.textContent = formatMoneda(k.valor_inventario_costo || 0);

    const elStockFisico = document.getElementById('rep-kpi-stock-fisico');
    if (elStockFisico) elStockFisico.textContent = `${formatCantidad(k.stock_total_actual || 0)} unidades en bodega`;

    const alertas = data.alertas_stock_minimo || [];
    const elAlertasTot = document.getElementById('rep-alertas-total');
    if (elAlertasTot) elAlertasTot.textContent = formatCantidad(alertas.length);

    const elAlertasSub = document.getElementById('rep-alertas-sub');
    if (elAlertasSub) {
        const totalProds = data.rotacion_abc?.total_productos || 235;
        elAlertasSub.textContent = `Auditoría sobre ${totalProds} repuestos`;
    }

    // 3. Gráficos Chart.js
    renderChartsReportes(data);

    // 4. Tabla Desglose Mensual del Año
    renderDesgloseMeses(data.desglose_mensual_anio);

    // 5. Tabla Rendimiento por Categoría
    renderTablaCategoriasReportes(data.categorias_analisis);

    // 6. Matriz de Rotación ABC
    renderTablaRotacionABCReportes(data.rotacion_abc);

    // 7. Ranking por Unidades Vendidas
    renderRankingUnidades(data.ranking_unidades);

    // 8. Repuestos Sin Movimiento
    renderRepuestosSinMovimiento(data.rotacion_abc);

    // 9. Alerta Universal de Stock Mínimo
    renderAlertaUniversalStock(data.alertas_stock_minimo);

    // 10. Medidas Estadísticas Descriptivas
    renderMedidasEstadisticas(data.medidas_estadisticas);

    // Compatibilidad adicional
    renderRepuestosDemanda();
}

/**
 * Gráficos con Chart.js
 */
function renderChartsReportes(data) {
    if (typeof Chart === 'undefined') return;

    // 1. Gráfico de Tendencia
    const ctxTendencia = document.getElementById('chart-ventas-tendencia');
    const emptyTendencia = document.getElementById('empty-state-tendencia');
    if (ctxTendencia) {
        if (window.chartTendenciaInstance) {
            window.chartTendenciaInstance.destroy();
            window.chartTendenciaInstance = null;
        }

        const lista = data.tendencia_lista || [];
        const tieneDatos = lista.length > 0 && lista.some(x => x.monto > 0);

        if (emptyTendencia) emptyTendencia.style.display = tieneDatos ? 'none' : 'flex';
        ctxTendencia.style.display = tieneDatos ? 'block' : 'none';

        if (tieneDatos) {
            const labels = lista.map(i => i.fecha);
            const montos = lista.map(i => i.monto);

            window.chartTendenciaInstance = new Chart(ctxTendencia, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Ventas (C$)',
                        data: montos,
                        borderColor: '#f59e0b',
                        backgroundColor: 'rgba(245, 158, 11, 0.12)',
                        borderWidth: 2.5,
                        fill: true,
                        tension: 0.3,
                        pointBackgroundColor: '#f59e0b',
                        pointRadius: 3.5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        x: { ticks: { color: '#94a3b8', font: { size: 10 } }, grid: { display: false } },
                        y: {
                            ticks: {
                                color: '#94a3b8',
                                font: { size: 10 },
                                callback: (val) => formatMoneda(val)
                            },
                            grid: { color: 'rgba(148, 163, 184, 0.08)' }
                        }
                    }
                }
            });
        }
    }

    // 2. Gráfico de Métodos de Pago
    const ctxMetodos = document.getElementById('chart-metodos-pago');
    const emptyMetodos = document.getElementById('empty-state-metodos');
    if (ctxMetodos) {
        if (window.chartMetodosPagoInstance) {
            window.chartMetodosPagoInstance.destroy();
            window.chartMetodosPagoInstance = null;
        }

        const metodos = data.metodos_pago || [];
        const tieneDatos = metodos.length > 0 && metodos.some(m => m.total > 0);

        if (emptyMetodos) emptyMetodos.style.display = tieneDatos ? 'none' : 'flex';
        ctxMetodos.style.display = tieneDatos ? 'block' : 'none';

        if (tieneDatos) {
            window.chartMetodosPagoInstance = new Chart(ctxMetodos, {
                type: 'doughnut',
                data: {
                    labels: metodos.map(m => m.metodo),
                    datasets: [{
                        data: metodos.map(m => m.total),
                        backgroundColor: ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ec4899'],
                        borderWidth: 2,
                        borderColor: '#0f172a'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: '#cbd5e1', font: { size: 11 }, boxWidth: 12 } }
                    }
                }
            });
        }
    }

    // 3. Gráfico de Rentabilidad por Categoría (Bar)
    const ctxRent = document.getElementById('chart-rentabilidad-categoria');
    const emptyRent = document.getElementById('empty-state-rentabilidad');
    if (ctxRent) {
        if (window.chartRentabilidadInstance) {
            window.chartRentabilidadInstance.destroy();
            window.chartRentabilidadInstance = null;
        }

        const cats = data.categorias_analisis || [];
        const tieneDatos = cats.length > 0 && cats.some(c => c.total_ventas > 0);

        if (emptyRent) emptyRent.style.display = tieneDatos ? 'none' : 'flex';
        ctxRent.style.display = tieneDatos ? 'block' : 'none';

        if (tieneDatos) {
            window.chartRentabilidadInstance = new Chart(ctxRent, {
                type: 'bar',
                data: {
                    labels: cats.map(c => c.categoria),
                    datasets: [{
                        label: 'Utilidad Bruta (C$)',
                        data: cats.map(c => c.margen),
                        backgroundColor: '#10b981',
                        borderRadius: 4
                    }, {
                        label: 'Ventas Totales (C$)',
                        data: cats.map(c => c.total_ventas),
                        backgroundColor: '#3b82f6',
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'top', labels: { color: '#cbd5e1', font: { size: 10 }, boxWidth: 10 } }
                    },
                    scales: {
                        x: { ticks: { color: '#94a3b8', font: { size: 9.5 } }, grid: { display: false } },
                        y: {
                            ticks: {
                                color: '#94a3b8',
                                font: { size: 9.5 },
                                callback: (v) => formatMoneda(v)
                            },
                            grid: { color: 'rgba(148, 163, 184, 0.08)' }
                        }
                    }
                }
            });
        }
    }

    // 4. Gráfico Cuota de Categorías (Doughnut)
    const ctxCat = document.getElementById('chart-ventas-categoria');
    const emptyCat = document.getElementById('empty-state-categoria');
    if (ctxCat) {
        if (window.chartCategoriaInstance) {
            window.chartCategoriaInstance.destroy();
            window.chartCategoriaInstance = null;
        }

        const cats = data.categorias_analisis || [];
        const tieneDatos = cats.length > 0 && cats.some(c => c.total_ventas > 0);

        if (emptyCat) emptyCat.style.display = tieneDatos ? 'none' : 'flex';
        ctxCat.style.display = tieneDatos ? 'block' : 'none';

        if (tieneDatos) {
            window.chartCategoriaInstance = new Chart(ctxCat, {
                type: 'doughnut',
                data: {
                    labels: cats.map(c => c.categoria),
                    datasets: [{
                        data: cats.map(c => c.total_ventas),
                        backgroundColor: ['#38bdf8', '#10b981', '#f59e0b', '#a855f7', '#ec4899', '#6366f1', '#14b8a6'],
                        borderWidth: 2,
                        borderColor: '#0f172a'
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { position: 'right', labels: { color: '#cbd5e1', font: { size: 10 }, boxWidth: 10 } }
                    }
                }
            });
        }
    }
}

/**
 * Tabla: Desglose Anual por Meses
 */
function renderDesgloseMeses(desglose) {
    const tbody = document.getElementById('tbody-desglose-meses');
    if (!tbody) return;
    if (!desglose || desglose.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding: 1.5rem;">Sin registros de ventas mensuales en el período.</td></tr>';
        return;
    }
    const mesesNombres = ['', 'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'];
    tbody.innerHTML = desglose.map(m => `
        <tr>
            <td><strong>${m.nombre_mes || mesesNombres[m.mes] || ('Mes ' + m.mes)}</strong></td>
            <td style="text-align: center;">${formatCantidad(m.transacciones)}</td>
            <td style="text-align: center;">${formatCantidad(m.unidades)}</td>
            <td style="text-align: right; font-weight: 700; color: var(--text-main);">${formatMoneda(m.ventas)}</td>
            <td style="text-align: right; color: var(--text-muted);">${formatMoneda(m.costo)}</td>
            <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${formatMoneda(m.utilidad)}</td>
            <td style="text-align: right; font-weight: 700; color: ${(m.margen_porcentaje >= 20 ? 'var(--accent-green)' : 'var(--warning)')};">${(m.margen_porcentaje || 0).toFixed(2)}%</td>
        </tr>
    `).join('');
}

/**
 * Tabla: Rendimiento y Márgenes por Categoría (7 columnas)
 */
function renderTablaCategoriasReportes(categorias) {
    const tbody = document.getElementById('tbody-rendimiento-categorias');
    if (!tbody) return;
    if (!categorias || categorias.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding: 1.5rem;">Sin ventas registradas por categoría en este período.</td></tr>';
        return;
    }
    tbody.innerHTML = categorias.map(c => `
        <tr>
            <td><strong>${c.categoria}</strong></td>
            <td style="text-align: center; font-weight: 600;">${formatCantidad(c.unidades)}</td>
            <td style="text-align: right; font-weight: 700; color: var(--text-main);">${formatMoneda(c.total_ventas)}</td>
            <td style="text-align: right; color: var(--text-muted);">${formatMoneda(c.costo_ventas)}</td>
            <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${formatMoneda(c.margen)}</td>
            <td style="text-align: right; font-weight: 700; color: ${(c.margen_porcentaje >= 20 ? 'var(--accent-green)' : 'var(--warning)')};">${(c.margen_porcentaje || 0).toFixed(2)}%</td>
            <td style="text-align: right; color: var(--text-muted); font-weight: 600;">${(c.participacion_porcentaje || 0).toFixed(2)}%</td>
        </tr>
    `).join('');
}

/**
 * Tabla: Clasificación y Rotación ABC (9 columnas)
 */
function renderTablaRotacionABCReportes(rotacionData) {
    if (!rotacionData) return;

    const elTotal = document.getElementById('count-abc-todos');
    const elA = document.getElementById('count-abc-a');
    const elB = document.getElementById('count-abc-b');
    const elC = document.getElementById('count-abc-c');

    if (elTotal) elTotal.textContent = formatCantidad(rotacionData.total_productos || 0);
    if (elA) elA.textContent = formatCantidad(rotacionData.conteo_clase_a || 0);
    if (elB) elB.textContent = formatCantidad(rotacionData.conteo_clase_b || 0);
    if (elC) elC.textContent = formatCantidad(rotacionData.conteo_clase_c || 0);

    aplicarFiltroLocalTablaABC();
}

function filtrarTablaABC(clase) {
    _filtroABCActual = clase;
    ['todos', 'a', 'b', 'c'].forEach(b => {
        const btn = document.getElementById(`btn-filtro-abc-${b}`);
        if (btn) btn.classList.toggle('active', (b === clase.toLowerCase() || (b === 'todos' && clase === 'todos')));
    });
    aplicarFiltroLocalTablaABC();
}

function filtrarTablaABCPorTexto(texto) {
    aplicarFiltroLocalTablaABC();
}

function aplicarFiltroLocalTablaABC() {
    const tbody = document.getElementById('tbody-rotacion-abc');
    if (!tbody || !window._reporteDataCache || !window._reporteDataCache.rotacion_abc) return;

    let prods = window._reporteDataCache.rotacion_abc.productos || [];

    if (_filtroABCActual && _filtroABCActual !== 'todos') {
        prods = prods.filter(p => p.clase_abc === _filtroABCActual);
    }

    const q = document.getElementById('busqueda-tabla-abc')?.value.trim().toLowerCase();
    if (q) {
        prods = prods.filter(p =>
            (p.nombre && p.nombre.toLowerCase().includes(q)) ||
            (p.codigo && p.codigo.toLowerCase().includes(q)) ||
            (p.categoria && p.categoria.toLowerCase().includes(q))
        );
    }

    if (prods.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted" style="padding: 1.5rem;">No se encontraron repuestos con los filtros seleccionados.</td></tr>';
        return;
    }

    tbody.innerHTML = prods.map(p => {
        let badgeClase = '';
        if (p.clase_abc === 'A') {
            badgeClase = `<span class="badge" style="background: rgba(16, 185, 129, 0.2); color: var(--accent-green); font-weight: 800; border: 1px solid rgba(16, 185, 129, 0.4);">Clase A</span>`;
        } else if (p.clase_abc === 'B') {
            badgeClase = `<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: var(--warning); font-weight: 800; border: 1px solid rgba(245, 158, 11, 0.4);">Clase B</span>`;
        } else {
            badgeClase = `<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: var(--accent-red); font-weight: 800; border: 1px solid rgba(239, 68, 68, 0.4);">Clase C</span>`;
        }

        const bajoStock = p.stock <= p.min_stock;
        const stockIcon = bajoStock ? ' <i class="ph-bold ph-warning" style="color: var(--accent-red);" title="Stock bajo o agotado"></i>' : '';

        return `
            <tr>
                <td>${badgeClase}</td>
                <td><code style="font-size: 0.8rem;">${p.codigo || '—'}</code></td>
                <td><strong>${p.nombre}</strong></td>
                <td><span style="font-size: 0.82rem; color: var(--text-muted);">${p.categoria || '—'}</span></td>
                <td style="text-align: center; font-weight: 700; ${bajoStock ? 'color: var(--accent-red);' : ''}">${formatCantidad(p.stock)}${stockIcon}</td>
                <td style="text-align: right;">${formatMoneda(p.costo)}</td>
                <td style="text-align: right; font-weight: 700; color: var(--warning);">${formatMoneda(p.valor_inmovilizado)}</td>
                <td style="text-align: center; font-weight: 700;">${formatCantidad(p.unidades_vendidas)}</td>
                <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${formatMoneda(p.ingreso_generado)}</td>
            </tr>
        `;
    }).join('');
}

/**
 * Tabla: Ranking por Unidades Físicas Vendidas
 */
function renderRankingUnidades(ranking) {
    const tbody = document.getElementById('tbody-ranking-unidades');
    if (!tbody) return;
    if (!ranking || ranking.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-muted" style="padding: 1.5rem;">Sin registros de ventas en el período.</td></tr>';
        return;
    }
    tbody.innerHTML = ranking.map((p, idx) => `
        <tr>
            <td style="font-weight: 800; color: var(--primary); text-align: center; width: 35px;">#${idx + 1}</td>
            <td><strong>${p.nombre}</strong><br><small class="text-muted">SKU: ${p.codigo || '—'} | ${p.categoria || '—'}</small></td>
            <td style="text-align: center; font-weight: 700;">${formatCantidad(p.unidades_vendidas || p.cantidad_vendida || 0)} uds.</td>
            <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${formatMoneda(p.ingreso_generado || p.monto_total || 0)}</td>
        </tr>
    `).join('');
}

/**
 * Tabla: Repuestos Sin Movimiento en el Período
 */
function renderRepuestosSinMovimiento(rotacionData) {
    const tbody = document.getElementById('tbody-repuestos-sin-movimiento');
    const badge = document.getElementById('badge-conteo-sin-movimiento');
    if (!tbody) return;

    const prods = (rotacionData?.productos || []).filter(p => (p.unidades_vendidas || 0) === 0);
    if (badge) badge.textContent = `${formatCantidad(prods.length)} repuestos`;

    if (prods.length === 0) {
        tbody.innerHTML = '<tr><td colspan="4" class="text-center text-accent-green" style="padding: 1.5rem;">¡Excelente! Todos los repuestos registraron ventas en el período.</td></tr>';
        return;
    }

    tbody.innerHTML = prods.slice(0, 50).map(p => `
        <tr>
            <td><strong>${p.nombre}</strong><br><small class="text-muted">SKU: ${p.codigo || '—'} | ${p.categoria || '—'}</small></td>
            <td style="text-align: center; font-weight: 700;">${formatCantidad(p.stock)}</td>
            <td style="text-align: right;">${formatMoneda(p.costo)}</td>
            <td style="text-align: right; font-weight: 700; color: var(--warning);">${formatMoneda(p.valor_inmovilizado)}</td>
        </tr>
    `).join('');
}

/**
 * Tabla: Alerta Universal de Stock Mínimo (Auditoría Integral de los 235 repuestos)
 */
function renderAlertaUniversalStock(alertas) {
    const tbody = document.getElementById('tbody-alertas-stock-universal');
    const badge = document.getElementById('badge-alerta-universal-count');
    if (!tbody) return;

    const list = alertas || [];
    if (badge) badge.textContent = `${formatCantidad(list.length)} repuestos`;

    if (list.length === 0) {
        tbody.innerHTML = '<tr><td colspan="9" class="text-center text-accent-green" style="padding: 1.5rem;">¡Excelente! No hay repuestos en o bajo su nivel de stock mínimo.</td></tr>';
        return;
    }

    tbody.innerHTML = list.map(a => {
        let badgeNivel = '';
        if (a.nivel === 'Agotado') {
            badgeNivel = `<span class="badge" style="background: #dc2626; color: #fff; font-weight: 700;">Agotado (0)</span>`;
        } else if (a.nivel === 'Crítico') {
            badgeNivel = `<span class="badge" style="background: #ea580c; color: #fff; font-weight: 700;">Crítico (&le;50%)</span>`;
        } else {
            badgeNivel = `<span class="badge" style="background: #f59e0b; color: #1e293b; font-weight: 700;">Bajo Mínimo</span>`;
        }

        return `
            <tr>
                <td>${badgeNivel}</td>
                <td><code style="font-size: 0.8rem;">${a.codigo || '—'}</code></td>
                <td><strong>${a.nombre}</strong></td>
                <td><span style="font-size: 0.82rem; color: var(--text-muted);">${a.categoria || '—'}</span></td>
                <td style="text-align: center; font-weight: 800; color: var(--accent-red);">${formatCantidad(a.stock)}</td>
                <td style="text-align: center; color: var(--text-muted);">${formatCantidad(a.min_stock)}</td>
                <td style="text-align: center; font-weight: 700; color: var(--accent-red);">${formatCantidad(Math.max(0, a.min_stock - a.stock))}</td>
                <td style="text-align: right; font-weight: 700;">${formatMoneda(Math.max(0, a.min_stock - a.stock) * a.costo)}</td>
                <td style="text-align: center;"><span class="badge" style="background: rgba(148,163,184,0.15); color: var(--text-main); font-weight: 700;">${a.clase_abc || 'A'}</span></td>
            </tr>
        `;
    }).join('');
}

/**
 * Indicadores: Medidas Estadísticas Descriptivas de las Ventas
 */
function renderMedidasEstadisticas(m) {
    if (!m) return;

    if (document.getElementById('stat-n')) document.getElementById('stat-n').textContent = m.n || 0;
    if (document.getElementById('stat-media')) document.getElementById('stat-media').textContent = formatMoneda(m.media || 0);
    if (document.getElementById('stat-mediana')) document.getElementById('stat-mediana').textContent = formatMoneda(m.mediana || 0);
    if (document.getElementById('stat-max')) document.getElementById('stat-max').textContent = formatMoneda(m.maximo || 0);
    if (document.getElementById('stat-min')) document.getElementById('stat-min').textContent = formatMoneda(m.minimo || 0);
    if (document.getElementById('stat-rango')) document.getElementById('stat-rango').textContent = formatMoneda(m.rango || 0);
    if (document.getElementById('stat-varianza')) {
        document.getElementById('stat-varianza').textContent = (m.varianza || 0).toLocaleString('es-NI', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    if (document.getElementById('stat-desv')) document.getElementById('stat-desv').textContent = formatMoneda(m.desviacion_estandar || 0);
    if (document.getElementById('stat-cv')) document.getElementById('stat-cv').textContent = `${(m.coeficiente_variacion || 0).toFixed(2)}%`;
    if (document.getElementById('stat-interpretacion')) {
        document.getElementById('stat-interpretacion').textContent = m.interpretacion || 'Sin datos suficientes para interpretación estadística.';
    }
}

/**
 * RF66: Repuestos más y menos vendidos (vistas alternativas)
 */
function toggleDemandaView(tipo) {
    _demandaViewActual = tipo;
    document.getElementById('btn-demanda-top')?.classList.toggle('active', tipo === 'top');
    document.getElementById('btn-demanda-bottom')?.classList.toggle('active', tipo === 'bottom');
    renderRepuestosDemanda();
}

function renderRepuestosDemanda() {
    if (!window._reporteDataCache) return;
    const tbody = document.getElementById('tbody-repuestos-demanda');
    const titleEl = document.getElementById('title-repuestos-demanda');
    if (!tbody) return;

    const limite = parseInt(document.getElementById('select-demanda-limit')?.value || '10');

    if (_demandaViewActual === 'top') {
        if (titleEl) titleEl.innerHTML = '<i class="ph-bold ph-star" style="color: var(--warning);"></i> Top Repuestos Más Vendidos';
        const prods = (window._reporteDataCache.top_productos || []).slice(0, limite);
        if (prods.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:1.5rem;">Sin registros de ventas en el período.</td></tr>';
            return;
        }
        tbody.innerHTML = prods.map((p, idx) => `
            <tr>
                <td style="font-weight: 700; width: 40px; text-align: center; color: var(--primary);">#${idx + 1}</td>
                <td><strong>${p.nombre}</strong><br><small class="text-muted">SKU: ${p.codigo || '—'} | ${p.categoria || '—'}</small></td>
                <td style="text-align: center; font-weight: 700;">${p.unidades_vendidas || p.cantidad_vendida || 0} uds.</td>
                <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${formatMoneda(p.ingreso_generado || p.monto_total || 0)}</td>
                <td style="text-align: center;"><span class="badge" style="background: rgba(34,197,94,0.15); color: #22c55e;">Clase ${p.clase_abc || 'A'}</span></td>
            </tr>
        `).join('');
    } else {
        if (titleEl) titleEl.innerHTML = '<i class="ph-bold ph-trend-down" style="color: var(--accent-red);"></i> Repuestos con Menor Demanda / Sin Movimiento';
        const prods = (window._reporteDataCache.bottom_productos || []).slice(0, limite);
        if (prods.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:1.5rem;">No se encontraron repuestos con baja demanda.</td></tr>';
            return;
        }
        tbody.innerHTML = prods.map((p, idx) => `
            <tr>
                <td style="font-weight: 700; width: 40px; text-align: center; color: var(--text-muted);">#${idx + 1}</td>
                <td><strong>${p.nombre}</strong><br><small class="text-muted">SKU: ${p.codigo || '—'} | Stock: ${p.stock || 0} uds.</small></td>
                <td style="text-align: center; font-weight: 700; color: var(--accent-red);">${p.unidades_vendidas || p.cantidad_vendida || 0} uds.</td>
                <td style="text-align: right; font-weight: 700; color: var(--warning);">${formatMoneda(p.valor_inmovilizado || p.costo_inmovilizado || 0)} <small class="text-muted"><br>inmovilizado</small></td>
                <td style="text-align: center;"><span class="badge" style="background: rgba(239,68,68,0.15); color: #ef4444;">Clase C</span></td>
            </tr>
        `).join('');
    }
}

/**
 * RF68: Devoluciones y garantías de ventas
 */
async function cargarEstadisticasDevoluciones() {
    try {
        const res = await fetch('/api/reportes/devoluciones');
        const data = await res.json();

        if (document.getElementById('kpi-dev-operaciones')) document.getElementById('kpi-dev-operaciones').textContent = data.total_operaciones || 0;
        if (document.getElementById('kpi-dev-unidades')) document.getElementById('kpi-dev-unidades').textContent = (data.total_unidades || 0) + ' uds.';
        if (document.getElementById('kpi-dev-monto')) document.getElementById('kpi-dev-monto').textContent = formatMoneda(data.total_monto || 0);

        const tbody = document.getElementById('tbody-devoluciones-estadisticas');
        if (tbody) {
            const list = data.detalle || [];
            if (list.length === 0) {
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding:1.5rem;">No se registran devoluciones de repuestos en el sistema.</td></tr>';
                return;
            }
            tbody.innerHTML = list.map(d => `
                <tr>
                    <td><strong>#DEV-${d.id}</strong></td>
                    <td>Venta #${d.venta_id}</td>
                    <td>${d.fecha || '—'}</td>
                    <td><strong>${d.producto}</strong><br><small class="text-muted">${d.codigo}</small></td>
                    <td><span class="badge" style="background: rgba(245,158,11,0.15); color: var(--warning);">${d.motivo}</span></td>
                    <td style="text-align: right; font-weight: 700; color: var(--accent-red);">${formatMoneda(d.subtotal)}</td>
                </tr>
            `).join('');
        }
    } catch (e) {
        console.error('Error cargando devoluciones:', e);
    }
}

// =============================================================================
// 2. MÓDULO RECURSOS HUMANOS - CORTE V
// =============================================================================

// Variable global de caché
let _solicitudesCache = [];
let _contratosCache = [];
let _jornadasCache = [];
let _asistenciaCache = [];
let _horasExtrasCache = [];
let _liquidacionesCache = [];
let _pagosNominaCache = [];

// Inicializador de submódulos de RRHH al cambiar de pestaña
function initRrhhCorteVTab(tabId) {
    if (tabId === 'rrhh-reclutamiento' || tabId === 'all') {
        cargarSolicitudesEmpleo();
        cargarContratosLaborales();
    }
    if (tabId === 'rrhh-asistencia' || tabId === 'all') {
        cargarJornadasLaborales();
        cargarAsistenciaDiaria();
        cargarHorasExtras();
    }
    if (tabId === 'rrhh-historial' || tabId === 'all') {
        cargarLiquidacionesLaborales();
        cargarPagosNomina();
    }
    if (tabId === 'rrhh-seguridad' || tabId === 'all') {
        cargarRiesgosHigiene();
        cargarIncidentesHigiene();
        cargarEppHigiene();
        cargarCapacitacionesHigiene();
        cargarInspeccionesHigiene();
    }
    if (tabId === 'rrhh-legal' || tabId === 'all') {
        cargarMarcoLegal();
        cargarParametrosLaborales();
    }
}

// -----------------------------------------------------------------------------
// RF95, RF96: SOLICITUDES DE EMPLEO Y RECLUTAMIENTO
// -----------------------------------------------------------------------------
async function cargarSolicitudesEmpleo() {
    try {
        const res = await fetch('/api/rrhh/solicitudes');
        const data = await res.json();
        _solicitudesCache = data;

        const tbody = document.getElementById('tbody-solicitudes-empleo');
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding:1.5rem;">No hay solicitudes de empleo registradas.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(s => {
            let badgeBg = 'rgba(100,116,139,0.15)', badgeCol = '#64748b';
            if (s.estado === 'Seleccionada') { badgeBg = 'rgba(34,197,94,0.15)'; badgeCol = '#22c55e'; }
            else if (s.estado === 'Entrevista') { badgeBg = 'rgba(59,130,246,0.15)'; badgeCol = '#3b82f6'; }
            else if (s.estado === 'En revisión') { badgeBg = 'rgba(245,158,11,0.15)'; badgeCol = '#f59e0b'; }
            else if (s.estado === 'No seleccionada') { badgeBg = 'rgba(239,68,68,0.15)'; badgeCol = '#ef4444'; }

            return `
                <tr>
                    <td><code>${s.codigo_solicitud || 'SOL-' + s.id}</code></td>
                    <td><strong>${s.nombres_apellidos}</strong><br><small class="text-muted">Céd: ${s.identificacion} | Tel: ${s.telefono}</small></td>
                    <td><strong>${s.puesto_solicitado}</strong></td>
                    <td style="text-align: right; font-weight: 700;">${cs(s.salario_pretendido)}</td>
                    <td><span class="badge" style="background:${badgeBg}; color:${badgeCol}; font-weight:700;">${s.estado}</span></td>
                    <td>${s.fecha_registro?.slice(0, 10) || '—'}</td>
                    <td>
                        <div style="display:flex; gap:4px;">
                            <button class="btn btn-secondary" style="padding:3px 7px; font-size:0.75rem;" onclick="abrirModalEstadoSolicitud(${s.id})" title="Cambiar Estado">
                                <i class="ph-bold ph-pencil-simple"></i>
                            </button>
                            ${s.estado !== 'Seleccionada' ? `
                                <button class="btn btn-primary" style="padding:3px 7px; font-size:0.75rem;" onclick="contratarAspirante(${s.id})" title="Contratar e incorporar como empleado">
                                    <i class="ph-bold ph-user-check"></i> Contratar
                                </button>
                            ` : '<span style="color:#22c55e; font-size:0.75rem; font-weight:700;">✓ Contratado</span>'}
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Error cargando solicitudes:', e);
    }
}

function abrirModalNuevaSolicitud() {
    document.getElementById('form-nueva-solicitud')?.reset();
    openModal('modal-solicitud-empleo');
}

async function guardarSolicitudEmpleo(e) {
    if (e) e.preventDefault();
    const data = {
        nombres_apellidos: document.getElementById('sol-nombre').value.trim(),
        identificacion: document.getElementById('sol-cedula').value.trim(),
        telefono: document.getElementById('sol-telefono').value.trim(),
        email: document.getElementById('sol-email').value.trim(),
        direccion: document.getElementById('sol-direccion').value.trim(),
        puesto_solicitado: document.getElementById('sol-puesto').value.trim(),
        formacion_academica: document.getElementById('sol-formacion').value.trim(),
        experiencia_laboral: document.getElementById('sol-experiencia').value.trim(),
        referencias_laborales: document.getElementById('sol-referencias').value.trim(),
        salario_pretendido: parseFloat(document.getElementById('sol-salario').value || 0),
        disponibilidad: document.getElementById('sol-disponibilidad').value,
        observaciones: document.getElementById('sol-observaciones').value.trim()
    };

    if (!data.nombres_apellidos || !data.identificacion || !data.telefono || !data.puesto_solicitado) {
        Swal.fire('Campos requeridos', 'Por favor complete nombres, cédula, teléfono y puesto.', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/rrhh/solicitudes', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const resp = await res.json();
        if (res.ok) {
            Swal.fire('¡Éxito!', resp.mensaje || 'Solicitud registrada correctamente.', 'success');
            closeModal('modal-solicitud-empleo');
            cargarSolicitudesEmpleo();
        } else {
            Swal.fire('Error', resp.error || 'No se pudo registrar la solicitud.', 'error');
        }
    } catch (err) {
        Swal.fire('Error', 'Fallo de conexión al registrar la solicitud.', 'error');
    }
}

async function abrirModalEstadoSolicitud(id) {
    const s = _solicitudesCache.find(x => x.id === id);
    if (!s) return;

    const { value: formValues } = await Swal.fire({
        title: `Actualizar Estado: ${s.nombres_apellidos}`,
        html: `
            <div style="text-align: left; font-size: 0.9rem;">
                <label style="display:block; margin-bottom: 4px; font-weight:600;">Nuevo Estado:</label>
                <select id="swal-estado-sol" class="form-control" style="width:100%; margin-bottom: 12px;">
                    <option value="Recibida" ${s.estado === 'Recibida' ? 'selected' : ''}>Recibida</option>
                    <option value="En revisión" ${s.estado === 'En revisión' ? 'selected' : ''}>En revisión</option>
                    <option value="Entrevista" ${s.estado === 'Entrevista' ? 'selected' : ''}>Entrevista</option>
                    <option value="Seleccionada" ${s.estado === 'Seleccionada' ? 'selected' : ''}>Seleccionada</option>
                    <option value="No seleccionada" ${s.estado === 'No seleccionada' ? 'selected' : ''}>No seleccionada</option>
                </select>
                <label style="display:block; margin-bottom: 4px; font-weight:600;">Observaciones del proceso:</label>
                <textarea id="swal-obs-sol" class="form-control" style="width:100%; height: 70px;">${s.observaciones || ''}</textarea>
            </div>
        `,
        focusConfirm: false,
        showCancelButton: true,
        confirmButtonText: 'Guardar Estado',
        cancelButtonText: 'Cancelar',
        preConfirm: () => {
            return {
                estado: document.getElementById('swal-estado-sol').value,
                observaciones: document.getElementById('swal-obs-sol').value
            };
        }
    });

    if (formValues) {
        const res = await fetch(`/api/rrhh/solicitudes/${id}/estado`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formValues)
        });
        if (res.ok) {
            Swal.fire('Actualizado', 'Estado de la solicitud actualizado.', 'success');
            cargarSolicitudesEmpleo();
        } else {
            Swal.fire('Error', 'No se pudo actualizar el estado.', 'error');
        }
    }
}

async function contratarAspirante(id) {
    const s = _solicitudesCache.find(x => x.id === id);
    if (!s) return;

    const confirm = await Swal.fire({
        title: `¿Contratar a ${s.nombres_apellidos}?`,
        text: `Se creará el registro como empleado formal en el Directorio y se vinculará con su solicitud.`,
        icon: 'question',
        showCancelButton: true,
        confirmButtonText: 'Sí, Contratar',
        cancelButtonText: 'Cancelar'
    });

    if (!confirm.isConfirmed) return;

    try {
        const res = await fetch(`/api/rrhh/solicitudes/${id}/contratar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                salario_base: s.salario_pretendido || 7000,
                cargo: s.puesto_solicitado
            })
        });
        const resp = await res.json();
        if (res.ok) {
            Swal.fire('¡Empleado Contratado!', resp.mensaje, 'success');
            cargarSolicitudesEmpleo();
            if (typeof cargarEmpleadosRRHH === 'function') cargarEmpleadosRRHH();
        } else {
            Swal.fire('Error al contratar', resp.error, 'error');
        }
    } catch (e) {
        Swal.fire('Error', 'Fallo de conexión.', 'error');
    }
}

// -----------------------------------------------------------------------------
// RF98, RF99: CONTRATOS LABORALES Y CONTROL DE VIGENCIA
// -----------------------------------------------------------------------------
async function cargarContratosLaborales() {
    try {
        const res = await fetch('/api/rrhh/contratos');
        const data = await res.json();
        _contratosCache = data;

        const tbody = document.getElementById('tbody-contratos-laborales');
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding:1.5rem;">No hay contratos laborales registrados.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(c => {
            let bColor = '#22c55e', bBg = 'rgba(34,197,94,0.15)';
            if (c.estado === 'Vencido') { bColor = '#ef4444'; bBg = 'rgba(239,68,68,0.15)'; }
            else if (c.estado === 'Próximo a vencer') { bColor = '#f59e0b'; bBg = 'rgba(245,158,11,0.15)'; }
            else if (c.estado === 'Borrador') { bColor = '#64748b'; bBg = 'rgba(100,116,139,0.15)'; }

            return `
                <tr>
                    <td><code>${c.numero_contrato}</code></td>
                    <td><strong>${c.empleado}</strong><br><small class="text-muted">${c.cargo || '—'}</small></td>
                    <td>${c.tipo_contratacion}</td>
                    <td style="text-align: right; font-weight: 700;">${cs(c.salario)}</td>
                    <td>${c.fecha_inicio} al ${c.fecha_fin || 'Indefinido'}</td>
                    <td><span class="badge" style="background:${bBg}; color:${bColor}; font-weight:700;">${c.estado}</span></td>
                    <td>
                        <div style="display:flex; gap:4px;">
                            <a href="/rrhh/contrato/${c.id}/imprimir" target="_blank" class="btn btn-secondary" style="padding:3px 7px; font-size:0.75rem;" title="Imprimir Contrato Oficial">
                                <i class="ph-bold ph-printer"></i> Imprimir
                            </a>
                            <button class="btn btn-secondary" style="padding:3px 7px; font-size:0.75rem;" onclick="renovarContratoModal(${c.id})" title="Renovar / Prórroga">
                                <i class="ph-bold ph-arrows-clockwise"></i>
                            </button>
                        </div>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Error cargando contratos:', e);
    }
}

function abrirModalNuevoContrato() {
    // Llenar select de empleados
    const sel = document.getElementById('cont-empleado-id');
    if (sel && _empleadosCache) {
        sel.innerHTML = '<option value="">-- Seleccionar Empleado --</option>' +
            _empleadosCache.map(e => `<option value="${e.id}" data-salario="${e.salario_base}" data-cargo="${e.cargo}">${e.nombre_completo} (${e.cargo || 'Sin cargo'})</option>`).join('');
    }
    openModal('modal-contrato-laboral');
}

function autocompletarDatosContrato() {
    const sel = document.getElementById('cont-empleado-id');
    const opt = sel.options[sel.selectedIndex];
    if (opt && opt.dataset.salario) {
        document.getElementById('cont-salario').value = opt.dataset.salario;
        document.getElementById('cont-cargo').value = opt.dataset.cargo || '';
    }
}

async function guardarContratoLaboral(e) {
    if (e) e.preventDefault();
    const data = {
        empleado_id: parseInt(document.getElementById('cont-empleado-id').value),
        cargo: document.getElementById('cont-cargo').value.trim(),
        funciones: document.getElementById('cont-funciones').value.trim(),
        tipo_contratacion: document.getElementById('cont-tipo').value,
        fecha_inicio: document.getElementById('cont-fecha-inicio').value,
        fecha_fin: document.getElementById('cont-fecha-fin').value || null,
        jornada_laboral: document.getElementById('cont-jornada').value,
        salario: parseFloat(document.getElementById('cont-salario').value || 0),
        forma_pago: document.getElementById('cont-forma-pago').value
    };

    if (!data.empleado_id || !data.fecha_inicio || !data.salario) {
        Swal.fire('Atención', 'Complete empleado, fecha de inicio y salario.', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/rrhh/contratos', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const resp = await res.json();
        if (res.ok) {
            Swal.fire('¡Contrato Registrado!', resp.mensaje, 'success');
            closeModal('modal-contrato-laboral');
            cargarContratosLaborales();
        } else {
            Swal.fire('Error', resp.error || 'No se pudo guardar el contrato.', 'error');
        }
    } catch (err) {
        Swal.fire('Error', 'Fallo de conexión.', 'error');
    }
}

async function renovarContratoModal(id) {
    const c = _contratosCache.find(x => x.id === id);
    if (!c) return;

    const { value: nuevaFecha } = await Swal.fire({
        title: `Prórroga / Renovación: ${c.numero_contrato}`,
        text: `Empleado: ${c.empleado}. Ingrese nueva fecha de vencimiento:`,
        input: 'date',
        inputValue: new Date(new Date().setFullYear(new Date().getFullYear() + 1)).toISOString().slice(0, 10),
        showCancelButton: true,
        confirmButtonText: 'Aplicar Renovación'
    });

    if (nuevaFecha) {
        const res = await fetch(`/api/rrhh/contratos/${id}/estado`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ estado: 'Vigente', fecha_fin: nuevaFecha })
        });
        if (res.ok) {
            Swal.fire('Renovado', 'El contrato fue renovado exitosamente.', 'success');
            cargarContratosLaborales();
        }
    }
}

// -----------------------------------------------------------------------------
// RF97: EXPEDIENTE DIGITAL DEL EMPLEADO
// -----------------------------------------------------------------------------
let _expedienteEmpActivo = null;

async function abrirExpedienteDigital(empId, empNombre) {
    _expedienteEmpActivo = empId;
    document.getElementById('lbl-expediente-empleado').textContent = empNombre;
    openModal('modal-expediente-digital');
    cargarDocumentosExpediente(empId);
}

async function cargarDocumentosExpediente(empId) {
    const tbody = document.getElementById('tbody-expediente-documentos');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:1rem;">Cargando expediente...</td></tr>';

    try {
        const res = await fetch(`/api/rrhh/expedientes/${empId}`);
        const data = await res.json();

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:1.5rem;">No hay documentos registrados en el expediente digital.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(d => `
            <tr>
                <td><strong>${d.tipo_documento}</strong></td>
                <td>${d.nombre_archivo}</td>
                <td>${d.fecha_subida?.slice(0, 10) || '—'}</td>
                <td>${d.subido_por || 'Admin'}</td>
                <td>
                    <span class="badge" style="background: rgba(34,197,94,0.15); color: #22c55e;">Digitalizado</span>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Error cargando expediente:', e);
    }
}

async function guardarDocumentoExpediente(e) {
    if (e) e.preventDefault();
    if (!_expedienteEmpActivo) return;

    const data = {
        tipo_documento: document.getElementById('exp-tipo-doc').value,
        nombre_archivo: document.getElementById('exp-nombre-archivo').value.trim(),
        observaciones: document.getElementById('exp-observaciones').value.trim()
    };

    if (!data.nombre_archivo) {
        Swal.fire('Atención', 'Ingrese la referencia o nombre del documento digital.', 'warning');
        return;
    }

    try {
        const res = await fetch(`/api/rrhh/expedientes/${_expedienteEmpActivo}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            Swal.fire('Guardado', 'Documento anexado al expediente digital.', 'success');
            document.getElementById('form-expediente-doc')?.reset();
            cargarDocumentosExpediente(_expedienteEmpActivo);
        }
    } catch (e) {
        Swal.fire('Error', 'No se pudo guardar el documento.', 'error');
    }
}

// -----------------------------------------------------------------------------
// RF101: HISTORIAL DE MODIFICACIONES LABORALES
// -----------------------------------------------------------------------------
async function abrirHistorialLaboral(empId, empNombre) {
    document.getElementById('lbl-historial-empleado').textContent = empNombre;
    openModal('modal-historial-laboral');

    const tbody = document.getElementById('tbody-historial-laboral');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding:1rem;">Cargando historial...</td></tr>';

    try {
        const res = await fetch(`/api/rrhh/historial-laboral/${empId}`);
        const data = await res.json();

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding:1.5rem;">No se registran modificaciones contractuales previas.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(h => `
            <tr>
                <td><strong>${h.tipo_modificacion}</strong></td>
                <td><span style="color:var(--text-muted);">${h.valor_anterior || '—'}</span></td>
                <td><strong style="color:var(--primary);">${h.valor_nuevo || '—'}</strong></td>
                <td>${h.fecha_vigencia || '—'}</td>
                <td>${h.motivo || 'Actualización de condiciones'}</td>
                <td><small>${h.registrado_por || 'Admin'}</small></td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Error cargando historial:', e);
    }
}

// -----------------------------------------------------------------------------
// RF102, RF103: CONTROL DE ASISTENCIA Y JORNADAS
// -----------------------------------------------------------------------------
async function cargarJornadasLaborales() {
    try {
        const res = await fetch('/api/rrhh/jornadas');
        const data = await res.json();
        _jornadasCache = data;

        const sel = document.getElementById('emp-jornada-select');
        if (sel) {
            sel.innerHTML = '<option value="">-- Asignar Jornada --</option>' +
                data.map(j => `<option value="${j.id}">${j.nombre_jornada} (${j.hora_entrada} a ${j.hora_salida})</option>`).join('');
        }
    } catch (e) {
        console.error('Error cargando jornadas:', e);
    }
}

async function cargarAsistenciaDiaria(fecha = null) {
    const fInput = document.getElementById('filtro-asistencia-fecha');
    const fVal = fecha || (fInput ? fInput.value : new Date().toISOString().slice(0, 10));
    if (fInput && !fInput.value) fInput.value = fVal;

    try {
        const res = await fetch(`/api/rrhh/asistencia?fecha=${fVal}`);
        const data = await res.json();
        _asistenciaCache = data;

        const tbody = document.getElementById('tbody-asistencia-diaria');
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding:1.5rem;">No hay registros de asistencia para esta fecha.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(a => {
            let col = '#22c55e', bg = 'rgba(34,197,94,0.15)';
            if (a.estado === 'Llegada Tardía') { col = '#f59e0b'; bg = 'rgba(245,158,11,0.15)'; }
            else if (a.estado === 'Falta Injustificada') { col = '#ef4444'; bg = 'rgba(239,68,68,0.15)'; }
            else if (a.estado === 'Permiso') { col = '#3b82f6'; bg = 'rgba(59,130,246,0.15)'; }

            return `
                <tr>
                    <td><strong>${a.empleado}</strong><br><small class="text-muted">${a.cargo || '—'}</small></td>
                    <td>${a.fecha}</td>
                    <td>${a.hora_entrada || '—'}</td>
                    <td>${a.hora_salida || '—'}</td>
                    <td><span class="badge" style="background:${bg}; color:${col}; font-weight:700;">${a.estado}</span></td>
                    <td>${a.observaciones || '—'}</td>
                    <td>
                        <button class="btn btn-secondary" style="padding:3px 7px; font-size:0.75rem;" onclick="marcarSalidaAsistencia(${a.id})" title="Marcar Salida">
                            <i class="ph-bold ph-sign-out"></i> Salida
                        </button>
                    </td>
                </tr>
            `;
        }).join('');
    } catch (e) {
        console.error('Error cargando asistencia:', e);
    }
}

function abrirModalNuevaAsistencia() {
    const sel = document.getElementById('asist-empleado-id');
    if (sel && _empleadosCache) {
        sel.innerHTML = '<option value="">-- Seleccionar Empleado --</option>' +
            _empleadosCache.filter(e => e.activo).map(e => `<option value="${e.id}">${e.nombre_completo}</option>`).join('');
    }
    document.getElementById('asist-fecha').value = new Date().toISOString().slice(0, 10);
    openModal('modal-registro-asistencia');
}

async function guardarAsistencia(e) {
    if (e) e.preventDefault();
    const data = {
        empleado_id: parseInt(document.getElementById('asist-empleado-id').value),
        fecha: document.getElementById('asist-fecha').value,
        hora_entrada: document.getElementById('asist-hora-entrada').value,
        hora_salida: document.getElementById('asist-hora-salida').value || null,
        estado: document.getElementById('asist-estado').value,
        observaciones: document.getElementById('asist-observaciones').value.trim()
    };

    if (!data.empleado_id || !data.fecha) {
        Swal.fire('Atención', 'Seleccione empleado y fecha.', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/rrhh/asistencia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        if (res.ok) {
            Swal.fire('Registrado', 'Asistencia registrada correctamente.', 'success');
            closeModal('modal-registro-asistencia');
            cargarAsistenciaDiaria(data.fecha);
        }
    } catch (e) {
        Swal.fire('Error', 'Fallo de conexión.', 'error');
    }
}

async function marcarSalidaAsistencia(id) {
    const hora = new Date().toTimeString().slice(0, 5);
    try {
        const res = await fetch('/api/rrhh/asistencia', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ id: id, hora_salida: hora })
        });
        if (res.ok) {
            Swal.fire('Salida Marcada', `Hora registrada: ${hora}`, 'success');
            cargarAsistenciaDiaria();
        }
    } catch (e) {
        Swal.fire('Error', 'No se pudo marcar la salida.', 'error');
    }
}

// -----------------------------------------------------------------------------
// RF104: HORAS EXTRAS CON RECARGO LEGAL DEL 100% (LEY 185)
// -----------------------------------------------------------------------------
async function cargarHorasExtras() {
    try {
        const res = await fetch('/api/rrhh/horas-extras');
        const data = await res.json();
        _horasExtrasCache = data;

        const tbody = document.getElementById('tbody-horas-extras');
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding:1.5rem;">No hay horas extraordinarias registradas.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(h => `
            <tr>
                <td><strong>${h.empleado}</strong></td>
                <td>${h.fecha}</td>
                <td style="text-align: center; font-weight: 700;">${h.cantidad_horas} hrs</td>
                <td style="text-align: center;"><span class="badge" style="background: rgba(59,130,246,0.15); color: #3b82f6;">+${h.recargo_porcentaje}% Ley 185</span></td>
                <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${cs(h.monto_total)}</td>
                <td><small>${h.motivo || 'Cierre de inventario / Demanda alta'}</small></td>
                <td><span class="badge" style="background: rgba(34,197,94,0.15); color: #22c55e;">Aprobado por ${h.autorizado_por}</span></td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Error cargando horas extras:', e);
    }
}

function abrirModalHorasExtras() {
    const sel = document.getElementById('he-empleado-id');
    if (sel && _empleadosCache) {
        sel.innerHTML = '<option value="">-- Seleccionar Empleado --</option>' +
            _empleadosCache.filter(e => e.activo).map(e => `<option value="${e.id}">${e.nombre_completo}</option>`).join('');
    }
    document.getElementById('he-fecha').value = new Date().toISOString().slice(0, 10);
    openModal('modal-horas-extras');
}

async function guardarHorasExtras(e) {
    if (e) e.preventDefault();
    const data = {
        empleado_id: parseInt(document.getElementById('he-empleado-id').value),
        fecha: document.getElementById('he-fecha').value,
        cantidad_horas: parseFloat(document.getElementById('he-horas').value || 0),
        motivo: document.getElementById('he-motivo').value.trim()
    };

    if (!data.empleado_id || data.cantidad_horas <= 0) {
        Swal.fire('Atención', 'Seleccione un empleado y cantidad válida de horas.', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/rrhh/horas-extras', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const resp = await res.json();
        if (res.ok) {
            Swal.fire('¡Horas Extras Aprobadas!', resp.mensaje, 'success');
            closeModal('modal-horas-extras');
            cargarHorasExtras();
        } else {
            Swal.fire('Error', resp.error, 'error');
        }
    } catch (e) {
        Swal.fire('Error', 'Fallo de conexión.', 'error');
    }
}

// -----------------------------------------------------------------------------
// RF108: LIQUIDACIONES LABORALES (FINIQUITO LEY 185)
// -----------------------------------------------------------------------------
async function cargarLiquidacionesLaborales() {
    try {
        const res = await fetch('/api/rrhh/liquidaciones');
        const data = await res.json();
        _liquidacionesCache = data;

        const tbody = document.getElementById('tbody-liquidaciones-laborales');
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding:1.5rem;">No se registran liquidaciones laborales en el sistema.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(l => `
            <tr>
                <td><code>${l.codigo}</code></td>
                <td><strong>${l.empleado}</strong><br><small class="text-muted">${l.cargo || '—'}</small></td>
                <td>${l.motivo_salida}</td>
                <td>${l.antiguedad_anios}a ${l.antiguedad_meses}m ${l.antiguedad_dias}d</td>
                <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${cs(l.neto_a_pagar)}</td>
                <td><span class="badge" style="background: rgba(34,197,94,0.15); color: #22c55e;">${l.estado}</span></td>
                <td>
                    <a href="/rrhh/liquidacion/${l.id}/imprimir" target="_blank" class="btn btn-secondary" style="padding:3px 7px; font-size:0.75rem;" title="Imprimir Finiquito Legal">
                        <i class="ph-bold ph-printer"></i> Imprimir Finiquito
                    </a>
                </td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Error cargando liquidaciones:', e);
    }
}

function abrirModalNuevaLiquidacion() {
    const sel = document.getElementById('liq-empleado-id');
    if (sel && _empleadosCache) {
        sel.innerHTML = '<option value="">-- Seleccionar Empleado a Liquidar --</option>' +
            _empleadosCache.map(e => `<option value="${e.id}" data-ingreso="${e.fecha_ingreso || ''}">${e.nombre_completo} (Ingreso: ${e.fecha_ingreso ? e.fecha_ingreso.slice(0, 10) : '—'})</option>`).join('');
    }
    document.getElementById('liq-fecha-salida').value = new Date().toISOString().slice(0, 10);
    openModal('modal-liquidacion-laboral');
}

async function guardarLiquidacion(e) {
    if (e) e.preventDefault();
    const data = {
        empleado_id: parseInt(document.getElementById('liq-empleado-id').value),
        fecha_salida: document.getElementById('liq-fecha-salida').value,
        motivo_salida: document.getElementById('liq-motivo').value,
        dias_pendientes: parseFloat(document.getElementById('liq-dias-pendientes').value || 0),
        deducciones: parseFloat(document.getElementById('liq-deducciones').value || 0)
    };

    if (!data.empleado_id || !data.fecha_salida) {
        Swal.fire('Atención', 'Seleccione empleado y fecha de salida.', 'warning');
        return;
    }

    try {
        const res = await fetch('/api/rrhh/liquidaciones', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        const resp = await res.json();
        if (res.ok) {
            Swal.fire({
                title: '¡Liquidación Calculada!',
                text: resp.mensaje,
                icon: 'success',
                showCancelButton: true,
                confirmButtonText: 'Ver e Imprimir Finiquito',
                cancelButtonText: 'Cerrar'
            }).then(result => {
                if (result.isConfirmed) {
                    window.open(`/rrhh/liquidacion/${resp.id}/imprimir`, '_blank');
                }
            });
            closeModal('modal-liquidacion-laboral');
            cargarLiquidacionesLaborales();
        } else {
            Swal.fire('Error', resp.error, 'error');
        }
    } catch (e) {
        Swal.fire('Error', 'Fallo de conexión.', 'error');
    }
}

// -----------------------------------------------------------------------------
// RF109: SEGUIMIENTO DE PAGOS DE NÓMINA
// -----------------------------------------------------------------------------
async function cargarPagosNomina() {
    try {
        const res = await fetch('/api/rrhh/pagos-nomina');
        const data = await res.json();
        _pagosNominaCache = data;

        const tbody = document.getElementById('tbody-pagos-nomina');
        if (!tbody) return;

        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding:1.5rem;">No se registran comprobantes de pago de nómina.</td></tr>';
            return;
        }

        tbody.innerHTML = data.map(p => `
            <tr>
                <td><strong>${p.empleado}</strong></td>
                <td>Nómina #${p.nomina_id}</td>
                <td>${p.fecha_pago?.slice(0, 10) || '—'}</td>
                <td><span class="badge" style="background: rgba(59,130,246,0.15); color: #3b82f6;">${p.metodo_pago}</span></td>
                <td><code>${p.numero_referencia || '—'}</code></td>
                <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${cs(p.monto_pagado)}</td>
                <td><span class="badge" style="background: rgba(34,197,94,0.15); color: #22c55e;">${p.estado}</span></td>
            </tr>
        `).join('');
    } catch (e) {
        console.error('Error cargando pagos de nómina:', e);
    }
}

// -----------------------------------------------------------------------------
// RF110 - RF114: SEGURIDAD E HIGIENE OCUPACIONAL (LEY 618)
// -----------------------------------------------------------------------------
async function cargarRiesgosHigiene() {
    try {
        const res = await fetch('/api/rrhh/higiene/riesgos');
        const data = await res.json();
        const tbody = document.getElementById('tbody-higiene-riesgos');
        if (!tbody) return;
        tbody.innerHTML = data.map(r => `
            <tr>
                <td><strong>${r.area}</strong></td>
                <td>${r.tipo_riesgo}</td>
                <td><span class="badge" style="background:${r.nivel_riesgo === 'Alto' ? '#ef4444' : r.nivel_riesgo === 'Medio' ? '#f59e0b' : '#22c55e'}; color:#fff;">${r.nivel_riesgo}</span></td>
                <td>${r.medidas_preventivas}</td>
                <td><small>${r.responsable_seguimiento}</small></td>
            </tr>
        `).join('');
    } catch (e) {}
}

async function cargarIncidentesHigiene() {
    try {
        const res = await fetch('/api/rrhh/higiene/incidentes');
        const data = await res.json();
        const tbody = document.getElementById('tbody-higiene-incidentes');
        if (!tbody) return;
        if (data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding:1rem;">Sin incidentes laborales registrados.</td></tr>';
            return;
        }
        tbody.innerHTML = data.map(i => `
            <tr>
                <td>${i.fecha}</td>
                <td><strong>${i.area}</strong></td>
                <td>${i.empleado || 'General'}</td>
                <td>${i.descripcion_suceso}</td>
                <td>${i.medidas_correctivas}</td>
                <td><span class="badge" style="background:rgba(34,197,94,0.15); color:#22c55e;">${i.estado_caso}</span></td>
            </tr>
        `).join('');
    } catch (e) {}
}

async function cargarEppHigiene() {
    try {
        const res = await fetch('/api/rrhh/higiene/epp');
        const data = await res.json();
        const tbody = document.getElementById('tbody-higiene-epp');
        if (!tbody) return;
        tbody.innerHTML = data.map(e => `
            <tr>
                <td><strong>${e.empleado}</strong></td>
                <td>${e.tipo_equipo}</td>
                <td style="text-align: center;">${e.cantidad}</td>
                <td>${e.fecha_entrega}</td>
                <td><span class="badge" style="background:rgba(34,197,94,0.15); color:#22c55e;">${e.estado}</span></td>
            </tr>
        `).join('');
    } catch (e) {}
}

async function cargarCapacitacionesHigiene() {
    try {
        const res = await fetch('/api/rrhh/higiene/capacitaciones');
        const data = await res.json();
        const tbody = document.getElementById('tbody-higiene-capacitaciones');
        if (!tbody) return;
        tbody.innerHTML = data.map(c => `
            <tr>
                <td><strong>${c.nombre_capacitacion}</strong></td>
                <td>${c.fecha}</td>
                <td>${c.instructor_o_responsable}</td>
                <td>${c.participantes_detalle || 'Todo el personal'}</td>
                <td><span class="badge" style="background:rgba(59,130,246,0.15); color:#3b82f6;">Completada</span></td>
            </tr>
        `).join('');
    } catch (e) {}
}

async function cargarInspeccionesHigiene() {
    try {
        const res = await fetch('/api/rrhh/higiene/inspecciones');
        const data = await res.json();
        const tbody = document.getElementById('tbody-higiene-inspecciones');
        if (!tbody) return;
        tbody.innerHTML = data.map(i => `
            <tr>
                <td>${i.fecha_inspeccion}</td>
                <td><strong>${i.inspector}</strong></td>
                <td><span class="badge" style="background:${i.resultado === 'Aprobada' ? 'rgba(34,197,94,0.15)' : 'rgba(245,158,11,0.15)'}; color:${i.resultado === 'Aprobada' ? '#22c55e' : '#f59e0b'}; font-weight:700;">${i.resultado}</span></td>
                <td>${i.observaciones_detectadas || 'Instalaciones en orden'}</td>
                <td>${i.medidas_correctivas || 'Ninguna requerida'}</td>
            </tr>
        `).join('');
    } catch (e) {}
}

function abrirModalInspeccion6Puntos() {
    openModal('modal-inspeccion-higiene');
}

async function guardarInspeccion6Puntos(e) {
    if (e) e.preventDefault();
    const est = document.getElementById('chk-estanterias').checked;
    const pas = document.getElementById('chk-pasillos').checked;
    const ext = document.getElementById('chk-extintores').checked;
    const sen = document.getElementById('chk-senalizacion').checked;
    const ord = document.getElementById('chk-orden').checked;
    const sal = document.getElementById('chk-salidas').checked;

    const conformes = [est, pas, ext, sen, ord, sal].filter(Boolean).length;
    const resultado = conformes >= 5 ? 'Aprobada' : 'Observada';

    const obs = document.getElementById('insp-observaciones').value.trim();
    const med = document.getElementById('insp-medidas').value.trim();

    try {
        const res = await fetch('/api/rrhh/higiene/inspecciones', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                area: 'Tienda y Bodega de Repuestos',
                tipo_inspeccion: 'Inspección Periódica Integral de 6 Puntos',
                resultado: resultado,
                observaciones: `Puntos aprobados: ${conformes}/6. ${obs}`,
                medidas_correctivas: med || (conformes < 6 ? 'Subsanar puntos observados en un plazo de 72 horas.' : 'Mantener condiciones preventivas actuales.')
            })
        });
        if (res.ok) {
            Swal.fire('Inspección Registrada', `Resultado: ${resultado} (${conformes}/6 puntos aprobados)`, 'success');
            closeModal('modal-inspeccion-higiene');
            cargarInspeccionesHigiene();
        }
    } catch (e) {
        Swal.fire('Error', 'No se pudo guardar la inspección.', 'error');
    }
}

// -----------------------------------------------------------------------------
// RF115, RF116: MARCO LEGAL Y PARÁMETROS DEL SISTEMA
// -----------------------------------------------------------------------------
async function cargarMarcoLegal() {
    try {
        const res = await fetch('/api/rrhh/marco-legal');
        const data = await res.json();
        const container = document.getElementById('container-marco-legal');
        if (!container) return;

        container.innerHTML = data.map(n => `
            <div class="card" style="margin-bottom: 1rem; border-left: 4px solid var(--primary);">
                <div class="card-header" style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 style="margin:0;"><i class="ph-bold ph-scales"></i> ${n.nombre}</h3>
                    <a href="${n.enlace_oficial}" target="_blank" class="btn btn-secondary" style="font-size:0.75rem; padding:4px 8px;">
                        <i class="ph-bold ph-arrow-square-out"></i> Ver Ley Completa
                    </a>
                </div>
                <div class="card-body">
                    <p style="font-size:0.85rem; color:var(--text-muted); margin-bottom:0.75rem;">${n.descripcion}</p>
                    <div style="background:var(--bg-card); border-radius:6px; padding:0.75rem;">
                        <strong style="font-size:0.8rem; text-transform:uppercase; color:var(--primary);">Artículos Clave Aplicados al Sistema:</strong>
                        <ul style="margin:0.5rem 0 0 1.2rem; font-size:0.82rem; color:var(--text-main);">
                            ${n.articulos_clave.map(a => `<li>${a}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (e) {}
}

async function cargarParametrosLaborales() {
    try {
        const res = await fetch('/api/rrhh/parametros');
        const data = await res.json();
        const tbody = document.getElementById('tbody-parametros-laborales');
        if (!tbody) return;

        tbody.innerHTML = data.map(p => `
            <tr>
                <td><code>${p.codigo}</code></td>
                <td><strong>${p.nombre}</strong><br><small class="text-muted">${p.descripcion || ''}</small></td>
                <td style="text-align: right; font-weight: 800; font-size: 0.95rem; color: var(--primary);">${p.valor} ${p.unidad}</td>
                <td><small>${p.referencia_legal || 'Ley 185'}</small></td>
                <td>${p.fecha_vigencia?.slice(0, 10) || '2026-01-01'}</td>
                <td>
                    <button class="btn btn-secondary" style="padding:3px 7px; font-size:0.75rem;" onclick="editarParametroModal('${p.codigo}', '${p.nombre}', ${p.valor}, '${p.unidad}')">
                        <i class="ph-bold ph-pencil-simple"></i> Modificar
                    </button>
                </td>
            </tr>
        `).join('');
    } catch (e) {}
}

async function editarParametroModal(codigo, nombre, valorActual, unidad) {
    const { value: nuevoValor } = await Swal.fire({
        title: `Modificar Parámetro: ${nombre}`,
        text: `Ingrese el nuevo valor numérico (${unidad}):`,
        input: 'number',
        inputValue: valorActual,
        inputAttributes: { step: 'any' },
        showCancelButton: true,
        confirmButtonText: 'Guardar Parámetro'
    });

    if (nuevoValor !== undefined && nuevoValor !== null) {
        try {
            const res = await fetch(`/api/rrhh/parametros/${codigo}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ valor: parseFloat(nuevoValor) })
            });
            if (res.ok) {
                Swal.fire('Parámetro Actualizado', `El valor ahora es ${nuevoValor} ${unidad}`, 'success');
                cargarParametrosLaborales();
            }
        } catch (e) {
            Swal.fire('Error', 'No se pudo actualizar el parámetro.', 'error');
        }
    }
}

// -----------------------------------------------------------------------------
// EXPOSICIÓN GLOBAL Y AUTO-INICIALIZACIÓN
// -----------------------------------------------------------------------------
window.initRrhhCorteVTab = initRrhhCorteVTab;
window.cargarSolicitudesEmpleo = cargarSolicitudesEmpleo;
window.abrirModalNuevaSolicitud = abrirModalNuevaSolicitud;
window.guardarSolicitudEmpleo = guardarSolicitudEmpleo;
window.abrirModalEstadoSolicitud = abrirModalEstadoSolicitud;
window.contratarAspirante = contratarAspirante;
window.cargarContratosLaborales = cargarContratosLaborales;
window.abrirModalNuevoContrato = abrirModalNuevoContrato;
window.autocompletarDatosContrato = autocompletarDatosContrato;
window.guardarContratoLaboral = guardarContratoLaboral;
window.renovarContratoModal = renovarContratoModal;
window.abrirExpedienteDigital = abrirExpedienteDigital;
window.guardarDocumentoExpediente = guardarDocumentoExpediente;
window.abrirHistorialLaboral = abrirHistorialLaboral;
window.cargarJornadasLaborales = cargarJornadasLaborales;
window.cargarAsistenciaDiaria = cargarAsistenciaDiaria;
window.abrirModalNuevaAsistencia = abrirModalNuevaAsistencia;
window.guardarAsistencia = guardarAsistencia;
window.marcarSalidaAsistencia = marcarSalidaAsistencia;
window.cargarHorasExtras = cargarHorasExtras;
window.abrirModalHorasExtras = abrirModalHorasExtras;
window.guardarHorasExtras = guardarHorasExtras;
window.cargarLiquidacionesLaborales = cargarLiquidacionesLaborales;
window.abrirModalNuevaLiquidacion = abrirModalNuevaLiquidacion;
window.cargarPagosNomina = cargarPagosNomina;
window.cargarRiesgosHigiene = cargarRiesgosHigiene;
window.cargarIncidentesHigiene = cargarIncidentesHigiene;
window.cargarEppHigiene = cargarEppHigiene;
window.cargarCapacitacionesHigiene = cargarCapacitacionesHigiene;
window.cargarInspeccionesHigiene = cargarInspeccionesHigiene;
window.abrirModalInspeccion6Puntos = abrirModalInspeccion6Puntos;
window.guardarInspeccion6Puntos = guardarInspeccion6Puntos;
window.cargarMarcoLegal = cargarMarcoLegal;
window.cargarParametrosLaborales = cargarParametrosLaborales;
window.editarParametroModal = editarParametroModal;

// Reportes y Estadísticas (RF58 - RF68)
window.switchReportesTab = switchReportesTab;
window.toggleMenuExportar = toggleMenuExportar;
window.exportarExcelReal = exportarExcelReal;
window.generarInformeEjecutivo = generarInformeEjecutivo;
if (typeof imprimirInformeEjecutivo === 'function') {
    window.imprimirInformeEjecutivo = imprimirInformeEjecutivo;
}
window.aplicarFiltroReportesPreset = aplicarFiltroReportesPreset;
window.cambiarMesAnioDirecto = cambiarMesAnioDirecto;
window.cambiarCriterioABC = cambiarCriterioABC;
window.toggleModoComparar = toggleModoComparar;
window.ejecutarComparacionPeriodos = ejecutarComparacionPeriodos;
window.cerrarModoComparativo = cerrarModoComparativo;
window.filtrarTablaABC = filtrarTablaABC;
window.filtrarTablaABCPorTexto = filtrarTablaABCPorTexto;
window.aplicarFiltroLocalTablaABC = aplicarFiltroLocalTablaABC;
window.ejecutarConsultaReportes = ejecutarConsultaReportes;
window.renderReportesCompleto = renderReportesCompleto;
window.cargarEstadisticasDevoluciones = cargarEstadisticasDevoluciones;
window.toggleDemandaView = toggleDemandaView;

// Escuchar cambios de pestaña general de la barra lateral
document.addEventListener('DOMContentLoaded', () => {
    // Si RRHH ya está activo o al hacer clic en él
    document.querySelectorAll('[data-tab="tab-rrhh"]').forEach(btn => {
        btn.addEventListener('click', () => {
            setTimeout(() => { initRrhhCorteVTab('all'); }, 200);
        });
    });

    // Si Reportes ya está activo o al hacer clic en él
    document.querySelectorAll('[data-tab="tab-reportes"]').forEach(btn => {
        btn.addEventListener('click', () => {
            setTimeout(ejecutarConsultaReportes, 200);
            setTimeout(cargarEstadisticasDevoluciones, 250);
        });
    });

    // Disparar carga inicial por si se carga directamente en tab-rrhh o tab-reportes
    const tabRrhh = document.getElementById('tab-rrhh');
    if (tabRrhh && tabRrhh.classList.contains('active')) {
        setTimeout(() => { initRrhhCorteVTab('all'); }, 300);
    }
    const tabReportes = document.getElementById('tab-reportes');
    if (tabReportes && tabReportes.classList.contains('active')) {
        setTimeout(ejecutarConsultaReportes, 300);
    }
});
