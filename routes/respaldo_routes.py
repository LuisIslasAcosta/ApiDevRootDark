from flask import Blueprint
from controllers.respaldo_controller import (
    generar_respaldo,
    restaurar_respaldo,
    configurar_respaldo,
    listar_respaldos,
    restaurar_respaldo_lista,
    eliminar_respaldo
)

respaldo_bp = Blueprint("respaldo", __name__)

@respaldo_bp.route("/respaldo/<tipo>", methods=["GET"])
def backup(tipo):
    return generar_respaldo(tipo)

@respaldo_bp.route("/respaldo", methods=["POST"])
def restore():
    return restaurar_respaldo()

@respaldo_bp.route("/config-respaldo", methods=["POST"])
def config():
    return configurar_respaldo()

@respaldo_bp.route("/respaldos", methods=["GET"])
def listar():
    return listar_respaldos()

@respaldo_bp.route("/respaldo/restaurar/<tipo>/<nombre>", methods=["POST"])
def restaurar_desde_lista(tipo, nombre):
    return restaurar_respaldo_lista(nombre, tipo)

@respaldo_bp.route("/respaldo/<tipo>/<nombre>", methods=["DELETE"])
def eliminar_respaldo_desde_lista(tipo, nombre):
    return eliminar_respaldo(nombre, tipo)