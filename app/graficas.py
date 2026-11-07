"""Construcción de las gráficas del dashboard con Bokeh.

Cada función recibe el DataFrame mensual (ya con las métricas derivadas de
``kpis.agregar_metricas_mensuales``) y devuelve una figura de Bokeh lista
para incrustarse en Streamlit con ``streamlit_bokeh``.

Todas comparten el mismo estilo (``_aplicar_estilo``): fondo claro,
cuadrícula horizontal tenue, sin barra de herramientas y con *tooltip* al
pasar el mouse, que es la interactividad principal de Bokeh.
"""

from __future__ import annotations

import pandas as pd
from bokeh.models import (
    ColumnDataSource,
    CustomJSTickFormatter,
    HoverTool,
    Label,
    LabelSet,
    NumeralTickFormatter,
    Range1d,
    Span,
)
from bokeh.core.properties import value
from bokeh.plotting import figure

from app import tema
from app.kpis import tendencia_lineal

# streamlit-bokeh escala cada figura al ancho de su columna CONSERVANDO la
# proporción ancho/alto. Por eso se define una proporción por tipo de gráfica:
PROPORCION_ANCHA = (1200, 380)   # gráfica a todo lo ancho (ventas)
PROPORCION_MEDIA = (600, 380)    # gráficas en media columna


# --------------------------------------------------------------------------
# Utilidades comunes
# --------------------------------------------------------------------------
def _fuente(df: pd.DataFrame) -> ColumnDataSource:
    """Convierte el DataFrame en la fuente de datos que usa Bokeh."""
    datos = df.copy()
    datos["etiqueta"] = [tema.MESES_ES[m.month - 1] for m in datos["mes"]]
    return ColumnDataSource(datos)


def _figura(etiquetas: list[str], proporcion: tuple[int, int] = PROPORCION_MEDIA) -> figure:
    ancho, alto = proporcion
    p = figure(
        x_range=etiquetas,
        width=ancho,
        height=alto,
        toolbar_location=None,
        tools="",
    )
    # Aire a los lados para que la etiqueta del último punto no se corte
    p.x_range.range_padding = 0.2
    _aplicar_estilo(p)
    return p


def _aplicar_estilo(p: figure) -> None:
    p.background_fill_color = tema.FONDO_GRAFICA
    p.border_fill_color = tema.FONDO_GRAFICA
    p.outline_line_color = None
    p.min_border_left = 8
    p.min_border_right = 16

    # Cuadrícula: solo horizontal, línea fina y tenue
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = tema.LINEA_GUIA
    p.ygrid.grid_line_width = 1

    for eje in (p.xaxis, p.yaxis):
        eje.axis_line_color = tema.LINEA_EJE
        eje.major_tick_line_color = None
        eje.minor_tick_line_color = None
        eje.major_label_text_color = tema.TEXTO_TENUE
        eje.major_label_text_font = tema.FUENTE
        eje.major_label_text_font_size = "11px"
    p.yaxis.axis_line_color = None


def _estilo_leyenda(p: figure) -> None:
    p.legend.location = "top_left"
    p.legend.orientation = "horizontal"
    p.legend.background_fill_alpha = 0
    p.legend.border_line_color = None
    p.legend.label_text_color = tema.TEXTO_SECUNDARIO
    p.legend.label_text_font = tema.FUENTE
    p.legend.label_text_font_size = "11px"
    p.legend.glyph_width = 16
    p.legend.spacing = 12


def _puntos(p: figure, fuente: ColumnDataSource, y: str, color: str):
    """Marcadores de 8 px con un anillo del color del fondo."""
    return p.scatter(
        "etiqueta", y, source=fuente, size=8, fill_color=color,
        line_color=tema.FONDO_GRAFICA, line_width=2,
    )


def _etiqueta_final(p: figure, x: str, y: float, texto: str) -> None:
    """Etiqueta solo el último punto (no se rotula cada valor)."""
    p.add_layout(LabelSet(
        x="x", y="y", text="t",
        source=ColumnDataSource({"x": [x], "y": [y], "t": [texto]}),
        x_offset=8, y_offset=0, text_font_size="11px",
        text_color=tema.TEXTO_SECUNDARIO, text_font=value(tema.FUENTE),
        text_align="left", text_baseline="middle",
    ))


def _formato_millones() -> CustomJSTickFormatter:
    """Formato de eje "$1.2M". Se crea uno nuevo por figura porque Bokeh no
    permite compartir el mismo objeto entre documentos distintos."""
    return CustomJSTickFormatter(code="return '$' + (tick / 1e6).toFixed(1) + 'M';")


# --------------------------------------------------------------------------
# 1. Ventas mensuales + tendencia (línea)
# --------------------------------------------------------------------------
def grafica_ventas(df: pd.DataFrame) -> figure:
    fuente = _fuente(df)
    etiquetas = list(fuente.data["etiqueta"])
    p = _figura(etiquetas, PROPORCION_ANCHA)

    tendencia = tendencia_lineal(df["ventas_mxn"])
    if tendencia is not None:
        fuente.data["tendencia"] = tendencia
        p.line("etiqueta", "tendencia", source=fuente, color=tema.TEXTO_TENUE,
               line_width=1.5, line_dash=[6, 4], legend_label="Tendencia lineal")

    p.varea(x="etiqueta", y1=0, y2="ventas_mxn", source=fuente,
            fill_color=tema.SERIE_1, fill_alpha=0.10)
    p.line("etiqueta", "ventas_mxn", source=fuente, color=tema.SERIE_1,
           line_width=2, line_join="round", line_cap="round", legend_label="Ventas")
    puntos = _puntos(p, fuente, "ventas_mxn", tema.SERIE_1)

    ultimo = df["ventas_mxn"].iloc[-1]
    _etiqueta_final(p, etiquetas[-1], ultimo, f"${ultimo / 1e6:,.2f}M")

    p.y_range = Range1d(0, df["ventas_mxn"].max() * 1.18)
    p.yaxis.formatter = _formato_millones()
    p.add_tools(HoverTool(renderers=[puntos], mode="vline", tooltips=[
        ("Mes", "@etiqueta"),
        ("Ventas", "@ventas_mxn{$0,0}"),
        ("vs. mes anterior", "@crecimiento_ventas{+0.0%}"),
    ]))
    _estilo_leyenda(p)
    return p


# --------------------------------------------------------------------------
# 2. Número de pedidos (barras)
# --------------------------------------------------------------------------
def grafica_pedidos(df: pd.DataFrame) -> figure:
    fuente = _fuente(df)
    etiquetas = list(fuente.data["etiqueta"])
    p = _figura(etiquetas)

    barras = p.vbar(
        x="etiqueta", top="pedidos", source=fuente, width=0.45,
        fill_color=tema.SERIE_1, line_color=None,
        border_radius=(4, 4, 0, 0),  # esquinas redondeadas solo arriba
    )

    # Rotula únicamente el mes con más pedidos
    idx = int(df["pedidos"].idxmax())
    pos = df.index.get_loc(idx)
    p.add_layout(LabelSet(
        x="x", y="y", text="t", y_offset=4, text_align="center",
        source=ColumnDataSource({"x": [etiquetas[pos]],
                                 "y": [df.loc[idx, "pedidos"]],
                                 "t": [f"{df.loc[idx, 'pedidos']:,}"]}),
        text_font_size="11px", text_color=tema.TEXTO_SECUNDARIO, text_font=value(tema.FUENTE),
    ))

    p.y_range = Range1d(0, df["pedidos"].max() * 1.15)
    p.yaxis.formatter = NumeralTickFormatter(format="0,0")
    p.add_tools(HoverTool(renderers=[barras], tooltips=[
        ("Mes", "@etiqueta"),
        ("Pedidos", "@pedidos{0,0}"),
        ("Ticket promedio", "@ticket_promedio{$0,0.00}"),
    ]))
    return p


# --------------------------------------------------------------------------
# 3. Tasa de conversión (línea)
# --------------------------------------------------------------------------
def grafica_conversion(df: pd.DataFrame) -> figure:
    fuente = _fuente(df)
    etiquetas = list(fuente.data["etiqueta"])
    p = _figura(etiquetas)

    p.line("etiqueta", "tasa_conversion", source=fuente, color=tema.SERIE_1,
           line_width=2, line_join="round", line_cap="round")
    puntos = _puntos(p, fuente, "tasa_conversion", tema.SERIE_1)

    ultimo = df["tasa_conversion"].iloc[-1]
    _etiqueta_final(p, etiquetas[-1], ultimo, f"{ultimo:.2%}")

    minimo, maximo = df["tasa_conversion"].min(), df["tasa_conversion"].max()
    margen = max((maximo - minimo) * 0.25, 0.001)
    p.y_range = Range1d(max(minimo - margen, 0), maximo + margen)
    p.yaxis.formatter = NumeralTickFormatter(format="0.0%")
    p.add_tools(HoverTool(renderers=[puntos], mode="vline", tooltips=[
        ("Mes", "@etiqueta"),
        ("Conversión", "@tasa_conversion{0.00%}"),
        ("Visitas", "@visitas{0,0}"),
        ("Pedidos", "@pedidos{0,0}"),
    ]))
    return p


# --------------------------------------------------------------------------
# 4. Clientes nuevos vs recurrentes (tendencia, 2 series)
# --------------------------------------------------------------------------
def grafica_clientes(df: pd.DataFrame) -> figure:
    fuente = _fuente(df)
    etiquetas = list(fuente.data["etiqueta"])
    p = _figura(etiquetas)

    series = [("clientes_nuevos", "Nuevos", tema.SERIE_1),
              ("clientes_recurrentes", "Recurrentes", tema.SERIE_2)]
    renderers = []
    for columna, nombre, color in series:
        p.line("etiqueta", columna, source=fuente, color=color, line_width=2,
               line_join="round", line_cap="round", legend_label=nombre)
        renderers.append(_puntos(p, fuente, columna, color))

    p.y_range = Range1d(0, df[["clientes_nuevos", "clientes_recurrentes"]].max().max() * 1.2)
    p.yaxis.formatter = NumeralTickFormatter(format="0,0")
    # Un solo tooltip por mes con ambas series
    p.add_tools(HoverTool(renderers=[renderers[0]], mode="vline", tooltips=[
        ("Mes", "@etiqueta"),
        ("Nuevos", "@clientes_nuevos{0,0}"),
        ("Recurrentes", "@clientes_recurrentes{0,0}"),
        ("% recurrentes", "@pct_recurrentes{0.0%}"),
    ]))
    _estilo_leyenda(p)
    return p


# --------------------------------------------------------------------------
# 5. Satisfacción del cliente (línea con meta)
# --------------------------------------------------------------------------
def grafica_satisfaccion(df: pd.DataFrame) -> figure:
    fuente = _fuente(df)
    etiquetas = list(fuente.data["etiqueta"])
    p = _figura(etiquetas)

    meta = tema.META_SATISFACCION
    p.add_layout(Span(location=meta, dimension="width",
                      line_color=tema.TEXTO_TENUE, line_width=1, line_dash=[6, 4]))
    p.add_layout(Label(x=0, y=meta, x_units="screen", text=f"Meta {meta}",
                       x_offset=4, y_offset=4, text_font_size="11px",
                       text_color=tema.TEXTO_TENUE, text_font=tema.FUENTE))

    p.line("etiqueta", "calificacion_promedio", source=fuente, color=tema.SERIE_1,
           line_width=2, line_join="round", line_cap="round")
    puntos = _puntos(p, fuente, "calificacion_promedio", tema.SERIE_1)

    ultimo = df["calificacion_promedio"].iloc[-1]
    _etiqueta_final(p, etiquetas[-1], ultimo, f"{ultimo:.2f}")

    minimo = min(df["calificacion_promedio"].min(), meta)
    p.y_range = Range1d(max(minimo - 0.4, 1), 5.0)
    p.yaxis.formatter = NumeralTickFormatter(format="0.0")
    p.add_tools(HoverTool(renderers=[puntos], mode="vline", tooltips=[
        ("Mes", "@etiqueta"),
        ("Calificación", "@calificacion_promedio{0.00} / 5"),
        ("Reseñas", "@num_resenas{0,0}"),
    ]))
    return p
