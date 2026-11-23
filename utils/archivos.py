"""Subida y entrega segura de archivos.

- El tipo real del archivo se revisa por sus primeros bytes (firma), no por la extensión.
- Límite de tamaño por tipo.
- Nombre aleatorio (uuid) para que no se pueda adivinar la ruta.
- Carpeta configurable con UPLOADS_DIR (recomendado: fuera de la carpeta del código,
  p. ej. /var/lib/devrootdark/uploads).
- Los archivos de lecciones solo se entregan con un permiso firmado (?acceso=...) que
  la API da a quien tiene acceso al curso (alumno aceptado, profesor dueño o admin).
"""
import os
import uuid

from flask import current_app, jsonify, request, send_from_directory
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

from config.config import lecciones_collection

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UPLOADS_DIR = os.path.abspath(os.getenv("UPLOADS_DIR") or os.path.join(BASE_DIR, "uploads"))

MB = 1024 * 1024
# tipo -> (subcarpeta, extensión, tamaño máximo)
TIPOS = {
    "png": ("imagenes", "png", 10 * MB),
    "jpg": ("imagenes", "jpg", 10 * MB),
    "gif": ("imagenes", "gif", 10 * MB),
    "webp": ("imagenes", "webp", 10 * MB),
    "pdf": ("pdfs", "pdf", 50 * MB),
    "mp4": ("videos", "mp4", 1024 * MB),
    "webm": ("videos", "webm", 1024 * MB),
    "mp3": ("musica", "mp3", 50 * MB),
}
IMAGENES = {"png", "jpg", "gif", "webp"}
VIDEOS = {"mp4", "webm"}
MATERIAL_LECCION = IMAGENES | VIDEOS | {"pdf"}

EXTENSIONES_ENTREGABLES = {"png", "jpg", "jpeg", "gif", "webp", "mp4", "webm", "pdf", "mp3", "m4a", "ogg"}
DURACION_ACCESO = 12 * 3600  # segundos que vale el permiso de los archivos de un curso

for _sub in ("imagenes", "videos", "pdfs", "musica"):
    os.makedirs(os.path.join(UPLOADS_DIR, _sub), exist_ok=True)


class ArchivoInvalido(ValueError):
    pass


def detectar_tipo(cabecera: bytes):
    """Tipo real según la firma del archivo (magic bytes)."""
    if cabecera.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if cabecera.startswith(b"\xff\xd8\xff"):
        return "jpg"
    if cabecera[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if cabecera[:4] == b"RIFF" and cabecera[8:12] == b"WEBP":
        return "webp"
    if cabecera.startswith(b"%PDF-"):
        return "pdf"
    if cabecera[4:8] == b"ftyp":
        return "mp4"
    if cabecera.startswith(b"\x1a\x45\xdf\xa3"):
        return "webm"
    if cabecera.startswith(b"OggS"):
        return "ogg"
    if cabecera.startswith(b"ID3") or cabecera[:2] in (b"\xff\xfb", b"\xff\xf3", b"\xff\xf2"):
        return "mp3"
    return None


def _tamano(archivo):
    flujo = archivo.stream
    flujo.seek(0, os.SEEK_END)
    tamano = flujo.tell()
    flujo.seek(0)
    return tamano


def guardar_archivo(archivo, permitidos):
    """Valida y guarda un archivo subido. Devuelve el nombre aleatorio con el que quedó.

    Lanza ArchivoInvalido si el tipo real no está permitido o excede el tamaño.
    """
    if not archivo or not getattr(archivo, "filename", ""):
        raise ArchivoInvalido("Archivo vacío")
    cabecera = archivo.stream.read(16)
    archivo.stream.seek(0)
    tipo = detectar_tipo(cabecera)
    if tipo not in permitidos:
        raise ArchivoInvalido(f"Tipo de archivo no permitido: {archivo.filename}")
    subcarpeta, extension, maximo = TIPOS[tipo]
    if _tamano(archivo) > maximo:
        raise ArchivoInvalido(f"El archivo {archivo.filename} supera {maximo // MB} MB")
    nombre = f"{uuid.uuid4().hex}.{extension}"
    archivo.save(os.path.join(UPLOADS_DIR, subcarpeta, nombre))
    return nombre


def guardar_varios(archivos, permitidos):
    """Guarda una lista; si alguno es inválido, borra los ya guardados y lanza el error."""
    guardados = []
    try:
        for archivo in archivos:
            if archivo and archivo.filename:
                guardados.append(guardar_archivo(archivo, permitidos))
    except ArchivoInvalido:
        for nombre in guardados:
            borrar_archivo(nombre)
        raise
    return guardados


def ruta_archivo(nombre):
    extension = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
    for subcarpeta, ext, _ in TIPOS.values():
        if ext == extension:
            return os.path.join(UPLOADS_DIR, subcarpeta, nombre)
    return os.path.join(UPLOADS_DIR, nombre)


def borrar_archivo(nombre):
    try:
        os.remove(ruta_archivo(os.path.basename(nombre)))
    except OSError:
        pass


# ================= PERMISO FIRMADO PARA ARCHIVOS DE LECCIONES =================
def _firmador():
    return URLSafeTimedSerializer(current_app.config["JWT_SECRET_KEY"], salt="archivos-curso")


def firmar_acceso(curso_id, usuario_id):
    return _firmador().dumps({"c": str(curso_id), "u": str(usuario_id)})


def curso_del_permiso(permiso):
    try:
        datos = _firmador().loads(permiso or "", max_age=DURACION_ACCESO)
        return str(datos.get("c", ""))
    except (BadSignature, SignatureExpired, AttributeError):
        return None


def leccion_con_archivo(nombre):
    return lecciones_collection.find_one({"archivos": nombre}, {"curso_id": 1})


def agregar_permiso(lecciones, curso_id, usuario):
    """Añade a cada lección el permiso para descargar sus archivos."""
    permiso = firmar_acceso(curso_id, usuario["_id"])
    for leccion in lecciones:
        leccion["acceso"] = permiso
    return lecciones


def entregar(ruta):
    """Entrega un archivo de uploads (ruta relativa, p. ej. "videos/abc.mp4").

    Si pertenece a una lección, exige el permiso firmado ?acceso=... de ese curso.
    send_from_directory impide salir de la carpeta (../).
    """
    nombre = os.path.basename(ruta)
    extension = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
    if extension not in EXTENSIONES_ENTREGABLES:
        return jsonify({"mensaje": "Archivo no disponible"}), 404
    leccion = leccion_con_archivo(nombre)
    if leccion:
        curso = curso_del_permiso(request.args.get("acceso"))
        if not curso or curso != str(leccion.get("curso_id")):
            return jsonify({"mensaje": "Necesitas estar inscrito en el curso para ver este archivo"}), 403
    respuesta = send_from_directory(UPLOADS_DIR, ruta, conditional=True)
    respuesta.headers["Cache-Control"] = "private, max-age=3600" if leccion else "public, max-age=86400"
    return respuesta
