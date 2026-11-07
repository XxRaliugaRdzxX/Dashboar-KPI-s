"""Pruebas de la simulación de datos."""

import pandas as pd

from app import datos


def test_genera_12_meses_con_todas_las_columnas():
    df = datos.generar_datos()
    assert len(df) == 12
    assert list(df.columns) == datos.COLUMNAS
    assert df["mes"].dt.month.tolist() == list(range(1, 13))


def test_misma_semilla_mismos_datos():
    pd.testing.assert_frame_equal(datos.generar_datos(7), datos.generar_datos(7))


def test_semillas_distintas_dan_datos_distintos():
    assert not datos.generar_datos(1).equals(datos.generar_datos(2))


def test_valores_en_rangos_validos():
    df = datos.generar_datos()
    assert (df["pedidos"] > 0).all()
    assert (df["pedidos"] < df["visitas"]).all()
    assert (df["ventas_mxn"] > 0).all()
    assert (df["clientes_nuevos"] >= 0).all()
    assert (df["clientes_recurrentes"] >= 0).all()
    assert df["calificacion_promedio"].between(1, 5).all()
    assert (df["num_resenas"] <= df["pedidos"]).all()


def test_csv_ida_y_vuelta(tmp_path):
    ruta = tmp_path / "datos.csv"
    original = datos.generar_datos()
    datos.guardar_csv(original, ruta)
    leido = datos.cargar_datos(ruta)
    pd.testing.assert_frame_equal(original, leido, check_dtype=False)


def test_cargar_genera_csv_si_no_existe(tmp_path):
    ruta = tmp_path / "sub" / "datos.csv"
    df = datos.cargar_datos(ruta)
    assert ruta.exists()
    assert len(df) == 12
