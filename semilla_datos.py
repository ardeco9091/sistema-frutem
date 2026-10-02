import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "sistema_rrhh_full.db"

# Lista de nombres realistas
NOMBRES = [
    "Juan Carlos Pérez", "María Eugenia López", "Carlos Alberto Gómez", "Ana María Rodríguez",
    "Luis Fernando Fernández", "Laura Beatriz García", "José Luis Martínez", "Marta Susana González",
    "Miguel Ángel Díaz", "Cristina Elizabeth Sánchez", "Jorge Daniel Romero", "Silvia Alejandra Ruiz",
    "Roberto Antonio Flores", "Patricia Noemí Cabrera", "Ricardo Manuel Benítez", "Nancy Beatriz Acosta",
    "Eduardo Fabián Medina", "Mónica Liliana Herrera", "Sergio Adrián Silva", "Andrea Verónica Rojas",
    "Pablo Andrés Molina", "Verónica Inés Castro", "Walter Hugo Ortiz", "Gisela Paola Ledesma",
    "Gustavo Adolfo Roldán", "Claudia Marcela Vega", "Héctor Ramón Ferreyra", "Daniela Fernanda Luna",
    "Esteban Gabriel Ríos", "Natalia Soledad Peralta"
]

# Roles y sus sueldos aproximados (simulados)
ROLES = [
    ("Maestro Panadero", 5500),
    ("Ayudante Cocina", 3200),
    ("Cajero/a", 3800),
    ("Atención Mostrador", 3000),
    ("Limpieza", 2800),
    ("Repartidor", 3500)
]

def sembrar_datos():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    print("--- INICIANDO CARGA DE DATOS DEMO ---")

    # 1. LIMPIEZA (Opcional: comenta estas lineas si quieres mantener lo tuyo)
    print("🧹 Limpiando base de datos antigua...")
    cursor.execute("DELETE FROM empleados")
    cursor.execute("DELETE FROM fichadas")
    
    # Asegurar que las tablas existan (por si borraste el archivo .db)
    cursor.execute("CREATE TABLE IF NOT EXISTS empleados (id_reloj TEXT PRIMARY KEY, nombre TEXT, valor_hora REAL, foto_path TEXT)")
    cursor.execute("CREATE TABLE IF NOT EXISTS fichadas (id INTEGER PRIMARY KEY AUTOINCREMENT, fecha_hora TEXT, id_reloj TEXT, raw_data TEXT)")
    cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_fichada ON fichadas(fecha_hora, id_reloj)")

    # 2. INSERTAR 30 EMPLEADOS
    print("👥 Creando 30 empleados...")
    empleados_generados = []
    
    for i, nombre in enumerate(NOMBRES, 1):
        # Asignar rol aleatorio
        rol, sueldo = random.choice(ROLES)
        nombre_completo = f"{nombre} ({rol})"
        
        # ID simula ser el del reloj (1, 2, 3...)
        id_reloj = str(i)
        
        # Insertar
        cursor.execute("INSERT OR REPLACE INTO empleados (id_reloj, nombre, valor_hora, foto_path) VALUES (?, ?, ?, ?)",
                       (id_reloj, nombre_completo, sueldo, "SIN_FOTO"))
        
        empleados_generados.append(id_reloj)

    # 3. GENERAR FICHADAS DE HOY (Para que el Monitor se vea vivo)
    print("🕒 Generando fichadas de hoy...")
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    # Simulamos que los primeros 20 empleados vinieron hoy
    for id_emp in empleados_generados[:20]:
        # Hora de entrada aleatoria entre 06:00 y 09:00 AM
        hora_entrada = random.randint(6, 9)
        minuto_entrada = random.randint(0, 59)
        fecha_entrada = f"{hoy} {hora_entrada:02d}:{minuto_entrada:02d}:00"
        
        cursor.execute("INSERT OR IGNORE INTO fichadas (fecha_hora, id_reloj, raw_data) VALUES (?, ?, ?)",
                       (fecha_entrada, id_emp, "DEMO_AUTO"))
        
        # Simulamos que algunos (los primeros 5) ya se fueron (Turno mañana)
        if int(id_emp) <= 5:
            hora_salida = hora_entrada + 8 # 8 horas despues
            fecha_salida = f"{hoy} {hora_salida:02d}:{minuto_entrada:02d}:00"
            cursor.execute("INSERT OR IGNORE INTO fichadas (fecha_hora, id_reloj, raw_data) VALUES (?, ?, ?)",
                       (fecha_salida, id_emp, "DEMO_AUTO"))

    # 4. GENERAR HISTORIAL (Para que la Liquidación tenga datos)
    print("📅 Generando historial del mes pasado...")
    # Generamos 10 días hacia atrás
    for dias_atras in range(1, 10):
        fecha = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
        # Asumimos que casi todos vinieron
        for id_emp in empleados_generados:
            if random.random() > 0.1: # 90% de asistencia
                # Entrada
                h_in = random.randint(6, 9)
                m = random.randint(0, 59)
                dt_in = f"{fecha} {h_in:02d}:{m:02d}:00"
                
                # Salida (8 o 9 horas despues)
                h_out = h_in + random.choice([8, 9])
                dt_out = f"{fecha} {h_out:02d}:{m:02d}:00"
                
                cursor.execute("INSERT OR IGNORE INTO fichadas (fecha_hora, id_reloj, raw_data) VALUES (?, ?, ?)", (dt_in, id_emp, "DEMO_HIST"))
                cursor.execute("INSERT OR IGNORE INTO fichadas (fecha_hora, id_reloj, raw_data) VALUES (?, ?, ?)", (dt_out, id_emp, "DEMO_HIST"))

    conn.commit()
    conn.close()
    print("✅ ¡LISTO! Base de datos poblada para la DEMO.")
    print("   -> 30 Empleados creados.")
    print("   -> Fichadas de hoy generadas (Ver pestaña MONITOR).")
    print("   -> Historial generado (Ver pestaña LIQUIDACIÓN).")

if __name__ == "__main__":
    sembrar_datos()