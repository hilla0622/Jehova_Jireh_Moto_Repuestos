# Comparación de los requerimientos actualizados de Recursos Humanos

Revisión del 18 de octubre de 2026 del documento «Proyecto Corte 2 - Actualizado.docx», sección 1.6, frente al código actual de Jehová Jireh Moto Repuestos, incluidas las correcciones de esta conversación.

Se identificaron 48 requerimientos, RF80 a RF127. El texto relevante usa los colores azules OOXML `1F3864`, `1F497D` y `002060`. Se tomó la descripción completa de cada requerimiento, no los números RF de los comentarios del código, que corresponden a una numeración anterior.

Resultado funcional: 27 cubiertos, 19 parciales y 2 sin el flujo requerido. «Cubierto» significa que existe la funcionalidad solicitada con evidencia en código y, cuando se indica, pruebas; no equivale a una certificación exhaustiva ni normativa. «Parcial» significa que existe una parte útil pero falta al menos una condición expresa del documento. No es correcto declarar que el módulo cumple el 100 %.

Por instrucción del usuario no se considera incumplimiento el valor de 1.25 días. Esa cifra aparece en el párrafo introductorio del RF91; la descripción de la tabla ya pide acumulación según tiempo trabajado y parámetros, evitando duplicados. El código utiliza por defecto 2.5 días para el mes completo y calcula proporciones.

## Matriz completa

| RF | Requerimiento | Resultado | Evidencia y pendiente |
|---|---|---|---|
| 80 | Registro de empleados | Cubierto | API y formulario con nombre, cédula, INSS, cargo, salario, ingreso, contacto y observaciones. |
| 81 | Listado de empleados | Cubierto | Directorio con identificador, datos laborales, salario, vacaciones y estado. |
| 82 | Actualización del empleado | Cubierto | Formulario y PUT protegido para modificar datos personales y laborales. La auditoría completa se evalúa por separado en RF112. |
| 83 | Estado activo/inactivo | Cubierto | PATCH cambia el estado sin borrar al empleado ni sus registros anteriores. |
| 84 | Filtro por estado | Cubierto | Opciones para todos, activos e inactivos. |
| 85 | Gestión de cargos | Parcial | Registra y edita nombre, descripción y salario sugerido; faltan responsabilidades y área como datos gestionados del cargo. |
| 86 | Registro de vacaciones | Cubierto | Selección de empleado, fechas, días y observación. La aprobación previa se evalúa en RF116. |
| 87 | Registro de permisos | Cubierto | Permisos con y sin goce, fechas, días y motivo. |
| 88 | Registro de faltas | Cubierto | Movimiento independiente de falta con fechas, días y observación. |
| 89 | Cálculo automático de días | Cubierto | La pantalla calcula el intervalo inclusivo al cambiar las fechas. El servidor aún confía en los días enviados; conviene reforzarlo, aunque la automatización solicitada sí existe en la interfaz. |
| 90 | Saldo de vacaciones | Cubierto | Acumula con nómina, descuenta vacaciones y reintegra al eliminar movimientos. La transacción del alta de vacaciones merece refuerzo: inserción y descuento se confirman por separado. |
| 91 | Acumulación de vacaciones | Cubierto | Parámetro configurable, proporcionalidad y protección contra duplicación por empleado/período. Se excluye la cifra introductoria de 1.25 por indicación del usuario. |
| 92 | Historial de vacaciones, permisos y faltas | Cubierto | Consulta de movimientos con empleado, tipo, fechas, días y observaciones. |
| 93 | Selección del período | Cubierto | Mes y año en generación de nómina. |
| 94 | Nómina general | Cubierto | Procesa empleados activos elegibles y excluye quienes ingresaron después del período. |
| 95 | Salario devengado | Cubierto | Usa salario base y ajustes del período; incorpora horas extra aprobadas. |
| 96 | INSS laboral | Cubierto | Cálculo parametrizado con valor predeterminado de 7 %. |
| 97 | IR | Cubierto | Tabla progresiva incorporada y cálculo automático. Se verifica existencia funcional, no actualización normativa. |
| 98 | Provisiones laborales | Cubierto | Cálculo y almacenamiento de provisiones de vacaciones y aguinaldo. |
| 99 | Total de deducciones | Cubierto | Consolidación de INSS e IR en la nómina generada. Los conceptos adicionales generales se evalúan en RF118. |
| 100 | Salario neto | Cubierto | Resta deducciones de las percepciones. |
| 101 | INSS patronal separado | Cubierto | Se calcula y registra separado del descuento al trabajador. |
| 102 | Historial de nóminas | Cubierto | Período, generación, bruto, deducciones, neto, INSS patronal y estado. |
| 103 | Detalle de nómina | Cubierto | Consulta general e individual de los empleados incluidos. |
| 104 | Colilla individual completa | Parcial | Genera datos y montos, pero `vac_descansados` no se llena al generar nómina. Prueba con tres días de vacaciones devuelve cero días disfrutados en la colilla. Las nuevas copias contractuales no resuelven este campo pendiente. |
| 105 | Impresión de colilla | Cubierto | Vista imprimible por detalle, con espacios de firma del trabajador y de RRHH. |
| 106 | Solicitudes de empleo | Parcial | Registra información y correlativo; falta adjuntar el currículum a la solicitud del aspirante. El expediente de un empleado no sustituye ese adjunto. |
| 107 | Consulta y seguimiento de aspirantes | Parcial | Listado, estados y observaciones existentes; no hay búsqueda implementada por nombre, puesto, fecha o estado. |
| 108 | Expediente digital | Cubierto | Archivos reales PDF/PNG/JPG, asociación al trabajador, fecha, usuario y acceso privado. Los registros antiguos sin contenido se distinguen de los archivos descargables. |
| 109 | Contratos laborales | Parcial | Hay formulario y documento imprimible, y se pueden adjuntar contratos firmados al expediente. El formulario envía `salario`, pero la API lee `salario_mensual`: en la prueba guarda cero. Funciones y forma de pago enviadas por la pantalla no se persisten en ese POST; el lugar se toma del valor predeterminado. La salida es HTML para imprimir, no una generación PDF propia. |
| 110 | Vigencia y renovación de contratos | Parcial | Lista estados almacenados, pero el botón de renovación llama una ruta inexistente y responde 404. No se implementa el ciclo completo de firma, vencimiento, alertas y prórrogas con historial. |
| 111 | Afiliación al INSS | Parcial | Número de asegurado y documentos en expediente. Hay columnas de régimen/alta/estado en el esquema, pero no un flujo completo que las gestione, registre la baja y conserve movimientos de afiliación. |
| 112 | Historial de modificaciones laborales | Parcial | Hay tabla, API y consulta de historial. Editar salario o cargo desde empleados no crea automáticamente la entrada anterior/nueva con vigencia, motivo y responsable. Jornada y área tampoco quedan integradas al flujo. |
| 113 | Jornadas laborales | Parcial | Catálogo con horarios y descansos; falta asignación operativa al empleado e integración de la jornada con asistencia e incidencias de nómina. |
| 114 | Asistencia | Parcial | Registra entradas, salidas y estado manual. No calcula incidencias desde la jornada ni tiene el ciclo de revisión/corrección. “Marcar salida” envía un ID al POST de alta: el servidor lo ignora e intenta insertar con empleado 0, en vez de actualizar la asistencia existente. |
| 115 | Horas extraordinarias | Parcial | Registra horas, motivo, usuario, recargo e importe, y las incluye en nómina. La base horaria es fija (salario/240), no depende de la jornada asignada. Se guardan aprobadas directamente, sin revisión posterior separada. |
| 116 | Solicitud y aprobación de vacaciones/permisos | No cumple | Se registran movimientos definitivos y las vacaciones descuentan saldo inmediatamente. No existe el flujo de solicitud Pendiente/Aprobada/Rechazada con revisor y respaldos asociado al movimiento. |
| 117 | Clasificación y justificación de ausencias | Parcial | Reconoce falta y permisos con/sin goce. Faltan incapacidades y otras ausencias justificadas como categorías, respaldos vinculados y estado de revisión. |
| 118 | Ingresos y deducciones adicionales | No cumple | No existe el flujo general por concepto, monto, período, respaldo y responsable para comisiones, bonos y deducciones. Columnas en la base y horas extra agregadas no cubren ese registro individual. |
| 119 | Liquidaciones laborales | Parcial | Calcula componentes y ofrece documento imprimible. Se guarda como Borrador, pero falta aprobación y control que impida generar un documento final antes de aprobarlo. No se certificaron las fórmulas legales. |
| 120 | Pagos de nómina | Parcial | Registra pagos, referencia y saldo pendiente, con controles de duplicación y sobrepago. Falta comprobar aprobación de la nómina, adjuntar comprobante de pago y vincular el desembolso a su asiento contable. El asiento de generación de nómina no sustituye al asiento del pago. |
| 121 | Riesgos laborales | Cubierto | Área, tipo, descripción, nivel, medidas y responsable; además edición, filtros, propuestas e historial de revisiones. |
| 122 | Accidentes e incidentes | Parcial | API de registro y consulta básica. Faltan documentos de respaldo y actualización del seguimiento hasta cierre. La pantalla espera `descripcion_suceso` y `estado_caso`, distintos de los campos entregados por la API. |
| 123 | Entrega de EPP | Cubierto | Empleado, equipo, cantidad, fechas, estado e historial; reposiciones vinculadas y constancia opcional. Las reposiciones actuales sustituyen toda la cantidad del registro seleccionado. |
| 124 | Capacitaciones | Parcial | API para actividad, fecha, facilitador y conteo de asistentes. Faltan empleados participantes identificados y documentos acreditativos; la interfaz consulta nombres de campos diferentes de los de la API. |
| 125 | Inspecciones y medidas | Parcial | Lista de seis puntos, observaciones, medidas y resultado. Faltan responsable específico de las acciones, fecha de cumplimiento y seguimiento de su ejecución. El inspector no sustituye al responsable de la acción correctiva. |
| 126 | Marco legal consultable | Parcial | API con ley, artículo, tema, resumen y enlace. La pantalla espera otra estructura y falla al acceder a `articulos_clave.map`; tampoco implementa las búsquedas solicitadas por normativa, tema y artículo. |
| 127 | Parámetros legales y laborales | Parcial | Edición de valores, usuario y fecha; las nóminas guardadas no se recalculan. No hay versiones seleccionadas por período: se usa el valor actual aun al generar un período anterior. La tabla progresiva de IR continúa fija en código y la referencia normativa no se administra desde el flujo de edición. |

## Comprobaciones específicas de esta revisión

Se usaron datos ficticios en SQLite en memoria, bloqueando las conexiones reales. No se cambiaron el sistema, el documento ni los datos del negocio.

1. `PUT /api/rrhh/contratos/1/estado`: HTTP 404.
2. Alta de contrato con el JSON que envía la pantalla (`salario: 15000`): HTTP 201, `salario_mensual` guardado en cero.
3. Movimiento de vacaciones de tres días y generación de nómina: `vac_descansados` de la colilla devuelve 0.
4. Marco legal: la API devuelve `articulo`, `enlace`, `ley`, `resumen`, `tema`; la pantalla espera `articulos_clave`, entre otros campos distintos.
5. Petición de “Marcar salida” con `{id: 1, hora_salida: '17:00'}`: inserta una asistencia para empleado 0 en el adaptador sin claves foráneas. En una instalación con esa restricción puede fallar; no actualiza la entrada original.

Las 48 pruebas de regresión y las comprobaciones SQL Server/UI realizadas en el turno anterior validan los flujos cubiertos por ellas; no prueban que se satisfagan todos los nuevos requerimientos del documento.

## Orden recomendado para completar el módulo

Primero corregir contratos, renovación, salida de asistencia, vacaciones disfrutadas en colilla y renderizado del marco legal. Después completar aprobaciones de movimientos y liquidaciones, conceptos adicionales y pagos con comprobantes/contabilidad. Finalmente integrar afiliación, jornadas, auditoría laboral, capacitaciones e incidentes, y parámetros versionados por vigencia.

## Evidencia del código

- [Empleados, cargos, movimientos y nómina](C:/Users/arana/Downloads/Jehova_Jireh_Moto_Repuestos/app.py:2276).
- [Solicitudes, contratos, asistencia, liquidaciones y parámetros](C:/Users/arana/Downloads/Jehova_Jireh_Moto_Repuestos/routes_corte_v.py:24).
- [Pagos, archivos, EPP y riesgos](C:/Users/arana/Downloads/Jehova_Jireh_Moto_Repuestos/routes_rrhh_control.py:57).
- [Interfaz de contratos, asistencia y marco legal](C:/Users/arana/Downloads/Jehova_Jireh_Moto_Repuestos/Fronted/static/js/corte_v.js:1293).
- [Directorio, movimientos y colillas](C:/Users/arana/Downloads/Jehova_Jireh_Moto_Repuestos/Fronted/templates/index.html:4511).
- [Cálculo de nómina](C:/Users/arana/Downloads/Jehova_Jireh_Moto_Repuestos/calculos_rrhh.py:110).
