from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from controllers.progreso_academico import (
    progreso_alumno,
    alumnos_en_riesgo_profesor,
    progreso_alumno_curso,
    resumen_cursos,
)

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


@progreso_academico_bp.route("/progreso/alumno/curso/<curso_id>", methods=["GET"])
@jwt_required()
def get_progreso_alumno_curso(curso_id):
    """Progreso del alumno que inició sesión dentro de un curso (lecciones vistas, calificaciones)."""
    resultado = progreso_alumno_curso(str(get_jwt_identity()), curso_id)
    if "error" in resultado:
        return jsonify(resultado), 404
    return jsonify(resultado), 200


@progreso_academico_bp.route("/progreso/cursos/resumen", methods=["GET"])
@jwt_required()
def get_resumen_cursos():
    """Alumnos, contenido y desempeño por curso (profesor: sus cursos; administrador: todos)."""
    resultado = resumen_cursos(str(get_jwt_identity()))
    if "error" in resultado:
        return jsonify(resultado), 500
    return jsonify(resultado), 200
