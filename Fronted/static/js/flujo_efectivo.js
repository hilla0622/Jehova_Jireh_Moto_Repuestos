// ==============================================================================
// MÓDULO DE ESTADOS FINANCIEROS: ESTADO DE FLUJO DE EFECTIVO Y CONCILIACIÓN
// Marco Técnico: NIIF para PYMES Sección 7 / NIC 7 (RF96 - RF102, RF46)
// Sistema Jehová Jireh Moto Repuestos
// ==============================================================================

let metodoFlujoActual = 'Directo';
let flujoActualData = null;
let partidasEnTransito = [];
let conciliacionActualData = null;

// Formateador de moneda en Córdobas (C$)
function formatCordoba(val) {
    const num = parseFloat(val || 0);
    const sign = num < 0 ? '-' : '';
    const absVal = Math.abs(num);
    return `${sign}C$ ${absVal.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// -----------------------------------------------------------------------------
// 1. GENERACIÓN Y RENDERIZADO DEL ESTADO DE FLUJO DE EFECTIVO
// -----------------------------------------------------------------------------
function cambiarMetodoFlujo(metodo) {
    metodoFlujoActual = metodo;
    const btnDir = document.getElementById('btn-flujo-directo');
    const btnInd = document.getElementById('btn-flujo-indirecto');
    
    if (btnDir && btnInd) {
        if (metodo === 'Directo') {
            btnDir.className = 'btn btn-sm btn-primary';
            btnInd.className = 'btn btn-sm btn-outline';
            btnInd.style.color = 'white';
            btnInd.style.borderColor = 'rgba(255,255,255,0.3)';
        } else {
            btnInd.className = 'btn btn-sm btn-primary';
            btnDir.className = 'btn btn-sm btn-outline';
            btnDir.style.color = 'white';
            btnDir.style.borderColor = 'rgba(255,255,255,0.3)';
        }
    }
    loadFlujoEfectivo(metodo);
}

async function loadFlujoEfectivo(metodo = null) {
    if (!metodo) metodo = metodoFlujoActual;
    const container = document.getElementById('reporte-flujo-efectivo');
    if (!container) return;

    try {
        const finIni = document.getElementById('fin-fecha-inicio');
        const finFin = document.getElementById('fin-fecha-fin');
        const start = finIni ? finIni.value : '';
        const end = finFin ? finFin.value : '';

        let url = `/api/finanzas/flujo_efectivo?metodo=${metodo}`;
        if (start) url += `&start=${start}`;
        if (end) url += `&end=${end}`;

        container.innerHTML = `
            <div style="text-align: center; padding: 2.5rem; color: var(--text-muted);">
                <i class="ph-bold ph-spinner ph-spin" style="font-size: 2.5rem; color: #10b981;"></i>
                <p style="margin-top: 0.75rem; font-weight: 500;">Generando Estado de Flujos de Efectivo (${metodo})...</p>
            </div>
        `;

        const resp = await fetch(url);
        const data = await resp.json();

        if (data.error) {
            container.innerHTML = `<div class="alert alert-danger" style="padding: 1rem; color: #ef4444; background: rgba(239, 68, 68, 0.1); border-radius: 6px;">${data.error}</div>`;
            return;
        }

        flujoActualData = data;
        renderFlujoEfectivoHTML(data, container);

    } catch (e) {
        console.error("Error al cargar flujo de efectivo:", e);
        container.innerHTML = `<div class="alert alert-danger" style="padding: 1rem; color: #ef4444;">Error de conexión al cargar estado de flujo.</div>`;
    }
}

function renderFlujoEfectivoHTML(data, container) {
    let subtituloPeriodo = "A la fecha actual";
    if (data.periodo.start && data.periodo.start !== "Inicio" && data.periodo.end) {
        subtituloPeriodo = `Del ${data.periodo.start} al ${data.periodo.end}`;
    } else if (data.periodo.end) {
        subtituloPeriodo = `Al ${data.periodo.end}`;
    }

    let html = `
        <div style="max-width: 950px; margin: 0 auto; background: var(--bg-color); padding: 2.5rem; border-radius: 10px; box-shadow: 0 8px 20px rgba(0,0,0,0.06); border: 1px solid var(--border-color);">
            <!-- MEMBRETE COMERCIAL OFICIAL -->
            <div style="text-align: center; border-bottom: 2px solid #059669; padding-bottom: 1.25rem; margin-bottom: 2rem;">
                <h2 style="margin: 0; font-size: 1.6rem; letter-spacing: 0.5px; color: var(--text-color); font-weight: 800;">
                    JEHOVÁ JIREH MOTO REPUESTOS
                </h2>
                <h4 style="margin: 0.35rem 0 0 0; color: #059669; font-size: 1.2rem; font-weight: 700; text-transform: uppercase;">
                    Estado de Flujos de Efectivo (${data.metodo})
                </h4>
                <div style="font-size: 0.88rem; color: var(--text-muted); margin-top: 0.25rem;">
                    Norma Internacional: NIIF para PYMES (Sección 7) / NIC 7 &bull; ${subtituloPeriodo}
                </div>
                <div style="font-size: 0.8rem; color: var(--text-muted); font-weight: 600; margin-top: 0.25rem;">
                    Expresado en Córdobas (C$) &bull; RUC: 0012508820003U
                </div>
            </div>

            <table style="width: 100%; border-collapse: collapse; font-size: 0.93rem;">
                <tbody>
    `;

    // -------------------------------------------------------------------------
    // A. ACTIVIDADES DE OPERACIÓN
    // -------------------------------------------------------------------------
    html += `
        <tr style="background: rgba(5, 150, 105, 0.08);">
            <td colspan="2" style="font-weight: 800; font-size: 1.05rem; padding: 0.65rem 0.75rem; color: #047857; border-left: 4px solid #059669;">
                1. ACTIVIDADES DE OPERACIÓN
            </td>
        </tr>
    `;

    if (data.metodo === 'Directo') {
        if (data.actividades_operacion && data.actividades_operacion.length > 0) {
            data.actividades_operacion.forEach(item => {
                const esEntrada = item.importe >= 0;
                html += `
                    <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                        <td style="padding: 0.5rem 1rem 0.5rem 2rem;">
                            <i class="ph-bold ${esEntrada ? 'ph-arrow-down-left text-green-600' : 'ph-arrow-up-right text-red-500'}" style="margin-right: 6px;"></i>
                            ${item.concepto}
                        </td>
                        <td class="text-right" style="padding: 0.5rem 0.75rem; font-family: monospace; font-size: 0.95rem; font-weight: 500; color: ${esEntrada ? '#059669' : '#dc2626'};">
                            ${formatCordoba(item.importe)}
                        </td>
                    </tr>
                `;
            });
        } else {
            html += `<tr><td colspan="2" style="padding: 0.5rem 2rem; color: var(--text-muted); font-style: italic;">Sin movimientos operativos en el período</td></tr>`;
        }
    } else {
        // Método Indirecto
        const ind = data.indirecto_data || {};
        html += `
            <tr style="border-bottom: 1px solid rgba(0,0,0,0.05); font-weight: 600;">
                <td style="padding: 0.6rem 1rem 0.6rem 2rem;">Utilidad Neta del Ejercicio (según Estado de Resultados)</td>
                <td class="text-right" style="padding: 0.6rem 0.75rem; font-family: monospace; font-size: 0.95rem; font-weight: bold; color: ${ind.utilidad_neta >= 0 ? '#059669' : '#dc2626'};">
                    ${formatCordoba(ind.utilidad_neta)}
                </td>
            </tr>
            <tr style="background: rgba(0,0,0,0.02);">
                <td colspan="2" style="padding: 0.4rem 1rem 0.4rem 2rem; font-weight: 600; color: var(--text-muted); font-size: 0.85rem;">
                    (+) Ajustes por partidas que no requieren efectivo (RF100):
                </td>
            </tr>
        `;
        if (ind.ajustes_no_monetarios && ind.ajustes_no_monetarios.length > 0) {
            ind.ajustes_no_monetarios.forEach(aj => {
                html += `
                    <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                        <td style="padding: 0.45rem 1rem 0.45rem 3rem;">${aj.concepto}</td>
                        <td class="text-right" style="padding: 0.45rem 0.75rem; font-family: monospace;">${formatCordoba(aj.importe)}</td>
                    </tr>
                `;
            });
        }
        html += `
            <tr style="background: rgba(0,0,0,0.02);">
                <td colspan="2" style="padding: 0.4rem 1rem 0.4rem 2rem; font-weight: 600; color: var(--text-muted); font-size: 0.85rem;">
                    (&plusmn;) Cambios en cuentas de Capital de Trabajo:
                </td>
            </tr>
        `;
        if (ind.cambios_capital_trabajo && ind.cambios_capital_trabajo.length > 0) {
            ind.cambios_capital_trabajo.forEach(cw => {
                html += `
                    <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                        <td style="padding: 0.45rem 1rem 0.45rem 3rem;">${cw.descripcion}</td>
                        <td class="text-right" style="padding: 0.45rem 0.75rem; font-family: monospace; color: ${cw.impacto >= 0 ? '#059669' : '#dc2626'};">
                            ${formatCordoba(cw.impacto)}
                        </td>
                    </tr>
                `;
            });
        }
    }

    html += `
        <tr style="border-top: 2px solid var(--border-color); font-weight: 800; background: rgba(5, 150, 105, 0.04);">
            <td style="padding: 0.75rem 1rem 0.75rem 1.5rem; color: #047857;">Flujo Neto de Actividades de Operación</td>
            <td class="text-right" style="padding: 0.75rem 0.75rem; font-family: monospace; font-size: 1.05rem; color: ${data.flujo_neto_operacion >= 0 ? '#059669' : '#dc2626'};">
                ${formatCordoba(data.flujo_neto_operacion)}
            </td>
        </tr>
    `;

    // -------------------------------------------------------------------------
    // B. ACTIVIDADES DE INVERSIÓN
    // -------------------------------------------------------------------------
    html += `
        <tr><td colspan="2" style="padding-top: 1.5rem;"></td></tr>
        <tr style="background: rgba(37, 99, 235, 0.08);">
            <td colspan="2" style="font-weight: 800; font-size: 1.05rem; padding: 0.65rem 0.75rem; color: #1d4ed8; border-left: 4px solid #2563eb;">
                2. ACTIVIDADES DE INVERSIÓN
            </td>
        </tr>
    `;
    if (data.actividades_inversion && data.actividades_inversion.length > 0) {
        data.actividades_inversion.forEach(item => {
            const esEntrada = item.importe >= 0;
            html += `
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                    <td style="padding: 0.5rem 1rem 0.5rem 2rem;">
                        <i class="ph-bold ${esEntrada ? 'ph-arrow-down-left text-green-600' : 'ph-arrow-up-right text-red-500'}" style="margin-right: 6px;"></i>
                        ${item.concepto}
                    </td>
                    <td class="text-right" style="padding: 0.5rem 0.75rem; font-family: monospace; font-size: 0.95rem; font-weight: 500; color: ${esEntrada ? '#059669' : '#dc2626'};">
                        ${formatCordoba(item.importe)}
                    </td>
                </tr>
            `;
        });
    } else {
        html += `<tr><td colspan="2" style="padding: 0.5rem 2rem; color: var(--text-muted); font-style: italic;">Sin compras ni ventas de activos fijos en el período</td></tr>`;
    }
    html += `
        <tr style="border-top: 2px solid var(--border-color); font-weight: 800; background: rgba(37, 99, 235, 0.04);">
            <td style="padding: 0.75rem 1rem 0.75rem 1.5rem; color: #1d4ed8;">Flujo Neto de Actividades de Inversión</td>
            <td class="text-right" style="padding: 0.75rem 0.75rem; font-family: monospace; font-size: 1.05rem; color: ${data.flujo_neto_inversion >= 0 ? '#059669' : '#dc2626'};">
                ${formatCordoba(data.flujo_neto_inversion)}
            </td>
        </tr>
    `;

    // -------------------------------------------------------------------------
    // C. ACTIVIDADES DE FINANCIAMIENTO
    // -------------------------------------------------------------------------
    html += `
        <tr><td colspan="2" style="padding-top: 1.5rem;"></td></tr>
        <tr style="background: rgba(147, 51, 234, 0.08);">
            <td colspan="2" style="font-weight: 800; font-size: 1.05rem; padding: 0.65rem 0.75rem; color: #7e22ce; border-left: 4px solid #9333ea;">
                3. ACTIVIDADES DE FINANCIAMIENTO
            </td>
        </tr>
    `;
    if (data.actividades_financiamiento && data.actividades_financiamiento.length > 0) {
        data.actividades_financiamiento.forEach(item => {
            const esEntrada = item.importe >= 0;
            html += `
                <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                    <td style="padding: 0.5rem 1rem 0.5rem 2rem;">
                        <i class="ph-bold ${esEntrada ? 'ph-arrow-down-left text-green-600' : 'ph-arrow-up-right text-red-500'}" style="margin-right: 6px;"></i>
                        ${item.concepto}
                    </td>
                    <td class="text-right" style="padding: 0.5rem 0.75rem; font-family: monospace; font-size: 0.95rem; font-weight: 500; color: ${esEntrada ? '#059669' : '#dc2626'};">
                        ${formatCordoba(item.importe)}
                    </td>
                </tr>
            `;
        });
    } else {
        html += `<tr><td colspan="2" style="padding: 0.5rem 2rem; color: var(--text-muted); font-style: italic;">Sin movimientos de préstamos ni aportes en el período</td></tr>`;
    }
    html += `
        <tr style="border-top: 2px solid var(--border-color); font-weight: 800; background: rgba(147, 51, 234, 0.04);">
            <td style="padding: 0.75rem 1rem 0.75rem 1.5rem; color: #7e22ce;">Flujo Neto de Actividades de Financiamiento</td>
            <td class="text-right" style="padding: 0.75rem 0.75rem; font-family: monospace; font-size: 1.05rem; color: ${data.flujo_neto_financiamiento >= 0 ? '#059669' : '#dc2626'};">
                ${formatCordoba(data.flujo_neto_financiamiento)}
            </td>
        </tr>
    `;

    // -------------------------------------------------------------------------
    // D. CONCILIACIÓN Y CUADRATURA DE EFECTIVO (RF102)
    // -------------------------------------------------------------------------
    html += `
        <tr><td colspan="2" style="padding-top: 2rem;"></td></tr>
        <tr style="background: rgba(15, 23, 42, 0.08); border-top: 2px solid var(--text-color);">
            <td style="padding: 0.85rem 1rem 0.85rem 1.5rem; font-weight: 800; font-size: 1.05rem;">
                VARIACIÓN NETA DE EFECTIVO Y EQUIVALENTES (1 + 2 + 3)
            </td>
            <td class="text-right" style="padding: 0.85rem 0.75rem; font-family: monospace; font-size: 1.15rem; font-weight: 900; color: ${data.variacion_neta_efectivo >= 0 ? '#059669' : '#dc2626'};">
                ${formatCordoba(data.variacion_neta_efectivo)}
            </td>
        </tr>
        <tr>
            <td style="padding: 0.6rem 1rem 0.6rem 1.5rem; font-weight: 600; color: var(--text-muted);">
                (+) Saldo Inicial de Efectivo y Equivalentes
            </td>
            <td class="text-right" style="padding: 0.6rem 0.75rem; font-family: monospace; font-size: 1rem; font-weight: 600;">
                ${formatCordoba(data.saldo_inicial)}
            </td>
        </tr>
        <tr style="border-top: 2px double var(--border-color); background: rgba(5, 150, 105, 0.1);">
            <td style="padding: 0.85rem 1rem 0.85rem 1.5rem; font-weight: 800; font-size: 1.1rem; color: #047857;">
                (=) SALDO FINAL CALCULADO DE EFECTIVO Y EQUIVALENTES
            </td>
            <td class="text-right" style="padding: 0.85rem 0.75rem; font-family: monospace; font-size: 1.25rem; font-weight: 900; color: #047857;">
                ${formatCordoba(data.saldo_final_calculado)}
            </td>
        </tr>
    `;

    html += `</tbody></table>`;

    // -------------------------------------------------------------------------
    // CARD DE CUADRATURA ESTRICTA CONTRA BALANCE GENERAL (RF102)
    // -------------------------------------------------------------------------
    const cuadrado = data.esta_cuadrado;
    html += `
        <div style="margin-top: 2rem; border-radius: 8px; padding: 1.5rem; border: 2px solid ${cuadrado ? '#10b981' : '#f59e0b'}; background: ${cuadrado ? 'rgba(16, 185, 129, 0.06)' : 'rgba(245, 158, 11, 0.06)'};">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <div style="font-weight: 800; font-size: 1.05rem; color: ${cuadrado ? '#065f46' : '#92400e'}; display: flex; align-items: center; gap: 0.5rem;">
                        <i class="ph-bold ${cuadrado ? 'ph-check-circle' : 'ph-warning'}" style="font-size: 1.4rem;"></i>
                        ${cuadrado ? 'VALIDACIÓN DE CUADRATURA PERFECTA (RF102)' : 'ALERTA DE CUADRATURA CONTABLE'}
                    </div>
                    <div style="font-size: 0.85rem; color: var(--text-muted); margin-top: 0.25rem;">
                        Contraste contra cuentas de liquidez en el Balance General (Caja General 1.1.01 y Bancos 1.1.02):
                    </div>
                </div>
                <div style="text-align: right;">
                    <span style="display: inline-block; padding: 0.4rem 0.85rem; border-radius: 20px; font-weight: bold; font-size: 0.85rem; background: ${cuadrado ? '#10b981' : '#f59e0b'}; color: white;">
                        ${cuadrado ? '✓ Cuadrado al Centavo' : 'Diferencia: ' + formatCordoba(data.diferencia_cuadratura)}
                    </span>
                </div>
            </div>

            <!-- Desglose de Cuentas de Efectivo -->
            <div style="margin-top: 1rem; display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 1rem; border-top: 1px solid rgba(0,0,0,0.08); padding-top: 1rem;">
    `;

    if (data.desglose_efectivo && data.desglose_efectivo.length > 0) {
        data.desglose_efectivo.forEach(c => {
            html += `
                <div style="background: var(--bg-body); padding: 0.75rem 1rem; border-radius: 6px; border: 1px solid var(--border-color);">
                    <div style="font-size: 0.8rem; color: var(--text-muted);">${c.codigo} &bull; ${c.nombre}</div>
                    <div style="font-size: 1.1rem; font-weight: bold; font-family: monospace; color: var(--text-color); margin-top: 0.25rem;">
                        ${formatCordoba(c.saldo)}
                    </div>
                </div>
            `;
        });
    }

    html += `
                <div style="background: var(--bg-body); padding: 0.75rem 1rem; border-radius: 6px; border: 1px solid #059669; border-left: 4px solid #059669;">
                    <div style="font-size: 0.8rem; color: #059669; font-weight: 700;">TOTAL CAJA Y BANCOS AL CIERRE</div>
                    <div style="font-size: 1.15rem; font-weight: 800; font-family: monospace; color: #059669; margin-top: 0.25rem;">
                        ${formatCordoba(data.saldo_final_balance)}
                    </div>
                </div>
            </div>
        </div>
    `;

    // -------------------------------------------------------------------------
    // E. SECCIÓN DE FIRMAS OFICIALES (RF46)
    // -------------------------------------------------------------------------
    html += `
        <div style="margin-top: 3.5rem; display: grid; grid-template-columns: 1fr 1fr; gap: 4rem; text-align: center;">
            <div>
                <div style="border-top: 1.5px solid var(--text-color); padding-top: 0.6rem; width: 85%; margin: 0 auto;">
                    <strong style="font-size: 0.95rem; color: var(--text-color); display: block;">Lic. Gerente Administrativo y Financiero</strong>
                    <span style="font-size: 0.82rem; color: var(--text-muted);">Representante Legal &bull; Jehová Jireh Moto Repuestos</span>
                </div>
            </div>
            <div>
                <div style="border-top: 1.5px solid var(--text-color); padding-top: 0.6rem; width: 85%; margin: 0 auto;">
                    <strong style="font-size: 0.95rem; color: var(--text-color); display: block;">Contador Público Autorizado (CPA)</strong>
                    <span style="font-size: 0.82rem; color: var(--text-muted);">Contador Externo &bull; Colegiado CCPN No. 4920</span>
                </div>
            </div>
        </div>

        </div><!-- /Fin contenedor reporte -->
    `;

    container.innerHTML = html;
}

// -----------------------------------------------------------------------------
// 2. GUARDAR CORTE OFICIAL EN BASE DE DATOS
// -----------------------------------------------------------------------------
async function guardarCorteFlujoOficial() {
    if (!flujoActualData) {
        alert("Primero debe generar el estado de flujo de efectivo.");
        return;
    }

    if (!confirm("¿Desea oficializar y guardar este corte del Estado de Flujos de Efectivo en la base de datos?")) {
        return;
    }

    try {
        const payload = {
            ejercicio_fiscal: new Date().getFullYear(),
            periodo_tipo: 'Mensual',
            fecha_inicio: flujoActualData.periodo.start === 'Inicio' ? '2026-01-01' : flujoActualData.periodo.start,
            fecha_fin: flujoActualData.periodo.end,
            metodo: flujoActualData.metodo,
            saldo_inicial_efectivo: flujoActualData.saldo_inicial,
            flujo_neto_operacion: flujoActualData.flujo_neto_operacion,
            flujo_neto_inversion: flujoActualData.flujo_neto_inversion,
            flujo_neto_financiamiento: flujoActualData.flujo_neto_financiamiento,
            variacion_neta_efectivo: flujoActualData.variacion_neta_efectivo,
            saldo_final_calculado: flujoActualData.saldo_final_calculado,
            saldo_final_balance_general: flujoActualData.saldo_final_balance,
            observaciones: `Corte oficial generado bajo método ${flujoActualData.metodo}`,
            detalles: [
                ...(flujoActualData.actividades_operacion || []).map(i => ({ actividad: 'Operacion', concepto: i.concepto, tipo_movimiento: i.tipo, importe: i.importe })),
                ...(flujoActualData.actividades_inversion || []).map(i => ({ actividad: 'Inversion', concepto: i.concepto, tipo_movimiento: i.tipo, importe: i.importe })),
                ...(flujoActualData.actividades_financiamiento || []).map(i => ({ actividad: 'Financiamiento', concepto: i.concepto, tipo_movimiento: i.tipo, importe: i.importe }))
            ]
        };

        const resp = await fetch('/api/finanzas/flujo_efectivo/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const res = await resp.json();

        if (res.success) {
            alert("✓ " + res.message);
        } else {
            alert("Error: " + (res.error || "No se pudo guardar"));
        }
    } catch (e) {
        console.error(e);
        alert("Error de red al guardar corte oficial.");
    }
}

// -----------------------------------------------------------------------------
// 3. IMPRIMIR ESTADO DE FLUJO
// -----------------------------------------------------------------------------
function imprimirFlujoEfectivo() {
    const reportElem = document.getElementById('reporte-flujo-efectivo');
    if (!reportElem) return;

    const ventana = window.open('', '_blank');
    ventana.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
            <title>Estado de Flujos de Efectivo - Jehová Jireh</title>
            <style>
                body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 20px; color: #1e293b; }
                table { width: 100%; border-collapse: collapse; margin-top: 10px; }
                td, th { padding: 6px 10px; }
                .text-right { text-align: right; }
                @media print {
                    @page { margin: 1.5cm; }
                    body { print-color-adjust: exact; -webkit-print-color-adjust: exact; }
                }
            </style>
        </head>
        <body onload="window.print()">
            ${reportElem.innerHTML}
        </body>
        </html>
    `);
    ventana.document.close();
}

// -----------------------------------------------------------------------------
// 4. CONCILIACIÓN BANCARIA MENSUAL (RF98)
// -----------------------------------------------------------------------------
async function cargarDatosConciliacion() {
    const selectCta = document.getElementById('conc-cuenta-banco');
    const selectMes = document.getElementById('conc-mes');
    const inputAnio = document.getElementById('conc-anio');
    if (!selectCta || !selectMes || !inputAnio) return;

    const cuentaId = selectCta.value || 2;
    const mes = selectMes.value || (new Date().getMonth() + 1);
    const anio = inputAnio.value || new Date().getFullYear();

    try {
        const resp = await fetch(`/api/finanzas/conciliacion/datos?cuenta_id=${cuentaId}&anio=${anio}&mes=${mes}`);
        const data = await resp.json();

        if (data.error) {
            console.error(data.error);
            return;
        }

        conciliacionActualData = data;

        // Actualizar dropdown de cuentas de bancos si vienen opciones
        if (data.cuentas_bancos && selectCta.options.length <= 1) {
            selectCta.innerHTML = '';
            data.cuentas_bancos.forEach(b => {
                selectCta.innerHTML += `<option value="${b.id}" ${b.id == cuentaId ? 'selected' : ''}>${b.codigo} - ${b.nombre}</option>`;
            });
        }

        // Saldo según Libros
        const lblLibros = document.getElementById('conc-lbl-saldo-libros');
        if (lblLibros) lblLibros.innerText = formatCordoba(data.saldo_segun_libros);

        // Movimientos en Libros
        const tbodyMovs = document.getElementById('conc-tbody-movimientos-libros');
        if (tbodyMovs) {
            if (data.movimientos_mes && data.movimientos_mes.length > 0) {
                tbodyMovs.innerHTML = data.movimientos_mes.map(m => `
                    <tr>
                        <td style="padding: 4px 6px;">${m.fecha}</td>
                        <td style="padding: 4px 6px;">${m.concepto}</td>
                        <td class="text-right" style="padding: 4px 6px; font-family: monospace; color: #059669;">${m.debe > 0 ? formatCordoba(m.debe) : '-'}</td>
                        <td class="text-right" style="padding: 4px 6px; font-family: monospace; color: #dc2626;">${m.haber > 0 ? formatCordoba(m.haber) : '-'}</td>
                    </tr>
                `).join('');
            } else {
                tbodyMovs.innerHTML = `<tr><td colspan="4" class="text-center text-muted" style="padding: 10px;">Sin asientos en bancos durante este mes</td></tr>`;
            }
        }

        // Cargar saldo de banco y partidas si ya existía conciliación previa
        const inputBanco = document.getElementById('conc-input-saldo-banco');
        if (data.conciliacion_guardada) {
            if (inputBanco) inputBanco.value = data.conciliacion_guardada.saldo_segun_banco;
            partidasEnTransito = data.partidas_pendientes || [];
        } else {
            // Sugerir por defecto el mismo saldo de libros como punto de partida si está vacío
            if (inputBanco && (inputBanco.value === '0.00' || !inputBanco.value)) {
                inputBanco.value = data.saldo_segun_libros;
            }
            partidasEnTransito = [];
        }

        renderPartidasTransito();
        recalcularConciliacionEnVivo();
        cargarReclasificaciones();

    } catch (e) {
        console.error("Error al cargar conciliación:", e);
    }
}

function renderPartidasTransito() {
    const tbody = document.getElementById('conc-tbody-partidas-transito');
    if (!tbody) return;

    if (partidasEnTransito.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center text-muted" style="padding: 10px;">Sin partidas pendientes en tránsito registradas</td></tr>`;
        return;
    }

    tbody.innerHTML = partidasEnTransito.map((p, idx) => `
        <tr>
            <td style="padding: 4px 6px; font-weight: 600;">${p.tipo_partida}</td>
            <td style="padding: 4px 6px;">${p.numero_documento_referencia}</td>
            <td class="text-right" style="padding: 4px 6px; font-family: monospace; font-weight: bold;">${formatCordoba(p.monto)}</td>
            <td style="padding: 4px 6px;">
                <span style="font-size: 0.75rem; padding: 2px 6px; border-radius: 4px; background: ${p.efecto_en_saldo === 'Suma' ? '#dcfce7' : '#fee2e2'}; color: ${p.efecto_en_saldo === 'Suma' ? '#166534' : '#991b1b'}; font-weight: bold;">
                    ${p.efecto_en_saldo}
                </span>
            </td>
            <td style="padding: 4px 6px; text-align: center;">
                <button type="button" class="btn btn-sm" style="padding: 2px 5px; color: #ef4444;" onclick="eliminarPartidaTransito(${idx})" title="Eliminar partida">
                    <i class="ph-bold ph-trash"></i>
                </button>
            </td>
        </tr>
    `).join('');
}

function recalcularConciliacionEnVivo() {
    if (!conciliacionActualData) return;

    const saldoLibros = parseFloat(conciliacionActualData.saldo_segun_libros || 0);
    const inputBanco = document.getElementById('conc-input-saldo-banco');
    const saldoBanco = parseFloat(inputBanco ? inputBanco.value : 0) || 0;

    // Ajustes banco:
    // Depósitos en tránsito: suman al saldo del banco
    // Cheques en tránsito: restan al saldo del banco
    let ajusteBanco = 0;
    let ajusteLibros = 0;

    partidasEnTransito.forEach(p => {
        const m = parseFloat(p.monto || 0);
        if (p.tipo_partida === 'Deposito en Transito') {
            ajusteBanco += m;
        } else if (p.tipo_partida === 'Cheque en Transito') {
            ajusteBanco -= m;
        } else if (p.tipo_partida === 'Nota de Credito') {
            ajusteLibros += m;
        } else if (p.tipo_partida === 'Nota de Debito') {
            ajusteLibros -= m;
        } else {
            if (p.efecto_en_saldo === 'Suma') ajusteBanco += m;
            else ajusteBanco -= m;
        }
    });

    const saldoBancoAjustado = saldoBanco + ajusteBanco;
    const saldoLibrosAjustado = saldoLibros + ajusteLibros;
    const diferencia = Math.abs(saldoBancoAjustado - saldoLibrosAjustado);
    const cuadrado = diferencia < 0.01;

    // Actualizar etiquetas
    const lblLibrosAj = document.getElementById('conc-saldo-libros-ajustado');
    const lblBancoAj = document.getElementById('conc-saldo-banco-ajustado');
    if (lblLibrosAj) lblLibrosAj.innerText = formatCordoba(saldoLibrosAjustado);
    if (lblBancoAj) lblBancoAj.innerText = formatCordoba(saldoBancoAjustado);

    const badge = document.getElementById('conc-badge-cuadratura');
    if (badge) {
        if (cuadrado) {
            badge.style.background = '#dcfce7';
            badge.style.color = '#15803d';
            badge.innerHTML = `<i class="ph-bold ph-check-circle" style="font-size: 1.2rem;"></i> Conciliación Cuadrada (Dif: C$ 0.00)`;
        } else {
            badge.style.background = '#fee2e2';
            badge.style.color = '#b91c1c';
            badge.innerHTML = `<i class="ph-bold ph-warning" style="font-size: 1.2rem;"></i> Diferencia detectada: ${formatCordoba(diferencia)}`;
        }
    }
}

function abrirModalPartidaTransito() {
    const m = document.getElementById('modal-partida-transito');
    if (m) m.classList.add('active');
}

function cerrarModalPartidaTransito() {
    const m = document.getElementById('modal-partida-transito');
    if (m) m.classList.remove('active');
}

function agregarPartidaTransito(event) {
    event.preventDefault();
    const tipo = document.getElementById('partida-tipo').value;
    const fecha = document.getElementById('partida-fecha').value || new Date().toISOString().split('T')[0];
    const doc = document.getElementById('partida-doc').value.trim() || 'S/N';
    const monto = parseFloat(document.getElementById('partida-monto').value) || 0;
    const desc = document.getElementById('partida-desc').value.trim() || tipo;

    let efecto = 'Resta';
    if (tipo === 'Deposito en Transito' || tipo === 'Nota de Credito') {
        efecto = 'Suma';
    }

    partidasEnTransito.push({
        tipo_partida: tipo,
        fecha: fecha,
        numero_documento_referencia: doc,
        descripcion: desc,
        monto: monto,
        efecto_en_saldo: efecto,
        esta_conciliada: 0
    });

    renderPartidasTransito();
    recalcularConciliacionEnVivo();
    cerrarModalPartidaTransito();
    document.getElementById('form-partida-transito').reset();
}

function eliminarPartidaTransito(index) {
    partidasEnTransito.splice(index, 1);
    renderPartidasTransito();
    recalcularConciliacionEnVivo();
}

async function guardarConciliacionBancaria() {
    if (!conciliacionActualData) return;

    const selectCta = document.getElementById('conc-cuenta-banco');
    const selectMes = document.getElementById('conc-mes');
    const inputAnio = document.getElementById('conc-anio');
    const inputBanco = document.getElementById('conc-input-saldo-banco');

    const cuentaId = selectCta.value || 2;
    const mes = selectMes.value;
    const anio = inputAnio.value;
    const saldoLibros = parseFloat(conciliacionActualData.saldo_segun_libros || 0);
    const saldoBanco = parseFloat(inputBanco.value || 0);

    let ajusteBanco = 0;
    let ajusteLibros = 0;
    partidasEnTransito.forEach(p => {
        const m = parseFloat(p.monto || 0);
        if (p.tipo_partida === 'Deposito en Transito') ajusteBanco += m;
        else if (p.tipo_partida === 'Cheque en Transito') ajusteBanco -= m;
        else if (p.tipo_partida === 'Nota de Credito') ajusteLibros += m;
        else if (p.tipo_partida === 'Nota de Debito') ajusteLibros -= m;
        else {
            if (p.efecto_en_saldo === 'Suma') ajusteBanco += m;
            else ajusteBanco -= m;
        }
    });

    const saldoBancoAjustado = saldoBanco + ajusteBanco;
    const saldoLibrosAjustado = saldoLibros + ajusteLibros;
    const diferencia = Math.abs(saldoBancoAjustado - saldoLibrosAjustado);

    const payload = {
        cuenta_id: cuentaId,
        anio: anio,
        mes: mes,
        fecha_corte: conciliacionActualData.fecha_corte,
        saldo_segun_libros: saldoLibros,
        saldo_segun_banco: saldoBanco,
        diferencia: diferencia,
        estado: diferencia < 0.01 ? 'Conciliada' : 'Borrador',
        observaciones: `Conciliación bancaria ${mes}/${anio}. Saldo banco ajustado: C$ ${saldoBancoAjustado.toFixed(2)} vs libros ajustado: C$ ${saldoLibrosAjustado.toFixed(2)}.`,
        partidas: partidasEnTransito
    };

    try {
        const resp = await fetch('/api/finanzas/conciliacion/guardar', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const res = await resp.json();
        if (res.success) {
            alert("✓ " + res.message);
            cargarDatosConciliacion();
        } else {
            alert("Error: " + (res.error || "No se pudo guardar la conciliación."));
        }
    } catch (e) {
        console.error(e);
        alert("Error de red al guardar conciliación.");
    }
}

// -----------------------------------------------------------------------------
// 5. BITÁCORA DE RECLASIFICACIONES Y AUDITORÍA CONTABLE (RF97, RF99)
// -----------------------------------------------------------------------------
async function cargarReclasificaciones() {
    const tbody = document.getElementById('conc-tbody-reclasificaciones');
    if (!tbody) return;

    try {
        const resp = await fetch('/api/finanzas/reclasificaciones');
        const data = await resp.json();

        if (data.reclasificaciones && data.reclasificaciones.length > 0) {
            tbody.innerHTML = data.reclasificaciones.map(r => `
                <tr>
                    <td>${r.created_at ? r.created_at.substring(0, 16) : 'N/A'}</td>
                    <td><strong>#${r.asiento_id || 'N/A'}</strong> <span style="font-size:0.75rem; color:var(--text-muted);">${r.asiento_concepto || ''}</span></td>
                    <td><span class="badge">${r.origen_modulo}</span></td>
                    <td>${r.actividad_anterior}</td>
                    <td><strong style="color: #059669;">${r.actividad_nueva}</strong></td>
                    <td>${r.motivo}</td>
                    <td><i class="ph-bold ph-user"></i> ${r.usuario}</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="7" class="text-center text-muted" style="padding: 12px;">No hay reclasificaciones manuales registradas en la auditoría.</td></tr>`;
        }
    } catch (e) {
        console.error(e);
    }
}

function abrirModalReclasificacion() {
    const m = document.getElementById('modal-reclasificacion');
    if (m) m.classList.add('active');
}

function cerrarModalReclasificacion() {
    const m = document.getElementById('modal-reclasificacion');
    if (m) m.classList.remove('active');
}

async function guardarReclasificacion(event) {
    event.preventDefault();
    const asientoId = document.getElementById('reclass-asiento-id').value;
    const actAnt = document.getElementById('reclass-act-anterior').value;
    const actNueva = document.getElementById('reclass-act-nueva').value;
    const origen = document.getElementById('reclass-origen').value;
    const motivo = document.getElementById('reclass-motivo').value.trim();

    if (!motivo) {
        alert("Debe ingresar la justificación contable.");
        return;
    }

    try {
        const resp = await fetch('/api/finanzas/reclasificaciones', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                asiento_id: asientoId ? parseInt(asientoId) : null,
                origen_modulo: origen,
                actividad_anterior: actAnt,
                actividad_nueva: actNueva,
                motivo_reclasificacion: motivo
            })
        });
        const res = await resp.json();

        if (res.success) {
            alert("✓ " + res.message);
            cerrarModalReclasificacion();
            document.getElementById('form-reclasificacion').reset();
            cargarReclasificaciones();
        } else {
            alert("Error: " + (res.error || "No se pudo registrar"));
        }
    } catch (e) {
        console.error(e);
        alert("Error de red al guardar reclasificación.");
    }
}

// Inicialización automática cuando se selecciona la pestaña de finanzas
document.addEventListener('DOMContentLoaded', () => {
    // Si la fecha actual de finanzas está disponible, prellenar mes y año en conciliación
    const fechaFinElem = document.getElementById('fin-fecha-fin');
    const inputAnio = document.getElementById('conc-anio');
    const selectMes = document.getElementById('conc-mes');
    if (fechaFinElem && fechaFinElem.value && inputAnio && selectMes) {
        const parts = fechaFinElem.value.split('-');
        if (parts.length === 3) {
            inputAnio.value = parts[0];
            selectMes.value = parseInt(parts[1]);
        }
    }
});
