// RRHH: formularios persistentes, archivos privados y seguimiento.
let riesgosControl = [], eppControl = [], empleadosControl = [], detallesPagoControl = [], pagosControl = [];
const rrhhEsc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const rrhhHoy = () => new Intl.DateTimeFormat('sv-SE', {timeZone: 'America/Managua'}).format(new Date());
const rrhhValor = id => document.getElementById(id)?.value || '';
async function rrhhApi(url, options) {
    const response = await fetch(url, options);
    const data = await response.json();
    if (!response.ok) throw new Error(data.error || 'No se pudo completar la operación.');
    return data;
}
function rrhhFormulario(id) {
    const form = document.getElementById(id);
    form.reset();
    form.querySelector('.rrhh-error').textContent = '';
    return form;
}
async function rrhhGuardar(event, action) {
    event.preventDefault();
    const form = event.target, boton = form.querySelector('[type="submit"]');
    if (boton.disabled) return;
    boton.disabled = true;
    form.querySelector('.rrhh-error').textContent = '';
    try { await action(form); }
    catch (error) { form.querySelector('.rrhh-error').textContent = error.message; }
    finally { boton.disabled = false; }
}
const rrhhJson = (method, data) => ({method, headers: {'Content-Type':'application/json'}, body: JSON.stringify(data)});
function rrhhFilaError(id, columnas, error) {
    const tbody = document.getElementById(id);
    if (tbody) tbody.innerHTML = `<tr><td colspan="${columnas}" role="alert">${rrhhEsc(error.message)}</td></tr>`;
}

async function cargarRiesgosHigiene() {
    try { riesgosControl = await rrhhApi('/api/rrhh/higiene/riesgos'); renderRiesgos(); }
    catch (error) { rrhhFilaError('tbody-higiene-riesgos', 6, error); }
}
function renderRiesgos() {
    const tbody = document.getElementById('tbody-higiene-riesgos');
    if (!tbody) return;
    const buscar = rrhhValor('riesgo-buscar').toLocaleLowerCase();
    const rows = riesgosControl.filter(r => `${r.area} ${r.responsable_seguimiento}`.toLocaleLowerCase().includes(buscar)
        && (!rrhhValor('riesgo-nivel-filtro') || r.nivel_riesgo === rrhhValor('riesgo-nivel-filtro'))
        && (!rrhhValor('riesgo-estado-filtro') || r.estado === rrhhValor('riesgo-estado-filtro')));
    tbody.innerHTML = rows.map(r => `<tr>
        <td><strong>${rrhhEsc(r.area)}</strong><br>${rrhhEsc(r.tipo_riesgo)}<small class="rrhh-descripcion">${rrhhEsc(r.descripcion)}</small></td>
        <td><span class="badge rrhh-nivel-${['Bajo','Medio','Alto'].includes(r.nivel_riesgo) ? r.nivel_riesgo : 'Medio'}">${rrhhEsc(r.nivel_riesgo)}</span></td>
        <td>${rrhhEsc(r.medidas_preventivas)}</td><td>${rrhhEsc(r.responsable_seguimiento)}</td>
        <td>${rrhhEsc(r.estado || 'Pendiente')}<small class="rrhh-descripcion">${rrhhEsc(r.fecha_revision || 'Sin revisiones')}</small></td>
        <td><div class="rrhh-acciones"><button class="btn btn-secondary" onclick="abrirRiesgo(${r.id})">Editar</button><button class="btn btn-secondary" onclick="abrirSeguimientoRiesgo(${r.id})">Seguimiento</button></div></td>
    </tr>`).join('') || '<tr><td colspan="6">No hay riesgos para los filtros seleccionados.</td></tr>';
}
function abrirRiesgo(id) {
    const form = rrhhFormulario('form-riesgo-control'), row = riesgosControl.find(r => r.id === id);
    document.getElementById('riesgo-propuesta-grupo').hidden = !!row;
    if (row) for (const key of ['id','area','tipo_riesgo','descripcion','medidas_preventivas','responsable_seguimiento','nivel_riesgo','estado']) {
        form.elements[key].value = key === 'estado' && !['Pendiente','En seguimiento','Controlado'].includes(row[key]) ? 'Pendiente' : row[key] ?? '';
    }
    document.getElementById('riesgo-titulo').textContent = row ? 'Editar riesgo' : 'Registrar riesgo';
    openModal('modal-riesgo-control');
}
function aplicarPropuestaRiesgo(key) {
    // Propuestas aportadas por el usuario: no representan una inspección realizada.
    const propuestas = {
        cargas:['Bodega / Almacén','Manipulación manual de cargas','Medio','Capacitación en levantamiento seguro, uso de carretillas y distribución adecuada del peso.','Encargado de Inventario'],
        objetos:['Bodega / Almacén','Caída de objetos almacenados','Alto','Asegurar las estanterías, evitar sobrecargas y colocar los artículos más pesados en niveles inferiores.','Encargado de Inventario'],
        pasillos:['Bodega / Almacén','Caídas y tropiezos','Medio','Mantener los pasillos despejados, organizar la mercancía y limpiar inmediatamente cualquier derrame.','Encargado de Inventario'],
        posturas:['Ventas / Mostrador','Posturas prolongadas y movimientos repetitivos','Bajo','Realizar pausas breves, alternar posturas y mantener una distribución adecuada del espacio de trabajo.','Gerente de Operaciones'],
        electricidad:['Caja','Riesgo eléctrico','Bajo','Revisar periódicamente las instalaciones eléctricas, evitar conexiones sobrecargadas y mantener los cables protegidos.','Gerente de Operaciones'],
        cables:['Caja / Administración','Tropiezos por cables sueltos','Bajo','Organizar el cableado mediante canaletas y mantener despejadas las zonas de circulación.','Gerente de Operaciones'],
        pantalla:['Administración','Fatiga visual y posturas inadecuadas','Bajo','Ajustar la ubicación de la pantalla, mantener iluminación adecuada y realizar pausas durante el trabajo frente a la computadora.','Gerente Administrativo y Financiero']
    };
    const propuesta = propuestas[key];
    if (!propuesta) return;
    const form = document.getElementById('form-riesgo-control');
    ['area','tipo_riesgo','nivel_riesgo','medidas_preventivas','responsable_seguimiento'].forEach((campo,index) => {form.elements[campo].value = propuesta[index];});
    form.elements.descripcion.value = 'Propuesta pendiente de evaluación en el puesto. Documentar probabilidad, gravedad y condiciones observadas.';
    form.elements.estado.value = 'Pendiente';
}
function guardarRiesgo(event) {
    return rrhhGuardar(event, async form => {
        const data = Object.fromEntries(new FormData(form)), id = data.id;
        await rrhhApi('/api/rrhh/higiene/riesgos' + (id ? '/' + id : ''), rrhhJson(id ? 'PUT':'POST', data));
        closeModal('modal-riesgo-control'); await cargarRiesgosHigiene();
    });
}
async function abrirSeguimientoRiesgo(id) {
    const form = rrhhFormulario('form-seguimiento-riesgo'), row = riesgosControl.find(r => r.id === id);
    form.elements.riesgo_id.value = id;
    form.elements.fecha_revision.value = rrhhHoy();
    form.elements.estado.value = ['Pendiente','En seguimiento','Controlado'].includes(row?.estado) ? row.estado : 'Pendiente';
    document.getElementById('seguimiento-riesgo-nombre').textContent = `${row?.area || ''} — ${row?.tipo_riesgo || ''}`;
    document.getElementById('riesgo-historial').textContent = 'Cargando revisiones…';
    openModal('modal-seguimiento-riesgo'); await cargarSeguimientoRiesgo(id);
}
async function cargarSeguimientoRiesgo(id) {
    try {
        const rows = await rrhhApi(`/api/rrhh/higiene/riesgos/${id}/seguimiento`);
        document.getElementById('riesgo-historial').innerHTML = rows.map(r => `<article class="rrhh-revision"><strong>${rrhhEsc(r.fecha_revision)} · ${rrhhEsc(r.estado)}</strong><p>${rrhhEsc(r.observaciones)}</p><small>${rrhhEsc(r.registrado_por)}</small></article>`).join('') || '<p>Sin revisiones registradas.</p>';
    } catch (error) { document.getElementById('riesgo-historial').textContent = error.message; }
}
function guardarSeguimientoRiesgo(event) {
    return rrhhGuardar(event, async form => {
        const data = Object.fromEntries(new FormData(form));
        await rrhhApi(`/api/rrhh/higiene/riesgos/${data.riesgo_id}/seguimiento`, rrhhJson('POST', data));
        form.elements.observaciones.value = '';
        await cargarSeguimientoRiesgo(data.riesgo_id); await cargarRiesgosHigiene();
    });
}

async function cargarEppHigiene() {
    try {
        eppControl = await rrhhApi('/api/rrhh/higiene/epp');
        const select = document.getElementById('epp-empleado-filtro'), valor = select.value;
        const nombres = new Map(eppControl.map(r => [r.empleado_id, r.empleado]));
        select.innerHTML = '<option value="">Todos</option>' + [...nombres].map(([id,nombre]) => `<option value="${id}">${rrhhEsc(nombre)}</option>`).join('');
        select.value = nombres.has(Number(valor)) ? valor : '';
        renderEpp();
    } catch (error) { rrhhFilaError('tbody-higiene-epp', 7, error); }
}
function eppFiltrados() {
    return eppControl.filter(r => (!rrhhValor('epp-empleado-filtro') || String(r.empleado_id) === rrhhValor('epp-empleado-filtro'))
        && (r.area || '').toLocaleLowerCase().includes(rrhhValor('epp-area-filtro').toLocaleLowerCase())
        && (!rrhhValor('epp-desde') || r.fecha_entrega >= rrhhValor('epp-desde'))
        && (!rrhhValor('epp-hasta') || r.fecha_entrega <= rrhhValor('epp-hasta'))
        && (rrhhValor('epp-vista') !== 'pendientes' || (!r.reposicion_id && r.fecha_reposicion_sugerida && r.fecha_reposicion_sugerida <= rrhhHoy()))
        && (rrhhValor('epp-vista') !== 'repuestas' || r.reposicion_id));
}
function renderEpp() {
    const rows = eppFiltrados(), tbody = document.getElementById('tbody-higiene-epp');
    if (!tbody) return;
    document.getElementById('epp-resumen').textContent = `${rows.length} entregas · ${rows.reduce((n,r) => n + Number(r.cantidad || 0),0)} unidades en esta vista`;
    tbody.innerHTML = rows.map(r => `<tr>
        <td><strong>${rrhhEsc(r.empleado)}</strong><small class="rrhh-descripcion">${rrhhEsc(r.area || 'Área no registrada')}</small></td>
        <td>${rrhhEsc(r.tipo_equipo)}${r.repone_a_id ? `<small class="rrhh-descripcion">Repone entrega #${r.repone_a_id}</small>` : ''}</td>
        <td>${rrhhEsc(r.cantidad)}</td><td>${rrhhEsc(r.fecha_entrega)}</td><td>${rrhhEsc(r.estado_equipo)}</td>
        <td>${r.reposicion_id ? `Repuesta · #${r.reposicion_id}` : rrhhEsc(r.fecha_reposicion_sugerida || 'Sin fecha prevista')}${!r.reposicion_id && r.fecha_reposicion_sugerida && r.fecha_reposicion_sugerida <= rrhhHoy() ? '<small class="rrhh-descripcion rrhh-error">Pendiente de reposición</small>' : ''}</td>
        <td><div class="rrhh-acciones"><button class="btn btn-secondary" onclick="verDetalleEpp(${r.id})">Detalle</button><button class="btn btn-secondary" onclick="historialEppEmpleado(${r.empleado_id})">Historial</button>${!r.reposicion_id ? `<button class="btn btn-secondary" onclick="abrirEntregaEpp(${r.id})">Reponer</button>` : ''}</div></td>
    </tr>`).join('') || '<tr><td colspan="7">No hay dotaciones para los filtros seleccionados.</td></tr>';
}
function historialEppEmpleado(id) {
    document.getElementById('epp-empleado-filtro').value = String(id);
    for (const key of ['epp-area-filtro','epp-desde','epp-hasta']) document.getElementById(key).value = '';
    document.getElementById('epp-vista').value = 'historial'; renderEpp();
}
async function abrirEntregaEpp(id) {
    const form = rrhhFormulario('form-entrega-epp'), row = eppControl.find(r => r.id === id);
    document.getElementById('epp-titulo').textContent = row ? `Reponer entrega #${id}` : 'Registrar entrega de EPP';
    form.elements.fecha_entrega.value = rrhhHoy();
    form.elements.repone_a_id.value = row ? id : '';
    document.getElementById('epp-motivo-grupo').hidden = !row;
    document.getElementById('epp-reposicion-nota').hidden = !row;
    form.elements.motivo_reposicion.required = !!row;
    form.elements.tipo_equipo.readOnly = !!row;
    form.elements.cantidad.readOnly = !!row;
    form.elements.empleado_id.disabled = !!row;
    form.elements.empleado_id.innerHTML = '<option value="">Cargando trabajadores…</option>';
    openModal('modal-entrega-epp');
    try {
        empleadosControl = await rrhhApi('/api/empleados');
        form.elements.empleado_id.innerHTML = '<option value="">Seleccione un trabajador</option>' + empleadosControl.filter(e => e.activo).map(e => `<option value="${e.id}">${rrhhEsc(e.nombre_completo)}</option>`).join('');
        if (row) for (const key of ['empleado_id','tipo_equipo','cantidad','area']) form.elements[key].value = row[key] ?? '';
    } catch (error) { form.querySelector('.rrhh-error').textContent = error.message; }
}
function guardarEntregaEpp(event) {
    return rrhhGuardar(event, async form => {
        const data = new FormData(form);
        data.set('empleado_id', form.elements.empleado_id.value);
        await rrhhApi('/api/rrhh/higiene/epp', {method:'POST', body:data});
        closeModal('modal-entrega-epp'); await cargarEppHigiene();
    });
}
function verDetalleEpp(id) {
    const r = eppControl.find(e => e.id === id);
    if (!r) return;
    document.getElementById('epp-detalle-contenido').innerHTML = `<dl class="rrhh-detalle">${[
        ['Trabajador',r.empleado], ['Área',r.area], ['Equipo',r.tipo_equipo], ['Cantidad',r.cantidad],
        ['Fecha de entrega',r.fecha_entrega], ['Estado al entregar',r.estado_equipo], ['Reposición prevista',r.fecha_reposicion_sugerida],
        ['Entregado por',r.entregado_por], ['Observaciones',r.observaciones], ['Repone a',r.repone_a_id ? '#'+r.repone_a_id : ''],
        ['Motivo de reposición',r.motivo_reposicion], ['Entrega de reemplazo',r.reposicion_id ? '#'+r.reposicion_id : '']
    ].map(([k,v]) => `<dt>${k}</dt><dd>${rrhhEsc(v ?? '') || '—'}</dd>`).join('')}</dl>` +
        (r.archivo_id ? `<a class="btn btn-secondary" href="/api/rrhh/archivos/${r.archivo_id}">Descargar constancia de recepción</a>` : '<p>Sin constancia adjunta.</p>');
    openModal('modal-epp-detalle');
}
function exportarEpp() {
    const columns = ['empleado','area','tipo_equipo','cantidad','fecha_entrega','estado_equipo','fecha_reposicion_sugerida','entregado_por','repone_a_id','reposicion_id','motivo_reposicion','observaciones'];
    const cell = value => '"' + String(value ?? '').replace(/^[=+@\-\t\r]/, "'$&").replace(/"/g, '""') + '"';
    const csv = [columns.map(cell).join(','), ...eppFiltrados().map(row => columns.map(key => cell(row[key])).join(','))].join('\r\n');
    const url = URL.createObjectURL(new Blob(['\ufeff'+csv], {type:'text/csv;charset=utf-8'}));
    const link = document.createElement('a'); link.href = url; link.download = 'historial-epp.csv'; link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function cargarDocumentosExpediente(empId) {
    try {
        const rows = await rrhhApi(`/api/rrhh/expedientes/${empId}`);
        document.getElementById('tbody-expediente-documentos').innerHTML = rows.map(d => `<tr>
            <td>${rrhhEsc(d.tipo_documento)}</td><td>${rrhhEsc(d.nombre_archivo)}</td><td>${rrhhEsc(String(d.fecha_registro || '').slice(0,10))}</td>
            <td>${rrhhEsc(d.usuario_responsable)}</td><td>${d.archivo_id ? `<a href="/api/rrhh/archivos/${d.archivo_id}">Descargar</a>` : 'Solo referencia; sin archivo adjunto'}</td>
        </tr>`).join('') || '<tr><td colspan="5">No hay documentos registrados.</td></tr>';
    } catch (error) { rrhhFilaError('tbody-expediente-documentos', 5, error); }
}
function guardarDocumentoExpediente(event) {
    return rrhhGuardar(event, async form => {
        const data = new FormData();
        data.set('tipo_documento', document.getElementById('exp-tipo-doc').value);
        data.set('observaciones', document.getElementById('exp-observaciones').value);
        const file = document.getElementById('exp-archivo').files[0];
        if (!file) throw new Error('Seleccione un documento.');
        data.set('archivo', file);
        await rrhhApi(`/api/rrhh/expedientes/${_expedienteEmpActivo}`, {method:'POST',body:data});
        form.reset(); await cargarDocumentosExpediente(_expedienteEmpActivo);
    });
}

async function abrirPagoControl() {
    const form = rrhhFormulario('form-pago-control');
    if (form.elements.pago_id) form.elements.pago_id.value = '';
    form.elements.nomina_id.disabled = false;
    form.elements.empleado_id.disabled = false;
    form.elements.fecha_pago.value = rrhhHoy();
    form.elements.nomina_id.innerHTML = '<option value="">Cargando nóminas…</option>';
    form.elements.empleado_id.innerHTML = '<option value="">Seleccione una nómina</option>';
    document.getElementById('pago-saldo').textContent = '';
    const tit = document.getElementById('modal-pago-control-titulo');
    if (tit) tit.textContent = 'Registrar pago de nómina';
    const btn = document.getElementById('btn-guardar-pago-control');
    if (btn) btn.textContent = 'Confirmar pago';
    if (form.elements.metodo_pago) form.elements.metodo_pago.value = 'Transferencia Bancaria';
    if (form.elements.cuenta_id) form.elements.cuenta_id.value = '2';
    if (form.elements.estado) form.elements.estado.value = 'Confirmado';
    actualizarEstadoPagoUI();
    openModal('modal-pago-control');
    try {
        const rows = await rrhhApi('/api/nomina/historial');
        form.elements.nomina_id.innerHTML = '<option value="">Seleccione una nómina</option>' + rows.map(r => `<option value="${r.id}">#${r.id} · ${r.mes}/${r.anio}</option>`).join('');
    } catch (error) { form.querySelector('.rrhh-error').textContent = error.message; }
}
function actualizarCuentaSugeridaPago() {
    const form = document.getElementById('form-pago-control');
    if (!form || !form.elements.metodo_pago || !form.elements.cuenta_id) return;
    const metodo = form.elements.metodo_pago.value;
    form.elements.cuenta_id.value = (metodo === 'Efectivo') ? '1' : '2';
}
window.actualizarCuentaSugeridaPago = actualizarCuentaSugeridaPago;

function actualizarEstadoPagoUI() {
    const form = document.getElementById('form-pago-control');
    if (!form) return;
    const estado = form.elements.estado ? form.elements.estado.value : 'Confirmado';
    const esConfirmado = (estado === 'Confirmado');
    const metodoEl = form.elements.metodo_pago;
    const cuentaEl = form.elements.cuenta_id;
    const refEl = form.elements.numero_referencia;
    const btn = document.getElementById('btn-guardar-pago-control');

    [metodoEl, cuentaEl, refEl].forEach(el => {
        if (!el) return;
        el.disabled = !esConfirmado;
        el.style.opacity = esConfirmado ? '1' : '0.45';
        el.style.cursor = esConfirmado ? 'default' : 'not-allowed';
        el.style.backgroundColor = esConfirmado ? '' : 'rgba(255, 255, 255, 0.05)';
    });

    if (refEl) {
        refEl.required = esConfirmado;
        if (!esConfirmado) {
            refEl.placeholder = `(No aplica en estado ${estado})`;
        } else {
            refEl.placeholder = 'Ej: BAC-TRF-001 o LAFISE-002';
        }
    }

    if (btn) {
        const esNuevo = !form.elements.pago_id || !form.elements.pago_id.value;
        if (esNuevo) {
            btn.textContent = esConfirmado ? 'Confirmar pago' : `Guardar comprobante (${estado})`;
        }
    }
}
window.actualizarEstadoPagoUI = actualizarEstadoPagoUI;

async function cargarEmpleadosPago() {
    const form = document.getElementById('form-pago-control');
    form.elements.empleado_id.innerHTML = '<option value="">Seleccione un trabajador</option>';
    detallesPagoControl = []; document.getElementById('pago-saldo').textContent = '';
    form.elements.monto_pagado.value = '';
    if (!form.elements.nomina_id.value) return;
    const id = form.elements.nomina_id.value;
    try {
        const [detalle, pagos] = await Promise.all([rrhhApi(`/api/nomina/${id}/detalle`), rrhhApi('/api/rrhh/pagos-nomina')]);
        if (form.elements.nomina_id.value !== id) return;
        detallesPagoControl = detalle.detalles; pagosControl = pagos;
        form.elements.empleado_id.innerHTML += detallesPagoControl.map(r => `<option value="${r.empleado_id}">${rrhhEsc(r.empleado)}</option>`).join('');
    } catch (error) { form.querySelector('.rrhh-error').textContent = error.message; }
}
function mostrarSaldoPago() {
    const form = document.getElementById('form-pago-control');
    const row = detallesPagoControl.find(r => String(r.empleado_id) === form.elements.empleado_id.value);
    if (!row) { document.getElementById('pago-saldo').textContent = ''; return; }
    const pagado = pagosControl.filter(p => String(p.nomina_id) === form.elements.nomina_id.value && p.empleado_id === row.empleado_id && p.estado === 'Confirmado').reduce((n,p) => n+Number(p.monto_pagado),0);
    const saldo = Math.max(0, Number(row.neto_pagar)-pagado).toFixed(2);
    document.getElementById('pago-saldo').textContent = `Saldo pendiente: ${formatMoneda(saldo, 'C$ ')}`;
    form.elements.monto_pagado.max = saldo; form.elements.monto_pagado.value = saldo;
}
function guardarPagoControl(event) {
    return rrhhGuardar(event, async form => {
        const id = form.elements.pago_id?.value;
        const payload = Object.fromEntries(new FormData(form));
        if (form.elements.metodo_pago) payload.metodo_pago = form.elements.metodo_pago.value;
        if (form.elements.cuenta_id) payload.cuenta_id = form.elements.cuenta_id.value;
        if (form.elements.numero_referencia) payload.numero_referencia = form.elements.numero_referencia.value;
        if (form.elements.estado) payload.estado = form.elements.estado.value;
        if (id) {
            await rrhhApi(`/api/rrhh/pagos-nomina/${id}`, rrhhJson('PUT', payload));
        } else {
            await rrhhApi('/api/rrhh/pagos-nomina', rrhhJson('POST', payload));
        }
        closeModal('modal-pago-control');
        if (typeof cargarPagosNomina === 'function') await cargarPagosNomina();
    });
}

async function editarPagoNomina(id) {
    let p = (typeof _pagosNominaCache !== 'undefined' ? _pagosNominaCache : []).find(x => x.id === id);
    if (!p) {
        try {
            p = await rrhhApi(`/api/rrhh/pagos-nomina/${id}`);
        } catch (e) {
            console.error('Error buscando pago:', e);
        }
    }
    if (!p) {
        Swal.fire('Error', 'Comprobante de pago no encontrado.', 'error');
        return;
    }

    const form = rrhhFormulario('form-pago-control');
    if (form.elements.pago_id) form.elements.pago_id.value = p.id;

    try {
        const rows = await rrhhApi('/api/nomina/historial');
        form.elements.nomina_id.innerHTML = rows.map(r => `<option value="${r.id}" ${r.id === p.nomina_id ? 'selected' : ''}>#${r.id} · ${r.mes}/${r.anio}</option>`).join('');
    } catch (e) { }

    form.elements.nomina_id.value = p.nomina_id;
    form.elements.nomina_id.disabled = true;

    form.elements.empleado_id.innerHTML = `<option value="${p.empleado_id}" selected>${rrhhEsc(p.empleado || 'Empleado')}</option>`;
    form.elements.empleado_id.disabled = true;

    form.elements.fecha_pago.value = p.fecha_pago ? p.fecha_pago.slice(0, 10) : rrhhHoy();
    form.elements.metodo_pago.value = p.metodo_pago || 'Transferencia Bancaria';
    if (form.elements.cuenta_id) {
        form.elements.cuenta_id.value = p.cuenta_id ? String(p.cuenta_id) : (p.metodo_pago === 'Efectivo' ? '1' : '2');
    }
    form.elements.numero_referencia.value = p.numero_referencia || '';
    form.elements.monto_pagado.removeAttribute('max');
    form.elements.monto_pagado.value = p.monto_pagado;

    if (form.elements.estado) {
        form.elements.estado.value = p.estado || 'Confirmado';
    }
    actualizarEstadoPagoUI();

    document.getElementById('pago-saldo').textContent = `Monto registrado: C$ ${Number(p.monto_pagado).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
    const tit = document.getElementById('modal-pago-control-titulo');
    if (tit) tit.textContent = `Editar comprobante de pago #${p.id}`;
    const btn = document.getElementById('btn-guardar-pago-control');
    if (btn) btn.textContent = 'Actualizar pago';

    openModal('modal-pago-control');
}

async function eliminarPagoNomina(id) {
    let p = (typeof _pagosNominaCache !== 'undefined' ? _pagosNominaCache : []).find(x => x.id === id);
    const emp = p ? p.empleado : 'este trabajador';
    const monto = p ? Number(p.monto_pagado).toLocaleString('en-US', {minimumFractionDigits: 2}) : '';
    const ref = p && p.numero_referencia ? ` (Ref: ${p.numero_referencia})` : '';

    const confirm = await Swal.fire({
        title: '¿Eliminar comprobante de pago?',
        text: `Se eliminará el pago de ${emp} por C$ ${monto}${ref}. Esta acción no se puede deshacer.`,
        icon: 'warning',
        showCancelButton: true,
        confirmButtonColor: '#ef4444',
        cancelButtonColor: '#6b7280',
        confirmButtonText: 'Sí, eliminar',
        cancelButtonText: 'Cancelar'
    });

    if (!confirm.isConfirmed) return;

    try {
        const res = await rrhhApi(`/api/rrhh/pagos-nomina/${id}`, { method: 'DELETE' });
        Swal.fire('Eliminado', res.mensaje || 'Comprobante de pago eliminado correctamente.', 'success');
        if (typeof cargarPagosNomina === 'function') await cargarPagosNomina();
    } catch (e) {
        Swal.fire('Error', e.message || 'No se pudo eliminar el comprobante de pago.', 'error');
    }
}

window.editarPagoNomina = editarPagoNomina;
window.eliminarPagoNomina = eliminarPagoNomina;
window.abrirPagoControl = abrirPagoControl;

