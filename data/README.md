# Datos

## `ecommerce_mensual_2025.csv`

Datos **simulados** de una tienda en línea mexicana, de enero a diciembre de 2025
(una fila por mes). Se generan con `python scripts/generar_datos.py` usando la
semilla `42`, por lo que el archivo siempre se puede reproducir idéntico.

### Diccionario de datos

| Columna | Tipo | Descripción |
|---|---|---|
| `mes` | fecha (`AAAA-MM-DD`) | Primer día del mes |
| `visitas` | entero | Sesiones en el sitio durante el mes |
| `pedidos` | entero | Pedidos completados |
| `ventas_mxn` | decimal | Ingresos del mes en pesos mexicanos |
| `clientes_nuevos` | entero | Clientes que compraron por primera vez ese mes |
| `clientes_recurrentes` | entero | Clientes que ya habían comprado antes |
| `calificacion_promedio` | decimal (1–5) | Calificación promedio de las reseñas del mes |
| `num_resenas` | entero | Número de reseñas recibidas |

### Reglas de la simulación

Definidas en [`app/datos.py`](../app/datos.py):

| Variable | Regla |
|---|---|
| Visitas | 60,000 base × crecimiento de 1.5 % mensual × estacionalidad × ruido normal (±4 %) |
| Estacionalidad | Ene 0.90 · Feb 0.85 · Mar 0.95 · Abr 0.97 · **May 1.10 (Hot Sale)** · Jun 1.02 · Jul 0.98 · Ago 1.00 · Sep 0.97 · Oct 1.03 · **Nov 1.30 (Buen Fin)** · **Dic 1.40 (Navidad)** |
| Conversión | 2.2 % base, +0.06 pp por mes, +0.3 pp en mayo y noviembre, ruido ±0.15 pp |
| Pedidos | Binomial(visitas, conversión): cada visita "decide" si compra |
| Ticket promedio | $820 MXN, +0.4 % mensual; −5 % en noviembre (descuentos), +8 % en diciembre (regalos); ruido ±3.5 % |
| Ventas | pedidos × ticket |
| Clientes únicos | pedidos ÷ U(1.15, 1.30) (cada cliente hace entre 1.15 y 1.30 pedidos) |
| % recurrentes | 28 % base, +1.2 pp por mes (fidelización), ruido ±1.5 pp |
| Calificación | 4.35 ± 0.07; −0.15 en noviembre y diciembre (saturación de envíos) |
| Reseñas | Binomial(pedidos, 18 %) |

> Estos parámetros son supuestos razonables para fines académicos, no cifras
> de una empresa real.
