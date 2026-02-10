from config.config import usuarios_collection
from bson.objectid import ObjectId
import base64

import base64

def serializar_usuario(usuario):
    """Serializa un documento de usuario de MongoDB a un diccionario de Python."""
    foto_perfil = usuario.get("foto_perfil")
    if isinstance(foto_perfil, bytes):  # si es binario, lo convierto a base64
        foto_perfil = base64.b64encode(foto_perfil).decode("utf-8")

    return {
        "id": str(usuario["_id"]),
        "matricula": usuario.get("matricula"),
        "nombre": usuario.get("nombre"),
        "apellidop": usuario.get("apellidop"),   # 🔹 apellido paterno
        "apellidom": usuario.get("apellidom"),   # 🔹 apellido materno
        "email": usuario.get("email"),
        "telefono": usuario.get("telefono"),
        "password": usuario.get("password"),
        "foto_perfil": foto_perfil,
        "rol": usuario.get("rol")                # 🔹 ahora sí devuelve el rol
    }
    
def obtener_usuarios():
    """Obtiene todos los usuarios de la base de datos."""
    usuarios = usuarios_collection.find()
    return [serializar_usuario(usuario) for usuario in usuarios]

def obtener_usuario_por_id(usuario_id):
    usuario = usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    return serializar_usuario(usuario) if usuario else None

def actualizar_usuario(usuario_id, datos_actualizados):
    resultado = usuarios_collection.update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": datos_actualizados}
    )
    return resultado.modified_count > 0

def eliminar_usuario(usuario_id):
    resultado = usuarios_collection.delete_one({"_id": ObjectId(usuario_id)})
    return resultado.deleted_count > 0

def obtener_usuarios_recientes(limit=5):
    usuarios = usuarios_collection.find().sort([("_id", -1)]).limit(limit)
    return [serializar_usuario(usuario) for usuario in usuarios]