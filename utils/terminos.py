"""Términos y condiciones con versión.

Cada usuario guarda la versión que aceptó (terminos_version). Si la versión vigente
cambia, el usuario debe aceptarla otra vez antes de seguir usando la plataforma.

Para publicar una actualización: cambia TERMINOS_VERSION en el archivo .env
(por ejemplo TERMINOS_VERSION=2027-01-15) y reinicia el servicio.
"""
import os
from datetime import datetime

from bson.objectid import ObjectId
from config.config import usuarios_collection

VERSION_POR_DEFECTO = "2026-11-12"


def version_vigente():
    return (os.getenv("TERMINOS_VERSION") or VERSION_POR_DEFECTO).strip()


def terminos_pendientes(usuario):
    """True si el usuario no ha aceptado la versión vigente."""
    return (usuario or {}).get("terminos_version") != version_vigente()


def info_pendiente(usuario):
    """Datos que necesita el frontend para mostrar la ventana de aceptación."""
    anterior = (usuario or {}).get("terminos_version")
    return {
        "codigo": "terminos_pendientes",
        "version": version_vigente(),
        "actualizacion": bool(anterior),  # ya había aceptado una versión anterior
        "mensaje": ("Actualizamos los términos y condiciones. Acéptalos para continuar."
                    if anterior else "Debes aceptar los términos y condiciones para continuar."),
    }


def registrar_aceptacion(usuario_id):
    version = version_vigente()
    ahora = datetime.utcnow()
    _id = usuario_id if isinstance(usuario_id, ObjectId) else ObjectId(str(usuario_id))
    usuarios_collection.update_one(
        {"_id": _id},
        {
            "$set": {"terminos_version": version, "terminos_aceptados_en": ahora},
            "$push": {"terminos_historial": {"version": version, "fecha": ahora}},
        },
    )
    return version
