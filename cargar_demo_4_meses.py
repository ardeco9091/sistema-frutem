import os
import random
import unicodedata
from datetime import datetime, timedelta, time

from motor import MotorSistema


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

DEMO_ID_INICIO = 901
MESES_DEMO = 4
RAW_DEMO = "DEMO_4_MESES"

ROLES = [
    ("Maestro Panadero", 6500, time(4, 30), time(12, 30)),
    ("Ayudante Cocina", 3800, time(6, 30), time(14, 30)),
    ("Cajero/a", 4200, time(8, 0), time(16, 0)),
    ("Atencion Mostrador", 3500, time(9, 0), time(17, 0)),
    ("Limpieza", 3000, time(7, 0), time(15, 0)),
    ("Repartidor", 3800, time(10, 0), time(18, 0)),
]

NOMBRES = [
    "Juan Carlos Perez",
    "Maria Eugenia Lopez",
    "Carlos Alberto Gomez",
    "Ana Maria Rodriguez",
    "Luis Fernando Fernandez",
    "Laura Beatriz Garcia",
    "Jose Luis Martinez",
    "Marta Susana Gonzalez",
    "Miguel Angel Diaz",
    "Cristina Elizabeth Sanchez",
    "Jorge Daniel Romero",
    "Silvia Alejandra Ruiz",
    "Roberto Antonio Flores",
    "Patricia Noemi Cabrera",
    "Ricardo Manuel Benitez",
    "Nancy Beatriz Acosta",
    "Eduardo Fabian Medina",
    "Monica Liliana Herrera",
    "Sergio Adrian Silva",
    "Andrea Veronica Rojas",
    "Pablo Andres Molina",
    "Veronica Ines Castro",
    "Walter Hugo Ortiz",
    "Gisela Paola Ledesma",
    "Gustavo Adolfo Roldan",
    "Claudia Marcela Vega",
    "Hector Ramon Ferreyra",
    "Daniela Fernanda Luna",
    "Esteban Gabriel Rios",
    "Natalia Soledad Peralta",
]


ROL_KEYWORDS = {
    "Maestro Panadero": ["maestro_panadero", "panadero"],
    "Ayudante Cocina": ["ayudante_cocina", "cocina"],
    "Cajero/a": ["cajero", "cajera", "cashier"],
    "Atencion Mostrador": ["atencion_mostrador", "atención_mostrador", "mostrador"],
    "Limpieza": ["limpieza"],
    "Repartidor": ["repartidor"],
}


def normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return texto.lower().replace(" ", "_")


def listar_fotos_por_rol():
    base = os.path.dirname(os.path.abspath(__file__))
    carpeta = os.path.join(base, "fotos_personal")
    if not os.path.isdir(carpeta):
        return {}

    archivos = []
    for nombre in sorted(os.listdir(carpeta)):
        if nombre.lower().endswith((".jpg", ".jpeg", ".png")):
            archivos.append(os.path.join(carpeta, nombre).replace("\\", "/"))

    fotos_por_rol = {}
    for rol, keywords in ROL_KEYWORDS.items():
        fotos_por_rol[rol] = []
        for archivo in archivos:
            nombre_norm = normalizar(os.path.basename(archivo))
            if any(normalizar(keyword) in nombre_norm for keyword in keywords):
                fotos_por_rol[rol].append(archivo)

    return fotos_por_rol


def combinar_fecha_hora(fecha, hora_base, margen_minutos=12):
    minutos = random.randint(-margen_minutos, margen_minutos)
    dt = datetime.combine(fecha, hora_base) + timedelta(minutes=minutos)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def sumar_horas(fecha, hora_base, horas, margen_minutos=12):
    minutos = random.randint(-margen_minutos, margen_minutos)
    dt = datetime.combine(fecha, hora_base) + timedelta(hours=horas, minutes=minutos)
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def generar_empleados():
    fotos_por_rol = listar_fotos_por_rol()
    contadores = {rol: 0 for rol in fotos_por_rol}
    empleados = []

    for idx, nombre in enumerate(NOMBRES):
        rol, valor_hora, entrada, salida = ROLES[idx % len(ROLES)]
        fotos = fotos_por_rol.get(rol, [])
        if fotos:
            foto = fotos[contadores[rol] % len(fotos)]
            contadores[rol] += 1
        else:
            foto = "SIN_FOTO"
        id_reloj = str(DEMO_ID_INICIO + idx)
        empleados.append(
            {
                "id": id_reloj,
                "nombre": f"{nombre} ({rol})",
                "rol": rol,
                "valor_hora": valor_hora,
                "entrada": entrada,
                "salida": salida,
                "foto": foto,
            }
        )

    return empleados


def generar_fichadas(empleados):
    hoy = datetime.now().date()
    inicio = hoy - timedelta(days=MESES_DEMO * 30)
    fichadas = []

    fecha = inicio
    while fecha <= hoy:
        es_domingo = fecha.weekday() == 6
        es_sabado = fecha.weekday() == 5

        for emp in empleados:
            if es_domingo:
                continue

            # Ausencias moderadas para que los reportes parezcan reales.
            asistencia = 0.72 if es_sabado else 0.88
            if random.random() > asistencia:
                continue

            if fecha == hoy:
                # Hoy queda "vivo": algunos empleados ya salieron y otros siguen activos.
                fichadas.append((combinar_fecha_hora(fecha, emp["entrada"], 8), emp["id"], RAW_DEMO))
                if int(emp["id"]) % 3 == 0:
                    fichadas.append((sumar_horas(fecha, emp["entrada"], 8, 8), emp["id"], RAW_DEMO))
                continue

            if es_sabado:
                fichadas.append((combinar_fecha_hora(fecha, emp["entrada"], 10), emp["id"], RAW_DEMO))
                fichadas.append((sumar_horas(fecha, emp["entrada"], random.choice([4, 5, 6]), 10), emp["id"], RAW_DEMO))
                continue

            # Jornada completa con pausa de almuerzo para que aparezcan varias entradas/salidas.
            entrada_1 = combinar_fecha_hora(fecha, emp["entrada"], 10)
            salida_1 = sumar_horas(fecha, emp["entrada"], 4, 8)
            entrada_2 = sumar_horas(fecha, emp["entrada"], 4.5, 8)
            salida_2 = combinar_fecha_hora(fecha, emp["salida"], 12)
            fichadas.extend(
                [
                    (entrada_1, emp["id"], RAW_DEMO),
                    (salida_1, emp["id"], RAW_DEMO),
                    (entrada_2, emp["id"], RAW_DEMO),
                    (salida_2, emp["id"], RAW_DEMO),
                ]
            )

        fecha += timedelta(days=1)

    return fichadas


def cargar_demo_4_meses():
    random.seed(20260526)
    empleados = generar_empleados()
    fichadas = generar_fichadas(empleados)
    ids = [emp["id"] for emp in empleados]

    sistema = MotorSistema()
    conn = sistema.get_connection()
    cursor = conn.cursor()

    placeholders = ",".join(["%s"] * len(ids))

    print("--- CARGA DEMO 4 MESES FRUT&EM ---")
    print(f"Empleados demo: {ids[0]} a {ids[-1]}")
    print("Limpiando una carga demo anterior con esos IDs...")

    cursor.execute(f"DELETE FROM fichadas WHERE id_reloj IN ({placeholders})", ids)
    cursor.execute(f"DELETE FROM empleados WHERE id_reloj IN ({placeholders})", ids)

    print("Insertando empleados...")
    cursor.executemany(
        "INSERT INTO empleados (id_reloj, nombre, valor_hora, foto_path) VALUES (%s, %s, %s, %s)",
        [(emp["id"], emp["nombre"], emp["valor_hora"], emp["foto"]) for emp in empleados],
    )

    print(f"Insertando {len(fichadas)} fichadas...")
    cursor.executemany(
        "INSERT IGNORE INTO fichadas (fecha_hora, id_reloj, raw_data) VALUES (%s, %s, %s)",
        fichadas,
    )

    conn.commit()

    cursor.execute(f"SELECT COUNT(*) FROM empleados WHERE id_reloj IN ({placeholders})", ids)
    total_empleados = cursor.fetchone()[0]

    cursor.execute(f"SELECT COUNT(*) FROM fichadas WHERE id_reloj IN ({placeholders})", ids)
    total_fichadas = cursor.fetchone()[0]

    cursor.close()
    conn.close()

    print("LISTO.")
    print(f"Empleados demo cargados: {total_empleados}")
    print(f"Fichadas demo cargadas: {total_fichadas}")
    print("Periodo simulado: ultimos 4 meses hasta hoy.")
    print("Abri main.py y usa Monitor / Personal / Liquidacion para sacar capturas.")


if __name__ == "__main__":
    cargar_demo_4_meses()
