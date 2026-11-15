"""Música predeterminada de DevRootMusic.

Las canciones viven en uploads/musica/. Cada canción puede tener audio (.mp3) y
video (.mp4) con el mismo nombre: "Mi_cancion.mp3" + "Mi_cancion.mp4" = una sola canción.
- GET  /api/musica            lista pública (la ven todos los usuarios del reproductor)
- POST /api/musica            el administrador sube una canción nueva
- DELETE /api/musica/<archivo> el administrador la quita
"""
import os
import re

from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

from utils.seguridad import admin_requerido

musica_bp = Blueprint("musica_bp", __name__)

CARPETA_MUSICA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads", "musica")
EXT_AUDIO = {"mp3", "m4a", "ogg"}
EXT_VIDEO = {"mp4", "webm"}


def _titulo(nombre):
    """'Overclocked_Redline' -> 'Overclocked Redline'."""
    return re.sub(r"[_\-]+", " ", nombre).strip()


def listar_canciones():
    if not os.path.isdir(CARPETA_MUSICA):
        return []
    canciones = {}
    for archivo in sorted(os.listdir(CARPETA_MUSICA)):
        base, _, ext = archivo.rpartition(".")
        ext = ext.lower()
        if not base or ext not in EXT_AUDIO | EXT_VIDEO:
            continue
        c = canciones.setdefault(base, {"id": base, "titulo": _titulo(base), "audio": None, "video": None})
        c["audio" if ext in EXT_AUDIO else "video"] = f"musica/{archivo}"
    return sorted(canciones.values(), key=lambda c: c["titulo"].lower())


@musica_bp.route("/musica", methods=["GET"])
def listar():
    return jsonify(listar_canciones()), 200


@musica_bp.route("/musica", methods=["POST"])
@admin_requerido("subir_musica")
def subir():
    archivos = request.files.getlist("archivos")
    if not archivos:
        return jsonify({"mensaje": "Selecciona al menos un archivo .mp3 o .mp4"}), 400
    os.makedirs(CARPETA_MUSICA, exist_ok=True)
    guardados, rechazados = [], []
    for archivo in archivos:
        nombre = secure_filename(archivo.filename or "")
        ext = nombre.rsplit(".", 1)[-1].lower() if "." in nombre else ""
        if not nombre or ext not in EXT_AUDIO | EXT_VIDEO:
            rechazados.append(archivo.filename or "sin nombre")
            continue
        archivo.save(os.path.join(CARPETA_MUSICA, nombre))
        guardados.append(nombre)
    codigo = 201 if guardados else 400
    return jsonify({"guardados": guardados, "rechazados": rechazados, "canciones": listar_canciones()}), codigo


@musica_bp.route("/musica/<archivo>", methods=["DELETE"])
@admin_requerido("borrar_musica")
def borrar(archivo):
    nombre = secure_filename(archivo)
    ruta = os.path.join(CARPETA_MUSICA, nombre)
    if not nombre or not os.path.isfile(ruta):
        return jsonify({"mensaje": "No existe ese archivo"}), 404
    os.remove(ruta)
    return jsonify({"mensaje": "Archivo eliminado", "canciones": listar_canciones()}), 200
