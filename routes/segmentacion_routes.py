from flask import Blueprint, jsonify
from controllers.segmentacion import segmentar_estudiantes_curso
from utils.seguridad import exigir_gestion_curso, exigir_ver_alumno, sesion_requerida, solo_admin, staff_requerido, usuario_sesion, texto, exigir_acceso_curso

segmentacion_bp = Blueprint("segmentacion_bp", __name__)

@segmentacion_bp.route("/analisis/segmentacion/<curso_id>", methods=["GET"])
@staff_requerido
def obtener_segmentacion(curso_id):
    problema = exigir_gestion_curso(curso_id)
    if problema:
        return problema
    try:
        resultado = segmentar_estudiantes_curso(curso_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al procesar segmentación: {str(e)}"}), 500