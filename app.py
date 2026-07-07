import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import datetime
import os
from streamlit_drawable_canvas import st_canvas
import cv2
import numpy as np

# ==========================================
# 1. CONFIGURACIÓN E INTERFAZ DE STREAMLIT
# ==========================================
st.set_page_config(page_title="Gestor de Partes de Obra", layout="wide")
st.title("🚧 Sistema de Gestión de Partes de Obra")

# Archivos de almacenamiento en el servidor
HISTORIAL_CSV = "historial_partes_obra.csv"
HISTORIAL_HORAS_CSV = "historial_horas_operarios.csv"

# --- ZONA DE SEGURIDAD (BARRA LATERAL) ---
st.sidebar.header("🔑 Zona de Administración")
CONTRASENA_CORRECTA = "admin123" 
password_input = st.sidebar.text_input("Introduce contraseña para ver historial", type="password")

es_admin = (password_input == CONTRASENA_CORRECTA)

if es_admin:
    st.sidebar.success("🔓 Modo Administrador Activo")
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚨 Peligro: Limpieza")
    if st.sidebar.button("🗑️ Borrar todo el Historial (Resetear app)"):
        if os.path.exists(HISTORIAL_CSV):
            os.remove(HISTORIAL_CSV)
        if os.path.exists(HISTORIAL_HORAS_CSV):
            os.remove(HISTORIAL_HORAS_CSV)
        st.sidebar.warning("¡Historial reseteado por completo!")
        st.rerun()

# Diccionario global de unificación de nombres
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

def limpiar_texto_pdf(texto):
    if not texto:
        return ""
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U', '€': 'Euros'
    }
    t = str(texto)
    for orig, dest in reemplazos.items():
        t = t.replace(orig, dest)
    return t

def generar_pdf_generico(num_p, fec, ob, cli, jf, ubi, kilometros, trabs, ops_texto, mats_texto, firma_nombre="", firma_dni="", firma_bytes=None):
    """Función para construir el PDF incluyendo datos de firma si existen"""
    class PDFParte(FPDF):
        def header(self):
            self.set_font("Helvetica", "B", 14)
            self.set_text_color(46, 125, 50)
            self.cell(190, 10, "PARTE DIARIO DE TRABAJO", border=1, align="C")
            self.ln(15)

    pdf = PDFParte(orientation="P", unit="mm", format="A4")
    pdf.add_page()
    pdf.set_font("Helvetica", "", 10)

    # Bloque Información General
    pdf.set_fill_color(232, 245, 233)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 7, "Nº Parte:", border=1, fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(65, 7, limpiar_texto_pdf(num_p), border=1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 7, "Fecha:", border=1, fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(65, 7, limpiar_texto_pdf(fec), border=1)
    pdf.ln(7)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 7, "Obra:", border=1, fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(65, 7, limpiar_texto_pdf(ob), border=1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 7, "Jefe de Obra:", border=1, fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(65, 7, limpiar_texto_pdf(jf), border=1)
    pdf.ln(7)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 7, "Ubicacion:", border=1, fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(65, 7, limpiar_texto_pdf(ubi), border=1)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(30, 7, "Cliente:", border=1, fill=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(65, 7, limpiar_texto_pdf(cli), border=1)
    pdf.ln(12)

    # Trabajos
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(25, 110, 30)
    pdf.cell(190, 7, "TRABAJOS REALIZADOS")
    pdf.ln(7)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 6, limpiar_texto_pdf(trabs) if trabs else "Ninguno", border=1)
    pdf.ln(10)

    # Personal Asignado
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(25, 110, 30)
    pdf.cell(190, 7, "PERSONAL ASIGNADO")
    pdf.ln(7)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 6, limpiar_texto_pdf(ops_texto) if ops_texto else "No se registro personal", border=1)
    pdf.ln(10)

    # Materiales
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(25, 110, 30)
    pdf.cell(190, 7, "MATERIALES UTILIZADOS")
    pdf.ln(7)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 6, limpiar_texto_pdf(mats_texto) if mats_texto else "No se registraron materiales", border=1)
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(190, 6, f"Kilometros realizados: {kilometros} km")
    pdf.ln(10)

    # --- SECCIÓN DE FIRMA EN EL PDF ---
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(25, 110, 30)
    pdf.cell(190, 7, "CONFORMIDAD Y FIRMA")
    pdf.ln(7)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    
    texto_firmante = f"Firmante: {firma_nombre if firma_nombre else 'No especificado'} | DNI: {firma_dni if firma_dni else 'No especificado'}"
    pdf.cell(190, 6, limpiar_texto_pdf(texto_firmante), ln=True)
    
    if firma_bytes is not None:
        # Insertar la firma dibujada directamente en el PDF
        pdf.image(io.BytesIO(firma_bytes), x=20, y=pdf.get_y() + 2, w=60)
        pdf.ln(25)
    else:
        pdf.set_font("Helvetica", "I", 10)
        pdf.cell(190, 8, "[Parte guardado sin firma digital]", ln=True)
        pdf.ln(5)

    return bytes(pdf.output())

# ==========================================
# 2. FORMULARIO DE ENTRADA DE DATOS (WEB)
# ==========================================
col1, col2, col3 = st.columns(3)
with col1:
    num_parte = st.text_input("Nº Parte", value="1001")
    obra = st.text_input("Obra", value="Sin Obra")
    cliente = st.text_input("Cliente", value="")
with col2:
    fecha_dt = st.date_input("Fecha", datetime.date.today())
    fecha = fecha_dt.strftime("%d-%m-%Y")
    jefe_obra = st.text_input("Jefe de Obra", value="")
with col3:
    ubicacion = st.text_input("Ubicación", value="")
    km = st.number_input("Kilómetros realizados", min_value=0, value=0)

trabajos = st.text_area("Trabajos Realizados", value="")

st.subheader("👥 Personal Asignado")
df_operarios = st.data_editor(pd.DataFrame([{"Operario": "", "Horas": 0.0}]), num_rows="dynamic", key="tabla_operarios")

st.subheader("📦 Materiales Utilizados")
df_materiales = st.data_editor(pd.DataFrame([{"Material": "", "Cantidad": 0.0, "Unidad": "uds"}]), num_rows="dynamic", key="tabla_materiales")

# --- NUEVA ZONA: FIRMA DIGITAL EN PANTALLA ---
st.markdown("---")
st.subheader("✍️ Firma Digital de Conformidad (Opcional)")
col_f1, col_f2 = st.columns(2)
with col_f1:
    nombre_firmante = st.text_input("Nombre y Apellidos de quien firma")
    dni_firmante = st.text_input("DNI / NIE")
with col_f2:
    st.write("Firma con el dedo o ratón dentro del recuadro:")
    canvas_result = st_canvas(
        fill_color="rgba(255, 255, 255, 0)",
        stroke_width=3,
        stroke_color="#000000",
        background_color="#FFFFFF",
        height=120,
        width=300,
        drawing_mode="freedraw",
        key="canvas",
    )

# ==========================================
# 3. LÓGICA DE PROCESAMIENTO AL PULSAR BOTÓN
# ==========================================
if st.button("🚀 Registrar Parte y Guardar en el Historial"):
    
    # Procesar Operarios y Materiales
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

    # Procesar la firma digital si se ha dibujado algo
    firma_png_bytes = None
    if canvas_result.image_data is not None:
        # Verificar si realmente el usuario dibujó algo (no es un lienzo en blanco)
        img = canvas_result.image_data
        if np.any(img[:, :, 3] > 0): # Si hay algún píxel dibujado
            # Convertir a formato adecuado para el PDF
            import cv2
            alpha_channel = img[:, :, 3]
            rgb_img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            _, encoded_img = cv2.imencode(".png", rgb_img)
            firma_png_bytes = encoded_img.tobytes()

    # Generar PDF incluyendo los datos y bytes de la firma
    pdf_output = generar_pdf_generico(
        num_parte, fecha, obra, cliente, jefe_obra, ubicacion, km, trabajos, 
        operarios_texto, materiales_texto, nombre_firmante, dni_firmante, firma_png_bytes
    )

    # Guardar en Historial Local CSV
    nueva_fila_base = pd.DataFrame([{
        "Fecha": fecha, "Nº Parte": num_parte, "Obra": obra, "Cliente": cliente,
        "Jefe de Obra": jefe_obra, "Ubicación": ubicacion, "Trabajos": trabajos,
        "Operarios": operarios_texto, "Materiales": materiales_texto, "Km": km,
        "Firmante": nombre_firmante if nombre_firmante else "Sin firma",
        "DNI Firmante": dni_firmante if dni_firmante else "Sin DNI",
        "Procesado": "No"
    }])
    
    if os.path.exists(HISTORIAL_CSV):
        df_base_existente = pd.read_csv(HISTORIAL_CSV)
        df_base_final = pd.concat([df_base_existente, nueva_fila_base], ignore_index=True)
    else:
        df_base_final = nueva_fila_base
    df_base_final.to_csv(HISTORIAL_CSV, index=False)

    # Guardar Horas Operarios
    nuevas_filas_horas = []
    for nombre_op, horas_op in operarios_datos_crudos:
        nuevas_filas_horas.append({
            "Fecha": fecha, "Nº Parte": num_parte, "Obra": obra,
            "Nombre Operario": nombre_op, "Horas Trabajadas": horas_op
        })
    if nuevas_filas_horas:
        df_nuevas_horas = pd.DataFrame(nuevas_filas_horas)
        if os.path.exists(HISTORIAL_HORAS_CSV):
            df_horas_existente = pd.read_csv(HISTORIAL_HORAS_CSV)
            df_horas_final = pd.concat([df_horas_existente, df_nuevas_horas], ignore_index=True)
        else:
            df_horas_final = df_nuevas_horas
        df_horas_final.to_csv(HISTORIAL_HORAS_CSV, index=False)

    st.success("✅ ¡Parte registrado con éxito!")

    st.download_button(
        label="📥 Descargar Este Parte en PDF",
        data=pdf_output,
        file_name=f"Parte_{num_parte}_{fecha}.pdf",
        mime="application/pdf"
    )

# ==========================================
# 4. VISTA DEL HISTORIAL (SOLO ADMIN)
# ==========================================
if es_admin:
    st.markdown("---")
    st.subheader("📊 Panel de Control e Historial Completo (Modo Admin)")
    
    if os.path.exists(HISTORIAL_CSV):
        df_ver_base = pd.read_csv(HISTORIAL_CSV)
        st.dataframe(df_ver_base, use_container_width=True)
        
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            df_ver_base.to_excel(writer, sheet_name="Base de Datos", index=False)
            if os.path.exists(HISTORIAL_HORAS_CSV):
                df_ver_horas = pd.read_csv(HISTORIAL_HORAS_CSV)
                df_ver_horas.to_excel(writer, sheet_name="Historial_Horas", index=False)
                
        st.download_button(
            label="📥 Descargar Historial Completo en Excel (.xlsx)",
            data=excel_buffer.getvalue(),
            file_name="Historial_General_Partes.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("El historial está vacío actualmente.")
