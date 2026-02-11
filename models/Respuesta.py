from config.config import respuestas_collection, preguntas_collection
from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime

def guardar_respuestas(alumno_id, examen_id, respuestas):
    alumno_id = ObjectId(alumno_id)
    examen_id = ObjectId(examen_id)

    preguntas = list(preguntas_collection.find({"examen_id": examen_id}))
    correctas = 0

    for p in preguntas:
        r_alumno = respuestas.get(str(p["_id"]))
        if r_alumno == p.get("respuesta_correcta"):
            correctas += 1

    total = len(preguntas)
    calificacion = round((correctas / total) * 100, 2) if total > 0 else 0

    resultado = {
        "alumno_id": alumno_id,
        "examen_id": examen_id,
        "respuestas": respuestas,
        "correctas": correctas,
        "total": total,
        "calificacion": calificacion,
        "fecha": datetime.utcnow()
    }

    respuestas_collection.insert_one(resultado)

    return jsonify({
        "mensaje": "Respuestas guardadas",
        "calificacion": calificacion
    }), 201
