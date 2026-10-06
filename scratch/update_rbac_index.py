import re

index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'

with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

replacements_html = [
    # Inventario Menu
    ("{% if usuario.rol in ['Administrador', 'Vendedor', 'Encargado de Inventario', 'Contador'] %}",
     "{% if usuario.rol in ['Administrador', 'Gerente de Operaciones', 'Encargado de Inventario'] %}"),
    
    # Ventas Menu
    ("{% if usuario.rol in ['Administrador', 'Vendedor', 'Contador'] %}",
     "{% if usuario.rol in ['Administrador', 'Gerente de Operaciones', 'Vendedor', 'Contador'] %}"),

    # Compras Menu
    ("{% if usuario.rol in ['Administrador', 'Encargado de Inventario', 'Contador'] %}",
     "{% if usuario.rol in ['Administrador', 'Gerente de Operaciones', 'Encargado de Compras y Proveedores'] %}"),

    # Reportes and Finanzas
    ("{% if usuario.rol in ['Administrador', 'Contador'] %}",
     "{% if usuario.rol in ['Administrador', 'Gerente de Operaciones', 'Gerente Administrativo y Financiero', 'Contador'] %}"),
     
    # RRHH
    ("{% if usuario.rol in ['Administrador', 'Responsable de Recursos Humanos'] %}",
     "{% if usuario.rol in ['Administrador', 'Gerente Administrativo y Financiero', 'Responsable de Recursos Humanos'] %}"),
]

for old, new in replacements_html:
    index_content = index_content.replace(old, new)

# We will hide "Historial de Ventas" and "Pedidos Web" for Vendedor.
# To do this safely, we will wrap the elements inside if blocks.
import sys

def wrap_with_if(content, start_marker, end_marker, condition):
    start = content.find(start_marker)
    if start == -1: return content
    end = content.find(end_marker, start)
    if end == -1: return content
    end += len(end_marker)
    
    # Wrap
    original = content[start:end]
    wrapped = f"{{% if {condition} %}}\n{original}\n{{% endif %}}"
    return content[:start] + wrapped + content[end:]

# Wrap buttons
index_content = wrap_with_if(
    index_content,
    """<button class="subnav-btn {% if usuario.rol == 'Contador' %}active{% endif %}" onclick="switchVentasSubtab('historial-ventas', this)">""",
    """</button>""",
    "usuario.rol != 'Vendedor'"
)

index_content = wrap_with_if(
    index_content,
    """<button class="subnav-btn" onclick="switchVentasSubtab('pedidos-web', this)">""",
    """</button>""",
    "usuario.rol != 'Vendedor'"
)

# Hide "Nuevo Asiento" for Contador
index_content = wrap_with_if(
    index_content,
    """<button class="btn btn-primary" onclick="openModal('modal-asiento')">""",
    """</button>""",
    "usuario.rol != 'Contador'"
)

# Hide "Nueva Cuenta" for Contador
index_content = wrap_with_if(
    index_content,
    """<button class="btn btn-primary btn-sm" onclick="openModal('modal-cuenta')">""",
    """</button>""",
    "usuario.rol != 'Contador'"
)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_content)
    
print("index.html updated successfully.")
