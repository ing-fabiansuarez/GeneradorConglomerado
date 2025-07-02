import pandas as pd
from collections import defaultdict
from datetime import datetime
import locale

class CuadroFacturacionGenerator:
  

    def _formatear_fechas(self, fechas):
        fechas_ordenadas = sorted(fechas, key=lambda x: datetime.strptime(x, "%Y-%m-%d"))
        fechas_dict = defaultdict(list)

        meses_es = {
            "January": "enero", "February": "febrero", "March": "marzo",
            "April": "abril", "May": "mayo", "June": "junio",
            "July": "julio", "August": "agosto", "September": "septiembre",
            "October": "octubre", "November": "noviembre", "December": "diciembre"
        }

        for fecha in fechas_ordenadas:
            dt = datetime.strptime(fecha, "%Y-%m-%d")
            mes = dt.strftime("%B")
            dia = str(dt.day)
            fechas_dict[mes].append(dia)

        fechas_formateadas = []
        for mes, dias in fechas_dict.items():
            mes_es = meses_es.get(mes, mes)
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

    def generar_filtrado_por_profesional(self, conglomerado_path, output_path, nombre_profesional):
        df = pd.read_excel(conglomerado_path, sheet_name="CONGLOMERADO", engine="openpyxl")

        # Filtrar por el nombre del profesional
        df = df[df["NOMBRE DEL PROFESIONAL"] == nombre_profesional]

        if df.empty:
            raise ValueError(f"No se encontraron registros para el profesional: {nombre_profesional}")

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

    def generar_filtrado_por_profesional(self, conglomerado_path, output_path, nombres_profesionales: list):
        df = pd.read_excel(conglomerado_path, sheet_name="CONGLOMERADO", engine="openpyxl")

        # ✅ Filtra los registros por la lista de nombres seleccionados
        df = df[df["NOMBRE DEL PROFESIONAL"].isin(nombres_profesionales)]

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
