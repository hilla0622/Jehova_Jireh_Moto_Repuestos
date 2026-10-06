import os

main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'

with open(main_path, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8', errors='replace')

try:
    fixed1 = text.encode('latin1').decode('utf-8')
    print("Latin1 Fixed level 1 sample:")
    print(fixed1[:200])
    
    try:
        fixed2 = fixed1.encode('latin1').decode('utf-8')
        print("Latin1 Fixed level 2 sample:")
        print(fixed2[:200])
        
        # We will save fixed2 if it works
        with open(main_path + ".fixed.js", 'w', encoding='utf-8') as f:
            f.write(fixed2)
        print("Saved to .fixed.js")
    except Exception as e:
        print("Level 2 failed:", e)
        with open(main_path + ".fixed.js", 'w', encoding='utf-8') as f:
            f.write(fixed1)
        print("Saved level 1 to .fixed.js")
        
except Exception as e:
    print("Latin1 Could not reverse:", e)
