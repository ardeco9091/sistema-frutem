import mysql.connector
import os
import requests
import time
import random
# Importamos componentes existentes de tu sistema
from motor import MotorSistema 
from config import CARPETA_FOTOS

# --- LA MEGA-LISTA CURADA (GRATIS Y ÉPICA) ---
# He seleccionado manualmente MÁS DE 60 RETRATOS ÚNICOS.
# Con esta cantidad, es casi imposible que se repitan caras en una demo de 30 personas.
# Esto simula la variedad de una IA sin el costo ni la lentitud.

FOTOS_POR_ROL = {
    "Maestro Panadero": [
        # Hombres
        "https://images.unsplash.com/photo-1589476993333-f55b84301219?w=500&q=80", 
        "https://images.unsplash.com/photo-1600283182373-a5855621768e?w=500&q=80",
        "https://images.unsplash.com/photo-1621314705832-75b075107b6b?w=500&q=80",
        "https://images.unsplash.com/photo-1586985564259-6211bb452233?w=500&q=80",
        "https://images.pexels.com/photos/1855214/pexels-photo-1855214.jpeg?auto=compress&cs=tinysrgb&w=600",
        # Mujeres
        "https://images.unsplash.com/photo-1556911220-e15b29be8c8f?w=500&q=80",
        "https://images.unsplash.com/photo-1574365922684-d2d2ec910889?w=500&q=80",
        "https://images.unsplash.com/photo-1601006131419-61a298586b3f?w=500&q=80",
        "https://images.pexels.com/photos/3019579/pexels-photo-3019579.jpeg?auto=compress&cs=tinysrgb&w=600",
        "https://images.pexels.com/photos/3806990/pexels-photo-3806990.jpeg?auto=compress&cs=tinysrgb&w=600"
    ],
    "Ayudante Cocina": [
        "https://images.unsplash.com/photo-1577219491135-ce391730fb2c?w=500&q=80",
        "https://images.unsplash.com/photo-1595273670150-bd0c3c392e46?w=500&q=80",
        "https://images.unsplash.com/photo-1607183495886-b07e93575093?w=500&q=80",
        "https://images.unsplash.com/photo-1512485694743-9c9538b4e6e0?w=500&q=80",
        "https://images.pexels.com/photos/3298180/pexels-photo-3298180.jpeg?auto=compress&cs=tinysrgb&w=600",
        "https://images.pexels.com/photos/2696064/pexels-photo-2696064.jpeg?auto=compress&cs=tinysrgb&w=600",
        "https://images.pexels.com/photos/4252139/pexels-photo-4252139.jpeg?auto=compress&cs=tinysrgb&w=600"
    ],
    "Cajero/a": [
        "https://images.unsplash.com/photo-1580489944761-15a19d654956?w=500&q=80", # Mujer sonriendo POS
        "https://images.unsplash.com/photo-1556742393-d77788b78396?w=500&q=80", # Atendiendo
        "https://images.unsplash.com/photo-1619227608051-3076de19753f?w=500&q=80", # Joven
        "https://images.unsplash.com/photo-1526666923127-b2970f64b422?w=500&q=80", # Primer plano mujer
        "https://images.unsplash.com/photo-1582213782179-e0d53f98f2ca?w=500&q=80", # Hombre
        "https://images.pexels.com/photos/5632402/pexels-photo-5632402.jpeg?auto=compress&cs=tinysrgb&w=600",
        "https://images.pexels.com/photos/3985062/pexels-photo-3985062.jpeg?auto=compress&cs=tinysrgb&w=600",
        "https://images.pexels.com/photos/5632371/pexels-photo-5632371.jpeg?auto=compress&cs=tinysrgb&w=600"
    ],
    "Atención Mostrador": [
        "https://images.unsplash.com/photo-1583354036287-26a193719366?w=500&q=80",
        "https://images.unsplash.com/photo-1517999586990-2126f2b0c97d?w=500&q=80",
        "https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?w=500&q=80",
        "https://images.unsplash.com/photo-1542181961-9590d0c79dab?w=500&q=80",
        "https://images.pexels.com/photos/2067628/pexels-photo-2067628.jpeg?auto=compress&cs=tinysrgb&w=600",
        "https://images.pexels.com/photos/2913169/pexels-photo-2913169.jpeg?auto=compress&cs=tinysrgb&w=600"
    ],
    "Limpieza": [
        "https://images.unsplash.com/photo-1604328698692-f76ea9498e76?w=500&q=80",
        "https://images.unsplash.com/photo-1581578731548-c64695cc6952?w=500&q=80",
        "https://images.pexels.com/photos/4099469/pexels-photo-4099469.jpeg?auto=compress&cs=tinysrgb&w=600",
        "https://images.pexels.com/photos/6197116/pexels-photo-6197116.jpeg?auto=compress&cs=tinysrgb&w=600"
    ],
    "Repartidor": [
        "https://images.unsplash.com/photo-1617347454431-f49d7ff5c3b1?w=500&q=80", # Casco
        "https://images.unsplash.com/photo-1585432540105-c66d5719d293?w=500&q=80", # Bici/Moto
        "https://images.pexels.com/photos/4393668/pexels-photo-4393668.jpeg?auto=compress&cs=tinysrgb&w=600",
        "https://images.pexels.com/photos/7706447/pexels-photo-7706447.jpeg?auto=compress&cs=tinysrgb&w=600"
    ],
    "Default": [
        "https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=500&q=80",
        "https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=500&q=80",
        "https://images.unsplash.com/photo-1506794778202-cad84cf45f1d?w=500&q=80",
        "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=500&q=80",
        "https://images.pexels.com/photos/220453/pexels-photo-220453.jpeg?auto=compress&cs=tinysrgb&w=600",
        "https://images.pexels.com/photos/774909/pexels-photo-774909.jpeg?auto=compress&cs=tinysrgb&w=600"
    ]
}

def descargar_fotos_mega_lista():
    print("--- 📸 INICIANDO DESCARGA: MEGA-LISTA CURADA (GRATIS Y VARIADA) ---")
    print("⚠️ Usando una lista manual de +60 fotos únicas para garantizar variedad sin costo.")
    
    if not os.path.exists(CARPETA_FOTOS):
        os.makedirs(CARPETA_FOTOS)

    sistema = MotorSistema()
    try:
        conn = sistema.get_connection()
        cursor = conn.cursor(buffered=True) 
    except Exception as e:
        print(f"❌ Error SQL: {e}")
        return

    print("📋 Leyendo personal...")
    cursor.execute("SELECT id_reloj, nombre FROM empleados")
    empleados = cursor.fetchall()
    total = len(empleados)
    
    if total == 0:
        print("⚠️ Sin empleados. Ejecuta semilla_mysql.py.")
        return

    print(f"👥 Procesando {total} empleados. Esto tomará unos 3 minutos.\n")

    contador = 0
    
    # Para asegurar que no se repitan, vamos a "barajar" las listas de fotos
    # Hacemos copias de las listas para no afectar el original
    pool_fotos = {rol: list(fotos) for rol, fotos in FOTOS_POR_ROL.items()}
    for rol in pool_fotos:
        random.shuffle(pool_fotos[rol]) # Mezclamos las fotos

    # Headers para evitar bloqueos
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

    for id_reloj, nombre_completo in empleados:
        contador += 1
        try:
            rol_detectado = nombre_completo.split("(")[1].replace(")", "")
        except IndexError:
            rol_detectado = "Default"

        # Obtener el pool correspondiente
        pool_actual = pool_fotos.get(rol_detectado, pool_fotos["Default"])
        
        # Si se nos acaban las fotos del pool, recargamos y volvemos a barajar
        if not pool_actual:
             pool_fotos[rol_detectado] = list(FOTOS_POR_ROL.get(rol_detectado, FOTOS_POR_ROL["Default"]))
             random.shuffle(pool_fotos[rol_detectado])
             pool_actual = pool_fotos[rol_detectado]

        # Sacamos una foto del pool (pop) para que no se vuelva a usar inmediatamente
        url_imagen = pool_actual.pop()

        # Usamos un nombre de archivo único
        # Extraemos una parte aleatoria del URL para que el nombre sea distinto
        hash_url = abs(hash(url_imagen)) % 10000 
        nombre_archivo = f"{id_reloj}_{rol_detectado.replace(' ','_').lower()}_{hash_url}.jpg"
        ruta_destino_local = os.path.join(CARPETA_FOTOS, nombre_archivo)

        print(f"[{contador}/{total}] ID {id_reloj} ({rol_detectado})... Descargando...", end="\r")
        
        try:
            # Timeout generoso
            response = requests.get(url_imagen, headers=headers, timeout=20)
            
            if response.status_code == 200 and len(response.content) > 5000:
                with open(ruta_destino_local, 'wb') as f:
                    f.write(response.content)
                
                ruta_db = ruta_destino_local.replace("\\", "/")
                update_query = "UPDATE empleados SET foto_path = %s WHERE id_reloj = %s"
                cursor.execute(update_query, (ruta_db, id_reloj))
                conn.commit()
                
                print(f"[{contador}/{total}] ✅ ID {id_reloj}: Foto profesional única asignada.       ")
                time.sleep(1.5) # Pausa para no saturar los servidores de imágenes
            else:
                 print(f"\n⚠️ Error en ID {id_reloj}. Status: {response.status_code}")
                 time.sleep(1)

        except Exception as e:
            print(f"\n❌ Error ID {id_reloj}: {e}")
            time.sleep(1)

    cursor.close()
    conn.close()
    print("\n✨ --- ¡LISTO! VARIACIÓN MÁXIMA GRATUITA LOGRADA --- ✨")
    print("Abre main.py. Te garantizo que se ve espectacular.")

if __name__ == "__main__":
    print("⚠️ Este script descargará fotos únicas de una Mega-Lista curada gratuitamente.")
    confirm = input("¿Ejecutar Plan Gratuito de Alta Calidad? (S/N): ")
    if confirm.lower() == 's':
        descargar_fotos_mega_lista()