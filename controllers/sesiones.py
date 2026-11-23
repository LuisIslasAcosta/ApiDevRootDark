"""Sesiones: tokens de acceso cortos, tokens de renovación revocables y límite de intentos.

- El token de acceso dura poco (30 min). Si se lo roban, deja de servir pronto.
- El token de renovación (7 días) se guarda en la colección `sesiones`; se puede revocar
  (cerrar sesión, cambio de contraseña) y se cambia por uno nuevo en cada renovación.
- El inicio de sesión y la recuperación de contraseña tienen límite de intentos fallidos.
"""
from datetime import datetime, timedelta, timezone

from flask import request
from flask_jwt_extended import create_access_token, create_refresh_token, decode_token

from config.config import db

sesiones_collection = db["sesiones"]
intentos_collection = db["intentos_acceso"]

DURACION_ACCESO = timedelta(minutes=30)
DURACION_RENOVACION = timedelta(days=7)
VENTANA_FRESCA = timedelta(minutes=10)     # tiempo en que el token cuenta como "recién iniciado"
MAX_INTENTOS = 5
VENTANA_INTENTOS = timedelta(minutes=15)


def ahora():
    return datetime.now(timezone.utc)


def _utc(fecha):
    return fecha if fecha is None or fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


# ================= TOKENS =================
def crear_tokens(usuario_id, fresco=True):
    """Token de acceso y token de renovación registrado en la base de datos."""
    usuario_id = str(usuario_id)
    acceso = create_access_token(identity=usuario_id, fresh=VENTANA_FRESCA if fresco else False)
    renovacion = create_refresh_token(identity=usuario_id)
    datos = decode_token(renovacion)
    sesiones_collection.insert_one({
        "jti": datos["jti"],
        "usuario_id": usuario_id,
        "creada": ahora(),
        "expira": ahora() + DURACION_RENOVACION,
        "ip": (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip(),
        "agente": (request.headers.get("User-Agent") or "")[:200],
    })
    return acceso, renovacion


def renovacion_vigente(jti):
    sesion = sesiones_collection.find_one({"jti": jti})
    return bool(sesion) and _utc(sesion["expira"]) > ahora()


def rotar(jti, usuario_id):
    """Cambia el token de renovación usado por uno nuevo (el anterior deja de servir)."""
    sesiones_collection.delete_one({"jti": jti})
    return crear_tokens(usuario_id, fresco=False)


def revocar_token(token_renovacion):
    try:
        datos = decode_token(token_renovacion, allow_expired=True)
        sesiones_collection.delete_one({"jti": datos.get("jti")})
    except Exception:
        pass


def revocar_todas(usuario_id):
    """Cierra todas las sesiones del usuario (por ejemplo, al cambiar su contraseña)."""
    sesiones_collection.delete_many({"usuario_id": str(usuario_id)})


# ================= LÍMITE DE INTENTOS =================
def _clave(tipo, identificador):
    return f"{tipo}:{str(identificador).lower()}"


def bloqueado(tipo, identificador):
    """Minutos que faltan si se superó el límite de intentos fallidos; 0 si puede intentar."""
    registro = intentos_collection.find_one({"clave": _clave(tipo, identificador)})
    if not registro:
        return 0
    inicio = _utc(registro.get("inicio"))
    if not inicio or ahora() - inicio > VENTANA_INTENTOS:
        intentos_collection.delete_one({"_id": registro["_id"]})
        return 0
    if registro.get("fallos", 0) >= MAX_INTENTOS:
        restante = VENTANA_INTENTOS - (ahora() - inicio)
        return max(1, int(restante.total_seconds() // 60) + 1)
    return 0


def registrar_fallo(tipo, identificador):
    clave = _clave(tipo, identificador)
    registro = intentos_collection.find_one({"clave": clave})
    if not registro:
        intentos_collection.insert_one({"clave": clave, "fallos": 1, "inicio": ahora()})
    else:
        intentos_collection.update_one({"_id": registro["_id"]}, {"$inc": {"fallos": 1}})


def limpiar_intentos(tipo, identificador):
    intentos_collection.delete_many({"clave": _clave(tipo, identificador)})
