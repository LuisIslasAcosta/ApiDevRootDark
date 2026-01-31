from flask import Blueprint, request, jsonify
from controllers.respaldo import (
    configurar_respaldo,
    generar_respaldo,
    restaurar_respaldo,
)

respaldo_bp = Blueprint("respaldo_bp", __name__)

# Descargar respaldo (genera un .sql con mysqldump)
@respaldo_bp.route("/respaldo", methods=["GET"])
def descargar_respaldo():
    return generar_respaldo()

# Subir respaldo (restaura la BD desde un archivo .sql)
@respaldo_bp.route("/respaldo", methods=["POST"])
def subir_respaldo():
    return restaurar_respaldo()

# Configurar respaldo automático con APScheduler
@respaldo_bp.route("/config-respaldo", methods=["POST", "OPTIONS"])
def config_respaldo():
    if request.method == "POST":
        return configurar_respaldo()
    return jsonify({"status": "ok"}), 200