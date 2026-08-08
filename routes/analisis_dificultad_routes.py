from flask import Blueprint, jsonify
from controllers.analisis_dificultad import analizar_dificultad_curso

analisis_dificultad_bp = Blueprint("analisis_dificultad_bp", __name__)

@analisis_dificultad_bp.route("/analisis/dificultad/<curso_id>", methods=["GET"])
def obtener_analisis_dificultad(curso_id):
    try:
        resultado = analizar_dificultad_curso(curso_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al procesar el análisis de dificultad: {str(e)}"}), 500