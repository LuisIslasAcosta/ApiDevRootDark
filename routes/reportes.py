from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.reportes import obtener_reportes_profesor

reportes_bp = Blueprint("reportes_bp", __name__)

@reportes_bp.route("/reportes/profesor", methods=["GET"])
@jwt_required()
def reportes_profesor():
    profesor_id = get_jwt_identity()

    datos = obtener_reportes_profesor(profesor_id)
    return jsonify(datos), 200
