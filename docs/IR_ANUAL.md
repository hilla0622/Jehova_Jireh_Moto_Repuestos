# Declaración anual IR: cálculo y demostración

El guardado reconstruye la declaración desde los asientos, ajustes fiscales y
acreditamientos del ejercicio en SQL Server. Las modificaciones manuales del
formulario sirven para simular; para guardarlas hay que registrar su origen y
volver a cargar Contabilidad. El servidor rechaza diferencias de importes.

El balance usa movimientos hasta la fecha de corte; los resultados usan solo el
ejercicio. Los resultados de ejercicios anteriores todavía sin asiento de cierre
se incorporan a utilidades acumuladas. Un descuadre impide aprobar. El ejercicio
en curso puede guardarse como borrador, pero no aprobarse antes del cierre.

La tarifa del artículo 52 se aplica sobre toda la renta neta positiva: hasta
C$12 millones de ingresos brutos, 10%, 15%, 20%, 25% o 30% según el estrato de
renta neta; por encima de ese ingreso bruto, 30%. No es una escala marginal.
Las claves históricas `ir_calculado_30` e `ir-pmd-1` se conservan por compatibilidad.
El PMD implementado es 1%, correspondiente al resto de contribuyentes: no cubre
grandes/principales contribuyentes, cuota fija, exenciones ni casos especiales.
La clasificación y documentación fiscal del negocio deben corresponder a ese
supuesto antes de usarlo para una declaración real.

Referencias consultadas:

- [DGI: liquidación del IR, artículo 52](https://www.dgi.gob.ni/FAQ/liquidacion_del_impuesto.htm).
- [Ley 822, publicación oficial](https://www.ine.gob.ni/DGE/digesto/leyes/Ley822.pdf).
- [Ley 987, reforma de 2019, publicación oficial](https://www.mem.gob.ni/wp-content/uploads/2023/08/2019.02.28-Ley-987-Reforma-a-Ley-822-G-41.pdf).

## Carga de demostración 2024 y 2025

El escenario completo se carga con `seed_fiscal_operaciones.py`. Crea las
operaciones de origen y transforma los asientos del escenario inicial dentro
de una sola transacción. Sin `--apply`, valida y revierte los cambios.

```powershell
python seed_fiscal_operaciones.py
python seed_fiscal_operaciones.py --apply
```

Incluye 24 ventas de repuestos y taller con 24 cobros y comprobantes, 24 compras
de repuestos, 24 compras de servicios no inventariables (alquiler, energía y
publicidad), 49 movimientos de inventario y 24 nóminas con sus detalles y pagos.
Los dos empleados ficticios están inactivos, para excluirlos de nóminas actuales.
Los productos físicos DEMO tienen existencias propias; los servicios no generan
entradas ni salidas de inventario. No se alteran productos o empleados anteriores.

La nómina se calcula con `calcular_nomina_empleado` y una instantánea explícita
de parámetros de demostración, sin aplicar retroactivamente los parámetros con
vigencia en 2026 ni modificar su configuración. Las cargas patronales y provisiones
adicionales cambian los resultados respecto al ejemplo inicial solo contable.
Las obligaciones patronales y retenciones laborales quedan provisionadas; no se
simulan sus enteros a las instituciones ni presentaciones oficiales.

La tabla `demo_fiscal_origenes` relaciona documentos y asientos, conserva los
movimientos sustituidos y el soporte del equipo aportado y su depreciación.
El archivo `output/fiscal_demo/operaciones_2024_2025.json` contiene el manifiesto
de la carga aplicada. La pestaña «Respaldo por módulos» se retiró de la interfaz a petición del usuario;
la trazabilidad interna y los documentos operativos se conservan. Una venta genera
ingresos y costo en asientos distintos: no se deben sumar como ingresos.

Resultado del escenario completo, en córdobas:

| Ejercicio | Ingresos | Renta neta | IR determinado | Créditos | Por pagar | A favor |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 2024 | 1,080,000.00 | 167,700.00 | 25,155.00 | 14,400.00 | 10,755.00 | 0.00 |
| 2025 | 1,380,000.00 | 59,500.08 | 13,800.00 | 18,600.00 | 0.00 | 4,800.00 |

Se sustituyen únicamente borradores DEMO. Si ya existe una declaración DEMO
aprobada o presentada, la transformación se cancela. Las repeticiones verifican
la carga completa sin insertar nuevos registros. Cada asiento DEMO cuadra y los
cobros más retenciones concilian con ventas; los pagos de nómina concilian con
los netos. Los anticipos y retenciones originales se conservan sin duplicarlos.

### Escenario inicial solo contable

`seed_fiscal_demo.py` usa la misma base y variable `DB_SERVER` que `app.py`.
Crea únicamente las tablas fiscales faltantes del esquema del repositorio y la
cuenta `1.1.06` (anticipos y retenciones IR). Sin `--apply`, revierte todo.

```powershell
python seed_fiscal_demo.py          # validar y revertir
python seed_fiscal_demo.py --apply  # insertar y confirmar
```

La carga inicial contiene 121 asientos balanceados, 48 acreditamientos ficticios y dos
borradores. Usa `DEMO_FISCAL` como módulo de origen y referencias `DEMO-IR-*`.
Es repetible: no duplica estos registros. Este script inicial no modifica asientos existentes, no
crea ventas o compras operativas y no registra presentaciones ni pagos reales
ante la DGI. Es un escenario contable simplificado, sin IVA ni ciclo de facturas.

| Ejercicio | Ingresos | Renta neta | IR determinado | Créditos | Saldo por pagar |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2024 | 1,080,000.00 | 240,000.00 | 48,000.00 | 14,400.00 | 33,600.00 |
| 2025 | 1,380,000.00 | 180,000.00 | 27,000.00 | 18,600.00 | 8,400.00 |

Importes iniciales en córdobas, sustituidos por la tabla del escenario completo
cuando se ejecuta `seed_fiscal_operaciones.py`. Estos movimientos afectan los saldos acumulados
posteriores, incluyendo 2026; no se deben confundir con datos históricos reales.
El formulario y sus impresiones indican demostración cuando existen estos
asientos hasta la fecha de corte. Los borradores guardan esa marca y la identidad
fiscal disponible como instantánea. No se genera un RUC ficticio si falta configurar.

## Verificación

```powershell
python -m unittest discover -s tests -p test_fiscal.py -v
node tests/fiscal_frontend.cjs
python tests/smoke_fiscal_sqlserver.py
python tests/smoke_fiscal_operaciones.py
```

La última prueba necesita SQL Server y revierte todos sus cambios. Comprueba el
corte por fecha, balances, idempotencia, versiones originales/sustitutivas y la
coherencia de los importes del navegador con el servidor. La presentación se
registra en una sola transacción; un error en la constancia revierte la aprobación.
El sistema registra una constancia aportada por el usuario: no envía declaraciones
a la VET ni obtiene confirmaciones oficiales por sí mismo.
