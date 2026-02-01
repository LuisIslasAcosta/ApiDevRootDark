from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from models.Pregunta import registrar_pregunta, eliminar_pregunta
from controllers.preguntas import obtener_preguntas_por_examen, obtener_todas_preguntas

pregunta_bp = Blueprint("pregunta_bp", __name__)

@pregunta_bp.route("/preguntas", methods=["POST"])
def registrar():
    datos = request.json
    examen_id = datos.get("examen_id")
    tipo = datos.get("tipo")
    enunciado = datos.get("enunciado")
    opciones = datos.get("opciones", [])

    if not examen_id or not tipo or not enunciado:
        return jsonify({"mensaje": "Examen, tipo y enunciado son obligatorios"}), 400

    return registrar_pregunta(examen_id, tipo, enunciado, opciones)

@pregunta_bp.route("/preguntas/<pregunta_id>", methods=["DELETE"])
def eliminar(pregunta_id):
    try:
        exito = eliminar_pregunta(pregunta_id)
        if exito:
            return jsonify({"mensaje": "Pregunta eliminada correctamente"}), 200
        else:
            return jsonify({"mensaje": "No se pudo eliminar la pregunta"}), 400
    except InvalidId:
        return jsonify({"mensaje": "ID de pregunta inválido"}), 400

@pregunta_bp.route("/preguntas", methods=["GET"])
def listar():
    return jsonify(obtener_todas_preguntas()), 200

@pregunta_bp.route("/preguntas/examen/<examen_id>", methods=["GET"])
def listar_por_examen(examen_id):
    return jsonify(obtener_preguntas_por_examen(examen_id)), 200