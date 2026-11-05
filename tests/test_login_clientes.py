import unittest
from unittest.mock import patch

from werkzeug.security import check_password_hash, generate_password_hash

import app as portal


class LoginClientesTest(unittest.TestCase):
    def setUp(self):
        self.client = portal.app.test_client()
        self.email = 'cliente@example.com'
        self.password = ' clave de prueba '

    @patch.object(portal, 'execute_query')
    def test_registro_lleva_al_acceso_de_clientes(self, query):
        query.side_effect = [[], 1]
        response = self.client.post('/registro', data={
            'nombre_completo': 'Cliente de prueba',
            'email': self.email,
            'password': self.password,
        }, follow_redirects=True)

        self.assertEqual(response.request.path, '/clientes/login')
        self.assertIn('Cuenta creada', response.get_data(as_text=True))
        self.assertNotIn('Cuentas Rápidas de Prueba', response.get_data(as_text=True))
        stored_hash = query.call_args.kwargs['params'][2]
        self.assertTrue(check_password_hash(stored_hash, self.password))

    @patch.object(portal, 'execute_query')
    def test_cliente_entra_a_tienda_y_perfil_y_no_accede_a_datos_internos(self, query):
        query.return_value = {
            'id': 1, 'email': self.email, 'nombre_completo': 'Cliente de prueba',
            'password_hash': generate_password_hash(self.password), 'direccion': '',
        }
        response = self.client.post('/clientes/login', data={
            'username': self.email, 'password': self.password,
        })

        self.assertEqual(response.location, '/')
        query.assert_called_once()
        self.assertIn('FROM clientes', query.call_args.args[0])
        with self.client.session_transaction() as session:
            self.assertEqual(session['user']['rol'], 'Cliente')
        self.assertEqual(self.client.get('/perfil').status_code, 200)
        self.assertEqual(self.client.get('/dashboard').location, '/')
        for path in ('/api/ventas', '/api/compras', '/api/pedidos_web', '/api/pagos', '/api/productos'):
            with self.subTest(path=path):
                self.assertEqual(self.client.get(path).status_code, 403)
        query.assert_called_once()

    @patch.object(portal, 'execute_query', return_value={'password_hash': None})
    def test_cliente_sin_contrasena_no_inicia_sesion(self, query):
        response = self.client.post('/clientes/login', json={
            'username': self.email, 'password': self.password,
        })

        self.assertEqual(response.status_code, 401)
        self.assertIn('Correo o contraseña incorrectos', response.json['error'])
        with self.client.session_transaction() as session:
            self.assertNotIn('user', session)

    @patch.object(portal, 'execute_query')
    def test_boton_de_la_tienda_permite_elegir_tipo_de_acceso(self, query):
        query.return_value = []
        self.assertIn('href="/acceso"', self.client.get('/').get_data(as_text=True))
        html = self.client.get('/acceso').get_data(as_text=True)
        self.assertIn('Soy cliente', html)
        self.assertIn('Soy del personal', html)
        self.assertIn('href="/clientes/login"', html)
        self.assertIn('href="/personal/login"', html)
        self.assertNotIn('name="password"', html)

        cliente = self.client.get('/clientes/login').get_data(as_text=True)
        self.assertIn('type="email" id="username"', cliente)
        self.assertIn('action="/clientes/login"', cliente)
        personal = self.client.get('/personal/login').get_data(as_text=True)
        self.assertIn('Usuario del personal', personal)
        self.assertIn('type="text" id="username"', personal)
        self.assertIn('action="/personal/login"', personal)

    @patch.object(portal, 'execute_query', return_value=None)
    def test_acceso_del_personal_no_consulta_cuentas_de_clientes(self, query):
        response = self.client.post('/personal/login', json={
            'username': self.email, 'password': self.password,
        })
        self.assertEqual(response.status_code, 401)
        query.assert_called_once()
        self.assertIn('FROM usuarios', query.call_args.args[0])

    @patch.object(portal, 'execute_query')
    def test_acceso_general_sigue_admitiendo_correo(self, query):
        query.side_effect = [
            None,
            {'id': 1, 'email': self.email, 'nombre_completo': 'Cliente de prueba',
             'password_hash': generate_password_hash(self.password), 'direccion': ''},
        ]
        html = self.client.get('/login').get_data(as_text=True)
        self.assertIn('Usuario o correo electrónico', html)
        self.assertNotIn('Cuentas Rápidas de Prueba', html)

        response = self.client.post('/login', data={
            'username': self.email, 'password': self.password,
        })
        self.assertEqual(response.location, '/')
        with self.client.session_transaction() as session:
            self.assertEqual(session['user']['rol'], 'Cliente')
        self.assertEqual(self.client.get('/api/pedidos_web').status_code, 403)

    @patch.object(portal, 'get_db_connection')
    @patch.object(portal, 'execute_query')
    def test_personal_conserva_el_acceso_al_panel(self, query, connection):
        query.side_effect = [
            {'id': 1, 'username': 'empleado', 'nombre': 'Personal',
             'rol': 'Administrador', 'rol_id': 1},
            [],
        ]
        connection.return_value.cursor.return_value.fetchone.return_value = [1]
        response = self.client.post('/personal/login', data={
            'username': 'empleado', 'password': ' clave ',
        })

        self.assertEqual(response.location, '/dashboard')
        self.assertEqual(query.call_args_list[0].args[1], ('empleado', 'clave'))
        self.assertEqual(self.client.get('/dashboard').status_code, 200)
