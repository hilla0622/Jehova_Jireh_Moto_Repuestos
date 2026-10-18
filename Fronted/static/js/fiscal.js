/**
 * ==============================================================================
 *  fiscal.js — Controlador Frontend del Módulo Tributario y Declaración DGI
 *  Sistema Jehová Jireh Moto Repuestos
 *  Implementa: Formulario 106 (VET DGI Nicaragua) y Catálogo de Retenciones
 * ==============================================================================
 */

let fiscalDataActual = null;
let anioFiscalSeleccionado = 2026;
let catalogoRetencionesDGI = [];

document.addEventListener('DOMContentLoaded', () => {
    // Escuchar cambios en selector de año fiscal
    const anioSelect = document.getElementById('fiscal-select-anio');
    if (anioSelect) {
        anioSelect.addEventListener('change', (e) => {
            anioFiscalSeleccionado = parseInt(e.target.value);
            cargarSimulacionFiscal();
        });
    }

    // Auto-cálculo de importe en modal de constancia
    const inputBase = document.getElementById('acred-monto-base');
    const inputPorcentaje = document.getElementById('acred-porcentaje');
    const inputImporte = document.getElementById('acred-importe-total');
    if (inputBase && inputPorcentaje && inputImporte) {
        const recalcularRetencion = () => {
            const base = parseFloat(inputBase.value) || 0;
            const porc = parseFloat(inputPorcentaje.value) || 0;
            if (base > 0 && porc > 0) {
                inputImporte.value = (base * (porc / 100.0)).toFixed(2);
            }
        };
        inputBase.addEventListener('input', recalcularRetencion);
        inputPorcentaje.addEventListener('input', recalcularRetencion);
    }
});

function cargarModuloFiscal() {
    cargarInfoTributaria();
    cargarSimulacionFiscal();
}

async function cargarInfoTributaria() {
    try {
        const res = await fetch('/api/fiscal/info');
        if (!res.ok) throw new Error('Error al consultar configuración tributaria');
        const data = await res.json();
        catalogoRetencionesDGI = data.catalogo_retenciones || [];
        poblarSelectorCatalogoRetenciones();
    } catch (err) {
        console.warn('Nota fiscal info:', err);
    }
}

function poblarSelectorCatalogoRetenciones() {
    const sel = document.getElementById('acred-tipo-codigo');
    if (!sel) return;
    sel.innerHTML = '<option value="">-- Seleccione del Catálogo DGI --</option>';
    catalogoRetencionesDGI.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item.codigo;
        opt.dataset.alicuota = item.alicuota;
        opt.dataset.desc = item.descripcion;
        opt.dataset.tipo = item.codigo === 'ANTICIPO' ? 'ANTICIPO_PAGADO' : (item.codigo === 'SALDO_FAVOR_ANT' ? 'CREDITO_FISCAL' : 'RETENCION_SUFRIDA');
        opt.textContent = `[${item.codigo}] ${item.descripcion.substring(0, 65)}... (${item.alicuota}%)`;
        sel.appendChild(opt);
    });

    sel.addEventListener('change', (e) => {
        const opt = sel.options[sel.selectedIndex];
        if (opt && opt.dataset.alicuota) {
            const inputPorc = document.getElementById('acred-porcentaje');
            const inputTipo = document.getElementById('acred-tipo');
            const inputConc = document.getElementById('acred-concepto');
            if (inputPorc) inputPorc.value = opt.dataset.alicuota;
            if (inputTipo) inputTipo.value = opt.dataset.tipo;
            if (inputConc && !inputConc.value) inputConc.value = opt.dataset.desc;
            
            // Disparar recálculo
            const inputBase = document.getElementById('acred-monto-base');
            if (inputBase && parseFloat(inputBase.value) > 0) {
                const base = parseFloat(inputBase.value);
                const porc = parseFloat(opt.dataset.alicuota);
                const inputImp = document.getElementById('acred-importe-total');
                if (inputImp) inputImp.value = (base * (porc / 100.0)).toFixed(2);
            }
        }
    });
}

function switchFiscalSubtab(tabName, btn) {
    const container = document.getElementById('tab-fiscal');
    if (!container) return;

    container.querySelectorAll('.fiscal-subtab-btn').forEach(b => b.classList.remove('active'));
    container.querySelectorAll('.fiscal-tab-view').forEach(v => v.classList.remove('active'));

    if (btn) btn.classList.add('active');
    const target = document.getElementById(`fiscal-subtab-${tabName}`);
    if (target) target.classList.add('active');

    if (tabName === 'acreditamientos') cargarAcreditamientosFiscales();
    if (tabName === 'historial') cargarHistorialFiscal();
}

async function cargarSimulacionFiscal() {
    const anioSelect = document.getElementById('fiscal-select-anio');
    const anio = anioSelect ? anioSelect.value : anioFiscalSeleccionado;
    anioFiscalSeleccionado = parseInt(anio);

    const bannerLoading = document.getElementById('fiscal-loading-state');
    if (bannerLoading) bannerLoading.style.display = 'block';

    try {
        const res = await fetch(`/api/fiscal/simulacion/${anioFiscalSeleccionado}`);
        if (!res.ok) throw new Error('Error al generar simulación contable DGI.');
        const data = await res.json();
        fiscalDataActual = data;
        renderizarFormulario106(data);
    } catch (err) {
        mostrarNotificacion(`Error fiscal: ${err.message}`, 'error');
    } finally {
        if (bannerLoading) bannerLoading.style.display = 'none';
    }
}

function renderizarFormulario106(sim) {
    const n = sim.negocio || {};
    const bal = sim.balance || {};
    const res = sim.resultados || {};
    const calc = sim.calculo_ir || {};
    const liq = sim.liquidacion || {};

    // 1. Datos Generales (Header VET y Sección A)
    const setT = (id, val) => {
        const el = document.getElementById(id);
        if (el) el.textContent = val;
    };

    setT('vet-empresa-ruc', n.ruc || 'J0310000000001');
    setT('vet-empresa-razon', n.razon_social || 'Jehová Jireh Moto Repuestos y Servicios');
    setT('vet-empresa-actividad', n.actividad_economica || 'Venta de repuestos y taller');
    setT('vet-periodo-fiscal', `12 / ${sim.anio}`);
    setT('vet-no-declaracion', `IR106-${sim.anio}-SIM`);

    // 2. Sección B: Balance General (Renglones 1..23)
    const tbodyBalance = document.getElementById('vet-tbody-balance');
    if (tbodyBalance && bal.renglones) {
        tbodyBalance.innerHTML = '';
        bal.renglones.forEach(r => {
            const tr = document.createElement('tr');
            if (r.destacado) tr.classList.add('row-highlight-total');
            tr.innerHTML = `
                <td style="text-align: center; font-weight: bold; width: 60px;">${r.renglon}</td>
                <td style="font-weight: ${r.destacado ? 'bold' : 'normal'};">${r.descripcion}</td>
                <td style="text-align: right; font-weight: bold; font-family: monospace;">
                    C$ ${parseFloat(r.importe || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </td>
                <td style="text-align: center; color: var(--text-muted); font-size: 0.8rem;">
                    ${r.cuentas ? `<span class="badge badge-sm badge-secondary">${r.cuentas}</span>` : '—'}
                </td>
            `;
            tbodyBalance.appendChild(tr);
        });
    }

    // Alerta de cuadre
    const alertaCuadre = document.getElementById('vet-alerta-cuadre');
    if (alertaCuadre) {
        if (bal.balance_cuadrado) {
            alertaCuadre.className = 'alert-cuadre alert-success';
            alertaCuadre.innerHTML = `<i class="ph-bold ph-check-circle"></i> Balance General debidamente cuadrado. Total Activos: <strong>C$ ${bal.total_activos.toLocaleString('en-US', {minimumFractionDigits: 2})}</strong> = Pasivo + Patrimonio: <strong>C$ ${(bal.total_pasivos + bal.patrimonio_total).toLocaleString('en-US', {minimumFractionDigits: 2})}</strong>`;
        } else {
            alertaCuadre.className = 'alert-cuadre alert-warning';
            alertaCuadre.innerHTML = `<i class="ph-bold ph-warning"></i> Advertencia de cuadre contable: Diferencia de C$ ${bal.diferencia_cuadre.toLocaleString('en-US', {minimumFractionDigits: 2})}. Activos: C$ ${bal.total_activos.toLocaleString('en-US', {minimumFractionDigits: 2})} vs Pasivo+Patrimonio: C$ ${(bal.total_pasivos + bal.patrimonio_total).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
        }
    }

    // 3. Sección D: Estado de Resultados
    const tbodyResultados = document.getElementById('vet-tbody-resultados');
    if (tbodyResultados && res.renglones) {
        tbodyResultados.innerHTML = '';
        res.renglones.forEach(r => {
            const tr = document.createElement('tr');
            if (r.destacado) tr.classList.add('row-highlight-total');
            tr.innerHTML = `
                <td style="text-align: center; font-weight: bold; width: 60px;">${r.renglon}</td>
                <td style="font-weight: ${r.destacado ? 'bold' : 'normal'};">${r.descripcion}</td>
                <td style="text-align: right; font-weight: bold; font-family: monospace;">
                    C$ ${parseFloat(r.importe || 0).toLocaleString('en-US', {minimumFractionDigits: 2, maximumFractionDigits: 2})}
                </td>
                <td style="text-align: center; color: var(--text-muted); font-size: 0.8rem;">
                    ${r.cuentas ? `<span class="badge badge-sm badge-secondary">${r.cuentas}</span>` : '—'}
                </td>
            `;
            tbodyResultados.appendChild(tr);
        });
    }

    // 4. Sección E: Cálculo del IR (Cards comparativas y método)
    setT('kpi-renta-gravable', `C$ ${parseFloat(calc.renta_neta_gravable || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`);
    setT('kpi-ir-30', `C$ ${parseFloat(calc.ir_calculado_30 || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`);
    setT('kpi-pmd-1', `C$ ${parseFloat(calc.pmd_calculado_1 || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`);
    setT('kpi-ir-determinado', `C$ ${parseFloat(calc.ir_determinado || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`);
    setT('badge-metodo-aplicado', calc.metodo_aplicado || 'IR 30%');

    // 5. Sección F: Liquidación del Impuesto
    setT('liq-ir-determinado', `C$ ${parseFloat(liq.ir_determinado || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`);
    setT('liq-anticipos', `- C$ ${parseFloat(liq.anticipos_mensuales || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`);
    setT('liq-retenciones', `- C$ ${parseFloat(liq.retenciones_sufridas || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`);
    setT('liq-creditos', `- C$ ${parseFloat(liq.creditos_fiscales_ant || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`);
    setT('liq-total-acred', `C$ ${parseFloat(liq.total_acreditamientos || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}`);

    const badgeSaldo = document.getElementById('liq-saldo-final-badge');
    const valorSaldo = document.getElementById('liq-saldo-final-valor');
    if (liq.saldo_a_pagar > 0) {
        if (badgeSaldo) {
            badgeSaldo.textContent = 'SALDO A PAGAR A LA DGI';
            badgeSaldo.className = 'badge-fiscal-status badge-pagar';
        }
        if (valorSaldo) {
            valorSaldo.textContent = `C$ ${parseFloat(liq.saldo_a_pagar).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
            valorSaldo.style.color = '#dc2626';
        }
    } else {
        if (badgeSaldo) {
            badgeSaldo.textContent = 'SALDO A FAVOR DEL CONTRIBUYENTE';
            badgeSaldo.className = 'badge-fiscal-status badge-favor';
        }
        if (valorSaldo) {
            valorSaldo.textContent = `C$ ${parseFloat(liq.saldo_a_favor).toLocaleString('en-US', {minimumFractionDigits: 2})}`;
            valorSaldo.style.color = '#16a34a';
        }
    }
}

async function cargarAcreditamientosFiscales() {
    const tbody = document.getElementById('tbody-acreditamientos');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted">Cargando constancias de retención...</td></tr>';

    try {
        const res = await fetch(`/api/fiscal/acreditamientos?anio=${anioFiscalSeleccionado}`);
        if (!res.ok) throw new Error('Error al cargar acreditamientos.');
        const filas = await res.json();
        
        if (!filas.length) {
            tbody.innerHTML = '<tr><td colspan="8" class="text-center text-muted" style="padding: 2rem;">No hay constancias de retención ni anticipos registrados para este ejercicio fiscal. Presione "+ Registrar Constancia" para agregar una.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        filas.forEach(f => {
            const tr = document.createElement('tr');
            const badgeTipo = f.tipo === 'RETENCION_SUFRIDA' ? 'badge-primary' : (f.tipo === 'ANTICIPO_PAGADO' ? 'badge-success' : 'badge-warning');
            const descTipo = f.tipo === 'RETENCION_SUFRIDA' ? 'Retención Sufrida' : (f.tipo === 'ANTICIPO_PAGADO' ? 'Anticipo 1%' : 'Crédito Fiscal');

            tr.innerHTML = `
                <td><span class="badge ${badgeTipo}">${descTipo}</span></td>
                <td><strong>${f.numero_referencia}</strong></td>
                <td>${f.fecha}</td>
                <td>${f.agente_retenedor_nombre || f.agente_retenedor_ruc || 'N/A'}</td>
                <td style="text-align: right; font-family: monospace;">C$ ${f.monto_base.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                <td style="text-align: center;">${f.porcentaje_aplicado > 0 ? f.porcentaje_aplicado + '%' : '—'}</td>
                <td style="text-align: right; font-weight: bold; font-family: monospace; color: var(--accent-green);">
                    C$ ${f.importe_total.toLocaleString('en-US', {minimumFractionDigits: 2})}
                </td>
                <td style="text-align: center;">
                    ${f.estado !== 'Aplicado Total' ? `
                    <button class="btn btn-outline btn-sm text-danger" onclick="eliminarAcreditamientoFiscal(${f.id})" title="Eliminar constancia">
                        <i class="ph-bold ph-trash"></i>
                    </button>
                    ` : '<span class="badge badge-sm badge-secondary">Aplicada</span>'}
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="8" class="text-danger text-center">${err.message}</td></tr>`;
    }
}

function abrirModalAcreditamiento() {
    const anioInput = document.getElementById('acred-anio');
    if (anioInput) anioInput.value = anioFiscalSeleccionado;
    openModal('modal-acreditamiento');
}

async function guardarAcreditamientoFiscal(e) {
    e.preventDefault();
    const payload = {
        tipo: document.getElementById('acred-tipo').value,
        concepto: document.getElementById('acred-concepto').value,
        ejercicio_fiscal: parseInt(document.getElementById('acred-anio').value) || anioFiscalSeleccionado,
        periodo_mes: parseInt(document.getElementById('acred-mes').value) || 1,
        fecha: document.getElementById('acred-fecha').value,
        numero_referencia: document.getElementById('acred-referencia').value,
        agente_retenedor_ruc: document.getElementById('acred-agente-ruc').value,
        agente_retenedor_nombre: document.getElementById('acred-agente-nombre').value,
        monto_base: parseFloat(document.getElementById('acred-monto-base').value) || 0,
        porcentaje_aplicado: parseFloat(document.getElementById('acred-porcentaje').value) || 0,
        importe_total: parseFloat(document.getElementById('acred-importe-total').value) || 0
    };

    try {
        const res = await fetch('/api/fiscal/acreditamientos', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al guardar constancia');

        mostrarNotificacion('Constancia de retención registrada exitosamente.', 'success');
        closeModal('modal-acreditamiento');
        document.getElementById('form-acreditamiento').reset();
        cargarAcreditamientosFiscales();
        cargarSimulacionFiscal(); // Refrescar liquidación
    } catch (err) {
        mostrarNotificacion(err.message, 'error');
    }
}

async function eliminarAcreditamientoFiscal(id) {
    if (!confirm('¿Desea eliminar esta constancia de retención?')) return;
    try {
        const res = await fetch(`/api/fiscal/acreditamientos/${id}`, {method: 'DELETE'});
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al eliminar');
        mostrarNotificacion('Constancia eliminada.', 'success');
        cargarAcreditamientosFiscales();
        cargarSimulacionFiscal();
    } catch (err) {
        mostrarNotificacion(err.message, 'error');
    }
}

function abrirModalAjusteFiscal() {
    const anioInput = document.getElementById('ajuste-anio');
    if (anioInput) anioInput.value = anioFiscalSeleccionado;
    openModal('modal-ajuste-fiscal');
}

async function guardarAjusteFiscal(e) {
    e.preventDefault();
    const payload = {
        ejercicio_fiscal: parseInt(document.getElementById('ajuste-anio').value) || anioFiscalSeleccionado,
        concepto: document.getElementById('ajuste-concepto').value,
        tipo_ajuste: document.getElementById('ajuste-tipo').value,
        efecto: document.getElementById('ajuste-efecto').value,
        importe: parseFloat(document.getElementById('ajuste-importe').value) || 0,
        referencia_normativa: document.getElementById('ajuste-normativa').value,
        justificacion: document.getElementById('ajuste-justificacion').value
    };

    try {
        const res = await fetch('/api/fiscal/ajustes', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al guardar ajuste');

        mostrarNotificacion('Ajuste fiscal registrado con éxito.', 'success');
        closeModal('modal-ajuste-fiscal');
        document.getElementById('form-ajuste-fiscal').reset();
        cargarSimulacionFiscal();
    } catch (err) {
        mostrarNotificacion(err.message, 'error');
    }
}

async function guardarDeclaracionFiscal(esAprobada) {
    const confirmMsg = esAprobada
        ? `¿Confirmar APROBACIÓN de la Declaración Anual IR ${anioFiscalSeleccionado}? Esta acción aplicará las constancias de retención.`
        : `¿Guardar BORRADOR de la Declaración Anual IR ${anioFiscalSeleccionado}?`;
    
    if (!confirm(confirmMsg)) return;

    try {
        const res = await fetch('/api/fiscal/declaracion/guardar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                anio: anioFiscalSeleccionado,
                aprobar: esAprobada
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al guardar');

        mostrarNotificacion(data.mensaje, 'success');
        cargarSimulacionFiscal();
        cargarHistorialFiscal();
    } catch (err) {
        mostrarNotificacion(err.message, 'error');
    }
}

async function cargarHistorialFiscal() {
    const tbody = document.getElementById('tbody-historial-fiscal');
    if (!tbody) return;
    tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">Cargando historial de declaraciones...</td></tr>';

    try {
        const res = await fetch('/api/fiscal/declaraciones');
        if (!res.ok) throw new Error('Error al consultar historial.');
        const decls = await res.json();
        if (!decls.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted" style="padding: 2rem;">No hay declaraciones anuales guardadas aún en el sistema.</td></tr>';
            return;
        }

        tbody.innerHTML = '';
        decls.forEach(d => {
            const tr = document.createElement('tr');
            const badgeEstado = d.estado === 'Presentada' ? 'badge-success' : (d.estado === 'Aprobada' ? 'badge-primary' : 'badge-warning');
            tr.innerHTML = `
                <td><strong>IR-${d.ejercicio_fiscal} (v${d.version})</strong></td>
                <td>${d.fecha_creacion}</td>
                <td><span class="badge ${badgeEstado}">${d.estado}</span></td>
                <td style="text-align: right; font-family: monospace;">C$ ${d.ir_determinado.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                <td style="text-align: right; font-family: monospace;">C$ ${d.acreditamientos.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                <td style="text-align: right; font-weight: bold; font-family: monospace; color: ${d.saldo_a_pagar > 0 ? '#dc2626' : '#16a34a'};">
                    C$ ${(d.saldo_a_pagar > 0 ? d.saldo_a_pagar : d.saldo_a_favor).toLocaleString('en-US', {minimumFractionDigits: 2})}
                    <small>(${d.saldo_a_pagar > 0 ? 'A Pagar' : 'A Favor'})</small>
                </td>
                <td style="text-align: center;">
                    ${d.estado === 'Aprobada' ? `
                    <button class="btn btn-outline btn-sm" onclick="abrirModalPresentacionDGI(${d.id}, ${d.saldo_a_pagar})" title="Registrar Presentación / Pago DGI">
                        <i class="ph-bold ph-paper-plane-tilt"></i> Registrar Presentación
                    </button>
                    ` : ''}
                    <button class="btn btn-secondary btn-sm" onclick="imprimirFormulario106(${d.id})" title="Imprimir Formulario 106">
                        <i class="ph-bold ph-printer"></i> Imprimir VET
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (err) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-danger text-center">${err.message}</td></tr>`;
    }
}

function abrirModalPresentacionDGI(declId, saldo) {
    document.getElementById('pres-decl-id').value = declId;
    document.getElementById('pres-monto').value = saldo > 0 ? saldo.toFixed(2) : '0.00';
    openModal('modal-presentacion-dgi');
}

async function guardarPresentacionDGI(e) {
    e.preventDefault();
    const payload = {
        declaracion_id: document.getElementById('pres-decl-id').value,
        numero_referencia_dgi: document.getElementById('pres-referencia').value,
        fecha_evento: document.getElementById('pres-fecha').value,
        importe_pagado: parseFloat(document.getElementById('pres-monto').value) || 0,
        banco_caja: document.getElementById('pres-banco').value,
        medio_pago: document.getElementById('pres-medio-pago').value,
        observaciones: document.getElementById('pres-observaciones').value
    };

    try {
        const res = await fetch('/api/fiscal/declaracion/presentar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error al registrar presentación');

        mostrarNotificacion('Constancia de presentación DGI registrada exitosamente.', 'success');
        closeModal('modal-presentacion-dgi');
        cargarHistorialFiscal();
        cargarSimulacionFiscal();
    } catch (err) {
        mostrarNotificacion(err.message, 'error');
    }
}

function imprimirFormulario106() {
    if (!fiscalDataActual) {
        mostrarNotificacion('Primero cargue la simulación fiscal.', 'warning');
        return;
    }

    const printWin = window.open('', '_blank', 'width=950,height=800');
    const sim = fiscalDataActual;
    const n = sim.negocio || {};
    const bal = sim.balance || {};
    const res = sim.resultados || {};
    const calc = sim.calculo_ir || {};
    const liq = sim.liquidacion || {};

    let htmlBalanceRows = '';
    (bal.renglones || []).forEach(r => {
        htmlBalanceRows += `
            <tr style="${r.destacado ? 'font-weight: bold; background: #e2e8f0;' : ''}">
                <td style="text-align: center; border: 1px solid #cbd5e1; padding: 4px;">${r.renglon}</td>
                <td style="border: 1px solid #cbd5e1; padding: 4px;">${r.descripcion}</td>
                <td style="text-align: right; border: 1px solid #cbd5e1; padding: 4px; font-family: monospace;">C$ ${parseFloat(r.importe || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
            </tr>
        `;
    });

    let htmlResultadosRows = '';
    (res.renglones || []).forEach(r => {
        htmlResultadosRows += `
            <tr style="${r.destacado ? 'font-weight: bold; background: #e2e8f0;' : ''}">
                <td style="text-align: center; border: 1px solid #cbd5e1; padding: 4px;">${r.renglon}</td>
                <td style="border: 1px solid #cbd5e1; padding: 4px;">${r.descripcion}</td>
                <td style="text-align: right; border: 1px solid #cbd5e1; padding: 4px; font-family: monospace;">C$ ${parseFloat(r.importe || 0).toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
            </tr>
        `;
    });

    const docContent = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Declaración Anual IR Formulario 106 - ${n.razon_social}</title>
            <style>
                body { font-family: Arial, sans-serif; font-size: 11px; margin: 15mm; color: #0f172a; }
                .vet-header { border: 2px solid #0284c7; padding: 12px; margin-bottom: 12px; background: #f0f9ff; }
                .vet-title { font-size: 15px; font-weight: bold; color: #0369a1; text-align: center; margin: 6px 0; }
                .sec-title { background: #0369a1; color: white; padding: 4px 8px; font-weight: bold; font-size: 11px; margin-top: 12px; }
                table { width: 100%; border-collapse: collapse; font-size: 10px; margin-top: 4px; }
                .kpi-box { display: flex; justify-content: space-between; border: 1px solid #cbd5e1; padding: 8px; margin-top: 6px; }
                .kpi-item { text-align: center; flex: 1; }
                @media print { .no-print { display: none; } }
            </style>
        </head>
        <body>
            <div class="no-print" style="margin-bottom: 15px; text-align: right;">
                <button onclick="window.print()" style="padding: 8px 16px; background: #0284c7; color: white; border: none; border-radius: 4px; cursor: pointer; font-weight: bold;">Imprimir Formulario</button>
            </div>
            
            <div class="vet-header">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <div style="font-weight: bold; color: #0369a1; font-size: 12px;">Gobierno de Reconciliación y Unidad Nacional</div>
                        <div style="color: #64748b; font-size: 10px;">Dirección General de Ingresos (DGI) - Nicaragua</div>
                        <div style="font-weight: bold; color: #0284c7;">Ventanilla Electrónica Tributaria (VET)</div>
                    </div>
                    <div style="text-align: right;">
                        <div style="font-size: 18px; font-weight: bold; color: #0369a1;">106</div>
                        <div style="font-weight: bold;">DECLARACIÓN ANUAL DEL IR</div>
                        <div style="font-size: 10px;">Ejercicio Fiscal: <strong>${sim.anio}</strong></div>
                    </div>
                </div>
            </div>

            <div class="sec-title">A. DATOS GENERALES</div>
            <table style="margin-bottom: 10px;">
                <tr>
                    <td style="width: 25%; font-weight: bold; border: 1px solid #cbd5e1; padding: 4px; background: #f8fafc;">RUC:</td>
                    <td style="border: 1px solid #cbd5e1; padding: 4px;">${n.ruc}</td>
                    <td style="width: 25%; font-weight: bold; border: 1px solid #cbd5e1; padding: 4px; background: #f8fafc;">Régimen:</td>
                    <td style="border: 1px solid #cbd5e1; padding: 4px;">${n.regimen_tributario}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; border: 1px solid #cbd5e1; padding: 4px; background: #f8fafc;">Razón Social:</td>
                    <td colspan="3" style="border: 1px solid #cbd5e1; padding: 4px;">${n.razon_social}</td>
                </tr>
                <tr>
                    <td style="font-weight: bold; border: 1px solid #cbd5e1; padding: 4px; background: #f8fafc;">Actividad Económica:</td>
                    <td colspan="3" style="border: 1px solid #cbd5e1; padding: 4px;">${n.actividad_economica}</td>
                </tr>
            </table>

            <div class="sec-title">B. BALANCE GENERAL</div>
            <table>
                <thead>
                    <tr style="background: #f1f5f9;">
                        <th style="border: 1px solid #cbd5e1; padding: 4px; width: 40px;">Renglón</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4px; text-align: left;">Descripción del Rubro</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4px; text-align: right; width: 140px;">Importe (C$)</th>
                    </tr>
                </thead>
                <tbody>
                    ${htmlBalanceRows}
                </tbody>
            </table>

            <div class="sec-title">D. ESTADO DE RESULTADOS</div>
            <table>
                <thead>
                    <tr style="background: #f1f5f9;">
                        <th style="border: 1px solid #cbd5e1; padding: 4px; width: 40px;">Renglón</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4px; text-align: left;">Descripción del Rubro</th>
                        <th style="border: 1px solid #cbd5e1; padding: 4px; text-align: right; width: 140px;">Importe (C$)</th>
                    </tr>
                </thead>
                <tbody>
                    ${htmlResultadosRows}
                </tbody>
            </table>

            <div class="sec-title">E. CÁLCULO DEL IR Y CONCILIACIÓN FISCAL</div>
            <div class="kpi-box">
                <div class="kpi-item">
                    <div>Renta Neta Gravable</div>
                    <strong style="font-size: 13px;">C$ ${calc.renta_neta_gravable.toLocaleString('en-US', {minimumFractionDigits: 2})}</strong>
                </div>
                <div class="kpi-item">
                    <div>IR 30% (Act. Económicas)</div>
                    <strong style="font-size: 13px;">C$ ${calc.ir_calculado_30.toLocaleString('en-US', {minimumFractionDigits: 2})}</strong>
                </div>
                <div class="kpi-item">
                    <div>PMD 1% (Ingresos Brutos)</div>
                    <strong style="font-size: 13px;">C$ ${calc.pmd_calculado_1.toLocaleString('en-US', {minimumFractionDigits: 2})}</strong>
                </div>
                <div class="kpi-item" style="border-left: 2px solid #0369a1; background: #e0f2fe;">
                    <div>IR Determinado (${calc.metodo_aplicado})</div>
                    <strong style="font-size: 14px; color: #0369a1;">C$ ${calc.ir_determinado.toLocaleString('en-US', {minimumFractionDigits: 2})}</strong>
                </div>
            </div>

            <div class="sec-title">F. LIQUIDACIÓN DEL IMPUESTO</div>
            <table>
                <tr>
                    <td style="border: 1px solid #cbd5e1; padding: 5px;">IR Determinado del Ejercicio Fiscal</td>
                    <td style="border: 1px solid #cbd5e1; padding: 5px; text-align: right; font-weight: bold; width: 140px;">C$ ${liq.ir_determinado.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #cbd5e1; padding: 5px;">(-) Anticipos Mensuales Pagados del 1% (Ley 822 Art. 61)</td>
                    <td style="border: 1px solid #cbd5e1; padding: 5px; text-align: right; color: #16a34a;">- C$ ${liq.anticipos_mensuales.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                </tr>
                <tr>
                    <td style="border: 1px solid #cbd5e1; padding: 5px;">(-) Retenciones en la Fuente que le practicaron (Retenciones Sufridas)</td>
                    <td style="border: 1px solid #cbd5e1; padding: 5px; text-align: right; color: #16a34a;">- C$ ${liq.retenciones_sufridas.toLocaleString('en-US', {minimumFractionDigits: 2})}</td>
                </tr>
                <tr style="background: #f8fafc; font-weight: bold; font-size: 12px;">
                    <td style="border: 1px solid #cbd5e1; padding: 7px;">${liq.saldo_a_pagar > 0 ? 'SALDO A PAGAR A LA DGI' : 'SALDO A FAVOR DEL CONTRIBUYENTE'}</td>
                    <td style="border: 1px solid #cbd5e1; padding: 7px; text-align: right; color: ${liq.saldo_a_pagar > 0 ? '#dc2626' : '#16a34a'};">
                        C$ ${(liq.saldo_a_pagar > 0 ? liq.saldo_a_pagar : liq.saldo_a_favor).toLocaleString('en-US', {minimumFractionDigits: 2})}
                    </td>
                </tr>
            </table>

            <div style="margin-top: 25px; display: flex; justify-content: space-around; text-align: center;">
                <div style="width: 200px; border-top: 1px solid #0f172a; padding-top: 4px;">
                    Elaborado por (Contador)
                </div>
                <div style="width: 200px; border-top: 1px solid #0f172a; padding-top: 4px;">
                    Aprobado por (Gerencia)
                </div>
            </div>

            <div style="margin-top: 15px; font-size: 9px; color: #94a3b8; text-align: center;">
                Comprobante de Simulación emitido por Jehová Jireh Moto Repuestos • Plataforma Fiscal Conforme Ley 822 Nicaragua
            </div>
        </body>
        </html>
    `;

    printWin.document.open();
    printWin.document.write(docContent);
    printWin.document.close();
}
