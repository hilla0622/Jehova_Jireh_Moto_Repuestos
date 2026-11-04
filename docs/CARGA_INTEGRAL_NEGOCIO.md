# Historial comercial de Jehová Jireh Moto Repuestos

La carga `seed_negocio.py` crea operaciones relacionadas desde enero de 2024 hasta
el 2 de noviembre de 2026. Los nombres, contactos y operaciones se generan para
la presentación del proyecto; no son una importación de operaciones reales.
Los textos comerciales contienen nombres habituales, referencias de documentos,
conceptos de negocio y repuestos concretos. La procedencia queda en las tablas
técnicas `cargas_negocio`, `carga_negocio_registros` y `carga_negocio_cambios`.

La carga agrega catálogo de lubricantes, bujías, frenos, arrastre, cables, filtros,
llantas, cámaras, baterías, rodamientos y piezas de motor. Incluye clientes
particulares y talleres, proveedores, reposiciones con recepción de mercadería,
ventas de mostrador, pedidos web, pagos, comprobantes, crédito y cobros posteriores,
devoluciones, kardex, aperturas y cierres de caja, depósitos y gastos operativos.

En personal se agregan trabajadores y un antecedente de retiro, contratos,
historial de ingreso, solicitudes de empleo, asistencia, permisos con goce,
vacaciones, horas extras, nóminas, colillas y pagos. También se agregan riesgos,
seguimientos, equipos de protección, capacitaciones, inspecciones e incidentes.
Los importes de nómina reutilizan el motor de cálculo del proyecto y una
instantánea de parámetros documentada en el script.

Los domingos y algunas fechas de cierre no generan ventas. Los días de cobro,
el mes, el crecimiento anual y un factor aleatorio cambian la afluencia. Los
productos tienen distinta rotación; las cantidades, descuentos y métodos de pago
también varían. Los pedidos web completados no se vuelven a insertar en ventas.
Los pedidos pendientes y las compras sin recibir no mueven inventario ni ingresos.

Los registros anteriores se conservan. Se normalizan los textos autorizados y se
guardan sus valores anteriores en `carga_negocio_cambios`. Las cabeceras de nómina
se recalculan al incorporar detalles faltantes, sin reemplazar los detalles previos.
El capital de trabajo inicial contempla la necesidad máxima de efectivo de la
serie y una reserva operativa. El aporte del propietario se registra por partida
doble; no se cambian ventas, costos ni pagos para ocultar un saldo bancario negativo.
En esta carga se autorizó un aporte adicional de C$300,000 al 01/01/2024. El ajuste
se aplicó con `completar_capital_carga.py --apply`, que verifica el importe autorizado,
actualiza solo los borradores propios de la carga y conserva los eventos de flujo
anteriores como historial. La repetición no genera un segundo aporte.

Ocho asientos anteriores solo registraban salario bruto y neto, sin sus
contrapartidas de deducciones. Los importes respaldados por esa diferencia se
registran en `2.1.09 Deducciones de nómina por conciliar`. No se inventa su reparto
entre INSS, IR u otras retenciones. La cuenta se incluye en el formulario fiscal;
su distribución detallada sigue pendiente de los soportes correspondientes.

Las migraciones de flujo existentes se aplican dentro de la misma transacción
para preparar cortes anuales. Las conciliaciones bancarias se conservan como
borradores pendientes de extracto. Las declaraciones de IR también se guardan
como borradores; no se crean presentaciones oficiales ni constancias de la DGI.
No se inventan archivos adjuntos, firmas ni extractos emitidos por terceros.

## Ejecución y respaldo

```powershell
python seed_negocio.py --fin 2026-11-02          # valida y revierte
python seed_negocio.py --fin 2026-11-02 --apply  # valida y confirma si todo cuadra
```

Antes de `--apply` debe existir un respaldo completo verificado, registrado en
`output/carga_negocio/respaldo.json`. El respaldo de esta sesión se creó con
`BACKUP DATABASE ... WITH COPY_ONLY, CHECKSUM` y se comprobó con `RESTORE VERIFYONLY`.
No se sobrescribe el archivo de respaldo que ya estaba en la carpeta del proyecto.

La versión es única: repetir el comando con el mismo período no crea duplicados.
Una segunda ejecución con otro período se rechaza para evitar sobreponer cargas.
Un bloqueo transaccional impide ejecuciones concurrentes de esta misma carga.

Antes del commit se verifican totales de documentos, cobros, stock no negativo,
continuidad cronológica de kardex, inventario valorado, nómina y pagos, arqueos de
caja, asientos balanceados, diversidad mensual y restricciones de SQL Server.
Los registros insertados quedan identificados en el registro técnico de carga.
Cualquier error revierte toda la transacción.

El resultado está en `output/carga_negocio/resultado.json`. La revisión previa
usa `verificacion.json`. Esos archivos y los respaldos contienen información
local del proyecto y no forman parte del código versionado.

Las consultas de historial de ventas, compras, pedidos y asientos se cambiaron a dos
consultas por listado (cabeceras y detalles), evitando abrir una conexión por
documento. El contrato JSON que utiliza la interfaz se conserva.
