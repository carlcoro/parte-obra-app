import streamlit as st
import openpyxl
import pandas as pd
from fpdf import FPDF
import io
import datetime

# ==========================================
# 0. CONFIGURACIÓN E INTERFAZ DE STREAMLIT
# ==========================================
st.set_page_config(page_title="Gestor de Partes de Obra", layout="wide")
st.title("🚧 Sistema de Gestión de Partes de Obra")

# Diccionario de unificación de nombres
DICCIONARIO_NOMBRES = {
    "carlos": "Carlos Corobo", "carlos c": "Carlos Corobo", "carlos corobo": "Carlos Corobo",
    "sergio": "Sergio Moreno", "sergio m": "Sergio Moreno", "sergio moreno": "Sergio Moreno",
    "arturo": "Arturo Cano", "arturo c": "Arturo Cano", "arturo cano": "Arturo Cano",
    "gabriel": "Gabriel Moreno", "gabriel m": "Gabriel Moreno", "gabriel moreno": "Gabriel Moreno"
}

def unificar_nombre(nombre_crudo):
    if not nombre_crudo:
        return "Desconocido"
    return DICCIONARIO_NOMBRES.get(str(nombre_crudo).strip().lower(), str(nombre_crudo).strip())

# ==========================================
# 1. FORMULARIO DE ENTRADA DE DATOS
# ==========================================
col1, col2, col3 = st.columns(3)
with col1:
    num_parte = st.text_input("Nº Parte", value="1")
    obra = st.text_input("Obra", value="Sin Obra")
    cliente = st.text_input("Cliente", value="")
with col2:
    fecha_dt = st.date_input("Fecha", datetime.date.today())
    fecha = fecha_dt.strftime("%d-%m-%Y")
    jefe_obra = st.text_input("Jefe de Obra", value="")
with col3:
    ubicacion = st.text_input("Ubicación", value="")
    km = st.number_input("Kilómetros realizados", min_value=0, value=0)

trabajos = st.text_area("Trabajos Realizados (Uno por línea)", value="")

st.subheader("👥 Personal Asignado")
df_operarios = st.data_editor(
    pd.DataFrame([{"Operario": "", "Horas": 0.0}]),
    num_rows="dynamic",
    key="tabla_operarios"
)

st.subheader("📦 Materiales Utilizados")
df_materiales = st.data_editor(
    pd.DataFrame([{"Material": "", "Cantidad": 0.0, "Unidad": "uds"}]),
    num_rows="dynamic",
    key="tabla_materiales"
)

# Subir la plantilla Excel existente
st.subheader("📁 Archivo Base")
archivo_subido = st.file_uploader("Sube tu archivo 'Plantilla_Parte_Obra_Profesional.xlsx'", type=["xlsx"])

# ==========================================
# 2. PROCESAMIENTO Y GENERACIÓN (AL COLEGIO DE BOTONES)
# ==========================================
if archivo_subido is not None:
    if st.button("🚀 Generar Documentos y Actualizar Base de Datos"):
        
        # --- PROCESAR DATOS DE OPERARIOS Y MATERIALES ---
        operarios_datos_crudos = []
        operarios_lista = []
        for index, row in df_operarios.iterrows():
            if row["Operario"]:
                op_oficial = unificar_nombre(row["Operario"])
                operarios_datos_crudos.append((op_oficial, row["Horas"]))
                operarios_lista.append(f"{op_oficial} ({row['Horas']}h)")
        operarios_texto = ", ".join(operarios_lista)

        materiales_lista = []
        materiales_datos = []
        for index, row in df_materiales.iterrows():
            if row["Material"]:
                materiales_lista.append(f"{row['Material']}: {row['Cantidad']} {row['Unidad']}")
                materiales_datos.append((str(row['Material']), str(row['Cantidad']), str(row['Unidad'])))
        materiales_texto = ", ".join(materiales_lista)

        # --- GENERAR PDF EN MEMORIA ---
        class PDFParte(FPDF):
            def header(self):
                self.set_font("Helvetica", "B", 14)
                self.set_text_color(46, 125, 50)
                self.cell(190, 10, "PARTE DIARIO DE TRABAJO", border=1, ln=1, align="C")
                self.ln(5)

        pdf = PDFParte(orientation="P", unit="mm", format="A4")
        pdf.add_page()
        pdf.set_font("Helvetica", "", 10)

        # Bloque Información General
        pdf.set_fill_color(232, 245, 233)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "Nº Parte:", border=1, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(65, 7, str(num_parte), border=1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "Fecha:", border=1, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(65, 7, str(fecha), border=1, ln=1)

        # (Se omite parte del diseño visual repetitivo del PDF por espacio, mantiene tu estructura original)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "Obra:", border=1, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(65, 7, str(obra), border=1)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(30, 7, "Jefe de Obra:", border=1, fill=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(65, 7, str(jefe_obra), border=1, ln=1)
        pdf.ln(5)

        # Trabajos
        pdf.set_font("Helvetica", "B", 11)
        pdf.cell(190, 7, "TRABAJOS REALIZADOS", ln=1)
        pdf.set_font("Helvetica", "", 10)
        pdf.multi_cell(190, 6, trabajos if trabajos else "Ninguno", border=1)
        pdf.ln(5)

        # Operarios en PDF
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(130, 6, "Operario", border=1, fill=True)
        pdf.cell(60, 6, "Horas", border=1, ln=1, fill=True)
        pdf.set_font("Helvetica", "", 10)
        for op, hr in operarios_datos_crudos:
            pdf.cell(130, 6, str(op), border=1)
            pdf.cell(60, 6, f"{hr} h", border=1, ln=1)

        # Convertir PDF a bytes para descarga
        pdf_output = pdf.output(dest='S').encode('latin1')

        # --- MODIFICAR EXCEL EN MEMORIA ---
        wb = openpyxl.load_workbook(archivo_subido)
        ws_base = wb["Base de Datos"]
        
        nueva_fila = [fecha, num_parte, obra, cliente, "", operarios_texto, materiales_texto, km, "No"]
        ws_base.append(nueva_fila)

        if "Historial_Horas" not in wb.sheetnames:
            ws_horas = wb.create_sheet(title="Historial_Horas")
            ws_horas.append(["Fecha", "Nº Parte", "Obra", "Nombre Operario", "Horas Trabajadas"])
        else:
            ws_horas = wb["Historial_Horas"]

        for nombre_op, horas_op in operarios_datos_crudos:
            ws_horas.append([fecha, num_parte, obra, nombre_op, horas_op])

        # Guardar cambios del Excel en un buffer de memoria
        excel_buffer = io.BytesIO()
        wb.save(excel_buffer)
        excel_buffer.seek(0)

        # --- MOSTRAR BOTONES DE DESCARGA ---
        st.success("¡Todo procesado con éxito en la nube! Descarga tus archivos aquí abajo:")
        
        st.download_button(
            label="📥 Descargar Parte en PDF",
            data=pdf_output,
            file_name=f"Parte_{num_parte}_{fecha}.pdf",
            mime="application/pdf"
        )
        
        st.download_button(
            label="📥 Descargar Excel Actualizado",
            data=excel_buffer,
            file_name="Plantilla_Parte_Obra_Profesional.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
else:
    st.info("Por favor, sube tu archivo Excel en la sección de arriba para comenzar a operar.")