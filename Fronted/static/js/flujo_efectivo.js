// ==============================================================================
// MÓDULO DE ESTADOS FINANCIEROS: ESTADO DE FLUJO DE EFECTIVO Y CONCILIACIÓN
// Marco Técnico: NIIF para PYMES Sección 7 / NIC 7 (RF96 - RF102, RF46)
// Sistema Jehová Jireh Moto Repuestos
// ==============================================================================

let metodoFlujoActual = 'Directo';
let flujoActualData = null;
let partidasEnTransito = [];
let conciliacionActualData = null;
let solicitudFlujo = 0;
let solicitudConciliacion = 0;
function escapeFlujo(v) { return String(v ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }

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
            btnDir.removeAttribute('style');
            btnInd.className = 'btn btn-sm btn-outline';
            btnInd.removeAttribute('style');
        } else {
            btnInd.className = 'btn btn-sm btn-primary';
            btnInd.removeAttribute('style');
            btnDir.className = 'btn btn-sm btn-outline';
            btnDir.removeAttribute('style');
        }
    }
    loadFlujoEfectivo(metodo);
}

async function loadFlujoEfectivo(metodo = null) {
    if (!metodo) metodo = metodoFlujoActual;
    const container = document.getElementById('reporte-flujo-efectivo');
    if (!container) return;

    const solicitud = ++solicitudFlujo;
    flujoActualData = null;
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
        if (solicitud !== solicitudFlujo) return;

        if (data.error) {
            container.innerHTML = `<div class="alert alert-danger" style="padding: 1rem; color: #ef4444; background: rgba(239, 68, 68, 0.1); border-radius: 6px;">${escapeFlujo(data.error)}</div>`;
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

    const avisos = (data.pendientes_clasificacion || []).map(p => `Asiento ${p.asiento_id}: ${p.motivo}`);
    if (data.metodo === 'Indirecto' && data.diferencia_entre_metodos !== 0) avisos.push('Diferencia con el método directo: ' + formatCordoba(data.diferencia_entre_metodos) + '. Revise los ajustes y el capital de trabajo.');
    let html = (avisos.length ? `<div role="alert" style="padding:1rem;background:#fff3cd;color:#664d03;margin-bottom:1rem"><strong>Reporte pendiente de revisión</strong><ul>${avisos.map(a => `<li>${escapeFlujo(a)}</li>`).join('')}</ul></div>` : '') + `
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
            data.actividades_operacion.forEach((item, idx) => {
                const esEntrada = item.importe >= 0;
                const tieneDesglose = item.movimientos && item.movimientos.length > 1;
                const rowId = `dir_op_row_${idx}`;
                html += `
                    <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                        <td style="padding: 0.5rem 1rem 0.5rem 2rem;">
                            <i class="ph-bold ${esEntrada ? 'ph-arrow-down-left text-green-600' : 'ph-arrow-up-right text-red-500'}" style="margin-right: 6px;"></i>
                            <span style="font-weight: 500;">${escapeFlujo(item.concepto)}</span>
                            ${tieneDesglose ? `
                                <a href="javascript:void(0)" onclick="toggleDesgloseWk('${rowId}')" style="margin-left: 0.6rem; font-size: 0.75rem; color: #2563eb; text-decoration: none; font-weight: 500; background: rgba(37,99,235,0.08); padding: 2px 8px; border-radius: 12px; display: inline-flex; align-items: center; gap: 3px;">
                                    <span id="btn_${rowId}">&#9656; Ver ${item.movimientos.length} transacciones</span>
                                </a>
                            ` : ''}
                            ${tieneDesglose ? `
                                <div id="${rowId}" style="display: none; margin-top: 0.4rem; padding: 0.5rem 0.75rem; background: rgba(0,0,0,0.02); border-left: 3px solid #059669; border-radius: 4px; font-size: 0.8rem;">
                                    <table style="width: 100%; border-collapse: collapse;">
                                        ${item.movimientos.map(m => `
                                            <tr style="border-bottom: 1px dashed rgba(0,0,0,0.06);">
                                                <td style="padding: 3px 0; color: var(--text-muted);">${escapeFlujo(m.concepto)}</td>
                                                <td class="text-right" style="padding: 3px 0; font-family: monospace; color: ${m.importe >= 0 ? '#059669' : '#dc2626'};">${formatCordoba(m.importe)}</td>
                                            </tr>
                                        `).join('')}
                                    </table>
                                </div>
                            ` : ''}
                        </td>
                        <td class="text-right" style="padding: 0.5rem 0.75rem; font-family: monospace; font-size: 0.95rem; font-weight: 600; color: ${esEntrada ? '#059669' : '#dc2626'};">
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
                        <td style="padding: 0.45rem 1rem 0.45rem 3rem;">${escapeFlujo(aj.concepto)}</td>
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
            ind.cambios_capital_trabajo.forEach((cw, idx) => {
                const tieneDesglose = cw.movimientos && cw.movimientos.length > 1;
                const rowId = `wk_row_${idx}`;
                html += `
                    <tr style="border-bottom: 1px solid rgba(0,0,0,0.05);">
                        <td style="padding: 0.5rem 1rem 0.5rem 3rem;">
                            <span style="font-weight: 500;">${escapeFlujo(cw.descripcion)}</span>
                            ${tieneDesglose ? `
                                <a href="javascript:void(0)" onclick="toggleDesgloseWk('${rowId}')" style="margin-left: 0.6rem; font-size: 0.75rem; color: #2563eb; text-decoration: none; font-weight: 500; background: rgba(37,99,235,0.08); padding: 2px 8px; border-radius: 12px; display: inline-flex; align-items: center; gap: 3px;">
                                    <span id="btn_${rowId}">&#9656; Ver ${cw.movimientos.length} asientos</span>
                                </a>
                            ` : ''}
                            ${tieneDesglose ? `
                                <div id="${rowId}" style="display: none; margin-top: 0.4rem; padding: 0.5rem 0.75rem; background: rgba(0,0,0,0.02); border-left: 3px solid #2563eb; border-radius: 4px; font-size: 0.8rem;">
                                    <table style="width: 100%; border-collapse: collapse;">
                                        ${cw.movimientos.map(m => `
                                            <tr style="border-bottom: 1px dashed rgba(0,0,0,0.06);">
                                                <td style="padding: 3px 0; color: var(--text-muted);">${escapeFlujo(m.descripcion)}</td>
                                                <td class="text-right" style="padding: 3px 0; font-family: monospace; color: ${m.impacto >= 0 ? '#059669' : '#dc2626'};">${formatCordoba(m.impacto)}</td>
                                            </tr>
                                        `).join('')}
                                    </table>
                                </div>
                            ` : ''}
                        </td>
                        <td class="text-right" style="padding: 0.5rem 0.75rem; font-family: monospace; font-weight: 600; color: ${cw.impacto >= 0 ? '#059669' : '#dc2626'};">
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
                        ${escapeFlujo(item.concepto)}
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
                        ${escapeFlujo(item.concepto)}
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
    const cuadrado = data.puede_guardar;
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
                        ${cuadrado ? '✓ Cuadrado al Centavo' : 'Revisión pendiente. Diferencia: ' + formatCordoba(data.diferencia_cuadratura)}
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
                    <div style="font-size: 0.8rem; color: var(--text-muted);">${escapeFlujo(c.codigo)} &bull; ${escapeFlujo(c.nombre)}</div>
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
                    <strong style="font-size: 0.95rem; color: var(--text-color); display: block;">Gerente Administrativo y Financiero</strong>
                    <span style="font-size: 0.82rem; color: var(--text-muted);">Nombre y firma</span>
                </div>
            </div>
            <div>
                <div style="border-top: 1.5px solid var(--text-color); padding-top: 0.6rem; width: 85%; margin: 0 auto;">
                    <strong style="font-size: 0.95rem; color: var(--text-color); display: block;">Contador Externo</strong>
                    <span style="font-size: 0.82rem; color: var(--text-muted);">Nombre y firma</span>
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

    if (!confirm("¿Desea guardar este corte verificado, con su detalle, como borrador?")) {
        return;
    }

    try {
        if (!flujoActualData.puede_guardar) {
            alert('Resuelva las partidas pendientes y las diferencias antes de guardar.');
            return;
        }
        const payload = {
            fecha_inicio: flujoActualData.periodo.start,
            fecha_fin: flujoActualData.periodo.end,
            metodo: flujoActualData.metodo,
            periodo_tipo: 'Personalizado',
            revision: flujoActualData.revision
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
    if (!ventana) { alert('Permita abrir la ventana de impresión para imprimir o guardar como PDF.'); return; }
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
// La interfaz y el cotejo bancario se implementan en conciliacion.js.

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
                    <td><strong>#${r.asiento_id || 'N/A'}</strong> <span style="font-size:0.75rem; color:var(--text-muted);">${escapeFlujo(r.asiento_concepto || '')}</span></td>
                    <td><span class="badge">${escapeFlujo(r.origen_modulo)}</span></td>
                    <td>${escapeFlujo(r.actividad_anterior)}</td>
                    <td><strong style="color: #059669;">${escapeFlujo(r.actividad_nueva)}</strong></td>
                    <td>${escapeFlujo(r.motivo)}</td>
                    <td><i class="ph-bold ph-user"></i> ${escapeFlujo(r.usuario)}</td>
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
        const asientoResp = await fetch('/api/finanzas/flujo/asiento/' + encodeURIComponent(asientoId));
        const asiento = await asientoResp.json();
        if (!asientoResp.ok) throw new Error(asiento.error);
        const resp = await fetch('/api/finanzas/reclasificaciones', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                asiento_id: asientoId ? parseInt(asientoId) : null,
                revision: asiento.revision,
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
            await loadFlujoEfectivo();
        } else {
            alert("Error: " + (res.error || "No se pudo registrar"));
        }
    } catch (e) {
        console.error(e);
        alert("Error de red al guardar reclasificación.");
    }
}

window.toggleDesgloseWk = function(rowId) {
    const el = document.getElementById(rowId);
    const btn = document.getElementById('btn_' + rowId);
    if (!el) return;
    if (el.style.display === 'none') {
        el.style.display = 'block';
        if (btn) btn.innerHTML = '&#9662; Ocultar asientos';
    } else {
        el.style.display = 'none';
        if (btn) btn.innerHTML = '&#9656; Ver desglose';
    }
};

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
