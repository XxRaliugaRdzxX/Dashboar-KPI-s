"""Simulación y carga de los datos mensuales del e-commerce.

Como no se cuenta con datos reales, se generan 12 meses de datos sintéticos
con reglas de negocio simples pero creíbles:

* **Visitas**: base mensual con crecimiento constante + estacionalidad
  (Hot Sale en mayo, Buen Fin en noviembre, Navidad en diciembre) + ruido.
* **Pedidos**: cada visita convierte con cierta probabilidad
  (distribución binomial). La conversión mejora poco a poco y sube en
  meses de promoción.
* **Ventas**: pedidos x ticket promedio (con ruido). En el Buen Fin el
  ticket baja por descuentos y en diciembre sube por regalos.
* **Clientes**: los pedidos se reparten entre clientes únicos; la fracción
  de clientes recurrentes crece mes a mes (fidelización).
* **Satisfacción**: calificación de 1 a 5 cercana a 4.35; baja un poco en
  temporada alta por saturación logística.

Se usa una *semilla* para que los datos sean reproducibles: con la misma
semilla siempre se obtienen exactamente los mismos números.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

RAIZ_PROYECTO = Path(__file__).resolve().parents[1]
RUTA_CSV = RAIZ_PROYECTO / "data" / "ecommerce_mensual_2025.csv"

SEMILLA_DEFAULT = 42
ANIO = 2025

# Factor de estacionalidad por mes (1.0 = mes "normal")
ESTACIONALIDAD = np.array(
    [0.90, 0.85, 0.95, 0.97, 1.10, 1.02, 0.98, 1.00, 0.97, 1.03, 1.30, 1.40]
)
MESES_PROMOCION = {5, 11}  # Hot Sale y Buen Fin

COLUMNAS = [
    "mes",
    "visitas",
    "pedidos",
    "ventas_mxn",
    "clientes_nuevos",
    "clientes_recurrentes",
    "calificacion_promedio",
    "num_resenas",
]


def generar_datos(semilla: int = SEMILLA_DEFAULT, anio: int = ANIO) -> pd.DataFrame:
    """Genera 12 meses de datos simulados. Misma semilla => mismos datos."""
    rng = np.random.default_rng(semilla)
    n = 12
    i = np.arange(n)                      # 0..11, índice del mes
    num_mes = i + 1                       # 1..12
    promo = np.isin(num_mes, list(MESES_PROMOCION))

    # 1) Visitas: base * crecimiento 1.5 % mensual * estacionalidad * ruido 4 %
    visitas = 60_000 * (1.015 ** i) * ESTACIONALIDAD * rng.normal(1, 0.04, n)
    visitas = visitas.round().astype(int)

    # 2) Tasa de conversión "real" del mes y pedidos (binomial)
    conversion = 0.022 + 0.0006 * i + 0.003 * promo + rng.normal(0, 0.0015, n)
    conversion = np.clip(conversion, 0.012, 0.05)
    pedidos = rng.binomial(visitas, conversion)

    # 3) Ticket promedio en MXN y ventas
    ajuste_ticket = np.ones(n)
    ajuste_ticket[10] = 0.95   # noviembre: descuentos del Buen Fin
    ajuste_ticket[11] = 1.08   # diciembre: compras de regalos
    ticket = 820 * (1 + 0.004 * i) * ajuste_ticket * rng.normal(1, 0.035, n)
    ventas = (pedidos * ticket).round(2)

    # 4) Clientes únicos del mes: cada cliente hace entre 1.15 y 1.30 pedidos
    clientes = (pedidos / rng.uniform(1.15, 1.30, n)).round().astype(int)
    pct_recurrentes = np.clip(0.28 + 0.012 * i + rng.normal(0, 0.015, n), 0.05, 0.95)
    recurrentes = (clientes * pct_recurrentes).round().astype(int)
    nuevos = clientes - recurrentes

    # 5) Satisfacción (1-5) y número de reseñas (~18 % de los pedidos)
    saturacion = np.where(num_mes >= 11, 0.15, 0.0)
    calificacion = np.clip(4.35 - saturacion + rng.normal(0, 0.07, n), 1, 5).round(2)
    resenas = rng.binomial(pedidos, 0.18)

    return pd.DataFrame(
        {
            "mes": pd.date_range(f"{anio}-01-01", periods=n, freq="MS"),
            "visitas": visitas,
            "pedidos": pedidos,
            "ventas_mxn": ventas,
            "clientes_nuevos": nuevos,
            "clientes_recurrentes": recurrentes,
            "calificacion_promedio": calificacion,
            "num_resenas": resenas,
        },
        columns=COLUMNAS,
    )


def guardar_csv(df: pd.DataFrame, ruta: Path = RUTA_CSV) -> Path:
    """Guarda los datos en CSV (crea la carpeta si no existe)."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(ruta, index=False, date_format="%Y-%m-%d")
    return ruta


def cargar_datos(ruta: Path = RUTA_CSV) -> pd.DataFrame:
    """Lee el CSV de ``data/``. Si no existe, lo genera con la semilla default.

    Si la carpeta no se puede escribir (p. ej. un contenedor de solo lectura),
    los datos simplemente se quedan en memoria.
    """
    if not ruta.exists():
        df = generar_datos()
        try:
            guardar_csv(df, ruta)
        except OSError:
            pass
        return df

    df = pd.read_csv(ruta, parse_dates=["mes"])
    faltantes = set(COLUMNAS) - set(df.columns)
    if faltantes:
        raise ValueError(f"Al CSV {ruta.name} le faltan columnas: {sorted(faltantes)}")
    return df[COLUMNAS].sort_values("mes").reset_index(drop=True)
