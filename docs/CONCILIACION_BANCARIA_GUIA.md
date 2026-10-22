# Conciliación bancaria por movimientos

La pantalla sigue el ejemplo del video proporcionado: revisar el estado del banco contra el auxiliar contable de la empresa, vincular coincidencias y explicar las diferencias con un papel de trabajo que parte del banco y llega a libros.

## Uso

1. Seleccionar una cuenta bancaria y un mes. El auxiliar de la empresa se obtiene del mayor: saldo inicial, entradas (Debe), salidas (Haber), saldo de cada movimiento y saldo final.
2. Copiar los saldos inicial y final del extracto y agregar sus movimientos con fecha, concepto, referencia opcional, tipo e importe. Se ordenan por fecha; los movimientos del mismo día mantienen el orden de captura. Si se transcribe un importe incorrecto, quitar primero su vínculo o diferencia, eliminar la fila y agregarla de nuevo.
3. Marcar coincidencias exactas. Solo se vinculan automáticamente importes del mismo sentido y fecha que sean únicos en ambos lados. Revisar los conceptos. Las coincidencias con fechas diferentes se vinculan seleccionando una fila de cada tabla. Un movimiento solo puede pertenecer a un vínculo.
4. Usar **Solo banco** o **Solo empresa** en los movimientos ausentes del otro estado. La fecha, importe y origen de la diferencia quedan vinculados a la fila. El paso 3 agrupa los cuatro tipos y permite consultar sus referencias y explicaciones.
5. Revisar el papel de trabajo y guardar. La conciliación se considera revisada cuando el extracto reproduce su saldo final, no quedan movimientos del mes sin revisar y la diferencia aritmética es cero. Un trabajo incompleto se guarda como borrador.

El vínculo uno a uno exige el mismo importe y sentido; no admite dividir un depósito entre varios cobros ni agrupar varios movimientos. La captura del extracto es manual: no se importan PDF, imágenes, Excel ni archivos bancarios en esta versión.

## Ejemplo verificado

Las imágenes muestran un saldo inicial de 78,000 en ambos estados, banco final de 35,500 y empresa final de 28,000. La comisión de la imagen es **1,500**; la transcripción dice 10,000 en ese pasaje y es inconsistente con el estado de cuenta.

| Paso desde el saldo bancario | Importe |
| --- | ---: |
| Saldo final del banco | 35,500.00 |
| + Retiro bancario no registrado en la empresa | 1,500.00 |
| + Entrada de la empresa no reflejada por el banco | 16,000.00 |
| − Depósito bancario no registrado en la empresa | 5,000.00 |
| − Salida de la empresa no reflejada por el banco | 20,000.00 |
| Saldo en conciliación | 28,000.00 |
| Saldo de la empresa | 28,000.00 |
| Diferencia pendiente | 0.00 |

Hay 15 movimientos en cada estado, 13 pares coincidentes y cuatro diferencias. El pago de mercadería aparece el 1 de enero en la empresa y el 2 de enero en el banco; se vincula manualmente. El importe de 35,000 de entrada no se confunde con el retiro del mismo monto.

La interfaz presenta los importes en C$, como el resto del sistema. Los datos del video se utilizan únicamente en pruebas, nunca se insertan en la base del negocio.

## Pendientes y correcciones

Guardar no crea asientos ni modifica documentos de otros módulos. Una comisión o un cobro faltante requiere el registro contable correspondiente. Luego se marca la diferencia como resuelta y se documenta la referencia. Al recargar el mayor, puede vincularse el movimiento nuevo con el del banco.

Los pendientes se arrastran al siguiente corte; el extracto y sus vínculos pertenecen únicamente al mes original. Un cheque o depósito de un período anterior aparece en el auxiliar como pendiente separado, sin sumarlo otra vez al saldo. Puede vincularse al movimiento del extracto actual, quedando resuelto con su referencia. Las notas bancarias anteriores pueden vincularse al movimiento contable de resolución del mes mediante un selector.

Las diferencias heredadas no pueden eliminarse ni cambiarse de importe. Los cortes que tienen meses posteriores quedan bloqueados en pantalla y servidor. Para las nuevas versiones, la vista histórica usa los movimientos y saldos de la empresa guardados en ese momento. Los cortes antiguos que carecen de esa instantánea conservan el comportamiento previo.

Las conciliaciones anteriores por saldos siguen siendo legibles. La pantalla informa que necesitan completar el extracto para adoptar la revisión por movimientos.

## Persistencia y comprobación

No requiere una migración nueva: el extracto, los vínculos, el control de revisión y la instantánea del mayor se guardan en la bitácora `flujo_eventos`, junto con las partidas. Se conservan las tablas y la migración v2 ya usadas por el módulo. El servidor recalcula saldos, valida tipos, fechas y enlaces, rechaza revisiones obsoletas y guarda en una transacción.

Pruebas automatizadas: `test_flujo.py` (23 casos existentes) y `test_conciliacion.py` (10 casos del nuevo cotejo). Usan SQLite en memoria con adaptador de SQL Server; no certifican una instalación real de SQL Server. El ejemplo compartido está en `tests/ejemplo_conciliacion.py`.

Vista de prueba local: `python -B tests/preview_finanzas.py --conciliacion`, puerto 5088. Requiere Flask. Su base es sintética y se descarta al detener el servidor. El recorrido en navegador verificó captura manual, coincidencias, vínculo con diferente fecha, clasificación de las cuatro diferencias, guardado y recuperación después de recargar.
