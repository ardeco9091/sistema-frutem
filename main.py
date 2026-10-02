import customtkinter as ctk
from tkinter import ttk, messagebox, filedialog
import sys
import os
import threading
import time
# import pandas as pd  <-- Ya no es estrictamente necesario en main.py si reportes.py se encarga
import calendar
import shutil
import sqlite3
import re
import traceback
import ctypes
from datetime import datetime, timedelta
from PIL import Image, ImageTk
import json
import traceback


def manejar_errores_caja(tipo, valor, traza):
    """Función para capturar errores y guardarlos en un archivo antes de cerrar."""
    mensaje = "".join(traceback.format_exception(tipo, valor, traza))
    with open("ERROR_LOG_CAJA.txt", "a") as f:
        f.write(f"\n{'='*50}\n")
        f.write(f"FECHA: {datetime.now()}\n")
        f.write(f"ERROR: {mensaje}\n")
    # Mostrar mensaje amigable al usuario
    from tkinter import messagebox
    messagebox.showerror("Error del Sistema", 
                         f"Ocurrió un problema: {valor}\nSe ha guardado el detalle en ERROR_LOG_CAJA.txt")

# Conectamos la función al sistema
sys.excepthook = manejar_errores_caja

# En main.py, después de los imports:

# --- FIX PARA WINDOWS 7 ---
try:
    # Intentamos decirle a Windows que ya somos "DPI Aware" para evitar conflictos gráficos
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except:
        pass # Si falla (ej. Win 7 muy viejo), seguimos sin hacer nada
# --------------------------

# --- CONFIGURACIÓN DE COLORES Y RUTAS ---
# Definimos valores por defecto por si falta config.py
COLOR_ACCENT = "#8B0000"
COLOR_HOVER = "#A52A2A"
COLOR_TEXTO = "white"
COLOR_FONDO_SPLASH = "#2b2b2b"
COLOR_BARRA = "#FF0000"
COLOR_GOLD = "#FFD700"
DB_NAME = "sistema_rrhh_full.db"
DIR_FOTOS = "fotos_empleados"
LOGO_PATH = "logo.png"
CONFIG_FILE = "config.json"

if not os.path.exists(DIR_FOTOS):
    os.makedirs(DIR_FOTOS)

# --- IMPORTACIONES MODULARES (INTENTO) ---
# --- IMPORTACIONES MODULARES ---
motor = None
config_data = {}

try:
    try: from config import *
    except: pass 
    
    from motor import MotorSistema, NET_DVR_ACS_EVENT_COND, NET_DVR_TIME
    
    # IMPORTAMOS REPORTES Y SI FALLA, QUE NOS AVISE FUERTE
    try:
        import reportes
    except ImportError as e:
        messagebox.showerror("Error Crítico", f"No se pudo cargar el módulo de reportes.\n¿Instalaste las librerías?\nError: {e}")
        # Creamos un reportes 'dummy' para que no crashee todo, pero avisamos
        class reportes:
            @staticmethod
            def generar_nombre(ext): return f"error.{ext}"
    
    motor = MotorSistema()
    # ... resto del código ...
    
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config_data = json.load(f)
    else:
        # Configuración por defecto si no existe el archivo
        config_data = {
            "ip_reloj": "192.168.1.201", "puerto": 8000,
            "usuario_reloj": "admin", "clave_reloj": "CAMBIAR_CLAVE_DEL_RELOJ",
            "app_user": "admin", "app_pass": "admin",
            "db_name": "sistema_rrhh_full.db"
        }

except Exception as e:
    print(f"Advertencia iniciando motor/config: {e}")

# --- MANEJO DE ERRORES GLOBAL ---
def manejar_errores_criticos(tipo, valor, traza):
    mensaje_error = "".join(traceback.format_exception(tipo, valor, traza))
    with open("ERROR_LOG.txt", "a") as f:
        f.write(f"\n\n--- ERROR {datetime.now()} ---\n")
        f.write(mensaje_error)
    try:
        messagebox.showerror("Error Crítico", f"Ocurrió un error inesperado:\n{valor}\nRevisa ERROR_LOG.txt")
    except: pass

    # --- FUNCIÓN AUXILIAR PARA FORMATEAR HORAS ---
def decimal_a_hm(horas_decimales):
    """Convierte 7.75 (decimal) a '07:45' (texto HH:MM) para visualización."""
    try:
        if not horas_decimales or horas_decimales < 0: return "00:00"
        
        horas = int(horas_decimales)
        minutos_dec = (horas_decimales - horas) * 60
        minutos = int(round(minutos_dec))
        
        # Ajuste por si el redondeo nos da 60 minutos
        if minutos == 60:
            horas += 1
            minutos = 0
            
        return f"{horas:02d}:{minutos:02d}"
    except:
        return "00:00"
# -------------------------------------------

# --- WIDGET CALENDARIO ---
class CTkCalendar(ctk.CTkFrame):
    def __init__(self, master, start_date=None, command=None, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)
        self.command = command
        self.date = start_date if start_date else datetime.now()
        self.mes_actual = self.date.month
        self.anio_actual = self.date.year
        self.lista_meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
        self.anio_list = [str(y) for y in range(self.anio_actual - 5, self.anio_actual + 6)]
        
        self.h = ctk.CTkFrame(self, fg_color=COLOR_ACCENT, corner_radius=5, height=40); self.h.pack(fill="x", pady=(0,5))
        self.om = ctk.CTkOptionMenu(self.h, values=self.lista_meses, width=110, fg_color="#800000", button_color="#500000", command=self.upd); self.om.set(self.lista_meses[self.mes_actual-1]); self.om.pack(side="left", padx=5)
        self.oa = ctk.CTkOptionMenu(self.h, values=self.anio_list, width=80, fg_color="#800000", button_color="#500000", command=self.upd); self.oa.set(str(self.anio_actual)); self.oa.pack(side="right", padx=5)
        
        self.fd = ctk.CTkFrame(self, fg_color="transparent"); self.fd.pack(fill="x")
        for d in ["Lu","Ma","Mi","Ju","Vi","Sa","Do"]: ctk.CTkLabel(self.fd, text=d, width=42, font=("Arial",12,"bold"), text_color="gray").pack(side="left", padx=1)
        self.fg = ctk.CTkFrame(self, fg_color="transparent"); self.fg.pack(fill="both", expand=True, pady=5)
        self.render()

    def upd(self, _): 
        try: self.mes_actual=self.lista_meses.index(self.om.get())+1; self.anio_actual=int(self.oa.get()); self.render()
        except: pass
    
    def render(self):
        for w in self.fg.winfo_children(): w.destroy()
        cal = calendar.monthcalendar(self.anio_actual, self.mes_actual); hoy = datetime.now()
        for r, sem in enumerate(cal):
            for c, d in enumerate(sem):
                if d!=0:
                    col, txt = ("transparent", "white")
                    if d==hoy.day and self.mes_actual==hoy.month and self.anio_actual==hoy.year: col, txt = (COLOR_GOLD, "black")
                    ctk.CTkButton(self.fg, text=str(d), width=40, height=35, fg_color=col, text_color=txt, hover_color=COLOR_HOVER, command=lambda x=d: self.sel(x)).grid(row=r, column=c, padx=1, pady=1)
    
    def sel(self, d): 
        if self.command: self.command(f"{self.anio_actual}-{self.mes_actual:02d}-{d:02d}")

class PopupCalendario(ctk.CTkToplevel):
    def __init__(self, parent, callback):
        super().__init__(parent); self.callback = callback; self.title("Fecha"); self.geometry("320x350"); self.attributes("-topmost", True)
        try: self.geometry(f"+{parent.winfo_rootx()+50}+{parent.winfo_rooty()+50}")
        except: pass
        CTkCalendar(self, command=self.on_sel).pack(fill="both", expand=True, padx=10, pady=10)
    def on_sel(self, f): self.callback(f); self.destroy()

class PantallaCarga(ctk.CTkToplevel):
    def __init__(self, parent, on_finish):
        super().__init__(parent); self.on_finish = on_finish
        self.overrideredirect(True); self.configure(fg_color=COLOR_FONDO_SPLASH); self.attributes("-topmost", True)
        w, h = 500, 300; ws, hs = self.winfo_screenwidth(), self.winfo_screenheight(); self.geometry(f"{w}x{h}+{(ws-w)//2}+{(hs-h)//2}")
        frame = ctk.CTkFrame(self, fg_color=COLOR_FONDO_SPLASH); frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        if os.path.exists(LOGO_PATH):
            try:
                pil = Image.open(LOGO_PATH); r = pil.width/pil.height; w_img = int(120*r)
                tk_img = ctk.CTkImage(light_image=pil, dark_image=pil, size=(w_img, 120))
                ctk.CTkLabel(frame, image=tk_img, text="").pack(pady=(10,20))
            except: ctk.CTkLabel(frame, text="FRUT&EM", font=("Arial", 40, "bold"), text_color="white").pack(pady=20)
        else: ctk.CTkLabel(frame, text="FRUT&EM", font=("Arial", 40, "bold"), text_color="white").pack(pady=20)
        
        self.lbl = ctk.CTkLabel(frame, text="Iniciando...", text_color=COLOR_TEXTO); self.lbl.pack(pady=5)
        self.bar = ctk.CTkProgressBar(frame, width=400, height=15, progress_color=COLOR_BARRA, fg_color="#7f0000"); self.bar.set(0); self.bar.pack(pady=20)
        self.pasos = [(0.2,"Cargando DB..."),(0.5,"Verificando Drivers..."),(0.8,"Iniciando Interfaz..."),(1.0,"Listo!")]; self.i = 0
        self.after(500, self.animar)

    def animar(self):
        if self.i < len(self.pasos): v, t = self.pasos[self.i]; self.bar.set(v); self.lbl.configure(text=t); self.i += 1; self.after(400, self.animar)
        else: self.destroy(); self.on_finish()

class Login(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Login")
        
        # Centrar ventana
        ws, hs = self.winfo_screenwidth(), self.winfo_screenheight()
        self.geometry(f'400x450+{(ws-400)//2}+{(hs-450)//2}')
        self.attributes("-topmost", True)
        self.protocol("WM_DELETE_WINDOW", lambda: os._exit(0))
        
        # --- LOGO / CANDADO ---
        try:
            # Intentamos cargar candado.png
            if hasattr(parent, 'cargar_icono'):
                self.ico_lock = parent.cargar_icono("candado.png", size=(80,80))
            else:
                self.ico_lock = None

            if self.ico_lock:
                ctk.CTkLabel(self, text="", image=self.ico_lock).pack(pady=40)
            else:
                ctk.CTkLabel(self, text="LOGIN", font=("Arial", 30, "bold")).pack(pady=40)
        except:
            ctk.CTkLabel(self, text="LOGIN", font=("Arial", 30, "bold")).pack(pady=40)
        
        # Inputs
        self.u = ctk.CTkEntry(self, width=250, placeholder_text="Usuario")
        self.u.pack(pady=10)
        
        self.p = ctk.CTkEntry(self, width=250, placeholder_text="Contraseña", show="*")
        self.p.pack(pady=10)
        
        # Botón (Aquí estaba el error, llamaba a validar y no existía)
        ctk.CTkButton(self, text="INGRESAR", fg_color="#00C853", command=self.validar).pack(pady=30)
        
        self.msg = ctk.CTkLabel(self, text="", text_color="red")
        self.msg.pack()
        
        self.bind('<Return>', lambda e: self.validar())

    # --- ESTA ES LA FUNCIÓN QUE FALTABA ---
    def validar(self):
        user_real = config_data.get("app_user", "admin")
        pass_real = config_data.get("app_pass", "admin")
        
        if self.u.get() == user_real and self.p.get() == pass_real:
            self.destroy()          # 1. Cierra el Login
            self.parent.deiconify() # 2. Muestra el Sistema
            
            # Si es cajera, hacemos clic virtual en "LIQUIDACIÓN" para que no quede pantalla negra
            if user_real != "admin":
                self.parent.tabview.set("LIQUIDACIÓN")
            # ------------------------------------------------------------
            
            print("🔑 Login correcto. Iniciando conexión en segundo plano...")
            threading.Thread(target=self.parent.conectar, daemon=True).start()
            
        else:
            self.msg.configure(text="Contraseña Incorrecta")
            self.p.delete(0, 'end')

class VentanaConfig(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent); self.parent = parent; self.title("Config"); self.geometry("400x350"); self.attributes("-topmost", True)
        ctk.CTkLabel(self, text="Configuración", font=("Arial",18,"bold")).pack(pady=20)
        self.ip = ctk.CTkEntry(self, width=250); self.ip.pack(pady=5); self.ip.insert(0, config_data.get("ip_reloj", ""))
        ctk.CTkButton(self, text="Guardar", command=self.save).pack(pady=30)
    def save(self):
        d=config_data.copy(); d["ip_reloj"]=self.ip.get().strip()
        with open(CONFIG_FILE,'w') as f: json.dump(d,f,indent=4)
        messagebox.showinfo("OK","Reiniciando..."); self.parent.destroy(); os._exit(0)

class VentanaPerfil(ctk.CTkToplevel):
    def __init__(self, parent, id_reloj):
        super().__init__(parent)
        self.id_reloj = str(id_reloj)
        self.title(f"Perfil - {self.id_reloj}")
        self.geometry("600x650")
        self.attributes("-topmost", True)
        self.configure(fg_color=("gray92", "#1a1a1a"))
        
        # 1. PEDIMOS TODOS LOS DATOS AL MOTOR DE UNA VEZ
        datos = motor.obtener_datos_perfil(self.id_reloj)
        
        if not datos:
            messagebox.showerror("Error", "Empleado no encontrado o error en DB")
            self.destroy()
            return
            
        # Desempaquetamos los datos que nos dio el motor
        nom, val, fot, dinero_hoy, horas_hoy, dinero_mes, horas_mes = datos

        # --- INTERFAZ GRÁFICA (Igual que antes, solo pinta datos) ---
        f_header = ctk.CTkFrame(self, fg_color="transparent"); f_header.pack(pady=20)
        
        l_foto = ctk.CTkLabel(f_header, text=nom[:2], font=("Arial", 40), width=120, height=120, fg_color=("white", "#333"), corner_radius=60)
        l_foto.pack()
        
        if fot and os.path.exists(fot):
            try:
                im_pil = Image.open(fot)
                im = ctk.CTkImage(im_pil, size=(120, 120))
                l_foto.configure(image=im, text="")
            except: pass

        ctk.CTkLabel(self, text=nom, font=("Arial", 26, "bold")).pack(pady=(10, 0))
        ctk.CTkLabel(self, text=f"ID: {self.id_reloj} • Valor Hora: ${val:,.2f}", text_color="gray", font=("Arial", 14)).pack(pady=(0, 20))

        # Tarjetas de Estadísticas
        f_stats = ctk.CTkFrame(self, fg_color="transparent"); f_stats.pack(fill="x", padx=20)
        f_stats.grid_columnconfigure(0, weight=1); f_stats.grid_columnconfigure(1, weight=1)

        c1 = ctk.CTkFrame(f_stats, fg_color="#004D40", corner_radius=15, border_width=2, border_color="#69F0AE")
        c1.grid(row=0, column=0, padx=10, sticky="ew")
        ctk.CTkLabel(c1, text="HOY", text_color="#69F0AE", font=("Arial", 12, "bold")).pack(pady=(15,0))
        ctk.CTkLabel(c1, text=f"${dinero_hoy:,.0f}", text_color="white", font=("Arial", 32, "bold")).pack(pady=5)
        ctk.CTkLabel(c1, text=f"{horas_hoy:.2f} hs", text_color="white", font=("Arial", 14)).pack(pady=(0,15))

        c2 = ctk.CTkFrame(f_stats, fg_color="#1A237E", corner_radius=15, border_width=2, border_color="#448AFF")
        c2.grid(row=0, column=1, padx=10, sticky="ew")
        ctk.CTkLabel(c2, text="ESTE MES", text_color="#448AFF", font=("Arial", 12, "bold")).pack(pady=(15,0))
        ctk.CTkLabel(c2, text=f"${dinero_mes:,.0f}", text_color="white", font=("Arial", 32, "bold")).pack(pady=5)
        ctk.CTkLabel(c2, text=f"{horas_mes:.2f} hs", text_color="white", font=("Arial", 14)).pack(pady=(0,15))

        # Historial Reciente
        ctk.CTkLabel(self, text="Últimos Fichajes:", font=("Arial", 14, "bold"), anchor="w").pack(fill="x", padx=30, pady=(30, 5))
        f_hist = ctk.CTkScrollableFrame(self, height=150, fg_color=("white", "#2b2b2b")); f_hist.pack(fill="x", padx=20, pady=(0, 20))
        
        # Pedimos el historial al motor
        raw_hist = motor.obtener_historial_reciente(self.id_reloj)
        
        if not raw_hist:
            ctk.CTkLabel(f_hist, text="Sin registros recientes").pack()
        else:
            for r in raw_hist:
                dt = datetime.strptime(r[0], "%Y-%m-%d %H:%M:%S")
                row_f = ctk.CTkFrame(f_hist, fg_color="transparent"); row_f.pack(fill="x", pady=2)
                ctk.CTkLabel(row_f, text="🕒 Fichada:", font=("Arial", 12, "bold"), text_color="gray").pack(side="left", padx=10)
                ctk.CTkLabel(row_f, text=dt.strftime("%d/%m %H:%M"), font=("Arial", 12)).pack(side="left")

# --- SISTEMA PRINCIPAL ---
class SistemaV79(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        

        self.en_ejecucion = True

        self.ultima_fichada_compleja = datetime.min

        self.protocol("WM_DELETE_WINDOW", self.cerrar_programa)

        # 1. Mantenemos la ventana oculta al principio
        self.withdraw() 
        
        self.title("SISTEMA FRUT&EM"); self.geometry("1280x900")
        try: 
            if os.path.exists(LOGO_PATH): self.wm_iconphoto(False, ImageTk.PhotoImage(file=LOGO_PATH))
        except: pass
        
        archivos_necesarios = ["HCNetSDK.dll", "config.json"]
        faltantes = [f for f in archivos_necesarios if not os.path.exists(f)]
        if faltantes: messagebox.showwarning("Faltan Archivos", f"Faltan:\n{', '.join(faltantes)}")

        # --- AQUÍ ESTÁ EL CAMBIO ---
        # 2. Activamos la Pantalla de Carga (Splash)
        # Ella se encargará de llamar a 'self.mostrar_login' cuando termine de cargar
        self.after(100, lambda: PantallaCarga(self, self.mostrar_login))
        
        # BORRA o COMENTA la línea vieja que decía: self.after(100, self.mostrar_login)
        # ---------------------------

        self.tabview = ctk.CTkTabview(self); self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        claves = ["mon", "per", "liq", "hist", "stock", "pos"]
        nombres = ["MONITOR", "PERSONAL", "LIQUIDACIÓN", "HISTORIAL", "👟 STOCK", "🥐 CAJA / VENTAS"]
        self.tabs = {n: self.tabview.add(t) for n,t in zip(claves, nombres)}
        
        self.scroll_frame = None
        self.cards_cache = {}
        
        self.setup_ui()
    # En main.py, busca la función cerrar_programa:

    def cerrar_programa(self):
        try:
            print("Apagando sistema...")
            self.en_ejecucion = False 
            if motor:
                # AHORA USAMOS ESTO:
                motor.liberar_recursos() 
        except: pass
        try: self.destroy()
        except: pass
        os._exit(0)

    def mostrar_login(self): self.ventana_login = Login(self)
    
    def realizar_backup(self):
        try:
            if not os.path.exists("backups"): os.makedirs("backups")
            db_original = DB_NAME
            nombre_backup = f"backups/backup_{datetime.now().strftime('%Y-%m-%d')}_{db_original}"
            if not os.path.exists(nombre_backup) and os.path.exists(db_original):
                shutil.copy2(db_original, nombre_backup)
        except: pass

    def conectar(self):
    # ... (lógica previa de obtención de IPs y login) ...
        print("🏁 Iniciando conexión...")
        
        # --- DEFINICIÓN DE VARIABLES FALTANTES ---
        ip = config_data.get("ip_reloj")
        u = config_data.get("usuario_reloj")
        p = config_data.get("clave_reloj")
        # -------------------------------------------
        
        try:
            # Llamada al motor
            conectado = motor.conectar_sdk(ip, u, p, lambda pInfo: self.procesar(pInfo))

            if conectado:
                # 1. Actualizar texto de Monitor (Admin)
                self.lbl_status.configure(text="🟢 EN LÍNEA", text_color="#00E676")
                
                # 2. ACTUALIZAR LIQUIDACIÓN (Lo que ves en tu captura)
                # Como ya definiste self.img_on y self.lbl_estado_liq en setup_liq:
                if hasattr(self, 'lbl_estado_liq') and self.img_on:
                    self.lbl_estado_liq.configure(
                        image=self.img_on,      # Cambia a la bolita verde
                        text=" ONLINE",         # Cambia el texto
                        text_color="#00E676"    # Verde neón para visibilidad
                    )
                
                # 3. Lanzar procesos secundarios
                self.check_updates()
                threading.Thread(target=self.sync, args=(True,), daemon=True).start()

            else: 
                # Si la conexión falla
                self.lbl_status.configure(text="DESCONECTADO", text_color="red")
                
                if hasattr(self, 'lbl_estado_liq') and self.img_off:
                    self.lbl_estado_liq.configure(
                        image=self.img_off,     # Bolita roja
                        text=" OFFLINE",
                        text_color="red"
                    )
        except Exception as e:
            # Aquí actuará tu nuevo Log de Errores que configuramos
            print(f"Error en hilo de conexión: {e}")

    def check_updates(self):
        if not self.en_ejecucion: return 
        if hasattr(self, "flag_actualizar") and self.flag_actualizar:
            try: self.actualizar_tablero()
            except: pass
            self.flag_actualizar = False
        if self.en_ejecucion: self.after(1000, self.check_updates)

    

    def procesar(self, pInfo):
        """
        V52 LIVE (ANTI-FANTASMA):
        1. Elimina Fechas y Horas del texto ANTES de buscar IDs.
           (Evita que las 14:58 se lea como ID 2, o 15:04 como ID 4).
        2. Verifica que el nombre del empleado también aparezca en el mensaje (Doble Check).
        3. Mantiene el filtro de IP para evitar basura del sistema.
        """
        if not pInfo: return

        try:
            import ctypes, re, struct, gc
            # Importamos datetime aquí por seguridad
            from datetime import datetime 
            
            # 1. OBTENER TEXTO CRUDO
            raw_bytes = ctypes.string_at(pInfo, 1024)
            try: txt = raw_bytes.decode('utf-8', errors='ignore')
            except: txt = raw_bytes.decode('latin-1', errors='ignore')
            
            txt_lower = txt.lower()

            # 2. FILTROS DE BASURA (IPs y Alarmas)
            if "192.168" in txt or "remote" in txt_lower or "alarm" in txt_lower:
                return 
            
            # Si no dice "Face", "Card", "Verif" o "Authentic", es ruido.
            if not any(x in txt_lower for x in ["face", "card", "verif", "authentic"]):
                return

            # 3. LEER FECHA (Offset 12)
            cabecera_rapida = ctypes.string_at(pInfo, 64)
            fecha_str = ""; fecha_detectada = None
            try:
                y, m, d, h, min_, sec = struct.unpack('<IIIIII', cabecera_rapida[12:36])
                if 2020 <= y <= 2030:
                    fecha_detectada = datetime(y, m, d, h, min_, sec)
            except: pass
            
            if not fecha_detectada: return 
            fecha_str = fecha_detectada.strftime("%Y-%m-%d %H:%M:%S")

            # --- LA MAGIA V52: LIMPIEZA DE HORA ---
            # Borramos patrones de fecha (2026-01-24) y hora (14:58:00) del texto
            # para que el sistema NO lea esos números como IDs de empleados.
            txt_limpio = re.sub(r'\d{4}-\d{2}-\d{2}', '', txt) # Borra año-mes-día
            txt_limpio = re.sub(r'\d{2}:\d{2}:\d{2}', '', txt_limpio) # Borra hora:min:seg
            
            # Ahora buscamos IDs solo en el texto limpio
            posibles_ids = re.findall(r'\d+', txt_limpio)
            
            if not motor.known_ids: motor.actualizar_lista_blanca()
            
            for num in posibles_ids:
                # 4. DOBLE VERIFICACIÓN (NOMBRE)
                # Si el ID es de un dígito (ej: 2, 6, 8), es muy fácil que sea un error.
                # Obligamos a que el NOMBRE del empleado también esté en el texto del reloj.
                if num in motor.known_ids and num != '0':
                    
                    es_valido = True
                    # Si es ID corto (1 o 2 cifras), verificamos nombre para evitar fantasmas
                    if len(num) < 3:
                        data_emp = motor.known_ids[num]
                        nombre_real = data_emp['nombre'].lower().split()[0] # Primer nombre
                        # Si el nombre NO está en el texto, asumimos que es un número fantasma
                        if nombre_real not in txt_lower:
                            es_valido = False
                    
                    if es_valido:
                        print(f"⚡ V52 DETECTADO: {motor.known_ids[num]['nombre']} (ID {num})")
                        self.guardar_si_corresponde(num, fecha_str, "V52_LIVE")
            
            gc.collect()

        except Exception as e: print(f"Error V52: {e}")

    def guardar_si_corresponde(self, id_reloj, fecha_sql, origen):
        """
        Versión con FILTRO ANTI-REBOTE.
        Si la persona fichó hace menos de 60 segundos, se ignora la segunda marca
        para evitar entradas y salidas falsas instantáneas.
        """
        try:
            with motor.get_connection() as conn:
                cursor = conn.cursor()
                
                # 1. VERIFICAR DUPLICADO EXACTO (Misma hora exacta)
                cursor.execute("SELECT COUNT(*) FROM fichadas WHERE id_reloj = %s AND fecha_hora = %s", (id_reloj, fecha_sql))
                if cursor.fetchone()[0] > 0:
                    return # Ya existe, no hacemos nada.

                # 2. FILTRO ANTI-REBOTE (La Magia) 🛡️
                # Buscamos la última fichada registrada de este empleado
                cursor.execute("SELECT MAX(fecha_hora) FROM fichadas WHERE id_reloj = %s", (id_reloj,))
                resultado = cursor.fetchone()
                
                if resultado and resultado[0]:
                    ultima_fichada_str = str(resultado[0])
                    
                    # Convertimos los textos a objetos de fecha para poder restar
                    # El formato en base de datos suele ser YYYY-MM-DD HH:MM:SS
                    fmt = "%Y-%m-%d %H:%M:%S"
                    try:
                        dt_nueva = datetime.strptime(fecha_sql, fmt)
                        
                        # A veces la base de datos devuelve datetime, a veces string. Aseguramos:
                        if isinstance(resultado[0], datetime):
                            dt_ultima = resultado[0]
                        else:
                            dt_ultima = datetime.strptime(ultima_fichada_str, fmt)
                        
                        # Calculamos la diferencia en segundos
                        diferencia = (dt_nueva - dt_ultima).total_seconds()
                        
                        # SI LA DIFERENCIA ES MENOR A 60 SEGUNDOS -> ES UN REBOTE
                        # (Puedes cambiar 60 por 120 si quieres 2 minutos de filtro)
                        if 0 <= diferencia < 60:
                            print(f"   🚫 REBOTE IGNORADO: ID {id_reloj} (Solo pasaron {int(diferencia)}s)")
                            return 
                            
                    except Exception as e:
                        # Si falla la conversión de fecha, guardamos por si acaso para no perder datos
                        print(f"Warning fecha: {e}")

                # 3. INSERTAR (Si pasó los filtros)
                print(f"   ✅ ¡FICHADA GUARDADA: ID {id_reloj} | Hora: {fecha_sql}")
                cursor.execute("INSERT INTO fichadas (fecha_hora, id_reloj, raw_data) VALUES (%s, %s, %s)", (fecha_sql, id_reloj, origen))
                conn.commit()
                self.flag_actualizar = True
                
        except Exception as e:
            print(f"❌ Error DB: {e}")

    
    
    # Modificamos la definición para aceptar el modo silencioso
    def sync(self, silencioso=False):
        """
        V53 SYNC (AUTOMÁTICA + 7 DÍAS ATRÁS):
        - Busca datos de la última semana para recuperar lo que no bajaste ayer.
        - Modo silencioso para ejecutarse al inicio sin molestar.
        """
        if not silencioso:
            print("\n--- INICIANDO SYNC MANUAL ---")
        else:
            print("\n--- INICIANDO SYNC AUTOMÁTICO (BACKGROUND) ---")
        
        # CREDENCIALES
        if hasattr(motor, 'ip') and motor.ip:
            ip, user, password = motor.ip, motor.user, motor.password
        else:
            # Usamos los de config o default
            ip = config_data.get("ip_reloj", "192.168.1.19")
            user = config_data.get("usuario_reloj", "admin")
            password = config_data.get("clave_reloj", "CAMBIAR_CLAVE_DEL_RELOJ")

        if not silencioso: print(f"🌍 Conectando a {ip}...")

        try:
            import subprocess
            import json
            import time
            from datetime import datetime, timedelta # IMPORTANTE: timedelta
            
            motor.actualizar_lista_blanca() 
            
            now = datetime.now()
            
            # --- EL CAMBIO CLAVE: BUSCAR 7 DÍAS ATRÁS ---
            # Así, si no abriste el programa ayer, hoy lo recupera igual.
            fecha_inicio = now - timedelta(days=7)
            
            start_iso = fecha_inicio.strftime("%Y-%m-%dT00:00:00")
            end_iso   = now.strftime("%Y-%m-%dT23:59:59")
            # --------------------------------------------
            
            posicion_actual = 0
            total_recuperados = 0
            total_en_reloj = 0
            pagina = 1
            seguir_leyendo = True

            # Ventanita de progreso (SOLO SI NO ES SILENCIOSO)
            top = None
            lbl_progreso = None
            if not silencioso:
                top = ctk.CTkToplevel(self); top.geometry("300x120"); top.title("Recuperando...")
                top.attributes("-topmost", True)
                lbl_progreso = ctk.CTkLabel(top, text="Buscando datos pendientes...", font=("Arial", 14))
                lbl_progreso.pack(expand=True)
                top.update()

            while seguir_leyendo:
                if not silencioso:
                    print(f"📄 Leyendo Página {pagina}...")
                    if lbl_progreso: lbl_progreso.configure(text=f"Leyendo Página {pagina}...")
                    if top: top.update()

                payload = {
                    "AcsEventCond": {
                        "searchID": "1", 
                        "startTime": start_iso,
                        "endTime": end_iso,
                        "major": 0,
                        "minor": 0,
                        "maxResults": 30,
                        "searchResultPosition": posicion_actual
                    }
                }
                json_payload = json.dumps(payload)

                cmd = [
                    "curl", "--digest", "-u", f"{user}:{password}",
                    "-X", "POST", "-H", "Content-Type: application/json",
                    "-d", json_payload, "-k",
                    f"http://{ip}/ISAPI/AccessControl/AcsEvent?format=json"
                ]
                
                # Timeout para que no se cuelgue si el reloj no responde rápido
                # Añadimos creationflags para que no abra ventana negra de consola
                result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', 
                        creationflags=0x08000000) # <--- ESTO OCULTA EL CMD
                
                if "Unauthorized" in result.stdout:
                    if not silencioso: messagebox.showerror("Error", "Contraseña incorrecta.")
                    if top: top.destroy()
                    return

                try:
                    data = json.loads(result.stdout)
                    lista_eventos = []
                    
                    if "AcsEvent" in data and "InfoList" in data["AcsEvent"]:
                        lista_eventos = data["AcsEvent"]["InfoList"]
                        total_en_reloj = data["AcsEvent"].get("totalMatches", 0)
                    elif "AcsEventSearch" in data:
                        lista_eventos = data["AcsEventSearch"].get("AcsEvent", [])
                        total_en_reloj = data["AcsEventSearch"].get("totalMatches", 0)
                    
                    num_recibidos = len(lista_eventos)

                    for evento in lista_eventos:
                        emp_id = str(evento.get("employeeNoString", ""))
                        fecha_raw = evento.get("time", "")
                        remote_ip = evento.get("remoteHostAddr", "")
                        
                        if "192.168" in remote_ip: continue 
                        
                        if len(fecha_raw) >= 19:
                            fecha_sql = fecha_raw[:19].replace("T", " ")
                            if emp_id and emp_id.isdigit() and emp_id in motor.known_ids and emp_id != '0':
                                # La función guardar ya verifica si existe, así que no hay problema con repetidos
                                self.guardar_si_corresponde(emp_id, fecha_sql, "V53_AUTO")
                                total_recuperados += 1

                    posicion_actual += num_recibidos
                    pagina += 1
                    
                    if num_recibidos == 0 or posicion_actual >= total_en_reloj:
                        seguir_leyendo = False
                    
                except json.JSONDecodeError:
                    seguir_leyendo = False
            
            if top: top.destroy()
            
            print(f"✅ Sync Finalizado. Nuevos recuperados: {total_recuperados}")
            
            # Solo mostramos alertas si fue manual (no silencioso)
            if not silencioso:
                if total_recuperados > 0:
                    messagebox.showinfo("Éxito", f"Se recuperaron {total_recuperados} fichadas nuevas.")
                else:
                    messagebox.showinfo("Al día", "No había datos nuevos en el reloj.")

            self.after(0, self.actualizar_tablero)
        except Exception as e: 
            print(f"❌ Error Sync: {e}")
            if not silencioso: messagebox.showerror("Error", str(e))

            
    def cargar_icono(self, nombre_archivo, size=(20, 20)):
        """Versión PRO: Busca iconos AL LADO del ejecutable"""
        try:
            # 1. Detectar ruta BASE (Donde está el .exe o el .py)
            if getattr(sys, 'frozen', False):
                # Si es EXE, busca donde está instalado el archivo .exe
                ruta_base = os.path.dirname(sys.executable)
            else:
                # Si es código fuente, busca donde está este archivo .py
                ruta_base = os.path.dirname(os.path.abspath(__file__))
            
            # 2. Armar la ruta completa
            ruta_completa = os.path.join(ruta_base, "iconos", nombre_archivo)
            
            # 3. Cargar si existe
            if os.path.exists(ruta_completa):
                pil_img = Image.open(ruta_completa)
                return ctk.CTkImage(light_image=pil_img, 
                                  dark_image=pil_img, 
                                  size=size)
            else:
                print(f"⚠️ Icono no encontrado: {ruta_completa}")
                return None
        except Exception as e: 
            print(f"Error cargando icono {nombre_archivo}: {e}")
            return None

    # --- UI SETUP ---
    def setup_ui(self):
        self.setup_top_bar();
        self.setup_monitor();
        self.setup_personal();
        self.setup_liq();
        self.setup_hist();
        self.setup_stock_calzado() # Dibuja la carga de zapatos
        self.setup_pos()           # Dibuja la caja de ventas
        self.aplicar_permisos();

    

    def aplicar_permisos(self):
        """
        Si el usuario NO es 'admin', elimina las pestañas críticas
        y fuerza la vista en Liquidación.
        """
        usuario_actual = config_data.get("app_user", "admin").strip().lower()
        
        if usuario_actual != "admin":
            print(f"🔒 MODO RESTRINGIDO ACTIVADO PARA: {usuario_actual}")
            try:
                # 1. Borramos lo que no debe ver
                self.tabview.delete("MONITOR")
                self.tabview.delete("PERSONAL")
                self.tabview.delete("HISTORIAL")
                
                # 2. [SOLUCIÓN] FORZAMOS QUE SE MUESTRE LA PESTAÑA QUE QUEDA
                self.tabview.set("LIQUIDACIÓN") 
                
            except Exception as e:
                print(f"Error aplicando permisos: {e}")


    def setup_stock_calzado(self):
        f = self.tabs["stock"] # Previamente agregada en self.tabs
        
        # Panel de Carga (Izquierda - Estilo Personal)
        f1 = ctk.CTkFrame(f, width=300)
        f1.pack(side="left", fill="y", padx=10, pady=10)
        
        ctk.CTkLabel(f1, text="NUEVO INGRESO", font=("Arial", 16, "bold"), text_color=COLOR_GOLD).pack(pady=10)
        
        self.st_barras = ctk.CTkEntry(f1, placeholder_text="Código de Barras")
        self.st_barras.pack(pady=5, padx=10, fill="x")
        
        self.st_modelo = ctk.CTkEntry(f1, placeholder_text="Modelo / Nombre")
        self.st_modelo.pack(pady=5, padx=10, fill="x")

        ctk.CTkButton(f1, text="⚡ CARGA DEMO", fg_color="#455A64", 
        command=self.insertar_demo_calzados).pack(pady=10, padx=10, fill="x")
        
        # Fila para Color y Talle
        f_extra = ctk.CTkFrame(f1, fg_color="transparent")
        f_extra.pack(fill="x")
        self.st_color = ctk.CTkEntry(f_extra, placeholder_text="Color", width=130); self.st_color.pack(side="left", padx=10, pady=5)
        self.st_talle = ctk.CTkEntry(f_extra, placeholder_text="Talle", width=130); self.st_talle.pack(side="right", padx=10, pady=5)
        
        self.st_precio = ctk.CTkEntry(f1, placeholder_text="Precio $"); self.st_precio.pack(pady=5, padx=10, fill="x")
        self.st_cant = ctk.CTkEntry(f1, placeholder_text="Cantidad"); self.st_cant.pack(pady=5, padx=10, fill="x")
        
        # Botón de Guardado con tu icono de guardar
        ico_save = self.cargar_icono("guardar.png")
        ctk.CTkButton(f1, text="GUARDAR", image=ico_save, compound="left", 
                    fg_color="#1B5E20", command=self.save_stock).pack(pady=20, padx=10, fill="x")

        # Tabla de Inventario (Derecha - Estilo Historial)
        cols = ("ID", "MOD", "COL", "T", "STK", "PRE")
        self.tr_stk = ttk.Treeview(f, columns=cols, show="headings")
        self.tr_stk.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        
        headers = [("ID", 50), ("MOD", 200), ("COL", 100), ("T", 50), ("STK", 70), ("PRE", 100)]
        for cid, width in headers:
            self.tr_stk.heading(cid, text=cid)
            self.tr_stk.column(cid, width=width, anchor="center")
            # Botón de Venta (Color Azul para destacar)
            ctk.CTkButton(f1, text="🛒 VENDER SELECCIONADO", fg_color="#0D47A1", 
            command=self.ejecutar_venta_stock).pack(pady=5, padx=10, fill="x")

    def ejecutar_venta_stock(self):
        """Lógica para vender el zapato seleccionado en la tabla."""
        seleccion = self.tr_stk.selection()
        if not seleccion:
            messagebox.showwarning("Atención", "Por favor, selecciona un producto de la tabla.")
            return
        
        # Obtenemos el ID de la primera columna (índice 0)
        item = self.tr_stk.item(seleccion[0])
        id_db = item['values'][0]
        nombre_prod = item['values'][1]
        
        if messagebox.askyesno("Confirmar Venta", f"¿Registrar venta de: {nombre_prod}?"):
            exito, msg = motor.registrar_venta_rapida(id_db)
            if exito:
                messagebox.showinfo("Vendido", msg)
                self.load_stock() # Refrescamos para ver el nuevo stock (y si cambia a rojo)
            else:
                messagebox.showerror("Error", msg)

    def setup_top_bar(self):
        # 1. Creamos el marco "top" (ESTA LÍNEA FALTABA)
        top = ctk.CTkFrame(self, height=50, fg_color="transparent")
        top.pack(side="top", fill="x", padx=20, pady=(10,0), before=self.tabview)
        
        # 2. Título
        ctk.CTkLabel(top, text="SISTEMA DE CONTROL", font=("Arial", 20, "bold"), text_color=("gray30", "gray")).pack(side="left")
        
        # 3. Botón TEMA con Icono
        self.ico_tema = self.cargar_icono("luna.png", size=(20,20))
        txt_tema = "" if self.ico_tema else "TEMA"
        
        ctk.CTkButton(top, text=txt_tema, image=self.ico_tema, width=40, 
                     command=lambda: ctk.set_appearance_mode("Light" if ctk.get_appearance_mode()=="Dark" else "Dark")).pack(side="right", padx=5)

        # 4. Botón CONFIG con Icono
        self.ico_conf = self.cargar_icono("config.png", size=(20,20))
        txt_conf = "" if self.ico_conf else "CONF"
        
        ctk.CTkButton(top, text=txt_conf, image=self.ico_conf, width=40, fg_color="#333", 
                     command=lambda: VentanaConfig(self)).pack(side="right")

    def setup_monitor(self):
        f = self.tabs["mon"]
        
        # 1. Cabecera (Header)
        h = ctk.CTkFrame(f, height=80, fg_color="transparent")
        h.pack(fill="x", padx=10, pady=5)
        
        # 2. Logo (Izquierda)
        lf = ctk.CTkFrame(h, fg_color="transparent")
        lf.pack(side="left")
        
        self.logo_ui = self.cargar_icono("logo.png", size=(80, 120))
        if self.logo_ui: 
            ctk.CTkLabel(lf, image=self.logo_ui, text="").pack(side="left", padx=(0, 15))
        else: 
            ctk.CTkLabel(lf, text="FRUT&EM", font=("Arial", 20, "bold")).pack(side="left", padx=(0, 15))
        
        # 3. Estado (Izquierda)
        self.lbl_status = ctk.CTkLabel(h, text="CONECTANDO...", font=("Arial", 22, "bold"), text_color="orange")
        self.lbl_status.pack(side="left")
        
        # 4. BOTONES (Derecha) - AQUÍ AGREGAMOS EL BOTÓN QUE FALTA
        fr_btn = ctk.CTkFrame(h, fg_color="transparent")
        fr_btn.pack(side="right")
        
        # Botón REFRESCAR (Gris/Azul) - Solo lee la base de datos
        self.ico_mon = self.cargar_icono("monitor.png", size=(20,20))
        ctk.CTkButton(fr_btn, text="REFRESCAR", image=self.ico_mon, compound="left", 
                     command=self.actualizar_tablero).pack(side="left", padx=5)

        # 🔥 BOTÓN RECUPERAR (Verde Oscuro) - Lee la memoria del reloj 🔥
        self.ico_sync = self.cargar_icono("nube.png", size=(20,20)) 
        ctk.CTkButton(fr_btn, text="RECUPERAR", image=self.ico_sync, compound="left", fg_color="#00690E", width=120,
                     command=self.sync).pack(side="left", padx=5)

        # 5. Área de Tarjetas (Scroll)
        self.scroll_frame = ctk.CTkScrollableFrame(f, fg_color=("gray95", "#1a1a1a"))
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)

    def actualizar_tablero(self):
        """
        MONITOR MYSQL V25 (CONECTADO AL MOTOR):
        1. Se conecta a la BASE DE DATOS REAL (MySQL) a través del motor.
        2. Usa la sintaxis correcta (%s) para que no de errores.
        3. Busca la fecha activa automáticamente (2026, 2025, etc).
        """
        # 1. Limpiar pantalla
        for w in self.scroll_frame.winfo_children(): 
            try:
                w.destroy()
            except:
                pass # Si ya murió, lo ignoramos
        self.cards_cache = {}
        
        lista_tarjetas = []
        
        try:
            # ¡CORRECCIÓN CLAVE! Usamos 'motor.get_connection()' en vez de 'sqlite3'
                conn = motor.get_connection()
                cursor = conn.cursor()
                
                # A. BUSCAR LA FECHA ACTIVA (La última registrada en el sistema)
                cursor.execute("SELECT MAX(fecha_hora) FROM fichadas")
                res = cursor.fetchone()
                
                if res and res[0]:
                    # Convertimos a string y tomamos los primeros 10 caracteres (YYYY-MM-DD)
                    fecha_activa = str(res[0])[:10] 
                else:
                    fecha_activa = datetime.now().strftime("%Y-%m-%d")

                # B. TRAER EMPLEADOS (Desde MySQL)
                # Ojo: En MySQL fetchall devuelve tuplas (0=id, 1=nombre, 2=foto)
                cursor.execute("SELECT id_reloj, nombre, foto_path FROM empleados")
                empleados = cursor.fetchall()
                
                for emp in empleados:
                    eid = str(emp[0])   # ID
                    nombre = emp[1]     # Nombre
                    foto = emp[2]       # Foto
                    
                    # C. TRAER FICHADAS DE ESTE EMPLEADO EN LA FECHA ACTIVA
                    # Usamos %s para MySQL
                    query = "SELECT fecha_hora FROM fichadas WHERE id_reloj = %s AND fecha_hora LIKE %s ORDER BY fecha_hora ASC"
                    # El % después de la fecha es para el LIKE (ej: '2026-01-23%')
                    cursor.execute(query, (eid, f"{fecha_activa}%"))
                    fichadas = cursor.fetchall()
                    
                    if not fichadas: continue 

                    # D. LÓGICA DE TURNO (Par = Salió, Impar = Adentro)
                    cant = len(fichadas)
                    es_par = (cant % 2 == 0)
                    
                    # Extraemos la hora (HH:MM) de la tupla. La fecha está en la posición 0.
                    # fichadas[-1][0] es "2026-01-23 19:15:59", hacemos split para sacar "19:15"
                    ultima_hora = str(fichadas[-1][0]).split(" ")[1][:5]
                    primera_hora = str(fichadas[0][0]).split(" ")[1][:5]

                    datos_card = {
                        "id": eid,
                        "nombre": nombre,
                        "foto": foto,
                        "activo": not es_par,
                        "h_entrada": ultima_hora if not es_par else primera_hora,
                        "h_salida": ultima_hora if es_par else ""
                    }
                    lista_tarjetas.append(datos_card)

        except Exception as e:
            print(f"❌ Error al actualizar tablero: {e}")

        # Si no hay datos, mostramos mensaje
        if not lista_tarjetas:
            ctk.CTkLabel(self.scroll_frame, text="SIN MOVIMIENTOS HOY", font=("Arial", 20), text_color="gray").pack(pady=50)
            return

        # Dibujar tarjetas
        r, c = 0, 0
        for datos in lista_tarjetas:
            self.mk_card(datos, r, c)
            c += 1
            if c >= 4:
                c = 0; r += 1
                

    def mk_card(self, t, r, c):
        # t es el diccionario que viene del motor
        col = "#00C853" if t["activo"] else "#D32F2F"
        st = "🟢 TRABAJANDO" if t["activo"] else "🔴 JORNADA FIN"
        
        if t["activo"]:
            inf = f"Entrada: {t['h_entrada']}"
        else:
            inf = f"Ent: {t['h_entrada']} | Sal: {t['h_salida']}"

        card = ctk.CTkFrame(self.scroll_frame, width=250, height=370, fg_color=("white","#2b2b2b"), corner_radius=15, border_width=2, border_color=col)
        card.grid(row=r, column=c, padx=15, pady=15)
        card.grid_propagate(False)

        # Foto
        l = ctk.CTkLabel(card, text="[SIN FOTO]", width=180, height=180, fg_color=("gray90","#444"), corner_radius=10)
        l.pack(pady=(15, 10))
        
        if t["foto"] and os.path.exists(t["foto"]):
            try:
                im = ctk.CTkImage(Image.open(t["foto"]), size=(180,180))
                l.configure(image=im, text="")
                self.cards_cache[t["id"]] = im 
            except: pass
            
        ctk.CTkLabel(card, text=t["nombre"], font=("Arial",16,"bold"), wraplength=230).pack()
        ctk.CTkLabel(card, text=st, text_color=col, font=("Arial",12,"bold")).pack(pady=(2,0))
        ctk.CTkLabel(card, text=inf, text_color="gray", font=("Arial",12)).pack(pady=(0,5))
        
        # Botón Estadísticas
        ctk.CTkButton(card, text="👤 VER ESTADÍSTICAS", width=200, height=30, fg_color="#0D47A1", 
                     command=lambda: VentanaPerfil(self, t["id"])).pack(side="bottom", pady=15)

    def setup_personal(self):
        f = self.tabs["per"]; self.id_original = None
        f1 = ctk.CTkFrame(f, width=300); f1.pack(side="left", fill="y", padx=10, pady=10)
        
        # Entradas
        self.e_id = ctk.CTkEntry(f1, placeholder_text="ID"); self.e_id.pack(pady=5)
        self.e_nom = ctk.CTkEntry(f1, placeholder_text="Nombre"); self.e_nom.pack(pady=5)
        self.e_val = ctk.CTkEntry(f1, placeholder_text="$/Hora"); self.e_val.pack(pady=5)
        self.l_ph = ctk.CTkLabel(f1, text="[FOTO]", width=120, height=120, fg_color="#333"); self.l_ph.pack(pady=10)
        self.path_tmp = None
        
        # --- BOTONES CON ICONOS ---
        
        # 1. Foto
        self.ico_cam = self.cargar_icono("camara.png", size=(20,20))
        ctk.CTkButton(f1, text="Foto", image=self.ico_cam, compound="left", command=self.bf).pack(pady=5)
        
        # 2. Guardar (Ya lo tenías, lo mantenemos)
        self.ico_guardar = self.cargar_icono("guardar.png", size=(20,20))
        ctk.CTkButton(f1, text="Guardar", image=self.ico_guardar, compound="left", command=self.save_e).pack(pady=5)

        # 3. Borrar
        self.ico_borrar = self.cargar_icono("borrar.png", size=(20,20))
        ctk.CTkButton(f1, text="Borrar", image=self.ico_borrar, compound="left", fg_color="red", command=self.del_e).pack(pady=5)
        
        # 4. Limpiar
        self.ico_limp = self.cargar_icono("limpiar.png", size=(20,20))
        ctk.CTkButton(f1, text="Limpiar", image=self.ico_limp, compound="left", fg_color="gray", command=self.clr_e).pack(pady=5)
        
        # --------------------------
        
        # Tabla
        self.tr = ttk.Treeview(f, columns=("ID","Nom","Val"), show="headings"); self.tr.pack(side="right", fill="both", expand=True, padx=10, pady=10)
        self.tr.heading("ID", text="ID"); self.tr.heading("Nom", text="Nombre"); self.tr.heading("Val", text="$/H")
        self.tr.bind("<<TreeviewSelect>>", self.on_sel); self.load_e()
    
    def bf(self):
        p = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.png *.jpeg"), ("Todos", "*.*")])
        if p: self.path_tmp = p; self.upd_img_lbl(p)
    def upd_img_lbl(self, p): 
        if p and os.path.exists(p): 
            try:
                im = Image.open(p); tk = ctk.CTkImage(light_image=im, dark_image=im, size=(120, 120))
                self.l_ph.configure(image=tk, text=""); self.l_ph.image = tk
            except: self.l_ph.configure(image=None, text="[ERROR]")
        else: self.l_ph.configure(image=None, text="[SIN FOTO]")
    
    def save_e(self):
        # 1. Recoger datos de la interfaz
        eid = self.e_id.get().strip()
        nom = self.e_nom.get().strip()
        val_txt = self.e_val.get().strip()
        
        if not eid:
            messagebox.showwarning("Faltan Datos", "El ID es obligatorio")
            return

        try:
            val = float(val_txt) if val_txt else 0.0
        except:
            val = 0.0

        # Determinamos la foto (Lógica de interfaz)
        path_final = "SIN_FOTO"
        
        # Si eligió una foto nueva temporal
        if self.path_tmp:
            import shutil
            destino = f"{DIR_FOTOS}/f_{eid}.jpg"
            try:
                shutil.copy(self.path_tmp, destino)
                path_final = destino
            except: pass
        # Si no eligió nueva, mantenemos la anterior (si estamos editando)
        elif self.id_original:
            # Truco: le pedimos al motor que nos diga la foto actual si existe
            # (Por ahora usaremos una lógica simple para no complicar)
            path_final = self.chk_img(self.id_original) or "SIN_FOTO"

        # 2. LLAMADA AL MOTOR (Aquí ocurre la magia)
        exito, mensaje = motor.guardar_o_actualizar_empleado(eid, nom, val, path_final, self.id_original)
        
        if exito:
            messagebox.showinfo("Éxito", mensaje)
            self.load_e() # Recargar tabla
            self.clr_e()  # Limpiar campos
        else:
            messagebox.showerror("Error", mensaje)

            # --- BUSCA EL FINAL DE LA CLASE SistemaV79 EN main.py ---

    def insertar_demo_calzados(self):
        """Inserta datos de prueba para la demostración al cliente."""
        productos_demo = [
            ("779001", "Zapatilla Nike Air Max", "Nike", "Negro", 42, 85000, 2), # Stock Bajo
            ("779002", "Zapato de Vestir Oxford", "Grimoldi", "Marrón", 41, 120000, 10),
            ("779003", "Zapatilla Adidas Runner", "Adidas", "Blanco", 39, 75000, 1), # Stock Bajo
            ("779004", "Bota de Cuero Urbana", "Briganti", "Suela", 38, 95000, 5),
            ("779005", "Zapatilla Urbana Canvas", "Puma", "Azul", 40, 60000, 0) # Sin Stock
        ]
        
        for p in productos_demo:
            # Llamamos al motor para que guarde cada producto en MySQL
            motor.guardar_producto(p)
        
        # Refrescamos la tabla para que se vean los cambios
        self.load_stock() 
        messagebox.showinfo("Demo", "¡Datos de calzado cargados para la demo!")

    def save_stock(self):
        """Recoge datos de la pestaña de calzado y los guarda en MySQL vía motor."""
        # 1. Recoger datos de los inputs
        cod = self.st_barras.get().strip()
        mod = self.st_modelo.get().strip()
        col = self.st_color.get().strip()
        tal = self.st_talle.get().strip()
        pre = self.st_precio.get().strip()
        can = self.st_cant.get().strip()

        # 2. Validaciones básicas
        if not cod or not mod:
            messagebox.showwarning("Faltan Datos", "El código y el modelo son obligatorios.")
            return

        try:
            # Preparamos la tupla para el motor (orden exacto de la query)
            # (codigo, modelo, marca, color, talle, precio, cantidad)
            # Usamos "" para marca por ahora ya que no pusimos un entry específico
            datos = (cod, mod, "", col, float(tal), float(pre), int(can))
            
            # 3. Llamar al motor
            exito, msg = motor.guardar_producto(datos)
            
            if exito:
                messagebox.showinfo("Éxito", "Producto registrado en stock correctamente.")
                self.limpiar_inputs_stock()
                self.load_stock() # <--- ESTA LÍNEA ES CLAVE
                
                # Opcional: recargar la tabla de stock si ya tienes el método load_stock
            else:
                messagebox.showerror("Error MySQL", msg)
                
        except ValueError:
            messagebox.showerror("Error de Formato", "Talle, Precio y Cantidad deben ser números.")
        except Exception as e:
            messagebox.showerror("Error Crítico", f"No se pudo guardar: {e}")

    def load_stock(self):
        """Carga productos y resalta los que tienen poco stock."""
        for i in self.tr_stk.get_children(): 
            self.tr_stk.delete(i)
        
        # Configuramos los colores de las etiquetas
        self.tr_stk.tag_configure("bajo_stock", background="#FFEBEE", foreground="#B71C1C") # Rojo suave
        self.tr_stk.tag_configure("sin_stock", background="#212121", foreground="#FF5252") # Gris oscuro/Rojo
        
        productos = motor.obtener_todos_productos() 
        
        for p in productos:
            cantidad = p[7] # El campo 'cantidad' en tu tabla MySQL
            tag_fila = "normal"
            
            if cantidad == 0:
                tag_fila = "sin_stock"
            elif cantidad <= 3: # Umbral de stock crítico
                tag_fila = "bajo_stock"
                
            self.tr_stk.insert("", "end", values=(p[0], p[2], p[4], p[5], p[7], f"${p[6]:,.0f}"), tags=(tag_fila,))

    def limpiar_inputs_stock(self):
        """Limpia el formulario de calzado tras guardar."""
        for entry in [self.st_barras, self.st_modelo, self.st_color, 
                    self.st_talle, self.st_precio, self.st_cant]:
            entry.delete(0, 'end')
    
    def chk_img(self, eid):
        """Versión MySQL: Busca la ruta de la foto usando el motor"""
        try:
            conn = motor.get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT foto_path FROM empleados WHERE id_reloj=%s", (eid,))
            r = cursor.fetchone()
            cursor.close()
            conn.close()
            return r[0] if r else None
        except:
            return None
    def del_e(self):
        id_a_borrar = self.e_id.get()
        if not id_a_borrar: return
        
        if messagebox.askyesno("Confirmar", f"¿Borrar empleado {id_a_borrar}?"):
            try:
                conn = motor.get_connection()
                cursor = conn.cursor()
                cursor.execute("DELETE FROM empleados WHERE id_reloj=%s", (id_a_borrar,))
                conn.commit()
                cursor.close()
                conn.close()
                self.load_e()
                self.clr_e()
                motor.actualizar_lista_blanca()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo borrar: {e}")
    def clr_e(self): self.id_original=None; self.e_id.delete(0,'end'); self.e_nom.delete(0,'end'); self.e_val.delete(0,'end'); self.path_tmp=None; self.upd_img_lbl(None)
    def on_sel(self, e):
        s = self.tr.selection()
        if s: v=self.tr.item(s[0])['values']; self.id_original=str(v[0]); self.e_id.delete(0,'end'); self.e_id.insert(0,str(v[0])); self.e_nom.delete(0,'end'); self.e_nom.insert(0,str(v[1])); self.e_val.delete(0,'end'); self.e_val.insert(0,str(v[2])); self.upd_img_lbl(self.chk_img(str(v[0])))
    # En main.py, busca la función load_e (línea ~474 aprox)
    def load_e(self):
        for i in self.tr.get_children(): self.tr.delete(i)
        
        # Llamada limpia al motor (sin popups)
        datos = motor.obtener_todos_empleados()
        
        for r in datos:
            self.tr.insert("", "end", values=r)

    def setup_liq(self):
        print("--- CARGANDO PESTAÑA LIQUIDACIÓN (WIN 7) ---") 
        f = self.tabs["liq"]
        for widget in f.winfo_children(): widget.destroy()

        # BARRA DE HERRAMIENTAS
        ff = ctk.CTkFrame(f, fg_color=("gray85", "#2b2b2b"))
        ff.pack(fill="x", padx=10, pady=10)
        
        # 1. Calendarios y Buscador
        self.btn_desde = ctk.CTkButton(ff, text=datetime.now().strftime("%Y-%m-%d"), width=100, fg_color=COLOR_ACCENT, command=lambda: PopupCalendario(self, lambda x: self.btn_desde.configure(text=x))); self.btn_desde.pack(side="left", padx=5)
        self.btn_hasta = ctk.CTkButton(ff, text=datetime.now().strftime("%Y-%m-%d"), width=100, fg_color=COLOR_ACCENT, command=lambda: PopupCalendario(self, lambda x: self.btn_hasta.configure(text=x))); self.btn_hasta.pack(side="left", padx=5)
        
        self.ico_buscar = self.cargar_icono("buscar.png", size=(20,20))
        ctk.CTkButton(ff, text="BUSCAR", image=self.ico_buscar, compound="left", width=100, fg_color="#0277BD", command=self.calc_rng).pack(side="left", padx=10)
        
        # 2. BOTÓN RECUPERAR (Verde)
        ctk.CTkButton(ff, text="RECUPERAR", width=100, fg_color="#2E7D32", hover_color="#1B5E20", command=lambda: self.sync(silencioso=False)).pack(side="left", padx=5)

        # 3. Perfil
        self.entry_perfil = ctk.CTkEntry(ff, width=120); self.entry_perfil.pack(side="left", padx=5)
        self.entry_perfil.bind('<Return>', lambda e: self.calc_rng())
        self.ico_user = self.cargar_icono("usuario.png", size=(20,20))
        ctk.CTkButton(ff, text="PERFIL", image=self.ico_user, compound="left", width=80, fg_color="#7B1FA2", command=self.abrir_perfil_individual).pack(side="left", padx=5)

        # 4. BOTONES EXPORTAR
        fe = ctk.CTkFrame(ff, fg_color="transparent"); fe.pack(side="right", padx=5)
        self.ico_pdf = self.cargar_icono("pdf.png", size=(20,20)); ctk.CTkButton(fe, text="PDF", image=self.ico_pdf, compound="left", width=80, fg_color="red", command=self.export_pdf).pack(side="left", padx=5)
        self.ico_excel = self.cargar_icono("excel.png", size=(20,20)); ctk.CTkButton(fe, text="EXCEL", image=self.ico_excel, compound="left", width=80, fg_color="#1B5E20", command=self.export_excel_pro).pack(side="left", padx=5)
        self.ico_txt = self.cargar_icono("txt.png", size=(20,20)); ctk.CTkButton(fe, text="TXT", image=self.ico_txt, compound="left", width=80, fg_color="gray", command=self.export_txt).pack(side="left", padx=5)

        # --- [MODIFICADO] INDICADOR CON PNG PARA WINDOWS 7 ---
        # Cargamos los iconos en memoria
        self.img_on = self.cargar_icono("on.png", size=(15,15))   # Bolita Verde
        self.img_off = self.cargar_icono("off.png", size=(15,15)) # Bolita Roja
        
        # Creamos el label usando la imagen OFF por defecto
        # compound="left" pone la imagen a la izquierda del texto
        self.lbl_estado_liq = ctk.CTkLabel(ff, 
                                           text=" CONECTANDO...", 
                                           image=self.img_off, 
                                           compound="left", 
                                           font=("Arial", 12, "bold"), 
                                           text_color="gray")
        self.lbl_estado_liq.pack(side="right", padx=15)
        # -----------------------------------------------------

        # 5. TABLA (Igual que siempre)
        columns = ("ID", "F", "E", "ENT", "SAL", "H", "P")
        self.tree_pay = ttk.Treeview(f, columns=columns, show="headings")
        self.tree_pay.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tree_pay.heading("ID", text="ID"); self.tree_pay.column("ID", width=40, anchor="center")
        self.tree_pay.heading("F", text="FECHA"); self.tree_pay.column("F", width=90)
        self.tree_pay.heading("E", text="EMPLEADO"); self.tree_pay.column("E", width=200)
        self.tree_pay.heading("ENT", text="ENTRADAS"); self.tree_pay.column("ENT", width=120, anchor="center")
        self.tree_pay.heading("SAL", text="SALIDAS"); self.tree_pay.column("SAL", width=120, anchor="center")
        self.tree_pay.heading("H", text="HORAS"); self.tree_pay.column("H", width=70, anchor="center")
        self.tree_pay.heading("P", text="A PAGAR"); self.tree_pay.column("P", width=90, anchor="e")
        
        self.tree_pay.tag_configure("normal", background="white", foreground="black")
        self.tree_pay.tag_configure("error", background="#B71C1C", foreground="white") 
        self.tree_pay.bind("<Double-1>", self.al_doble_clic_lista)
        self.tree_pay.bind("<<TreeviewSelect>>", self.al_seleccionar_fila_liq)

    # --- REEMPLAZAR EN main.py (Clase SistemaV79) ---
    def calc_rng(self):
        # 1. Limpiar tabla
        for i in self.tree_pay.get_children(): self.tree_pay.delete(i)
        self.datos_exportacion = [] 
        
        di = self.btn_desde.cget("text")
        df = self.btn_hasta.cget("text")
        # [NUEVO] Obtenemos lo que haya escrito el usuario (Vacío = Todos)
        filtro_nombre = self.entry_perfil.get().strip()
        
        # 2. Pedir datos al motor (Le pasamos el filtro también)
        datos = motor.calcular_liquidacion_rango(di, df, filtro_nombre)
        
        if not datos:
            messagebox.showinfo("Información", "No se encontraron movimientos.")
            return

        self.datos_exportacion = datos 
        
        for fila in datos:
            pago_fmt = f"${fila['PAGO']:,.0f}"
            etiqueta = "error" if fila.get("ERROR", False) else "normal"
            horas_visual = decimal_a_hm(fila['HS'])

            self.tree_pay.insert("", "end", values=(
                fila["ID"],
                fila["FECHA"],
                fila["EMPLEADO"],
                fila["ENTRADAS"],
                fila["SALIDAS"],
                f"{horas_visual} hs",
                pago_fmt
            ), tags=(etiqueta,))

    def al_doble_clic_lista(self, event):
        s = self.tree_pay.selection()
        if not s: return
        try:
            # Obtenemos el ID directamente de la tabla (es el primer valor)
            id_reloj = self.tree_pay.item(s[0])['values'][0]
            VentanaPerfil(self, id_reloj)
        except Exception as e:
            print(f"Error al abrir perfil: {e}")
    def al_seleccionar_fila_liq(self, event):
        """Toma el nombre de la fila seleccionada y lo pone en el buscador."""
        seleccion = self.tree_pay.selection()
        if seleccion:
            # Los valores son: (ID, FECHA, EMPLEADO, ENT, SAL, HS, PAGO)
            # El nombre está en el índice 2
            item = self.tree_pay.item(seleccion[0])
            nombre = item['values'][2]
            
            # Llenamos el entry
            self.entry_perfil.delete(0, 'end')
            self.entry_perfil.insert(0, nombre)
    def abrir_perfil_individual(self):
        # 1. Obtener el nombre del buscador
        nombre_buscado = self.entry_perfil.get().strip()
        
        if not nombre_buscado: 
            messagebox.showwarning("Atención", "El campo de búsqueda está vacío.")
            return

        # 2. Pedir al motor que busque el ID en MySQL (Usando la conexión correcta)
        # Reutilizamos la función del motor que ya busca empleados
        datos_empleados = motor.obtener_todos_empleados() # Devuelve lista de tuplas (id, nombre, valor, foto)
        
        id_encontrado = None
        
        # Buscamos coincidencia exacta o parcial
        for emp in datos_empleados:
            eid, enombre, _, _ = emp
            # Comparamos nombres en minúsculas para evitar errores
            if nombre_buscado.lower() == enombre.lower():
                id_encontrado = eid
                break
            elif nombre_buscado.lower() in enombre.lower():
                id_encontrado = eid # Guardamos por si acaso es parcial
        
        # 3. Abrir perfil si encontramos algo
        if id_encontrado:
            VentanaPerfil(self, id_encontrado)
        else:
            messagebox.showerror("Error", f"No se encontró al empleado: {nombre_buscado}")
    def export_excel_pro(self):
        if not hasattr(self, 'datos_exportacion') or not self.datos_exportacion: 
            messagebox.showwarning("!", "Primero realiza una búsqueda")
            return
        
        # Usamos reportes.generar_nombre para que el archivo tenga fecha y hora automática
        nombre_default = reportes.generar_nombre("xlsx") 
        p = filedialog.asksaveasfilename(defaultextension=".xlsx", initialfile=nombre_default, filetypes=[("Excel", "*.xlsx")])
        
        if p:
            # Llamamos a TU función avanzada de reportes.py
            exito, msg = reportes.exportar_excel(self.datos_exportacion, p)
            if exito: 
                messagebox.showinfo("Éxito", msg)
                try: os.startfile(p)
                except: pass
            else:
                messagebox.showerror("Error", msg)

    def export_pdf(self):
        if not hasattr(self, 'datos_exportacion') or not self.datos_exportacion: 
            messagebox.showwarning("!", "Primero realiza una búsqueda")
            return

        nombre_default = reportes.generar_nombre("pdf")
        p = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=nombre_default, filetypes=[("PDF", "*.pdf")])
        
        if p:
            exito, msg = reportes.exportar_pdf(self.datos_exportacion, p)
            if exito:
                messagebox.showinfo("Éxito", msg)
                try: os.startfile(p)
                except: pass
            else:
                messagebox.showerror("Error", msg)

    def export_txt(self):
        if not hasattr(self, 'datos_exportacion') or not self.datos_exportacion: 
            messagebox.showwarning("!", "Primero realiza una búsqueda")
            return

        nombre_default = reportes.generar_nombre("txt")
        p = filedialog.asksaveasfilename(defaultextension=".txt", initialfile=nombre_default, filetypes=[("Texto", "*.txt")])
        
        if p:
            exito, msg = reportes.exportar_txt(self.datos_exportacion, p)
            if exito:
                messagebox.showinfo("Éxito", msg)
                try: os.startfile(p)
                except: pass
            else:
                messagebox.showerror("Error", msg)

    def setup_hist(self):
        f = self.tabs["hist"]
        # Marco de herramientas
        f1 = ctk.CTkFrame(f)
        f1.pack(fill="x", padx=10, pady=10)
        
        # 1. Filtro de Fecha
        self.date_picker = ctk.CTkEntry(f1, placeholder_text="YYYY-MM-DD", width=110)
        self.date_picker.pack(side="left", padx=5)
        self.date_picker.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # 2. NUEVO: Buscador Dinámico (Nombre/ID)
        self.hist_search = ctk.CTkEntry(f1, placeholder_text="Buscar nombre o ID...", width=200)
        self.hist_search.pack(side="left", padx=5)
        self.hist_search.bind("<KeyRelease>", lambda e: self.ver_db()) # Filtro al escribir

        # 3. Botón Refrescar
        self.ico_ver = self.cargar_icono("buscar.png", size=(20,20))
        ctk.CTkButton(f1, text="VER", image=self.ico_ver, compound="left", width=90, 
                     command=self.ver_db).pack(side="left", padx=5)
        
        # 4. BOTÓN EDITAR (Restaurado)
        self.ico_edit = self.cargar_icono("editar.png", size=(20,20))
        ctk.CTkButton(f1, text="EDITAR", image=self.ico_edit, compound="left", 
                     fg_color="#00897B", width=90, 
                     command=self.abrir_editor_manual).pack(side="left", padx=5)
        
        # 5. BOTÓN BORRAR (Restaurado)
        self.ico_del_hist = self.cargar_icono("borrar.png", size=(20,20))
        ctk.CTkButton(f1, text="BORRAR", image=self.ico_del_hist, compound="left", 
                     fg_color="#B71C1C", hover_color="#D32F2F", width=90, 
                     command=self.del_rec).pack(side="right", padx=10)
        
        # --- TABLA CON COLUMNA NOMBRE ---
        self.tree_hist = ttk.Treeview(f, columns=("ID_DB", "FECHA", "ID_REL", "NOM", "INFO"), show="headings")
        self.tree_hist.pack(fill="both", expand=True, padx=10, pady=(0,10))
        
        self.tree_hist.heading("ID_DB", text="ID DB")
        self.tree_hist.heading("FECHA", text="FECHA Y HORA")
        self.tree_hist.heading("ID_REL", text="ID RELOJ")
        self.tree_hist.heading("NOM", text="EMPLEADO")
        self.tree_hist.heading("INFO", text="ORIGEN/RAW")
        
        # Ajuste de anchos
        self.tree_hist.column("ID_DB", width=60, anchor="center")
        self.tree_hist.column("NOM", width=250)
        self.tree_hist.column("ID_REL", width=80, anchor="center")
    
    def ver_db(self):
        # Limpiar tabla
        for i in self.tree_hist.get_children(): self.tree_hist.delete(i)
        
        f_dia = self.date_picker.get().strip()
        f_txt = self.hist_search.get().strip()
        
        # Pedir datos al motor con ambos filtros
        rows = motor.buscar_fichadas_historial(f_txt, f_dia)
        
        for row in rows:
            self.tree_hist.insert("", "end", values=row)
    
    def del_rec(self):
        s = self.tree_hist.selection()
        if not s: return
        
        if messagebox.askyesno("Confirmar", "¿Seguro que deseas borrar los registros seleccionados?"):
            borrados = 0
            for i in s:
                id_db = self.tree_hist.item(i)['values'][0]
                # Llamada al motor para borrar
                if motor.eliminar_fichada(id_db):
                    borrados += 1
            
            if borrados > 0:
                messagebox.showinfo("Listo", f"Se borraron {borrados} registros.")
                self.ver_db() # Recargar tabla
                # Actualizamos monitor por si borramos algo de hoy
                self.actualizar_tablero()

    def abrir_editor_manual(self):
        top = ctk.CTkToplevel(self)
        top.title("Editor Manual")
        top.geometry("400x450")
        top.attributes("-topmost", True)
        
        # Variables iniciales
        edit_id_db = None
        edit_fecha = datetime.now().strftime("%Y-%m-%d")
        edit_hora = datetime.now().strftime("%H:%M:%S")
        edit_id_emp = ""

        # Si hay selección, precargamos datos para EDITAR
        seleccion = self.tree_hist.selection()
        if seleccion:
            item = self.tree_hist.item(seleccion[0])['values']
            edit_id_db = item[0]
            full_date = item[1]
            edit_id_emp = str(item[2])
            try:
                dt = datetime.strptime(full_date, "%Y-%m-%d %H:%M:%S")
                edit_fecha = dt.strftime("%Y-%m-%d")
                edit_hora = dt.strftime("%H:%M:%S")
            except: pass

        # 1. CARGAR EMPLEADOS DESDE EL MOTOR (Reutilizamos la función que hicimos antes)
        datos_emps = motor.obtener_todos_empleados() # Devuelve [(id, nombre, ...), ...]
        lista_emps = [f"{e[0]} - {e[1]}" for e in datos_emps]

        # UI del Popup
        ctk.CTkLabel(top, text="Seleccionar Empleado:").pack(pady=(20,5))
        combo_emp = ctk.CTkOptionMenu(top, values=lista_emps, width=250)
        combo_emp.pack(pady=5)
        
        # Pre-seleccionar empleado si es edición
        if edit_id_emp:
            for e in lista_emps:
                if e.startswith(f"{edit_id_emp} -"):
                    combo_emp.set(e)
                    break
        
        ctk.CTkLabel(top, text="Fecha (YYYY-MM-DD):").pack(pady=(10,5))
        entry_fecha = ctk.CTkEntry(top, width=250)
        entry_fecha.pack(pady=5)
        entry_fecha.insert(0, edit_fecha)
        
        ctk.CTkLabel(top, text="Hora (HH:MM:SS):").pack(pady=(10,5))
        entry_hora = ctk.CTkEntry(top, width=250)
        entry_hora.pack(pady=5)
        entry_hora.insert(0, edit_hora)

        # Función interna de guardado
        def accion_guardar():
            txt = combo_emp.get()
            if not txt or " - " not in txt:
                messagebox.showwarning("!", "Seleccione un empleado válido")
                return
            
            nid = txt.split(" - ")[0]
            fech_final = f"{entry_fecha.get()} {entry_hora.get()}"
            
            # 2. GUARDAR USANDO EL MOTOR
            if motor.guardar_fichada_manual(edit_id_db, nid, fech_final):
                top.destroy()
                self.ver_db()             # Recargar lista historial
                self.actualizar_tablero() # Recargar monitor (por si afectó a hoy)
                # Opcional: Si editaste un empleado visible en perfil, también podrías actualizarlo
            else:
                messagebox.showerror("Error", "No se pudo guardar")

        ctk.CTkButton(top, text="GUARDAR CAMBIOS", fg_color="#00897B", command=accion_guardar).pack(pady=30)

# --- INICIO DEL SISTEMA ---

        # --- MÓDULO PUNTO DE VENTA (DEMO PANADERÍA) ---
    def setup_pos(self):
        f = self.tabs["pos"]
        
        # 1. Layout Principal: Izquierda (Productos) - Derecha (Ticket)
        f.grid_columnconfigure(0, weight=3)
        f.grid_columnconfigure(1, weight=1)
        f.grid_rowconfigure(0, weight=1)

        # --- ÁREA DE PRODUCTOS (IZQUIERDA) ---
        p_frame = ctk.CTkFrame(f, fg_color="transparent")
        p_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        # Filtros de Categoría
        cat_frame = ctk.CTkScrollableFrame(p_frame, height=60, orientation="horizontal", fg_color="transparent")
        cat_frame.pack(fill="x", pady=(0, 10))
        
        categorias = ["🍞 PANADERÍA", "🍰 PASTELERÍA", "🥪 SÁNDWICHES", "☕ CAFETERÍA", "🥤 BEBIDAS"]
        self.cat_var = ctk.StringVar(value="🍞 PANADERÍA")

        for cat in categorias:
            btn = ctk.CTkButton(
                cat_frame, 
                text=cat, 
                width=120, 
                height=40,
                fg_color="#5D4037", # Marrón Panadería
                hover_color="#8D6E63",
                command=lambda c=cat: self.cargar_productos(c)
            )
            btn.pack(side="left", padx=5)

        # Grilla de Productos
        self.grid_prod = ctk.CTkScrollableFrame(p_frame, fg_color=("gray95", "#333"))
        self.grid_prod.pack(fill="both", expand=True)

        # --- ÁREA DE TICKET (DERECHA) ---
        t_frame = ctk.CTkFrame(f, fg_color=("white", "#2b2b2b"), corner_radius=15)
        t_frame.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(t_frame, text="🧾 TICKET ACTUAL", font=("Arial", 18, "bold")).pack(pady=15)
        
        # Lista de Items
        self.tree_ticket = ttk.Treeview(t_frame, columns=("cant", "prod", "total"), show="headings", height=15)
        self.tree_ticket.heading("cant", text="Cnt"); self.tree_ticket.column("cant", width=40, anchor="center")
        self.tree_ticket.heading("prod", text="Producto"); self.tree_ticket.column("prod", width=140)
        self.tree_ticket.heading("total", text="$ Total"); self.tree_ticket.column("total", width=80, anchor="e")
        self.tree_ticket.pack(fill="both", expand=True, padx=10)
        
        # Bind para borrar con doble click
        self.tree_ticket.bind("<Double-1>", self.borrar_item_ticket)

        # Totales y Botones
        f_tot = ctk.CTkFrame(t_frame, fg_color="transparent")
        f_tot.pack(fill="x", padx=15, pady=15)
        
        self.lbl_total_pos = ctk.CTkLabel(f_tot, text="TOTAL: $0", font=("Arial", 32, "bold"), text_color="#00E676")
        self.lbl_total_pos.pack(pady=10)
        
        ctk.CTkButton(f_tot, text="💵 COBRAR (F5)", height=60, font=("Arial", 20, "bold"), fg_color="#2E7D32", hover_color="#1B5E20", command=self.cobrar_demo).pack(fill="x", pady=5)
        ctk.CTkButton(f_tot, text="🗑️ CANCELAR", height=30, fg_color="#c62828", hover_color="#b71c1c", command=self.limpiar_ticket).pack(fill="x", pady=5)

        # Cargar productos iniciales
        self.cargar_productos("🍞 PANADERÍA")

    def cargar_productos(self, categoria):
        # Limpiar grilla
        for widget in self.grid_prod.winfo_children(): widget.destroy()
        
        # DATOS DEMO (ESTO LUEGO VENDRÁ DE LA BASE DE DATOS)
        db_fake = {
            "🍞 PANADERÍA": [
                ("🥖 Pan Francés", 2800, "kg"), ("🥐 Medialuna Manteca", 900, "un"), 
                ("🥐 Medialuna Grasa", 800, "un"), ("🍞 Pan de Miga", 4500, "paq"),
                ("🥨 Bizcochos", 3500, "kg"), ("🥯 Criollitos", 3200, "kg")
            ],
            "🍰 PASTELERÍA": [
                ("🍰 Torta Selva Negra", 18000, "un"), ("🧁 Muffin Choco", 1500, "un"),
                ("🍩 Dona Rellena", 1200, "un"), ("🍪 Alfajor Maicena", 900, "un"),
                ("🥧 Pasta Frola", 8500, "un"), ("🍮 Tiramisú", 4200, "porción")
            ],
            "🥪 SÁNDWICHES": [
                ("🥪 Miga J&Q", 12000, "doc"), ("🥪 Miga Surtido", 14000, "doc"),
                ("🥖 Pebete Completo", 3500, "un"), ("🌭 Pancho Elect.", 2000, "un")
            ],
            "☕ CAFETERÍA": [
                ("☕ Café Chico", 1800, "un"), ("☕ Café Jarrita", 2200, "un"),
                ("☕ Capuchino", 2600, "un"), ("🥛 Submarino", 2800, "un")
            ],
            "🥤 BEBIDAS": [
                ("🥤 Coca-Cola 500", 1800, "un"), ("🥤 Agua s/gas", 1500, "un"),
                ("🧃 Jugo Naranja", 2000, "un"), ("🍺 Cerveza Lata", 2500, "un")
            ]
        }

        items = db_fake.get(categoria, [])
        r, c = 0, 0
        MAX_COLS = 3 # Ajustar según tamaño de pantalla

        for nom, prec, unidad in items:
            # Tarjeta de Producto
            card = ctk.CTkButton(
                self.grid_prod,
                text=f"{nom}\n${prec} / {unidad}",
                font=("Arial", 16, "bold"),
                width=180, height=100,
                corner_radius=15,
                fg_color="#3E2723" if "PAN" in categoria else "#1565C0" if "BEB" in categoria else "#E65100", # Colores por categoría
                hover_color="#5D4037",
                command=lambda n=nom, p=prec: self.agregar_al_ticket(n, p)
            )
            card.grid(row=r, column=c, padx=10, pady=10, sticky="ew")
            
            c += 1
            if c >= MAX_COLS:
                c = 0; r += 1

    def agregar_al_ticket(self, nombre, precio):
        # Buscar si ya existe para sumar cantidad
        encontrado = False
        for item in self.tree_ticket.get_children():
            vals = self.tree_ticket.item(item)['values']
            if vals[1] == nombre:
                cant_nueva = int(vals[0]) + 1
                total_nuevo = cant_nueva * precio
                self.tree_ticket.item(item, values=(cant_nueva, nombre, total_nuevo))
                encontrado = True
                break
        
        if not encontrado:
            self.tree_ticket.insert("", "end", values=(1, nombre, precio))
        
        self.actualizar_total_ticket()

    def borrar_item_ticket(self, event):
        sel = self.tree_ticket.selection()
        if sel:
            self.tree_ticket.delete(sel[0])
            self.actualizar_total_ticket()

    def limpiar_ticket(self):
        for item in self.tree_ticket.get_children():
            self.tree_ticket.delete(item)
        self.actualizar_total_ticket()

    def actualizar_total_ticket(self):
        total = 0
        for item in self.tree_ticket.get_children():
            total += float(self.tree_ticket.item(item)['values'][2])
        self.lbl_total_pos.configure(text=f"TOTAL: ${total:,.0f}")

    def cobrar_demo(self):
        total_str = self.lbl_total_pos.cget("text")
        if total_str == "TOTAL: $0": return
        
        # Aquí iría la integración real de facturación o guardado en BD
        msg = f"✅ ¡VENTA REGISTRADA!\n\n{total_str}\n\n(En la versión final, esto abre\nel cajón de dinero e imprime el ticket)"
        messagebox.showinfo("Demo Panadería", msg)
        self.limpiar_ticket()


if __name__ == "__main__":
    if hasattr(sys, "excepthook"):
        sys.excepthook = manejar_errores_criticos
    
    print("--- INICIANDO SISTEMA FRUT&EM (MODO MYSQL) ---")
    app = SistemaV79()
    app.mainloop()
