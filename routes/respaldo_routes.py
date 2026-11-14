from flask import Blueprint, jsonify, request
from controllers.respaldo_controller import (
    generar_respaldo,
    restaurar_respaldo,
    configurar_respaldo,
    listar_respaldos,
    restaurar_respaldo_lista,
    eliminar_respaldo
)
from utils.seguridad import admin_requerido, auditoria_collection

respaldo_bp = Blueprint("respaldo", __name__)

# Todas las rutas de respaldos exigen token JWT de un usuario con rol "administrador"
# y quedan registradas en la colección auditoria_respaldos.


@respaldo_bp.route("/respaldo/<tipo>", methods=["GET"])
@admin_requerido("generar_respaldo")
def backup(tipo):
    return generar_respaldo(tipo)


@respaldo_bp.route("/respaldo", methods=["POST"])
@admin_requerido("restaurar_respaldo_archivo")
def restore():
    return restaurar_respaldo()


@respaldo_bp.route("/config-respaldo", methods=["POST"])
@admin_requerido("configurar_respaldo")
def config():
    return configurar_respaldo()


@respaldo_bp.route("/respaldos", methods=["GET"])
@admin_requerido("listar_respaldos")
def listar():
    return listar_respaldos()


@respaldo_bp.route("/respaldo/restaurar/<tipo>/<nombre>", methods=["POST"])
@admin_requerido("restaurar_respaldo_lista")
def restaurar_desde_lista(tipo, nombre):
    return restaurar_respaldo_lista(nombre, tipo)


@respaldo_bp.route("/respaldo/<tipo>/<nombre>", methods=["DELETE"])
@admin_requerido("eliminar_respaldo")
def eliminar_respaldo_desde_lista(tipo, nombre):
    return eliminar_respaldo(nombre, tipo)


@respaldo_bp.route("/respaldos/auditoria", methods=["GET"])
@admin_requerido("ver_auditoria")
def ver_auditoria():
    limite = min(int(request.args.get("limite", 50)), 200)
    registros = auditoria_collection.find({}, {"_id": 0}).sort("fecha", -1).limit(limite)
    return jsonify(list(registros)), 200
