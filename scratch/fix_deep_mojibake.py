import os
import re

main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'

with open(main_path, 'r', encoding='utf-8') as f:
    text = f.read()

replacements = {
    'ÃƒÆ’¡': 'á',
    'ÃƒÆ’©': 'é',
    'ÃƒÆ’³': 'ó',
    'ÃƒÆ’º': 'ú',
    'ÃƒÆ’±': 'ñ',
    'ÃƒÆ’­': 'í',
    'ÃƒÆ’"N': 'ÓN',
    'ÃƒÆ’Ã¢â‚¬ËœAS': 'ÑAS',
    'Ãƒâ€š¿': '¿',
    'JEHOVÃƒÆ’  JIREH': 'JEHOVÁ JIREH',
    'JehovÃƒÆ’¡': 'Jehová',
    'í°Ã…Â¸Ã¢â€žÂ¢': '🙏',
    'SÃƒÆ’ ': 'SÍ ',
    'ANÃƒÆ’ LISIS': 'ANÁLISIS',
    'ÃƒÆ’': 'Á' # Fallback for remaining like ÃƒÆ’ LISIS if it was just ÃƒÆ’
}

sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)

for k, v in sorted_replacements:
    text = text.replace(k, v)

# Fix remaining oddities in comments or strings
text = text.replace('LÁ³gica', 'Lógica')
text = text.replace('ConexiÁ³n', 'Conexión')

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(text)

# Cache bust to 2.0
index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    idx = f.read()
idx = idx.replace('js/main.js\') }}?v=1.9', 'js/main.js\') }}?v=2.0')
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(idx)

print("Deep mojibake fix applied!")
