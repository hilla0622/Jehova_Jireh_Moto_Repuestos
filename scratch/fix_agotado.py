import os

main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'

with open(main_path, 'r', encoding='utf-8') as f:
    text = f.read()

# Replace any garbled AGOTADO
import re
text = re.sub(r"'.*AGOTADO'", "'❌ AGOTADO'", text)

# Also fix the initial line
text = re.sub(r"console\.log\('.*?Inicializando Sistema", "console.log('⚡ Inicializando Sistema", text)

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(text)

# Also increment cache bust to 1.7
index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    idx = f.read()
idx = idx.replace('js/main.js\') }}?v=1.6', 'js/main.js\') }}?v=1.7')
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(idx)

print("AGOTADO fixed!")
