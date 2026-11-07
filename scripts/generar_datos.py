"""Genera (o regenera) el CSV de datos simulados en data/.

Uso (desde la raíz del proyecto):
    python scripts/generar_datos.py              # semilla 42 por defecto
    python scripts/generar_datos.py --semilla 7  # otro escenario
    python scripts/generar_datos.py --salida data/otro.csv
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import datos  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Genera datos simulados de e-commerce (12 meses).")
    parser.add_argument("--semilla", type=int, default=datos.SEMILLA_DEFAULT,
                        help=f"Semilla aleatoria (default: {datos.SEMILLA_DEFAULT}).")
    parser.add_argument("--salida", type=Path, default=datos.RUTA_CSV,
                        help="Ruta del CSV de salida (default: data/ecommerce_mensual_2025.csv).")
    args = parser.parse_args()

    df = datos.generar_datos(args.semilla)
    ruta = datos.guardar_csv(df, args.salida)
    print(f"{len(df)} meses generados con semilla {args.semilla} -> {ruta}")
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
