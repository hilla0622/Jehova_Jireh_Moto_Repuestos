import codecs

with codecs.open('app.py', 'r', 'utf-8') as f:
    content = f.read()

# Fix table name
content = content.replace('SELECT producto_id, cantidad FROM ventas_detalles WHERE venta_id = ?', 'SELECT producto_id, cantidad FROM detalle_ventas WHERE venta_id = ?')

# Add accounting reversion
reversion_code = '''        for det in detalles:
            cursor.execute("SELECT stock FROM productos WHERE id = ?", (det.producto_id,))
            prod = cursor.fetchone()
            if prod:
                stock_anterior = prod.stock
                stock_posterior = stock_anterior + det.cantidad
                cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (stock_posterior, det.producto_id))
                
                cursor.execute("""
                    INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, motivo, usuario_id)
                    VALUES (?, 'DEVOLUCION_CLIENTE', ?, ?, ?, ?, ?)
                """, (det.producto_id, det.cantidad, stock_anterior, stock_posterior, f"Anulacion de venta {venta.codigo_venta}", session['user']['id']))
        
        # --- REVERSION CONTABLE ---
        cursor.execute("SELECT id FROM asientos_contables WHERE referencia_id = ? AND modulo_origen IN ('VENTAS', 'VENTAS_WEB')", (v_id,))
        asiento = cursor.fetchone()
        if asiento:
            cursor.execute("""
                INSERT INTO asientos_contables (fecha, concepto, modulo_origen, referencia_id, usuario_id)
                VALUES (GETDATE(), ?, 'REVERSION_VENTA', ?, ?)
            """, (f"Anulacion Venta {venta.codigo_venta}", v_id, session['user']['id']))
            cursor.execute("SELECT @@IDENTITY AS id")
            new_asiento_id = cursor.fetchone().id
            
            cursor.execute("SELECT cuenta_id, debe, haber FROM movimientos_contables WHERE asiento_id = ?", (asiento.id,))
            movimientos = cursor.fetchall()
            for mov in movimientos:
                cursor.execute("""
                    INSERT INTO movimientos_contables (asiento_id, cuenta_id, debe, haber)
                    VALUES (?, ?, ?, ?)
                """, (new_asiento_id, mov.cuenta_id, mov.haber, mov.debe))
        # --------------------------
'''

# We find the original loop and replace it with the new loop + reversion
original_loop = '''        for det in detalles:
            cursor.execute("SELECT stock FROM productos WHERE id = ?", (det.producto_id,))
            prod = cursor.fetchone()
            if prod:
                stock_anterior = prod.stock
                stock_posterior = stock_anterior + det.cantidad
                cursor.execute("UPDATE productos SET stock = ? WHERE id = ?", (stock_posterior, det.producto_id))
                
                cursor.execute("""
                    INSERT INTO movimientos_inventario (producto_id, tipo_movimiento, cantidad, stock_anterior, stock_posterior, motivo, usuario_id)
                    VALUES (?, 'DEVOLUCION_CLIENTE', ?, ?, ?, ?, ?)
                """, (det.producto_id, det.cantidad, stock_anterior, stock_posterior, f"Anulacion de venta {venta.codigo_venta}", session['user']['id']))'''

content = content.replace(original_loop, reversion_code.strip())

with codecs.open('app.py', 'w', 'utf-8') as f:
    f.write(content)
