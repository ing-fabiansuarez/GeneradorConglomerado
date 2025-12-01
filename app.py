import streamlit as st
import pandas as pd
import tempfile
import os
from CuadroFacturacionGenerator import CuadroFacturacionGenerator
import auditoria_manager

st.set_page_config(page_title="Generador de Cuadro de Facturación", layout="centered")

st.title("🧾 Generador de Cuadro de Facturación")
st.markdown("Sube el archivo de Excel con el conglomerado, selecciona un profesional y descarga el archivo generado.")

uploaded_file = st.file_uploader("📤 Cargar archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_input:
        temp_input.write(uploaded_file.read())
        temp_input_path = temp_input.name

    try:
        df_preview = pd.read_excel(temp_input_path, sheet_name="CONGLOMERADO", engine="openpyxl")
        nombres_profesionales = sorted(df_preview["NOMBRE DEL PROFESIONAL"].dropna().unique())

        #Registrar carga del archivo
        auditoria_manager.registrar_carga_archivo(
            uploaded_file.name,
            len(nombres_profesionales),
            nombres_profesionales
        )

        nombre_seleccionado = st.selectbox("👤 Selecciona el profesional:", nombres_profesionales)

        if nombre_seleccionado and st.button("🚀 Generar archivo"):
            generador = CuadroFacturacionGenerator()

            with st.spinner("⏳ Generando archivo, por favor espera..."):
                temp_output = tempfile.NamedTemporaryFile(delete=False, suffix=f"_{nombre_seleccionado.replace(' ', '_')}.xlsx")
                temp_output_path = temp_output.name
                temp_output.close()

                generador.generar_filtrado_por_profesional(temp_input_path, temp_output_path, [nombre_seleccionado])

            # Registrar ANTES de mostrar el botón de descarga
            auditoria_manager.registrar_descarga(
                nombre_profesional=nombre_seleccionado,
                nombre_archivo="",
                info_adicional={
                    "archivo_origen": uploaded_file.name,
                    "num_registros": len(df_preview)
                }
            )
            st.success("✅ Archivo generado. Descárgalo a continuación:")

            with open(temp_output_path, "rb") as f:
                archivo_bytes = f.read()

                st.download_button(
                    label=f"📥 Descargar {nombre_seleccionado}",
                    data=f,
                    file_name=f"CUADRO_{nombre_seleccionado.replace(' ', '_')}.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key=f"download_{nombre_seleccionado}"
                )

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {e}")
    finally:
        os.remove(temp_input_path)
