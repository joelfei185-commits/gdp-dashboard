import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta
import math
from PIL import Image

# --- 1. CONFIGURACIÓN DE LA PÁGINA Y ESTILO VISUAL ---
st.set_page_config(
    page_title="Registro y Control - Ferretería El Indio",
    page_icon="🚛",
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
    .main-header {
        background-color: #1f4e78;
        color: white;
        padding: 12px;
        border-radius: 6px;
        text-align: center;
        font-weight: bold;
        font-size: 20px;
        margin-top: 25px;
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
        padding: 6px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #86efac;
        margin-bottom: 4px;
        font-size: 11px;
    }
    .status-busy {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 6px;
        border-radius: 4px;
        text-align: center;
        font-weight: bold;
        border: 1px solid #fca5a5;
        margin-bottom: 4px;
        font-size: 11px;
    }
    </style>
""", unsafe_allow_html=True)

# URL de tu Apps Script configurada
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyTrK1m9Rs1zSpUp1BRKn5WmSV-ixTrZ-R_yAng-xEGR_6NWYaz1T1W7uSjms5314U3/exec"

# --- 2. BARRA LATERAL ---
st.sidebar.markdown("<h2 style='text-align: center; color: #1f4e78;'>EL INDIO ®</h2>", unsafe_allow_html=True)
st.sidebar.markdown("---")
st.sidebar.markdown("### 🚛 Módulo de Registro")
st.sidebar.info("📅 **Sistema Automatizado**\n\nLos pedidos se enrutan de forma inteligente a su hoja semanal correspondiente.")

# --- 3. ENCABEZADO PRINCIPAL ---
try:
    logo_img = Image.open("logo.png")
    col_a, col_b, col_c = st.columns([2, 1, 2])
    with col_b:
        st.image(logo_img, width=200)
except Exception:
    pass

st.markdown("<h1 style='text-align: center; color: #1f4e78;'>REGISTRO Y CONTROL DE FLETES</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #64748b;'>Ingreso de materiales y asignación de despachos</p>", unsafe_allow_html=True)

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

@st.cache_data(ttl=30)
def obtener_materiales_desde_drive():
    try:
        response = requests.get(f"{WEB_APP_URL}?action=getMateriales", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return pd.DataFrame(data)
    except Exception:
        pass
    
    return pd.DataFrame({
        "MATERIAL": ["CEMENTO", "H. 3/8", "H. 1/4", "H. 1/2", "BLOCK 10", "SOLERA 10", "MITAD 10", "BLOCK 15", "SOLERA 15", "MITAD 15", "BLOCK 20", "SOLERA 20", "MITAD 20", "LADRILLO", "GRAVA", "ARENA", "DECOBLOCK"],
        "LBS": [93.5, 7.142857143, 3.333333333, 12.5, 20.0, 20.0, 10.0, 25.0, 25.0, 13.0, 30.0, 34.0, 16.0, 8.0, 40.0, 40.0, 88.0]
    })

df_materiales_base = obtener_materiales_desde_drive()

def actualizar_celda_hoja(celda, texto, color, nombre_hoja="Hoja1"):
    try:
        payload = {"action": "updateCell", "cell": celda, "text": texto, "color": color, "sheet": nombre_hoja}
        requests.post(WEB_APP_URL, json=payload, timeout=10)
    except Exception as e:
        st.error(f"Error al actualizar celda: {e}")

def agregar_fila_hoja(row_data, nombre_hoja="Hoja1"):
    try:
        payload = {"action": "appendRow", "row": row_data, "sheet": nombre_hoja}
        res = requests.post(WEB_APP_URL, json=payload, timeout=10)
        return res.json().get("row", 30)
    except Exception as e:
        st.error(f"Error al guardar registro: {e}")
        return 30

# Flota de motoristas
df_motoristas = pd.DataFrame({
    "MOTORISTA": ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS"],
    "CAPACIDAD (QUINTALES)": [100, 100, 50, 100, 100]
})

COLORES_MOTORISTAS = {
    "ELVIS": {"red": 1.0, "green": 0.92, "blue": 0.23},
    "LUIS PEREZ": {"red": 0.56, "green": 0.93, "blue": 0.56},
    "DIEGO": {"red": 0.68, "green": 0.85, "blue": 0.90},
    "ALVARO": {"red": 0.85, "green": 0.65, "blue": 1.0},
    "TOMAS": {"red": 1.0, "green": 0.75, "blue": 0.80}
}

mapa_dias_bloques = {
    "LUNES": [3, 4, 5, 6, 7], "MARTES": [8, 9, 10, 11, 12],
    "MIÉRCOLES": [13, 14, 15, 16, 17], "JUEVES": [18, 19, 20, 21, 22],
    "VIERNES": [23, 24, 25, 26, 27], "SÁBADO": [28, 29, 30, 31, 32]
}

mapa_filas_busqueda = {
    "8:00 a.m. (⭐ Viaje 1)_LUN_MIE": 6, "10:00 a.m. (⭐ Viaje 2)_LUN_MIE": 8,
    "2:30 p.m. (⭐ Viaje 3)_LUN_MIE": 14, "4:30 p.m. (⭐ Viaje 4)_LUN_MIE": 16,
    "8:00 a.m. (⭐ Viaje 1)_JUE_SAB": 20, "10:00 a.m. (⭐ Viaje 2)_JUE_SAB": 22,
    "2:30 p.m. (⭐ Viaje 3)_JUE_SAB": 24, "4:30 p.m. (⭐ Viaje 4)_JUE_SAB": 26
}

mapa_filas_vista = {
    ("LUNES", "8:00 a.m."): 6, ("LUNES", "10:00 a.m."): 8, ("LUNES", "2:30 p.m."): 14, ("LUNES", "4:30 p.m."): 16,
    ("MARTES", "8:00 a.m."): 6, ("MARTES", "10:00 a.m."): 8, ("MARTES", "2:30 p.m."): 14, ("MARTES", "4:30 p.m."): 16,
    ("MIÉRCOLES", "8:00 a.m."): 6, ("MIÉRCOLES", "10:00 a.m."): 8, ("MIÉRCOLES", "2:30 p.m."): 14, ("MIÉRCOLES", "4:30 p.m."): 16,
    ("JUEVES", "8:00 a.m."): 20, ("JUEVES", "10:00 a.m."): 22, ("JUEVES", "2:30 p.m."): 24, ("JUEVES", "4:30 p.m."): 26,
    ("VIERNES", "8:00 a.m."): 20, ("VIERNES", "10:00 a.m."): 22, ("VIERNES", "2:30 p.m."): 24, ("VIERNES", "4:30 p.m."): 26,
    ("SÁBADO", "8:00 a.m."): 20, ("SÁBADO", "10:00 a.m."): 22
}

HORARIOS_ESTRELLA = [
    "8:00 a.m. (⭐ Viaje 1)", "10:00 a.m. (⭐ Viaje 2)",
    "2:30 p.m. (⭐ Viaje 3)", "4:30 p.m. (⭐ Viaje 4)"
]

def obtener_clave_fila(hora_base, dia):
    return f"{hora_base}_LUN_MIE" if dia in ["LUNES", "MARTES", "MIÉRCOLES"] else f"{hora_base}_JUE_SAB"

def num_a_letra(num):
    letra = ""
    while num > 0:
        num, remainder = divmod(num - 1, 26)
        letra = chr(65 + remainder) + letra
    return letra

def es_reserva_real(val):
    if not val: return False
    val_str = str(val).strip()
    if val_str.lower() in ["none", "nan", "", "libre"]: return False
    val_upper = val_str.upper()
    motoristas_validos = ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS"]
    if any(mot in val_upper for mot in motoristas_validos) or "OCUPADO" in val_upper:
        return True
    return False

hoy = datetime.now()

if "form_reset" not in st.session_state:
    st.session_state.form_reset = False

if st.session_state.form_reset:
    st.session_state.reservado_por_input = ""
    st.session_state.direccion_input = ""
    for idx_m in range(len(df_materiales_base)):
        st.session_state[f"p1_{idx_m}"] = 0.0
        st.session_state[f"p2_{idx_m}"] = 0.0
    st.session_state.form_reset = False

dias_semana_map = {0: "LUNES", 1: "MARTES", 2: "MIÉRCOLES", 3: "JUEVES", 4: "VIERNES", 5: "SÁBADO"}
dias_inverso_map = {"LUNES": 0, "MARTES": 1, "MIÉRCOLES": 2, "JUEVES": 3, "VIERNES": 4, "SÁBADO": 5}
lunes_actual = hoy - timedelta(days=hoy.weekday())

if "fecha_seleccionada" not in st.session_state:
    st.session_state.fecha_seleccionada = hoy.date()

def actualizar_fecha_por_dia():
    dia = st.session_state.widget_dia_envio
    st.session_state.fecha_seleccionada = (lunes_actual + timedelta(days=dias_inverso_map.get(dia, 0))).date()

def actualizar_dia_por_fecha():
    nueva_fecha = st.session_state.widget_fecha_envio
    num_dia_semana = nueva_fecha.weekday()
    st.session_state.widget_dia_envio = dias_semana_map.get(num_dia_semana, "LUNES") if num_dia_semana <= 5 else "LUNES"


# ==========================================
# PARTE 1: FORMULARIO DE INGRESO Y RESERVA
# ==========================================
col1, col2 = st.columns(2)

with col1:
    st.markdown("### 📦 Ingreso de Materiales")
    cantidades_p1 = []
    for index, row in df_materiales_base.iterrows():
        key_p1 = f"p1_{index}"
        if key_p1 not in st.session_state: st.session_state[key_p1] = 0.0
        cant = st.number_input(f"{row['MATERIAL']} ({row['LBS']:.2f} lbs)", min_value=0.0, step=1.0, key=key_p1)
        cantidades_p1.append(cant)
    
    df_p1 = df_materiales_base.copy()
    df_p1["CANTIDAD"] = cantidades_p1
    df_p1["TOTAL QT"] = df_p1["CANTIDAD"] * df_p1["LBS"]

with col2:
    st.markdown("### 🚛 Resumen y Estado de Carga")
    motorista_seleccionado = st.selectbox("Seleccione Motorista", df_motoristas["MOTORISTA"])
    capacidad_quintales = float(df_motoristas[df_motoristas["MOTORISTA"] == motorista_seleccionado]["CAPACIDAD (QUINTALES)"].values[0])
    capacidad_en_libras = capacidad_quintales * 100

    peso_principal = df_p1["TOTAL QT"].sum()
    viajes_estimados = max(1, math.ceil(peso_principal / capacidad_en_libras)) if capacidad_en_libras > 0 and peso_principal > 0 else 1

    cantidades_p2 = [0.0] * len(df_materiales_base)
    if peso_principal > 0 and capacidad_en_libras > 0:
        with st.expander("➕ Añadir Materiales Extra / Rellenar Viaje"):
            st.selectbox("Elegir Viaje a Completar", [f"Viaje {i+1}" for i in range(viajes_estimados)])
            cantidades_p2 = []
            for index, row in df_materiales_base.iterrows():
                key_p2 = f"p2_{index}"
                if key_p2 not in st.session_state: st.session_state[key_p2] = 0.0
                cant_comp = st.number_input(f"Extra: {row['MATERIAL']}", min_value=0.0, step=1.0, key=key_p2)
                cantidades_p2.append(cant_comp)

    df_p2 = df_materiales_base.copy()
    df_p2["CANTIDAD"] = cantidades_p2
    df_p2["TOTAL QT"] = df_p2["CANTIDAD"] * df_p2["LBS"]

    df_total_general = df_p1.copy()
    df_total_general["CANTIDAD"] = df_p1["CANTIDAD"] + df_p2["CANTIDAD"]
    df_total_general["TOTAL QT"] = df_total_general["CANTIDAD"] * df_total_general["LBS"]

    peso_total_general = df_total_general["TOTAL QT"].sum()
    peso_total_quintales = peso_total_general / 100

    st.metric(label="Peso Total Acumulado", value=f"{peso_total_quintales:,.2f} qq", delta=f"{peso_total_general:,.2f} lbs")

    if peso_total_general > 0:
        st.info(f"🚚 **{motorista_seleccionado}** (Capacidad: {capacidad_quintales} qq) realizará la entrega en **{viajes_estimados} Viaje(s)**.")

st.markdown("---")
st.markdown("### 📅 Reserva de Espacio en el Calendario")

f_col1, f_col2 = st.columns(2)
with f_col1:
    fecha_registro = st.date_input("Fecha a Hacer el Viaje", key="widget_fecha_envio", on_change=actualizar_dia_por_fecha)
with f_col2:
    dia_envio = st.selectbox("Día de la semana", ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO"], key="widget_dia_envio", on_change=actualizar_fecha_por_dia)

nombre_hoja_actual = obtener_nombre_hoja_por_fecha(fecha_registro)
matriz_temp = obtener_matriz_hoja(nombre_hoja_actual)

with st.form("form_envio"):
    horarios_libres_opciones = []
    horarios_para_revisar = ["8:00 a.m. (⭐ Viaje 1)", "10:00 a.m. (⭐ Viaje 2)"] if dia_envio == "SÁBADO" else HORARIOS_ESTRELLA
    columnas_del_dia = mapa_dias_bloques.get(dia_envio, [])

    for hora_b in horarios_para_revisar:
        fila_meta_rev = mapa_filas_busqueda.get(obtener_clave_fila(hora_b, dia_envio), 0)
        row_idx_rev = fila_meta_rev - 1
        espacios_libres_en_hora = 0
        if matriz_temp and len(matriz_temp) > row_idx_rev:
            for c_num in columnas_del_dia:
                try:
                    val_celda = matriz_temp[row_idx_rev][c_num - 3]
                except IndexError:
                    val_celda = ""
                if not es_reserva_real(val_celda): espacios_libres_en_hora += 1
        else:
            espacios_libres_en_hora = 5

        if espacios_libres_en_hora > 0:
            horarios_libres_opciones.append(f"{hora_b} (Disponibles: {espacios_libres_en_hora}/5)")

    horario_seleccionado = st.selectbox("Seleccione Horario Disponible", horarios_libres_opciones) if horarios_libres_opciones else None
    if not horarios_libres_opciones: st.warning(f"⚠️ No hay horarios disponibles para el día {dia_envio}.")

    reservado_por = st.text_input("Nombre de Quien Reserva", key="reservado_por_input")
    direccion_envio = st.text_input("Dirección de Destino / Entrega", key="direccion_input")

    submitted = st.form_submit_button("🚀 Agendar Viajes y Guardar en el Sistema")

    if submitted:
        if peso_total_general == 0: st.warning("Debe seleccionar al menos un material.")
        elif not reservado_por.strip(): st.warning("Debe indicar el nombre de quien reserva.")
        elif not direccion_envio.strip(): st.warning("Debe indicar la dirección de destino.")
        elif not horario_seleccionado: st.error("⚠️ Debe seleccionar un horario válido.")
        else:
            try:
                matriz_datos = obtener_matriz_hoja(nombre_hoja_actual)
                columnas_dia = mapa_dias_bloques[dia_envio]
                hora_base_elegida = horario_seleccionado.split(" (Disponibles:")[0]
                idx_inicio = horarios_para_revisar.index(hora_base_elegida)
                
                horarios_a_reservar = [horarios_para_revisar[idx_inicio + i] for i in range(viajes_estimados)]
                espacios_totales_encontrados = []

                for hora_b in horarios_a_reservar:
                    fila_meta = mapa_filas_busqueda[obtener_clave_fila(hora_b, dia_envio)]
                    row_idx = fila_meta - 1
                    col_encontrada = None
                    for col_num in columnas_dia:
                        val = matriz_datos[row_idx][col_num - 3] if matriz_datos and len(matriz_datos) > row_idx else ""
                        if not es_reserva_real(val):
                            col_encontrada = col_num
                            break
                    if col_encontrada: espacios_totales_encontrados.append((col_encontrada, fila_meta, hora_b))

                if len(espacios_totales_encontrados) < viajes_estimados:
                    st.error("⚠️ Algunos de los horarios consecutivos seleccionados ya fueron ocupados.")
                else:
                    color_rgb = COLORES_MOTORISTAS.get(motorista_seleccionado, {"red": 1.0, "green": 0.92, "blue": 0.23})
                    for col_num, fila_meta, hora_b in espacios_totales_encontrados:
                        actualizar_celda_hoja(f"{num_a_letra(col_num)}{fila_meta}", f"{motorista_seleccionado} ({reservado_por}) - Ocupado", color_rgb, nombre_hoja_actual)

                    agregar_fila_hoja([
                        motorista_seleccionado, f"{viajes_estimados} Viajes", reservado_por,
                        f"{peso_total_quintales:,.2f} qq ({peso_total_general:,.2f} lbs)",
                        fecha_registro.strftime("%Y-%m-%d"), direccion_envio
                    ], nombre_hoja_actual)

                    st.session_state.form_reset = True
                    st.success(f"¡Se han agendado con éxito los {viajes_estimados} viajes en la hoja: {nombre_hoja_actual}!")
                    st.rerun()
            except Exception as e:
                st.error(f"Error al escribir en Google Drive: {e}")


# ==========================================
# PARTE 2: DASHBOARD DE DISPONIBILIDAD CONECTADO
# ==========================================
st.markdown(f"<div class='main-header'>ESTADO DE DISPONIBILIDAD — {nombre_hoja_actual}</div>", unsafe_allow_html=True)

# Pestañas por día con disponibilidad visual conectada a la matriz
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
                    if matriz_temp and len(matriz_temp) > fila_idx:
                        try:
                            val_celda = str(matriz_temp[fila_idx][col_num - 3])
                        except:
                            pass
                    
                    with cols_ui[c_idx]:
                        if es_reserva_real(val_celda):
                            st.markdown(f"<div class='status-busy'>Camión {c_idx+1}<br><small>{val_celda[:15]}</small></div>", unsafe_allow_html=True)
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
                        if matriz_temp and len(matriz_temp) > fila_idx:
                            try:
                                val_celda = str(matriz_temp[fila_idx][col_num - 3])
                            except:
                                pass
                        
                        with cols_ui[c_idx]:
                            if es_reserva_real(val_celda):
                                st.markdown(f"<div class='status-busy'>Camión {c_idx+1}<br><small>{val_celda[:15]}</small></div>", unsafe_allow_html=True)
                            else:
                                st.markdown(f"<div class='status-free'>Camión {c_idx+1}<br><small>Libre</small></div>", unsafe_allow_html=True)
            else:
                st.info("🚫 Tarde no laborable")
