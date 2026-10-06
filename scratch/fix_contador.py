import re

index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'
main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'

with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

# 1. Remove Contador from Ventas Menu
index_content = index_content.replace(
    "{% if usuario.rol in ['Administrador', 'Gerente de Operaciones', 'Vendedor', 'Contador'] %}",
    "{% if usuario.rol in ['Administrador', 'Gerente de Operaciones', 'Vendedor'] %}"
)

# 2. Inject window.usuarioRol into index.html
if "window.usuarioRol =" not in index_content:
    index_content = index_content.replace(
        "</script>\n</head>",
        "    window.usuarioRol = '{{ usuario.rol }}';\n    </script>\n</head>"
    )

# 3. Hide ACCIONES column header for Contador in Cuentas table
target_th = "<th>Acciones</th>"
replace_th = "{% if usuario.rol != 'Contador' %}<th>Acciones</th>{% endif %}"
# I need to be careful as there might be multiple "<th>Acciones</th>"
# Let's target the one under Catálogo de Cuentas Contables.
# Using regex for precision
import re

# We will just replace it in JS by checking window.usuarioRol. 
# Wait, if we hide the TH in HTML, we must hide the TD in JS.
# Let's change JS first.

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_content)

with open(main_path, 'r', encoding='utf-8') as f:
    main_content = f.read()

target_td = """                    <td>
                        <button class="btn" style="background-color: #ef4444; color: white; padding: 0.25rem 0.5rem; border: none; border-radius: 4px;" onclick="eliminarCuenta(${cta.id})">
                            <i class="ph-bold ph-trash"></i>
                        </button>
                    </td>"""

replace_td = """                    ${window.usuarioRol === 'Contador' ? '' : `<td>
                        <button class="btn" style="background-color: #ef4444; color: white; padding: 0.25rem 0.5rem; border: none; border-radius: 4px;" onclick="eliminarCuenta(${cta.id})">
                            <i class="ph-bold ph-trash"></i>
                        </button>
                    </td>`}"""

main_content = main_content.replace(target_td, replace_td)

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_content)

print("Fix applied successfully.")
