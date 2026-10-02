import os
import sys
import unicodedata
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)
sys.path.insert(0, BASE_DIR)

from motor import MotorSistema


DEMO_ID_MIN = 901
DEMO_ID_MAX = 930
CARPETA_FOTOS = os.path.join(BASE_DIR, "fotos_personal")

FOTOS_CAJERO_URLS = [
    "https://images.pexels.com/photos/3907119/pexels-photo-3907119.jpeg?auto=compress&cs=tinysrgb&w=600",
    "https://images.pexels.com/photos/4921256/pexels-photo-4921256.jpeg?auto=compress&cs=tinysrgb&w=600",
    "https://images.pexels.com/photos/6925905/pexels-photo-6925905.jpeg?auto=compress&cs=tinysrgb&w=600",
    "https://images.pexels.com/photos/7772128/pexels-photo-7772128.jpeg?auto=compress&cs=tinysrgb&w=600",
    "https://images.pexels.com/photos/36730429/pexels-photo-36730429.jpeg?auto=compress&cs=tinysrgb&w=600",
]

ROL_KEYWORDS = {
    "maestro panadero": ["maestro_panadero", "panadero"],
    "ayudante cocina": ["ayudante_cocina", "cocina"],
    "cajero/a": ["cajero", "cajera", "cashier"],
    "atencion mostrador": ["atencion_mostrador", "atención_mostrador", "mostrador"],
    "limpieza": ["limpieza"],
    "repartidor": ["repartidor"],
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto.lower().replace(" ", "_")


def descargar_fotos_cajero_si_faltan():
    os.makedirs(CARPETA_FOTOS, exist_ok=True)
    headers = {"User-Agent": "Mozilla/5.0"}
    for idx, url in enumerate(FOTOS_CAJERO_URLS, 1):
        destino = os.path.join(CARPETA_FOTOS, f"cajera_mostrador_cobrando_{idx}.jpg")
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=25) as response:
                contenido = response.read()
            if len(contenido) > 5000:
                with open(destino, "wb") as f:
                    f.write(contenido)
                print(f"Foto cajero/a descargada: {os.path.basename(destino)}")
        except Exception as exc:
            print(f"No se pudo descargar foto cajero/a {idx}: {exc}")


def listar_fotos_por_rol():
    fotos = {}
    archivos = [
        os.path.join(CARPETA_FOTOS, nombre)
        for nombre in sorted(os.listdir(CARPETA_FOTOS))
        if nombre.lower().endswith((".jpg", ".jpeg", ".png"))
    ]

    for rol, keywords in ROL_KEYWORDS.items():
        fotos[rol] = []
        for archivo in archivos:
            nombre_norm = normalizar(os.path.basename(archivo))
            if any(normalizar(keyword) in nombre_norm for keyword in keywords):
                fotos[rol].append(archivo.replace("\\", "/"))

    return fotos


def detectar_rol(nombre_empleado):
    if "(" not in nombre_empleado:
        return ""
    return nombre_empleado.split("(", 1)[1].split(")", 1)[0].strip().lower()


def ajustar_fotos():
    descargar_fotos_cajero_si_faltan()
    fotos_por_rol = listar_fotos_por_rol()
    contadores = {rol: 0 for rol in fotos_por_rol}

    sistema = MotorSistema()
    conn = sistema.get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT id_reloj, nombre
        FROM empleados
        WHERE CAST(id_reloj AS UNSIGNED) BETWEEN %s AND %s
        ORDER BY CAST(id_reloj AS UNSIGNED)
        """,
        (DEMO_ID_MIN, DEMO_ID_MAX),
    )
    empleados = cursor.fetchall()

    actualizados = 0
    for id_reloj, nombre in empleados:
        rol = detectar_rol(nombre)
        fotos = fotos_por_rol.get(rol, [])
        if not fotos:
            print(f"Sin foto disponible para {id_reloj} - {nombre}")
            continue

        idx = contadores[rol] % len(fotos)
        contadores[rol] += 1
        foto = fotos[idx]
        cursor.execute(
            "UPDATE empleados SET foto_path = %s WHERE id_reloj = %s",
            (foto, id_reloj),
        )
        actualizados += 1
        print(f"{id_reloj} -> {rol}: {os.path.basename(foto)}")

    conn.commit()
    cursor.close()
    conn.close()

    print(f"LISTO. Fotos ajustadas por rol: {actualizados}/{len(empleados)}")


if __name__ == "__main__":
    ajustar_fotos()
