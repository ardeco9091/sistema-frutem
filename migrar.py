import sqlite3
import pymysql
import json

# Configuración
SQLITE_DB = "sistema_rrhh_full.db"
MYSQL_CONFIG = {"host":"localhost", "user":"root", "password":"", "database":"sistema_rrhh"}

try:
    # 1. Conexiones
    lite = sqlite3.connect(SQLITE_DB)
    my = pymysql.connect(**MYSQL_CONFIG, autocommit=True)
    
    print("Iniciando migración...")
    
    # 2. Migrar Empleados
    emps = lite.execute("SELECT id_reloj, nombre, valor_hora, foto_path FROM empleados").fetchall()
    with my.cursor() as c:
        for e in emps:
            print(f"Migrando empleado: {e[1]}")
            c.execute("INSERT IGNORE INTO empleados VALUES (%s,%s,%s,%s)", e)
            
    # 3. Migrar Fichadas
    fichs = lite.execute("SELECT fecha_hora, id_reloj, raw_data FROM fichadas").fetchall()
    with my.cursor() as c:
        count = 0
        for f in fichs:
            c.execute("INSERT IGNORE INTO fichadas (fecha_hora, id_reloj, raw_data) VALUES (%s,%s,%s)", f)
            count += 1
        print(f"Migradas {count} fichadas.")

    print("✅ MIGRACIÓN COMPLETADA EXITOSAMENTE")
    
except Exception as e:
    print(f"❌ Error: {e}")