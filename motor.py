import mysql.connector 
import os
import ctypes
import json
from datetime import datetime
from config import CONFIG_FILE, DIR_FOTOS

# --- ESTRUCTURAS C (HIKVISION SDK) ---

class NET_DVR_ALARMER(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("byUserIDValid", ctypes.c_byte), ("bySerialValid", ctypes.c_byte), ("byVersionValid", ctypes.c_byte), ("byDeviceNameValid", ctypes.c_byte), ("byMacAddrValid", ctypes.c_byte), ("byLinkPortValid", ctypes.c_byte), ("byDeviceIPValid", ctypes.c_byte), ("bySocketIPValid", ctypes.c_byte), ("lUserID", ctypes.c_int), ("sSerialNumber", ctypes.c_byte*48), ("dwDeviceVersion", ctypes.c_uint), ("sDeviceName", ctypes.c_byte*32), ("byMacAddr", ctypes.c_byte*6), ("wLinkPort", ctypes.c_ushort), ("sDeviceIP", ctypes.c_byte*128), ("sSocketIP", ctypes.c_byte*128), ("byIpProtocol", ctypes.c_byte), ("byRes2", ctypes.c_byte*11)]

class NET_DVR_TIME(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("dwYear", ctypes.c_int), ("dwMonth", ctypes.c_int), ("dwDay", ctypes.c_int), ("dwHour", ctypes.c_int), ("dwMinute", ctypes.c_int), ("dwSecond", ctypes.c_int)]

# ESTA ES LA CLASE QUE FALTABA Y CAUSABA EL ERROR DE IMPORTACIÓN
class NET_DVR_ACS_EVENT_COND(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("dwSize", ctypes.c_uint), ("dwMajor", ctypes.c_uint), ("dwMinor", ctypes.c_uint), ("struStartTime", NET_DVR_TIME), ("struEndTime", NET_DVR_TIME), ("byCardNo", ctypes.c_byte*32), ("byName", ctypes.c_byte*32), ("byRes", ctypes.c_byte*256)]

class NET_DVR_ACS_EVENT_CFG(ctypes.Structure):
    _pack_ = 1
    _fields_ = [("dwSize", ctypes.c_uint), ("dwMajor", ctypes.c_uint), ("dwMinor", ctypes.c_uint), ("struTime", NET_DVR_TIME), ("byCardNo", ctypes.c_byte*32), ("byCardType", ctypes.c_byte), ("byWhiteListNo", ctypes.c_byte), ("byReportChannel", ctypes.c_byte), ("byCardReaderKind", ctypes.c_byte), ("dwCardReaderNo", ctypes.c_uint), ("dwDoorNo", ctypes.c_uint), ("dwVerifyNo", ctypes.c_uint), ("dwAlarmInNo", ctypes.c_uint), ("dwAlarmOutNo", ctypes.c_uint), ("dwCaseSensorNo", ctypes.c_uint), ("dwRS485No", ctypes.c_uint), ("dwMultiCardGroupNo", ctypes.c_uint), ("wAccessChannel", ctypes.c_ushort), ("byDeviceNo", ctypes.c_byte), ("byDistinguish", ctypes.c_byte), ("byEmployeeNo", ctypes.c_byte*32), ("wLocalControllerID", ctypes.c_ushort), ("byInternetAccess", ctypes.c_byte), ("byType", ctypes.c_byte), ("byMacAddr", ctypes.c_byte*6), ("bySwipeCardType", ctypes.c_byte), ("byRes2", ctypes.c_byte), ("dwSerialNo", ctypes.c_uint), ("byChannelControllerID", ctypes.c_byte), ("byChannelControllerLampID", ctypes.c_byte), ("byChannelControllerIRAdaptorID", ctypes.c_byte), ("byRes3", ctypes.c_byte), ("byRes", ctypes.c_byte*102)]

# CALLBACK 5 ARGUMENTOS
MSG_CALLBACK = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.POINTER(NET_DVR_ALARMER), ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p)

# --- CLASE MOTOR ---
class MotorSistema:
    def __init__(self):
        self.db_config = self.cargar_config_db()
        self.init_db()
        self.sdk = None
        self.uid = -1
        self.known_ids = set()
        self.cb_func = None 

    def cargar_config_db(self):
        default = {"host":"localhost", "user":"root", "password":"", "database":"sistema_rrhh", "port":3306}
        try:
            with open(CONFIG_FILE, 'r') as f:
                data = json.load(f)
                return data.get("db_config", default)
        except: return default

    def get_connection(self):
        try:
            return mysql.connector.connect(
                host=self.db_config["host"],
                user=self.db_config["user"],
                password=self.db_config["password"],
                database=self.db_config["database"],
                port=self.db_config["port"],
                autocommit=True,
                connect_timeout=5 # No esperar eternamente si el servidor no responde
            )
        except mysql.connector.Error as err:
            print(f"❌ Error de conexión MySQL: {err}")
            raise # Re-lanzamos para que main.py sepa que falló

    def init_db(self):
        if not os.path.exists(DIR_FOTOS): os.makedirs(DIR_FOTOS)
        try:
            conn = self.get_connection()
            cursor = conn.cursor()

            # Agregar esto dentro de motor.py -> init_db()
           # Dentro de motor.py -> init_db()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stock (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    codigo_barras VARCHAR(50) UNIQUE,
                    modelo VARCHAR(100),
                    marca VARCHAR(50),
                    color VARCHAR(50),
                    talle DECIMAL(3,1), 
                    precio_venta DECIMAL(10,2),
                    cantidad INT DEFAULT 0,
                    INDEX idx_modelo (modelo),
                    INDEX idx_barras (codigo_barras)
                ) ENGINE=InnoDB
            """)
            
            # 1. Crear tabla empleados
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS empleados (
                    id_reloj VARCHAR(20) PRIMARY KEY, 
                    nombre VARCHAR(100), 
                    valor_hora DECIMAL(10,2), 
                    foto_path VARCHAR(255)
                ) ENGINE=InnoDB
            """)
            
            # 2. Crear tabla fichadas (Solo una vez)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fichadas (
                    id INT AUTO_INCREMENT PRIMARY KEY, 
                    fecha_hora DATETIME, 
                    id_reloj VARCHAR(20), 
                    raw_data VARCHAR(255),
                    UNIQUE KEY idx_fichada (fecha_hora, id_reloj)
                ) ENGINE=InnoDB
            """)
            
            # 3. Optimización: Índice para acelerar los reportes de Liquidación
            # Nota: 'IF NOT EXISTS' en índices requiere MySQL 8.0+. 
            # Si usas una versión anterior, el bloque try/except que te pasé antes es más seguro.
            try:
                cursor.execute("CREATE INDEX idx_fecha ON fichadas(fecha_hora)")
                print("🚀 Índice de rendimiento verificado")
            except: 
                pass 
                
            # 4. Limpiar registros de IDs que ya no existen
            cursor.execute("DELETE FROM fichadas WHERE id_reloj NOT IN (SELECT id_reloj FROM empleados)")
            
            cursor.close()
            conn.close()
            self.actualizar_lista_blanca()
            print("✅ Base de Datos MySQL Inicializada y Limpia")
            
        except Exception as e:
            print(f"❌ Error fatal iniciando DB: {e}")

    def actualizar_lista_blanca(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_reloj FROM empleados")
            self.known_ids = [str(r[0]) for r in cursor.fetchall()]
            cursor.close()
            conn.close()
        except: 
            self.known_ids = []

    def conectar_sdk(self, ip, user, password, callback_evento=None):
        print(f"\n--- CONECTANDO SDK a {ip} ---")
        if self.uid >= 0: return True
        
        try:
            ruta_dll = os.path.join(os.getcwd(), "HCNetSDK.dll")
            self.sdk = ctypes.CDLL(ruta_dll)
            self.sdk.NET_DVR_Init()
            self.sdk.NET_DVR_SetConnectTime(2000, 1)
            
            device_info = (ctypes.c_byte * 48)()
            self.uid = self.sdk.NET_DVR_Login_V30(ip.encode('utf-8'), 8000, user.encode('utf-8'), password.encode('utf-8'), ctypes.byref(device_info))
            
            if self.uid >= 0:
                print(f"✅ LOGIN OK (UID: {self.uid})")
                
                if callback_evento:
                    # ADAPTADOR QUE DEJA PASAR TODO Y AVISA
                    def adaptador_callback(lCommand, pAlarmer, pAlarmInfo, dwBufLen, pUser):
                        print(f"⚡ [MOTOR] ¡SEÑAL DETECTADA! Comando: {lCommand}")
                        try:
                            callback_evento(pAlarmInfo)
                        except Exception as e:
                            print(f"❌ Error enviando datos a main.py: {e}")

                    self.cb_func = MSG_CALLBACK(adaptador_callback)
                    
                    if not self.sdk.NET_DVR_SetDVRMessageCallBack_V30(self.cb_func, None):
                        print("❌ Falló SetDVRMessageCallBack")
                    
                    alarm_h = self.sdk.NET_DVR_SetupAlarmChan_V30(self.uid, 0)
                    if alarm_h < 0:
                        alarm_h = self.sdk.NET_DVR_SetupAlarmChan(self.uid)
                    
                    print(f"📡 Canal Alarma Activo: {alarm_h}")
                return True
            else:
                print(f"❌ Falló Login: {self.sdk.NET_DVR_GetLastError()}")
                return False
        except Exception as e:
            print(f"❌ Error Crítico Motor: {e}")
            return False

    # --- FUNCIONES DE BASE DE DATOS (RESTAURADAS) ---

    def obtener_todos_productos(self, filtro=""):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if filtro:
                query = "SELECT * FROM stock WHERE modelo LIKE %s OR codigo_barras LIKE %s"
                cursor.execute(query, (f"%{filtro}%", f"%{filtro}%"))
            else:
                cursor.execute("SELECT * FROM stock ORDER BY modelo ASC")
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return res
        except: return []

    def guardar_producto(self, datos):
        """datos: (codigo, modelo, marca, color, talle, precio, cantidad)"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            query = """INSERT INTO stock (codigo_barras, modelo, marca, color, talle, precio_venta, cantidad)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE cantidad = cantidad + VALUES(cantidad), precio_venta = VALUES(precio_venta)"""
            cursor.execute(query, datos)
            conn.commit()
            cursor.close()
            conn.close()
            return True, "Stock actualizado"
        except Exception as e: return False, str(e)

    def obtener_todos_empleados(self):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_reloj, nombre, valor_hora, foto_path FROM empleados ORDER BY CAST(id_reloj AS UNSIGNED)")
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return res
        except: return []

    def guardar_o_actualizar_empleado(self, id_nuevo, nombre, valor, path_foto, id_original=None):
        try:
            id_nuevo = str(int(id_nuevo))
            conn = self.get_connection()
            cursor = conn.cursor()
            if not id_original:
                cursor.execute("SELECT 1 FROM empleados WHERE id_reloj=%s", (id_nuevo,))
                if cursor.fetchone(): return False, "ID ya existe"
                cursor.execute("INSERT INTO empleados VALUES (%s,%s,%s,%s)", (id_nuevo, nombre, valor, path_foto))
            else:
                cursor.execute("UPDATE empleados SET id_reloj=%s, nombre=%s, valor_hora=%s, foto_path=%s WHERE id_reloj=%s", (id_nuevo, nombre, valor, path_foto, id_original))
                if id_nuevo != id_original:
                    cursor.execute("UPDATE fichadas SET id_reloj=%s WHERE id_reloj=%s", (id_nuevo, id_original))
            cursor.close()
            conn.close()
            self.actualizar_lista_blanca()
            return True, "Guardado OK"
        except Exception as e: return False, str(e)

    def obtener_estado_diario(self):
        try:
            hoy = datetime.now().strftime("%Y-%m-%d")
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id_reloj, fecha_hora FROM fichadas WHERE fecha_hora LIKE %s ORDER BY fecha_hora ASC", (f"{hoy}%",))
            fichas = cursor.fetchall()
            cursor.execute("SELECT id_reloj, nombre, foto_path FROM empleados")
            emps = {str(r[0]):(r[1],r[2]) for r in cursor.fetchall()}
            cursor.close()
            conn.close()
            
            agrupado = {}
            for eid, fh in fichas:
                eid = str(eid); fh = str(fh)
                if eid not in agrupado: agrupado[eid] = []
                agrupado[eid].append(fh)
            
            res = []
            for eid, lista in agrupado.items():
                if not lista: continue
                # Filtro visual simple
                limpias = [lista[0]]
                for t in lista[1:]:
                    d1 = datetime.strptime(t, "%Y-%m-%d %H:%M:%S")
                    d2 = datetime.strptime(limpias[-1], "%Y-%m-%d %H:%M:%S")
                    if (d1-d2).total_seconds() > 60: limpias.append(t)
                
                activo = len(limpias)%2!=0
                nm, ft = emps.get(eid, (f"ID {eid}", None))
                hin = datetime.strptime(limpias[0], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                hout = None if activo else datetime.strptime(limpias[-1], "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                res.append({"id":eid, "nombre":nm, "foto":ft, "activo":activo, "h_entrada":hin, "h_salida":hout})
            
            # Ordenar: Activos primero
            res.sort(key=lambda x: x["activo"], reverse=True)
            return res
        except: return []

    def registrar_venta_rapida(self, id_producto):
        """Descuenta una unidad del stock en MySQL."""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # Verificamos que haya stock antes de vender
            cursor.execute("SELECT cantidad FROM stock WHERE id=%s", (id_producto,))
            res = cursor.fetchone()
            
            if res and res[0] > 0:
                cursor.execute("UPDATE stock SET cantidad = cantidad - 1 WHERE id=%s", (id_producto,))
                conn.commit()
                cursor.close()
                conn.close()
                return True, "Venta realizada con éxito"
            else:
                return False, "Error: No hay stock disponible"
        except Exception as e:
            return False, str(e)

    def _calcular_horas_limpio(self, lista_fechas, es_hoy=False):
        """
        Calcula horas trabajadas filtrando rebotes y aplicando la regla 
        de seguridad para Turno Cortado (>12hs se descarta).
        """
        # 1. Asegurar que sean objetos datetime y ordenar
        timestamps = []
        for t in lista_fechas:
            try:
                dt = t if isinstance(t, datetime) else datetime.strptime(str(t), "%Y-%m-%d %H:%M:%S")
                # Filtro Anti-Rebote (2 minutos)
                if not timestamps or (dt - timestamps[-1]).total_seconds() > 120:
                    timestamps.append(dt)
            except: pass
        
        total_horas = 0.0
        i = 0
        now = datetime.now()

        while i < len(timestamps):
            start = timestamps[i]
            end = None

            # Buscamos pareja (Entrada -> Salida)
            if i + 1 < len(timestamps):
                end = timestamps[i+1]
                i += 2 # Usamos el par
            else:
                # Es impar (está trabajando actualmente)
                # Solo calculamos tiempo en vivo si es HOY
                if es_hoy and start.date() == now.date():
                    end = now
                i += 1 # Avanzamos

            if end:
                segundos = (end - start).total_seconds()
                horas_tramo = segundos / 3600
                
                # --- REGLA DE PROTECCIÓN TURNOS CORTADOS ---
                # Si un solo tramo dura más de 12 horas, asumimos que olvidó fichar
                # la salida del mediodía. Lo ignoramos para no inflar el pago.
                if horas_tramo > 12.0:
                    print(f"⚠️ Tramo ignorado por exceso ({horas_tramo:.2f}hs): Posible olvido de fichada.")
                else:
                    total_horas += horas_tramo
                    
        return total_horas

    def obtener_datos_perfil(self, id_reloj):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # 1. Datos Empleado
            cursor.execute("SELECT nombre, valor_hora, foto_path FROM empleados WHERE id_reloj=%s", (id_reloj,))
            datos = cursor.fetchone()
            if not datos: 
                cursor.close(); conn.close(); return None
            
            nom, val, fot = datos
            val = float(val)

            # 2. Fichadas HOY
            hoy_str = datetime.now().strftime("%Y-%m-%d")
            cursor.execute("SELECT fecha_hora FROM fichadas WHERE id_reloj=%s AND fecha_hora LIKE %s ORDER BY fecha_hora ASC", (id_reloj, f"{hoy_str}%"))
            rows_hoy = [r[0] for r in cursor.fetchall()]

            # 3. Fichadas MES
            mes_str = datetime.now().strftime("%Y-%m")
            cursor.execute("SELECT fecha_hora FROM fichadas WHERE id_reloj=%s AND fecha_hora LIKE %s ORDER BY fecha_hora ASC", (id_reloj, f"{mes_str}%"))
            rows_mes = [r[0] for r in cursor.fetchall()]
            
            cursor.close()
            conn.close()

            # 4. Cálculo Inteligente usando el nuevo método
            hh_hoy = self._calcular_horas_limpio(rows_hoy, es_hoy=True)
            hh_mes = self._calcular_horas_limpio(rows_mes, es_hoy=False)

            return (nom, val, fot, (hh_hoy*val), hh_hoy, (hh_mes*val), hh_mes)

        except Exception as e:
            print(f"Error Perfil: {e}")
            return None

    def obtener_historial_reciente(self, id_reloj):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT fecha_hora FROM fichadas WHERE id_reloj=%s ORDER BY fecha_hora DESC LIMIT 10", (id_reloj,))
            res = cursor.fetchall()
            cursor.close()
            conn.close()
            return [(str(r[0]),) for r in res]
        except: return []

    def buscar_fichadas_historial(self, filtro_texto, fecha_filtro):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            # SQL con JOIN y búsqueda de texto
            query = """
                SELECT f.id, f.fecha_hora, f.id_reloj, e.nombre, f.raw_data 
                FROM fichadas f
                LEFT JOIN empleados e ON f.id_reloj = e.id_reloj
                WHERE f.fecha_hora LIKE %s 
                AND (e.nombre LIKE %s OR f.id_reloj LIKE %s)
                ORDER BY f.fecha_hora DESC
            """
            busqueda = f"%{filtro_texto}%"
            cursor.execute(query, (f"{fecha_filtro}%", busqueda, busqueda))
            res = cursor.fetchall()
            
            # Limpieza de nulos (si el empleado no existe en la tabla empleados)
            resultado = []
            for r in res:
                fila = list(r)
                if fila[3] is None: fila[3] = "⚠️ NO REGISTRADO"
                resultado.append(fila)
                
            cursor.close()
            conn.close()
            return resultado
        except Exception as e:
            print(f"Error Historial: {e}")
            return []

    def eliminar_fichada(self, id_db):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM fichadas WHERE id=%s", (id_db,))
            cursor.close()
            conn.close()
            return True
        except: return False

    def guardar_fichada_manual(self, id_db, id_reloj, fecha_hora):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            if id_db:
                cursor.execute("UPDATE fichadas SET fecha_hora=%s, id_reloj=%s, raw_data=%s WHERE id=%s", (fecha_hora, id_reloj, "CORRECCION", id_db))
            else:
                cursor.execute("INSERT INTO fichadas (fecha_hora, id_reloj, raw_data) VALUES (%s,%s,%s)", (fecha_hora, id_reloj, "MANUAL"))
            cursor.close()
            conn.close()
            return True
        except: return False

    

    # [MODIFICADO] Ahora recibe 'filtro_input' (opcional)
    def calcular_liquidacion_rango(self, f_inicio, f_fin, filtro_input=None):
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Traemos fichadas del rango (Esto sigue igual, traemos todo y filtramos en Python)
            # Es más seguro filtrar en Python para busquedas parciales de texto
            cursor.execute("SELECT id_reloj, fecha_hora FROM fichadas WHERE fecha_hora >= %s AND fecha_hora <= %s ORDER BY id_reloj, fecha_hora ASC", (f"{f_inicio} 00:00:00", f"{f_fin} 23:59:59"))
            fichas = cursor.fetchall()
            
            cursor.execute("SELECT id_reloj, nombre, valor_hora FROM empleados")
            emps = cursor.fetchall()
            cursor.close()
            conn.close()
            
            dict_emps = {str(r[0]): {'n': r[1], 'v': float(r[2])} for r in emps}
            agenda = {}

            # Agrupar fichadas por Empleado -> Día
            for eid, dt in fichas:
                eid = str(eid)
                dt = dt if isinstance(dt, datetime) else datetime.strptime(str(dt), "%Y-%m-%d %H:%M:%S")
                dia = dt.strftime("%Y-%m-%d")
                
                if eid not in agenda: agenda[eid] = {}
                if dia not in agenda[eid]: agenda[eid][dia] = []
                
                lista = agenda[eid][dia]
                if not lista or (dt - lista[-1]).total_seconds() > 60: 
                    lista.append(dt)
            
            res = []
            
            # Normalizamos el filtro a minúsculas para buscar fácil
            filtro_limpio = filtro_input.lower().strip() if filtro_input else ""

            for eid, dias in agenda.items():
                e = dict_emps.get(eid, {'n': f"ID {eid}", 'v': 0})
                nombre_emp = e['n']

                # --- LÓGICA DE FILTRADO ---
                # Si hay filtro escrito, y el nombre NO contiene ese texto, saltamos al siguiente
                # También permitimos buscar por ID exacto si el usuario escribió un número
                if filtro_limpio:
                    coincide_nombre = filtro_limpio in nombre_emp.lower()
                    coincide_id = (filtro_limpio == eid)
                    
                    if not (coincide_nombre or coincide_id):
                        continue # Saltamos este empleado, no lo agregamos a la lista
                # --------------------------
                
                for dia, lista in dias.items():
                    h_dia = 0.0
                    txt_ent = []
                    txt_sal = []
                    es_error = False
                    
                    i = 0
                    while i < len(lista):
                        t1 = lista[i]
                        t2 = None
                        if i+1 < len(lista): 
                            t2 = lista[i+1]; i += 2
                        else: 
                            i += 1 

                        s1 = t1.strftime("%H:%M")
                        txt_ent.append(s1)
                        
                        if t2:
                            s2 = t2.strftime("%H:%M")
                            horas_bloque = (t2-t1).total_seconds()/3600
                            if horas_bloque > 12.0:
                                txt_sal.append(f"{s2} (!)")
                                es_error = True
                            else:
                                h_dia += horas_bloque
                                txt_sal.append(s2)
                        else:
                            txt_sal.append("?")

                    pago = h_dia * e['v']
                    str_ent = " | ".join(txt_ent)
                    str_sal = " | ".join(txt_sal)

                    if h_dia > 0 or txt_ent: 
                        res.append({
                            "ID": eid,
                            "FECHA": dia, 
                            "EMPLEADO": nombre_emp, 
                            "ENTRADAS": str_ent, 
                            "SALIDAS": str_sal, 
                            "HS": round(h_dia, 2), 
                            "PAGO": round(pago, 2),
                            "ERROR": es_error
                        })
            
            res.sort(key=lambda x: (x["FECHA"], x["EMPLEADO"]))
            return res

        except Exception as e: 
            print(f"Error Liq: {e}")
            return []