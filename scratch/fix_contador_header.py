import re

index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'

with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

# We need to replace <th>Acciones</th> under "Catálogo de Cuentas Contables"
# Let's find the table block for "fin-catalogo"
target_table_header = """                                        <thead>
                                            <tr>
                                                <th>Código</th>
                                                <th>Nombre de la Cuenta</th>
                                                <th>Clasificación</th>
                                                <th>Naturaleza</th>
                                                <th>Acciones</th>
                                            </tr>
                                        </thead>"""
replace_table_header = """                                        <thead>
                                            <tr>
                                                <th>Código</th>
                                                <th>Nombre de la Cuenta</th>
                                                <th>Clasificación</th>
                                                <th>Naturaleza</th>
                                                {% if usuario.rol != 'Contador' %}<th>Acciones</th>{% endif %}
                                            </tr>
                                        </thead>"""
index_content = index_content.replace(target_table_header, replace_table_header)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_content)
