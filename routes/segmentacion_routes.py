from flask import Blueprint, jsonify
from controllers.segmentacion import segmentar_estudiantes_curso

segmentacion_bp = Blueprint("segmentacion_bp", __name__)

@segmentacion_bp.route("/analisis/segmentacion/<curso_id>", methods=["GET"])
def obtener_segmentacion(curso_id):
    try:
        resultado = segmentar_estudiantes_curso(curso_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al procesar segmentación: {str(e)}"}), 500