from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.seguridad import staff_requerido
from controllers.ventas_decision_tree import analizar_ventas_decision_tree

ventas_dt_bp = Blueprint("ventas_dt", __name__)

@ventas_dt_bp.route("/ventas/decision-tree", methods=["GET"])
@staff_requerido
def ventas_decision_tree_route():

    #  OBTENER USUARIO LOGGEADO
    profesor_id = get_jwt_identity()

    #  PASARLO AL CONTROLLER
    resultado = analizar_ventas_decision_tree(profesor_id)

    return jsonify(resultado), 200