from config.config import preguntas_collection
from bson.objectid import ObjectId

def serializar_pregunta(pregunta):
    return {
        "id": str(pregunta["_id"]),
        "examen_id": pregunta["examen_id"],
        "tipo": pregunta["tipo"],
        "enunciado": pregunta["enunciado"],
        "opciones": pregunta.get("opciones", [])
    }

def obtener_todas_preguntas():
    preguntas = preguntas_collection.find()
    return [serializar_pregunta(p) for p in preguntas]

def obtener_preguntas_por_examen(examen_id):
    preguntas = preguntas_collection.find({"examen_id": examen_id})
    return [serializar_pregunta(p) for p in preguntas]