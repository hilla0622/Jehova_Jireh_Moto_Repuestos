import os

main_path = r'c:\Users\Hillar\Downloads\prueba\prueba\Jehova_Jireh_Moto_Repuestos\Fronted\static\js\main.js'

with open(main_path, 'rb') as f:
    raw = f.read()

text = raw.decode('utf-8', errors='replace')

# Let's try to reverse Mojibake
try:
    # First level of reverse
    fixed1 = text.encode('cp1252').decode('utf-8')
    print("Fixed level 1 sample:")
    print(fixed1[:200])
    
    # Is there a second level?
    try:
        fixed2 = fixed1.encode('cp1252').decode('utf-8')
        print("Fixed level 2 sample:")
        print(fixed2[:200])
        
        # Third level?
        try:
            fixed3 = fixed2.encode('cp1252').decode('utf-8')
            print("Fixed level 3 sample:")
            print(fixed3[:200])
        except:
            pass
    except:
        pass
except Exception as e:
    print("Could not reverse:", e)
