from config.config import respuestas_collection, examenes_collection
from bson.objectid import ObjectId

def obtener_resultados_por_alumno(alumno_id):
    alumno_id = ObjectId(alumno_id)

    resultados = respuestas_collection.find({"alumno_id": alumno_id})

    return [
        {
            "id": str(r["_id"]),
            "examen_id": str(r["examen_id"]),
            "examen_titulo": obtener_titulo_examen(r["examen_id"]),
            "calificacion": r.get("calificacion", 0),
            "correctas": r.get("correctas", 0),
            "total": r.get("total", 0)
        }
        for r in resultados
    ]

def obtener_titulo_examen(examen_id):
    try:
        examen = examenes_collection.find_one({"_id": ObjectId(examen_id)})
        return examen.get("titulo", "Examen sin título") if examen else "Examen eliminado"
    except:
        return "Examen no encontrado"
