#!/usr/bin/env bash
# Migra la API a un usuario sin privilegios y carpetas separadas (V-03).
# - Código:  /opt/devrootdark/api   (solo lectura para el servicio)
# - Datos:   /var/lib/devrootdark/{uploads,backups,comprobantes}
# - Usuario: devrootdark (sin shell, sin acceso a /home)
# Uso, desde la carpeta del repo en el servidor:  sudo bash deploy/instalar_seguro.sh
# Se puede ejecutar varias veces (también sirve para actualizar).
set -euo pipefail
[ "$(id -u)" -eq 0 ] || { echo "Ejecuta con sudo"; exit 1; }

REPO="$(cd "$(dirname "$0")/.." && pwd)"
APP=/opt/devrootdark/api
DATOS=/var/lib/devrootdark

id devrootdark >/dev/null 2>&1 || useradd --system --home-dir /nonexistent --shell /usr/sbin/nologin devrootdark
mkdir -p "$APP" "$DATOS"/{uploads,backups,comprobantes}

# 1) Código (sin datos, sin venv, sin .git)
rsync -a --delete \
  --exclude venv --exclude .git --exclude uploads --exclude backups --exclude comprobantes \
  --exclude __pycache__ --exclude reports --exclude tests/reports --exclude .env \
  "$REPO"/ "$APP"/

# 2) Datos: se copian una sola vez desde la carpeta anterior (no se borra nada del repo)
for d in uploads backups comprobantes; do
  if [ -d "$REPO/$d" ] && [ -z "$(ls -A "$DATOS/$d" 2>/dev/null)" ]; then
    cp -a "$REPO/$d"/. "$DATOS/$d"/
  fi
done

# 3) .env con las carpetas nuevas (se conserva el que ya tienes)
[ -f "$APP/.env" ] || cp "$REPO/.env" "$APP/.env"
for v in "UPLOADS_DIR=$DATOS/uploads" "BACKUPS_DIR=$DATOS/backups" "COMPROBANTES_DIR=$DATOS/comprobantes"; do
  clave="${v%%=*}"
  grep -q "^$clave=" "$APP/.env" && sed -i "s|^$clave=.*|$v|" "$APP/.env" || echo "$v" >> "$APP/.env"
done

# 4) Entorno de Python
[ -x "$APP/venv/bin/python" ] || python3 -m venv "$APP/venv"
"$APP/venv/bin/pip" install -q -r "$APP/requirements.txt"

# 5) Permisos: root es dueño del código; el servicio solo lee el código y escribe en sus datos
chown -R root:devrootdark "$APP"
chmod -R u=rwX,g=rX,o= "$APP"
chmod 640 "$APP/.env"
chown -R devrootdark:devrootdark "$DATOS"
chmod -R u=rwX,g=rX,o= "$DATOS"

# 6) Servicio
cp "$REPO/deploy/apidevrootdark.service" /etc/systemd/system/apidevrootdark.service
systemctl daemon-reload
systemctl enable --now apidevrootdark
systemctl restart apidevrootdark
sleep 3
systemctl is-active apidevrootdark && echo "API en línea como usuario devrootdark"
curl -fsS http://127.0.0.1:5000/api/cursos >/dev/null && echo "Responde en 127.0.0.1:5000"

echo
echo "Revisa qué publica Tailscale Funnel (solo debe aparecer el puerto 5000):"
tailscale funnel status || true
