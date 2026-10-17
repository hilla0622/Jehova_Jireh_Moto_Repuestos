// RF96-RF100: controles del contador. El servidor valida y audita cada cambio.
let configFlujo = null;
let asientoFlujo = null;
let cortesFlujo = {};
const campoFlujo = id => document.getElementById(id);

async function apiFlujo(url, body) {
    const resp = await fetch(url, body === undefined ? {} : {
        method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || 'No se pudo completar la operación.');
    return data;
}

async function accionFlujo(accion) {
    const status = campoFlujo('flujo-control-mensaje');
    try { status.textContent = 'Procesando…'; await accion(); }
    catch (e) { status.textContent = e.message; }
}

async function cargarConfiguracionFlujo() {
    await accionFlujo(async () => {
        configFlujo = await apiFlujo('/api/finanzas/flujo/configuracion');
        campoFlujo('flujo-config-cuenta').innerHTML = opcionesCuentasFlujo();
        campoFlujo('flujo-regla-origen').innerHTML = configFlujo.modulos.filter(m => m.modulo_origen).map(m =>
            `<option value="${escapeFlujo(m.modulo_origen)}">${escapeFlujo(m.modulo_origen)}</option>`).join('');
        mostrarEtiquetaFlujo();
        campoFlujo('flujo-regla-origen').onchange = () => {
            campoFlujo('flujo-regla-actividad').value = configFlujo.reglas[campoFlujo('flujo-regla-origen').value]?.actividad || '';
        };
        campoFlujo('flujo-regla-origen').onchange();
        campoFlujo('flujo-control-mensaje').textContent = 'Configuración cargada.';
    });
}

function opcionesCuentasFlujo() {
    return (configFlujo?.cuentas || []).map(c => `<option value="${c.id}">${escapeFlujo(c.codigo)} — ${escapeFlujo(c.nombre)}${c.flujo_categoria ? '' : ' (sin etiqueta)'}</option>`).join('');
}

function mostrarEtiquetaFlujo() {
    const c = configFlujo?.cuentas.find(c => c.id === Number(campoFlujo('flujo-config-cuenta').value));
    if (!c) return;
    campoFlujo('flujo-config-etiqueta').value = c.flujo_categoria || '';
    campoFlujo('flujo-config-nomonetario').checked = Boolean(c.ajuste_no_monetario);
}

async function cambioFlujo(url, body) {
    const res = await apiFlujo(url, body);
    await loadFlujoEfectivo();
    campoFlujo('flujo-control-mensaje').textContent = res.message;
}

function guardarEtiquetaFlujo(event) {
    event.preventDefault();
    accionFlujo(async () => {
        await cambioFlujo('/api/finanzas/flujo/configuracion', {
            cuenta_id: Number(campoFlujo('flujo-config-cuenta').value),
            flujo_categoria: campoFlujo('flujo-config-etiqueta').value,
            ajuste_no_monetario: campoFlujo('flujo-config-nomonetario').checked,
            motivo: campoFlujo('flujo-config-motivo').value
        });
        configFlujo = await apiFlujo('/api/finanzas/flujo/configuracion');
    });
}

function guardarReglaFlujo(event) {
    event.preventDefault();
    accionFlujo(async () => {
        await cambioFlujo('/api/finanzas/flujo/configuracion', {
            tipo: 'regla', modulo_origen: campoFlujo('flujo-regla-origen').value,
            actividad: campoFlujo('flujo-regla-actividad').value || null,
            motivo: campoFlujo('flujo-regla-motivo').value
        });
        configFlujo = await apiFlujo('/api/finanzas/flujo/configuracion');
    });
}

function consultarAsientoFlujo(event) {
    event.preventDefault();
    const aid = Number(campoFlujo('flujo-asiento-id').value);
    asientoFlujo = null;
    campoFlujo('flujo-asiento-herramientas').hidden = true;
    accionFlujo(async () => {
        const data = await apiFlujo('/api/finanzas/flujo/asiento/' + aid);
        if (aid !== Number(campoFlujo('flujo-asiento-id').value)) return;
        asientoFlujo = {...data, id: aid};
        campoFlujo('flujo-asiento-detalle').innerHTML = `<table class="table"><thead><tr><th>Movimiento</th><th>Cuenta</th><th>Debe</th><th>Haber</th><th>Etiqueta</th></tr></thead><tbody>${data.movimientos.map(m => `<tr><td>${m.movimiento_id}</td><td>${escapeFlujo(m.codigo)} ${escapeFlujo(m.nombre)}</td><td>${formatCordoba(m.debe)}</td><td>${formatCordoba(m.haber)}</td><td>${escapeFlujo(m.flujo_categoria || 'Pendiente')}</td></tr>`).join('')}</tbody></table>`;
        campoFlujo('flujo-asiento-herramientas').hidden = false;
        campoFlujo('flujo-distribucion-filas').innerHTML = '';
        const partes = data.distribucion?.partes || [{actividad: 'Operacion', importe: data.movimientos.filter(m => m.es_efectivo).reduce((n, m) => n + Number(m.debe) - Number(m.haber), 0)}];
        partes.forEach(p => agregarDistribucionFlujo(p));
        campoFlujo('flujo-ajuste-movimiento').innerHTML = data.movimientos.filter(m => !m.es_efectivo).map(m => `<option value="${m.movimiento_id}">${m.movimiento_id} — ${escapeFlujo(m.nombre)}</option>`).join('');
        campoFlujo('flujo-ajuste-movimiento').onchange = () => {
            const a = data.ajustes[campoFlujo('flujo-ajuste-movimiento').value];
            campoFlujo('flujo-ajuste-importe').value = a?.activo ? a.importe : 0;
            campoFlujo('flujo-ajuste-motivo').value = a?.motivo || '';
        };
        campoFlujo('flujo-ajuste-movimiento').onchange();
        campoFlujo('flujo-correccion-filas').innerHTML = '';
        data.movimientos.forEach(m => agregarCorreccionFlujo(m));
        campoFlujo('flujo-correccion-fecha').value = data.movimientos[0]?.fecha || '';
        campoFlujo('flujo-control-mensaje').textContent = `Asiento ${aid} cargado. Revise sus movimientos antes de aplicar cambios.`;
    });
}

function agregarDistribucionFlujo(p = {}) {
    const row = document.createElement('div');
    row.className = 'flujo-distribucion-fila';
    row.style.cssText = 'display:flex;gap:.5rem;flex-wrap:wrap;margin:.5rem 0';
    row.innerHTML = `<select class="form-control" aria-label="Actividad" style="flex:1"><option value="Operacion">Operación</option><option value="Inversion">Inversión</option><option value="Financiamiento">Financiamiento</option></select><input class="form-control" aria-label="Importe con signo" type="number" step="0.01" required style="flex:1"><button type="button" class="btn btn-secondary">Quitar</button>`;
    row.querySelector('select').value = p.actividad || 'Operacion';
    row.querySelector('input').value = p.importe ?? '';
    row.querySelector('button').onclick = () => row.remove();
    campoFlujo('flujo-distribucion-filas').appendChild(row);
}

function guardarDistribucionFlujo(event) {
    event.preventDefault();
    if (!asientoFlujo) return;
    accionFlujo(() => cambioFlujo('/api/finanzas/reclasificaciones', {
        asiento_id: asientoFlujo.id, revision: asientoFlujo.revision,
        partes: [...document.querySelectorAll('.flujo-distribucion-fila')].map(r => ({actividad: r.querySelector('select').value, importe: r.querySelector('input').value})),
        motivo: campoFlujo('flujo-distribucion-motivo').value
    }));
}

function guardarAjusteFlujo(event) {
    event.preventDefault();
    accionFlujo(() => cambioFlujo('/api/finanzas/flujo/ajustes', {
        movimiento_id: Number(campoFlujo('flujo-ajuste-movimiento').value),
        importe: campoFlujo('flujo-ajuste-importe').value,
        restaurar: campoFlujo('flujo-ajuste-restaurar').checked, motivo: campoFlujo('flujo-ajuste-motivo').value
    }));
}

function agregarCorreccionFlujo(m = {}) {
    const row = document.createElement('div');
    row.className = 'flujo-correccion-fila';
    row.style.cssText = 'display:flex;gap:.5rem;flex-wrap:wrap;margin:.5rem 0';
    row.innerHTML = `<select class="form-control" aria-label="Cuenta" style="flex:2">${opcionesCuentasFlujo()}</select><input class="form-control" aria-label="Debe" type="number" min="0" step="0.01" placeholder="Debe" required style="flex:1;min-width:6rem"><input class="form-control" aria-label="Haber" type="number" min="0" step="0.01" placeholder="Haber" required style="flex:1;min-width:6rem"><button type="button" class="btn btn-secondary">Quitar</button>`;
    if (m.cuenta_id) row.querySelector('select').value = m.cuenta_id;
    row.querySelectorAll('input')[0].value = m.debe || 0;
    row.querySelectorAll('input')[1].value = m.haber || 0;
    row.querySelector('button').onclick = () => row.remove();
    campoFlujo('flujo-correccion-filas').appendChild(row);
}

function guardarCorreccionFlujo(event) {
    event.preventDefault();
    if (!asientoFlujo || !confirm('Se registrará un asiento de ajuste en el mayor, conservando el original. ¿Continuar?')) return;
    accionFlujo(async () => {
        await cambioFlujo('/api/finanzas/flujo/correcciones', {
            asiento_id: asientoFlujo.id, revision: asientoFlujo.revision,
            fecha: campoFlujo('flujo-correccion-fecha').value, motivo: campoFlujo('flujo-correccion-motivo').value,
            movimientos: [...document.querySelectorAll('.flujo-correccion-fila')].map(r => ({cuenta_id: Number(r.querySelector('select').value), debe: r.querySelectorAll('input')[0].value, haber: r.querySelectorAll('input')[1].value}))
        });
        asientoFlujo = null;
        campoFlujo('flujo-asiento-herramientas').hidden = true;
    });
}

function cargarHistorialFlujo() {
    accionFlujo(async () => {
        const [cortes, auditoria] = await Promise.all([apiFlujo('/api/finanzas/flujo_efectivo/cortes'), apiFlujo('/api/finanzas/flujo/auditoria')]);
        cortesFlujo = cortes.cortes;
        campoFlujo('flujo-cortes-lista').innerHTML = Object.entries(cortesFlujo).map(([id, c]) => `<button class="btn btn-secondary" type="button" onclick="mostrarCorteFlujo(${Number(id)})">Corte ${Number(id)}: ${escapeFlujo(c.periodo.start)} a ${escapeFlujo(c.periodo.end)} (${escapeFlujo(c.metodo)})</button>`).join('') || '<p>Sin cortes guardados.</p>';
        campoFlujo('flujo-auditoria-lista').innerHTML = auditoria.eventos.map(e => `<details><summary>${escapeFlujo(e.created_at)} · ${escapeFlujo(e.tipo)} · ${escapeFlujo(e.usuario)}: ${escapeFlujo(e.motivo)}</summary><pre style="white-space:pre-wrap">${escapeFlujo(JSON.stringify(e.contenido, null, 2))}</pre></details>`).join('');
        campoFlujo('flujo-control-mensaje').textContent = 'Historial cargado.';
    });
}

function mostrarCorteFlujo(id) {
    const reporte = cortesFlujo[id];
    if (!reporte) return;
    flujoActualData = null; // Un corte histórico se consulta/imprime, no se vuelve a guardar como actual.
    renderFlujoEfectivoHTML(reporte, campoFlujo('reporte-flujo-efectivo'));
    campoFlujo('reporte-flujo-efectivo').insertAdjacentHTML('afterbegin', `<p><strong>Corte histórico ${Number(id)}. Importes conservados a la fecha de elaboración.</strong></p>`);
    campoFlujo('reporte-flujo-efectivo').scrollIntoView({behavior: 'smooth'});
}


function exportarEstadoFinanciero(descargar) {
    const args = new URLSearchParams({metodo: metodoFlujoActual});
    const inicio = campoFlujo('fin-fecha-inicio').value, fin = campoFlujo('fin-fecha-fin').value;
    if (inicio) args.set('start', inicio);
    if (fin) args.set('end', fin);
    if (descargar) args.set('descargar', '1');
    const url = '/api/finanzas/reportes/exportar/' + campoFlujo('fin-exportar-tipo').value + '?' + args;
    if (descargar) {
        const link = document.createElement('a'); link.href = url; link.download = ''; link.click();
    } else {
        const popup = window.open(url, '_blank');
        if (!popup) alert('Permita abrir la ventana del reporte para imprimir o guardar PDF.');
    }
}
