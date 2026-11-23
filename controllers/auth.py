import re
from config.config import usuarios_collection
from utils.hash_utils import verificar_hash
from controllers.sesiones import crear_tokens
from utils.terminos import terminos_pendientes, info_pendiente, registrar_aceptacion, version_vigente
import base64

def validar_login(email, password, acepta_terminos=False):
    email = email if isinstance(email, str) else ""
    password = password if isinstance(password, str) else ""
    usuario = usuarios_collection.find_one(
        {"email": {"$regex": f"^{re.escape((email or '').strip())}$", "$options": "i"}}
    )

    if not usuario:
        return None

    #  Verificar contraseña correctamente
    if not usuario.get("password") or not verificar_hash(password, usuario["password"]):
        return None

    #  Cuentas nuevas: deben confirmar su correo antes de entrar
    #  (las cuentas antiguas no tienen el campo y siguen funcionando)
    if usuario.get("verificado") is False:
        return {"error": "correo_no_verificado", "email": usuario.get("email")}

    #  Términos y condiciones: hay que aceptar la versión vigente para entrar
    resultado = revisar_terminos(usuario, acepta_terminos)
    if resultado:
        return resultado

    return respuesta_login(usuario)


def revisar_terminos(usuario, acepta_terminos):
    """None si puede entrar; si no, el aviso de términos pendientes."""
    if not terminos_pendientes(usuario):
        return None
    if acepta_terminos is True:
        usuario["terminos_version"] = registrar_aceptacion(usuario["_id"])
        return None
    return {"error": "terminos_pendientes", **info_pendiente(usuario)}


def respuesta_login(usuario):
    """Token JWT y datos públicos del usuario (login normal y con Google)."""
    # Token de acceso corto (fresco: recién inició sesión) y token de renovación revocable
    access_token, refresh_token = crear_tokens(usuario["_id"], fresco=True)

    foto_perfil = usuario.get("foto_perfil")
    if isinstance(foto_perfil, bytes):
        foto_perfil = base64.b64encode(foto_perfil).decode("utf-8")
    # Cuentas de Google: su foto de perfil (URL) si no subieron una propia
    foto_perfil = foto_perfil or usuario.get("foto_url")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "usuario": {
            "id": str(usuario["_id"]),
            "nombre": usuario.get("nombre"),
            "email": usuario.get("email"),
            "foto_perfil": foto_perfil,
            "rol": usuario.get("rol", "usuario"),
            "terminos_version": usuario.get("terminos_version") or version_vigente(),
        }
    }
