from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from bson.objectid import ObjectId
from config.config import examenes_collection, preguntas_collection
from models.Pregunta import eliminar_pregunta
from controllers.preguntas import obtener_todas_preguntas, obtener_preguntas_por_examen
from utils.seguridad import (
    error, exigir_acceso_curso, exigir_gestion_curso, sesion_requerida, solo_admin,
    staff_requerido, texto,
)

pregunta_bp = Blueprint("pregunta_bp", __name__)


def _examen(examen_id):
    examen_id = texto(examen_id)
    return examenes_collection.find_one({"_id": ObjectId(examen_id)}) if ObjectId.is_valid(examen_id) else None


# ================= CREAR PREGUNTA MANUAL (profesor dueño o admin) =================
@pregunta_bp.route("/preguntas", methods=["POST"])
@staff_requerido
def registrar():
    datos = request.get_json(silent=True) or {}

    examen_id = texto(datos.get("examen_id"))
    enunciado = texto(datos.get("enunciado"), 2000)
    opciones = [texto(o, 500) for o in (datos.get("opciones") or []) if texto(o, 500)] if isinstance(datos.get("opciones"), list) else []

    if not examen_id or not enunciado:
        return jsonify({"mensaje": "Examen y enunciado son obligatorios"}), 400
    examen = _examen(examen_id)
    if not examen:
        return error(404, "Examen no encontrado")
    problema = exigir_gestion_curso(examen.get("curso_id"))
    if problema:
        return problema

    preguntas_collection.insert_one({
        "examen_id": examen_id,
        "tipo": texto(datos.get("tipo", "multiple"), 30) or "multiple",
        "enunciado": enunciado,
        "opciones": opciones,
        "respuesta_correcta": texto(datos.get("respuesta_correcta"), 500),
    })

    return jsonify({"mensaje": "Pregunta registrada correctamente"}), 201


# ================= ELIMINAR (profesor dueño o admin) =================
@pregunta_bp.route("/preguntas/<pregunta_id>", methods=["DELETE"])
@staff_requerido
def eliminar(pregunta_id):
    pregunta = preguntas_collection.find_one({"_id": ObjectId(pregunta_id)}) if ObjectId.is_valid(pregunta_id) else None
    if not pregunta:
        return error(404, "Pregunta no encontrada")
    examen = _examen(pregunta.get("examen_id"))
    problema = exigir_gestion_curso(examen.get("curso_id")) if examen else error(404, "Examen no encontrado")
    if problema:
        return problema
    try:
        return jsonify({"ok": eliminar_pregunta(pregunta_id)}), 200
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400


# ================= LISTAR TODAS (solo admin) =================
@pregunta_bp.route("/preguntas", methods=["GET"])
@solo_admin
def listar():
    return jsonify(obtener_todas_preguntas()), 200


# ================= PREGUNTAS DE UN EXAMEN (sin respuestas, con acceso al curso) =================
@pregunta_bp.route("/preguntas/examen/<examen_id>", methods=["GET"])
@sesion_requerida
def obtener_preguntas_examen(examen_id):
    examen = _examen(examen_id)
    if not examen:
        return error(404, "Examen no encontrado")
    problema = exigir_acceso_curso(examen.get("curso_id"))
    if problema:
        return problema
    return jsonify(obtener_preguntas_por_examen(texto(examen_id))), 200
