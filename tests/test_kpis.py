"""Pruebas del cálculo de KPIs con datos pequeños calculables a mano."""

import pandas as pd
import pytest

from app import kpis


@pytest.fixture
def df_simple():
    return pd.DataFrame({
        "mes": pd.date_range("2025-01-01", periods=2, freq="MS"),
        "visitas": [1000, 2000],
        "pedidos": [20, 60],
        "ventas_mxn": [10_000.0, 36_000.0],
        "clientes_nuevos": [10, 20],
        "clientes_recurrentes": [5, 25],
        "calificacion_promedio": [4.0, 5.0],
        "num_resenas": [10, 30],
    })


def test_resumen(df_simple):
    r = kpis.calcular_resumen(df_simple)
    assert r.ventas_totales == 46_000
    assert r.pedidos_totales == 80
    assert r.ticket_promedio == pytest.approx(46_000 / 80)        # 575
    assert r.tasa_conversion == pytest.approx(80 / 3000)
    assert r.pct_recurrentes == pytest.approx(30 / 60)            # 50 %
    # Ponderado por reseñas: (4*10 + 5*30) / 40 = 4.75
    assert r.satisfaccion == pytest.approx(4.75)


def test_metricas_mensuales(df_simple):
    m = kpis.agregar_metricas_mensuales(df_simple)
    assert m["ticket_promedio"].tolist() == pytest.approx([500, 600])
    assert m["tasa_conversion"].tolist() == pytest.approx([0.02, 0.03])
    assert m["crecimiento_ventas"].iloc[1] == pytest.approx(2.6)
    assert "ticket_promedio" not in df_simple.columns  # no modifica el original


def test_variacion_ultimo_mes():
    assert kpis.variacion_ultimo_mes(pd.Series([100, 110])) == pytest.approx(0.10)
    assert kpis.variacion_ultimo_mes(pd.Series([100])) is None


def test_tendencia_lineal():
    assert kpis.tendencia_lineal(pd.Series([1, 2, 3])).tolist() == pytest.approx([1, 2, 3])
    assert kpis.tendencia_lineal(pd.Series([5])) is None
