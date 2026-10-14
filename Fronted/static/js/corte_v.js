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
// 1. REPORTE Y ESTADÍSTICAS - FILTROS DINÁMICOS Y COMPLEMENTOS (RF58, RF66, RF68)
// =============================================================================
let _filtroPresetActivo = 'mes';
let _demandaViewActual = 'top'; // 'top' o 'bottom'

function aplicarFiltroReportesPreset(preset) {
    _filtroPresetActivo = preset;

    // Actualizar botones visuales
    document.querySelectorAll('.btn-preset-reporte').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.preset === preset);
    });

    const fCustomContainer = document.getElementById('rep-filtro-fechas-custom');
    if (fCustomContainer) {
        fCustomContainer.style.display = (preset === 'personalizado') ? 'flex' : 'none';
        if (preset === 'personalizado') return; // Espera a que el usuario presione el botón de filtrar
    }

    ejecutarConsultaReportes();
}

async function ejecutarConsultaReportes() {
    let url = '/api/reportes?';
    if (_filtroPresetActivo === 'personalizado') {
        const d = document.getElementById('rep-fecha-inicio')?.value;
        const h = document.getElementById('rep-fecha-fin')?.value;
        if (!d || !h) {
            Swal.fire('Atención', 'Selecciona ambas fechas (Desde y Hasta) para el filtro personalizado.', 'warning');
            return;
        }
        url += `fecha_inicio=${d}&fecha_fin=${h}`;
    } else if (_filtroPresetActivo && _filtroPresetActivo !== 'historico') {
        url += `rango=${_filtroPresetActivo}`;
    } else {
        url += `rango=historico`;
    }

    try {
        const res = await fetch(url);
        const data = await res.json();
        if (data.error) {
            Swal.fire('Error', data.error, 'error');
            return;
        }

        _reporteDataCache = data;

        // Período activo
        const pTexto = data.periodo?.texto || 'Histórico Completo';
        const elPeriodo = document.getElementById('rep-periodo-activo-texto');
        if (elPeriodo) elPeriodo.textContent = pTexto;

        // Renderizar KPIs
        const k = data.kpis || {};
        if (document.getElementById('rep-ingresos')) document.getElementById('rep-ingresos').textContent = formatMoneda(k.ventas_totales_monto || 0);
        if (document.getElementById('rep-unidades-vendidas')) document.getElementById('rep-unidades-vendidas').textContent = `${k.unidades_vendidas_total || 0} unid. | ${k.ventas_totales_conteo || 0} ventas`;
        if (document.getElementById('rep-costo-ventas')) document.getElementById('rep-costo-ventas').textContent = formatMoneda(k.costo_ventas_monto || 0);
        if (document.getElementById('rep-egresos-compras')) document.getElementById('rep-egresos-compras').textContent = `Compras: ${formatMoneda(k.compras_totales_monto || 0)}`;
        if (document.getElementById('rep-margen')) document.getElementById('rep-margen').textContent = formatMoneda(k.margen_bruto_monto || 0);
        if (document.getElementById('rep-margen-pct')) document.getElementById('rep-margen-pct').textContent = `Margen: ${k.margen_bruto_porcentaje || 0}%`;
        if (document.getElementById('rep-ticket-promedio')) document.getElementById('rep-ticket-promedio').textContent = formatMoneda(k.ticket_promedio || 0);

        // Gráficos y Tablas
        if (typeof renderChartsEstadisticas === 'function') renderChartsEstadisticas(data);
        if (typeof renderTablaRotacionABC === 'function') renderTablaRotacionABC(data.rotacion_abc);
        if (typeof renderAlertasExistencias === 'function') renderAlertasExistencias(data.alertas);
        if (typeof renderTablaCategorias === 'function') renderTablaCategorias(data.categorias_analisis);

        // RF66: Repuestos más y menos vendidos
        renderRepuestosDemanda();

        // RF68: Devoluciones
        cargarEstadisticasDevoluciones();

    } catch (e) {
        console.error('Error cargando reportes con filtro dinámico:', e);
    }
}

function toggleDemandaView(tipo) {
    _demandaViewActual = tipo;
    document.getElementById('btn-demanda-top')?.classList.toggle('active', tipo === 'top');
    document.getElementById('btn-demanda-bottom')?.classList.toggle('active', tipo === 'bottom');
    renderRepuestosDemanda();
}

function renderRepuestosDemanda() {
    if (!_reporteDataCache) return;
    const tbody = document.getElementById('tbody-repuestos-demanda');
    const titleEl = document.getElementById('title-repuestos-demanda');
    if (!tbody) return;

    const limite = parseInt(document.getElementById('select-demanda-limit')?.value || '10');

    if (_demandaViewActual === 'top') {
        if (titleEl) titleEl.innerHTML = '<i class="ph-bold ph-star" style="color: var(--warning);"></i> Top Repuestos Más Vendidos';
        const prods = (_reporteDataCache.top_productos || []).slice(0, limite);
        if (prods.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:1.5rem;">Sin registros de ventas en el período.</td></tr>';
            return;
        }
        tbody.innerHTML = prods.map((p, idx) => `
            <tr>
                <td style="font-weight: 700; width: 40px; text-align: center; color: var(--primary);">#${idx + 1}</td>
                <td><strong>${p.nombre}</strong><br><small class="text-muted">SKU: ${p.codigo || '—'} | ${p.categoria || '—'}</small></td>
                <td style="text-align: center; font-weight: 700;">${p.cantidad_vendida || 0} uds.</td>
                <td style="text-align: right; font-weight: 700; color: var(--accent-green);">${formatMoneda(p.monto_total || 0)}</td>
                <td style="text-align: center;"><span class="badge" style="background: rgba(34,197,94,0.15); color: #22c55e;">Clase ${p.clase_abc || 'A'}</span></td>
            </tr>
        `).join('');
    } else {
        if (titleEl) titleEl.innerHTML = '<i class="ph-bold ph-trend-down" style="color: var(--accent-red);"></i> Repuestos con Menor Demanda / Sin Movimiento';
        const prods = (_reporteDataCache.bottom_productos || []).slice(0, limite);
        if (prods.length === 0) {
            tbody.innerHTML = '<tr><td colspan="5" class="text-center text-muted" style="padding:1.5rem;">No se encontraron repuestos con baja demanda.</td></tr>';
            return;
        }
        tbody.innerHTML = prods.map((p, idx) => `
            <tr>
                <td style="font-weight: 700; width: 40px; text-align: center; color: var(--text-muted);">#${idx + 1}</td>
                <td><strong>${p.nombre}</strong><br><small class="text-muted">SKU: ${p.codigo || '—'} | Stock: ${p.stock || 0} uds.</small></td>
                <td style="text-align: center; font-weight: 700; color: var(--accent-red);">${p.cantidad_vendida || 0} uds.</td>
                <td style="text-align: right; font-weight: 700; color: var(--warning);">${formatMoneda(p.costo_inmovilizado || 0)} <small class="text-muted"><br>inmovilizado</small></td>
                <td style="text-align: center;"><span class="badge" style="background: rgba(239,68,68,0.15); color: #ef4444;">Clase C</span></td>
            </tr>
        `).join('');
    }
}

// RF68: Devoluciones de ventas
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
                tbody.innerHTML = '<tr><td colspan="6" class="text-center text-muted" style="padding:1.5rem;">No se registran devoluciones de repuestos.</td></tr>';
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
window.autocompletarDatosLiquidacion = autocompletarDatosLiquidacion;
window.guardarLiquidacionLaboral = guardarLiquidacionLaboral;
window.cargarPagosNomina = cargarPagosNomina;
window.abrirModalNuevoPagoNomina = abrirModalNuevoPagoNomina;
window.autocompletarDatosPagoNomina = autocompletarDatosPagoNomina;
window.guardarPagoNomina = guardarPagoNomina;
window.cargarRiesgosHigiene = cargarRiesgosHigiene;
window.abrirModalNuevoRiesgo = abrirModalNuevoRiesgo;
window.guardarRiesgoHigiene = guardarRiesgoHigiene;
window.cargarIncidentesHigiene = cargarIncidentesHigiene;
window.abrirModalNuevoIncidente = abrirModalNuevoIncidente;
window.guardarIncidenteHigiene = guardarIncidenteHigiene;
window.cargarEppHigiene = cargarEppHigiene;
window.abrirModalEntregaEpp = abrirModalEntregaEpp;
window.guardarEntregaEpp = guardarEntregaEpp;
window.cargarCapacitacionesHigiene = cargarCapacitacionesHigiene;
window.abrirModalNuevaCapacitacion = abrirModalNuevaCapacitacion;
window.guardarCapacitacionHigiene = guardarCapacitacionHigiene;
window.cargarInspeccionesHigiene = cargarInspeccionesHigiene;
window.abrirModalInspeccion6Puntos = abrirModalInspeccion6Puntos;
window.guardarInspeccion6Puntos = guardarInspeccion6Puntos;
window.cargarMarcoLegal = cargarMarcoLegal;
window.cargarParametrosLaborales = cargarParametrosLaborales;
window.editarParametroModal = editarParametroModal;
window.aplicarFiltroReportesPreset = aplicarFiltroReportesPreset;
window.ejecutarConsultaReportes = ejecutarConsultaReportes;
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

    // Disparar carga inicial por si se carga directamente en tab-rrhh
    const tabRrhh = document.getElementById('tab-rrhh');
    if (tabRrhh && tabRrhh.classList.contains('active')) {
        setTimeout(() => { initRrhhCorteVTab('all'); }, 300);
    }
});
