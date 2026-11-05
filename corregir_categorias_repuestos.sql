-- Correccion de ocho fichas. Repetible; conserva precios, stock y compatibilidad.
SET NOCOUNT ON;
SET XACT_ABORT ON;
SET QUOTED_IDENTIFIER ON;
DECLARE @Correcciones TABLE (sku varchar(50) PRIMARY KEY, categoria nvarchar(100));
INSERT @Correcciones VALUES
('BOM039',N'Sistema de Frenos'),
('BOM046',N'Sistema de Frenos'),
('BOM066',N'Sistema de Frenos'),
('BOM087',N'Sistema de Frenos'),
('BOM067',N'Sistema de Frenos'),
('AMO033',N'Suspensión y Dirección'),
('SIS016',N'Sistema Eléctrico y Encendido'),
('SIS023',N'Sistema Eléctrico y Encendido');
BEGIN TRANSACTION;
IF EXISTS (SELECT 1 FROM @Correcciones x
 WHERE (SELECT COUNT(*) FROM dbo.categorias c WHERE c.nombre=x.categoria) <> 1)
 THROW 50001, 'Falta una categoria de destino o esta duplicada.', 1;
UPDATE p SET categoria_id=c.id, updated_at=GETDATE()
FROM dbo.productos p JOIN @Correcciones x ON x.sku=p.codigo_sku
JOIN dbo.categorias c ON c.nombre=x.categoria
WHERE p.categoria_id IS NULL OR p.categoria_id<>c.id;
SELECT @@ROWCOUNT AS productos_corregidos;
COMMIT;
SELECT p.codigo_sku,p.nombre,c.nombre AS categoria
FROM dbo.productos p JOIN @Correcciones x ON x.sku=p.codigo_sku
JOIN dbo.categorias c ON c.id=p.categoria_id ORDER BY p.codigo_sku;
