import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace('SELECT stock FROM productos WHERE id = ?', 'SELECT stock_actual AS stock FROM productos WHERE id = ?')
content = content.replace('UPDATE productos SET stock = ? WHERE id = ?', 'UPDATE productos SET stock_actual = ? WHERE id = ?')

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(content)
