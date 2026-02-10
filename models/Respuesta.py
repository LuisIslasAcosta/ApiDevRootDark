from config.config import respuestas_collection
from flask import jsonify

def guardar_respuesta(alumno_id, examen_id, respuestas, calificacion):
    intento = {
        "alumno_id": alumno_id,
        "examen_id": examen_id,
        "respuestas": respuestas,
        "calificacion": calificacion
    }

    respuestas_collection.insert_one(intento)
    return jsonify({"mensaje": "Respuestas guardadas"}), 201
