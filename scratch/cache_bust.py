import os

index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'

with open(index_path, 'r', encoding='utf-8') as f:
    index_content = f.read()

target = """    <script src="{{ url_for('static', filename='js/main.js') }}"></script>"""
replacement = """    <script src="{{ url_for('static', filename='js/main.js') }}?v=1.1"></script>"""

index_content = index_content.replace(target, replacement)

with open(index_path, 'w', encoding='utf-8') as f:
    f.write(index_content)

print("Cache busting agregado.")
