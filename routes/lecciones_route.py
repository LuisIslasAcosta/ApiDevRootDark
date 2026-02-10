from flask import Blueprint, request, jsonify
from models.Leccion import registrar_leccion
from controllers.lecciones import obtener_lecciones_por_curso

leccion_bp = Blueprint("leccion_bp", __name__)

@leccion_bp.route("/lecciones", methods=["POST"])
def crear():
    datos = request.json
    return registrar_leccion(
        curso_id=datos.get("curso_id"),
        titulo=datos.get("titulo"),
        contenido=datos.get("contenido"),
        recursos=datos.get("recursos", [])
    )

@leccion_bp.route("/lecciones/curso/<curso_id>", methods=["GET"])
def listar(curso_id):
    return jsonify(obtener_lecciones_por_curso(curso_id)), 200
