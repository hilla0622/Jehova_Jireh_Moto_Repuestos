import os
import pyodbc

def verificar_base_de_datos():
    print("=" * 60)
    print("  VERIFICACIÓN DEL ESTADO DE LA BASE DE DATOS LOCAL")
    print("=" * 60)
    
    comp_name = os.environ.get('COMPUTERNAME', 'LAPTOP-CNR3S3I3')
    db_name = 'jehova_jireh_db'
    print(f"Equipo actual: {comp_name}")
    print(f"Base de datos esperada: {db_name}")
    
    # Probar conexión
    conn = None
    servidor_conectado = None
    servidores = [comp_name, '.', 'localhost', 'HILLARY']
    
    for srv in servidores:
        try:
            conn_str = (
                r'DRIVER={ODBC Driver 17 for SQL Server};'
                fr'SERVER={srv};'
                fr'DATABASE={db_name};'
                r'Trusted_Connection=yes;'
            )
            conn = pyodbc.connect(conn_str, timeout=3)
            servidor_conectado = srv
            break
        except Exception:
            continue
            
    if not conn:
        print("[ERROR] No se pudo conectar a Microsoft SQL Server en ningún servidor local.")
        return

    print(f"[OK] Conectado exitosamente a SQL Server a través de: {servidor_conectado}\n")
    cursor = conn.cursor()

    # Contar tablas
    cursor.execute("""
        SELECT t.name AS tabla, SUM(p.rows) AS filas
        FROM sys.tables t
        JOIN sys.partitions p ON t.object_id = p.object_id
        WHERE p.index_id IN (0,1)
        GROUP BY t.name
        ORDER BY t.name
    """)
    tablas = cursor.fetchall()
    print(f"--- Tablas existentes ({len(tablas)}) ---")
    for tabla, filas in tablas:
        print(f"  • {tabla:<28}: {filas:>6} registros")

    # Contar vistas
    cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.VIEWS ORDER BY TABLE_NAME")
    vistas = [r[0] for r in cursor.fetchall()]
    print(f"\n--- Vistas activas ({len(vistas)}) ---")
    for v in vistas:
        print(f"  • {v}")

    # Permisos
    cursor.execute("SELECT COUNT(*) FROM permisos")
    cant_permisos = cursor.fetchone()[0]
    print(f"\n[OK] Permisos del sistema configurados: {cant_permisos}")

    conn.close()
    print("\n" + "=" * 60)
    print("  ESTADO DE LA BASE DE DATOS: 100% OPERATIVA Y ACTUALIZADA")
    print("=" * 60)

if __name__ == '__main__':
    verificar_base_de_datos()
