from bson import ObjectId
from flask import Blueprint, request, jsonify, make_response
from config.config import lecciones_collection, niveles_collection
from models.Leccion import crear_leccion, eliminar_leccion
from controllers.lecciones import obtener_lecciones_por_curso, obtener_lecciones_por_nivel
from utils.archivos import MATERIAL_LECCION, ArchivoInvalido, agregar_permiso, borrar_archivo, guardar_varios
from utils.seguridad import (
    error, exigir_acceso_curso, exigir_gestion_curso, sesion_requerida, staff_requerido,
    texto, usuario_sesion,
)

leccion_bp = Blueprint("leccion_bp", __name__)


# =========================
# CREAR LECCIÓN (profesor dueño o admin)
# =========================
@leccion_bp.route("/lecciones", methods=["POST", "OPTIONS"])
@staff_requerido
def registrar():
    if request.method == "OPTIONS":
        return _preflight_response()

    curso_id = texto(request.form.get("curso_id"))
    nivel_id = texto(request.form.get("nivel_id")) or None
    titulo = texto(request.form.get("titulo"), 200)
    contenido = texto(request.form.get("contenido", ""), 20000)

    if not curso_id or not titulo:
        return error(400, "curso_id y titulo son obligatorios")
    problema = exigir_gestion_curso(curso_id)
    if problema:
        return problema

    try:
        # Tipo real revisado por firma, tamaño limitado y nombre aleatorio
        archivos_subidos = guardar_varios(request.files.getlist("archivos"), MATERIAL_LECCION)
    except ArchivoInvalido as e:
        return error(400, str(e))

    leccion = crear_leccion(curso_id, titulo, contenido, archivos_subidos, nivel_id)
    return jsonify(leccion), 201


# =========================
# LISTAR POR CURSO (con acceso al curso)
# =========================
@leccion_bp.route("/lecciones/curso/<curso_id>", methods=["GET", "OPTIONS"])
@sesion_requerida
def listar_por_curso(curso_id):
    if request.method == "OPTIONS":
        return _preflight_response()
    problema = exigir_acceso_curso(curso_id)
    if problema:
        return problema
    return jsonify(agregar_permiso(obtener_lecciones_por_curso(curso_id), curso_id, usuario_sesion())), 200


# =========================
# LISTAR POR NIVEL (con acceso al curso del nivel)
# =========================
@leccion_bp.route("/lecciones/nivel/<nivel_id>", methods=["GET", "OPTIONS"])
@sesion_requerida
def listar_por_nivel(nivel_id):
    if request.method == "OPTIONS":
        return _preflight_response()
    nivel = niveles_collection.find_one({"_id": ObjectId(nivel_id)}) if ObjectId.is_valid(nivel_id) else None
    if not nivel:
        return error(404, "Nivel no encontrado")
    problema = exigir_acceso_curso(nivel.get("curso_id"))
    if problema:
        return problema
    return jsonify(agregar_permiso(obtener_lecciones_por_nivel(nivel_id), nivel.get("curso_id"), usuario_sesion())), 200


# =========================
# ELIMINAR LECCIÓN (profesor dueño o admin)
# =========================
@leccion_bp.route("/lecciones/<leccion_id>", methods=["DELETE", "OPTIONS"])
@staff_requerido
def eliminar(leccion_id):
    if request.method == "OPTIONS":
        return _preflight_response()
    leccion = lecciones_collection.find_one({"_id": ObjectId(leccion_id)}) if ObjectId.is_valid(leccion_id) else None
    if not leccion:
        return error(404, "Lección no encontrada")
    problema = exigir_gestion_curso(leccion.get("curso_id"))
    if problema:
        return problema
    if eliminar_leccion(leccion_id):
        for nombre in leccion.get("archivos", []):
            if not lecciones_collection.find_one({"archivos": nombre}):
                borrar_archivo(nombre)
        return jsonify({"mensaje": "Lección eliminada correctamente"}), 200
    return jsonify({"mensaje": "No se pudo eliminar la lección"}), 400


def _preflight_response():
    # Los encabezados CORS los agrega flask_cors (configurado en app.py)
    return make_response("", 204)
