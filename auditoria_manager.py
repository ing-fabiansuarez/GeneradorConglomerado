"""
Sistema de Auditoría para registro de descargas y cargas de archivos
Maneja toda la lógica de conexión con Supabase y captura de información del usuario
"""

import streamlit as st
from datetime import datetime
from supabase import create_client, Client
import socket
import platform
import os 
from dotenv import load_dotenv

# ===========================
# CONFIGURACIÓN DE SUPABASE
# ===========================

# Cargar variables de entorno desde archivo .env
load_dotenv()

# Intentar obtener credenciales desde múltiples fuentes
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Si no están en .env, intentar con Streamlit secrets (solo en deployment)
if not SUPABASE_URL or not SUPABASE_KEY:
    try:
        SUPABASE_URL = st.secrets["SUPABASE_URL"]
        SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
    except (KeyError, FileNotFoundError, AttributeError):
        # No hay secrets configurados, esto es normal en desarrollo local
        pass

# Validar que existan las credenciales
if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ No se encontraron credenciales de Supabase. Sistema de auditoría deshabilitado.")
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
        print("✅ Conexión con Supabase establecida")
    except Exception as e:
        print(f"❌ Error al conectar con Supabase: {e}")
        supabase = None


# ===========================
# FUNCIONES DE CAPTURA DE INFO
# ===========================

def obtener_info_usuario():
    """
    Recopila información detallada del usuario y sistema
    
    Returns:
        dict: Diccionario con toda la información capturada
    """
    try:
        # Información básica del navegador
        user_agent = st.context.headers.get("User-Agent", "Desconocido")
        
        # Intentar obtener IP real del usuario
        # Streamlit Cloud usa headers especiales para IP real
        ip_address = (
            st.context.headers.get("X-Forwarded-For", "").split(",")[0].strip() or
            st.context.headers.get("X-Real-Ip", "") or
            st.context.headers.get("Remote-Addr", "") or
            "127.0.0.1"
        )
        
        # Información del servidor/host
        hostname = socket.gethostname()
        
        # Información adicional del sistema
        platform_info = platform.system()
        
        return {
            "ip_address": ip_address,
            "user_agent": user_agent,
            "hostname": hostname,
            "platform": platform_info,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        return {
            "ip_address": "Error al obtener IP",
            "user_agent": "Error",
            "hostname": "Error",
            "platform": "Error",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


def obtener_session_id():
    """
    Obtiene o genera un ID único de sesión
    
    Returns:
        str: ID único de la sesión actual
    """
    if "session_id" not in st.session_state:
        st.session_state.session_id = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return st.session_state.session_id


# ===========================
# FUNCIONES DE REGISTRO
# ===========================

def registrar_descarga(nombre_profesional, nombre_archivo, info_adicional=None):
    """
    Registra cada descarga en la base de datos de Supabase
    
    Args:
        nombre_profesional (str): Nombre del profesional seleccionado
        nombre_archivo (str): Nombre del archivo generado
        info_adicional (dict, optional): Información adicional a registrar
    
    Returns:
        tuple: (bool: éxito, str: mensaje)
    """
    if supabase is None:
        return False, "Sistema de auditoría no disponible"
    
    try:
        info_usuario = obtener_info_usuario()
        
        registro = {
            "profesional_nombre": nombre_profesional,
            "archivo_generado": nombre_archivo,
            "ip_address": info_usuario["ip_address"],
            "user_agent": info_usuario["user_agent"],
            "hostname": info_usuario["hostname"],
            "platform": info_usuario["platform"],
            "fecha_descarga": info_usuario["timestamp"],
            "sesion_id": obtener_session_id(),
            "info_adicional": info_adicional or {}
        }
        
        # Insertar en Supabase
        response = supabase.table("descargas_auditoria").insert(registro).execute()
        
        return True, "Registro exitoso"
    except Exception as e:
        return False, f"Error al registrar: {str(e)}"


def registrar_carga_archivo(nombre_archivo_original, num_profesionales, nombres_profesionales):
    """
    Registra cuando se carga un archivo Excel en la aplicación
    
    Args:
        nombre_archivo_original (str): Nombre del archivo cargado
        num_profesionales (int): Cantidad de profesionales encontrados
        nombres_profesionales (list): Lista con nombres de todos los profesionales
    
    Returns:
        bool: True si el registro fue exitoso, False si hubo error
    """
    if supabase is None:
        return False
    
    try:
        info_usuario = obtener_info_usuario()
        
        registro = {
            "archivo_cargado": nombre_archivo_original,
            "num_profesionales": num_profesionales,
            "lista_profesionales": nombres_profesionales,
            "ip_address": info_usuario["ip_address"],
            "user_agent": info_usuario["user_agent"],
            "fecha_carga": info_usuario["timestamp"],
            "sesion_id": obtener_session_id()
        }
        
        supabase.table("cargas_archivos").insert(registro).execute()
        return True
    except Exception as e:
        print(f"Error al registrar carga de archivo: {str(e)}")
        return False


# ===========================
# FUNCIONES DE CONSULTA
# ===========================

def obtener_historial_descargas(limite=100):
    """
    Obtiene el historial de descargas desde Supabase
    
    Args:
        limite (int): Número máximo de registros a obtener
    
    Returns:
        list: Lista de registros de descargas
    """
    if supabase is None:
        return []
    
    try:
        response = supabase.table("descargas_auditoria")\
            .select("*")\
            .order("fecha_descarga", desc=True)\
            .limit(limite)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Error al obtener historial: {str(e)}")
        return []


def obtener_descargas_por_profesional(nombre_profesional):
    """
    Obtiene todas las descargas de un profesional específico
    
    Args:
        nombre_profesional (str): Nombre del profesional
    
    Returns:
        list: Lista de descargas del profesional
    """
    if supabase is None:
        return []
    
    try:
        response = supabase.table("descargas_auditoria")\
            .select("*")\
            .eq("profesional_nombre", nombre_profesional)\
            .order("fecha_descarga", desc=True)\
            .execute()
        return response.data
    except Exception as e:
        print(f"Error al consultar descargas: {str(e)}")
        return []


def obtener_estadisticas_descargas():
    """
    Obtiene estadísticas generales de descargas
    
    Returns:
        dict: Diccionario con estadísticas
    """
    if supabase is None:
        return {"total": 0, "profesionales_unicos": 0, "ips_unicas": 0}
    
    try:
        # Total de descargas
        response_total = supabase.table("descargas_auditoria")\
            .select("*", count="exact")\
            .execute()
        
        total = response_total.count if response_total.count else 0
        
        # Obtener datos para contar únicos
        response_data = supabase.table("descargas_auditoria")\
            .select("profesional_nombre, ip_address")\
            .execute()
        
        if response_data.data:
            profesionales_unicos = len(set(r["profesional_nombre"] for r in response_data.data))
            ips_unicas = len(set(r["ip_address"] for r in response_data.data))
        else:
            profesionales_unicos = 0
            ips_unicas = 0
        
        return {
            "total": total,
            "profesionales_unicos": profesionales_unicos,
            "ips_unicas": ips_unicas
        }
    except Exception as e:
        print(f"Error al obtener estadísticas: {str(e)}")
        return {"total": 0, "profesionales_unicos": 0, "ips_unicas": 0}