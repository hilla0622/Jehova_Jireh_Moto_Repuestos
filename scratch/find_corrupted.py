import re
import io

main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'

with io.open(main_path, 'r', encoding='utf-8') as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines):
    if 'Ã' in line:
        print(f"Line {i+1}: {line.strip()}")
