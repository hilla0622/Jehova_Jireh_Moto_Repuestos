import os

index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'

with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

target = """    <script src="{{ url_for('static', filename='js/main.js') }}?v=1.4"></script>"""
replacement = """    <script src="{{ url_for('static', filename='js/main.js') }}?v=1.5"></script>"""

if target in index_content:
    index_content = index_content.replace(target, replacement)
else:
    # try 1.3 just in case
    index_content = index_content.replace("js/main.js') }}?v=1.3", "js/main.js') }}?v=1.5")

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_content)

print("Cache busting version 1.5 agregado.")
