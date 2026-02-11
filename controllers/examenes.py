from config.config import examenes_collection, cursos_collection
from bson.objectid import ObjectId

def serializar_examen(examen):
    curso = cursos_collection.find_one({"_id": ObjectId(examen["curso_id"])})
    return {
        "id": str(examen["_id"]),
        "curso_id": examen["curso_id"],
        "curso_nombre": curso["nombre"] if curso else "Desconocido",
        "leccion_id": examen.get("leccion_id"),  # <-- nuevo
        "titulo": examen["titulo"],
        "fecha": examen["fecha"],
        "preguntas": examen.get("preguntas", [])
    }


def obtener_examenes():
    examenes = examenes_collection.find()
    return [serializar_examen(ex) for ex in examenes]

def obtener_examenes_por_curso(curso_id):
    examenes = examenes_collection.find({"curso_id": curso_id})
    return [serializar_examen(ex) for ex in examenes]

def actualizar_examen(examen_id, datos):
    result = examenes_collection.update_one(
        {"_id": ObjectId(examen_id)},
        {"$set": datos}
    )
    return result.modified_count > 0
