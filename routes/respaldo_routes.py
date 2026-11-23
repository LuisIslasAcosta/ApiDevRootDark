from flask import Blueprint, jsonify, request
from controllers.respaldo_controller import (
    generar_respaldo,
    restaurar_respaldo,
    configurar_respaldo,
    listar_respaldos,
    restaurar_respaldo_lista,
    eliminar_respaldo
)
from werkzeug.utils import secure_filename
from utils.seguridad import admin_requerido, auditoria_collection

respaldo_bp = Blueprint("respaldo", __name__)

# Todas las rutas de respaldos exigen token JWT de un usuario con rol "administrador"
# y quedan registradas en la colección auditoria_respaldos.
# Generar, restaurar, configurar y borrar exigen además un token "fresco": haber escrito
# la contraseña hace menos de 10 minutos (un token renovado automáticamente no sirve).


@respaldo_bp.route("/respaldo/<tipo>", methods=["GET"])
@admin_requerido("generar_respaldo", fresco=True)
def backup(tipo):
    return generar_respaldo(tipo)


@respaldo_bp.route("/respaldo", methods=["POST"])
@admin_requerido("restaurar_respaldo_archivo", fresco=True)
def restore():
    return restaurar_respaldo()


@respaldo_bp.route("/config-respaldo", methods=["POST"])
@admin_requerido("configurar_respaldo", fresco=True)
def config():
    return configurar_respaldo()


@respaldo_bp.route("/respaldos", methods=["GET"])
@admin_requerido("listar_respaldos")
def listar():
    return listar_respaldos()


@respaldo_bp.route("/respaldo/restaurar/<tipo>/<nombre>", methods=["POST"])
@admin_requerido("restaurar_respaldo_lista", fresco=True)
def restaurar_desde_lista(tipo, nombre):
    return restaurar_respaldo_lista(secure_filename(nombre), tipo)


@respaldo_bp.route("/respaldo/<tipo>/<nombre>", methods=["DELETE"])
@admin_requerido("eliminar_respaldo", fresco=True)
def eliminar_respaldo_desde_lista(tipo, nombre):
    return eliminar_respaldo(secure_filename(nombre), tipo)


@respaldo_bp.route("/respaldos/auditoria", methods=["GET"])
@admin_requerido("ver_auditoria")
def ver_auditoria():
    limite = min(max(request.args.get("limite", 50, type=int) or 50, 1), 200)
    registros = auditoria_collection.find({}, {"_id": 0}).sort("fecha", -1).limit(limite)
    return jsonify(list(registros)), 200
