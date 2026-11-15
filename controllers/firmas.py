"""Firma autógrafa de cada profesor para sus certificados.

- El profesor dibuja o sube su firma; se guarda como PNG transparente.
- Se guarda en una colección aparte (no en el usuario) para no cargarla en cada consulta.
- Al emitir un certificado se copia la firma vigente: si el profesor la cambia después,
  los certificados ya emitidos conservan la firma con la que salieron.
"""
import base64
import binascii
import hashlib
import struct
from datetime import datetime, timezone

from bson.objectid import ObjectId

from config.config import db, usuarios_collection

firmas_collection = db["firmas"]

PREFIJO = "data:image/png;base64,"
TAMANO_MAXIMO = 200 * 1024        # 200 KB
LADO_MAXIMO = 2000                # px
ROLES_CON_FIRMA = ("profesor", "administrador")


class ErrorFirma(Exception):
    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def _rol(usuario_id):
    if not ObjectId.is_valid(str(usuario_id)):
        return None
    usuario = usuarios_collection.find_one({"_id": ObjectId(str(usuario_id))})
    return (usuario or {}).get("rol")


def validar_png(data_url):
    """Comprueba que sea un PNG real, pequeño y de tamaño razonable. Devuelve los bytes."""
    if not isinstance(data_url, str) or not data_url.startswith(PREFIJO):
        raise ErrorFirma("La firma debe ser una imagen PNG.")
    try:
        datos = base64.b64decode(data_url[len(PREFIJO):], validate=True)
    except (binascii.Error, ValueError):
        raise ErrorFirma("La imagen de la firma está dañada.")
    if len(datos) > TAMANO_MAXIMO:
        raise ErrorFirma("La firma es demasiado pesada (máximo 200 KB).")
    if len(datos) < 33 or datos[:8] != b"\x89PNG\r\n\x1a\n" or datos[12:16] != b"IHDR":
        raise ErrorFirma("La firma debe ser una imagen PNG.")
    ancho, alto = struct.unpack(">II", datos[16:24])
    if not (20 <= ancho <= LADO_MAXIMO and 10 <= alto <= LADO_MAXIMO):
        raise ErrorFirma("El tamaño de la imagen de la firma no es válido.")
    return datos


def guardar_firma(usuario_id, data_url):
    if _rol(usuario_id) not in ROLES_CON_FIRMA:
        raise ErrorFirma("Solo los profesores pueden registrar una firma.", 403)
    datos = validar_png(data_url)
    huella = hashlib.sha256(datos).hexdigest()
    firmas_collection.update_one(
        {"profesor_id": str(usuario_id)},
        {"$set": {
            "profesor_id": str(usuario_id),
            "imagen": data_url,
            "huella": huella,
            "actualizada": datetime.now(timezone.utc),
        }},
        upsert=True,
    )
    return {"mensaje": "Firma guardada", "huella": huella[:12].upper()}


def obtener_firma(profesor_id):
    """Firma vigente del profesor (o None)."""
    if not profesor_id:
        return None
    return firmas_collection.find_one({"profesor_id": str(profesor_id)})


def mi_firma(usuario_id):
    firma = obtener_firma(usuario_id)
    if not firma:
        return {"firma": None}
    return {
        "firma": firma["imagen"],
        "huella": firma["huella"][:12].upper(),
        "actualizada": firma["actualizada"].isoformat() if firma.get("actualizada") else None,
    }


def borrar_firma(usuario_id):
    firmas_collection.delete_one({"profesor_id": str(usuario_id)})
    return {"mensaje": "Firma eliminada"}


def codigo_firma(folio, huella):
    """Código corto que liga la firma con ese certificado (se imprime debajo de la firma)."""
    if not huella:
        return None
    return hashlib.sha256(f"{folio}|{huella}".encode()).hexdigest()[:10].upper()
