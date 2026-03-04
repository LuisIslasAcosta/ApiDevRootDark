from flask import Blueprint, request, jsonify
from models.Respuesta import guardar_respuestas
from controllers.respuestas import obtener_resultados_por_alumno

respuesta_bp = Blueprint("respuesta_bp", __name__)

@respuesta_bp.route("/respuestas", methods=["POST"])
def registrar():
    datos = request.json
    return guardar_respuestas(
        alumno_id=datos.get("alumno_id"),
        examen_id=datos.get("examen_id"),
        respuestas=datos.get("respuestas")
    )

@respuesta_bp.route("/respuestas/alumno/<alumno_id>", methods=["GET"])
def listar_por_alumno(alumno_id):
    return jsonify(obtener_resultados_por_alumno(alumno_id)), 200
