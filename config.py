import os
import json
import customtkinter as ctk
import sys


# --- RUTAS INTELIGENTES ---
# Esto detecta si estás corriendo en Python (código) o como EXE (congelado)
if getattr(sys, 'frozen', False):
    # Si es .exe, la ruta es donde está el archivo ejecutable
    ROOT_DIR = os.path.dirname(sys.executable)
else:
    # Si es código, la ruta es donde está este archivo .py
    ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:
    base_dir = os.path.dirname(os.path.abspath(__file__))

# Ahora forzamos a que config.json se busque SIEMPRE al lado del ejecutable
CONFIG_FILE = os.path.join(ROOT_DIR, "config.json")
DB_NAME = os.path.join(ROOT_DIR, "sistema_rrhh_full.db") # También aseguramos la DB local
CARPETA_FOTOS = os.path.join(base_dir, "fotos_personal")
DIR_FOTOS = os.path.join(ROOT_DIR, "fotos_empleados")
LOGO_PATH = os.path.join(ROOT_DIR, "logo.png")

# --- RUTAS ---
CONFIG_FILE = "config.json"
DB_NAME = "sistema_rrhh_full.db"
DIR_FOTOS = "fotos_empleados"
LOGO_PATH = "logo.png"

# --- COLORES EXACTOS V76 ---
COLOR_ACCENT = "#B71C1C"       # Rojo corporativo
COLOR_GOLD = "#FFD700"         # Dorado
COLOR_HOVER = "#D32F2F"        # Rojo hover
COLOR_FONDO_SPLASH = "#B71C1C" # Fondo carga
COLOR_BARRA = "#FFD700"        # Barra de carga
COLOR_TEXTO = "white"

# --- CONFIGURACIÓN DEFAULT ---
DEFAULT_CONFIG = {
    "ip_reloj": "192.168.1.201",
    "puerto": 8000,
    "usuario_reloj": "admin",
    "clave_reloj": "CAMBIAR_CLAVE_DEL_RELOJ",
    "app_user": "admin",
    "app_pass": "CAMBIAR_CLAVE_DE_LA_APP",
    "db_name": "sistema_rrhh_full.db",
    "db_config": {
        "host": "localhost", # En la cajera cambiarás esto por la IP del admin
        "user": "root",
        "password": "",
        "database": "sistema_rrhh",
        "port": 3306
    }
}

def cargar_config():
    if not os.path.exists(CONFIG_FILE):
        try:
            # CORRECCIÓN: 'with' debe ir en su propia línea indentada
            with open(CONFIG_FILE, 'w') as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        except:
            pass
        return DEFAULT_CONFIG
    
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except:
        return DEFAULT_CONFIG

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")
