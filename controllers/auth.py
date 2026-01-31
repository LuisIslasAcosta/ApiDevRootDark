import base64
from models.models import User
from utils.hash_utils import verificar_contraseña
from flask_jwt_extended import create_access_token

def validar_login(email, password):
    usuario = User.query.filter_by(email=email).first()
    if usuario and verificar_contraseña(usuario.password, password):
        access_token = create_access_token(identity=usuario.id)

        foto_perfil = usuario.foto_perfil
        if isinstance(foto_perfil, (bytes, bytearray)):
            foto_perfil = base64.b64encode(foto_perfil).decode("utf-8")

        return {
            "access_token": access_token,
            "usuario": {
                "id": usuario.id,
                "nombre": usuario.nombre,
                "email": usuario.email,
                "foto_perfil": foto_perfil,
                "rol": usuario.rol
            }
        }
    return None