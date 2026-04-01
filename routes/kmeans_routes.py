from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.kmeans import ejecutar_kmeans

kmeans_bp = Blueprint("kmeans", __name__)

@kmeans_bp.route("/api/kmeans", methods=["GET"])
@jwt_required()
def kmeans_route():
    profesor_id = get_jwt_identity()
    resultado = ejecutar_kmeans(profesor_id)
    return jsonify(resultado), 200
