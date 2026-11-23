from flask import Blueprint, jsonify
from controllers.predicciones import analizar_riesgo_curso
from utils.seguridad import exigir_gestion_curso, exigir_ver_alumno, sesion_requerida, solo_admin, staff_requerido, usuario_sesion, texto, exigir_acceso_curso

prediccion_bp = Blueprint("prediccion_bp", __name__)

@prediccion_bp.route("/prediccion/riesgo/<curso_id>", methods=["GET"])
@staff_requerido
def obtener_riesgo_academico(curso_id):
    problema = exigir_gestion_curso(curso_id)
    if problema:
        return problema
    try:
        resultado = analizar_riesgo_curso(curso_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al procesar predicción: {str(e)}"}), 500