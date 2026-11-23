from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from bson.objectid import ObjectId
from models.Examen import registrar_examen, eliminar_examen
from controllers.examenes import obtener_examenes, obtener_examenes_por_curso, serializar_examen
from config.config import examenes_collection, preguntas_collection
import json
from utils.excel_preguntas import leer_preguntas, ErrorExcel
from config.config import cursos_collection
from utils.seguridad import (
    error, es_admin, exigir_acceso_curso, exigir_gestion_curso, sesion_requerida,
    staff_requerido, texto, tiene_acceso_curso, usuario_sesion, variantes_id,
)

examen_bp = Blueprint("examen_bp", __name__)


def _id_flexible(valor):
    """Coincide con el id guardado como texto o como ObjectId."""
    opciones = [valor]
    if ObjectId.is_valid(valor):
        opciones.append(ObjectId(valor))
    return {"$in": opciones}

# ================= CREAR EXAMEN =================
@examen_bp.route("/examenes", methods=["POST"])
@staff_requerido
def registrar():

    titulo = texto(request.form.get("titulo"), 200)
    curso_id = texto(request.form.get("curso_id"))
    leccion_id = texto(request.form.get("leccion_id"))
    nivel_id = texto(request.form.get("nivel_id")) or None
    fecha = texto(request.form.get("fecha"), 40)

    if not curso_id or not leccion_id or not titulo or not fecha:
        return jsonify({"mensaje": "Curso, lección, título y fecha son obligatorios"}), 400
    problema = exigir_gestion_curso(curso_id)
    if problema:
        return problema

    # Leer las preguntas ANTES de crear el examen (si el Excel trae errores, no se crea nada)
    preguntas = []
    archivo = request.files.get("archivo")
    if archivo and archivo.filename:
        try:
            preguntas = leer_preguntas(archivo)
        except ErrorExcel as e:
            return jsonify({"mensaje": str(e)}), 400
    else:
        preguntas_json = request.form.get("preguntas_json")
        if preguntas_json:
            try:
                lista = json.loads(preguntas_json)
            except ValueError:
                return jsonify({"mensaje": "Las preguntas no tienen un formato válido."}), 400
            for p in lista:
                opciones = [str(o).strip() for o in p.get("opciones", []) if str(o or "").strip()]
                enunciado = str(p.get("enunciado") or "").strip()
                if not enunciado or len(opciones) < 2:
                    continue  # se ignoran preguntas incompletas
                preguntas.append({
                    "tipo": p.get("tipo", "multiple"),
                    "enunciado": enunciado,
                    "opciones": opciones,
                    "respuesta_correcta": str(p.get("respuesta_correcta") or "").strip(),
                })

    # Crear examen (argumentos por nombre: antes se guardaban en el orden equivocado)
    respuesta, status = registrar_examen(
        curso_id=curso_id, titulo=titulo, fecha=fecha,
        leccion_id=leccion_id, nivel_id=nivel_id,
    )
    if status != 201:
        return respuesta, status

    examen_id = respuesta.json["examen_id"]

    # Tiempo e intentos (si no vienen, se usan 60 minutos y 3 intentos)
    ajustes = {}
    for campo, minimo, maximo in (("duracion_minutos", 1, 600), ("intentos_max", 1, 20)):
        try:
            valor = int(request.form.get(campo) or 0)
        except ValueError:
            valor = 0
        if valor:
            ajustes[campo] = max(minimo, min(maximo, valor))
    if ajustes:
        examenes_collection.update_one({"_id": ObjectId(examen_id)}, {"$set": ajustes})

    if preguntas:
        preguntas_collection.insert_many([{**p, "examen_id": examen_id} for p in preguntas])

    return jsonify({
        "mensaje": f"Examen creado correctamente con {len(preguntas)} preguntas",
        "examen_id": examen_id,
        "preguntas": len(preguntas),
    }), 201


def _visibles(examenes):
    """Solo los exámenes de cursos a los que el usuario tiene acceso."""
    usuario = usuario_sesion()
    permitidos, resultado = {}, []
    for ex in examenes:
        curso = str(ex.get("curso_id", ""))
        if curso not in permitidos:
            permitidos[curso] = tiene_acceso_curso(usuario, curso)
        if permitidos[curso]:
            resultado.append(serializar_examen(ex))
    return resultado


# ================= LISTAR =================
@examen_bp.route("/examenes", methods=["GET"])
@staff_requerido
def listar():
    usuario = usuario_sesion()
    if es_admin(usuario):
        return jsonify(obtener_examenes()), 200
    # El profesor solo ve los exámenes de sus cursos
    mis_cursos = [v for c in cursos_collection.find({"profesor": {"$in": variantes_id(usuario["_id"])}}, {"_id": 1})
                  for v in variantes_id(c["_id"])]
    return jsonify([serializar_examen(ex) for ex in examenes_collection.find({"curso_id": {"$in": mis_cursos}})]), 200


@examen_bp.route("/examenes/curso/<curso_id>", methods=["GET"])
@sesion_requerida
def listar_por_curso(curso_id):
    problema = exigir_acceso_curso(curso_id)
    if problema:
        return problema
    return jsonify(obtener_examenes_por_curso(curso_id)), 200


@examen_bp.route("/examenes/leccion/<leccion_id>", methods=["GET"])
@sesion_requerida
def listar_por_leccion(leccion_id):
    return jsonify(_visibles(examenes_collection.find({"leccion_id": _id_flexible(leccion_id)}))), 200


@examen_bp.route("/examenes/nivel/<nivel_id>", methods=["GET"])
@sesion_requerida
def listar_por_nivel(nivel_id):
    return jsonify(_visibles(examenes_collection.find({"nivel_id": _id_flexible(nivel_id)}))), 200


# ================= ELIMINAR =================
@examen_bp.route("/examenes/<examen_id>", methods=["DELETE"])
@staff_requerido
def eliminar(examen_id):
    if not ObjectId.is_valid(examen_id):
        return error(400, "ID inválido")
    examen = examenes_collection.find_one({"_id": ObjectId(examen_id)})
    if not examen:
        return error(404, "Examen no encontrado")
    problema = exigir_gestion_curso(examen.get("curso_id"))
    if problema:
        return problema
    try:
        ok = eliminar_examen(examen_id)
        if ok:
            preguntas_collection.delete_many({"examen_id": examen_id})  # sus preguntas también
        return jsonify({"ok": ok}), 200
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400
