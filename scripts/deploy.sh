#!/usr/bin/env bash
# ---------------------------------------------------------------------------
# Despliegue del Dashboard de KPIs con Docker Compose.
#
# Uso:
#   ./scripts/deploy.sh <comando> [opciones]
#
# Comandos:
#   up        Construye la imagen, levanta el contenedor y espera a que esté "healthy"
#   down      Detiene y elimina el contenedor
#   restart   Reinicia el contenedor (sin reconstruir la imagen)
#   logs      Muestra los logs en vivo (Ctrl+C para salir)
#   status    Muestra el estado del contenedor y su healthcheck
#
# Opciones (para "up"):
#   --local       Publica el puerto solo en 127.0.0.1 (no visible desde la red)
#   --port N      Puerto del host (default: 8501)
#
# Ejemplos:
#   ./scripts/deploy.sh up --local
#   ./scripts/deploy.sh up --port 8080
#   ./scripts/deploy.sh status
# ---------------------------------------------------------------------------
set -euo pipefail

# Rutas: el script funciona sin importar desde qué carpeta se ejecute
RAIZ="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$RAIZ/deploy/docker-compose.yml"
CONTENEDOR="dashboard-kpis"
ESPERA_MAX=90   # segundos máximos esperando el estado "healthy"

# Colores solo si la salida es una terminal
if [[ -t 1 ]]; then
  VERDE=$'\e[32m'; ROJO=$'\e[31m'; AMARILLO=$'\e[33m'; NEGRITA=$'\e[1m'; NORMAL=$'\e[0m'
else
  VERDE=""; ROJO=""; AMARILLO=""; NEGRITA=""; NORMAL=""
fi

info()  { echo "${NEGRITA}==>${NORMAL} $*"; }
ok()    { echo "${VERDE}✔${NORMAL} $*"; }
aviso() { echo "${AMARILLO}!${NORMAL} $*"; }
error() { echo "${ROJO}✘ $*${NORMAL}" >&2; exit 1; }

uso() { sed -n '3,22p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'; }

compose() { docker compose -f "$COMPOSE_FILE" "$@"; }

# ---------------------------------------------------------------------------
# Verificación de requisitos
# ---------------------------------------------------------------------------
verificar_requisitos() {
  info "Verificando requisitos"
  command -v docker >/dev/null 2>&1 \
    || error "Docker no está instalado. Ver https://docs.docker.com/engine/install/"
  ok "Docker $(docker version --format '{{.Client.Version}}' 2>/dev/null)"

  docker compose version >/dev/null 2>&1 \
    || error "Falta el plugin 'docker compose' (Compose v2)."
  ok "Docker Compose $(docker compose version --short)"

  docker info >/dev/null 2>&1 \
    || error "El daemon de Docker no responde. ¿Está iniciado? (sudo systemctl start docker) ¿Tu usuario está en el grupo 'docker'?"
  ok "Daemon de Docker activo"

  [[ -f "$COMPOSE_FILE" ]] || error "No se encontró $COMPOSE_FILE"
}

# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------
estado_salud() {
  docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' \
    "$CONTENEDOR" 2>/dev/null || echo "no existe"
}

cmd_up() {
  local host="0.0.0.0" puerto="8501"
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --local) host="127.0.0.1"; shift ;;
      --port)
        [[ "${2:-}" =~ ^[0-9]+$ ]] || error "--port requiere un número"
        puerto="$2"; shift 2 ;;
      *) error "Opción desconocida para 'up': $1" ;;
    esac
  done

  verificar_requisitos

  info "Construyendo y levantando el contenedor"
  DASHBOARD_HOST="$host" DASHBOARD_PORT="$puerto" compose up --build -d

  info "Esperando a que el dashboard esté listo (máx. ${ESPERA_MAX}s)"
  local transcurrido=0 estado
  while (( transcurrido < ESPERA_MAX )); do
    estado="$(estado_salud)"
    case "$estado" in
      healthy) break ;;
      unhealthy|exited|dead)
        compose logs --tail 30
        error "El contenedor quedó en estado '$estado'." ;;
    esac
    sleep 3; transcurrido=$(( transcurrido + 3 ))
  done
  [[ "$(estado_salud)" == "healthy" ]] \
    || error "Tiempo agotado: el contenedor no llegó a 'healthy'. Revisa: $0 logs"

  ok "Dashboard en línea: ${NEGRITA}http://localhost:${puerto}${NORMAL}"
  if [[ "$host" == "0.0.0.0" ]]; then
    aviso "El puerto es visible desde tu red local. Usa --local para limitarlo a esta máquina."
  else
    ok "Publicado solo en 127.0.0.1 (no visible desde la red)"
  fi
}

cmd_down()    { verificar_requisitos; info "Deteniendo el contenedor"; compose down; ok "Contenedor detenido"; }
cmd_restart() { verificar_requisitos; info "Reiniciando el contenedor"; compose restart; ok "Reiniciado. Estado: $(estado_salud)"; }
cmd_logs()    { compose logs -f --tail 100; }

cmd_status() {
  verificar_requisitos
  info "Estado"
  compose ps
  echo "Healthcheck: $(estado_salud)"
}

# ---------------------------------------------------------------------------
# Punto de entrada
# ---------------------------------------------------------------------------
comando="${1:-}"
[[ $# -gt 0 ]] && shift
case "$comando" in
  up)      cmd_up "$@" ;;
  down)    cmd_down ;;
  restart) cmd_restart ;;
  logs)    cmd_logs ;;
  status)  cmd_status ;;
  -h|--help|help|"") uso ;;
  *) echo "Comando desconocido: $comando" >&2; uso; exit 1 ;;
esac
