from bson import ObjectId
from flask import Blueprint, request, jsonify
from config.config import niveles_collection
from models.Nivel import crear_nivel
from controllers.niveles import obtener_niveles_por_curso, eliminar_nivel
from controllers.lecciones import obtener_lecciones_por_nivel
from utils.archivos import agregar_permiso
from utils.seguridad import (
    error, exigir_acceso_curso, exigir_gestion_curso, sesion_requerida, staff_requerido,
    texto, usuario_sesion,
)

nivel_bp = Blueprint("nivel_bp", __name__)


# =========================
# CREAR UN NUEVO NIVEL (profesor dueño o admin)
# =========================
@nivel_bp.route("/niveles", methods=["POST"])
@staff_requerido
def registrar():
    datos = request.get_json(silent=True) or {}
    curso_id = texto(datos.get("curso_id"))
    problema = exigir_gestion_curso(curso_id)
    if problema:
        return problema
    try:
        orden = int(datos.get("orden", 1))
    except (TypeError, ValueError):
        orden = 1
    return crear_nivel(
        curso_id=curso_id,
        titulo=texto(datos.get("titulo"), 200),
        descripcion=texto(datos.get("descripcion", ""), 2000),
        orden=orden,
    )


# =========================
# LISTAR NIVELES DE UN CURSO (solo títulos: público, sirve como temario)
# =========================
@nivel_bp.route("/niveles/curso/<curso_id>", methods=["GET"])
def listar_por_curso(curso_id):
    return jsonify(obtener_niveles_por_curso(curso_id)), 200


# =========================
# LISTAR NIVELES CON SUS LECCIONES (solo con acceso al curso)
# =========================
@nivel_bp.route("/niveles/curso/<curso_id>/con_lecciones", methods=["GET"])
@sesion_requerida
def listar_por_curso_con_lecciones(curso_id):
    problema = exigir_acceso_curso(curso_id)
    if problema:
        return problema
    niveles = obtener_niveles_por_curso(curso_id)
    for nivel in niveles:
        nivel["lecciones"] = agregar_permiso(obtener_lecciones_por_nivel(nivel["id"]), curso_id, usuario_sesion())
    return jsonify(niveles), 200


# =========================
# ELIMINAR UN NIVEL (profesor dueño o admin)
# =========================
@nivel_bp.route("/niveles/<nivel_id>", methods=["DELETE"])
@staff_requerido
def eliminar_nivel_route(nivel_id):
    if not ObjectId.is_valid(nivel_id):
        return error(404, "Nivel no encontrado")
    nivel = niveles_collection.find_one({"_id": ObjectId(nivel_id)})
    if not nivel:
        return error(404, "Nivel no encontrado")
    problema = exigir_gestion_curso(nivel.get("curso_id"))
    if problema:
        return problema
    return jsonify({"ok": eliminar_nivel(nivel_id)})
