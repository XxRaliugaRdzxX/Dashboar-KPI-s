# ---------------------------------------------------------------------------
# Imagen del Dashboard de KPIs (Streamlit + Bokeh)
# Construir desde la RAÍZ del proyecto:
#   docker build -f deploy/Dockerfile -t dashboard-kpis .
# ---------------------------------------------------------------------------
FROM python:3.12-slim

# Python sin archivos .pyc, logs sin búfer y pip sin caché (imagen más ligera)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Usuario sin privilegios: el contenedor no corre como root
RUN useradd --create-home --uid 10001 appuser

# 1) Dependencias primero: esta capa se reutiliza mientras requirements.txt no cambie
COPY requirements.txt .
RUN pip install -r requirements.txt

# 2) Código, configuración y datos
COPY --chown=appuser:appuser .streamlit/ .streamlit/
COPY --chown=appuser:appuser app/ app/
COPY --chown=appuser:appuser scripts/ scripts/
COPY --chown=appuser:appuser data/ data/

USER appuser

EXPOSE 8501

# Docker marca el contenedor como "healthy" cuando Streamlit responde
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=4)" || exit 1

CMD ["streamlit", "run", "app/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
