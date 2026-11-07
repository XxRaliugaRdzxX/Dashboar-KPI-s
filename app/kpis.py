"""Cálculo de los KPIs a partir de los datos mensuales.

Todas las funciones son "puras": reciben un DataFrame y devuelven valores,
sin depender de Streamlit. Así se pueden probar con pytest.

Fórmulas:
    Ticket promedio (AOV)  = ventas / pedidos
    Tasa de conversión     = pedidos / visitas
    % clientes recurrentes = recurrentes / (nuevos + recurrentes)
    Satisfacción           = promedio de calificaciones ponderado por
                             el número de reseñas de cada mes
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ResumenKPIs:
    ventas_totales: float
    pedidos_totales: int
    visitas_totales: int
    ticket_promedio: float
    tasa_conversion: float
    clientes_nuevos: int
    clientes_recurrentes: int
    pct_recurrentes: float
    satisfaccion: float
    resenas_totales: int


def agregar_metricas_mensuales(df: pd.DataFrame) -> pd.DataFrame:
    """Agrega columnas derivadas por mes (no modifica el DataFrame original)."""
    out = df.copy()
    clientes = out["clientes_nuevos"] + out["clientes_recurrentes"]
    out["ticket_promedio"] = out["ventas_mxn"] / out["pedidos"]
    out["tasa_conversion"] = out["pedidos"] / out["visitas"]
    out["clientes_totales"] = clientes
    out["pct_recurrentes"] = out["clientes_recurrentes"] / clientes
    out["crecimiento_ventas"] = out["ventas_mxn"].pct_change()
    return out


def calcular_resumen(df: pd.DataFrame) -> ResumenKPIs:
    """KPIs del periodo completo seleccionado.

    Ojo: los clientes se suman mes a mes, así que una misma persona que
    compra en dos meses cuenta dos veces ("clientes-mes").
    """
    ventas = float(df["ventas_mxn"].sum())
    pedidos = int(df["pedidos"].sum())
    visitas = int(df["visitas"].sum())
    nuevos = int(df["clientes_nuevos"].sum())
    recurrentes = int(df["clientes_recurrentes"].sum())
    resenas = int(df["num_resenas"].sum())

    satisfaccion = (
        float(np.average(df["calificacion_promedio"], weights=df["num_resenas"]))
        if resenas > 0
        else float(df["calificacion_promedio"].mean())
    )

    return ResumenKPIs(
        ventas_totales=ventas,
        pedidos_totales=pedidos,
        visitas_totales=visitas,
        ticket_promedio=ventas / pedidos if pedidos else 0.0,
        tasa_conversion=pedidos / visitas if visitas else 0.0,
        clientes_nuevos=nuevos,
        clientes_recurrentes=recurrentes,
        pct_recurrentes=recurrentes / (nuevos + recurrentes) if (nuevos + recurrentes) else 0.0,
        satisfaccion=satisfaccion,
        resenas_totales=resenas,
    )


def variacion_ultimo_mes(serie: pd.Series) -> float | None:
    """Cambio relativo del último mes contra el anterior (None si no hay 2 meses)."""
    if len(serie) < 2 or serie.iloc[-2] == 0:
        return None
    return float(serie.iloc[-1] / serie.iloc[-2] - 1)


def tendencia_lineal(valores: pd.Series) -> np.ndarray | None:
    """Recta de mínimos cuadrados ajustada a la serie (None si hay < 2 puntos)."""
    if len(valores) < 2:
        return None
    x = np.arange(len(valores))
    pendiente, intercepto = np.polyfit(x, valores.to_numpy(dtype=float), 1)
    return pendiente * x + intercepto
