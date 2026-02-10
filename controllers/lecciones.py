from config.config import lecciones_collection
from bson.objectid import ObjectId

def serializar_leccion(leccion):
    return {
        "id": str(leccion["_id"]),
        "curso_id": leccion["curso_id"],
        "titulo": leccion["titulo"],
        "contenido": leccion["contenido"],
        "recursos": leccion.get("recursos", [])
    }

def obtener_lecciones_por_curso(curso_id):
    lecciones = lecciones_collection.find({"curso_id": curso_id})
    return [serializar_leccion(l) for l in lecciones]
