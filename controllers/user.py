from config.config import usuarios_collection
from bson.objectid import ObjectId
import base64

def serializar_usuario(usuario):
    foto_perfil = usuario.get("foto_perfil")

    if isinstance(foto_perfil, bytes):
        foto_perfil = base64.b64encode(foto_perfil).decode("utf-8")

    return {
        "id": str(usuario["_id"]),
        "matricula": usuario.get("matricula"),
        "nombre": usuario.get("nombre"),
        "apellidop": usuario.get("apellidop"),
        "apellidom": usuario.get("apellidom"),
        "email": usuario.get("email"),
        "telefono": usuario.get("telefono"),
        "foto_perfil": foto_perfil,
        "rol": usuario.get("rol")
        # ❌ NO enviar password
    }


def obtener_usuarios():
    usuarios = usuarios_collection.find()
    return [serializar_usuario(usuario) for usuario in usuarios]


def obtener_usuario_por_id(usuario_id):
    usuario = usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    return serializar_usuario(usuario) if usuario else None


def actualizar_usuario(usuario_id, datos_actualizados):
    # Evitar que se actualice password aquí
    datos_actualizados.pop("password", None)

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
