from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.seguridad import staff_requerido
from controllers.ventas import analizar_ventas

ventas_bp = Blueprint("ventas", __name__)


@ventas_bp.route("/ventas", methods=["GET"])
@staff_requerido
def ventas_route():
    try:
        profesor_id = get_jwt_identity()

        resultado = analizar_ventas(profesor_id)

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500