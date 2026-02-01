from config.config import inscripciones_collection, cursos_collection, usuarios_collection
from bson.objectid import ObjectId

def serializar_inscripcion(inscripcion):
    curso = cursos_collection.find_one({"_id": ObjectId(inscripcion["curso_id"])})
    alumno = usuarios_collection.find_one({"_id": ObjectId(inscripcion["alumno_id"])})
    return {
        "id": str(inscripcion["_id"]),
        "curso_id": inscripcion["curso_id"],
        "curso_nombre": curso["nombre"] if curso else "Desconocido",
        "alumno_id": inscripcion["alumno_id"],
        "alumno_nombre": alumno["nombre"] if alumno else "Desconocido"
    }

def obtener_inscripciones():
    inscripciones = inscripciones_collection.find()
    return [serializar_inscripcion(ins) for ins in inscripciones]

def obtener_inscripciones_por_curso(curso_id):
    inscripciones = inscripciones_collection.find({"curso_id": curso_id})
    return [serializar_inscripcion(ins) for ins in inscripciones]

def obtener_inscripciones_por_alumno(alumno_id):
    inscripciones = inscripciones_collection.find({"alumno_id": alumno_id})
    return [serializar_inscripcion(ins) for ins in inscripciones]