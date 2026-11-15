"""Rutas de intentos de examen (en línea y sin conexión)."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required, verify_jwt_in_request

from controllers.intentos import (
    ErrorIntento,
    buscar_examen,
    buscar_intento,
    autorizar,
    enviar_intento,
    intentos_de_examen,
    marcar_inicio,
    obtener_o_crear_intento,
    rol_de,
)

intento_bp = Blueprint("intento_bp", __name__)


def _usuario_opcional():
    """El token es opcional en el envío: si caducó sin conexión, vale la clave del intento."""
    try:
        verify_jwt_in_request(optional=True)
        return get_jwt_identity()
    except Exception:
        return None


def _error(e):
    return jsonify({"mensaje": e.mensaje}), e.codigo


# Descarga (o recupera) el intento: preguntas en orden propio y sin respuestas
@intento_bp.route("/intentos/examen/<examen_id>", methods=["POST"])
@jwt_required()
def crear(examen_id):
    try:
        paquete, codigo = obtener_o_crear_intento(get_jwt_identity(), examen_id)
        return jsonify(paquete), codigo
    except ErrorIntento as e:
        return _error(e)


# Marca el inicio (se manda al empezar; si no hay señal, se manda al reconectar)
@intento_bp.route("/intentos/<intento_id>/iniciar", methods=["POST"])
def iniciar(intento_id):
    datos = request.get_json(silent=True) or {}
    try:
        intento = buscar_intento(intento_id)
        autorizar(intento, _usuario_opcional(), datos.get("clave_envio"))
        if intento["estado"] not in ("abierto", "enviado"):
            raise ErrorIntento("Este intento ya no está disponible", 409)
        inicio = marcar_inicio(intento, datos.get("iniciado_cliente"), datos.get("reloj_cliente"))
        return jsonify({"iniciado_en": inicio.isoformat()}), 200
    except ErrorIntento as e:
        return _error(e)


# Entrega las respuestas. Idempotente: reenviar el mismo intento no lo vuelve a calificar
@intento_bp.route("/intentos/<intento_id>/enviar", methods=["POST"])
def enviar(intento_id):
    try:
        resultado, codigo = enviar_intento(intento_id, request.get_json(silent=True) or {}, _usuario_opcional())
        return jsonify(resultado), codigo
    except ErrorIntento as e:
        return _error(e)


# Profesor o administrador: intentos de un examen con sus alertas
@intento_bp.route("/intentos/examen/<examen_id>", methods=["GET"])
@jwt_required()
def listar(examen_id):
    if rol_de(get_jwt_identity()) not in ("profesor", "administrador"):
        return jsonify({"mensaje": "Solo el profesor puede ver los intentos"}), 403
    if not buscar_examen(examen_id):
        return jsonify({"mensaje": "El examen no existe"}), 404
    return jsonify(intentos_de_examen(examen_id)), 200
