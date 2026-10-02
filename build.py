import PyInstaller.__main__
import os
import shutil

# --- CONFIGURACIÓN DE LA COMPILACIÓN ---
NOMBRE_APP = "Sistema_FrutEm_V79"
ICONO = "iconos/logo.ico"  # Asegúrate de tener un .ico, si no, pon None o comenta
MAIN_FILE = "main.py"

# Verificar si existe carpeta iconos, si no, crearla dummy para que no falle
if not os.path.exists("iconos"):
    os.makedirs("iconos")

# --- GENERAR LISTA DE DATOS OCULTOS DE CUSTOMTKINTER ---
import customtkinter
ctk_path = os.path.dirname(customtkinter.__file__)

# Argumentos para PyInstaller
args = [
    MAIN_FILE,
    f'--name={NOMBRE_APP}',
    '--noconfirm',
    '--windowed',  # No mostrar consola negra (cámbialo a --console si quieres ver errores al inicio)
    '--clean',
    
    # INCLUIR CARPETA DE TEMAS DE CUSTOMTKINTER (CRÍTICO)
    f'--add-data={ctk_path};customtkinter/',
    
    # INCLUIR TUS RECURSOS
    '--add-data=iconos;iconos/',
    '--add-data=logo.png;.',
    
    # IMPORTACIONES OCULTAS QUE A VECES FALLAN
    '--hidden-import=PIL._tkinter_finder',
    '--hidden-import=mysql.connector',
    '--hidden-import=babel.numbers',
    '--hidden-import=ctypes',
    
    # EXCLUIR MÓDULOS INNECESARIOS PARA ALIGERAR
    '--exclude-module=tkinter.test',
    '--exclude-module=matplotlib',
    '--exclude-module=scipy',
]

# Si tienes icono .ico
if ICONO and os.path.exists(ICONO):
    args.append(f'--icon={ICONO}')

print("🚀 INICIANDO COMPILACIÓN DE FRUT&EM...")
PyInstaller.__main__.run(args)

print("\n✅ COMPILACIÓN FINALIZADA.")
print("📂 Buscando archivos críticos para copiar a la carpeta dist/...")

# --- POST-COMPILACIÓN: COPIAR ARCHIVOS EXTERNOS ---
# Como usas una DLL y un config.json que se pueden editar, 
# es MEJOR tenerlos al lado del EXE y no empaquetados dentro.

dist_path = os.path.join("dist", NOMBRE_APP)

# 1. Copiar DLL de Hikvision (CRÍTICO)
dll_name = "HCNetSDK.dll"
if os.path.exists(dll_name):
    shutil.copy(dll_name, os.path.join(dist_path, dll_name))
    print(f"   -> Copiada {dll_name}")
else:
    print(f"⚠️  ADVERTENCIA: No encontré {dll_name}. Recuerda ponerla junto al exe.")

# 2. Copiar config.json (Para que el usuario pueda cambiar la IP sin recompilar)
config_name = "config.json"
if os.path.exists(config_name):
    shutil.copy(config_name, os.path.join(dist_path, config_name))
    print(f"   -> Copiado {config_name}")

# 3. Crear carpeta de fotos
fotos_dir = os.path.join(dist_path, "fotos_empleados")
if not os.path.exists(fotos_dir):
    os.makedirs(fotos_dir)
    print("   -> Creada carpeta fotos_empleados")

print(f"\n✨ ¡LISTO! Tu sistema está en la carpeta: dist/{NOMBRE_APP}")