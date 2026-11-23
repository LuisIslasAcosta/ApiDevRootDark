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
        #  NO enviar password
    }


def obtener_usuarios():
    usuarios = usuarios_collection.find()
    return [serializar_usuario(usuario) for usuario in usuarios]


def obtener_usuario_por_id(usuario_id):
    usuario = usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    return serializar_usuario(usuario) if usuario else None


# Datos que el propio usuario puede cambiar de su perfil
CAMPOS_PERFIL = ("nombre", "apellidop", "apellidom", "telefono", "foto_perfil", "pais", "ciudad")
ROLES_VALIDOS = ("usuario", "profesor", "administrador")


def actualizar_usuario(usuario_id, datos_actualizados, como_admin=False):
    """Actualiza solo campos permitidos. El rol únicamente lo cambia un administrador.

    Nunca se actualizan aquí la contraseña, el _id, la matrícula ni la verificación del correo
    (evita que alguien se asigne el rol de administrador mandando campos extra).
    """
    datos_actualizados = datos_actualizados if isinstance(datos_actualizados, dict) else {}
    cambios = {}
    for campo in CAMPOS_PERFIL:
        valor = datos_actualizados.get(campo)
        if isinstance(valor, str):
            cambios[campo] = valor.strip()[:3_000_000 if campo == "foto_perfil" else 120]
    if como_admin and datos_actualizados.get("rol") in ROLES_VALIDOS:
        cambios["rol"] = datos_actualizados["rol"]
    if not cambios:
        return False

    resultado = usuarios_collection.update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": cambios}
    )

    return resultado.modified_count > 0


def eliminar_usuario(usuario_id):
    resultado = usuarios_collection.delete_one({"_id": ObjectId(usuario_id)})
    return resultado.deleted_count > 0


def obtener_usuarios_recientes(limit=5):
    usuarios = usuarios_collection.find().sort([("_id", -1)]).limit(limit)
    return [serializar_usuario(usuario) for usuario in usuarios]
