"""Colores y constantes visuales compartidas por todas las gráficas.

Se definen en un solo lugar para que el dashboard se vea consistente y para
poder cambiar la identidad visual sin tocar el código de las gráficas.

Los dos colores de serie (azul y naranja) se tomaron de una paleta
categórica validada para daltonismo: se distinguen entre sí aun con
deuteranopia, protanopia y tritanopia.
"""

# Superficies y tinta
FONDO_GRAFICA = "#fcfcfb"
TEXTO_PRINCIPAL = "#0b0b0b"
TEXTO_SECUNDARIO = "#52514e"
TEXTO_TENUE = "#898781"
LINEA_GUIA = "#e1e0d9"   # cuadrícula
LINEA_EJE = "#c3c2b7"    # ejes / línea base

# Series (en orden fijo: la serie 1 siempre es azul, la 2 siempre naranja)
SERIE_1 = "#2a78d6"  # azul
SERIE_2 = "#eb6834"  # naranja

# Misma familia que usa Streamlit, con respaldo sans-serif
FUENTE = "Source Sans Pro, Helvetica, Arial, sans-serif"

# Supuesto de negocio para la gráfica de satisfacción (ajustable)
META_SATISFACCION = 4.5

MESES_ES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
            "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
