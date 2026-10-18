-- Ampliación aditiva de RRHH. No reescribe nóminas ni dotaciones históricas.
IF COL_LENGTH('detalle_nomina', 'historico_salario') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_salario] decimal(12,2) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_nombre') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_nombre] nvarchar(150) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_identificacion') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_identificacion] nvarchar(50) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_cargo') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_cargo] nvarchar(100) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_inss') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_inss] nvarchar(50) NULL;
GO
IF COL_LENGTH('detalle_nomina', 'historico_ingreso') IS NULL
    ALTER TABLE [detalle_nomina] ADD [historico_ingreso] date NULL;
GO
IF COL_LENGTH('higiene_epp', 'area') IS NULL
    ALTER TABLE [higiene_epp] ADD [area] nvarchar(50) NULL;
GO
IF COL_LENGTH('higiene_epp', 'repone_a_id') IS NULL
    ALTER TABLE [higiene_epp] ADD [repone_a_id] int NULL;
GO
IF COL_LENGTH('higiene_epp', 'motivo_reposicion') IS NULL
    ALTER TABLE [higiene_epp] ADD [motivo_reposicion] nvarchar(255) NULL;
GO
IF COL_LENGTH('higiene_riesgos', 'fecha_revision') IS NULL
    ALTER TABLE [higiene_riesgos] ADD [fecha_revision] date NULL;
GO
IF COL_LENGTH('pagos_nomina', 'registrado_por') IS NULL
    ALTER TABLE pagos_nomina ADD registrado_por nvarchar(100) NULL;
GO
IF OBJECT_ID('rrhh_archivos', 'U') IS NULL
BEGIN
CREATE TABLE [rrhh_archivos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [clase] varchar(20) NOT NULL,
    [referencia_id] int NOT NULL,
    [nombre_archivo] nvarchar(255) NOT NULL,
    [mime] varchar(100) NOT NULL,
    [contenido] varbinary(MAX) NOT NULL,
    [registrado_por] nvarchar(100) NOT NULL,
    [fecha_registro] datetime DEFAULT (getdate()) NOT NULL,
    CONSTRAINT [pk_rrhh_archivos] PRIMARY KEY ([id]),
    CONSTRAINT [uq_rrhh_archivo_referencia] UNIQUE ([clase], [referencia_id])
);
END
GO
IF OBJECT_ID('higiene_riesgo_seguimientos', 'U') IS NULL
BEGIN
CREATE TABLE [higiene_riesgo_seguimientos] (
    [id] int IDENTITY(1,1) NOT NULL,
    [riesgo_id] int NOT NULL,
    [fecha_revision] date NOT NULL,
    [observaciones] nvarchar(4000) NOT NULL,
    [estado] nvarchar(30) NOT NULL,
    [registrado_por] nvarchar(100) NOT NULL,
    CONSTRAINT [pk_higiene_riesgo_seguimientos] PRIMARY KEY ([id]),
    CONSTRAINT [fk_seguimiento_riesgo] FOREIGN KEY ([riesgo_id]) REFERENCES higiene_riesgos(id)
);
END
GO
