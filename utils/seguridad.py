"""Utilidades de seguridad: acceso solo para administradores y bitácora de acciones sensibles."""
from datetime import datetime, timezone
from functools import wraps

from bson.objectid import ObjectId
from flask import jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from config.config import db, usuarios_collection

auditoria_collection = db["auditoria_respaldos"]


def _usuario_actual():
    usuario_id = str(get_jwt_identity() or "")
    if not ObjectId.is_valid(usuario_id):
        return None
    return usuarios_collection.find_one({"_id": ObjectId(usuario_id)}, {"rol": 1, "email": 1})


def registrar_auditoria(accion, detalle="", exito=True):
    """Guarda quién hizo qué, cuándo y desde dónde (no debe romper la petición si falla)."""
    try:
        usuario = _usuario_actual() or {}
        auditoria_collection.insert_one({
            "accion": accion,
            "detalle": detalle,
            "exito": exito,
            "usuario_id": str(usuario.get("_id", "")),
            "email": usuario.get("email", ""),
            "ip": request.headers.get("X-Forwarded-For", request.remote_addr),
            "fecha": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:  # la bitácora nunca debe tumbar la operación
        print(f"No se pudo registrar la auditoría: {e}")


def admin_requerido(accion):
    """Exige token JWT válido y rol administrador. Registra cada intento en la bitácora."""
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            try:
                verify_jwt_in_request()
            except Exception:
                return jsonify({"message": "Inicia sesión como administrador"}), 401

            usuario = _usuario_actual()
            if not usuario or usuario.get("rol") != "administrador":
                registrar_auditoria(accion, "Acceso denegado: el usuario no es administrador", exito=False)
                return jsonify({"message": "Solo el administrador puede usar los respaldos"}), 403

            respuesta = funcion(*args, **kwargs)
            codigo = respuesta[1] if isinstance(respuesta, tuple) and len(respuesta) > 1 else getattr(respuesta, "status_code", 200)
            registrar_auditoria(accion, str(kwargs) if kwargs else "", exito=int(codigo) < 400)
            return respuesta
        return envoltura
    return decorador
