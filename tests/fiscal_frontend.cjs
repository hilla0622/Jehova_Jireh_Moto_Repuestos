const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../Fronted/static/js/fiscal.js'), 'utf8');
const fixtures = process.argv.includes('--stdin') ? JSON.parse(fs.readFileSync(0, 'utf8')) : [{
    anio: 2024, cuentas_balance: {}, cuentas_resultados: {},
    calculo_ir: {}, liquidacion: {},
}];

(async () => {
    for (const fixture of fixtures) {
        const nodes = new Map();
        const context = vm.createContext({
            console, Date, alert: message => { throw Error(message); }, window: {},
            document: {addEventListener() {}, getElementById(id) {
                if (!nodes.has(id)) nodes.set(id, {value: '0.00', textContent: '', style: {}});
                return nodes.get(id);
            }},
            fetch: async () => ({ok: true, json: async () => fixture}),
        });
        vm.runInContext(source, context);
        vm.runInContext(`anioFiscalSeleccionado = ${fixture.anio}`, context);
        await vm.runInContext('cargarSimulacionFiscal()', context);
        const payload = vm.runInContext('recopilarPayloadSimulacion()', context);
        if (!fixture.resultados) {
            assert.equal(payload.balance.total_activos, 0);
            assert.equal(payload.resultados.total_ingresos_brutos, 0);
            assert.equal(payload.liquidacion.anticipos_mensuales, 0);
            assert.equal(payload.liquidacion.saldo_a_pagar, 0);
        } else {
            for (const [section, fields] of Object.entries({
                balance: ['total_activos','total_pasivos','patrimonio_total'],
                resultados: ['total_ingresos_brutos','total_costos','total_gastos'],
                calculo_ir: ['renta_neta_gravable','ir_calculado_30','pmd_calculado_1','ir_determinado'],
                liquidacion: ['total_acreditamientos','saldo_a_pagar','saldo_a_favor'],
            })) {
                for (const field of fields) assert.equal(payload[section][field], fixture[section][field],
                    `${fixture.anio}: ${section}.${field}`);
            }
        }
        for (const [income, rent, rate] of [[12000000,100000,10],[12000000,100000.01,15],
            [12000000,200000.01,20],[12000000,350000.01,25],[12000000,500000.01,30],
            [12000000.01,10000,30]]) {
            assert.equal(context.tasaIrAnual(income,rent),rate);
        }
    }
    console.log(`OK: ceros, tarifas y coherencia frontend/servidor (${fixtures.length} ejercicios).`);
})().catch(error => { console.error(error); process.exitCode = 1; });
