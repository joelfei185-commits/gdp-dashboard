from datetime import datetime, timedelta
import json
import math
import tempfile
from google.oauth2 import service_account
import gspread
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Logística de Envío - Ferretería & Homecenter El Indio",
    page_icon="🏗️",
    layout="wide",
)

st.title("🏗️ LOGISTICA DE ENVIO FERRETERIA & HOMECENTER EL INDIO")
st.markdown("Sincronizado con tu Dashboard profesional en Google Drive.")


@st.cache_resource
def conectar_google_sheets():
  scope = [
      "https://spreadsheets.google.com/feeds",
      "https://www.googleapis.com/auth/drive",
  ]

  if "gcp_service_account" in st.secrets:
    secret_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in secret_dict:
      pk = str(secret_dict["private_key"])
      # Corrección exhaustiva para asegurar formato PEM válido de la llave privada
      pk = pk.replace("\\n", "\n")
      if "----BEGIN PRIVATE KEY----" in pk and not pk.startswith(
          "-----BEGIN PRIVATE KEY-----"
      ):
        pk = (
            "-----BEGIN PRIVATE KEY-----\n"
            + pk.split("----BEGIN PRIVATE KEY----")[-1]
        )
      if "----END PRIVATE KEY----" in pk and not pk.endswith(
          "-----END PRIVATE KEY-----\n"
      ):
        pk = (
            pk.split("----END PRIVATE KEY----")[0]
            + "-----END PRIVATE KEY-----\n"
        )
      secret_dict["private_key"] = pk

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".json"
    ) as f:
      json.dump(secret_dict, f)
      temp_filename = f.name

    creds = service_account.Credentials.from_service_account_file(
        temp_filename, scopes=scope
    )
  else:
    creds = service_account.Credentials.from_service_account_file(
        "credentials.json", scopes=scope
    )

  client = gspread.authorize(creds)
  return client.open("CALCULO DE MATERIALES MAC")


# Lista fija de materiales exacta
df_materiales_base = pd.DataFrame({
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

# Intentar conectar a Google Drive para motoristas y calendario
try:
  sh = conectar_google_sheets()

  df_motoristas = pd.DataFrame({
      "MOTORISTA": ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS"],
      "CAPACIDAD (QUINTALES)": [100, 100, 50, 100, 100],
  })

  st.success("¡Conectado y sincronizado con Google Drive exitosamente!")

except Exception as e:
  st.warning(f"Aviso de conexión: {e}. Usando valores locales.")
  df_motoristas = pd.DataFrame(
      {"MOTORISTA": ["ELVIS"], "CAPACIDAD (QUINTALES)": [100]}
  )

# Colores corporativos en formato RGB para cada motorista
COLORES_MOTORISTAS = {
    "ELVIS": {"red": 1.0, "green": 0.92, "blue": 0.23},  # Amarillo suave
    "LUIS PEREZ": {"red": 0.56, "green": 0.93, "blue": 0.56},  # Verde suave
    "DIEGO": {"red": 0.68, "green": 0.85, "blue": 0.90},  # Celeste suave
    "ALVARO": {"red": 0.85, "green": 0.65, "blue": 1.0},  # Morado/Lila suave
    "TOMAS": {"red": 1.0, "green": 0.75, "blue": 0.80},  # Rosa suave
}

# Mapeo de bloques de columnas exactos por día (C=3 hasta AF=32)
mapa_dias_bloques = {
    "LUNES": [3, 4, 5, 6, 7],  # C a G
    "MARTES": [8, 9, 10, 11, 12],  # H a L
    "MIÉRCOLES": [13, 14, 15, 16, 17],  # M a Q
    "JUEVES": [18, 19, 20, 21, 22],  # R a V
    "VIERNES": [23, 24, 25, 26, 27],  # W a AA
    "SÁBADO": [28, 29, 30, 31, 32],  # AB a AF
}

# Mapeo exacto de filas en Google Sheets
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
  motoristas_validos = ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS"]
  for mot in motoristas_validos:
    if mot in val_upper:
      return True
  return False


# --- GESTIÓN DE ESTADOS DE SESIÓN Y SINCRONIZACIÓN BIDIRECCIONAL ---
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

hoy = datetime.now()
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


# --- INTERFAZ DE LA APLICACIÓN ---
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
      st.markdown(
          "Selecciona un viaje para agregarle complementos y rellenar su peso"
          " libre:"
      )
      viajes_disponibles_opciones = [
          f"Viaje {i+1}" for i in range(viajes_estimados)
      ]
      viaje_a_rellenar = st.selectbox(
          "Elegir Viaje a Completar", viajes_disponibles_opciones
      )

      st.markdown("---")
      st.markdown(
          f"Agregando materiales extra para **{viaje_a_rellenar}**:"
      )
      cantidades_p2 = []
      for index, row in df_materiales_base.iterrows():
        mat_nombre = str(row["MATERIAL"])
        mat_lbs = float(row["LBS"])
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

  if capacidad_en_libras > 0 and peso_total_general > 0:
    viajes_estimados = max(1, math.ceil(peso_total_general / capacidad_en_libras))
    st.info(
        f"💡 Capacidad máxima del vehículo (**{motorista_seleccionado}**):"
        f" **{capacidad_quintales:,.0f} qq** ({capacidad_en_libras:,.0f} lbs)."
        f" Requerirá **{viajes_estimados} viaje(s)**."
    )

st.markdown("---")
st.subheader("📊 Desglose de Carga y Peso Libre por Viaje")

df_con_carga = df_total_general[df_total_general["CANTIDAD"] > 0].copy()
if not df_con_carga.empty and capacidad_en_libras > 0:
  nombres_materiales = df_con_carga["MATERIAL"].tolist()
  cantidades_materiales = df_con_carga["CANTIDAD"].tolist()
  pesos_unitarios = df_con_carga["LBS"].tolist()

  viajes_detalle = []
  item_idx = 0
  cantidad_actual_item = (
      cantidades_materiales[0] if len(cantidades_materiales) > 0 else 0
  )

  for v in range(viajes_estimados):
    peso_este_viaje = 0.0
    materiales_en_viaje = []

    while item_idx < len(nombres_materiales) and peso_este_viaje < (
        capacidad_en_libras - 1e-5
    ):
      mat_nombre = nombres_materiales[item_idx]
      peso_u = pesos_unitarios[item_idx]

      espacio_libre = capacidad_en_libras - peso_este_viaje
      cantidad_que_cabe = espacio_libre / peso_u if peso_u > 0 else 0
      cantidad_a_llevar = min(cantidad_actual_item, cantidad_que_cabe)

      if cantidad_a_llevar > 0:
        peso_parcial = cantidad_a_llevar * peso_u
        materiales_en_viaje.append(
            f"{mat_nombre}: {cantidad_a_llevar:,.1f} un. ({peso_parcial:,.2f}"
            " lbs)"
        )
        peso_este_viaje += peso_parcial
        cantidad_actual_item -= cantidad_a_llevar

      if cantidad_actual_item <= 1e-5:
        item_idx += 1
        if item_idx < len(cantidades_materiales):
          cantidad_actual_item = cantidades_materiales[item_idx]

    porcentaje_llenado = (
        (peso_este_viaje / capacidad_en_libras) * 100
        if capacidad_en_libras > 0
        else 0
    )
    peso_libre_lbs = capacidad_en_libras - peso_este_viaje
    peso_libre_qq = peso_libre_lbs / 100

    sugerencia_texto = "✅ Viaje optimizado al límite"
    if peso_libre_lbs > 50.0:
      sugerencia_texto = f"⚠️ **Sugerencia:** A este viaje le faltan **{peso_libre_qq:,.2f} qq** ({peso_libre_lbs:,.1f} lbs) para llenarse."

    viajes_detalle.append({
        "Viaje": f"Viaje {v+1}",
        "Peso Transportado": f"{peso_este_viaje / 100:,.2f} qq ({peso_este_viaje:,.1f} lbs)",
        "⚖️ PESO LIBRE / DISPONIBLE": f"{peso_libre_qq:,.2f} qq ({peso_libre_lbs:,.1f} lbs)",
        "Espacio Usado": f"{porcentaje_llenado:.1f}%",
        "💡 Sugerencia de Carga": sugerencia_texto,
        "Materiales Asignados": ", ".join(materiales_en_viaje),
    })

  df_viajes_opt = pd.DataFrame(viajes_detalle)
  st.dataframe(df_viajes_opt, hide_index=True, use_container_width=True)
else:
  st.info(
      "👉 Ingrese cantidades de materiales arriba para ver el desglose y el"
      " peso disponible por viaje."
  )

st.markdown("---")
st.subheader("📅 Reserva de Espacio en el Calendario y Registro en Hoja 1")

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

try:
  sheet_temp = sh.worksheet("Hoja1")
  matriz_temp = sheet_temp.get("C1:AF26")
except Exception:
  matriz_temp = []

with st.form("form_envio"):
  horarios_libres_opciones = []
  if dia_envio == "SÁBADO":
    horarios_para_revisar = [
        "8:00 a.m. (⭐ Viaje 1)",
        "10:00 a.m. (⭐ Viaje 2)",
    ]
  else:
    horarios_para_revisar = HORARIOS_ESTRELLA

  columnas_del_dia = mapa_dias_bloques.get(dia_envio, [])

  for hora_b in horarios_para_revisar:
    clave_fila_rev = obtener_clave_fila(hora_b, dia_envio)
    fila_meta_rev = mapa_filas.get(clave_fila_rev, 0)
    row_idx_rev = fila_meta_rev - 1

    espacios_libres_en_hora = 0
    if matriz_temp and len(matriz_temp) > row_idx_rev:
      for c_num in columnas_del_dia:
        c_idx_rev = c_num - 3
        val_celda = ""
        try:
          val_celda = matriz_temp[row_idx_rev][c_idx_rev]
        except IndexError:
          pass
        if not es_reserva_real(val_celda):
          espacios_libres_en_hora += 1
    else:
      espacios_libres_en_hora = 5

    if espacios_libres_en_hora > 0:
      horarios_libres_opciones.append(
          f"{hora_b} (Disponibles: {espacios_libres_en_hora}/5)"
      )

  if horarios_libres_opciones:
    horario_seleccionado = st.selectbox(
        "Seleccione Horario Disponible", horarios_libres_opciones
    )
  else:
    st.warning(
        f"⚠️ No hay horarios disponibles con espacio para el día {dia_envio}."
    )
    horario_seleccionado = None

  reservado_por = st.text_input(
      "Nombre de Quien Reserva", key="reservado_por_input"
  )
  direccion_envio = st.text_input(
      "Dirección de Destino / Entrega", key="direccion_input"
  )

  submitted = st.form_submit_button("Agendar Viajes y Guardar Registro")

  if submitted:
    if peso_total_general == 0:
      st.warning("Debe seleccionar al menos un material.")
    elif not reservado_por.strip():
      st.warning("Debe indicar el nombre de quien reserva.")
    elif not direccion_envio.strip():
      st.warning("Debe indicar la dirección de destino.")
    elif not horario_seleccionado:
      st.error("⚠️ Debe seleccionar un horario válido.")
    elif viajes_estimados > 4:
      st.error(
          "⚠️ La carga requiere más de 4 viajes, excediendo el límite diario"
          " por motorista."
      )
    elif dia_envio == "SÁBADO" and viajes_estimados > 2:
      st.error(
          "⚠️ Los sábados solo se trabaja hasta mediodía (máximo 2 viajes"
          " posibles)."
      )
    else:
      try:
        sheet_principal = sh.worksheet("Hoja1")
        matriz_datos = sheet_principal.get("C1:AF26")
        columnas_dia = mapa_dias_bloques[dia_envio]

        hora_base_elegida = horario_seleccionado.split(" (Disponibles:")[0]

        idx_inicio = horarios_para_revisar.index(hora_base_elegida)
        horarios_a_reservar = []

        for i in range(viajes_estimados):
          if idx_inicio + i < len(horarios_para_revisar):
            horarios_a_reservar.append(horarios_para_revisar[idx_inicio + i])

        if len(horarios_a_reservar) < viajes_estimados:
          st.error(
              "⚠️ No hay suficientes horarios sucesivos disponibles para los"
              f" {viajes_estimados} viajes requeridos."
          )
        else:
          espacios_totales_encontrados = []
          error_espacio = False

          for hora_b in horarios_a_reservar:
            clave_f = obtener_clave_fila(hora_b, dia_envio)
            fila_meta = mapa_filas[clave_f]
            row_idx = fila_meta - 1

            col_encontrada = None
            for col_num in columnas_dia:
              col_idx = col_num - 3
              val = ""
              try:
                val = matriz_datos[row_idx][col_idx]
              except IndexError:
                pass

              if not es_reserva_real(val):
                col_encontrada = col_num
                break

            if col_encontrada:
              espacios_totales_encontrados.append(
                  (col_encontrada, fila_meta, hora_b)
              )
            else:
              error_espacio = True
              break

          if error_espacio or len(espacios_totales_encontrados) < viajes_estimados:
            st.error(
                "⚠️ Algunos de los horarios consecutivos seleccionados ya"
                " fueron ocupados. Por favor actualice el cuadro."
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

              sheet_principal.update_acell(celda_destino, texto_reserva)
              sheet_principal.format(
                  celda_destino,
                  {
                      "backgroundColor": color_rgb,
                      "textFormat": {"bold": True},
                      "horizontalAlignment": "CENTER",
                  },
              )

            fecha_str = fecha_registro.strftime("%Y-%m-%d")
            try:
              columna_c_valores = sheet_principal.col_values(3)
              siguiente_fila = 30

              for idx_f in range(29, len(columna_c_valores)):
                val_fila = str(columna_c_valores[idx_f]).strip()
                if (
                    not val_fila
                    or val_fila.lower() == "none"
                    or val_fila.lower() == "nan"
                ):
                  siguiente_fila = idx_f + 1
                  break
              else:
                siguiente_fila = max(30, len(columna_c_valores) + 1)

              sheet_principal.update(
                  f"C{siguiente_fila}:H{siguiente_fila}",
                  [[
                      motorista_seleccionado,
                      f"{viajes_estimados} Viajes",
                      reservado_por,
                      f"{peso_total_quintales:,.2f} qq ({peso_total_general:,.2f} lbs)",
                      fecha_str,
                      direccion_envio,
                  ]],
              )
            except Exception as ex:
              st.warning(f"Detalle al guardar registro: {ex}")

            st.session_state.form_reset = True

            st.success(
                f"¡Se han agendado con éxito los {viajes_estimados} viajes"
                f" consecutivos para el {dia_envio} ({fecha_str}) en la fila"
                f" {siguiente_fila}!"
            )
            st.rerun()

      except Exception as e:
        st.error(f"Error al verificar o guardar en Google Drive: {e}")

st.markdown("---")
st.subheader("👀 Cuadro de Disponibilidad (Horarios Clave con ⭐)")

if st.button("🔄 Actualizar Cuadro de Disponibilidad"):
  st.rerun()

try:
  sheet_principal = sh.worksheet("Hoja1")
  matriz_datos = sheet_principal.get("C1:AF26")

  datos_calendario = []
  for hora_etiqueta in HORARIOS_ESTRELLA:
    fila_actual = {"HORA": hora_etiqueta}

    for dia, cols in mapa_dias_bloques.items():
      clave_f = obtener_clave_fila(hora_etiqueta, dia)
      r_num = mapa_filas[clave_f]
      r_idx = r_num - 1

      ocupaciones = []
      libres_count = 0

      for c_num in cols:
        c_idx = c_num - 3
        val = ""
        try:
          val = matriz_datos[r_idx][c_idx]
        except IndexError:
          pass

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

  df_calendario = pd.DataFrame(datos_calendario)
  st.dataframe(df_calendario, hide_index=True, use_container_width=True)

except Exception as e:
  st.warning(f"No se pudo cargar el cuadro de disponibilidad: {e}")
