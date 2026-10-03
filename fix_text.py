import codecs

with codecs.open('Fronted/static/js/main.js', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Bajo! (' in line:
        lines[i] = "        const badgeText = isLow ? \u00A1Bajo! () : Disponible ();\n"

with codecs.open('Fronted/static/js/main.js', 'w', 'utf-8') as f:
    f.writelines(lines)
