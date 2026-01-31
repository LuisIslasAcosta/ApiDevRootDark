from flask import Blueprint, jsonify
from models.models import User, Curso

estadisticas_bp = Blueprint("estadisticas_bp", __name__)

@estadisticas_bp.route("/estadisticas", methods=["GET"])
def obtener_estadisticas():
    try:
        total_usuarios = User.query.count()
        total_cursos = Curso.query.count()

        return jsonify({
            "usuarios_registrados": total_usuarios,
            "cursos_creados": total_cursos
        }), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener estadísticas: {str(e)}"}), 500