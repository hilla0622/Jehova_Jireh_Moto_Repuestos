const {chromium} = require('playwright');
const assert = require('node:assert/strict');
const path = require('node:path');
const fs = require('node:fs');
(async () => {
    const browser = await chromium.launch({headless:true, channel:'msedge'});
    const page = await browser.newPage({viewport:{width:1440,height:1000}});
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    try {
        await page.goto('http://127.0.0.1:5088/__rrhh_preview');
        await page.getByRole('button',{name:'Registrar riesgo',exact:true}).click();
        const riesgo = page.locator('#form-riesgo-control');
        await page.locator('#riesgo-propuesta').selectOption('cargas');
        assert.match(await riesgo.locator('[name="medidas_preventivas"]').inputValue(), /carretillas/);
        assert.doesNotMatch(await riesgo.locator('[name="medidas_preventivas"]').inputValue(), /faja/);
        for (const [key,value] of Object.entries({area:'Bodega / Almacén', tipo_riesgo:'Caída de objetos almacenados', descripcion:'Estantería de repuestos. Pendiente de evaluación.', medidas_preventivas:'Asegurar estantes y distribuir cargas.', responsable_seguimiento:'Encargado de Inventario'})) await riesgo.locator(`[name="${key}"]`).fill(value);
        await riesgo.getByRole('button',{name:'Guardar riesgo'}).click();
        await page.locator('#tbody-higiene-riesgos').getByRole('button',{name:'Editar',exact:true}).click();
        await riesgo.locator('[name="medidas_preventivas"]').fill('Revisar fijaciones y mantener los artículos pesados abajo.');
        await riesgo.getByRole('button',{name:'Guardar riesgo'}).click();
        await page.locator('#tbody-higiene-riesgos').getByRole('button',{name:'Seguimiento',exact:true}).click();
        const seguimiento = page.locator('#form-seguimiento-riesgo');
        await seguimiento.locator('[name="observaciones"]').fill('Se revisaron y fijaron los estantes.');
        await seguimiento.locator('[name="estado"]').selectOption('Controlado');
        await seguimiento.getByRole('button',{name:'Registrar revisión'}).click();
        await page.locator('#riesgo-historial').getByText('Se revisaron y fijaron los estantes.',{exact:true}).waitFor();
        await seguimiento.getByRole('button',{name:'Cerrar',exact:true}).click();

        await page.getByRole('button',{name:'Registrar entrega',exact:true}).click();
        const epp = page.locator('#form-entrega-epp');
        await epp.locator('[name="empleado_id"]').selectOption('1');
        await epp.locator('[name="tipo_equipo"]').fill('Guantes de protección mecánica');
        await epp.locator('[name="area"]').fill('Bodega / Almacén');
        await epp.locator('[name="cantidad"]').fill('2');
        await epp.locator('[name="fecha_entrega"]').fill('2026-01-01');
        await epp.locator('[name="fecha_reposicion_sugerida"]').fill('2026-02-01');
        await epp.locator('[name="archivo"]').setInputFiles({name:'constancia.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.4\nConstancia ficticia')});
        await epp.getByRole('button',{name:'Guardar entrega'}).click();
        await page.locator('#epp-vista').selectOption('pendientes');
        await page.locator('#tbody-higiene-epp').getByRole('button',{name:'Detalle',exact:true}).click();
        const downloadPromise = page.waitForEvent('download');
        await page.getByRole('link',{name:'Descargar constancia de recepción'}).click();
        const download = await downloadPromise;
        assert.equal(download.suggestedFilename(), 'constancia.pdf');
        await page.locator('#modal-epp-detalle .modal-footer button').click();
        await page.locator('#tbody-higiene-epp').getByRole('button',{name:'Reponer',exact:true}).click();
        await epp.locator('[name="fecha_entrega"]').fill('2026-03-01');
        await epp.locator('[name="fecha_reposicion_sugerida"]').fill('2027-03-01');
        await epp.locator('[name="motivo_reposicion"]').fill('Deterioro del equipo original.');
        await epp.getByRole('button',{name:'Guardar entrega'}).click();
        await page.locator('#modal-entrega-epp').waitFor({state:'hidden'});
        await page.locator('#epp-vista').selectOption('historial');
        await page.locator('#tbody-higiene-epp').getByText('Repuesta · #2',{exact:true}).waitFor();
        assert.equal(await page.locator('#tbody-higiene-epp tr').count(),2);

        await page.getByRole('button',{name:'Expediente de prueba'}).click();
        await page.locator('#exp-archivo').setInputFiles({name:'cedula.pdf',mimeType:'application/pdf',buffer:Buffer.from('%PDF-1.4\nDocumento ficticio')});
        await page.getByRole('button',{name:'Guardar documento',exact:false}).click();
        await page.locator('#tbody-expediente-documentos').getByRole('link',{name:'Descargar'}).waitFor();
        await page.locator('#modal-expediente-digital .modal-footer button').click();

        await page.getByRole('button',{name:'Registrar pago',exact:true}).click();
        const pago = page.locator('#form-pago-control');
        await pago.locator('[name="nomina_id"]').selectOption('1');
        await pago.locator('[name="empleado_id"]').selectOption('1');
        await pago.locator('[name="monto_pagado"]').fill('100');
        await pago.locator('[name="numero_referencia"]').fill('PRUEBA-001');
        await pago.getByRole('button',{name:'Confirmar pago'}).click();
        await page.locator('#tbody-pagos-nomina').getByText('PRUEBA-001',{exact:true}).waitFor();

        const output = process.argv[2];
        if (output) {fs.mkdirSync(output,{recursive:true}); await page.screenshot({path:path.join(output,'rrhh-escritorio.png'),fullPage:true});}
        await page.setViewportSize({width:390,height:844});
        assert.ok(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth + 1));
        await page.getByRole('button',{name:'Registrar entrega',exact:true}).click();
        if (output) await page.screenshot({path:path.join(output,'rrhh-movil.png'),fullPage:true});
        assert.ok(await page.locator('#form-entrega-epp button[type="submit"]').isVisible());
        assert.deepEqual(errors,[]);
        console.log('UI OK: riesgo, edición, seguimiento, entrega, reposición, constancia, expediente, pago y vista móvil.');
    } finally { await browser.close(); }
})().catch(e => {console.error(e);process.exitCode=1;});
