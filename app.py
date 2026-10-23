import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Control Maestro - Ferretería El Indio",
    page_icon="👔",
    layout="wide",
)

st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .main-header {
        background-color: #1f4e78;
        color: white;
        padding: 12px;
        border-radius: 6px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        margin-bottom: 15px;
    }
    .metric-box {
        background-color: #ffffff;
        border: 1px solid #cbd5e1;
        border-radius: 6px;
        padding: 12px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
    }
    .time-slot {
        background-color: #e2e8f0;
        padding: 6px;
        font-weight: bold;
        color: #1e293b;
        border-radius: 4px;
        margin-top: 10px;
        margin-bottom: 5px;
        text-align: center;
    }
    .status-free {
        background-color: #dcfce7;
        color: #166534;
        padding: 8px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #86efac;
        margin-bottom: 4px;
        font-size: 11px;
    }
    </style>
""", unsafe_allow_html=True)

WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyTrK1m9Rs1zSpUp1BRKn5WmSV-ixTrZ-R_yAng-xEGR_6NWYaz1T1W7uSjms5314U3/exec"

# --- 2. ACCESO Y SEGURIDAD ---
PASSWORD_CORRECTA = "elindio2026"

if "autenticado" not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    st.markdown("<h3 style='text-align: center; color: #1f4e78; margin-top: 50px;'>🔒 Control Maestro - Acceso Restringido</h3>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.5, 1])
    with col2:
        clave = st.text_input("Contraseña de administrador:", type="password")
        if st.button("Ingresar", use_container_width=True, type="primary"):
            if clave == PASSWORD_CORRECTA:
                st.session_state.autenticado = True
                st.rerun()
            else:
                st.error("Clave incorrecta.")
    st.stop()

# --- 3. FUNCIONES DE APOYO ---
def obtener_nombre_hoja(fecha_obj):
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

def num_a_letra(num):
    letra = ""
    while num > 0:
        num, remainder = divmod(num - 1, 26)
        letra = chr(65 + remainder) + letra
    return letra

mapa_dias_bloques = {
    "LUNES": [3, 4, 5, 6, 7], "MARTES": [8, 9, 10, 11, 12],
    "MIÉRCOLES": [13, 14, 15, 16, 17], "JUEVES": [18, 19, 20, 21, 22],
    "VIERNES": [23, 24, 25, 26, 27], "SÁBADO": [28, 29, 30, 31, 32]
}

mapa_filas_vista = {
    ("LUNES", "8:00 a.m."): 6, ("LUNES", "10:00 a.m."): 8, ("LUNES", "2:30 p.m."): 14, ("LUNES", "4:30 p.m."): 16,
    ("MARTES", "8:00 a.m."): 6, ("MARTES", "10:00 a.m."): 8, ("MARTES", "2:30 p.m."): 14, ("MARTES", "4:30 p.m."): 16,
    ("MIÉRCOLES", "8:00 a.m."): 6, ("MIÉRCOLES", "10:00 a.m."): 8, ("MIÉRCOLES", "2:30 p.m."): 14, ("MIÉRCOLES", "4:30 p.m."): 16,
    ("JUEVES", "8:00 a.m."): 20, ("JUEVES", "10:00 a.m."): 22, ("JUEVES", "2:30 p.m."): 24, ("JUEVES", "4:30 p.m."): 26,
    ("VIERNES", "8:00 a.m."): 20, ("VIERNES", "10:00 a.m."): 22, ("VIERNES", "2:30 p.m."): 24, ("VIERNES", "4:30 p.m."): 26,
    ("SÁBADO", "8:00 a.m."): 20, ("SÁBADO", "10:00 a.m."): 22
}

def es_reserva_real(val):
    if not val: return False
    val_str = str(val).strip()
    if val_str.lower() in ["none", "nan", "", "libre"]: return False
    val_upper = val_str.upper()
    motoristas_validos = ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS"]
    if any(mot in val_upper for mot in motoristas_validos) or "OCUPADO" in val_upper:
        return True
    return False

# --- 4. BARRA LATERAL Y CONTROLES ---
st.sidebar.markdown("### ⚙️ Panel de Control")
fecha_consulta = st.sidebar.date_input("Semana a Consultar:", datetime.now().date())
nombre_hoja = obtener_nombre_hoja(fecha_consulta)

st.sidebar.markdown("---")

matriz_datos = obtener_matriz_hoja(nombre_hoja)

# Filtrado estricto de fletes reales para la tabla inferior
df_historial = pd.DataFrame()
if matriz_datos and len(matriz_datos) >= 30:
    filas_raw = matriz_datos[29:]
    filas_validas = []
    for idx_f, fila in enumerate(filas_raw):
        if len(fila) >= 6 and str(fila[2]).strip() != "" and str(fila[2]).upper() not in ["MOTORISTA", "NONE", "NAN"]:
            filas_validas.append([idx_f + 30] + list(fila)) # Guardamos el número de fila real
    
    if filas_validas:
        df_historial = pd.DataFrame(filas_validas)
        df_historial.columns = ["NUM_FILA", "COL_A", "COL_B", "MOTORISTA", "CANT. VIAJES", "RESERVADO POR", "PESO TOTAL", "FECHA", "DIRECCION"] + [f"C_{i}" for i in range(len(df_historial.columns)-9)]

total_viajes = len(df_historial) if not df_historial.empty else 0
peso_total_qq = 0.0

if not df_historial.empty:
    for val in df_historial["PESO TOTAL"]:
        try:
            num_str = str(val).split("qq")[0].strip().replace(",", "")
            peso_total_qq += float(num_str)
        except:
            pass

# Botón de Reiniciar Semana Completa
if st.sidebar.button("🔄 Reiniciar Semana Completa", use_container_width=True, type="primary"):
    try:
        with st.spinner("Reiniciando semana en el servidor..."):
            response = requests.get(f"{WEB_APP_URL}?action=reset&sheet={nombre_hoja}", timeout=15)
            if response.status_code == 200:
                st.sidebar.success(f"¡La {nombre_hoja} ha sido reiniciada!")
                st.rerun()
            else:
                st.sidebar.error("No se pudo conectar con el servidor.")
    except Exception as e:
        st.sidebar.error(f"Error: {e}")

if st.sidebar.button("🚪 Cerrar Sesión", use_container_width=True):
    st.session_state.autenticado = False
    st.rerun()

# --- 5. PANEL PRINCIPAL ---
st.markdown(f"<div class='main-header'>CENTRAL DE LOGÍSTICA — {nombre_hoja}</div>", unsafe_allow_html=True)

# Tarjetas métricas
col_m1, col_m2 = st.columns(2)
with col_m1:
    st.markdown(f"<div class='metric-box'><span style='color: #64748b; font-size: 13px; font-weight: bold;'>TOTAL DE VIAJES</span><h2 style='color: #1f4e78; margin: 0;'>{total_viajes}</h2></div>", unsafe_allow_html=True)
with col_m2:
    st.markdown(f"<div class='metric-box'><span style='color: #64748b; font-size: 13px; font-weight: bold;'>PESO TOTAL (QQ)</span><h2 style='color: #b91c1c; margin: 0;'>{peso_total_qq:.2f}</h2></div>", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# --- 6. CUADRO VISUAL DE DISPONIBILIDAD CON BOTONES DE ELIMINAR EN CASILLAS ---
st.markdown("#### 📅 Disponibilidad de Espacio por Día")

dias = ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO"]
tabs = st.tabs([f"📌 {d}" for d in dias])

for idx_dia, tab in enumerate(tabs):
    nombre_dia = dias[idx_dia]
    with tab:
        st.caption(f"Horarios y cupos para el día **{nombre_dia}**")
        
        col_m, col_t = st.columns(2)
        columnas_dia = mapa_dias_bloques.get(nombre_dia, [])
        
        with col_m:
            st.markdown("##### 🌅 Mañana")
            for h in ["8:00 a.m.", "10:00 a.m."]:
                st.markdown(f"<div class='time-slot'>⏱️ {h}</div>", unsafe_allow_html=True)
                fila_idx = mapa_filas_vista.get((nombre_dia, h), 0) - 1
                
                c1, c2, c3, c4, c5 = st.columns(5)
                cols_ui = [c1, c2, c3, c4, c5]
                
                for c_idx, col_num in enumerate(columnas_dia):
                    val_celda = ""
                    if matriz_datos and len(matriz_datos) > fila_idx:
                        try:
                            val_celda = str(matriz_datos[fila_idx][col_num - 3])
                        except:
                            pass
                    
                    with cols_ui[c_idx]:
                        if es_reserva_real(val_celda):
                            # Casilla Ocupada con botón directo de eliminar
                            st.markdown(f"<div style='background-color: #fee2e2; color: #991b1b; padding: 4px; border-radius: 4px; text-align: center; font-size: 10px; font-weight: bold;'>Camión {c_idx+1}<br>{val_celda[:12]}</div>", unsafe_allow_html=True)
                            celda_letra = num_a_letra(col_num)
                            coord_celda = f"{celda_letra}{fila_idx + 1}"
                            if st.button("🗑️ Borrar", key=f"del_{nombre_hoja}_{coord_celda}", use_container_width=True):
                                try:
                                    # Limpiamos la celda en la matriz horaria
                                    requests.post(WEB_APP_URL, json={"action": "updateCell", "cell": coord_celda, "text": "", "color": {"red": 1, "green": 1, "blue": 1}, "sheet": nombre_hoja}, timeout=10)
                                    st.success("¡Viaje liberado!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Error: {e}")
                        else:
                            st.markdown(f"<div class='status-free'>Camión {c_idx+1}<br><small>Libre</small></div>", unsafe_allow_html=True)

        with col_t:
            st.markdown("##### 🌆 Tarde")
            if nombre_dia != "SÁBADO":
                for h in ["2:30 p.m.", "4:30 p.m."]:
                    st.markdown(f"<div class='time-slot'>⏱️ {h}</div>", unsafe_allow_html=True)
                    fila_idx = mapa_filas_vista.get((nombre_dia, h), 0) - 1
                    
                    c1, c2, c3, c4, c5 = st.columns(5)
                    cols_ui = [c1, c2, c3, c4, c5]
                    
                    for c_idx, col_num in enumerate(columnas_dia):
                        val_celda = ""
                        if matriz_datos and len(matriz_datos) > fila_idx:
                            try:
                                val_celda = str(matriz_datos[fila_idx][col_num - 3])
                            except:
                                pass
                        
                        with cols_ui[c_idx]:
                            if es_reserva_real(val_celda):
                                st.markdown(f"<div style='background-color: #fee2e2; color: #991b1b; padding: 4px; border-radius: 4px; text-align: center; font-size: 10px; font-weight: bold;'>Camión {c_idx+1}<br>{val_celda[:12]}</div>", unsafe_allow_html=True)
                                celda_letra = num_a_letra(col_num)
                                coord_celda = f"{celda_letra}{fila_idx + 1}"
                                if st.button("🗑️ Borrar", key=f"del_{nombre_hoja}_{coord_celda}", use_container_width=True):
                                    try:
                                        requests.post(WEB_APP_URL, json={"action": "updateCell", "cell": coord_celda, "text": "", "color": {"red": 1, "green": 1, "blue": 1}, "sheet": nombre_hoja}, timeout=10)
                                        st.success("¡Viaje liberado!")
                                        st.rerun()
                                    except Exception as e:
                                        st.error(f"Error: {e}")
                            else:
                                st.markdown(f"<div class='status-free'>Camión {c_idx+1}<br><small>Libre</small></div>", unsafe_allow_html=True)
            else:
                st.info("🚫 Tarde no laborable")

st.markdown("<br><hr>", unsafe_allow_html=True)

# --- 7. TABLA DE REGISTROS DE DESPACHO ABAJO ---
st.markdown("#### 📋 Despachos Agendados en la Semana")

if not df_historial.empty:
    # Mostramos la tabla sin la columna interna NUM_FILA
    st.dataframe(
        df_historial[["MOTORISTA", "CANT. VIAJES", "RESERVADO POR", "PESO TOTAL", "FECHA", "DIRECCION"]], 
        use_container_width=True,
        hide_index=True
    )
else:
    st.info("No hay fletes agendados aún para esta semana.")
