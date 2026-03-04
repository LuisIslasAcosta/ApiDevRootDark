from config.config import cursos_collection
from bson.objectid import ObjectId

def serializar_curso(curso):
    return {
        "id": str(curso["_id"]),
        "nombre": curso["nombre"],
        "descripcion": curso["descripcion"],
        "profesor": curso["profesor"],
        "imagenes": curso.get("imagenes", []),
        "videos": curso.get("videos", [])
    }

def obtener_cursos():
    cursos = cursos_collection.find()
    return [serializar_curso(curso) for curso in cursos]

def obtener_curso_por_id(curso_id):
    curso = cursos_collection.find_one({"_id": ObjectId(curso_id)})
    return serializar_curso(curso) if curso else None

def actualizar_curso(curso_id, datos_actualizados):
    resultado = cursos_collection.update_one(
        {"_id": ObjectId(curso_id)},
        {"$set": datos_actualizados}
    )
    return resultado.modified_count > 0

def eliminar_curso(curso_id):
    resultado = cursos_collection.delete_one({"_id": ObjectId(curso_id)})
    return resultado.deleted_count > 0

def obtener_cursos_recientes(limit=5):
    cursos = cursos_collection.find().sort("_id", -1).limit(limit)
    return [serializar_curso(curso) for curso in cursos]