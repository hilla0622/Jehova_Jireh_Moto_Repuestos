# Correcciones de RRHH — 17 de octubre de 2026

## Comportamiento

- La generación incluye las horas extra aprobadas del empleado y período, registradas antes de generar la nómina. Los ingresos adicionales quedan guardados en el detalle y aparecen en las colillas.
- Las ausencias se seleccionan por intersección de fechas. Los días registrados se distribuyen proporcionalmente por los días calendario del intervalo inclusivo; también se admiten fracciones. Un movimiento de cuatro días del 30 de enero al 2 de febrero descuenta dos días en cada mes. El ajuste de séptimo día marcado en un movimiento se aplica una sola vez, en el mes de su fecha final.
- Se registra INATEC por pagar en 2.1.10 y se verifica el balance antes de confirmar. Las cuentas faltantes se crean dentro de la transacción: 6.1.01, 6.1.11, 6.1.12, 2.1.04, 2.1.06, 2.1.07, 2.1.08 y 2.1.10. Una cuenta inactiva o una 2.1.10 ocupada por otro concepto detiene la operación.
- La anulación conserva los asientos originales y genera contrapartidas con origen `RRHH_ANULACION`. Revierte vacaciones y elimina los detalles sin depender de cascadas. Se rechaza si hay pagos confirmados o si revertir las vacaciones dejaría saldo negativo.
- Los parámetros se muestran en porcentajes convencionales (7 significa 7%). Se admite tanto el esquema `codigo` como el antiguo `clave`, con conversión de fracciones y del factor de horas extra. Se usan en INSS, INATEC, provisiones, vacaciones acumuladas y recargo de horas extra. El parámetro de salario mínimo sigue siendo informativo; no modifica contratos. La tabla de IR no se cambió.
- La vista previa usa el mismo cálculo del servidor. Los cambios de parámetros se aplican en nuevas operaciones, no recalculan nóminas guardadas ni horas extra ya aprobadas.
- Administrador, Responsable de Recursos Humanos y Gerente Administrativo y Financiero comparten acceso a RRHH. Los demás roles no pueden consultar empleados ni las rutas privadas de RRHH.

## Verificación

`python -B -m unittest discover -s tests -v`: 39 pruebas, incluidas 16 regresiones de RRHH. Datos ficticios en SQLite; el adaptador no verifica bloqueos de SQL Server.

`python -B tests/smoke_rrhh_sqlserver.py`: integración en SQL Server con tablas temporales en una conexión aislada. Comprueba parámetros, horas extra, ausencias, generación, creación de cuentas, balance, anulación y regeneración. Al cerrar la conexión se eliminan las tablas temporales. No modifica las tablas del negocio.

Los cambios no reparan automáticamente los asientos ni las nóminas históricas generadas con la versión anterior. No se certificó cumplimiento normativo ni se alteraron las tasas configuradas del negocio.
