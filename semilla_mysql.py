import mysql.connector
import random
from datetime import datetime, timedelta
from motor import MotorSistema # Importamos tu motor para usar TU configuración

# --- DATOS PARA LA DEMO PANADERÍA ---
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

ROLES = [
    ("Maestro Panadero", 6500), # Ganan más
    ("Ayudante Cocina", 3800),
    ("Cajero/a", 4200),
    ("Atención Mostrador", 3500),
    ("Limpieza", 3000),
    ("Repartidor", 3800)
]

def sembrar_datos_mysql():
    print("🔌 Conectando usando tu configuración de motor.py...")
    
    # Instanciamos tu motor para que lea el config.json solo
    sistema = MotorSistema()
    
    try:
        conn = sistema.get_connection()
        cursor = conn.cursor()
        print("✅ Conexión MySQL Exitosa.")
    except Exception as e:
        print(f"❌ Error conectando a MySQL: {e}")
        print("Revisa que XAMPP/MySQL esté prendido y el config.json tenga la clave correcta.")
        return

    print("--- INICIANDO CARGA DE DATOS DEMO (PANADERÍA) ---")

    # 1. LIMPIEZA
    print("🧹 Limpiando tablas antiguas...")
    # Orden importante: primero fichadas (hijas), luego empleados (padres)
    cursor.execute("DELETE FROM fichadas")
    cursor.execute("DELETE FROM empleados")
    
    # 2. INSERTAR 30 EMPLEADOS
    print("👥 Creando 30 empleados...")
    empleados_generados = []
    
    query_emp = "INSERT INTO empleados (id_reloj, nombre, valor_hora, foto_path) VALUES (%s, %s, %s, %s)"
    
    for i, nombre in enumerate(NOMBRES, 1):
        rol, sueldo = random.choice(ROLES)
        nombre_completo = f"{nombre} ({rol})"
        id_reloj = str(i)
        
        # MySQL usa %s como placeholder, no ?
        cursor.execute(query_emp, (id_reloj, nombre_completo, sueldo, "SIN_FOTO"))
        empleados_generados.append((id_reloj, rol))

    # 3. GENERAR FICHADAS DE HOY (Monitor en Vivo)
    print("🕒 Generando fichadas de HOY...")
    hoy = datetime.now().strftime("%Y-%m-%d")
    
    query_fichada = "INSERT INTO fichadas (fecha_hora, id_reloj, raw_data) VALUES (%s, %s, %s)"
    
    # Simulamos que los primeros 18 empleados vinieron hoy
    for id_emp, rol in empleados_generados[:18]:
        # Los Panaderos entran super temprano (4 AM - 6 AM)
        if "Panadero" in rol:
            hora_entrada = random.randint(4, 6)
        else:
            hora_entrada = random.randint(7, 9)
            
        minuto_entrada = random.randint(0, 59)
        fecha_entrada = f"{hoy} {hora_entrada:02d}:{minuto_entrada:02d}:00"
        
        cursor.execute(query_fichada, (fecha_entrada, id_emp, "DEMO_AUTO"))
        
        # Simulamos que algunos (los panaderos que entraron a las 4am) ya se fueron
        if "Panadero" in rol and random.random() > 0.5:
            hora_salida = hora_entrada + 8 
            fecha_salida = f"{hoy} {hora_salida:02d}:{minuto_entrada:02d}:00"
            cursor.execute(query_fichada, (fecha_salida, id_emp, "DEMO_AUTO"))

    # 4. GENERAR HISTORIAL (Para Liquidación)
    print("📅 Generando historial del mes pasado...")
    for dias_atras in range(1, 15): # 15 días de historia
        fecha = (datetime.now() - timedelta(days=dias_atras)).strftime("%Y-%m-%d")
        
        # Domingo descansan (opcional)
        fecha_dt = datetime.now() - timedelta(days=dias_atras)
        if fecha_dt.weekday() == 6: continue 

        for id_emp, rol in empleados_generados:
            if random.random() > 0.15: # 85% de asistencia
                # Entrada
                if "Panadero" in rol: h_in = random.randint(4, 6)
                else: h_in = random.randint(7, 9)
                
                m = random.randint(0, 59)
                dt_in = f"{fecha} {h_in:02d}:{m:02d}:00"
                
                # Salida (8 o 9 horas despues)
                h_out = h_in + random.choice([8, 9])
                dt_out = f"{fecha} {h_out:02d}:{m:02d}:00"
                
                # Insertamos entrada y salida
                # Usamos INSERT IGNORE o try/catch por si generamos duplicados exactos random
                try:
                    cursor.execute(query_fichada, (dt_in, id_emp, "DEMO_HIST"))
                    cursor.execute(query_fichada, (dt_out, id_emp, "DEMO_HIST"))
                except: pass

    conn.commit()
    cursor.close()
    conn.close()
    print("✅ ¡LISTO! Base de datos MySQL poblada para la DEMO PANADERÍA.")

if __name__ == "__main__":
    sembrar_datos_mysql()