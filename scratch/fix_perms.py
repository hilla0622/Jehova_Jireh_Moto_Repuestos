import os

index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'

with open(index_path, 'r', encoding='utf-8') as f:
    c = f.read()

c = c.replace("['Administrador', 'Encargado de Inventario']", "['Administrador', 'Gerente de Operaciones', 'Encargado de Inventario']")
c = c.replace("['Administrador', 'Vendedor']", "['Administrador', 'Gerente de Operaciones', 'Vendedor']")
c = c.replace("['Administrador', 'Encargado de Compras y Proveedores']", "['Administrador', 'Gerente de Operaciones', 'Encargado de Compras y Proveedores']")

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(c)

print("index.html updated successfully")
