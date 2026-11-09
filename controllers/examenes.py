from config.config import examenes_collection, cursos_collection, preguntas_collection
from bson.objectid import ObjectId

def serializar_examen(examen):
    curso_id = str(examen.get("curso_id", ""))
    curso = cursos_collection.find_one({"_id": ObjectId(curso_id)}) if ObjectId.is_valid(curso_id) else None
    examen_id = str(examen["_id"])
    num_preguntas = preguntas_collection.count_documents({"examen_id": examen_id}) or len(examen.get("preguntas", []))
    return {
        "id": str(examen["_id"]),
        "curso_id": str(examen["curso_id"]),
        "curso_nombre": curso["nombre"] if curso else "Desconocido",
        "leccion_id": str(examen.get("leccion_id", "")),
        "nivel_id": str(examen.get("nivel_id", "")),
        "titulo": examen.get("titulo", ""),
        "fecha": examen.get("fecha", ""),
        "preguntas": examen.get("preguntas", []),
        "num_preguntas": num_preguntas
    }


def obtener_examenes():
    examenes = examenes_collection.find()
    return [serializar_examen(ex) for ex in examenes]

def obtener_examenes_por_curso(curso_id):
    # El curso_id puede estar guardado como texto o como ObjectId
    valores = [curso_id] + ([ObjectId(curso_id)] if ObjectId.is_valid(curso_id) else [])
    examenes = examenes_collection.find({"curso_id": {"$in": valores}})
    return [serializar_examen(ex) for ex in examenes]

def actualizar_examen(examen_id, datos):
    try:
        result = examenes_collection.update_one(
            {"_id": ObjectId(examen_id)},
            {"$set": datos}
        )
        return result.modified_count > 0
    except:
        return False
