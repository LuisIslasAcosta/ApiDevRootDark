from config.config import niveles_collection
from datetime import datetime

def crear_nivel(curso_id, titulo, descripcion="", orden=1):
    nivel = {
        "curso_id": curso_id,
        "titulo": titulo,
        "descripcion": descripcion,
        "orden": orden,
        "fecha_creacion": datetime.utcnow()
    }
    niveles_collection.insert_one(nivel)
    return {"ok": True, "mensaje": "Nivel creado"}
