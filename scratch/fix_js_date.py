import os

main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'

with open(main_path, 'r', encoding='utf-8') as f:
    main_content = f.read()

target = "<td>${formatDateToLocal(m.fecha)}</td>"
replacement = "<td>${m.fecha.substring(0, 16).replace('T', ' ')}</td>"

if target in main_content:
    main_content = main_content.replace(target, replacement)
    
with open(main_path, 'w', encoding='utf-8') as f:
    f.write(main_content)

print("JS arreglado.")
