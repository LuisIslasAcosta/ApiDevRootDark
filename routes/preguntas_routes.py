from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from config.config import preguntas_collection
from models.Pregunta import registrar_pregunta, eliminar_pregunta
from controllers.preguntas import obtener_todas_preguntas, obtener_preguntas_por_examen

pregunta_bp = Blueprint("pregunta_bp", __name__)

@pregunta_bp.route("/preguntas", methods=["POST"])
def registrar():
    if not request.is_json:
        return jsonify({"mensaje": "El cuerpo debe ser JSON"}), 415

    datos = request.get_json()
    examen_id = datos.get("examen_id")
    tipo = datos.get("tipo")
    enunciado = datos.get("enunciado")
    opciones = datos.get("opciones", [])

    if not examen_id or not tipo or not enunciado:
        return jsonify({"mensaje": "Examen, tipo y enunciado son obligatorios"}), 400

    nueva_pregunta = {
        "examen_id": examen_id,
        "tipo": tipo,
        "enunciado": enunciado,
        "opciones": opciones
    }
    preguntas_collection.insert_one(nueva_pregunta)
    return jsonify({"mensaje": "Pregunta registrada correctamente"}), 201

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