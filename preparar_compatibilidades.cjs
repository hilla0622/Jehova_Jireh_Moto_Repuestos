// Extrae solo modelos escritos explicitamente; no completa cilindradas abreviadas.
const fs = require('node:fs');
const input = fs.readFileSync('catalogo_compatibilidad_revision.json', 'utf8').replace(/^\uFEFF/, '').replace(/\r?\n/g, '').trim();
const products = JSON.parse(input);
const pattern = /\b(?:CG\s*\d{3}|CGL\s*\d{3}|GN\s*125H?|GS\s*125|EN\s*125|AX\s*100|AX4|YBR\s*125|XTZ\s*125|XR\s*150L?|XR\s*125L?|NXR\s*125|NS\s*200|RS\s*200|AS\s*200|NS\s*125|NS\s*160|N160|FZ\s*16|FZ\s*150|GXT\s*200|GY\s*200|GY6\s*150|WY\s*\d{3}|HJ\s*125(?:-7)?|HJ\s*110|JH\s*\d{3}|TT\s*\d{3}|TTR\s*150|SX\s*\d{3}|CR5|AG\s*200|DR\s*200|XL\s*\d{3}|XT\s*225|CRF\s*230|AN\s*125|CBF\s*150|BM\s*150|CRUX\s*110|RX\s*100|SZ\s*150|RKS\s*150|PULSAR\s*\d{3}|DISCOVER\s*\d{3}|PLATINA\s*\d{3}|GIXXER\s*150)\b/gi;
const quote = s => "N'" + s.replace(/'/g, "''") + "'";
const mapped = [], pending = [];
const additional = /\b(?:APACHE\s*\d{3}|RAYBAR\s*\d{3}|DAYUN\s*\d{3}|YUMBO\s*\d{3}|YARA\s*\d{3}|UM\s*\d{3}|DAKAR\s*\d{3}|GY6\s*125|WR250F|YZ250F|NKD125|CORAL150|LF200|RE205|DY125|ZS150|YBR125ED-G|HONDA NAVI|CB1|HAYATE)\b/gi;
for (const p of products) {
  const matches = [...new Set([...(p.nombre.match(pattern) || []), ...(p.nombre.match(additional) || [])].map(m => m.toUpperCase().replace(/\s+/g, '')).map(m => m.replace(/^PULSAR/, 'Pulsar ').replace(/^DISCOVER/, 'Discover ').replace(/^PLATINA/, 'Platina ').replace(/^GIXXER/, 'Gixxer ')))];
  if (matches.length) mapped.push({...p, modelos: matches.join(' / ')});
  else pending.push(p);
}
const sql = `-- Modelos explicitos del nombre; no certifica versiones ni amplia abreviaturas.
SET XACT_ABORT ON;
SET QUOTED_IDENTIFIER ON;
IF COL_LENGTH('dbo.productos','compatibilidad_fuente') IS NULL
 ALTER TABLE dbo.productos ADD compatibilidad_fuente nvarchar(80) NULL;
GO
DECLARE @Mapa TABLE (sku varchar(50) PRIMARY KEY, nombre nvarchar(200), modelos nvarchar(255));
INSERT @Mapa VALUES
${mapped.map(p => `(${quote(p.codigo_sku)},${quote(p.nombre)},${quote(p.modelos)})`).join(',\n')};
BEGIN TRANSACTION;
UPDATE p SET modelo_compatible=m.modelos,compatibilidad_fuente=N'Nombre del catálogo',updated_at=GETDATE()
FROM dbo.productos p JOIN @Mapa m ON m.sku=p.codigo_sku AND m.nombre=p.nombre
WHERE p.activo=1 AND (NULLIF(LTRIM(RTRIM(p.modelo_compatible)),'') IS NULL
 OR (p.compatibilidad_fuente=N'Nombre del catálogo' AND p.modelo_compatible<>m.modelos));
SELECT @@ROWCOUNT AS compatibilidades_completadas;
-- Diferenciar fichas sin evidencia suficiente para fusionarlas.
UPDATE dbo.productos SET nombre=N'Amortiguadores traseros CG150 par (SKU AMO901)',updated_at=GETDATE()
WHERE codigo_sku='AMO901' AND nombre=N'AMORTIGUADORES TRASEROS CG150 PAR';
UPDATE dbo.productos SET nombre=N'Kit de arrastre CG125 cadena corona y piñón (SKU KIT901)',updated_at=GETDATE()
WHERE codigo_sku='KIT901' AND nombre=N'KIT DE ARRASTRE CG125 CADENA CORONA Y PIÑÓN';
COMMIT;
`;
fs.writeFileSync('normalizar_catalogo_compatibilidades.sql', sql);
fs.writeFileSync('compatibilidades_por_revisar.json', JSON.stringify(pending, null, 2)+'\n');
fs.writeFileSync('catalogo_compatibilidad_revision.json', JSON.stringify(products, null, 2)+'\n');
console.log(JSON.stringify({modelos_explicitos: mapped.length, pendientes_o_por_medida: pending.length}));
