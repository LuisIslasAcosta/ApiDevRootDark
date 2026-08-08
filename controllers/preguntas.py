from config.config import preguntas_collection, examenes_collection
from bson.objectid import ObjectId

def serializar_pregunta(pregunta):
    # PRIORIZAR el campo 'id' sobre '_id' para mantener consistencia con el frontend
    pregunta_id = pregunta.get("id")
    if pregunta_id is None:
        # Si no hay campo 'id', usar '_id' como respaldo
        pregunta_id = str(pregunta["_id"])
    else:
        # Si existe 'id', convertirlo a string
        pregunta_id = str(pregunta_id)
    
    return {
        "id": pregunta_id,
        "examen_id": pregunta["examen_id"],
        "tipo": pregunta.get("tipo", "multiple"),
        "enunciado": pregunta.get("enunciado", ""),
        "opciones": pregunta.get("opciones", [])
    }

def obtener_todas_preguntas():
    preguntas = preguntas_collection.find()
    return [serializar_pregunta(p) for p in preguntas]

def obtener_preguntas_por_examen(examen_id):
    # Primero buscar en la colección de preguntas separada
    preguntas = list(preguntas_collection.find({"examen_id": examen_id}))
    
    # Si no hay preguntas en la colección separada, buscar en el campo del examen
    if not preguntas:
        try:
            examen = examenes_collection.find_one({"_id": ObjectId(examen_id)})
            if examen and examen.get("preguntas"):
                # Convertir las preguntas del examen al formato esperado
                # Usar el índice como ID para mantener consistencia
                preguntas = [
                    {
                        "_id": ObjectId(),
                        "id": str(idx),  # ID consistente basado en el índice
                        "examen_id": examen_id,
                        "tipo": p.get("tipo", "multiple"),
                        "enunciado": p.get("enunciado", ""),
                        "opciones": p.get("opciones", []),
                        "respuesta_correcta": p.get("respuesta_correcta", "")
                    }
                    for idx, p in enumerate(examen["preguntas"])
                ]
        except:
            pass
    
    return [serializar_pregunta(p) for p in preguntas]
