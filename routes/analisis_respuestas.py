from flask import Blueprint, jsonify
from controllers.analisis_respuestas import analizar_respuestas

analisis_bp = Blueprint("analisis", __name__)

@analisis_bp.route("/respuestas/analisis/<alumno_id>", methods=["GET"])
def analisis_por_alumno(alumno_id):
    resultado = analizar_respuestas(alumno_id)
    return jsonify(resultado), 200
