# Especificaciones de despliegue

## Resumen

| Concepto | Valor |
|---|---|
| Imagen base | `python:3.12-slim` |
| Nombre de la imagen | `dashboard-kpis:1.0.0` |
| Nombre del contenedor | `dashboard-kpis` |
| Puerto interno | `8501` (Streamlit) |
| Puerto en el host | `8501` (configurable con `DASHBOARD_PORT`) |
| Usuario dentro del contenedor | `appuser` (sin privilegios de root) |
| Healthcheck | `GET http://localhost:8501/_stcore/health` cada 30 s |
| Reinicio | `unless-stopped` |
| Tamaño aproximado de la imagen | ~870 MB |

> **Contexto de construcción:** el `Dockerfile` vive en `deploy/`, pero se
> construye desde la **raíz** del proyecto, porque necesita copiar `app/`,
> `data/` y `requirements.txt`. El `docker-compose.yml` ya lo indica con
> `context: ..`.

## Con Docker Compose (recomendado)

Desde la raíz del proyecto:

```bash
# Construir y levantar en segundo plano
docker compose -f deploy/docker-compose.yml up --build -d

# Ver estado (debe decir "healthy" tras unos segundos)
docker compose -f deploy/docker-compose.yml ps

# Ver logs
docker compose -f deploy/docker-compose.yml logs -f

# Detener y eliminar el contenedor
docker compose -f deploy/docker-compose.yml down
```

Usar otro puerto en el host (por ejemplo, 8080):

```bash
DASHBOARD_PORT=8080 docker compose -f deploy/docker-compose.yml up --build -d
```

## Solo con Docker

```bash
docker build -f deploy/Dockerfile -t dashboard-kpis:1.0.0 .
docker run -d --name dashboard-kpis -p 8501:8501 dashboard-kpis:1.0.0
docker stop dashboard-kpis && docker rm dashboard-kpis
```

## Qué entra en la imagen

Controlado por [`.dockerignore`](../.dockerignore). Solo se copian:

- `requirements.txt` (para instalar dependencias)
- `app/` (código del dashboard)
- `data/` (CSV con los datos simulados)
- `scripts/` (por si se quiere regenerar datos dentro del contenedor)
- `.streamlit/` (tema y configuración)

Quedan fuera: pruebas, documentación, entorno virtual, `.git` y archivos de
desarrollo.

## Notas para un despliegue en servidor (pendiente)

Aún no se despliega en servidor. Cuando se haga, conviene considerar:

- Poner un *proxy* inverso (Nginx o Caddy) con HTTPS delante del puerto 8501.
- Streamlit usa WebSockets: el proxy debe permitir `Upgrade`/`Connection`.
- No exponer el puerto 8501 directamente a internet; publicar solo `127.0.0.1:8501:8501`.
