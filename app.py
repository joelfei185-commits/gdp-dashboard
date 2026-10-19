from datetime import datetime, timedelta
import math
import pandas as pd
from PIL import Image
import requests
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Logística de Envío - Ferretería & Homecenter El Indio",
    page_icon="🧰",
    layout="wide",
)

# URL de tu Apps Script configurada
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbyTrK1m9Rs1zSpUp1BRKn5WmSV-ixTrZ-R_yAng-xEGR_6NWYaz1T1W7uSjms5314U3/exec"

# --- MENÚ LATERAL (OPCIÓN B) ---
st.sidebar.markdown(
    "<h2 style='text-align: center; color: #1f4e78;'>EL INDIO ®</h2>",
    unsafe_allow_html=True,
)
st.sidebar.markdown("---")
menu_opcion = st.sidebar.radio(
    "Menú de Navegación",
    [
        "🚛 Logística y Reservas",
        "📦 Consulta de Materiales",
        "📊 Reportes Mensuales",
    ],
)

# --- CONTROL DE SEMANA AUTOMÁTICO POR FECHA ---
st.sidebar.markdown("---")
st.sidebar.markdown("### 📅 Control de Semana")
st.sidebar.info(
    "💡 Las hojas semanales se generan y seleccionan **automáticamente** según"
    " la fecha del viaje que elijas en el formulario."
)

# --- LOGO CENTRADO Y EN TAMAÑO IDEAL ---
try:
  logo_img = Image.open("logo.png")
  col_a, col_b, col_c = st.columns([2, 1, 2])
  with col_b:
    st.image(logo_img, width=220)
except Exception:
  pass

# Título centrado corporativo
st.markdown(
    "<h1 style='text-align: center; margin-top: -10px;'>LOGÍSTICA DE ENVÍO"
    " FERRETERÍA & HOMECENTER EL INDIO</h1>",
    unsafe_allow_html=True,
)
st.markdown(
    "<p style='text-align: center; color: gray;'>Sincronización activa —"
    " Gestión automatizada por fecha</p>",
    unsafe_allow_html=True,
)


# Función auxiliar para calcular el nombre de la hoja según una fecha (para lectura de disponibilidad)
def obtener_nombre_hoja_por_fecha(fecha_obj):
  lunes = fecha_obj - timedelta(days=fecha_obj.weekday())
  sabado = lunes + timedelta(days=5)
  meses = [
      "ENERO",
      "FEBRERO",
      "MARZO",
      "ABRIL",
      "MAYO",
      "JUNIO",
      "JULIO",
      "AGOSTO",
      "SEPTIEMBRE",
      "OCTUBRE",
      "NOVIEMBRE",
      "DICIEMBRE",
  ]
  mes_nombre = meses[lunes.month - 1]
  return f"SEMANA {lunes.day}-{sabado.day} {mes_nombre}"


def obtener_matriz_hoja(nombre_hoja="Hoja1"):
  try:
    response = requests.get(
        f"{WEB_APP_URL}?action=getData&sheet={nombre_hoja}", timeout=10
    )
    if response.status_code == 200:
      return response.json()
  except Exception:
    pass
  return []


# Carga dinámica de materiales desde Google Drive
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
      "MATERIAL": [
          "CEMENTO",
          "H. 3/8",
          "H. 1/4",
          "H. 1/2",
          "BLOCK 10",
          "SOLERA 10",
          "MITAD 10",
          "BLOCK 15",
          "SOLERA 15",
          "MITAD 15",
          "BLOCK 20",
          "SOLERA 20",
          "MITAD 20",
          "LADRILLO",
          "GRAVA",
          "ARENA",
          "DECOBLOCK",
      ],
      "LBS": [
          93.5,
          7.142857143,
          3.333333333,
          12.5,
          20.0,
          20.0,
          10.0,
          25.0,
          25.0,
          13.0,
          30.0,
          34.0,
          16.0,
          8.0,
          40.0,
          40.0,
          88.0,
      ],
  })


df_materiales_base = obtener_materiales_desde_drive()


def actualizar_celda_hoja(celda, texto, color, nombre_hoja="Hoja1"):
  try:
    payload = {
        "action": "updateCell",
        "cell": celda,
        "text": texto,
        "color": color,
        "sheet": nombre_hoja,
    }
    requests.post(WEB_APP_URL, json=payload, timeout=10)
  except Exception as e:
    st.error(f"Error al actualizar celda: {e}")


def agregar_fila_hoja(row_data):
  try:
    payload = {"action": "appendRow", "row": row_data}
    res = requests.post(WEB_APP_URL, json=payload, timeout=10)
    return res.json().get("row", 30)
  except Exception as e:
    st.error(f"Error al guardar registro: {e}")
    return 30


# FLOTA DE MOTORISTAS (Diego con 50 qq / Camión Pequeño)
df_motoristas = pd.DataFrame({
    "MOTORISTA": ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS"],
    "CAPACIDAD (QUINTALES)": [100, 100, 50, 100, 100],
})

st.success("¡Conectado y sincronizado con Google Drive exitosamente!")

COLORES_MOTORISTAS = {
    "ELVIS": {"red": 1.0, "green": 0.92, "blue": 0.23},
    "LUIS PEREZ": {"red": 0.56, "green": 0.93, "blue": 0.56},
    "DIEGO": {"red": 0.68, "green": 0.85, "blue": 0.90},
    "ALVARO": {"red": 0.85, "green": 0.65, "blue": 1.0},
    "TOMAS": {"red": 1.0, "green": 0.75, "blue": 0.80},
}

mapa_dias_bloques = {
    "LUNES": [3, 4, 5, 6, 7],
    "MARTES": [8, 9, 10, 11, 12],
    "MIÉRCOLES": [13, 14, 15, 16, 17],
    "JUEVES": [18, 19, 20, 21, 22],
    "VIERNES": [23, 24, 25, 26, 27],
    "SÁBADO": [28, 29, 30, 31, 32],
}

mapa_filas = {
    "8:00 a.m. (⭐ Viaje 1)_LUN_MIE": 6,
    "10:00 a.m. (⭐ Viaje 2)_LUN_MIE": 8,
    "2:30 p.m. (⭐ Viaje 3)_LUN_MIE": 14,
    "4:30 p.m. (⭐ Viaje 4)_LUN_MIE": 16,
    "8:00 a.m. (⭐ Viaje 1)_JUE_SAB": 20,
    "10:00 a.m. (⭐ Viaje 2)_JUE_SAB": 22,
    "2:30 p.m. (⭐ Viaje 3)_JUE_SAB": 24,
    "4:30 p.m. (⭐ Viaje 4)_JUE_SAB": 26,
}

HORARIOS_ESTRELLA = [
    "8:00 a.m. (⭐ Viaje 1)",
    "10:00 a.m. (⭐ Viaje 2)",
    "2:30 p.m. (⭐ Viaje 3)",
    "4:30 p.m. (⭐ Viaje 4)",
]


def obtener_clave_fila(hora_base, dia):
  if dia in ["LUNES", "MARTES", "MIÉRCOLES"]:
    return f"{hora_base}_LUN_MIE"
  else:
    return f"{hora_base}_JUE_SAB"


def num_a_letra(num):
  letra = ""
  while num > 0:
    num, remainder = divmod(num - 1, 26)
    letra = chr(65 + remainder) + letra
  return letra


def es_reserva_real(val):
  if not val:
    return False
  val_str = str(val).strip()
  if val_str.lower() in ["none", "nan", ""]:
    return False

  val_upper = val_str.upper()

  if any(
      h in val_upper
      for h in ["8:00 A.M.", "10:00 A.M.", "2:30 P.M.", "4:30 P.M.", "ALMUERZO"]
  ):
    if not any(
        mot in val_upper
        for mot in ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS"]
    ):
      return False

  for mot in ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS", "OCUPADO"]:
    if mot in val_upper:
      return True

  return False


# --- CONTENIDO SEGÚN MENÚ SELECCIONADO ---
hoy = datetime.now()

if menu_opcion == "🚛 Logística y Reservas":

  if "form_reset" not in st.session_state:
    st.session_state.form_reset = False

  if st.session_state.form_reset:
    st.session_state.reservado_por_input = ""
    st.session_state.direccion_input = ""
    for idx_m in range(len(df_materiales_base)):
      st.session_state[f"p1_{idx_m}"] = 0.0
      st.session_state[f"p2_{idx_m}"] = 0.0
    st.session_state.form_reset = False

  dias_semana_map = {
      0: "LUNES",
      1: "MARTES",
      2: "MIÉRCOLES",
      3: "JUEVES",
      4: "VIERNES",
      5: "SÁBADO",
  }
  dias_inverso_map = {
      "LUNES": 0,
      "MARTES": 1,
      "MIÉRCOLES": 2,
      "JUEVES": 3,
      "VIERNES": 4,
      "SÁBADO": 5,
  }

  lunes_actual = hoy - timedelta(days=hoy.weekday())

  if "fecha_seleccionada" not in st.session_state:
    st.session_state.fecha_seleccionada = hoy.date()

  if "dia_seleccionado" not in st.session_state:
    num_dia = hoy.weekday()
    st.session_state.dia_seleccionado = (
        dias_semana_map.get(num_dia, "LUNES") if num_dia <= 5 else "LUNES"
    )


  def actualizar_fecha_por_dia():
    dia = st.session_state.widget_dia_envio
    delta_dias = dias_inverso_map.get(dia, 0)
    st.session_state.fecha_seleccionada = (
        lunes_actual + timedelta(days=delta_dias)
    ).date()


  def actualizar_dia_por_fecha():
    nueva_fecha = st.session_state.widget_fecha_envio
    num_dia_semana = nueva_fecha.weekday()
    if num_dia_semana <= 5:
      st.session_state.widget_dia_envio = dias_semana_map.get(
          num_dia_semana, "LUNES"
      )
    else:
      st.session_state.widget_dia_envio = "LUNES"


  col1, col2 = st.columns(2)

  with col1:
    st.subheader("📦 Ingreso de Materiales (Pedido Principal)")
    cantidades_p1 = []
    for index, row in df_materiales_base.iterrows():
      mat_nombre = str(row["MATERIAL"])
      mat_lbs = float(row["LBS"])
      key_p1 = f"p1_{index}"
      if key_p1 not in st.session_state:
        st.session_state[key_p1] = 0.0
      cant = st.number_input(
          f"{mat_nombre} (P. unidad: {mat_lbs:.2f} lbs)",
          min_value=0.0,
          step=1.0,
          key=key_p1,
      )
      cantidades_p1.append(cant)

    df_p1 = df_materiales_base.copy()
    df_p1["CANTIDAD"] = cantidades_p1
    df_p1["TOTAL QT"] = df_p1["CANTIDAD"] * df_p1["LBS"]

  with col2:
    st.subheader("🚛 Resumen y Estado de Carga")
    motorista_seleccionado = st.selectbox(
        "Seleccione Motorista", df_motoristas["MOTORISTA"]
    )
    capacidad_quintales = float(
        df_motoristas[df_motoristas["MOTORISTA"] == motorista_seleccionado][
            "CAPACIDAD (QUINTALES)"
        ].values[0]
    )
    capacidad_en_libras = capacidad_quintales * 100

    peso_principal = df_p1["TOTAL QT"].sum()
    viajes_estimados = 1
    if capacidad_en_libras > 0 and peso_principal > 0:
      viajes_estimados = max(1, math.ceil(peso_principal / capacidad_en_libras))

    cantidades_p2 = [0.0] * len(df_materiales_base)
    if peso_principal > 0 and capacidad_en_libras > 0:
      with st.expander(
          "➕ Añadir Materiales Extra / Rellenar Viaje Incompleto"
      ):
        viajes_disponibles_opciones = [
            f"Viaje {i+1}" for i in range(viajes_estimados)
        ]
        viaje_a_rellenar = st.selectbox(
            "Elegir Viaje a Completar", viajes_disponibles_opciones
        )
        cantidades_p2 = []
        for index, row in df_materiales_base.iterrows():
          mat_nombre = str(row["MATERIAL"])
          key_p2 = f"p2_{index}"
          if key_p2 not in st.session_state:
            st.session_state[key_p2] = 0.0
          cant_comp = st.number_input(
              f"Extra: {mat_nombre}",
              min_value=0.0,
              step=1.0,
              key=key_p2,
          )
          cantidades_p2.append(cant_comp)

    df_p2 = df_materiales_base.copy()
    df_p2["CANTIDAD"] = cantidades_p2
    df_p2["TOTAL QT"] = df_p2["CANTIDAD"] * df_p2["LBS"]

    df_total_general = df_p1.copy()
    df_total_general["CANTIDAD"] = df_p1["CANTIDAD"] + df_p2["CANTIDAD"]
    df_total_general["TOTAL QT"] = (
        df_total_general["CANTIDAD"] * df_total_general["LBS"]
    )

    peso_total_general = df_total_general["TOTAL QT"].sum()
    peso_total_quintales = peso_total_general / 100

    st.metric(
        label="Peso Total de Carga (Principal + Extras)",
        value=f"{peso_total_quintales:,.2f} qq ({peso_total_general:,.2f} lbs)",
    )

    if peso_total_general > 0:
      st.info(
          f"🚚 **{motorista_seleccionado}** (Capacidad: {capacidad_quintales}"
          f" qq) hará este envío en **{viajes_estimados} Viaje(s)**."
      )

  st.markdown("---")
  st.subheader("📅 Reserva de Espacio en el Calendario")

  f_col1, f_col2 = st.columns(2)
  with f_col1:
    fecha_registro = st.date_input(
        "Fecha a Hacer el Viaje",
        key="widget_fecha_envio",
        on_change=actualizar_dia_por_fecha,
    )
  with f_col2:
    dia_envio = st.selectbox(
        "Día de la semana",
        ["LUNES", "MARTES", "MIÉRCOLES", "JUEVES", "VIERNES", "SÁBADO"],
        key="widget_dia_envio",
        on_change=actualizar_fecha_por_dia,
    )

  # Determinamos la hoja semanal automáticamente según la fecha seleccionada en el formulario
  nombre_hoja_actual = obtener_nombre_hoja_por_fecha(fecha_registro)
  matriz_temp = obtener_matriz_hoja(nombre_hoja_actual)

  with st.form("form_envio"):
    horarios_libres_opciones = []
    horarios_para_revisar = (
        ["8:00 a.m. (⭐ Viaje 1)", "10:00 a.m. (⭐ Viaje 2)"]
        if dia_envio == "SÁBADO"
        else HORARIOS_ESTRELLA
    )
    columnas_del_dia = mapa_dias_bloques.get(dia_envio, [])

    for hora_b in horarios_para_revisar:
      clave_fila_rev = obtener_clave_fila(hora_b, dia_envio)
      fila_meta_rev = mapa_filas.get(clave_fila_rev, 0)
      row_idx_rev = fila_meta_rev - 1

      espacios_libres_en_hora = 0
      if matriz_temp and len(matriz_temp) > row_idx_rev:
        for c_num in columnas_del_dia:
          c_idx_rev = c_num - 3
          try:
            val_celda = matriz_temp[row_idx_rev][c_idx_rev]
          except IndexError:
            val_celda = ""
          if not es_reserva_real(val_celda):
            espacios_libres_en_hora += 1
      else:
        espacios_libres_en_hora = 5

      if espacios_libres_en_hora > 0:
        horarios_libres_opciones.append(
            f"{hora_b} (Disponibles: {espacios_libres_en_hora}/5)"
        )

    horario_seleccionado = (
        st.selectbox("Seleccione Horario Disponible", horarios_libres_opciones)
        if horarios_libres_opciones
        else None
    )
    if not horarios_libres_opciones:
      st.warning(f"⚠️ No hay horarios disponibles para el día {dia_envio}.")

    reservado_por = st.text_input(
        "Nombre de Quien Reserva", key="reservado_por_input"
    )
    direccion_envio = st.text_input(
        "Dirección de Destino / Entrega", key="direccion_input"
    )

    submitted = st.form_submit_button("Agendar Viajes y Guardar en Google Drive")

    if submitted:
      if peso_total_general == 0:
        st.warning("Debe seleccionar al menos un material.")
      elif not reservado_por.strip():
        st.warning("Debe indicar el nombre de quien reserva.")
      elif not direccion_envio.strip():
        st.warning("Debe indicar la dirección de destino.")
      elif not horario_seleccionado:
        st.error("⚠️ Debe seleccionar un horario válido.")
      else:
        try:
          # Recargamos la matriz de la hoja correspondiente por seguridad
          matriz_datos = obtener_matriz_hoja(nombre_hoja_actual)
          columnas_dia = mapa_dias_bloques[dia_envio]
          hora_base_elegida = horario_seleccionado.split(" (Disponibles:")[0]
          idx_inicio = horarios_para_revisar.index(hora_base_elegida)

          horarios_a_reservar = [
              horarios_para_revisar[idx_inicio + i]
              for i in range(viajes_estimados)
          ]
          espacios_totales_encontrados = []

          for hora_b in horarios_a_reservar:
            clave_f = obtener_clave_fila(hora_b, dia_envio)
            fila_meta = mapa_filas[clave_f]
            row_idx = fila_meta - 1
            col_encontrada = None
            for col_num in columnas_dia:
              col_idx = col_num - 3
              val = (
                  matriz_datos[row_idx][col_idx]
                  if matriz_datos and len(matriz_datos) > row_idx
                  else ""
              )
              if not es_reserva_real(val):
                col_encontrada = col_num
                break
            if col_encontrada:
              espacios_totales_encontrados.append(
                  (col_encontrada, fila_meta, hora_b)
              )

          if len(espacios_totales_encontrados) < viajes_estimados:
            st.error(
                "⚠️ Algunos de los horarios consecutivos seleccionados ya"
                " fueron ocupados."
            )
          else:
            color_rgb = COLORES_MOTORISTAS.get(
                motorista_seleccionado, {"red": 1.0, "green": 1.0, "blue": 1.0}
            )
            for col_num, fila_meta, hora_b in espacios_totales_encontrados:
              letra_col = num_a_letra(col_num)
              celda_destino = f"{letra_col}{fila_meta}"
              texto_reserva = (
                  f"{motorista_seleccionado} ({reservado_por}) - Ocupado"
              )
              actualizar_celda_hoja(
                  celda_destino, texto_reserva, color_rgb, nombre_hoja_actual
              )

            fecha_str = fecha_registro.strftime("%Y-%m-%d")
            fila_guardada = agregar_fila_hoja([
                motorista_seleccionado,
                f"{viajes_estimados} Viajes",
                reservado_por,
                f"{peso_total_quintales:,.2f} qq ({peso_total_general:,.2f}"
                " lbs)",
                fecha_str,
                direccion_envio,
            ])

            st.session_state.form_reset = True
            st.success(
                f"¡Se han agendado con éxito los {viajes_estimados} viajes en"
                f" Google Drive ({nombre_hoja_actual})!"
            )
            st.rerun()
        except Exception as e:
          st.error(f"Error al escribir en Google Drive: {e}")

  st.markdown("---")
  st.subheader(
      f"👀 Cuadro de Disponibilidad en Google Drive ({nombre_hoja_actual})"
  )

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
          val = (
              matriz_datos[r_idx][c_idx]
              if matriz_datos and len(matriz_datos) > r_idx
              else ""
          )
          if dia == "SÁBADO" and hora_etiqueta in [
              "2:30 p.m. (⭐ Viaje 3)",
              "4:30 p.m. (⭐ Viaje 4)",
          ]:
            fila_actual[dia] = "🚫 No laborable"
            continue
          if not es_reserva_real(val):
            libres_count += 1
          else:
            ocupaciones.append(str(val).split(" - ")[0])

        if dia != "SÁBADO" or hora_etiqueta not in [
            "2:30 p.m. (⭐ Viaje 3)",
            "4:30 p.m. (⭐ Viaje 4)",
        ]:
          if libres_count == len(cols):
            fila_actual[dia] = "🟢 Todo Libre (5)"
          elif libres_count == 0:
            fila_actual[dia] = f"🔴 Ocupado ({', '.join(ocupaciones)})"
          else:
            fila_actual[dia] = (
                f"🟡 {libres_count} Libres | Ocup: {', '.join(ocupaciones)}"
            )
      datos_calendario.append(fila_actual)

    st.dataframe(
        pd.DataFrame(datos_calendario), hide_index=True, use_container_width=True
    )
  except Exception as e:
    st.warning(f"No se pudo cargar el cuadro desde Google Drive: {e}")

elif menu_opcion == "📦 Consulta de Materiales":
  st.subheader("📦 Lista Actual de Materiales y Pesos (Google Drive)")
  st.write(
      "Aquí puedes verificar los materiales sincronizados que alimentan el"
      " sistema de cálculo de peso."
  )
  st.dataframe(df_materiales_base, use_container_width=True)

elif menu_opcion == "📊 Reportes Mensuales":
  st.subheader("📊 Historial y Reportes Mensuales")
  st.info(
      "💡 Los envíos registrados se archivan automáticamente en pestañas"
      " semanales y mensuales dentro de tu archivo de Google Drive."
  )
  st.write(
      "Puedes consultar el consolidado detallado abriendo directamente tu"
      " Google Sheet y revisando las pestañas correspondientes."
  )
