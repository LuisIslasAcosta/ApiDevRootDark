from flask import Blueprint, request, jsonify
from controllers.calificacion import calificar_examen
from models.Respuesta import guardar_respuesta

respuesta_bp = Blueprint("respuesta_bp", __name__)

@respuesta_bp.route("/examenes/enviar", methods=["POST"])
def enviar():
    datos = request.json

    alumno_id = datos.get("alumno_id")
    examen_id = datos.get("examen_id")
    respuestas = datos.get("respuestas")

    calificacion = calificar_examen(examen_id, respuestas)

    return guardar_respuesta(alumno_id, examen_id, respuestas, calificacion)
