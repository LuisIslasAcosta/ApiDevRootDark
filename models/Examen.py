from config.config import examenes_collection
from flask import jsonify
from bson.objectid import ObjectId

def registrar_examen(curso_id, leccion_id, titulo, fecha):
    nuevo_examen = {
        "curso_id": curso_id,
        "leccion_id": leccion_id,
        "titulo": titulo,
        "fecha": fecha
    }

    try:
        resultado = examenes_collection.insert_one(nuevo_examen)

        return jsonify({
            "examen_id": str(resultado.inserted_id)
        }), 201

    except Exception as e:
        return jsonify({"mensaje": f"Error: {str(e)}"}), 500


def eliminar_examen(examen_id):
    resultado = examenes_collection.delete_one({"_id": ObjectId(examen_id)})
    return resultado.deleted_count > 0
