from config.config import cursos_collection
from flask import jsonify

def registrar_curso(nombre, descripcion, profesor, imagenes=None, videos=None):
    # Verificar si ya existe un curso con el mismo nombre
    if cursos_collection.find_one({"nombre": nombre}):
        return jsonify({"mensaje": "El curso ya existe"}), 400

    nuevo_curso = {
        "nombre": nombre,
        "descripcion": descripcion,
        "profesor": profesor,
        "imagenes": imagenes if imagenes else [],
        "videos": videos if videos else []
    }

    try:
        resultado = cursos_collection.insert_one(nuevo_curso)
        nuevo_curso["_id"] = str(resultado.inserted_id)
        return jsonify({"mensaje": "Curso registrado correctamente", "curso": nuevo_curso}), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar curso: {str(e)}"}), 500