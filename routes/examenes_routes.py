from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from models.Examen import registrar_examen, eliminar_examen
from controllers.examenes import obtener_examenes, obtener_examenes_por_curso

examen_bp = Blueprint("examen_bp", __name__)

@examen_bp.route("/examenes", methods=["POST"])
def registrar():
    datos = request.json
    curso_id = datos.get("curso_id")
    titulo = datos.get("titulo")
    fecha = datos.get("fecha")
    preguntas = datos.get("preguntas", [])

    if not curso_id or not titulo or not fecha:
        return jsonify({"mensaje": "Curso, título y fecha son obligatorios"}), 400

    return registrar_examen(curso_id, titulo, fecha, preguntas)

@examen_bp.route("/examenes/<examen_id>", methods=["DELETE"])
def eliminar(examen_id):
    try:
        exito = eliminar_examen(examen_id)
        if exito:
            return jsonify({"mensaje": "Examen eliminado correctamente"}), 200
        else:
            return jsonify({"mensaje": "No se pudo eliminar el examen"}), 400
    except InvalidId:
        return jsonify({"mensaje": "ID de examen inválido"}), 400

@examen_bp.route("/examenes", methods=["GET"])
def listar():
    return jsonify(obtener_examenes()), 200

@examen_bp.route("/examenes/curso/<curso_id>", methods=["GET"])
def listar_por_curso(curso_id):
    return jsonify(obtener_examenes_por_curso(curso_id)), 200