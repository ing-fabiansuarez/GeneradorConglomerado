import pandas as pd
from collections import defaultdict
from datetime import datetime
import locale

class CuadroFacturacionGenerator:
    def __init__(self):
        self._configurar_locale()

    def _configurar_locale(self):
        # Establecer idioma español para los nombres de los meses
        try:
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')  # Para Linux/macOS
        except locale.Error:
            locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')  # Para Windows

    def _formatear_fechas(self, fechas):
        fechas_ordenadas = sorted(fechas, key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
        fechas_dict = defaultdict(list)
        
        for fecha in fechas_ordenadas:
            dt = datetime.strptime(fecha, "%Y-%m-%d")
            mes = dt.strftime("%B")  # Nombre del mes en inglés
            dia = str(dt.day)
            fechas_dict[mes].append(dia)
        
        fechas_formateadas = []
        for mes, dias in fechas_dict.items():
            mes_es = datetime.strptime(mes, "%B").strftime("%B").capitalize()
            fechas_formateadas.append(f"{', '.join(dias)} {mes_es}")
        
        return ", ".join(fechas_formateadas)

    def generar(self, conglomerado_path, output_path):
        df = pd.read_excel(conglomerado_path, sheet_name="CONGLOMERADO", engine="openpyxl")
        
        df_filtered = df[[
            "DOC PROFESIONAL", "NOMBRE DEL PROFESIONAL", "Tipo de nota",
            "Documento", "NOMBRE USUARIO", "FECHA INI AUT", "FECHA FINAL", "AUT", "FECHA ATENCION"
        ]]
        
        sesiones_dict = defaultdict(lambda: {"count": 0, "fechas": []})
        
        for _, row in df_filtered.iterrows():
            clave = (
                row["DOC PROFESIONAL"], row["NOMBRE DEL PROFESIONAL"], row["Tipo de nota"],
                row["Documento"], row["NOMBRE USUARIO"], row["AUT"], row["FECHA INI AUT"],
                row["FECHA FINAL"]
            )
            sesiones_dict[clave]["count"] += 1
            sesiones_dict[clave]["fechas"].append(row["FECHA ATENCION"].date().isoformat())
        
        datos_expandidos = []
        for clave, valores in sesiones_dict.items():
            doc_profesional, nombre_profesional, tipo_nota, documento, nombre_usuario, autorizacion, fecha_ini_aut, fecha_final = clave
            fechas_atencion = self._formatear_fechas(valores["fechas"])
            
            fila = [
                doc_profesional, nombre_profesional, tipo_nota,
                nombre_usuario, documento,
                autorizacion, fecha_ini_aut, fecha_final,
                valores["count"], fechas_atencion
            ]
            datos_expandidos.append(fila)
        
        df_grouped = pd.DataFrame(datos_expandidos, columns=[
            "DOC PROFESIONAL", "NOMBRE DEL PROFESIONAL", "Tipo de nota",
            "NOMBRE USUARIO", "Documento", "AUT", "FECHA INI AUT", "FECHA FINAL", 
            "NO de sesiones", "Fechas de atención DIAS Y MESES"
        ])
        
        df_grouped.rename(columns={
            "DOC PROFESIONAL": "CC Profesional",
            "NOMBRE DEL PROFESIONAL": "Nombre completo de profesional",
            "Tipo de nota": "Area",
            "Documento": "Doc Usuario",
            "NOMBRE USUARIO": "Nombre completo de Usuario",
            "FECHA INI AUT": "Fecha Inicial",
            "FECHA FINAL": "Fecha Final",
            "AUT": "No Autorización",
        }, inplace=True)
        
        df_grouped.insert(0, "TIPO CONTRATO (OPS O NOMINA)", "Nomina")
        df_grouped.insert(7, "SES AUTOR", "")
        df_grouped.insert(11, "AUTOR", "")
        df_grouped.insert(12, "GLOSAS", "")
        df_grouped.insert(13, "RECONOCE LA EMPRESA", "")
        
        df_grouped["Valor"] = df_grouped["NO de sesiones"] * 4500
        df_grouped["Fecha Inicial"] = ""
        df_grouped["Fecha Final"] = ""
        
        df_grouped.to_excel(output_path, sheet_name="CUADRO SESIONES REALIZADAS", index=False, engine="openpyxl")
