import codecs

with codecs.open('Fronted/static/js/main.js', 'r', 'utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'Todo el stock' in line and 'niveles' in line:
        lines[i] = '                tbodyStock.innerHTML = <tr><td colspan="4" class="text-center text-accent-green">\u00A1Excelente! Todo el stock est\u00E1 en niveles \u00F3ptimos.</td></tr>;\n'

with codecs.open('Fronted/static/js/main.js', 'w', 'utf-8') as f:
    f.writelines(lines)
