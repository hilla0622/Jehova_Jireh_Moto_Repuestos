# RRHH: pagos, documentos y seguridad e higiene

## Cambios

- Pagos: formulario con nómina, trabajador, saldo pendiente, importe, fecha, método y referencia. El servidor valida el importe y la pertenencia a la nómina, evita referencias repetidas por método y bloquea sobrepagos. Admite pagos parciales. Usa `registrado_por`, compatible con el esquema entregado. Los bloqueos de la cabecera serializan pagos frente a generación y anulación.
- Nómina: los nuevos detalles guardan nombre, identificación, cargo, INSS, fecha de ingreso y salario contractual del momento. Los recibos ya no sustituyen cero días o cero vacaciones por valores predeterminados. Los registros anteriores sin esta copia se identifican como incompletos en la API y llevan una nota en la colilla impresa; no se inventa su historia contractual.
- Expedientes: carga real de PDF, PNG y JPG de hasta 5 MB, descarga restringida a los roles de RRHH y almacenamiento binario en `rrhh_archivos`. Los antiguos nombres sin contenido se muestran como referencias, no como documentos digitalizados. Archivos y metadatos se guardan en una transacción.
- EPP: entregas con empleado, equipo, área, cantidad, estado, fechas, observaciones y constancia opcional. Las reposiciones enlazan una nueva entrega con la anterior y conservan el historial. Cada reposición reemplaza toda la cantidad de la entrega seleccionada; no admite reposiciones parciales. Hay detalle, historial por empleado, filtros de área/período y exportación CSV de la vista actual. Las reposiciones pendientes son las entregas sin reemplazo cuya fecha prevista ya llegó.
- Riesgos: alta, edición, filtros por área/responsable, nivel y estado, y revisiones con fecha, observaciones y responsable. Una revisión atrasada queda en el historial sin reemplazar el estado de una revisión más reciente. Las propuestas del texto aportado por el usuario están disponibles como puntos de partida; no se guardan automáticamente ni sustituyen una evaluación. Los registros existentes se conservan.

## Base de datos

`migrar_rrhh_control.py` aplica `migracion_rrhh_control.sql` en una transacción. Es una migración aditiva e idempotente: agrega campos a `detalle_nomina`, `higiene_epp` y `higiene_riesgos`, y crea `rrhh_archivos` y `higiene_riesgo_seguimientos`. Se agrega `pagos_nomina.registrado_por` si la instalación antigua solo tenía `usuario_responsable`. `database.sql` incluye el esquema actualizado y la ampliación para bases existentes.

Aplicada a la base local durante esta revisión. No se crearon pagos, nóminas, dotaciones ni riesgos ficticios en las tablas del negocio. La base de datos debe incluirse en los respaldos para conservar los documentos adjuntos.

## Verificación

- `python -B -m unittest discover -s tests -v`: 48 pruebas, 25 de RRHH. SQLite en memoria, con bloqueo explícito de conexiones reales.
- `python -B tests/smoke_rrhh_sqlserver.py`: integración real con SQL Server utilizando exclusivamente tablas temporales. Incluye nómina, copia histórica, pagos, EPP, reposiciones, riesgos, revisiones y archivos binarios. No es una prueba de carga concurrente.
- `tests/preview_rrhh.py` y `tests/ui_rrhh.cjs`: prueba de formularios y descargas en navegador con datos ficticios, en escritorio y móvil.
- Lectura de los endpoints principales contra la base local tras la migración.

No se cambiaron las tasas laborales ni se certificó cumplimiento normativo. Las propuestas de riesgos y sus niveles son orientativos, según el material proporcionado.
