from config.config import lecciones_collection
from flask import jsonify

def registrar_leccion(curso_id, titulo, contenido, recursos=None):
    nueva_leccion = {
        "curso_id": curso_id,
        "titulo": titulo,
        "contenido": contenido,
        "recursos": recursos if recursos else []
    }

    try:
        lecciones_collection.insert_one(nueva_leccion)
        return jsonify({"mensaje": "Lección creada correctamente"}), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error: {str(e)}"}), 500
