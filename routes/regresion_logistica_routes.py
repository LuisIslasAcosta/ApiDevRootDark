from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.regresion_logistica import analizar_regresion_logistica

regresion_logistica_bp = Blueprint("regresion_logistica", __name__)

@regresion_logistica_bp.route("/analisis/regresion-logistica", methods=["GET"])
@jwt_required()
def regresion_logistica_route():
    profesor_id = get_jwt_identity()
    resultado = analizar_regresion_logistica(profesor_id)
    return jsonify(resultado), 200