from config.config import niveles_collection
from bson import ObjectId

def _id_flexible(valor):
    """Coincide con el id guardado como texto o como ObjectId."""
    valor = str(valor)
    return {"$in": [valor] + ([ObjectId(valor)] if ObjectId.is_valid(valor) else [])}


def serializar_nivel(n):
    return {
        "id": str(n["_id"]),
        "curso_id": str(n["curso_id"]),
        "titulo": n["titulo"],
        "orden": n.get("orden", 1)
    }


def obtener_niveles_por_curso(curso_id):
    niveles = niveles_collection.find({"curso_id": _id_flexible(curso_id)}).sort("orden", 1)
    return [serializar_nivel(n) for n in niveles]

def eliminar_nivel(nivel_id):
    result = niveles_collection.delete_one({"_id": ObjectId(nivel_id)})
    return result.deleted_count > 0
