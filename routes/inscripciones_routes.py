from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from models.Inscripciones import registrar_inscripcion, eliminar_inscripcion
from controllers.inscripciones import obtener_inscripciones, obtener_inscripciones_por_curso, obtener_inscripciones_por_alumno

inscripcion_bp = Blueprint("inscripcion_bp", __name__)

@inscripcion_bp.route("/inscripciones", methods=["POST"])
def registrar():
    datos = request.json
    curso_id = datos.get("curso_id")
    alumno_id = datos.get("alumno_id")

    if not curso_id or not alumno_id:
        return jsonify({"mensaje": "Curso y alumno son obligatorios"}), 400

    return registrar_inscripcion(curso_id, alumno_id)

@inscripcion_bp.route("/inscripciones/<inscripcion_id>", methods=["DELETE"])
def eliminar(inscripcion_id):
    try:
        exito = eliminar_inscripcion(inscripcion_id)
        if exito:
            return jsonify({"mensaje": "Inscripción eliminada correctamente"}), 200
        else:
            return jsonify({"mensaje": "No se pudo eliminar la inscripción"}), 400
    except InvalidId:
        return jsonify({"mensaje": "ID de inscripción inválido"}), 400

@inscripcion_bp.route("/inscripciones", methods=["GET"])
def listar():
    return jsonify(obtener_inscripciones()), 200

@inscripcion_bp.route("/inscripciones/curso/<curso_id>", methods=["GET"])
def listar_por_curso(curso_id):
    return jsonify(obtener_inscripciones_por_curso(curso_id)), 200

@inscripcion_bp.route("/inscripciones/alumno/<alumno_id>", methods=["GET"])
def listar_por_alumno(alumno_id):
    return jsonify(obtener_inscripciones_por_alumno(alumno_id)), 200