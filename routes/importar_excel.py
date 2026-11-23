from flask import Blueprint, request, jsonify
from bson.objectid import ObjectId
from config.config import preguntas_collection, examenes_collection
from utils.excel_preguntas import leer_preguntas, ErrorExcel
from utils.seguridad import exigir_gestion_curso, staff_requerido, texto

excel_bp = Blueprint("excel_bp", __name__)


@excel_bp.route("/preguntas/importar_excel", methods=["POST"])
@staff_requerido
def importar_excel():
    """Agrega a un examen existente las preguntas de un Excel (profesor dueño o admin)."""
    examen_id = texto(request.form.get("examen_id"))
    examen = examenes_collection.find_one({"_id": ObjectId(examen_id)}) if ObjectId.is_valid(examen_id) else None
    if not examen:
        return jsonify({"mensaje": "El examen no existe."}), 404
    problema = exigir_gestion_curso(examen.get("curso_id"))
    if problema:
        return problema

    try:
        preguntas = leer_preguntas(request.files.get("archivo"))
    except ErrorExcel as e:
        return jsonify({"mensaje": str(e)}), 400

    preguntas_collection.insert_many([{**p, "examen_id": examen_id} for p in preguntas])

    return jsonify({
        "mensaje": f"Se importaron {len(preguntas)} preguntas correctamente.",
        "importadas": len(preguntas),
    }), 201
