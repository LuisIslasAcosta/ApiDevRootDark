from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.kmeans import ejecutar_kmeans, metodo_codo

kmeans_bp = Blueprint("kmeans", __name__)

@kmeans_bp.route("/kmeans", methods=["GET"])
@jwt_required()
def kmeans_route():
    profesor_id = get_jwt_identity()
    k = request.args.get("k", 3, type=int)
    resultado = ejecutar_kmeans(profesor_id, k=k)
    return jsonify(resultado), 200

@kmeans_bp.route("/kmeans/metodo-codo", methods=["GET"])
@jwt_required()
def metodo_codo_route():
    profesor_id = get_jwt_identity()
    k_min = request.args.get("k_min", 1, type=int)
    k_max = request.args.get("k_max", 10, type=int)
    resultado = metodo_codo(profesor_id, k_range=(k_min, k_max))
    return jsonify(resultado), 200
