from config.config import usuarios_collection
from utils.hash_utils import verificar_contraseña
from flask_jwt_extended import create_access_token
import base64

def validar_login(email, password):
    usuario = usuarios_collection.find_one({"email": email})
    if usuario and verificar_contraseña(usuario["password"], password):
        access_token = create_access_token(identity=str(usuario["_id"]))

        foto_perfil = usuario.get("foto_perfil")
        if isinstance(foto_perfil, bytes):
            foto_perfil = base64.b64encode(foto_perfil).decode("utf-8")

        rol = usuario.get("rol", "usuario")

        return {
            "access_token": access_token,
            "usuario": {
                "id": str(usuario["_id"]),
                "nombre": usuario["nombre"],
                "email": usuario["email"],
                "foto_perfil": foto_perfil,
                "rol": rol
            }
        }
    return None