"""
=============================================================================
  routes_fiscal.py — Rutas Flask para el Módulo Tributario y Declaración DGI
  Sistema Jehová Jireh Moto Repuestos
=============================================================================
"""

from functools import wraps
from flask import request, jsonify, session, render_template, make_response
import fiscal_service

ROLES_FISCALES = ['Administrador', 'Gerente Administrativo y Financiero', 'Contador']

def fiscal_role_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user' not in session:
            return jsonify({"error": "Sesión no iniciada."}), 401
        if session['user'].get('rol') not in ROLES_FISCALES:
            return jsonify({"error": "Acceso denegado: este módulo está reservado para Administración y Contabilidad."}), 403
        return f(*args, **kwargs)
    return decorated

def register_fiscal_routes(app):

    @app.route('/api/fiscal/respaldo-demo/<int:anio>', methods=['GET'])
    @fiscal_role_required
    def api_fiscal_respaldo_demo(anio):
        from app import get_db_connection
        conn = get_db_connection()
        try:
            return jsonify({'documentos': fiscal_service.obtener_respaldo_demostracion(conn.cursor(), anio)})
        finally:
            conn.close()
    
    @app.route('/api/fiscal/info', methods=['GET'])
    @fiscal_role_required
    def api_fiscal_info():
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            info = fiscal_service.obtener_info_tributaria(cursor)
            reglas = fiscal_service.obtener_reglas_fiscales(cursor)
            return jsonify({
                "negocio": info,
                "reglas": reglas,
                "catalogo_retenciones": fiscal_service.CATALOGO_RETENCIONES_DGI
            })
        finally:
            conn.close()

    @app.route('/api/fiscal/simulacion/<int:anio>', methods=['GET'])
    @fiscal_role_required
    def api_fiscal_simulacion(anio):
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            info = fiscal_service.obtener_info_tributaria(cursor)
            saldos = fiscal_service.obtener_saldos_contables_ejercicio(cursor, anio)
            ajustes = fiscal_service.obtener_ajustes_ejercicio(cursor, anio)
            acreds = fiscal_service.obtener_acreditamientos_ejercicio(cursor, anio)
            sim = fiscal_service.mapear_formulario_106(saldos, ajustes, acreds)
            sim["negocio"] = info
            return jsonify(sim)
        except Exception as e:
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/fiscal/guardar', methods=['POST'])
    @app.route('/api/fiscal/declaracion/guardar', methods=['POST'])
    @fiscal_role_required
    def api_fiscal_guardar_declaracion():
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            data = request.json or {}
            es_aprobada = bool(data.get("es_aprobada", data.get("aprobar", False)))
            sim = fiscal_service.preparar_declaracion_desde_contabilidad(cursor, data)
            anio = sim['anio']

            decl_id = fiscal_service.guardar_declaracion_completa(
                cursor, sim, session['user']['id'], es_aprobada=es_aprobada
            )
            conn.commit()
            return jsonify({
                "success": True,
                "declaracion_id": decl_id,
                "mensaje": f"Declaración Anual IR {anio} guardada exitosamente como {'Aprobada' if es_aprobada else 'Borrador'}."
            })
        except ValueError as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/fiscal/historial', methods=['GET'])
    @app.route('/api/fiscal/declaraciones', methods=['GET'])
    @fiscal_role_required
    def api_fiscal_listar_declaraciones():
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            decls = fiscal_service.listar_declaraciones_guardadas(cursor)
            return jsonify({"declaraciones": decls})
        finally:
            conn.close()

    @app.route('/api/fiscal/declaracion/<int:decl_id>', methods=['GET', 'DELETE'])
    @fiscal_role_required
    def api_fiscal_declaracion_item(decl_id):
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if request.method == 'GET':
                detalle = fiscal_service.obtener_declaracion_detalle(cursor, decl_id)
                if not detalle:
                    return jsonify({"error": "Declaración no encontrada."}), 404
                return jsonify({"declaracion": detalle})
            
            if request.method == 'DELETE':
                fiscal_service.eliminar_declaracion(cursor, decl_id)
                conn.commit()
                return jsonify({
                    "success": True,
                    "mensaje": "Borrador de declaración eliminado correctamente."
                })
        except ValueError as ve:
            conn.rollback()
            return jsonify({"error": str(ve)}), 400
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/fiscal/presentar', methods=['POST'])
    @app.route('/api/fiscal/declaracion/presentar', methods=['POST'])
    @fiscal_role_required
    def api_fiscal_presentar_declaracion():
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            data = request.json or {}
            # Guardado, aprobación y constancia se confirman en una sola transacción.
            if 'simulacion' in data:
                sim = fiscal_service.preparar_declaracion_desde_contabilidad(cursor, data)
                data['declaracion_id'] = fiscal_service.guardar_declaracion_completa(
                    cursor, sim, session['user']['id'], es_aprobada=True)
            fiscal_service.registrar_presentacion_dgi(cursor, data, session['user']['id'])
            conn.commit()
            return jsonify({
                "success": True,
                "declaracion_id": data['declaracion_id'],
                "mensaje": "Constancia de presentación y pago ante la DGI registrada con éxito."
            })
        except ValueError as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 400
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/fiscal/acreditamientos', methods=['GET', 'POST'])
    @app.route('/api/fiscal/acreditamiento', methods=['POST'])
    @fiscal_role_required
    def api_fiscal_acreditamientos():
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            if request.method == 'GET':
                anio = int(request.args.get('anio', 2026))
                filas = fiscal_service.obtener_acreditamientos_ejercicio(cursor, anio)
                return jsonify({"acreditamientos": filas})

            # POST: Nuevo acreditamiento
            data = request.json or {}
            new_id = fiscal_service.guardar_acreditamiento(cursor, data, session['user']['id'])
            conn.commit()
            return jsonify({
                "success": True,
                "id": new_id,
                "mensaje": "Constancia de retención / anticipo registrada exitosamente."
            }), 201
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/fiscal/acreditamientos/<int:anio>', methods=['GET'])
    @fiscal_role_required
    def api_fiscal_acreditamientos_anio(anio):
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            filas = fiscal_service.obtener_acreditamientos_ejercicio(cursor, anio)
            return jsonify({"acreditamientos": filas})
        finally:
            conn.close()

    @app.route('/api/fiscal/acreditamientos/<int:id>', methods=['DELETE'])
    @app.route('/api/fiscal/acreditamiento/<int:id>', methods=['DELETE'])
    @fiscal_role_required
    def api_fiscal_eliminar_acreditamiento(id):
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            fiscal_service.eliminar_acreditamiento(cursor, id)
            conn.commit()
            return jsonify({"success": True, "mensaje": "Acreditamiento eliminado."})
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/fiscal/ajustes', methods=['POST'])
    @app.route('/api/fiscal/ajuste', methods=['POST'])
    @fiscal_role_required
    def api_fiscal_guardar_ajuste():
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            data = request.json or {}
            fiscal_service.guardar_ajuste_fiscal(cursor, data, session['user']['id'])
            conn.commit()
            return jsonify({"success": True, "mensaje": "Ajuste fiscal guardado."})
        except Exception as e:
            conn.rollback()
            return jsonify({"error": str(e)}), 500
        finally:
            conn.close()

    @app.route('/api/fiscal/ajustes/<int:anio>', methods=['GET'])
    @fiscal_role_required
    def api_fiscal_ajustes_anio(anio):
        from app import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            filas = fiscal_service.obtener_ajustes_ejercicio(cursor, anio)
            return jsonify({"ajustes": filas})
        finally:
            conn.close()
