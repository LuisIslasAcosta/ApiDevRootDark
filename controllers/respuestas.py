from config.config import respuestas_collection
from bson.objectid import ObjectId

def obtener_resultados_por_alumno(alumno_id):
    alumno_id = ObjectId(alumno_id)

    resultados = respuestas_collection.find({"alumno_id": alumno_id})

    return [
        {
            "id": str(r["_id"]),
            "examen_id": str(r["examen_id"]),
            "calificacion": r.get("calificacion", 0),
            "correctas": r.get("correctas", 0),
            "total": r.get("total", 0)
        }
        for r in resultados
    ]
