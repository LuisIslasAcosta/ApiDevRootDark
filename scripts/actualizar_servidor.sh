#!/usr/bin/env bash
# Actualiza la API en el servidor sin perder el archivo .env (que no está en el repositorio).
# Uso (en el servidor):  bash scripts/actualizar_servidor.sh
set -e
cd "$(dirname "$0")/.."
cp .env ~/env-respaldo-devrootdark
git pull origin api
cp ~/env-respaldo-devrootdark .env
./venv/bin/pip install -q -r requirements.txt
sudo systemctl restart apidevrootdark
sleep 2
systemctl is-active apidevrootdark && echo "API actualizada y en línea"
