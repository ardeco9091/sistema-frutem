import os

# Obtenemos la ruta donde estamos parados
ruta_base = os.path.dirname(os.path.abspath(__file__))
ruta_iconos = os.path.join(ruta_base, "iconos")

print("-" * 30)
print(f"📂 Ruta Base: {ruta_base}")
print(f"📂 Ruta Iconos: {ruta_iconos}")
print("-" * 30)

if os.path.exists(ruta_iconos):
    print("✅ La carpeta 'iconos' EXISTE.")
    print("📄 Archivos encontrados dentro:")
    archivos = os.listdir(ruta_iconos)
    for a in archivos:
        print(f"   👉 '{a}'")
        
    # Prueba específica con monitor
    ruta_mon = os.path.join(ruta_iconos, "monitor.png")
    if os.path.exists(ruta_mon):
        print("\n✅ El archivo 'monitor.png' EXISTE y Python lo ve.")
        try:
            from PIL import Image
            img = Image.open(ruta_mon)
            print(f"✅ Pillow pudo abrir la imagen. Tamaño: {img.size}")
        except ImportError:
            print("❌ ERROR: No tienes instalada la librería Pillow (pip install Pillow)")
        except Exception as e:
            print(f"❌ ERROR al abrir la imagen: {e}")
    else:
        print("\n❌ EL ARCHIVO 'monitor.png' NO EXISTE (Revisa si se llama .png.png)")
else:
    print("❌ ERROR FATAL: Python no encuentra la carpeta 'iconos'.")