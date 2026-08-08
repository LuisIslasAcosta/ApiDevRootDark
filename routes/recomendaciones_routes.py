from flask import Blueprint, jsonify
from controllers.recomendaciones import generar_recomendaciones_por_curso, generar_recomendaciones_para_alumno

recomendacion_bp = Blueprint("recomendacion_bp", __name__)

@recomendacion_bp.route("/recomendaciones/curso/<curso_id>", methods=["GET"])
def obtener_recomendaciones_por_curso(curso_id):
    try:
        resultado = generar_recomendaciones_por_curso(curso_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al generar recomendaciones por curso: {str(e)}"}), 500

@recomendacion_bp.route("/recomendaciones/alumno/<alumno_id>", methods=["GET"])
def obtener_recomendaciones_para_alumno(alumno_id):
    try:
        resultado = generar_recomendaciones_para_alumno(alumno_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al generar recomendaciones para alumno: {str(e)}"}), 500