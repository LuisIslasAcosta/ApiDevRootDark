from config.config import cursos_collection
from config.config import  usuarios_collection
from bson.objectid import ObjectId

def serializar_curso(curso):
    profesor_id = str(curso["profesor"])
    
    print(f" Buscando profesor con ID: {profesor_id}")
    
    usuario = usuarios_collection.find_one({"_id": ObjectId(profesor_id)})
    
    nombre_profesor = "Desconocido"
    if usuario:
        nombre_profesor = f"{usuario.get('nombre', '')} {usuario.get('apellidop', '')}"
        print(f" Profesor encontrado: {nombre_profesor}")
    else:
        print(f" Profesor NO encontrado para ID: {profesor_id}")

    return {
        "id": str(curso["_id"]),
        "nombre": curso["nombre"],
        "descripcion": curso["descripcion"],
        "profesor": nombre_profesor,  
        "profesor_id": profesor_id,   
        "precio": curso.get("precio", 0),
        "imagenes": curso.get("imagenes", []),
        "videos": curso.get("videos", [])
    }

def obtener_cursos():
    cursos = cursos_collection.find()
    return [serializar_curso(curso) for curso in cursos]

def obtener_curso_por_id(curso_id):
    curso = cursos_collection.find_one({"_id": ObjectId(curso_id)})
    return serializar_curso(curso) if curso else None

def actualizar_curso(curso_id, datos_actualizados):
    resultado = cursos_collection.update_one(
        {"_id": ObjectId(curso_id)},
        {"$set": datos_actualizados}
    )
    return resultado.modified_count > 0

def eliminar_curso(curso_id):
    resultado = cursos_collection.delete_one({"_id": ObjectId(curso_id)})
    return resultado.deleted_count > 0

def obtener_cursos_recientes(limit=5):
    cursos = cursos_collection.find().sort("_id", -1).limit(limit)
    return [serializar_curso(curso) for curso in cursos]