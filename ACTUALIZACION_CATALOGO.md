# Moneda, fichas y compatibilidades

## Actualizacion de una base existente del equipo

Ejecutar en SQL Server, sobre la base del proyecto, en este orden:

1. `ampliar_catalogo_nicaragua.sql`: revisar el lote y cambiar `@Aplicar` a `1` para crear las 18 fichas faltantes.
2. `cargar_existencias_confirmadas.sql`: cargar las existencias iniciales y costos confirmados. Conserva stock existente y no repite el ajuste ya registrado.
3. `corregir_categorias_repuestos.sql`.
4. `actualizar_nombre_compras.sql`.
5. `normalizar_catalogo_compatibilidades.sql`.

Despues iniciar la aplicacion. Git no actualiza la base de datos automaticamente.
Las funciones de plan de abastecimiento y preparacion de compras sugeridas no forman parte de esta version.

Antes de iniciar esta version en otra base SQL Server del proyecto, ejecutar
`normalizar_catalogo_compatibilidades.sql` sobre esa base. Es repetible y agrega
la columna `compatibilidad_fuente`, usada por el portal. No modifica precios ni stock.

El portal muestra C$ en productos, carrito y comprobante de pedido. No se hizo
conversion de importes: los valores originales ya estaban expresados en cordobas.

Las compatibilidades nuevas transcriben modelos explicitos del nombre original.
No certifican anos, versiones, medidas o conectores. El portal distingue esa
procedencia y conserva la advertencia especifica de referencias XR150 para XR150L.
No se expandieron abreviaturas como CG125-150 a modelos adicionales.

`compatibilidades_por_revisar.json` identifica las 40 referencias sin un modelo
concreto extraible. Incluye piezas por medida y familias genericas; no se deben
asignar a todas las motos como si tuvieran compatibilidad universal.

AMO901 y KIT901 tienen nombres similares a otras fichas, pero precios distintos
y marca no registrada. Se diferenciaron por SKU; no se fusionaron ni eliminaron.
Las cantidades, precios e historial se conservaron.

La fuente de la extraccion esta en `catalogo_compatibilidad_revision.json`.
`node preparar_compatibilidades.cjs` regenera la migracion y la lista pendiente.
