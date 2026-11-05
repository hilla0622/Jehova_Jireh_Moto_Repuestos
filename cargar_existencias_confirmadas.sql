-- Cantidades y costos inicialmente propuestos, confirmados como reales por el usuario
-- en el chat del 2026-11-04. No representa una factura de proveedor.
-- Requiere las 18 fichas de ampliar_catalogo_nicaragua.sql.
-- Solo completa existencias/costos en cero; conserva cambios manuales.
SET NOCOUNT ON;
SET XACT_ABORT ON;
SET QUOTED_IDENTIFIER ON;
IF DB_NAME() <> N'jehova_jireh_db'
    THROW 50001, 'Selecciona jehova_jireh_db.', 1;
DECLARE @Lote TABLE (sku varchar(50) PRIMARY KEY, cantidad int, costo decimal(12,2), venta decimal(12,2));
INSERT @Lote VALUES
('OD-NS200-CABLECL',18,89.29,125),
('OD-NS200-FILTRO',12,114.29,160),
('OD-XR150-CABLEVEL',10,89.29,125),
('OD-XR150-CDI',5,250.00,350),
('OD-XR150-ESPEJO',8,107.14,150),
('OD-XR150-FILTRO',12,128.57,180),
('OD-XR150-MORDAZA',4,607.14,850),
('OD-XR150-RECT',5,232.14,325),
('OD-XR150-TAPON',6,321.43,450),
('OD-YBR125-MORDAZA',4,567.86,795),
('YOG-P000993',10,114.29,160),
('YOG-P002764',4,821.43,1150),
('YOG-P004724',6,164.29,230),
('YOG-P004727',6,150.00,210),
('YOG-P005167',4,892.86,1250),
('YOG-P005340',4,371.43,520),
('YOG-P009235',5,250.00,350),
('YOG-P016691',8,85.71,120);
DECLARE @Ajustes TABLE (producto_id int, anterior int, posterior int);
BEGIN TRANSACTION;
IF (SELECT COUNT(*) FROM dbo.productos p WITH (UPDLOCK,HOLDLOCK) JOIN @Lote l ON l.sku=p.codigo_sku) <> 18
    THROW 50002, 'Faltan fichas o existen SKU duplicados.', 1;
UPDATE p SET stock_actual=l.cantidad, updated_at=GETDATE()
OUTPUT inserted.id,deleted.stock_actual,inserted.stock_actual INTO @Ajustes
FROM dbo.productos p JOIN @Lote l ON l.sku=p.codigo_sku
WHERE p.stock_actual=0 AND p.activo=1
AND NOT EXISTS (SELECT 1 FROM dbo.movimientos_inventario m
 WHERE m.producto_id=p.id AND m.referencia_origen='CONFIRMADO-18-20261104');
UPDATE p SET costo=CASE WHEN p.costo=0 THEN l.costo ELSE p.costo END,
 precio_venta=CASE WHEN p.precio_venta=0 THEN l.venta ELSE p.precio_venta END,
 updated_at=GETDATE()
FROM dbo.productos p JOIN @Lote l ON l.sku=p.codigo_sku
WHERE p.costo=0 OR p.precio_venta=0;
INSERT dbo.movimientos_inventario
(producto_id,tipo_movimiento,cantidad,stock_anterior,stock_posterior,referencia_origen,motivo,usuario_id)
SELECT producto_id,'AJUSTE_ENTRADA',posterior-anterior,anterior,posterior,
'CONFIRMADO-18-20261104','Carga por script: cantidades y costos propuestos confirmados por el usuario en chat 2026-11-04.',1
FROM @Ajustes;
COMMIT;
SELECT p.codigo_sku,p.stock_actual,p.costo,p.precio_venta
FROM dbo.productos p JOIN @Lote l ON l.sku=p.codigo_sku ORDER BY p.codigo_sku;
SELECT COUNT(*) AS productos_ajustados,SUM(posterior-anterior) AS unidades_agregadas FROM @Ajustes;
