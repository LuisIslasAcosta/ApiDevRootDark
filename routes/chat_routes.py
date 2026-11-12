from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from controllers import chat

chat_bp = Blueprint("chat_bp", __name__)


def _responder(funcion, *args, codigo_ok=200):
    try:
        return jsonify(funcion(*args)), codigo_ok
    except chat.ErrorChat as e:
        return jsonify({"mensaje": e.mensaje}), e.codigo
    except Exception as e:
        print("ERROR chat:", e)
        return jsonify({"mensaje": "Error en el chat"}), 500


def _yo():
    return str(get_jwt_identity())


# ---------------- Alumno y profesor ----------------

@chat_bp.route("/chat/contactos", methods=["GET"])
@jwt_required()
def get_contactos():
    return _responder(chat.contactos, _yo())


@chat_bp.route("/chat/conversaciones", methods=["GET"])
@jwt_required()
def get_conversaciones():
    return _responder(chat.mis_conversaciones, _yo())


@chat_bp.route("/chat/conversaciones", methods=["POST"])
@jwt_required()
def post_conversacion():
    datos = request.get_json(silent=True) or {}
    return _responder(chat.abrir_conversacion, _yo(), datos.get("curso_id"), datos.get("usuario_id"))


@chat_bp.route("/chat/conversaciones/<conversacion_id>/mensajes", methods=["GET"])
@jwt_required()
def get_mensajes(conversacion_id):
    return _responder(chat.mensajes, _yo(), conversacion_id)


@chat_bp.route("/chat/conversaciones/<conversacion_id>/mensajes", methods=["POST"])
@jwt_required()
def post_mensaje(conversacion_id):
    datos = request.get_json(silent=True) or {}
    return _responder(chat.enviar_mensaje, _yo(), conversacion_id, datos.get("texto"), codigo_ok=201)


@chat_bp.route("/chat/conversaciones/<conversacion_id>/reportes", methods=["POST"])
@jwt_required()
def post_reporte(conversacion_id):
    datos = request.get_json(silent=True) or {}
    return _responder(
        chat.reportar, _yo(), conversacion_id,
        datos.get("motivo"), datos.get("descripcion"), datos.get("mensaje_id"),
        codigo_ok=201,
    )


# ---------------- Administrador ----------------

@chat_bp.route("/chat/admin/reportes", methods=["GET"])
@jwt_required()
def get_reportes_admin():
    return _responder(chat.admin_reportes, _yo(), request.args.get("estado"))


@chat_bp.route("/chat/admin/reportes/<reporte_id>", methods=["GET"])
@jwt_required()
def get_reporte_admin(reporte_id):
    return _responder(chat.admin_detalle_reporte, _yo(), reporte_id)


@chat_bp.route("/chat/admin/reportes/<reporte_id>", methods=["PUT"])
@jwt_required()
def put_reporte_admin(reporte_id):
    datos = request.get_json(silent=True) or {}
    return _responder(chat.admin_resolver, _yo(), reporte_id, datos.get("decision"), datos.get("nota"))
