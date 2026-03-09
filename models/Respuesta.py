from config.config import preguntas_collection, respuestas_collection
from bson.objectid import ObjectId
from flask import jsonify

def guardar_respuestas(alumno_id, examen_id, respuestas):

    preguntas = list(preguntas_collection.find({"examen_id": examen_id}))

    correctas = 0
    total = len(preguntas)

    for pregunta in preguntas:

        pregunta_id = str(pregunta["_id"])
        respuesta_usuario = respuestas.get(pregunta_id)

        respuesta_correcta = pregunta.get("respuesta_correcta")

        if respuesta_usuario and respuesta_correcta:

            if respuesta_usuario.strip().lower() == respuesta_correcta.strip().lower():
                correctas += 1

    calificacion = 0

    if total > 0:
        calificacion = round((correctas / total) * 100)

    respuestas_collection.insert_one({
        "alumno_id": ObjectId(alumno_id),
        "examen_id": examen_id,
        "correctas": correctas,
        "total": total,
        "calificacion": calificacion
    })

    return jsonify({
        "mensaje": "Examen enviado",
        "correctas": correctas,
        "total": total,
        "calificacion": calificacion
    }), 201