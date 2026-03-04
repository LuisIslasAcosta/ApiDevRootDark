from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from models.Examen import registrar_examen, eliminar_examen
from controllers.examenes import obtener_examenes, obtener_examenes_por_curso, serializar_examen
from config.config import examenes_collection, preguntas_collection
import pandas as pd
import json

examen_bp = Blueprint("examen_bp", __name__)

# ================= CREAR EXAMEN =================
@examen_bp.route("/examenes", methods=["POST"])
def registrar():

    titulo = request.form.get("titulo")
    curso_id = request.form.get("curso_id")
    leccion_id = request.form.get("leccion_id")
    fecha = request.form.get("fecha")

    if not curso_id or not leccion_id or not titulo or not fecha:
        return jsonify({"mensaje": "Curso, lección, título y fecha son obligatorios"}), 400

    # Crear examen
    respuesta, status = registrar_examen(curso_id, leccion_id, titulo, fecha)

    if status != 201:
        return respuesta, status

    examen_id = respuesta.json["examen_id"]

    # ================= PREGUNTAS JSON =================
    preguntas_json = request.form.get("preguntas_json")

    if preguntas_json:
        preguntas_list = json.loads(preguntas_json)

        for p in preguntas_list:
            preguntas_collection.insert_one({
                "examen_id": examen_id,
                "tipo": p.get("tipo", "multiple"),
                "enunciado": p.get("enunciado"),
                "opciones": p.get("opciones", []),
                "respuesta_correcta": p.get("respuesta_correcta")
            })

    # ================= EXCEL =================
    archivo = request.files.get("archivo")

    if archivo:
        df = pd.read_excel(archivo)

        for _, fila in df.iterrows():
            preguntas_collection.insert_one({
                "examen_id": examen_id,
                "tipo": "multiple",
                "enunciado": fila["pregunta"],
                "opciones": [
                    fila.get("opcion1"),
                    fila.get("opcion2"),
                    fila.get("opcion3"),
                    fila.get("opcion4")
                ],
                "respuesta_correcta": fila["respuesta_correcta"]
            })

    return jsonify({
        "mensaje": "Examen creado correctamente",
        "examen_id": examen_id
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
    examenes = examenes_collection.find({"leccion_id": leccion_id})
    return jsonify([serializar_examen(ex) for ex in examenes]), 200


# ================= ELIMINAR =================
@examen_bp.route("/examenes/<examen_id>", methods=["DELETE"])
def eliminar(examen_id):
    try:
        ok = eliminar_examen(examen_id)
        return jsonify({"ok": ok}), 200
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400
