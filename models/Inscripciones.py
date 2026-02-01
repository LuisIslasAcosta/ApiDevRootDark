from config.config import inscripciones_collection
from flask import jsonify
from bson.objectid import ObjectId

def registrar_inscripcion(curso_id, alumno_id):
    nueva_inscripcion = {
        "curso_id": curso_id,
        "alumno_id": alumno_id
    }

    try:
        inscripciones_collection.insert_one(nueva_inscripcion)
        return jsonify({"mensaje": "Inscripción registrada correctamente"}), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar inscripción: {str(e)}"}), 500

def eliminar_inscripcion(inscripcion_id):
    resultado = inscripciones_collection.delete_one({"_id": ObjectId(inscripcion_id)})
    return resultado.deleted_count > 0