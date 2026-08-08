from flask import Blueprint, jsonify
from controllers.predicciones import analizar_riesgo_curso

prediccion_bp = Blueprint("prediccion_bp", __name__)

@prediccion_bp.route("/prediccion/riesgo/<curso_id>", methods=["GET"])
def obtener_riesgo_academico(curso_id):
    try:
        resultado = analizar_riesgo_curso(curso_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al procesar predicción: {str(e)}"}), 500