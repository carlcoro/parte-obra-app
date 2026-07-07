import streamlit as st
import pandas as pd
from fpdf import FPDF
import io
import datetime
import os

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

# Comprobamos si eres el administrador
es_admin = (password_input == CONTRASENA_CORRECTA)

if es_admin:
    st.sidebar.success("🔓 Modo Administrador Activo")
    
    # BOTÓN PARA RESETEAR / BORRAR HISTORIAL
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚨 Peligro: Limpieza")
    if st.sidebar.button("🗑️ Borrar todo el Historial (Resetear app)"):
        if os.path.exists(HISTORIAL_CSV):
            os.remove(HISTORIAL_CSV)
        if os.path.exists(HISTORIAL_HORAS_CSV):
            os.remove(HISTORIAL_HORAS_CSV)
        st.sidebar.warning("¡Historial reseteado por completo! Las pruebas han sido eliminadas.")
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
    """Reemplaza caracteres conflictivos y símbolos como el € para evitar errores en FPDF"""
    if not texto:
        return ""
    reemplazos = {
        'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u',
        'Á': 'A', 'É': 'E', 'Í': 'I', 'Ó': 'O', 'Ú': 'U',
        'ñ': 'n', 'Ñ': 'N', 'ü': 'u', 'Ü': 'U',
        '€': 'Euros'
    }
    t = str(texto)
    for orig, dest in reemplazos.items():
        t = t.replace(orig, dest)
    return t

def generar_pdf_generico(num_p, fec, ob, cli, jf, ubi, kilometros, trabs, ops_texto, mats_texto):
    """Función auxiliar para reconstruir el PDF con los datos guardados"""
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

    # Personal Asignado (Texto unificado)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(25, 110, 30)
    pdf.cell(190, 7, "PERSONAL ASIGNADO")
    pdf.ln(7)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(190, 6, limpiar_texto_pdf(ops_texto) if ops_texto else "No se registro personal", border=1)
    pdf.ln(10)

    # Materiales (Texto unificado)
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
    pdf.ln(6)

    # Firmas
    pdf.ln(15)
    pos_y = pdf.get_y()
    pdf.line(20, pos_y + 15, 80, pos_y + 15)
    pdf.line(130, pos_y + 15, 190, pos_y + 15)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_y(pos_y + 16)
    pdf.cell(95, 5, "Firma del Cliente", align="C")
    pdf.cell(95, 5, "Firma del Jefe de Obra", align="C")

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

# ==========================================
# 3. LÓGICA DE PROCESAMIENTO AL PULSAR BOTÓN
# ==========================================
if st.button("🚀 Registrar Parte y Guardar en el Historial"):
    
    # --- PROCESAR OPERARIOS Y MATERIALES ---
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

    # --- GENERAR PDF ---
    pdf_output = generar_pdf_generico(
        num_parte, fecha, obra, cliente, jefe_obra, ubicacion, km, trabajos, operarios_texto, materiales_texto
    )

    # --- GUARDAR EN HISTORIAL LOCAL (CSV) ---
    nueva_fila_base = pd.DataFrame([{
        "Fecha": fecha, "Nº Parte": num_parte, "Obra": obra, "Cliente": cliente,
        "Jefe de Obra": jefe_obra, "Ubicación": ubicacion, "Trabajos": trabajos,
        "Operarios": operarios_texto, "Materiales": materiales_texto,
        "Km": km, "Procesado": "No"
    }])
    if os.path.exists(HISTORIAL_CSV):
        df_base_existente = pd.read_csv(HISTORIAL_CSV)
        df_base_final = pd.concat([df_base_existente, nueva_fila_base], ignore_index=True)
    else:
        df_base_final = nueva_fila_base
    df_base_final.to_csv(HISTORIAL_CSV, index=False)

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

    # --- BOTÓN DE DESCARGA ---
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
        
        # --- NUEVA FUNCIÓN: RECUPERAR / DESCARGAR CUALQUIER PDF ---
        st.markdown("#### 📄 Recuperar PDF desde el Historial")
        opciones_partes = df_ver_base.apply(lambda row: f"Parte Nº {row['Nº Parte']} - Obra: {row['Obra']} ({row['Fecha']})", axis=1).tolist()
        
        parte_seleccionado_str = st.selectbox("Selecciona el parte que quieres descargar en PDF:", opciones_partes)
        
        if parte_seleccionado_str:
            # Obtener el índice seleccionado
            idx = opciones_partes.index(parte_seleccionado_str)
            fila_p = df_ver_base.iloc[idx]
            
            # Reconstruir el PDF con los datos guardados en esa fila
            pdf_historial_bytes = generar_pdf_generico(
                str(fila_p.get("Nº Parte", "")),
                str(fila_p.get("Fecha", "")),
                str(fila_p.get("Obra", "")),
                str(fila_p.get("Cliente", "")),
                str(fila_p.get("Jefe de Obra", "")),
                str(fila_p.get("Ubicación", "")),
                int(fila_p.get("Km", 0)),
                str(fila_p.get("Trabajos", "")),
                str(fila_p.get("Operarios", "")),
                str(fila_p.get("Materiales", ""))
            )
            
            st.download_button(
                label=f"📥 Descargar PDF del Parte Nº {fila_p['Nº Parte']}",
                data=pdf_historial_bytes,
                file_name=f"Parte_{fila_p['Nº Parte']}_{fila_p['Fecha']}.pdf",
                mime="application/pdf",
                key="btn_descarga_historial"
            )
        
        st.markdown("---")
        # Generar descarga del Excel completo
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
        st.info("El historial está vacío actualmente. Listo para usar mañana.")
