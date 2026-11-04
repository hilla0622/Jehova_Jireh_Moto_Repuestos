/* Asistente IR: presenta únicamente el informe reconstruido por el servidor. */
let revisionIR = 0;
let solicitudIR = null;

function reiniciarAnalisisIR() {
    revisionIR++;
    if (solicitudIR) solicitudIR.abort();
    solicitudIR = null;
    const contenido = document.getElementById('ir-insight-content');
    const estado = document.getElementById('ir-insight-status');
    const boton = document.getElementById('ir-insight-generate');
    const periodo = document.getElementById('ir-insight-period');
    if (!contenido || !estado || !boton || !periodo) return;
    contenido.hidden = true;
    contenido.innerHTML = '';
    contenido.setAttribute('aria-busy', 'false');
    estado.hidden = false;
    estado.classList.remove('is-error');
    estado.textContent = 'Genera el informe para interpretar la información del ejercicio seleccionado.';
    periodo.textContent = `Ejercicio ${anioFiscalSeleccionado}`;
    boton.disabled = false;
    boton.innerHTML = '<i class="ph-bold ph-sparkle" aria-hidden="true"></i> Analizar ejercicio';
}

function renderizarAnalisisIR(informe) {
    const e = typeof escaparFiscal === 'function' ? escaparFiscal : (v => String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])));
    const dinero = n => new Intl.NumberFormat('es-NI', {style: 'currency', currency: 'NIO', maximumFractionDigits: 2}).format(n ?? 0);
    const fecha = f => f ? f.split('-').reverse().join('/') : '';
    const comparacion = informe.comparacion_disponible;
    const parrafos = informe.interpretacion_ia
        ? informe.interpretacion_ia.split(/\n\s*\n/).filter(p => p.trim())
        : (informe.parrafos?.length ? informe.parrafos : [informe.resumen]);
    return `${informe.datos_demostracion || informe.anterior_demostracion ? '<p class="ir-insight-notice">Datos de demostración en el ejercicio o en su comparación. Sin validez oficial.</p>' : ''}
        <article class="ir-insight-report" aria-label="Interpretación del ejercicio">
            <span class="ir-insight-label">${informe.modo === 'ia' ? 'INTERPRETACIÓN CON IA' : 'INFORME CONTABLE'}</span>
            ${parrafos.map(p => `<p class="ir-insight-narrative">${e(p)}</p>`).join('')}
        </article>
        <p class="ir-insight-provider">${e(informe.aviso_ia)}</p>
        ${comparacion ? `<details><summary>Consultar cifras de la comparación</summary><p class="ir-insight-provider">Hasta ${e(fecha(informe.fecha_corte))} frente a ${e(fecha(informe.corte_anterior))}.</p><div class="ir-insight-table-wrap"><table><thead><tr><th scope="col">Concepto</th><th scope="col">Actual</th><th scope="col">Anterior</th><th scope="col">Diferencia</th></tr></thead><tbody>${informe.metricas.map(m => `<tr><th scope="row">${e(m.titulo)}</th><td>${e(dinero(m.actual))}</td><td>${e(dinero(m.anterior))}</td><td>${e(dinero(m.diferencia))}</td></tr>`).join('')}</tbody></table></div></details>` : ''}
        ${informe.observaciones.length ? `<details><summary>Consultar registros y observaciones de respaldo (${informe.observaciones.length})</summary>${informe.observaciones.map(o => `<div class="ir-insight-source"><p><strong>${e(o.titulo)}.</strong> ${e(o.detalle)}</p><small>${e(o.fuente)}</small><button type="button" class="ir-insight-link" data-ir-destino="${e(o.destino)}">Revisar ${o.destino === 'acreditamientos' ? 'acreditamientos' : 'formulario'} →</button></div>`).join('')}</details>` : ''}`;
}

async function generarAnalisisIR() {
    if (solicitudIR) return;
    const contenido = document.getElementById('ir-insight-content');
    const estado = document.getElementById('ir-insight-status');
    const boton = document.getElementById('ir-insight-generate');
    const revision = ++revisionIR;
    const anio = anioFiscalSeleccionado;
    solicitudIR = new AbortController();
    boton.disabled = true;
    boton.textContent = 'Analizando ejercicio…';
    contenido.hidden = true;
    estado.hidden = false;
    estado.classList.remove('is-error');
    estado.textContent = 'Consultando Contabilidad y preparando la interpretación del ejercicio…';
    contenido.setAttribute('aria-busy', 'true');
    try {
        const res = await fetch(`/api/fiscal/analisis/${anio}`, {method: 'POST', signal: solicitudIR.signal});
        const informe = await res.json();
        if (!res.ok) throw new Error(informe.error || 'No se pudo generar el análisis.');
        if (revision !== revisionIR || anio !== anioFiscalSeleccionado) return;
        contenido.innerHTML = renderizarAnalisisIR(informe);
        contenido.hidden = false;
        estado.textContent = 'Informe generado para el ejercicio seleccionado.';
        estado.hidden = true;
        document.getElementById('ir-insight-period').textContent = `Ejercicio ${anio} · Corte ${informe.fecha_corte.split('-').reverse().join('/')}`;
    } catch (error) {
        if (revision !== revisionIR || error.name === 'AbortError') return;
        estado.classList.add('is-error');
        estado.textContent = error.message || 'No se pudo generar el análisis. Vuelve a intentar.';
    } finally {
        if (revision === revisionIR) {
            solicitudIR = null;
            boton.disabled = false;
            boton.innerHTML = '<i class="ph-bold ph-arrows-clockwise" aria-hidden="true"></i> Volver a analizar';
            contenido.setAttribute('aria-busy', 'false');
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    reiniciarAnalisisIR();
    document.getElementById('ir-insight-content')?.addEventListener('click', event => {
        const boton = event.target.closest('[data-ir-destino]');
        if (!boton) return;
        const destino = boton.dataset.irDestino;
        if (!['vet', 'acreditamientos'].includes(destino)) return;
        const tab = Array.from(document.querySelectorAll('.dgi-nav-tab-btn')).find(b =>
            b.getAttribute('onclick')?.includes(`'${destino}'`));
        switchFiscalTab(destino, tab);
        document.getElementById(`fiscal-view-${destino}`)?.scrollIntoView({behavior: 'smooth', block: 'start'});
    });
});
