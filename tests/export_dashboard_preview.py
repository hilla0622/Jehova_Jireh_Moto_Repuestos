import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from app import app

result = {}
with app.test_client() as client:
    with client.session_transaction() as state:
        state['user'] = {'id': 1, 'nombre': 'Gilda Pérez', 'rol': 'Administrador'}
    for url in ('/dashboard','/api/productos','/api/ventas','/api/proveedores','/api/movimientos'):
        response = client.get(url)
        assert response.status_code == 200, (url,response.status_code)
        result[url] = response.get_data(as_text=True) if url == '/dashboard' else response.get_json()
    for rol in ('Vendedor','Contador','Encargado de Inventario','Encargado de Compras y Proveedores'):
        with client.session_transaction() as state:
            state['user'] = {'id': 1, 'nombre': 'Vista de prueba', 'rol': rol}
        result[rol] = client.get('/dashboard').get_data(as_text=True)
folder = ROOT/'tmp'/'dashboard_review'
folder.mkdir(parents=True,exist_ok=True)
(folder/'snapshot.json').write_text(json.dumps(result,ensure_ascii=False),encoding='utf-8')
print('Vista y datos reales exportados mediante consultas GET.')
