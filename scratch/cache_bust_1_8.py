import os

index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'

with open(index_path, 'r', encoding='utf-8') as f:
    idx = f.read()
idx = idx.replace('js/main.js\') }}?v=1.7', 'js/main.js\') }}?v=1.8')
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(idx)

print("Cache bust 1.8 applied!")
