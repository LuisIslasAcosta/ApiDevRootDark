import pandas as pd
from flask import Blueprint, request, jsonify
from config.config import preguntas_collection

excel_bp = Blueprint("excel_bp", __name__)

@excel_bp.route("/preguntas/importar_excel", methods=["POST"])
def importar_excel():
    archivo = request.files.get("archivo")
    examen_id = request.form.get("examen_id")

    df = pd.read_excel(archivo)

    for _, fila in df.iterrows():
        preguntas_collection.insert_one({
            "examen_id": examen_id,
            "tipo": "multiple",
            "enunciado": fila["pregunta"],
            "opciones": [
                fila["opcion1"],
                fila["opcion2"],
                fila["opcion3"],
                fila["opcion4"]
            ],
            "respuesta_correcta": fila["respuesta_correcta"]
        })

    return jsonify({"mensaje": "Preguntas importadas correctamente"}), 201
