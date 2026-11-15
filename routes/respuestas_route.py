from flask import Blueprint, request, jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required
from models.Respuesta import guardar_respuestas
from controllers.respuestas import obtener_resultados_por_alumno
from controllers.intentos import (
    alumno_tiene_acceso,
    buscar_examen,
    configuracion_examen,
    intentos_usados,
)

respuesta_bp = Blueprint("respuesta_bp", __name__)


# Envío directo (versión anterior de la app). La app nueva usa /intentos.
# Ahora exige sesión, toma al alumno del token (ya no del cuerpo) y respeta el límite de intentos.
@respuesta_bp.route("/respuestas", methods=["POST"])
@jwt_required()
def registrar():
    datos = request.get_json(silent=True) or {}
    alumno_id = get_jwt_identity()
    examen = buscar_examen(datos.get("examen_id"))
    if not examen:
        return jsonify({"mensaje": "El examen no existe"}), 404
    if not alumno_tiene_acceso(alumno_id, examen.get("curso_id", "")):
        return jsonify({"mensaje": "Necesitas una inscripción aceptada en este curso"}), 403
    maximo = configuracion_examen(examen)["intentos_max"]
    if intentos_usados(alumno_id, str(examen["_id"])) >= maximo:
        return jsonify({"mensaje": f"Ya usaste tus {maximo} intentos de este examen"}), 409
    return guardar_respuestas(
        alumno_id=alumno_id,
        examen_id=str(examen["_id"]),
        respuestas=datos.get("respuestas") or {}
    )


@respuesta_bp.route("/respuestas/alumno/<alumno_id>", methods=["GET"])
def listar_por_alumno(alumno_id):
    return jsonify(obtener_resultados_por_alumno(alumno_id)), 200
