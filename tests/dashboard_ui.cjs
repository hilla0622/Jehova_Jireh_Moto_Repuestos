// Preparación: python tests/export_dashboard_preview.py (SQL Server local, solo GET).
// Ejecución: node tests/dashboard_ui.cjs (Playwright y Microsoft Edge instalados).
const { chromium } = require('playwright');
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const root = path.resolve(__dirname, '..');
const output = path.join(root, 'tmp/dashboard_review');
const snapshot = JSON.parse(fs.readFileSync(path.join(output, 'snapshot.json'), 'utf8'));

(async () => {
    const browser = await chromium.launch({channel: 'msedge', headless: true});
    const page = await browser.newPage({viewport: {width: 1365, height: 900}});
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.route('http://dashboard.local/**', async route => {
        const url = new URL(route.request().url());
        if (url.pathname === '/dashboard') return route.fulfill({contentType:'text/html',body:snapshot['/dashboard']});
        if (url.pathname.startsWith('/static/')) {
            const file = path.join(root,'Fronted',url.pathname);
            const contentType = file.endsWith('.css') ? 'text/css' : file.endsWith('.js') ? 'text/javascript' : file.endsWith('.png') ? 'image/png' : 'image/jpeg';
            return route.fulfill({body:fs.readFileSync(file),contentType});
        }
        return route.fulfill({json:snapshot[url.pathname] || []});
    });
    try {
        await page.goto('http://dashboard.local/dashboard');
        await page.waitForFunction(() => document.querySelector('#dashboard-load-status').hidden);
        assert.equal(await page.locator('#tab-panel .action-tile').count(), 6);
        assert.equal(await page.locator('#dashboard-activity tr').count(), 6);
        const latest = [...snapshot['/api/ventas']].sort((a,b) => b.fecha.localeCompare(a.fecha) || b.id-a.id)[0];
        assert.match(await page.locator('#recent-sales-list tr').first().innerText(), new RegExp(latest.codigo_venta));
        assert.equal(await page.locator('#stat-proveedores').innerText(), String(snapshot['/api/proveedores'].length));
        assert.equal(await page.locator('#tab-panel .welcome-banner').count(), 0);
        assert.equal(await page.locator('#tab-panel .stat-card').count(), 0);
        const positions = await page.locator('.dashboard-panel').evaluateAll(nodes => nodes.map(node => ({x:node.getBoundingClientRect().x,y:node.getBoundingClientRect().y})));
        assert.equal(positions[0].y,positions[1].y);
        assert(positions[0].x < positions[1].x);
        await page.screenshot({path:path.join(output,'dashboard-desktop.png'), fullPage:true});
        await page.locator('#tab-panel .action-tile').filter({hasText:'Consultar Inventario'}).click();
        await page.locator('#tab-inventario.active').waitFor();
        await page.evaluate(() => switchTab('tab-panel'));
        await page.waitForFunction(() => document.querySelector('#dashboard-load-status').hidden);
        await page.evaluate(() => document.documentElement.setAttribute('data-theme','dark'));
        await page.screenshot({path:path.join(output,'dashboard-dark.png'), fullPage:true});
        await page.evaluate(() => document.documentElement.setAttribute('data-theme','light'));
        await page.setViewportSize({width:390,height:844});
        await page.waitForFunction(() => document.querySelector('.sidebar').getBoundingClientRect().right <= 0);
        await page.screenshot({path:path.join(output,'dashboard-mobile.png'), fullPage:true});
        assert(await page.evaluate(() => document.body.scrollWidth <= innerWidth));
        assert(await page.locator('.dashboard-panel').evaluateAll(nodes => nodes.every(node => node.getBoundingClientRect().right <= innerWidth)));
        // Nombres con caracteres HTML se muestran como texto; no se interpretan.
        await page.evaluate(() => {
            renderRecentSalesList([{id:1,codigo_venta:'VEN-0001',cliente:'<img src=x onerror=alert(1)>',fecha:'2026-10-01',total:10,estado:'Completada'}]);
        });
        assert.equal(await page.locator('#recent-sales-list img').count(), 0);
        await page.evaluate(() => { renderDashboardStock([]); renderRecentSalesList([]); renderDashboardActivity([],[]); });
        assert.match(await page.locator('#dashboard-low-stock').innerText(), /No hay repuestos/);
        await page.route('http://dashboard.local/api/productos', route => route.fulfill({status:500,json:{error:'Prueba'}}));
        await page.evaluate(() => loadDashboardStats());
        assert.match(await page.locator('#dashboard-low-stock').innerText(), /No se pudo/);
        assert.match(await page.locator('#dashboard-load-status').innerText(), /algunos datos/);
        assert.equal(await page.locator('#recent-sales-list tr').count(), 6);
        // Los accesos de cada perfil apuntan a una sección existente.
        for (const rol of ['Vendedor','Contador','Encargado de Inventario','Encargado de Compras y Proveedores']) {
            const valid = await page.evaluate(html => {
                const doc = new DOMParser().parseFromString(html,'text/html');
                return [...doc.querySelectorAll('#tab-panel .action-tile')].every(button => doc.getElementById(button.getAttribute('onclick').match(/'([^']+)'/)[1]));
            },snapshot[rol]);
            assert(valid,rol);
        }
        assert.deepEqual(errors, []);
        console.log('OK: distribución, seis accesos, navegación, datos reales, orden de ventas, móvil, estados vacíos, fallos parciales y perfiles.');
    } finally { await browser.close(); }
})().catch(error => { console.error(error); process.exitCode=1; });
