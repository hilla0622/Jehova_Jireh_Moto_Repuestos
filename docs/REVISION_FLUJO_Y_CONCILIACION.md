# Flujo de efectivo y conciliación bancaria: implementación y validación

Base revisada: rama `pruebas-de-migracion`, commit previo `90688bb2b6049068f938203f5c723a1008bf95f0`.
Documento funcional: **Requerimientos Funcionales - Estado de Flujo de Efectivo.pdf**, cuatro páginas, RF96–RF102 y actualización de RF46.

## Cobertura de requisitos

| Requisito | Implementación | Comprobación |
|---|---|---|
| RF96 | Panel para etiquetar cada cuenta como operación, inversión, financiamiento o efectivo; reglas por módulo/tipo de transacción; historial con usuario y motivo. Las cuentas nuevas sin etiqueta que intervienen en efectivo se señalan como pendientes. | Pruebas de configuración, reglas y cuentas sin etiqueta. |
| RF97 | Consulta del asiento y distribución manual del efectivo entre actividades, con importes firmados y motivo. Las distribuciones se aplican a ambos métodos y no pueden exceder sus cobros/pagos reales. | Venta de equipo con ganancia, compra mixta y transferencia con comisión. |
| RF98 | Saldo del mayor por cuenta/corte; saldo bancario obligatorio; ajustes en el lado correcto; pendientes heredadas del último corte anterior; resolución documentada; vínculo opcional al movimiento contable. | Signos, error en libros, resolución, continuidad mensual, conflictos de revisión e historial. |
| RF99 | Reclasificación efectiva y corrección contable mediante un asiento por diferencias, sin borrar el comprobante original; auditoría de antes/después. Tras corregir se exige revisar la clasificación del efectivo original. | Corrección de importe y de cuenta; prevención de corrección duplicada; registro original intacto. |
| RF100 | Ajuste automático configurable en cuentas de resultados no monetarias; ajustes manuales con referencia al movimiento, importe y motivo; sustitución del ajuste automático, no suma duplicada; restauración del automático. | Depreciación, provisión, ajuste parcial incorrecto, sustitución y restauración. |
| RF101 | Métodos directo e indirecto con período explícito, actividades y detalle; guardado recalculado en servidor; instantánea completa consultable. | Compras, ventas, cobros de clientes, pagos a proveedores, financiación, operaciones sin efectivo y corte indirecto persistido. |
| RF102 | Cálculos con Decimal y centavos; saldo inicial + variación = saldo final; comparación con las cuentas de efectivo del mismo mayor y fecha. Se bloquea el guardado si hay diferencias o clasificaciones pendientes. | Centavos, corte temporal, saldo inicial, cambios posteriores a la consulta y comparación entre métodos. |
| RF46 | Exportación HTML de flujo, resultados, balance general y comprobación; impresión/guardado PDF mediante navegador; membrete, período, moneda y espacios de firmas. Los saldos acumulados se cortan en la fecha final; resultados y flujo usan el intervalo. | Prueba de las cuatro exportaciones y vista de flujo en navegador. |

## Reglas importantes para el contador

- El flujo directo toma exclusivamente movimientos de cuentas marcadas como efectivo. Las contrapartidas sirven para clasificarlos, no para fabricar entradas o salidas por operaciones a crédito.
- Una compra de C$10,000 con C$2,000 pagados y C$8,000 financiados genera una salida de C$2,000. La adquisición totalmente a crédito no genera efectivo.
- Las transferencias puras entre cuentas de efectivo no se incluyen. Las transferencias con comisiones y los asientos ambiguos requieren distribución explícita.
- El método indirecto parte del resultado del período y muestra ajustes y cambios operativos identificados. Los cambios de capital de trabajo excluyen operaciones no monetarias no operativas identificables. No se agrega una diferencia residual para aparentar cuadratura.
- Los ajustes manuales sustituyen la contribución automática del movimiento seleccionado al método indirecto. Un cero elimina esa contribución. Una justificación es obligatoria; el importe no puede superar el movimiento de referencia. No son asientos del mayor.
- Una nota bancaria pendiente ajusta la conciliación, pero no altera por sí sola Caja/Bancos ni el flujo. Para reconocerla contablemente se registra el asiento correspondiente y después se documenta la resolución de la partida.
- Los cortes de flujo se conservan como borradores verificados. La interfaz no los presenta como aprobados por alguien que no los aprobó.
- No se permite reescribir una conciliación anterior si ya existen meses posteriores: así se conserva la continuidad de sus pendientes. La corrección/reapertura administrativa de esa cadena no forma parte de esta implementación.
- Las correcciones RF99 actúan en el mayor. No reescriben documentos comerciales, inventario ni obligaciones fiscales de otros módulos.

## Aplicación de la migración

La aplicación requiere la migración **migrar_flujo_v2.py** antes de usar estas rutas. Los scripts SQL históricos del repositorio no se han regenerado con los cambios v2.

1. Probar en una copia de SQL Server con el esquema actual y respaldar la base antes de actualizarla.
2. Si el módulo original no estaba instalado, ejecutar primero `python migrar_modulo_flujo_efectivo.py`. No volver a ejecutarlo sobre una instalación configurada: su etiquetado original puede sustituir reglas de cuentas.
3. Ejecutar `python migrar_flujo_v2.py` usando la misma instancia/base que la aplicación. Acepta `--server` y `--database` para probar primero sobre una copia; también respeta `DB_SERVER`.
4. Reiniciar la aplicación y recargar el navegador; los scripts frontend usan versión `2.0`.
5. Revisar las etiquetas, especialmente subcuentas bancarias, equivalentes y cuentas nuevas; contrastar un mes con el mayor y el extracto.

La migración v2 agrega `ajuste_no_monetario`, la bitácora `flujo_eventos` y un índice único por cuenta/año/mes. Se ejecuta en una transacción y revierte ante errores. Si existen conciliaciones duplicadas, se detiene para que se revisen sin eliminarlas automáticamente. No modifica importes de asientos ni saldos. Las instantáneas de conciliaciones, ajustes, reglas, correcciones y reportes se guardan en la bitácora; las tablas existentes conservan sus cabeceras y detalles.

## Validación ejecutada y límites

```powershell
python -B -m unittest discover -s tests -v
node --check Fronted/static/js/flujo_efectivo.js
node --check Fronted/static/js/flujo_controles.js
```

Pasaron 23 pruebas, varias con escenarios para ambos métodos. Las pruebas de rutas usan una base SQLite en memoria y adaptan únicamente la sintaxis de SQL Server necesaria para comprobar la lógica. Incluyen rollback por fallo simulado. No se conectan a la base del negocio.

La prueba visual `tests/ui_finanzas.cjs` usa Playwright y el servidor `python -B tests/preview_finanzas.py` (puerto local 5087, datos sintéticos). Recorre configuración, consulta de asiento, distribución, método indirecto, guardado, conciliación y exportación, y comprueba que no haya errores JavaScript.

## Migración aplicada el 16 de octubre de 2026

Por solicitud del usuario se aplicó `migrar_flujo_v2.py` en la instancia `HILLARY`, base `jehova_jireh_db`. Se verificaron la nueva columna, la tabla de auditoría y el índice único. Antes y después se conservaron 32 asientos y 138 movimientos, con Debe C$1,881,441.59 y Haber C$1,881,030.59.

Las consultas del flujo directo e indirecto, configuración, conciliación y exportación devolvieron HTTP 200 contra SQL Server. La verificación posterior solo leyó datos: no guardó reportes ni conciliaciones de prueba.

Se identificaron diferencias preexistentes en los asientos 27 (C$240) y 28 (C$171), total C$411. Para el intervalo 2026-08-01 a 2026-10-13, el directo muestra diferencia cero pero bloquea el guardado por esos asientos; el indirecto muestra diferencia de -C$411 y también bloquea el guardado. No se corrigieron esos comprobantes automáticamente.

Queda pendiente la revisión contable de estos registros y el recorrido de escritura con un caso real controlado. Los cambios de código no se han publicado en GitHub. La validación sintética no certifica la exactitud de los registros existentes ni sustituye el criterio del contador en transacciones ambiguas.
