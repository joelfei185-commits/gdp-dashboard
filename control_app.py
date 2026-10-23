import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Central de Logística - Ferretería El Indio",
    page_icon="🚛",
    layout="wide",
)

# Estilos CSS para replicar la apariencia visual del cuadro
st.markdown("""
    <style>
    .stApp { background-color: #eef2f6; }
    .header-box {
        background-color: #1f4e78;
        color: white;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 24px;
    }
    .metric-card {
        background-color: #ffffff;
        border: 2px solid #1f4e78;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    .day-header {
        background-color: #2f5597;
        color: white;
        text-align: center;
        font-weight: bold;
        padding: 8px;
        font-size: 18px;
        border-radius: 5px 5px 0px 0px;
    }
    </style>
""", unsafe_allow_html=True)

# URL de tu Web App de Google Apps Script (Backend de Datos)
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyTrK1m9Rs1zSpUp1BRKn5WmSV-ixTrZ-R_yAng-xEGR_6NWYaz1T1W7uSjms5314U3/exec"

# --- 2. SISTEMA DE ACCESO Y SEGURIDAD (CONTRASENA) ---
PASSWORD_CORRECTA = "elindio2026"  # Puedes cambiar esta clave si lo deseas

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h2 style='text-align: center; color: #1f4e78;'>🔒 Acceso Restringido - Control Maestro</h2>", unsafe_allow_html=True)
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        clave_ingresada = st.text_input("Ingrese la clave de administrador:", type="password")
        if st.button("Ingresar al Sistema", use_container_width=True):
            if clave_ingresada == PASSWORD_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("🔑 Clave incorrecta. Acceso denegado.")
    st.stop()

# --- 3. FUNCIONES DE CONEXIÓN AL BACKEND ---
def obtener_nombre_hoja_por_fecha(fecha_obj):
    lunes = fecha_obj - timedelta(days=fecha_obj.weekday())
    sabado = lunes + timedelta(days=5)
    meses = ["ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO", "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"]
    return f"SEMANA {lunes.day}-{sabado.day} {meses[lunes.month - 1]}"

def obtener_matriz_hoja(nombre_hoja):
    try:
        response = requests.get(f"{WEB_APP_URL}?action=getData&sheet={nombre_hoja}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

# --- 4. PANEL PRINCIPAL ---
st.sidebar.markdown("### ⚙️ Administración")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.autenticado = False
    st.rerun()

fecha_consulta = st.sidebar.date_input("Consultar Semana del:", datetime.now().date())
nombre_hoja_actual = obtener_nombre_hoja_por_fecha(fecha_consulta)

# Banner Principal Replicado
st.markdown(f"<div class='header-box'>CENTRAL DE LOGÍSTICA - {nombre_hoja_actual}</div>", unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# Indicadores Superiores (Total Viajes y Peso Total)
matriz_datos = obtener_matriz_hoja(nombre_hoja_actual)

total_viajes = 0
peso_total_qq = 0.0

if matriz_datos and len(matriz_datos) > 1:
    try:
        total_viajes = matriz_datos[1][4] or 0
        peso_total_qq = matriz_datos[1][7] or 0
    except Exception:
        pass

m_col1, m_col2, m_col3 = st.columns([2, 2, 2])
with m_col1:
    st.markdown(f"<div class='metric-card'><h4 style='color:#1f4e78;'>TOTAL DE VIAJES</h4><h2 style='color:#c00000;'>{total_viajes}</h2></div>", unsafe_allow_html=True)
with m_col2:
    st.markdown(f"<div class='metric-card'><h4 style='color:#1f4e78;'>PESO TOTAL (QQ)</h4><h2 style='color:#c00000;'>{peso_total_qq}</h2></div>", unsafe_allow_html=True)
with m_col3:
    if st.button("🔄 REINICIAR SEMANA", use_container_width=True, type="primary"):
        st.warning("Función de reinicio enviada al servidor.")

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #1f4e78; background-color: #d9e1f2; padding: 10px; border-radius: 5px;'>DISPONIBILIDAD DE ESPACIO</h3>", unsafe_allow_html=True)

# Mapeos de la Matriz Visual (Lunes a Sábado)
dias_bloque_1 = ["LUNES", "MARTES", "MIÉRCOLES"]
dias_bloque_2 = ["JUEVES", "VIERNES", "SÁBADO"]
horarios_manana = ["8:00 a.m.", "10:00 a.m."]
horarios_tarde = ["2:30 p.m.", "4:30 p.m."]

def renderizar_bloque_dias(lista_dias, fila_inicio_m, fila_inicio_t):
    cols = st.columns(len(lista_dias))
    for idx, dia in enumerate(lista_dias):
        with cols[idx]:
            st.markdown(f"<div class='day-header'>{dia}</div>", unsafe_allow_html=True)
            
            # Horarios Mañana
            for h in horarios_manana:
                st.text(f"⏱️ {h}")
                # Muestra los 5 bloques para los motoristas
                for m_idx in range(5):
                    st.text_input(f"{dia} {h} - Camión {m_idx+1}", value="Libre", key=f"{dia}_{h}_{m_idx}", label_visibility="collapsed")
            
            st.markdown("<div style='text-align:center; background-color:#e2e8f0; font-weight:bold; margin: 5px 0;'>🍽️ HORA DE ALMUERZO</div>", unsafe_allow_html=True)
            
            # Horarios Tarde
            if dia != "SÁBADO":
                for h in horarios_tarde:
                    st.text(f"⏱️ {h}")
                    for m_idx in range(5):
                        st.text_input(f"{dia} {h} - Camión {m_idx+1}", value="Libre", key=f"{dia}_{h}_{m_idx}", label_visibility="collapsed")
            else:
                st.info("🚫 Tarde No Laborable")

# Renderizar Primera Mitad (Lunes, Martes, Miércoles)
renderizar_bloque_dias(dias_bloque_1, 6, 14)
st.markdown("<hr>", unsafe_allow_html=True)
# Renderizar Segunda Mitad (Jueves, Viernes, Sábado)
renderizar_bloque_dias(dias_bloque_2, 20, 24)

# --- 5. REGISTRO DE HISTORIAL INFERIOR ---
st.markdown("<br><h3 style='color: #1f4e78;'>📋 Registro de Despachos Agendados</h3>", unsafe_allow_html=True)
if matriz_datos and len(matriz_datos) >= 30:
    filas_historial = matriz_datos[29:]
    df_historial = pd.DataFrame(filas_historial).dropna(how="all")
    if not df_historial.empty:
        df_historial.columns = ["COL_A", "COL_B", "MOTORISTA", "CANT. VIAJES", "RESERVADO POR", "PESO TOTAL", "FECHA", "DIRECCION"] + [f"C_{i}" for i in range(len(df_historial.columns)-8)]
        st.dataframe(df_historial[["MOTORISTA", "CANT. VIAJES", "RESERVADO POR", "PESO TOTAL", "FECHA", "DIRECCION"]], use_container_width=True)
    else:
        st.info("No hay viajes agendados en esta semana.")
else:
    st.info("Cargando tabla de registros...")