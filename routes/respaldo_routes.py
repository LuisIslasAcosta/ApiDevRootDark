# routes/respaldo_routes.py
from flask import Blueprint, request, jsonify
from controllers.respaldo_controller import configurar_respaldo
from controllers.respaldo_controller import generar_respaldo, restaurar_respaldo

respaldo_bp = Blueprint("respaldo", __name__)

@respaldo_bp.route("/respaldo", methods=["GET"])
def descargar_respaldo():
    return generar_respaldo()

@respaldo_bp.route("/respaldo", methods=["POST"])
def subir_respaldo():
    return restaurar_respaldo()

@respaldo_bp.route("/config-respaldo", methods=["POST", "OPTIONS"])
def config_respaldo():
    if request.method == "POST":
        return configurar_respaldo()
    return jsonify({"status": "ok"}), 200 