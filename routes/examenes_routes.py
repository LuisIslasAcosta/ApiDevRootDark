from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from bson.objectid import ObjectId
from models.Examen import registrar_examen, eliminar_examen
from controllers.examenes import obtener_examenes, obtener_examenes_por_curso, serializar_examen
from config.config import examenes_collection, preguntas_collection
import json
from utils.excel_preguntas import leer_preguntas, ErrorExcel

examen_bp = Blueprint("examen_bp", __name__)


def _id_flexible(valor):
    """Coincide con el id guardado como texto o como ObjectId."""
    opciones = [valor]
    if ObjectId.is_valid(valor):
        opciones.append(ObjectId(valor))
    return {"$in": opciones}

# ================= CREAR EXAMEN =================
@examen_bp.route("/examenes", methods=["POST"])
def registrar():

    titulo = (request.form.get("titulo") or "").strip()
    curso_id = request.form.get("curso_id")
    leccion_id = request.form.get("leccion_id")
    nivel_id = request.form.get("nivel_id") or None
    fecha = request.form.get("fecha")

    if not curso_id or not leccion_id or not titulo or not fecha:
        return jsonify({"mensaje": "Curso, lección, título y fecha son obligatorios"}), 400

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

    if preguntas:
        preguntas_collection.insert_many([{**p, "examen_id": examen_id} for p in preguntas])

    return jsonify({
        "mensaje": f"Examen creado correctamente con {len(preguntas)} preguntas",
        "examen_id": examen_id,
        "preguntas": len(preguntas),
    }), 201


# ================= LISTAR =================
@examen_bp.route("/examenes", methods=["GET"])
def listar():
    return jsonify(obtener_examenes()), 200


@examen_bp.route("/examenes/curso/<curso_id>", methods=["GET"])
def listar_por_curso(curso_id):
    return jsonify(obtener_examenes_por_curso(curso_id)), 200


@examen_bp.route("/examenes/leccion/<leccion_id>", methods=["GET"])
def listar_por_leccion(leccion_id):
    examenes = examenes_collection.find({"leccion_id": _id_flexible(leccion_id)})
    return jsonify([serializar_examen(ex) for ex in examenes]), 200


@examen_bp.route("/examenes/nivel/<nivel_id>", methods=["GET"])
def listar_por_nivel(nivel_id):
    examenes = examenes_collection.find({"nivel_id": _id_flexible(nivel_id)})
    return jsonify([serializar_examen(ex) for ex in examenes]), 200


# ================= ELIMINAR =================
@examen_bp.route("/examenes/<examen_id>", methods=["DELETE"])
def eliminar(examen_id):
    try:
        ok = eliminar_examen(examen_id)
        if ok:
            preguntas_collection.delete_many({"examen_id": examen_id})  # sus preguntas también
        return jsonify({"ok": ok}), 200
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400
