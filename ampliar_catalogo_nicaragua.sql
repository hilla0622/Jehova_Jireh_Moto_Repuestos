-- Ejecutar en jehova_jireh_db con SQL Server.
-- Con @Aplicar = 0 solo se revisa el lote. Cambiar @Aplicar a 1 para
-- registrar las fichas con precio de venta informado.
-- Los precios de venta en el lote son sugeridos en C$ (2026-11-04),
-- estimados a partir de productos comparables del catálogo de la tienda y
-- referencias regionales. Cuando no hay costo informado, el esquema del
-- inventario requiere guardar cero hasta que se registre el costo real.
-- Las piezas ingresan con stock cero. Registrar la recepción por inventario.
-- Los códigos OD-* son SKUs internos propuestos. Los códigos YOG-P* incluyen
-- la referencia P* del proveedor. Registrar el costo de la cotización o factura.
-- Comparables de mercado, separados de los campos de carga:
-- Bost Nicaragua publica C$115 para un filtro NS200 sin indicar HAIOSKY.
-- Fuente: https://es.scribd.com/document/943030729/CATALOGO-ACTUALIZADO-TICO
-- Motocentro también lista su referencia P010415 para NS200 sin precio público.
-- Fuente: https://motocentro.com.ni/filtros
-- El C$0.01 publicado en la ficha del CDI XR150 requiere cotización.
-- Fuente: https://comercialortegadiaz.com/cdi-honda-xr150
SET NOCOUNT ON;
SET XACT_ABORT ON;
SET QUOTED_IDENTIFIER ON;

DECLARE @Aplicar bit = 0;
DECLARE @Yog nvarchar(250) = N'https://motocentro.com.ni/wp-content/uploads/2025/02/LOW-CATALOGO-2025-YOG.pdf';
DECLARE @Motor nvarchar(250) = N'https://comercialortegadiaz.com/categoria/motor/';
DECLARE @Frenos nvarchar(250) = N'https://comercialortegadiaz.com/categoria/frenos/';
DECLARE @Controles nvarchar(250) = N'https://comercialortegadiaz.com/categoria/controles/';
DECLARE @Lote TABLE (
    sku varchar(50) PRIMARY KEY,
    nombre nvarchar(200) NOT NULL,
    categoria nvarchar(100) NOT NULL,
    marca nvarchar(100) NOT NULL,
    modelo_objetivo nvarchar(100) NOT NULL,
    fuente nvarchar(250) NOT NULL,
    nota nvarchar(200) NOT NULL,
    modelo_confirmado nvarchar(255) NULL,
    costo decimal(12,2) NULL,
    precio decimal(12,2) NULL
);

INSERT INTO @Lote VALUES
('OD-XR150-FILTRO', N'Filtro de aire XR150 HAIOSKY', N'Motor y Partes Internas', N'HAIOSKY', N'Honda XR150L', @Motor, N'Proveedor lo identifica como XR150. Comparar forma y dimensiones.', NULL, NULL, 180.00),
('OD-XR150-MORDAZA', N'Mordaza de freno delantera XR150 HAIOSKY', N'Sistema de Frenos', N'HAIOSKY', N'Honda XR150L', @Frenos, N'Confirmar año y anclaje con el proveedor.', NULL, NULL, 850.00),
('OD-XR150-CABLEVEL', N'Cable de velocímetro XR150 HAIOSKY', N'Cables y Controles', N'HAIOSKY', N'Honda XR150L', @Controles, N'Confirmar que la versión use cable y comprobar ambos terminales.', NULL, NULL, 125.00),
('OD-XR150-CDI', N'Módulo CDI XR150 HAIOSKY', N'Sistema Eléctrico y Encendido', N'HAIOSKY', N'Honda XR150L', N'https://comercialortegadiaz.com/producto/cdi-honda-xr150/', N'Confirmar conector y versión.', NULL, NULL, 350.00),
('OD-XR150-RECT', N'Rectificador de corriente XR150 HAIOSKY', N'Sistema Eléctrico y Encendido', N'HAIOSKY', N'Honda XR150L', N'https://comercialortegadiaz.com/producto/rectificador-de-corriente-xr150/', N'Confirmar conector y versión.', NULL, NULL, 325.00),
('OD-XR150-ESPEJO', N'Espejo retrovisor XR150 HAIOSKY', N'Chasis y Accesorios', N'HAIOSKY', N'Honda XR150L', N'https://comercialortegadiaz.com/producto/espejo-xr150/', N'Confirmar lado, rosca y unidad de venta.', NULL, NULL, 150.00),
('OD-XR150-TAPON', N'Tapón de tanque XR150 HAIOSKY', N'Carburación y Combustible', N'HAIOSKY', N'Honda XR150L', N'https://comercialortegadiaz.com/producto/tapon-del-tanque-xr150/', N'Confirmar tipo de cierre y año.', NULL, NULL, 450.00),
('YOG-P016691', N'Direccional XR150 YOG P016691', N'Sistema Eléctrico y Encendido', N'YOG', N'Honda XR150L', N'https://motocentro.com.ni/productos/pide-via-honda-xr-150-p016691', N'Confirmar lado, posición y conector.', NULL, NULL, 120.00),
('YOG-P005340', N'Árbol de levas XR150 YOG P005340', N'Motor y Partes Internas', N'YOG', N'Honda XR150L', N'https://motocentro.com.ni/productos/arbola-de-leva-xr-150-dayun-intrepida-cbf150-p005340', N'Proveedor lo identifica como XR150. Confirmar versión del motor.', NULL, NULL, 520.00),
('YOG-P004724', N'Balancín XR150 YOG P004724', N'Motor y Partes Internas', N'YOG', N'Honda XR150L', N'https://motocentro.com.ni/productos/balancin-cbf-150-xr-150-cbf150-dayun-intrepidity-p004724', N'Proveedor lo identifica como XR150. Confirmar posición y motor.', NULL, NULL, 230.00),
('OD-NS200-FILTRO', N'Filtro de aire Pulsar NS200 HAIOSKY', N'Motor y Partes Internas', N'HAIOSKY', N'Pulsar NS200', @Motor, N'Confirmar versión de la caja del filtro.', NULL, NULL, 160.00),
('OD-NS200-CABLECL', N'Cable de embrague Pulsar NS200 HAIOSKY', N'Cables y Controles', N'HAIOSKY', N'Pulsar NS200', @Controles, N'Confirmar largo y terminales.', NULL, NULL, 125.00),
('OD-YBR125-MORDAZA', N'Mordaza de freno delantera YBR125 HAIOSKY', N'Sistema de Frenos', N'HAIOSKY', N'YBR125', @Frenos, N'Solo para la versión con freno delantero de disco que coincida en anclaje.', NULL, NULL, 795.00),
('YOG-P004727', N'Balancín YBR125 YOG P004727', N'Motor y Partes Internas', N'YOG', N'YBR125', @Yog, N'Confirmar posición y versión del motor.', NULL, NULL, 210.00),
('YOG-P009235', N'Mando de manubrio YBR125 YOG P009235', N'Cables y Controles', N'YOG', N'YBR125', @Yog, N'Confirmar lado, conector y unidad de venta.', NULL, NULL, 350.00),
('YOG-P002764', N'Juego de amortiguadores traseros YBR125 YOG P002764', N'Suspensión y Dirección', N'YOG', N'YBR125', N'https://motocentro.com.ni/product-category/repuestos/suspension', N'Confirmar largo entre anclajes.', NULL, NULL, 1150.00),
('YOG-P005167', N'Velocímetro GN125 YOG P005167', N'Sistema Eléctrico y Encendido', N'YOG', N'GN125', @Yog, N'Confirmar versión del tablero.', NULL, NULL, 1250.00),
('YOG-P000993', N'Foco delantero GN125 YOG P000993', N'Sistema Eléctrico y Encendido', N'YOG', N'GN125', @Yog, N'Confirmar base, voltaje y potencia de la bombilla.', NULL, NULL, 160.00);

IF DB_NAME() <> N'jehova_jireh_db'
    THROW 50001, N'Seleccione la base jehova_jireh_db.', 1;

IF @Aplicar = 0
BEGIN
    SELECT l.*,
        CASE
            WHEN NOT EXISTS (SELECT 1 FROM dbo.categorias c WHERE c.nombre = l.categoria)
                THEN N'Categoría por revisar'
            WHEN EXISTS (SELECT 1 FROM dbo.productos p WHERE p.codigo_sku = l.sku OR p.nombre = l.nombre)
                THEN N'Ya registrado'
            ELSE N'Ficha lista para alta sin existencias'
        END AS estado
    FROM @Lote l
    ORDER BY l.modelo_objetivo, l.categoria, l.nombre;
    RETURN;
END;

IF NOT EXISTS (
    SELECT 1 FROM @Lote WHERE precio > 0
)
    THROW 50002, N'Complete el precio de venta para al menos una fila.', 1;

BEGIN TRANSACTION;

IF EXISTS (
    SELECT 1 FROM @Lote l
    WHERE l.precio > 0
      AND (SELECT COUNT(*) FROM dbo.categorias c WHERE c.nombre = l.categoria) <> 1
)
    THROW 50003, N'Alguna categoría del lote falta o está duplicada. Revise antes de importar.', 1;

INSERT INTO dbo.productos
    (codigo_sku, categoria_id, nombre, descripcion, marca, modelo_compatible, costo, precio_venta, stock_actual, activo)
OUTPUT inserted.codigo_sku, inserted.nombre, inserted.stock_actual
SELECT l.sku, c.id, l.nombre,
    CONCAT(l.nota, N' Modelo objetivo: ', l.modelo_objetivo, N'. Referencia: ', l.fuente,
        CASE WHEN l.costo IS NULL THEN N' Costo de compra pendiente de registrar.' ELSE N'' END),
    l.marca, NULLIF(LTRIM(RTRIM(l.modelo_confirmado)), N''), COALESCE(l.costo, 0), l.precio, 0, 1
FROM @Lote l
JOIN dbo.categorias c ON c.nombre = l.categoria
WHERE l.precio > 0
  AND NOT EXISTS (
    SELECT 1 FROM dbo.productos p WITH (UPDLOCK, HOLDLOCK)
    WHERE p.codigo_sku = l.sku OR p.nombre = l.nombre
  );

COMMIT TRANSACTION;
