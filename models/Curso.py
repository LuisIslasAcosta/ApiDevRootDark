from config.config import cursos_collection
from flask import jsonify

def registrar_curso(nombre, descripcion, profesor, precio, imagenes=None, videos=None):

    if cursos_collection.find_one({"nombre": nombre}):
        return jsonify({"mensaje": "El curso ya existe"}), 400

    try:
        nuevo_curso = {
            "nombre": nombre,
            "descripcion": descripcion,
            "profesor": profesor,
            "precio": float(precio) if precio else 0,
            "imagenes": imagenes if imagenes else [],
            "videos": videos if videos else []
        }

        resultado = cursos_collection.insert_one(nuevo_curso)
        nuevo_curso["_id"] = str(resultado.inserted_id)

        return jsonify({
            "mensaje": "Curso registrado correctamente",
            "curso": nuevo_curso
        }), 201

    except Exception as e:
        return jsonify({
            "mensaje": f"Error al registrar curso: {str(e)}"
        }), 500