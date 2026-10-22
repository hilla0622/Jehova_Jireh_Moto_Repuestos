// Ejecutar con el servidor de tests/preview_finanzas.py y Playwright instalado.
const { chromium } = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');

(async () => {
    const browser = await chromium.launch({headless: true, channel: 'msedge'});
    const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
    const page = await context.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    page.on('dialog', d => d.accept());
    try {
        await page.goto('http://127.0.0.1:5087/');
        await page.locator('#reporte-flujo-efectivo').getByText('Cuadrado al Centavo').waitFor();
        await page.locator('.flujo-controles > summary').click();
        await page.getByText('Configuración cargada.', {exact: true}).waitFor();
        await page.getByText('Etiquetas de cuentas y reglas por tipo de transacción', {exact: true}).click();
        await page.locator('#flujo-config-cuenta').selectOption('12');
        assert.equal(await page.locator('#flujo-config-nomonetario').isChecked(), true);
        await page.getByText('Revisar un asiento, distribuir efectivo y registrar ajustes', {exact: true}).click();
        await page.locator('#flujo-asiento-id').fill('3');
        await page.getByRole('button', {name: 'Consultar asiento', exact: true}).click();
        await page.locator('#flujo-asiento-detalle').getByText('Equipo', {exact: false}).waitFor();
        await page.locator('.flujo-distribucion-fila select').selectOption('Inversion');
        await page.locator('.flujo-distribucion-fila input').fill('-200');
        await page.locator('#flujo-distribucion-motivo').fill('Compra parcialmente financiada: solo el pago efectivo.');
        await page.getByRole('button', {name: 'Aplicar distribución', exact: true}).click();
        await page.getByText('Distribución aplicada al flujo y registrada en auditoría.', {exact: true}).waitFor();
        await page.getByRole('button', {name: 'Método Indirecto', exact: true}).click();
        await page.locator('#reporte-flujo-efectivo').getByText('Estado de Flujos de Efectivo (Indirecto)', {exact: true}).waitFor();
        const guardado = page.waitForResponse(r => r.url().endsWith('/flujo_efectivo/guardar'));
        await page.getByRole('button', {name: 'Guardar Corte Verificado', exact: false}).click();
        assert.equal((await guardado).status(), 200);
        const output = process.argv[2];
        if (output) {
            fs.mkdirSync(output, {recursive: true});
            await page.locator('.flujo-controles > summary').click();
            await page.screenshot({path: path.join(output, 'flujo.png'), fullPage: true});
        }
        await page.getByRole('button', {name: 'Conciliación Bancaria', exact: false}).click();
        await page.locator('#conc-cuenta-banco option[value="2"]').waitFor({state: 'attached'});
        assert.equal(await page.locator('#conc-input-saldo-banco').inputValue(), '');
        await page.locator('#conc-input-saldo-banco').fill('10000');
        await page.locator('#conc-badge-cuadratura').getByText('Diferencia cero · revisión pendiente', {exact: true}).waitFor();
        if (output) await page.screenshot({path: path.join(output, 'conciliacion.png'), fullPage: true});
        const exported = await page.context().newPage();
        await exported.goto('http://127.0.0.1:5087/api/finanzas/reportes/exportar/flujo?start=2026-10-01&end=2026-10-31&metodo=Indirecto');
        await exported.getByText('Contador Externo', {exact: false}).waitFor();
        if (output) await exported.screenshot({path: path.join(output, 'exportacion.png'), fullPage: true});
        assert.deepEqual(errors, []);
        console.log('UI: configuración, distribución, método indirecto, guardado, conciliación y exportación OK.');
    } finally {
        await browser.close();
    }
})().catch(e => { console.error(e); process.exitCode = 1; });
