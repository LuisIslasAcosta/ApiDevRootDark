from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from config.config import preguntas_collection
from models.Pregunta import eliminar_pregunta
from bson.objectid import ObjectId
from controllers.preguntas import obtener_todas_preguntas, obtener_preguntas_por_examen

pregunta_bp = Blueprint("pregunta_bp", __name__)

# ================= CREAR PREGUNTA MANUAL =================
@pregunta_bp.route("/preguntas", methods=["POST"])
def registrar():
    datos = request.get_json()

    examen_id = datos.get("examen_id")
    tipo = datos.get("tipo", "multiple")
    enunciado = datos.get("enunciado")
    opciones = datos.get("opciones", [])
    respuesta_correcta = datos.get("respuesta_correcta")

    if not examen_id or not enunciado:
        return jsonify({"mensaje": "Examen y enunciado son obligatorios"}), 400

    preguntas_collection.insert_one({
        "examen_id": examen_id,
        "tipo": tipo,
        "enunciado": enunciado,
        "opciones": opciones,
        "respuesta_correcta": respuesta_correcta
    })

    return jsonify({"mensaje": "Pregunta registrada correctamente"}), 201


# ================= ELIMINAR =================
@pregunta_bp.route("/preguntas/<pregunta_id>", methods=["DELETE"])
def eliminar(pregunta_id):
    try:
        exito = eliminar_pregunta(pregunta_id)
        return jsonify({"ok": exito}), 200
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400


# ================= LISTAR TODAS =================
@pregunta_bp.route("/preguntas", methods=["GET"])
def listar():
    return jsonify(obtener_todas_preguntas()), 200


@pregunta_bp.route("/preguntas/examen/<examen_id>", methods=["GET"])
def obtener_preguntas_examen(examen_id):
    try:
        filtro = {"examen_id": examen_id}

        # Si es ObjectId válido, probar también
        try:
            filtro = {"$or": [
                {"examen_id": examen_id},
                {"examen_id": ObjectId(examen_id)}
            ]}
        except:
            pass

        preguntas = list(preguntas_collection.find(filtro))

        resultado = [
            {
                "id": str(p["_id"]),
                "enunciado": p.get("enunciado", ""),
                "opciones": p.get("opciones", []),
                "tipo": p.get("tipo", "multiple")
            }
            for p in preguntas
        ]

        return jsonify(resultado), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500