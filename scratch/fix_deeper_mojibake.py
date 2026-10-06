import os
import re

main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'

with open(main_path, 'r', encoding='utf-8') as f:
    text = f.read()

replacements = {
    'CÃƒÆ’³digo': 'Código',
    'CÃƒÂ³digo': 'Código',
    'Ãƒâ€š¡': '¡',
    'í°Ã…Â¸Ã…Â½"°': '🎉',
    'Ã‚Â¡': '¡',
    'ÃƒÆ’': 'á',  # Probably á or similar. But let's be careful.
    'Ãƒâ€š': '¡',
}

# Just do exact literal string replacements for the most obvious ones left
text = text.replace('CÃƒÆ’³digo', 'Código')
text = text.replace('CÃƒÂ³digo', 'Código')
text = text.replace('Ãƒâ€š¡', '¡')
text = text.replace('í°Ã…Â¸Ã…Â½"°', '🎉')
text = text.replace('ÃƒÂ©', 'é')
text = text.replace('ÃƒÂ³', 'ó')
text = text.replace('ÃƒÂ¡', 'á')
text = text.replace('ÃƒÂ­', 'í')
text = text.replace('ÃƒÂº', 'ú')

# Any other weird stuff in console.log
text = text.replace('?????????????????????????? Inicializando Sistema Jehov?????????????????? Jireh Moto Repuestos...', '⚡ Inicializando Sistema Jehová Jireh Moto Repuestos...')
text = text.replace('????????????????????Gracias por su compra en Jehov?????????????????? Jireh! ?????????????????????????????????????????', '⭐ ¡Gracias por su compra en Jehová Jireh! ⭐')

with open(main_path, 'w', encoding='utf-8') as f:
    f.write(text)

# Cache bust to 1.9
index_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\templates\index.html'
with open(index_path, 'r', encoding='utf-8') as f:
    idx = f.read()
idx = idx.replace('js/main.js\') }}?v=1.8', 'js/main.js\') }}?v=1.9')
with open(index_path, 'w', encoding='utf-8') as f:
    f.write(idx)

print("Final Mojibake fix applied!")
