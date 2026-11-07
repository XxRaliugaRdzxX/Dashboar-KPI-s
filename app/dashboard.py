"""Punto de entrada del dashboard: ``streamlit run app/dashboard.py``.

Flujo en cada interacción del usuario (Streamlit vuelve a ejecutar este
archivo de arriba a abajo):

    1. Cargar datos  (CSV de data/ o simulación con otra semilla)  -> datos.py
    2. Filtrar por el rango de meses elegido en la barra lateral
    3. Calcular KPIs                                               -> kpis.py
    4. Pintar tarjetas (Streamlit) y gráficas (Bokeh)              -> graficas.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Streamlit solo agrega la carpeta app/ al path; se agrega la raíz del
# proyecto para poder importar el paquete "app" igual que en las pruebas.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402
from streamlit_bokeh import streamlit_bokeh  # noqa: E402

from app import datos, graficas, kpis, tema  # noqa: E402

st.set_page_config(page_title="Dashboard KPIs · E-commerce", page_icon="📊", layout="wide")


# --------------------------------------------------------------------------
# Datos (en caché para no recalcular en cada clic)
# --------------------------------------------------------------------------
@st.cache_data
def obtener_datos(semilla: int) -> pd.DataFrame:
    if semilla == datos.SEMILLA_DEFAULT:
        return datos.cargar_datos()
    return datos.generar_datos(semilla)


# --------------------------------------------------------------------------
# Barra lateral: filtros
# --------------------------------------------------------------------------
with st.sidebar:
    st.header("Filtros")

    with st.expander("Escenario de datos", expanded=False):
        semilla = st.number_input(
            "Semilla de simulación", min_value=0, max_value=99_999,
            value=datos.SEMILLA_DEFAULT, step=1,
            help=(f"Con {datos.SEMILLA_DEFAULT} se leen los datos guardados en "
                  "data/. Cualquier otro número simula un escenario nuevo en memoria."),
        )

    df_completo = kpis.agregar_metricas_mensuales(obtener_datos(int(semilla)))
    etiquetas = [tema.MESES_ES[m.month - 1] for m in df_completo["mes"]]

    desde, hasta = st.select_slider(
        "Rango de meses", options=etiquetas, value=(etiquetas[0], etiquetas[-1])
    )
    st.caption(
        "Fuente: " + ("`data/ecommerce_mensual_2025.csv`"
                      if semilla == datos.SEMILLA_DEFAULT
                      else f"simulación en memoria (semilla {semilla})")
    )

i, j = etiquetas.index(desde), etiquetas.index(hasta)
df = df_completo.iloc[i: j + 1].reset_index(drop=True)
resumen = kpis.calcular_resumen(df)


# --------------------------------------------------------------------------
# Encabezado
# --------------------------------------------------------------------------
st.title("Dashboard de KPIs · E-commerce")
st.caption(
    f"Datos simulados · {desde}–{hasta} {datos.ANIO} · {len(df)} mes(es). "
    "Los cambios de cada tarjeta comparan el último mes del rango contra el anterior."
)


# --------------------------------------------------------------------------
# Tarjetas de métricas clave
# --------------------------------------------------------------------------
def _pct(valor: float | None) -> str | None:
    return None if valor is None else f"{valor:+.1%}"


def _dif(serie: pd.Series, factor: float, sufijo: str, decimales: int) -> str | None:
    """Diferencia absoluta del último mes contra el anterior (p. ej. puntos)."""
    if len(serie) < 2:
        return None
    return f"{(serie.iloc[-1] - serie.iloc[-2]) * factor:+.{decimales}f} {sufijo}"


DESCRIPCION_DELTA = "último mes vs. anterior"

fila_1 = st.columns(3)
fila_2 = st.columns(3)

fila_1[0].metric(
    "Ventas totales", f"${resumen.ventas_totales / 1e6:,.2f} M",
    delta=_pct(kpis.variacion_ultimo_mes(df["ventas_mxn"])),
    delta_description=DESCRIPCION_DELTA, border=True,
    chart_data=df["ventas_mxn"].round(0).tolist(), chart_type="area",
    help="Suma de ventas del periodo en pesos mexicanos (MXN).",
)
fila_1[1].metric(
    "Número de pedidos", f"{resumen.pedidos_totales:,}",
    delta=_pct(kpis.variacion_ultimo_mes(df["pedidos"])),
    delta_description=DESCRIPCION_DELTA, border=True,
    chart_data=df["pedidos"].tolist(), chart_type="bar",
)
fila_1[2].metric(
    "Valor promedio del pedido", f"${resumen.ticket_promedio:,.2f}",
    delta=_pct(kpis.variacion_ultimo_mes(df["ticket_promedio"])),
    delta_description=DESCRIPCION_DELTA, border=True,
    chart_data=df["ticket_promedio"].round(2).tolist(),
    help="Ticket promedio (AOV) = ventas / pedidos.",
)
fila_2[0].metric(
    "Tasa de conversión", f"{resumen.tasa_conversion:.2%}",
    delta=_dif(df["tasa_conversion"], 100, "pp", 2),
    delta_description=DESCRIPCION_DELTA, border=True,
    chart_data=(df["tasa_conversion"] * 100).round(3).tolist(),
    help=f"Pedidos / visitas. Visitas del periodo: {resumen.visitas_totales:,}. "
         "pp = puntos porcentuales.",
)
fila_2[1].metric(
    "Clientes recurrentes", f"{resumen.pct_recurrentes:.1%}",
    delta=_dif(df["pct_recurrentes"], 100, "pp", 1),
    delta_description=DESCRIPCION_DELTA, border=True,
    chart_data=(df["pct_recurrentes"] * 100).round(2).tolist(),
    help=(f"Recurrentes: {resumen.clientes_recurrentes:,} · Nuevos: "
          f"{resumen.clientes_nuevos:,} (suma de clientes por mes)."),
)
fila_2[2].metric(
    "Satisfacción del cliente", f"{resumen.satisfaccion:.2f} / 5",
    delta=_dif(df["calificacion_promedio"], 1, "pts", 2),
    delta_description=DESCRIPCION_DELTA, border=True,
    chart_data=df["calificacion_promedio"].tolist(),
    help=f"Promedio ponderado por {resumen.resenas_totales:,} reseñas.",
)


# --------------------------------------------------------------------------
# Gráficas (Bokeh)
# --------------------------------------------------------------------------
def mostrar(figura, clave: str) -> None:
    streamlit_bokeh(figura, use_container_width=True, theme=None, key=clave)


st.subheader("Ventas mensuales y tendencia")
mostrar(graficas.grafica_ventas(df), "ventas")

col_a, col_b = st.columns(2)
with col_a:
    st.subheader("Pedidos por mes")
    mostrar(graficas.grafica_pedidos(df), "pedidos")
with col_b:
    st.subheader("Tasa de conversión")
    mostrar(graficas.grafica_conversion(df), "conversion")

col_c, col_d = st.columns(2)
with col_c:
    st.subheader("Clientes nuevos vs. recurrentes")
    mostrar(graficas.grafica_clientes(df), "clientes")
with col_d:
    st.subheader("Satisfacción del cliente")
    mostrar(graficas.grafica_satisfaccion(df), "satisfaccion")


# --------------------------------------------------------------------------
# Tabla de datos (vista accesible + descarga)
# --------------------------------------------------------------------------
with st.expander("Ver tabla de datos del periodo"):
    tabla = df.assign(mes=df["mes"].dt.strftime("%Y-%m"))
    st.dataframe(
        tabla, hide_index=True, width="stretch",
        column_config={
            "ventas_mxn": st.column_config.NumberColumn("Ventas (MXN)", format="$%,.2f"),
            "ticket_promedio": st.column_config.NumberColumn("Ticket", format="$%,.2f"),
            "tasa_conversion": st.column_config.NumberColumn("Conversión", format="percent"),
            "pct_recurrentes": st.column_config.NumberColumn("% recurrentes", format="percent"),
            "crecimiento_ventas": st.column_config.NumberColumn("Crec. ventas", format="percent"),
        },
    )
    st.download_button(
        "Descargar CSV", tabla.to_csv(index=False).encode("utf-8"),
        file_name=f"kpis_{desde}_{hasta}_{datos.ANIO}.csv".lower(), mime="text/csv",
    )
