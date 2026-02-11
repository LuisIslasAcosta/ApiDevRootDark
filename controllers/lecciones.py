from config.config import lecciones_collection
from bson.objectid import ObjectId

# =========================
# SERIALIZAR LECCIÓN
# =========================
def serializar_leccion(leccion):
    return {
        "id": str(leccion["_id"]),
        "curso_id": leccion.get("curso_id"),
        "nivel_id": leccion.get("nivel_id"),
        "titulo": leccion.get("titulo"),
        "contenido": leccion.get("contenido", ""),
        "archivos": leccion.get("archivos", [])
    }

# =========================
# CREAR LECCIÓN
# =========================
def crear_leccion(curso_id, titulo, contenido, archivos=[], nivel_id=None):
    leccion = {
        "curso_id": curso_id,
        "nivel_id": nivel_id,
        "titulo": titulo,
        "contenido": contenido,
        "archivos": archivos
    }
    result = lecciones_collection.insert_one(leccion)
    leccion["_id"] = result.inserted_id
    return serializar_leccion(leccion)

# =========================
# ELIMINAR LECCIÓN
# =========================
def eliminar_leccion(leccion_id):
    result = lecciones_collection.delete_one({"_id": ObjectId(leccion_id)})
    return result.deleted_count > 0

# =========================
# OBTENER LECCIONES POR CURSO
# =========================
def obtener_lecciones_por_curso(curso_id):
    lecciones = lecciones_collection.find({"curso_id": curso_id})
    return [serializar_leccion(l) for l in lecciones]

# =========================
# OBTENER LECCIONES POR NIVEL
# =========================
def obtener_lecciones_por_nivel(nivel_id):
    lecciones = lecciones_collection.find({"nivel_id": nivel_id})
    return [serializar_leccion(l) for l in lecciones]

