from config.config import preguntas_collection
from flask import jsonify
from bson.objectid import ObjectId

def registrar_pregunta(examen_id, tipo, enunciado, opciones, respuesta_correcta):
    nueva_pregunta = {
        "examen_id": examen_id,
        "tipo": tipo,
        "enunciado": enunciado,
        "opciones": opciones,
        "respuesta_correcta": respuesta_correcta
    }

    try:
        preguntas_collection.insert_one(nueva_pregunta)
        return jsonify({"mensaje": "Pregunta creada"}), 201
    except Exception as e:
        return jsonify({"mensaje": str(e)}), 500


def eliminar_pregunta(pregunta_id):
    resultado = preguntas_collection.delete_one({"_id": ObjectId(pregunta_id)})
    return resultado.deleted_count > 0