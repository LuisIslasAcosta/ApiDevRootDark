from flask import Blueprint, jsonify
from controllers.analisis_respuestas import analizar_respuestas
from utils.seguridad import exigir_gestion_curso, exigir_ver_alumno, sesion_requerida, solo_admin, staff_requerido, usuario_sesion, texto, exigir_acceso_curso

analisis_bp = Blueprint("analisis", __name__)

@analisis_bp.route("/respuestas/analisis/<alumno_id>", methods=["GET"])
@sesion_requerida
def analisis_por_alumno(alumno_id):
    problema = exigir_ver_alumno(alumno_id)
    if problema:
        return problema
    resultado = analizar_respuestas(alumno_id)
    return jsonify(resultado), 200
