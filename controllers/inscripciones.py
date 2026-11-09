from config.config import inscripciones_collection, cursos_collection, usuarios_collection
from bson.objectid import ObjectId

def serializar_inscripcion(inscripcion):
    curso_id = str(inscripcion.get("curso_id", ""))
    alumno_id = str(inscripcion.get("alumno_id", ""))
    curso = cursos_collection.find_one({"_id": ObjectId(curso_id)}) if ObjectId.is_valid(curso_id) else None
    alumno = usuarios_collection.find_one({"_id": ObjectId(alumno_id)}) if ObjectId.is_valid(alumno_id) else None

    return {
        "id": str(inscripcion["_id"]),
        "curso_id": curso_id,
        "curso_nombre": curso["nombre"] if curso else "Desconocido",
        "alumno_id": alumno_id,
        "alumno_nombre": alumno.get("nombre", "Sin nombre") if alumno else "Usuario eliminado",
        "alumno_email": alumno.get("email", "") if alumno else ""
    }


def obtener_inscripciones():
    inscripciones = inscripciones_collection.find()
    return [serializar_inscripcion(ins) for ins in inscripciones]

def obtener_inscripciones_por_curso(curso_id):
    inscripciones = inscripciones_collection.find({"curso_id": {"$in": [curso_id] + ([ObjectId(curso_id)] if ObjectId.is_valid(curso_id) else [])}})
    return [serializar_inscripcion(ins) for ins in inscripciones]

def obtener_inscripciones_por_alumno(alumno_id):
    inscripciones = inscripciones_collection.find({"alumno_id": alumno_id})
    return [serializar_inscripcion(ins) for ins in inscripciones]