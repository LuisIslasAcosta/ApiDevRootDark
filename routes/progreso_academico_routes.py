from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from controllers.progreso_academico import progreso_alumno, alumnos_en_riesgo_profesor

progreso_academico_bp = Blueprint("progreso_academico_bp", __name__)


@progreso_academico_bp.route("/progreso/alumno", methods=["GET"])
@jwt_required()
def get_progreso_alumno():
    """Progreso por curso, riesgos, consejos y cursos recomendados del alumno que inició sesión."""
    resultado = progreso_alumno(str(get_jwt_identity()))
    if "error" in resultado:
        return jsonify(resultado), 500
    return jsonify(resultado), 200


@progreso_academico_bp.route("/progreso/profesor/riesgo", methods=["GET"])
@jwt_required()
def get_alumnos_en_riesgo():
    """Alumnos de los cursos del profesor en riesgo de reprobar o abandonar, con recomendaciones."""
    incluir_todos = request.args.get("todos", "false").lower() == "true"
    resultado = alumnos_en_riesgo_profesor(str(get_jwt_identity()), incluir_todos)
    if "error" in resultado:
        return jsonify(resultado), 500
    return jsonify(resultado), 200
