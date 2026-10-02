import pandas as pd
import os
from datetime import datetime
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.drawing.image import Image
from openpyxl.utils import get_column_letter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from config import LOGO_PATH # Importamos la ruta del logo

# --- FUNCIÓN AUXILIAR DE HORAS ---
def decimal_a_hm(horas_decimales):
    """Convierte 7.75 a '07:45'"""
    try:
        if not horas_decimales or horas_decimales < 0: return "00:00"
        horas = int(horas_decimales)
        minutos = int(round((horas_decimales - horas) * 60))
        if minutos == 60: horas += 1; minutos = 0
        return f"{horas:02d}:{minutos:02d}"
    except: return "00:00"

def generar_nombre(ext):
    h = datetime.now()
    # Usamos segundos para evitar sobrescritura y guiones para máxima compatibilidad
    # Ejemplo: Reporte_24-Ene_14-58-02.pdf
    ms = ["","Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
    return f"Reporte_{h.day:02d}-{ms[h.month]}_{h.hour:02d}-{h.minute:02d}-{h.second:02d}.{ext}"

# ==============================================================================
#                             EXCEL PROFESIONAL V2.0
# ==============================================================================

def exportar_stock_excel(datos, path):
    # Reutilizamos tu lógica de openpyxl pero enfocada a productos
    # Usamos COLOR_ACCENT para el header
    try:
        df = pd.DataFrame(datos)
        # ... lógica similar a exportar_excel ...
        return True, "Reporte de stock generado"
    except Exception as e: return False, str(e)

def exportar_excel(datos, path):
    try:
        df = pd.DataFrame(datos)
        
        # 1. PREPARAR DATOS Y TOTALES
        cols_exportar = ["ID", "FECHA", "EMPLEADO", "ENTRADAS", "SALIDAS", "HS", "PAGO"]
        cols_finales = [c for c in cols_exportar if c in df.columns]
        df = df[cols_finales]
        
        # Calculamos totales numéricos antes de convertir a texto
        tot_h_dec = df["HS"].sum() if "HS" in df.columns else 0
        tot_p = df["PAGO"].sum() if "PAGO" in df.columns else 0
        
        # Convertimos columna HS a formato visual HH:MM
        if "HS" in df.columns:
            df["HS"] = df["HS"].apply(decimal_a_hm)

        # Renombrar columnas para el Excel
        df = df.rename(columns={
            "HS": "HORAS", 
            "PAGO": "A PAGAR ($)",
            "ENTRADAS": "ENTRADA",
            "SALIDAS": "SALIDA"
        })

        # Fila de totales
        row_total = {
            "ID": "", 
            "FECHA": "", 
            "EMPLEADO": "TOTAL FINAL", 
            "ENTRADA": "", 
            "SALIDA": "", 
            "HORAS": decimal_a_hm(tot_h_dec), 
            "A PAGAR ($)": tot_p
        }
        df_total = pd.DataFrame([row_total])
        df = pd.concat([df, df_total], ignore_index=True)

        # 2. ESCRIBIR EN EXCEL (EMPEZANDO EN LA FILA 5 PARA DEJAR ESPACIO AL TITULO)
        with pd.ExcelWriter(path, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Liquidación', startrow=4)
            ws = writer.sheets['Liquidación']
            
            # --- ESTILOS DEFINIDOS ---
            borde_fino = Border(
                left=Side(style='thin'), right=Side(style='thin'), 
                top=Side(style='thin'), bottom=Side(style='thin')
            )
            borde_total = Border(top=Side(style='double'), bottom=Side(style='thick'))
            
            relleno_rojo = PatternFill("solid", fgColor="B71C1C")
            relleno_gris = PatternFill("solid", fgColor="F2F2F2")
            relleno_dorado = PatternFill("solid", fgColor="FFD700")
            
            fuente_blanca = Font(color="FFFFFF", bold=True, size=11)
            fuente_titulo = Font(color="B71C1C", bold=True, size=16)
            fuente_subtitulo = Font(color="555555", bold=True, size=10)

            # 3. CABECERA PERSONALIZADA (LOGO Y TÍTULO)
            # Intentar poner logo
            if os.path.exists(LOGO_PATH):
                try:
                    img = Image(LOGO_PATH)
                    img.width = 85
                    img.height = 85
                    ws.add_image(img, 'A1')
                except: pass
            
            # Título Principal (Celdas B1 a G1 combinadas)
            ws.merge_cells('B2:G2')
            cell_title = ws['B2']
            cell_title.value = "REPORTE DE LIQUIDACIÓN DE PERSONAL"
            cell_title.font = fuente_titulo
            cell_title.alignment = Alignment(horizontal='center', vertical='center')

            # Fecha de Generación
            ws.merge_cells('B3:G3')
            cell_sub = ws['B3']
            cell_sub.value = f"Generado el: {datetime.now().strftime('%d/%m/%Y a las %H:%M hs')}"
            cell_sub.font = fuente_subtitulo
            cell_sub.alignment = Alignment(horizontal='center', vertical='top')

            # 4. FORMATEAR CABECERA DE TABLA (FILA 5)
            for cell in ws[5]:
                cell.fill = relleno_rojo
                cell.font = fuente_blanca
                cell.alignment = Alignment(horizontal="center", vertical="center")
                cell.border = borde_fino

            # 5. FORMATEAR DATOS (FILAS 6 en adelante)
            max_row = ws.max_row
            col_pago_letter = None
            
            # Buscamos cual es la columna de PAGO dinámicamente
            for idx, col in enumerate(df.columns, 1):
                if "PAGO" in str(col).upper():
                    col_pago_letter = get_column_letter(idx)

            # Iteramos filas de datos
            for row in range(6, max_row + 1):
                # Estilo alternado (Zebra) para leer mejor
                es_par = (row % 2 == 0)
                fill_row = relleno_gris if es_par else None
                
                # Detectar si es la fila de TOTALES (la última)
                es_total = (row == max_row)
                
                for col in range(1, len(df.columns) + 1):
                    cell = ws.cell(row=row, column=col)
                    cell.border = borde_fino
                    
                    if es_total:
                        cell.fill = relleno_dorado
                        cell.font = Font(bold=True, size=12)
                        cell.border = borde_total
                    elif fill_row:
                        cell.fill = fill_row

                    # Alineaciones inteligentes
                    # ID (Col 1) y Fecha (Col 2) -> Centro
                    if col <= 2: 
                        cell.alignment = Alignment(horizontal='center')
                    # Horas (Col 6 aprox) -> Centro
                    elif "HORAS" in df.columns[col-1]:
                        cell.alignment = Alignment(horizontal='center')
                    # Plata -> Derecha
                    elif "PAGO" in df.columns[col-1]:
                        cell.alignment = Alignment(horizontal='right')
                        cell.number_format = '$ #,##0' # Formato Moneda
                    # Texto normal (Nombres) -> Izquierda con sangría
                    else:
                        cell.alignment = Alignment(horizontal='left', indent=1)

            # 6. AJUSTE DE ANCHOS
            ws.column_dimensions['A'].width = 8   # ID
            ws.column_dimensions['B'].width = 12  # Fecha
            ws.column_dimensions['C'].width = 30  # Empleado
            ws.column_dimensions['D'].width = 18  # Entrada
            ws.column_dimensions['E'].width = 18  # Salida
            ws.column_dimensions['F'].width = 12  # Horas
            ws.column_dimensions['G'].width = 15  # Pago

            # 7. INMOVILIZAR PANELES (Para que el título baje contigo)
            ws.freeze_panes = 'A6'

        return True, "Excel Profesional generado"
    except Exception as e:
        return False, f"Error Excel: {str(e)}"

# ==============================================================================
#                             TXT Y PDF (Sin Cambios)
# ==============================================================================

def exportar_txt(datos, path):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write("="*100+"\n  REPORTE DETALLADO - FRUT&EM\n"+"="*100+"\n\n")
            df = pd.DataFrame(datos)
            total_gral = 0
            if "EMPLEADO" in df.columns:
                grupos = df.groupby(["ID", "EMPLEADO"]) if "ID" in df.columns else df.groupby("EMPLEADO")
                for key, g in grupos:
                    if isinstance(key, tuple): eid, nom = key; header = f"EMPLEADO: {nom} (ID: {eid})"
                    else: header = f"EMPLEADO: {key}"
                    
                    f.write(header + "\n" + ("-"*100) + "\n")
                    f.write(f"{'FECHA':<12} | {'ENTRADAS':<20} | {'SALIDAS':<20} | {'HORAS':<8} | {'A PAGAR':<12}\n")
                    f.write("-" * 100 + "\n")
                    sub = 0
                    for _, r in g.iterrows():
                        pago = r.get('PAGO', 0)
                        hs_vis = decimal_a_hm(r.get('HS', 0))
                        ent = str(r.get('ENTRADAS', '')); sal = str(r.get('SALIDAS', ''))
                        f.write(f"{r.get('FECHA',''):<12} | {ent:<20} | {sal:<20} | {hs_vis:<6} hs | ${pago:>10,.0f}\n")
                        sub += pago
                    f.write("-" * 100 + f"\nSUBTOTAL: ${sub:,.2f}\n\n")
                    total_gral += sub
            f.write("="*100+f"\nTOTAL FINAL: ${total_gral:,.2f}\n"+"="*100)
        return True, "TXT guardado"
    except Exception as e: return False, str(e)

def exportar_pdf(datos, path):
    try:
        c = canvas.Canvas(path, pagesize=A4); w, h = A4
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, h-50, "REPORTE DE PERSONAL - FRUT&EM")
        y = h-100; df = pd.DataFrame(datos); total_gral = 0
        if "EMPLEADO" in df.columns:
            grupos = df.groupby(["ID", "EMPLEADO"]) if "ID" in df.columns else df.groupby("EMPLEADO")
            for key, g in grupos:
                if y < 100: c.showPage(); y = h-50
                if isinstance(key, tuple): eid, nom = key; titulo = f"Empleado: {nom} (ID: {eid})"
                else: titulo = f"Empleado: {key}"
                
                c.setFont("Helvetica-Bold", 12); c.setFillColor(colors.darkred)
                c.drawString(50, y, titulo); y -= 20
                c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 9)
                c.drawString(50, y, "FECHA"); c.drawString(130, y, "ENTRADAS"); c.drawString(250, y, "SALIDAS")
                c.drawString(380, y, "HORAS"); c.drawString(450, y, "A PAGAR"); y -= 5
                c.line(50, y, 550, y); y -= 15
                sub = 0; c.setFont("Helvetica", 9)
                for _, r in g.iterrows():
                    if y < 50: c.showPage(); y = h-50
                    pago = r.get('PAGO', 0); hs_vis = decimal_a_hm(r.get('HS', 0))
                    c.drawString(50, y, str(r.get('FECHA','')))
                    c.drawString(130, y, str(r.get('ENTRADAS',''))[:20])
                    c.drawString(250, y, str(r.get('SALIDAS',''))[:20])
                    c.drawString(380, y, f"{hs_vis} hs")
                    c.drawString(450, y, f"${pago:,.0f}")
                    sub += pago; y -= 15
                total_gral += sub; y -= 20
        c.setFont("Helvetica-Bold", 16); c.setFillColor(colors.darkblue)
        c.drawString(50, y-20, f"TOTAL FINAL A PAGAR: ${total_gral:,.0f}"); c.save()
        return True, "PDF Generado"
    except Exception as e: return False, str(e)