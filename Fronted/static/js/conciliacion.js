// Conciliación mensual: extracto, cotejo uno a uno y puente banco → empresa.
let extractoConciliacion = {movimientos: [], vinculos: []};
let seleccionConciliacion = {banco: '', empresa: ''};
let conciliacionModificada = false;
let conciliacionGuardando = false;
const gruposConciliacion = [
    ['Nota de Debito', '+', 'Retiros del banco sin registrar en la empresa', 'Ejemplo: comisiones bancarias. Se suman para volver del saldo del banco al saldo de libros.'],
    ['Deposito en Transito', '+', 'Entradas de la empresa que no aparecen en el banco', 'Ejemplo: un depósito pendiente de acreditación. Se suma al saldo del banco.'],
    ['Nota de Credito', '−', 'Depósitos del banco sin registrar en la empresa', 'Ejemplo: un cobro recibido aún no contabilizado. Se resta para llegar al saldo de libros.'],
    ['Cheque en Transito', '−', 'Salidas de la empresa que no aparecen en el banco', 'Ejemplo: un cheque entregado y todavía no cobrado. Se resta del saldo del banco.'],
    ['Error en Libros', '±', 'Otros errores en los registros de la empresa', 'Revisá el comprobante y documentá la corrección. El puente invierte el efecto del ajuste a libros.']
];
const concEl = id => document.getElementById(id);
const concCentavos = valor => Math.round(Number(valor || 0) * 100);
const concDinero = centavos => formatCordoba(centavos / 100);
const concTexto = escapeFlujo;
function mensajeConciliacion(texto, error = false) {
    concEl('conc-mensaje').textContent = texto;
    concEl('conc-mensaje').dataset.error = error;
}
function marcarCambioConciliacion() {
    if (!conciliacionActualData || conciliacionActualData.solo_lectura) return;
    conciliacionModificada = true;
    concEl('conc-estado-guardado').textContent = 'Cambios sin guardar';
}
function editarConciliacion() {
    return conciliacionActualData && !conciliacionActualData.solo_lectura && !conciliacionGuardando;
}
async function cargarDatosConciliacion(descartar = false) {
    if (!concEl('conc-cuenta-banco') || conciliacionGuardando) return;
    if (conciliacionModificada && !descartar && !confirm('Hay cambios sin guardar. ¿Querés descartarlos y cargar el período?')) {
        concEl('conc-cuenta-banco').value = conciliacionActualData.cuenta.id;
        concEl('conc-mes').value = conciliacionActualData.mes;
        concEl('conc-anio').value = conciliacionActualData.anio;
        return;
    }
    const params = new URLSearchParams({cuenta_id: concEl('conc-cuenta-banco').value,
        anio: concEl('conc-anio').value, mes: concEl('conc-mes').value});
    const solicitud = ++solicitudConciliacion;
    conciliacionActualData = null;
    conciliacionModificada = false;
    concEl('conc-edicion').disabled = true;
    concEl('conc-estado-guardado').textContent = 'Cargando…';
    mensajeConciliacion('Cargando el mayor y el estado de cuenta guardado…');
    try {
        const resp = await fetch(`/api/finanzas/conciliacion/datos?${params}`);
        const data = await resp.json();
        if (solicitud !== solicitudConciliacion) return;
        if (!resp.ok || data.error) throw new Error(data.error || 'No se pudo cargar la conciliación.');
        conciliacionActualData = data;
        partidasEnTransito = data.partidas_pendientes || [];
        extractoConciliacion = data.extracto || {movimientos: [], vinculos: []};
        seleccionConciliacion = {banco: '', empresa: ''};
        concEl('conc-cuenta-banco').innerHTML = data.cuentas_bancos.map(c => `<option value="${c.id}">${concTexto(c.codigo)} · ${concTexto(c.nombre)}</option>`).join('');
        concEl('conc-cuenta-banco').value = data.cuenta.id;
        concEl('conc-input-saldo-banco').value = data.conciliacion_guardada?.saldo_segun_banco ?? '';
        concEl('conc-saldo-inicial-banco').value = data.extracto?.saldo_inicial ?? '';
        concEl('conc-lbl-saldo-libros').textContent = formatCordoba(data.saldo_segun_libros);
        concEl('conc-periodo-texto').textContent = `${data.cuenta.nombre} · Del ${data.fecha_corte.slice(0, 7)}-01 al ${data.fecha_corte}. Importes en córdobas (C$).`;
        for (const id of ['conc-banco-fecha', 'partida-fecha']) {
            concEl(id).max = data.fecha_corte;
            concEl(id).value = data.fecha_corte;
        }
        concEl('conc-banco-fecha').min = `${data.fecha_corte.slice(0, 7)}-01`;
        concEl('conc-edicion').disabled = data.solo_lectura;
        concEl('conc-estado-guardado').textContent = data.solo_lectura ? 'Histórico · solo lectura' : data.conciliacion_guardada ? `Guardada · ${data.conciliacion_guardada.estado}` : 'Nueva conciliación';
        mensajeConciliacion(data.solo_lectura ? 'Este mes tiene conciliaciones posteriores y está protegido. Consultá sus movimientos y diferencias; la edición está deshabilitada.' : data.conciliacion_guardada && !data.extracto ? 'Este corte se guardó con el método anterior, por saldos. Sus diferencias se conservaron. Completá el extracto para revisar movimiento por movimiento.' : 'Empezá con los saldos y movimientos del extracto. Los registros de la empresa ya están cargados.');
        renderPartidasTransito();
        renderComparacionConciliacion();
        if (typeof cargarReclasificaciones === 'function') cargarReclasificaciones();
    } catch (e) {
        if (solicitud !== solicitudConciliacion) return;
        concEl('conc-estado-guardado').textContent = 'No se pudo cargar';
        mensajeConciliacion(e.message, true);
    }
}
function empresaDisponibleConciliacion() {
    const movimientos = (conciliacionActualData?.movimientos_mes || []).map(m => ({...m, clave: `m:${m.movimiento_id}`, neto: concCentavos(m.debe) - concCentavos(m.haber)}));
    for (const p of partidasEnTransito.filter(p => p.heredada && ['Deposito en Transito', 'Cheque en Transito'].includes(p.tipo_partida))) {
        if (!p.esta_conciliada || extractoConciliacion.vinculos.some(v => v.partida_uid === p.uid)) movimientos.push({clave: `p:${p.uid}`, fecha: p.fecha, concepto: `Pendiente anterior: ${p.descripcion}`, referencia: p.numero_documento_referencia, neto: concCentavos(p.monto) * (p.tipo_partida === 'Deposito en Transito' ? 1 : -1), pendiente: true});
    }
    return movimientos;
}
function estadoFilaConciliacion(lado, id) {
    const vi = extractoConciliacion.vinculos.findIndex(v => lado === 'Banco' ? v.banco_uid === id : id === (v.partida_uid ? `p:${v.partida_uid}` : `m:${v.movimiento_id}`));
    if (vi >= 0) return {estado: 'vinculado', indice: vi};
    const pi = partidasEnTransito.findIndex(p => !p.esta_conciliada && p.origen === lado && String(p.origen_id) === (lado === 'Empresa' ? id.slice(2) : id) && p.periodo_origen === conciliacionActualData.fecha_corte.slice(0, 7));
    if (pi >= 0) return {estado: 'explicado', indice: pi};
    if (lado === 'Empresa') {
        const resuelta = partidasEnTransito.some(p => p.heredada && p.esta_conciliada && ['Nota de Credito', 'Nota de Debito'].includes(p.tipo_partida) && `m:${p.movimiento_contable_id}` === id);
        if (resuelta) return {estado: 'explicado', indice: -1};
    }
    return {estado: 'pendiente'};
}
function accionesFilaConciliacion(lado, id, index, pendiente = false) {
    const estado = estadoFilaConciliacion(lado, id);
    if (estado.estado === 'vinculado') return `<span class="conc-status">✓ Vinculado</span><button type="button" class="conc-link" onclick="desvincularConciliacion(${estado.indice})">Desvincular</button>`;
    if (estado.estado === 'explicado') return '<span class="conc-status explicado">Diferencia explicada</span>';
    const key = lado === 'Banco' ? 'banco' : 'empresa';
    return `<label class="conc-inline"><input type="radio" name="conc-seleccion-${key}" value="${concTexto(id)}" ${seleccionConciliacion[key] === id ? 'checked' : ''} onchange="seleccionarFilaConciliacion('${key}',this.value)"> Seleccionar</label>${!pendiente ? `<button type="button" class="conc-link" onclick="clasificarFilaConciliacion('${lado}',${index})">Solo ${lado === 'Banco' ? 'banco' : 'empresa'}</button>` : '<small>Pendiente anterior</small>'}${lado === 'Banco' ? `<button type="button" class="conc-link" onclick="eliminarMovimientoBanco(${index})">Eliminar</button>` : ''}`;
}
function renderComparacionConciliacion() {
    if (!conciliacionActualData) return;
    const solo = concEl('conc-solo-pendientes').checked;
    let saldo = concCentavos(concEl('conc-saldo-inicial-banco').value);
    let filas = `<tr><td>Saldo inicial</td><td></td><td></td><td>${concEl('conc-saldo-inicial-banco').value === '' ? '—' : concDinero(saldo)}</td><td></td></tr>`;
    extractoConciliacion.movimientos.forEach((m, i) => {
        saldo += concCentavos(m.deposito) - concCentavos(m.retiro);
        const estado = estadoFilaConciliacion('Banco', m.uid).estado;
        if (solo && estado !== 'pendiente') return;
        filas += `<tr data-estado="${estado}"><td><small>${concTexto(m.fecha)}</small>${concTexto(m.concepto)}<small>${concTexto(m.referencia || 'Sin referencia')}</small></td><td>${m.retiro ? formatCordoba(m.retiro) : '—'}</td><td>${m.deposito ? formatCordoba(m.deposito) : '—'}</td><td>${concDinero(saldo)}</td><td>${accionesFilaConciliacion('Banco', m.uid, i)}</td></tr>`;
    });
    if (!extractoConciliacion.movimientos.length) filas += '<tr><td colspan="5" class="conc-empty">Todavía no agregaste movimientos del banco.<br>Transcribilos desde tu estado de cuenta con el botón del paso 1.</td></tr>';
    concEl('conc-tbody-banco').innerHTML = filas;
    let libros = concCentavos(conciliacionActualData.saldo_inicial_libros);
    filas = `<tr><td>Saldo inicial</td><td></td><td></td><td>${concDinero(libros)}</td><td></td></tr>`;
    empresaDisponibleConciliacion().forEach((m, i) => {
        if (!m.pendiente) libros += m.neto;
        const estado = estadoFilaConciliacion('Empresa', m.clave).estado;
        if (solo && estado !== 'pendiente') return;
        filas += `<tr data-estado="${estado}"><td><small>${concTexto(m.fecha)}</small>${concTexto(m.concepto)}<small>${m.pendiente ? concTexto(m.referencia) + ' · Ya incluido en el saldo inicial' : `Asiento ${m.asiento_id}`}</small></td><td>${m.neto > 0 ? concDinero(m.neto) : '—'}</td><td>${m.neto < 0 ? concDinero(-m.neto) : '—'}</td><td>${m.pendiente ? '—' : concDinero(libros)}</td><td>${accionesFilaConciliacion('Empresa', m.clave, i, m.pendiente)}</td></tr>`;
    });
    if (!empresaDisponibleConciliacion().length) filas += '<tr><td colspan="5" class="conc-empty">No hay movimientos de esta cuenta en el mes seleccionado.</td></tr>';
    concEl('conc-tbody-movimientos-libros').innerHTML = filas;
    const final = concEl('conc-input-saldo-banco').value;
    concEl('conc-control-extracto').textContent = concEl('conc-saldo-inicial-banco').value === '' ? 'Ingresá el saldo inicial que figura en el extracto.' : `Saldo inicial + depósitos − retiros = ${concDinero(saldo)}. ${final === '' ? 'Falta el saldo final del extracto.' : saldo === concCentavos(final) ? 'Coincide con el saldo final del extracto.' : `Faltan movimientos o hay importes por revisar: diferencia ${concDinero(saldo - concCentavos(final))}.`}`;
    concEl('conc-vincular').disabled = !(seleccionConciliacion.banco && seleccionConciliacion.empresa);
    recalcularConciliacionEnVivo();
}
function seleccionarFilaConciliacion(lado, valor) {
    seleccionConciliacion[lado] = valor;
    concEl('conc-vincular').disabled = !(seleccionConciliacion.banco && seleccionConciliacion.empresa);
}
function agregarMovimientoBanco(event) {
    event.preventDefault();
    if (!editarConciliacion()) return;
    const monto = Number(concEl('conc-banco-monto').value), dia = concEl('conc-banco-fecha').value;
    if (!Number.isFinite(monto) || monto <= 0 || dia.slice(0, 7) !== conciliacionActualData.fecha_corte.slice(0, 7)) return mensajeConciliacion('Revisá la fecha del mes y el importe positivo del movimiento.', true);
    const tipo = concEl('conc-banco-tipo').value;
    extractoConciliacion.movimientos.push({uid: crypto.randomUUID(), fecha: dia, concepto: concEl('conc-banco-concepto').value.trim(), referencia: concEl('conc-banco-ref').value.trim(), retiro: tipo === 'retiro' ? monto : 0, deposito: tipo === 'deposito' ? monto : 0});
    extractoConciliacion.movimientos.sort((a, b) => a.fecha.localeCompare(b.fecha));
    concEl('conc-form-banco').reset();
    concEl('conc-banco-fecha').value = dia;
    marcarCambioConciliacion(); renderComparacionConciliacion();
    mensajeConciliacion('Movimiento agregado al extracto. Continuá con el siguiente o comparalo con la empresa.');
    concEl('conc-banco-concepto').focus();
}
function eliminarMovimientoBanco(index) {
    if (!editarConciliacion()) return;
    const m = extractoConciliacion.movimientos[index];
    if (!m || estadoFilaConciliacion('Banco', m.uid).estado !== 'pendiente') return;
    extractoConciliacion.movimientos.splice(index, 1);
    seleccionConciliacion.banco = '';
    marcarCambioConciliacion(); renderComparacionConciliacion();
}
function crearVinculoConciliacion(banco, empresa) {
    if (empresa.pendiente) {
        const p = partidasEnTransito.find(p => `p:${p.uid}` === empresa.clave);
        p.esta_conciliada = true;
        p.resolucion = `Reflejado en el extracto ${banco.fecha}: ${banco.referencia || banco.concepto}`;
        extractoConciliacion.vinculos.push({banco_uid: banco.uid, partida_uid: p.uid});
    } else extractoConciliacion.vinculos.push({banco_uid: banco.uid, movimiento_id: empresa.movimiento_id});
}
function vincularSeleccionConciliacion() {
    if (!editarConciliacion()) return;
    const b = extractoConciliacion.movimientos.find(m => m.uid === seleccionConciliacion.banco);
    const e = empresaDisponibleConciliacion().find(m => m.clave === seleccionConciliacion.empresa);
    if (!b || !e || estadoFilaConciliacion('Banco', b.uid).estado !== 'pendiente' || estadoFilaConciliacion('Empresa', e.clave).estado !== 'pendiente') return mensajeConciliacion('Seleccioná un movimiento disponible de cada estado.', true);
    if (concCentavos(b.deposito) - concCentavos(b.retiro) !== e.neto) return mensajeConciliacion('Los movimientos seleccionados no tienen el mismo importe o sentido. Revisalos antes de vincular.', true);
    crearVinculoConciliacion(b, e);
    seleccionConciliacion = {banco: '', empresa: ''};
    marcarCambioConciliacion(); renderPartidasTransito(); renderComparacionConciliacion();
    mensajeConciliacion('Movimientos vinculados. Ambos representan la misma entrada o salida.');
}
function vincularCoincidenciasConciliacion() {
    if (!editarConciliacion()) return;
    const bs = extractoConciliacion.movimientos.filter(m => estadoFilaConciliacion('Banco', m.uid).estado === 'pendiente');
    const es = empresaDisponibleConciliacion().filter(m => !m.pendiente && estadoFilaConciliacion('Empresa', m.clave).estado === 'pendiente');
    let cantidad = 0;
    for (const b of bs) {
        const neto = concCentavos(b.deposito) - concCentavos(b.retiro);
        const candidatos = es.filter(e => e.fecha === b.fecha && e.neto === neto);
        if (candidatos.length === 1 && bs.filter(o => o.fecha === b.fecha && concCentavos(o.deposito) - concCentavos(o.retiro) === neto).length === 1) { crearVinculoConciliacion(b, candidatos[0]); cantidad++; }
    }
    seleccionConciliacion = {banco: '', empresa: ''};
    if (cantidad) marcarCambioConciliacion();
    renderComparacionConciliacion();
    mensajeConciliacion(`${cantidad} coincidencia(s) marcada(s) por fecha, monto y sentido. Revisá los conceptos; podés desvincular cualquier par. Las fechas diferentes y los importes repetidos requieren revisión manual.`);
}
function desvincularConciliacion(index) {
    if (!editarConciliacion()) return;
    const v = extractoConciliacion.vinculos[index];
    if (v.partida_uid) { const p = partidasEnTransito.find(p => p.uid === v.partida_uid); if (p) {p.esta_conciliada = false; p.resolucion = '';} }
    extractoConciliacion.vinculos.splice(index, 1);
    marcarCambioConciliacion(); renderPartidasTransito(); renderComparacionConciliacion();
}
function clasificarFilaConciliacion(lado, index) {
    if (!editarConciliacion()) return;
    const m = lado === 'Banco' ? extractoConciliacion.movimientos[index] : empresaDisponibleConciliacion()[index];
    const id = lado === 'Banco' ? m.uid : m.clave;
    if (estadoFilaConciliacion(lado, id).estado !== 'pendiente') return;
    const neto = lado === 'Banco' ? concCentavos(m.deposito) - concCentavos(m.retiro) : m.neto;
    if (!neto) return mensajeConciliacion('Un movimiento sin importe requiere revisión en el Libro Mayor.', true);
    const tipo = lado === 'Banco' ? (neto > 0 ? 'Nota de Credito' : 'Nota de Debito') : (neto > 0 ? 'Deposito en Transito' : 'Cheque en Transito');
    partidasEnTransito.push({uid: crypto.randomUUID(), tipo_partida: tipo, fecha: m.fecha, numero_documento_referencia: m.referencia || (lado === 'Banco' ? `Extracto ${m.fecha}` : `Asiento ${m.asiento_id}`), descripcion: m.concepto, monto: Math.abs(neto) / 100, efecto_en_saldo: neto > 0 ? 'Suma' : 'Resta', esta_conciliada: false, origen: lado, origen_id: lado === 'Banco' ? m.uid : String(m.movimiento_id), periodo_origen: conciliacionActualData.fecha_corte.slice(0, 7)});
    seleccionConciliacion = {banco: '', empresa: ''};
    marcarCambioConciliacion(); renderPartidasTransito(); renderComparacionConciliacion();
    mensajeConciliacion('Diferencia agregada al paso 3. Revisá su explicación y el documento de soporte.');
}
function renderPartidasTransito() {
    if (!concEl('conc-grupos')) return;
    const abiertos = new Set(Array.from(concEl('conc-grupos').querySelectorAll('details[open]')).map(el => el.dataset.partida));
    concEl('conc-grupos').innerHTML = gruposConciliacion.filter(([tipo]) => tipo !== 'Error en Libros' || partidasEnTransito.some(p => p.tipo_partida === tipo)).map(([tipo, signo, titulo, ayuda]) => {
        const items = partidasEnTransito.map((p, i) => ({p, i})).filter(({p}) => p.tipo_partida === tipo);
        const suma = items.filter(({p}) => !p.esta_conciliada).reduce((n, {p}) => n + concCentavos(p.monto), 0);
        return `<article class="conc-group"><div class="conc-group-head"><h5>${titulo}</h5><strong>${signo} ${concDinero(suma)}</strong></div><p>${ayuda}</p>${items.length ? items.map(({p, i}) => partidaHTMLConciliacion(p, i)).join('') : '<span class="conc-partida-meta">Sin diferencias registradas en este grupo.</span>'}</article>`;
    }).join('');
    for (const el of concEl('conc-grupos').querySelectorAll('details')) el.open = abiertos.has(el.dataset.partida);
}
function partidaHTMLConciliacion(p, i) {
    const vinculada = extractoConciliacion.vinculos.some(v => v.partida_uid === p.uid);
    const opciones = (conciliacionActualData?.movimientos_mes || []).map(m => `<option value="${m.movimiento_id}" ${String(p.movimiento_contable_id) === String(m.movimiento_id) ? 'selected' : ''}>${concTexto(m.fecha)} · ${concTexto(m.concepto)} · ${formatCordoba(Number(m.debe) - Number(m.haber))}</option>`).join('');
    return `<details data-partida="${concTexto(p.uid)}" class="${p.esta_conciliada ? 'conc-partida-resuelta' : ''}"><summary>${p.esta_conciliada ? '✓ Resuelta' : p.heredada ? 'Pendiente anterior' : 'Pendiente'} · ${concTexto(p.numero_documento_referencia)} · ${formatCordoba(p.monto)}</summary><div class="conc-partida-meta">${concTexto(p.fecha)} · ${concTexto(p.descripcion)}${p.origen ? `<br>Origen: ${concTexto(p.origen)} · ${concTexto(p.periodo_origen)}` : ''}</div><div class="conc-partida-fields"><label class="conc-inline"><input type="checkbox" ${p.esta_conciliada ? 'checked' : ''} ${vinculada ? 'disabled' : ''} onchange="resolverPartidaConciliacion(${i},this.checked)"> Resuelta con soporte</label><label>Referencia o explicación de resolución<input class="form-control" maxlength="500" value="${concTexto(p.resolucion || '')}" oninput="partidasEnTransito[${i}].resolucion=this.value;marcarCambioConciliacion()" placeholder="Ej. comisión registrada en asiento 45"></label><label>Movimiento contable de resolución (opcional)<select class="form-control" onchange="partidasEnTransito[${i}].movimiento_contable_id=this.value?Number(this.value):null;marcarCambioConciliacion();renderComparacionConciliacion()"><option value="">Sin vínculo contable</option>${p.movimiento_contable_id && !(conciliacionActualData?.movimientos_mes || []).some(m => String(m.movimiento_id) === String(p.movimiento_contable_id)) ? `<option selected value="${p.movimiento_contable_id}">Movimiento anterior #${p.movimiento_contable_id}</option>` : ''}${opciones}</select></label>${p.heredada ? '<small>Se conserva para mantener el historial. Resolvé el pendiente cuando tengas el soporte.</small>' : `<button type="button" class="conc-link" onclick="eliminarPartidaTransito(${i})">Quitar esta diferencia</button>`}${vinculada ? '<small>Vinculada al extracto actual. Desvinculá el movimiento para reabrir el pendiente.</small>' : ''}</div></details>`;
}
function resolverPartidaConciliacion(i, resuelta) {
    if (!editarConciliacion()) return;
    partidasEnTransito[i].esta_conciliada = resuelta;
    marcarCambioConciliacion(); renderPartidasTransito(); renderComparacionConciliacion();
}
function agregarPartidaTransito(event) {
    event.preventDefault();
    if (!editarConciliacion()) return;
    const tipo = concEl('partida-tipo').value;
    partidasEnTransito.push({uid: crypto.randomUUID(), tipo_partida: tipo, fecha: concEl('partida-fecha').value, numero_documento_referencia: concEl('partida-doc').value.trim(), descripcion: concEl('partida-desc').value.trim(), monto: Number(concEl('partida-monto').value), efecto_en_saldo: tipo === 'Error en Libros' ? concEl('partida-efecto').value : ['Deposito en Transito', 'Nota de Credito'].includes(tipo) ? 'Suma' : 'Resta', esta_conciliada: false});
    concEl('form-partida-transito').reset(); concEl('partida-fecha').value = conciliacionActualData.fecha_corte;
    marcarCambioConciliacion(); renderPartidasTransito(); renderComparacionConciliacion();
}
function eliminarPartidaTransito(index) {
    if (!editarConciliacion() || partidasEnTransito[index].heredada) return;
    partidasEnTransito.splice(index, 1);
    marcarCambioConciliacion(); renderPartidasTransito(); renderComparacionConciliacion();
}
function resumenConciliacionPantalla(libros, banco, partidas) {
    let l = concCentavos(libros), b = concCentavos(banco);
    for (const p of partidas.filter(p => !p.esta_conciliada)) {
        const m = concCentavos(p.monto);
        if (p.tipo_partida === 'Deposito en Transito') b += m;
        else if (p.tipo_partida === 'Cheque en Transito') b -= m;
        else if (p.tipo_partida === 'Nota de Credito') l += m;
        else if (p.tipo_partida === 'Nota de Debito') l -= m;
        else if (p.tipo_partida === 'Error en Libros') l += p.efecto_en_saldo === 'Suma' ? m : -m;
    }
    return {libros: l / 100, banco: b / 100, diferencia: (b - l) / 100, puente: (b - l + concCentavos(libros)) / 100};
}
function recalcularConciliacionEnVivo() {
    if (!conciliacionActualData) return;
    const valor = concEl('conc-input-saldo-banco').value, inicial = concEl('conc-saldo-inicial-banco').value;
    const banco = concCentavos(valor), libros = concCentavos(conciliacionActualData.saldo_segun_libros);
    const r = resumenConciliacionPantalla(libros / 100, banco / 100, partidasEnTransito);
    const sinBanco = extractoConciliacion.movimientos.filter(m => estadoFilaConciliacion('Banco', m.uid).estado === 'pendiente').length;
    const sinEmpresa = empresaDisponibleConciliacion().filter(m => !m.pendiente && estadoFilaConciliacion('Empresa', m.clave).estado === 'pendiente').length;
    const finalCalculado = concCentavos(inicial) + extractoConciliacion.movimientos.reduce((n, m) => n + concCentavos(m.deposito) - concCentavos(m.retiro), 0);
    const completo = inicial !== '' && finalCalculado === banco && sinBanco + sinEmpresa === 0;
    const cuadrado = valor !== '' && r.diferencia === 0;
    const pendientes = partidasEnTransito.filter(p => !p.esta_conciliada);
    const ajustes = pendientes.filter(p => ['Nota de Credito', 'Nota de Debito', 'Error en Libros'].includes(p.tipo_partida)).length;
    const fila = (label, monto, clase = '') => `<div class="${clase}"><span>${label}</span><strong>${valor === '' ? '—' : concDinero(monto)}</strong></div>`;
    let html = fila('Saldo final del banco', banco);
    for (const [tipo, signo, titulo] of gruposConciliacion) {
        const total = pendientes.filter(p => p.tipo_partida === tipo).reduce((n, p) => n + concCentavos(p.monto) * (tipo === 'Error en Libros' && p.efecto_en_saldo === 'Suma' ? -1 : 1), 0);
        if (tipo !== 'Error en Libros' || total) html += fila(`${signo} ${titulo}`, total);
    }
    html += fila('Saldo en conciliación', concCentavos(r.puente), 'conc-total') + fila('Saldo final de la empresa', libros) + fila('Diferencia pendiente por conciliar', concCentavos(r.diferencia), 'conc-total');
    concEl('conc-puente').innerHTML = html;
    concEl('conc-diferencia-original').textContent = valor === '' ? '—' : concDinero(banco - libros);
    concEl('conc-conteo').textContent = `${extractoConciliacion.vinculos.length} vinculados · ${sinBanco + sinEmpresa} sin revisar`;
    concEl('conc-badge-cuadratura').textContent = valor === '' ? 'Ingresá el saldo del banco' : cuadrado ? (completo ? 'Diferencia explicada · C$ 0.00' : 'Diferencia cero · revisión pendiente') : `Falta explicar ${formatCordoba(r.diferencia)}`;
    concEl('conc-badge-cuadratura').dataset.ok = cuadrado && completo;
    concEl('conc-siguiente-paso').textContent = !completo ? 'Completá el extracto y revisá los movimientos de ambos lados. Podés guardar el avance como borrador.' : !cuadrado ? 'Revisá los saldos y las diferencias del paso 3. Todavía no coinciden con el saldo de la empresa.' : ajustes ? 'La diferencia está explicada. Quedan ajustes por registrar en contabilidad; después documentá su resolución.' : pendientes.length ? 'La diferencia está explicada. Conservá los pendientes y verificá cuándo aparecen en el banco.' : 'Todos los movimientos están revisados y los saldos coinciden.';
    concEl('conc-pendientes-resumen').textContent = `${pendientes.length} diferencia(s) pendiente(s) de resolver · ${ajustes} por revisar en contabilidad.`;
    concEl('conc-guardar').textContent = cuadrado && completo ? 'Guardar conciliación revisada' : 'Guardar borrador';
}
async function guardarConciliacionBancaria() {
    if (!editarConciliacion()) return;
    const banco = concEl('conc-input-saldo-banco').value, inicial = concEl('conc-saldo-inicial-banco').value;
    if (banco === '' || inicial === '') return mensajeConciliacion('Ingresá el saldo inicial y el saldo final del extracto bancario antes de guardar.', true);
    if (partidasEnTransito.some(p => p.esta_conciliada && !(p.resolucion || '').trim())) return mensajeConciliacion('Escribí la referencia de resolución de cada diferencia marcada como resuelta.', true);
    const payload = {cuenta_id: conciliacionActualData.cuenta.id, anio: conciliacionActualData.anio, mes: conciliacionActualData.mes, saldo_segun_banco: banco, revision: conciliacionActualData.revision, partidas: partidasEnTransito, extracto: {...extractoConciliacion, saldo_inicial: inicial}, observaciones: conciliacionActualData.conciliacion_guardada?.observaciones || ''};
    conciliacionGuardando = true; concEl('conc-edicion').disabled = true;
    try {
        const resp = await fetch('/api/finanzas/conciliacion/guardar', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)});
        const res = await resp.json();
        if (!resp.ok || !res.success) throw new Error(res.error || 'No se pudo guardar.');
        conciliacionModificada = false; conciliacionGuardando = false;
        await cargarDatosConciliacion(true);
        mensajeConciliacion(`${res.message} Se conservaron el extracto, los vínculos y las diferencias. Guardar no genera asientos contables.`);
    } catch (e) {
        mensajeConciliacion(e.message, true);
    } finally {
        conciliacionGuardando = false;
        concEl('conc-edicion').disabled = !conciliacionActualData || conciliacionActualData.solo_lectura;
    }
}
document.addEventListener('DOMContentLoaded', () => {
    const editor = concEl('conc-edicion');
    if (!editor) return;
    editor.addEventListener('input', e => { if (!['radio', 'checkbox'].includes(e.target.type)) marcarCambioConciliacion(); });
    editor.addEventListener('change', e => { if (e.target.name?.startsWith('conc-seleccion-') || e.target.id === 'conc-solo-pendientes') return; marcarCambioConciliacion(); });
    concEl('conc-input-saldo-banco').addEventListener('input', renderComparacionConciliacion);
    window.addEventListener('beforeunload', e => { if (conciliacionModificada) {e.preventDefault(); e.returnValue = '';} });
});
