import ctypes
import time
from datetime import datetime
import json
import os
import sys

# Importamos tu motor
try:
    from motor import MotorSistema
except ImportError:
    print("❌ Error: No se encuentra 'motor.py'.")
    sys.exit()

def callback_espia(pInfo):
    """
    Versión corregida: Recibe UN solo argumento (pInfo),
    igual que lo hace tu main.py.
    """
    if not pInfo:
        return

    try:
        # 1. Leemos 1024 bytes de golpe (para no perder nada)
        # Usamos string_at para obtener los bytes crudos
        raw_data = ctypes.string_at(pInfo, 1024)
        
        # 2. VISTA HEXADECIMAL (Primeros 64 bytes)
        # Aquí veremos dónde se esconden la fecha y los IDs
        hex_view = " ".join(f"{b:02X}" for b in raw_data[:64])
        
        # 3. VISTA TEXTO
        try:
            texto = raw_data.decode('utf-8', errors='ignore')
        except:
            texto = raw_data.decode('latin-1', errors='ignore')
            
        texto_limpio = texto.replace('\x00', '').strip()

        # 4. IMPRIMIR Y GUARDAR
        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
        
        reporte = (
            f"\n{'='*60}\n"
            f"⏰ HORA PC: {timestamp}\n"
            f"🔢 HEX (Primeros 64 bytes):\n{hex_view}\n"
            f"📝 TEXTO: {texto_limpio}\n"
            f"{'='*60}\n"
        )
        
        print(reporte)
        
        with open("RADIOGRAFIA_RELOJ.txt", "a", encoding="utf-8") as f:
            f.write(reporte)
            
    except Exception as e:
        print(f"Error en espía: {e}")

# --- BLOQUE PRINCIPAL ---
if __name__ == "__main__":
    print("🕵️ INICIANDO ESCÁNER COMPATIBLE...")
    print("⚠️  Asegúrate de que main.py esté CERRADO.")
    
    if os.path.exists("config.json"):
        with open("config.json", 'r') as f:
            config = json.load(f)
    else:
        config = {"ip_reloj": "192.168.1.201", "usuario_reloj": "admin", "clave_reloj": "CAMBIAR_CLAVE_DEL_RELOJ"}

    ip = config.get("ip_reloj")
    user = config.get("usuario_reloj")
    clave = config.get("clave_reloj")

    motor = MotorSistema()
    print(f"🔌 Conectando a {ip}...")
    
    # Pasamos la función que acepta 1 argumento
    if motor.conectar_sdk(ip, user, clave, callback_espia):
        print("✅ CONECTADO Y ESCUCHANDO.")
        print("📂 Guardando en 'RADIOGRAFIA_RELOJ.txt'...")
        print("👉 ¡Haz fichar a alguien o espera que el reloj mande basura!")
        print("❌ Presiona Ctrl + C para salir.")
        
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nApagando escáner...")
            motor.liberar_recursos()
    else:
        print("❌ Error de conexión.")
