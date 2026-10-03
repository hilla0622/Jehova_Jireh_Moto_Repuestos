import codecs

endpoint = '''
@app.route('/api/ventas/<int:v_id>/anular', methods=['POST'])
@role_required('Administrador', 'Vendedor')
def api_venta_anular(v_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT estado, codigo_venta FROM ventas WHERE id = ?", (v_id,))
        venta = cursor.fetchone()
        if not venta:
            return jsonify({"error": "Venta no encontrada."}), 404
        if venta.estado == 'Anulada':
            return jsonify({"error": "Esta venta ya se encuentra anulada."}), 400

        cursor.execute("UPDATE ventas SET estado = 'Anulada' WHERE id = ?", (v_id,))
        
        cursor.execute("SELECT producto_id, cantidad FROM ventas_detalles WHERE venta_id = ?", (v_id,))
        detalles = cursor.fetchall()
        
        for det in detalles:
            cursor.execute("SELECT stock FROM productos WHERE id = ?", (det.producto_id,))
            prod = cursor.fetchone()
            if prod:
                stock_anterior = prod.stock
                stock_posterior = stock_anterior + det.cantidad
                cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (stock_posterior, det.producto_id))
                
                cursor.execute(\"\"\"
                    INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, motivo, usuario_id)
                    VALUES (?, 'DEVOLUCION_CLIENTE', ?, ?, ?, ?, ?)
                \"\"\", (det.producto_id, det.cantidad, stock_anterior, stock_posterior, f"Anulacion de venta {venta.codigo_venta}", session['user']['id']))
        
        conn.commit()
        return jsonify({"success": True, "mensaje": f"Venta {venta.codigo_venta} anulada correctamente. Stock retornado."})
    except Exception as e:
        conn.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        cursor.close()
        conn.close()

'''

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

content = content.replace('# --- COMPRAS Y PROVEEDORES ---', endpoint + '\n# --- COMPRAS Y PROVEEDORES ---')

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(content)

print("Done")