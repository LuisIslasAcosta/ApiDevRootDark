from config.config import examenes_collection
from flask import jsonify
from bson.objectid import ObjectId

def registrar_examen(curso_id, titulo, fecha, preguntas):
    nuevo_examen = {
        "curso_id": curso_id,
        "titulo": titulo,
        "fecha": fecha,
        "preguntas": preguntas
    }

    try:
        examenes_collection.insert_one(nuevo_examen)
        return jsonify({"mensaje": "Examen registrado correctamente"}), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar examen: {str(e)}"}), 500

def eliminar_examen(examen_id):
    resultado = examenes_collection.delete_one({"_id": ObjectId(examen_id)})
    return resultado.deleted_count > 0