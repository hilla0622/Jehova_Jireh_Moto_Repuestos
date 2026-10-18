# Datos de demostración de Recursos Humanos

Carga aplicada el 18 de octubre de 2026 en la base SQL Server configurada por la aplicación.
Se conservaron los cinco empleados activos y los registros anteriores. Los datos nuevos
incluyen la marca `[DEMO-RRHH-2026]` o el responsable `Demo académica`.

## Recorrido para presentar

- Personal: cinco empleados; se completaron campos vacíos de dirección, fecha de nacimiento,
  contacto de emergencia y jornada. Los datos complementarios son ficticios; los teléfonos
  de emergencia `0000-*` son de muestra y no deben utilizarse como contactos reales.
- Contratos: cinco en total. Se agregaron los dos empleados que no tenían contrato.
- Expedientes: una ficha de inducción PDF descargable por empleado, además de los registros anteriores.
- Historial laboral: cinco asignaciones iniciales de jornada.
- Asistencia: seleccionar **15, 16 o 17 de octubre de 2026**. Se agregaron trece registros,
  respetando las asistencias y ausencias preexistentes.
- Horas extras: dos registros de una hora por recepción de mercadería; usan el parámetro
  de recargo configurado en la base y corresponden a salidas extendidas en la asistencia.
- Seguridad: un incidente sin lesiones, dos entregas de EPP para bodega, una capacitación
  para cinco participantes, una inspección y un seguimiento de riesgo nuevos.
- Solicitudes de empleo, cargos, jornadas, movimientos, nóminas, pagos, liquidaciones,
  parámetros y calendario ya tenían información; se conservaron.

No se modificaron salarios, saldos de vacaciones, cálculos legales ni registros de pagos.
No se inventaron bajas ni vencimientos para llenar campos que no correspondían.
Los PDF son muestras académicas sin firmas, sellos ni validez oficial.

## Datos anteriores que conviene revisar

Los contratos antiguos de los empleados 1, 2 y 3 contienen cargos o salarios distintos
de sus fichas actuales. Se conservaron: esta carga no interpreta esos contratos como
una autorización para modificar remuneraciones o historia laboral. Los adjuntos antiguos
que solo guardaban un nombre de archivo siguen así; los cinco PDF nuevos sí se descargan.

## Repetir y verificar

`python seed_rrhh_demo.py` prueba toda la carga y revierte la transacción.
`python seed_rrhh_demo.py --apply` confirma los cambios. Requiere las dependencias
de la aplicación, reportlab y acceso a SQL Server. Está preparado para el escenario
revisado de cinco empleados activos; no debe ejecutarse indiscriminadamente en otra base.

El manifiesto `output/rrhh_demo_manifest.json` conserva los identificadores insertados
y los valores anteriores de los campos complementados. Los PDF están en `output/pdf/`.
La carga repetida después de aplicarla produjo cero inserciones y cero actualizaciones.

Se corrigieron lecturas de campos en las tablas de contratos, jornadas, historial,
incidentes, capacitaciones y marco legal, y la serialización de horas de asistencia.
Verificación: 25 pruebas de RRHH aprobadas; consultas autenticadas satisfactorias;
cinco descargas PDF verificadas; cinco funciones de presentación probadas con datos
de la base sin valores `undefined` o `NaN`. PDF renderizados y revisados visualmente.
Las correcciones de código requieren reiniciar el servidor si no recarga automáticamente.

## Nómina de horas extras

Las horas extras aprobadas se suman al bruto del mes al generar la nómina, recalculando
INSS, IR, neto, aportes patronales y provisiones. Si se registran después de cerrar la
nómina, el formulario las incorpora de inmediato cuando todavía no existe un pago para
el trabajador. También se puede usar **Incluir horas extras pendientes** desde el detalle
de nómina. El sistema enlaza cada hora con su nómina para impedir que se cobre dos veces
y registra el asiento de ajuste.

La hora aprobada de Juan del 2 de septiembre de 2026 se incorporó a la nómina #3 porque
no había un pago registrado para él en ese período. Su ingreso extra ahora figura como
C$100.00 y su neto pasó de C$10,736.00 a C$10,815.05. Se creó el asiento contable del
ajuste, balanceado por C$0.00. Las nóminas con pagos ya registrados requieren registrar
el faltante como pago complementario para preservar el comprobante original.
