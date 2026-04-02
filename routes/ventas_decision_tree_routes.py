from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.ventas_decision_tree import analizar_ventas_decision_tree

ventas_dt_bp = Blueprint("ventas_dt", __name__)

@ventas_dt_bp.route("/api/ventas/decision-tree", methods=["GET"])
@jwt_required()
def ventas_decision_tree_route():

    # 🔥 OBTENER USUARIO LOGGEADO
    profesor_id = get_jwt_identity()

    # 🔥 PASARLO AL CONTROLLER
    resultado = analizar_ventas_decision_tree(profesor_id)

    return jsonify(resultado), 200