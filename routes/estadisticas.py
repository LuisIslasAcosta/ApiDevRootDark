from flask import Blueprint, jsonify
from config.config import usuarios_collection, cursos_collection
from utils.seguridad import exigir_gestion_curso, exigir_ver_alumno, sesion_requerida, solo_admin, staff_requerido, usuario_sesion, texto, exigir_acceso_curso

estadisticas_bp = Blueprint("estadisticas_bp", __name__)

@estadisticas_bp.route("/estadisticas", methods=["GET"])
@solo_admin
def obtener_estadisticas():
    try:
        total_usuarios = usuarios_collection.count_documents({})
        total_cursos = cursos_collection.count_documents({})

        return jsonify({
            "usuarios_registrados": total_usuarios,
            "cursos_creados": total_cursos
        }), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener estadísticas: {str(e)}"}), 500