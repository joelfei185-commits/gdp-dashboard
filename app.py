from datetime import datetime, timedelta
import math
import pandas as pd
import streamlit as st

# Configuración de la página
st.set_page_config(
    page_title="Logística de Envío - Ferretería & Homecenter El Indio",
    page_icon="🏗️",
    layout="wide",
)

st.title("🏗️ LOGISTICA DE ENVIO FERRETERIA & HOMECENTER EL INDIO")
st.markdown(
    "Sistema autónomo de cálculo de materiales, pesos y gestión de envíos."
)

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

df_motoristas = pd.DataFrame({
    "MOTORISTA": ["ELVIS", "LUIS PEREZ", "DIEGO", "ALVARO", "TOMAS"],
    "CAPACIDAD (QUINTALES)": [100, 100, 50, 100, 100],
})

# Colores corporativos para cada motorista
COLORES_MOTORISTAS = {
    "ELVIS": "🟡 Yellow",
    "LUIS PEREZ": "🟢 Green",
    "DIEGO": "🔵 Light Blue",
    "ALVARO": "🟣 Purple",
    "TOMAS": "🔴 Pink",
}

HORARIOS_ESTRELLA = [
    "8:00 a.m. (⭐ Viaje 1)",
    "10:00 a.m. (⭐ Viaje 2)",
    "2:30 p.m. (⭐ Viaje 3)",
    "4:30 p.m. (⭐ Viaje 4)",
]

# Inicializar base de datos local en la sesión
if "registros_locales" not in st.session_state:
  st.session_state.registros_locales = []

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


# --- INTERFAZ ---
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

  st.dataframe(
      pd.DataFrame(viajes_detalle), hide_index=True, use_container_width=True
  )
else:
  st.info(
      "👉 Ingrese cantidades de materiales arriba para ver el desglose y el"
      " peso disponible por viaje."
  )

st.markdown("---")
st.subheader("📅 Registro y Control de Envíos")

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

with st.form("form_envio"):
  horarios_para_revisar = (
      ["8:00 a.m. (⭐ Viaje 1)", "10:00 a.m. (⭐ Viaje 2)"]
      if dia_envio == "SÁBADO"
      else HORARIOS_ESTRELLA
  )
  horario_seleccionado = st.selectbox(
      "Seleccione Horario de Salida", horarios_para_revisar
  )

  reservado_por = st.text_input(
      "Nombre de Quien Reserva", key="reservado_por_input"
  )
  direccion_envio = st.text_input(
      "Dirección de Destino / Entrega", key="direccion_input"
  )

  submitted = st.form_submit_button("Guardar Registro de Envío")

  if submitted:
    if peso_total_general == 0:
      st.warning("Debe seleccionar al menos un material.")
    elif not reservado_por.strip():
      st.warning("Debe indicar el nombre de quien reserva.")
    elif not direccion_envio.strip():
      st.warning("Debe indicar la dirección de destino.")
    else:
      nuevo_registro = {
          "MOTORISTA": motorista_seleccionado,
          "VIAJES": f"{viajes_estimados} Viajes",
          "RESERVADO POR": reservado_por,
          "PESO TOTAL": f"{peso_total_quintales:,.2f} qq ({peso_total_general:,.2f} lbs)",
          "FECHA": fecha_registro.strftime("%Y-%m-%d"),
          "DÍA": dia_envio,
          "HORARIO": horario_seleccionado,
          "DIRECCIÓN": direccion_envio,
      }
      st.session_state.registros_locales.append(nuevo_registro)
      st.session_state.form_reset = True
      st.success("¡Registro guardado exitosamente en la aplicación!")
      st.rerun()

if st.session_state.registros_locales:
  st.markdown("---")
  st.subheader("📋 Historial de Envíos Registrados")
  df_historial = pd.DataFrame(st.session_state.registros_locales)
  st.dataframe(df_historial, hide_index=True, use_container_width=True)

  if st.button("🗑️ Limpiar Historial"):
    st.session_state.registros_locales = []
    st.rerun()
