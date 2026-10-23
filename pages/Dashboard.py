import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
from PIL import Image

# --- 1. CONFIGURACIÓN DEL PANEL DE CONTROL ---
st.set_page_config(
    page_title="Panel de Control - Ferretería El Indio",
    page_icon="📊",
    layout="wide",
)

st.markdown("""
    <style>
    .stApp {
        background-color: #f4f6f9;
    }
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }
    div.stMetric {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 15px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.02);
    }
    </style>
""", unsafe_allow_html=True)

# URL de tu Apps Script configurada
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyTrK1m9Rs1zSpUp1BRKn5WmSV-ixTrZ-R_yAng-xEGR_6NWYaz1T1W7uSjms5314U3/exec"

# --- 2. BARRA LATERAL DE NAVEGACIÓN ---
st.sidebar.markdown("<h2 style='text-align: center; color: #1f4e78;'>EL INDIO ®</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("### 📊 Panel de Supervisión")
seccion_dashboard = st.sidebar.radio(
    "Seleccione Vista",
    ["👀 Disponibilidad Semanal", "📋 Historial de Viajes", "📈 Resumen por Motorista"]
)

st.sidebar.markdown("---")
st.sidebar.info("🔒 **Modo Solo Lectura**\n\nEste panel es exclusivo para supervisión y control operativo.")

# --- 3. ENCABEZADO ---
st.markdown("<h1 style='text-align: center; color: #1f4e78;'>PANEL DE CONTROL LOGÍSTICO</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b;'>Monitoreo en tiempo real de fletes y disponibilidad de flota</p>", unsafe_allow_html=True)

# --- 4. FUNCIONES DE CONEXIÓN ---
def obtener_nombre_hoja_por_fecha(fecha_obj):
    lunes = fecha_obj - timedelta(days=fecha_obj.weekday())
    sabado = lunes + timedelta(days=5)
    meses = [
        "ENERO", "FEBRERO", "MARZO", "ABRIL", "MAYO", "JUNIO",
        "JULIO", "AGOSTO", "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE"
    ]
    return f"SEMANA {lunes.day}-{sabado.day} {meses[lunes.month - 1]}"

def obtener_matriz_hoja(nombre_hoja="Hoja1"):
    try:
        response = requests.get(f"{WEB_APP_URL}?action=getData&sheet={nombre_hoja}", timeout=10)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

# Mapeos y constantes
mapa_dias_bloques = {
    "LUNES": [3, 4, 5, 6, 7], "MARTES": [8, 9, 10, 11, 12],
    "MIÉRCOLES": [13, 14, 15, 16, 17], "JUEVES": [18, 19, 20, 21, 22],
    "VIERNES": [23, 24, 25, 26, 27], "SÁBADO": [28, 29, 30, 31, 32]
}

mapa_filas = {
    "8:00 a.m. (⭐ Viaje 1)_LUN_MIE": 6, "10:00 a.m. (⭐ Viaje 2)_LUN_MIE": 8,
    "2:30 p.m. (⭐ Viaje 3)_LUN_MIE": 14, "4:30 p.m. (⭐ Viaje 4)_LUN_MIE": 16,
    "8:00 a.m. (⭐ Viaje 1)_JUE_SAB": 20, "10:00 a.m. (⭐ Viaje 2)_JUE_SAB": 22,
    "2:30 p.m. (⭐ Viaje 3)_JUE_SAB": 24, "4:30 p.m. (⭐ Viaje 4)_JUE_SAB": 26
}

HORARIOS_ESTRELLA = [
    "8:00 a.m. (⭐ Viaje 1)", "10:00 a.m. (⭐ Viaje 2)",
    "2:30 p.m. (⭐ Viaje 3)", "4:30 p.m. (⭐ Viaje 4)"
]

def obtener_clave_fila(hora_base, dia):
    return f"{hora_base}_LUN_MIE" if dia in ["LUNES", "MARTES", "MIÉRCOLES"] else f"{hora_base}_JUE_SAB"

def es_reserva_real(val):
    if not val: return False
    val_str = str(val).strip()
    if val_str.lower() in ["none", "nan", ""]: return False
    val_upper = val_str.upper()
    if any(h in val_upper for h in ["8:00 A.M.", "10:00 A.M.", "2:30 P.M.", "4:30 P.M.", "ALMUERZO"]):
        if not any(mot in val_upper for mot in ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS"]):
            return False
    return any(mot in val_upper for mot in ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS", "OCUPADO"])

# --- 5. LÓGICA DE LAS VISTAS DEL DASHBOARD ---
hoy = datetime.now()
fecha_filtro = st.date_input("Seleccionar Fecha para Consultar Semana", hoy.date())
nombre_hoja_actual = obtener_nombre_hoja_por_fecha(fecha_filtro)

st.markdown(f"### 📅 Visualizando Semana: `{nombre_hoja_actual}`")

if seccion_dashboard == "👀 Disponibilidad Semanal":
    try:
        matriz_datos = obtener_matriz_hoja(nombre_hoja_actual)
        datos_calendario = []
        for hora_etiqueta in HORARIOS_ESTRELLA:
            fila_actual = {"HORA": hora_etiqueta}
            for dia, cols in mapa_dias_bloques.items():
                clave_f = obtener_clave_fila(hora_etiqueta, dia)
                r_num = mapa_filas[clave_f]
                r_idx = r_num - 1
                ocupaciones, libres_count = [], 0
                for c_num in cols:
                    c_idx = c_num - 3
                    val = matriz_datos[r_idx][c_idx] if matriz_datos and len(matriz_datos) > r_idx else ""
                    if dia == "SÁBADO" and hora_etiqueta in ["2:30 p.m. (⭐ Viaje 3)", "4:30 p.m. (⭐ Viaje 4)"]:
                        fila_actual[dia] = "🚫 No laborable"
                        continue
                    if not es_reserva_real(val):
                        libres_count += 1
                    else:
                        ocupaciones.append(str(val).split(" - ")[0])
                
                if dia != "SÁBADO" or hora_etiqueta not in ["2:30 p.m. (⭐ Viaje 3)", "4:30 p.m. (⭐ Viaje 4)"]:
                    if libres_count == len(cols): fila_actual[dia] = "🟢 Todo Libre (5)"
                    elif libres_count == 0: fila_actual[dia] = f"🔴 Ocupado ({', '.join(ocupaciones)})"
                    else: fila_actual[dia] = f"🟡 {libres_count} Libres | Ocup: {', '.join(ocupaciones)}"
            datos_calendario.append(fila_actual)

        st.dataframe(pd.DataFrame(datos_calendario), hide_index=True, use_container_width=True)
    except Exception as e:
        st.warning(f"No se pudo cargar el cuadro de disponibilidad: {e}")

elif seccion_dashboard == "📋 Historial de Viajes":
    st.markdown("### 📋 Registro de Envíos de la Semana")
    st.info("Aquí puedes consultar los fletes agendados en esta hoja semanal de Google Drive.")
    try:
        matriz_datos = obtener_matriz_hoja(nombre_hoja_actual)
        if len(matriz_datos) >= 30:
            filas_registros = matriz_datos[29:] # A partir de la fila 30
            lista_limpia = []
            for fila in filas_registros:
                if any(fila): # Si la fila no está vacía
                    lista_limpia.append({
                        "MOTORISTA": fila[2] if len(fila) > 2 else "",
                        "VIAJES": fila[3] if len(fila) > 3 else "",
                        "RESERVADO POR": fila[4] if len(fila) > 4 else "",
                        "PESO TOTAL": fila[5] if len(fila) > 5 else "",
                        "FECHA": fila[6] if len(fila) > 6 else "",
                        "DIRECCION": fila[7] if len(fila) > 7 else ""
                    })
            if lista_limpia:
                st.dataframe(pd.DataFrame(lista_limpia), use_container_width=True)
            else:
                st.write("No hay registros guardados todavía en esta semana.")
        else:
            st.write("No se encontraron registros en la tabla inferior de la hoja.")
    except Exception as e:
        st.warning(f"Error al cargar el historial: {e}")

elif seccion_dashboard == "📈 Resumen por Motorista":
    st.markdown("### 📈 Estado de la Flota")
    st.metric("Motoristas Activos", "5 Operativos", "Elvis, Luis Pérez, Diego, Álvaro, Tomás")
    st.write("Próximamente métricas detalladas y gráficos de carga por cada camión.")
