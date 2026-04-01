from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from controllers.ventas import analizar_ventas

ventas_bp = Blueprint("ventas", __name__)


@ventas_bp.route("/api/ventas", methods=["GET"])
def ventas_route():
    try:
        verify_jwt_in_request()
        profesor_id = get_jwt_identity()

        resultado = analizar_ventas(profesor_id)

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500