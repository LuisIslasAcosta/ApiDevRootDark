from config.config import examenes_collection, cursos_collection
from bson.objectid import ObjectId

def serializar_examen(examen):
    curso = cursos_collection.find_one({"_id": ObjectId(examen["curso_id"])})
    return {
        "id": str(examen["_id"]),
        "curso_id": examen["curso_id"],
        "curso_nombre": curso["nombre"] if curso else "Desconocido",
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