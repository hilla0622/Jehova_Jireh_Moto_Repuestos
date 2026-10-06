import os

app_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\app.py'

with open(app_path, 'r', encoding='utf-8') as f:
    app_content = f.read()

target = """                "asiento_id": m['asiento_id'],
                "fecha": m['fecha'],
                "concepto": m['concepto'],"""

replacement = """                "asiento_id": m['asiento_id'],
                "fecha": m['fecha'].isoformat() if hasattr(m['fecha'], 'isoformat') else str(m['fecha']),
                "concepto": m['concepto'],"""

if target in app_content:
    app_content = app_content.replace(target, replacement)
    with open(app_path, 'w', encoding='utf-8') as f:
        f.write(app_content)
    print("app.py arreglado para la serializacion de fecha")
else:
    print("No se encontro el target en app.py")
