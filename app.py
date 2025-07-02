import streamlit as st
import pandas as pd
import tempfile
import os
from CuadroFacturacionGenerator import CuadroFacturacionGenerator

st.set_page_config(page_title="Generador de Cuadro de Facturación", layout="centered")

st.title("🧾 Generador de Cuadro de Facturación")
st.markdown("Sube el archivo de Excel con el conglomerado y descarga el archivo procesado.")

uploaded_file = st.file_uploader("📤 Cargar archivo Excel (.xlsx)", type=["xlsx"])

if uploaded_file:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as temp_input:
        temp_input.write(uploaded_file.read())
        temp_input_path = temp_input.name

    temp_output_path = temp_input_path.replace(".xlsx", "_GENERADO.xlsx")

    try:
        with st.spinner("⏳ Generando el archivo, por favor espera..."):
            generador = CuadroFacturacionGenerator()
            generador.generar(temp_input_path, temp_output_path)

        with open(temp_output_path, "rb") as f:
            st.success("✅ Archivo generado exitosamente.")
            st.download_button(
                label="📥 Descargar archivo generado",
                data=f,
                file_name="CUADRO_FACTURACION_GENERADO.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    except Exception as e:
        st.error(f"❌ Ocurrió un error al procesar el archivo: {e}")
    finally:
        os.remove(temp_input_path)
        if os.path.exists(temp_output_path):
            os.remove(temp_output_path)
