"""Firma del profesor (se imprime en los certificados de sus cursos)."""
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity, jwt_required

from controllers.firmas import ErrorFirma, borrar_firma, guardar_firma, mi_firma

firmas_bp = Blueprint("firmas_bp", __name__)


@firmas_bp.route("/firma", methods=["GET"])
@jwt_required()
def ver():
    return jsonify(mi_firma(get_jwt_identity())), 200


@firmas_bp.route("/firma", methods=["PUT"])
@jwt_required()
def guardar():
    datos = request.get_json(silent=True) or {}
    try:
        return jsonify(guardar_firma(get_jwt_identity(), datos.get("imagen"))), 200
    except ErrorFirma as e:
        return jsonify({"mensaje": e.mensaje}), e.codigo


@firmas_bp.route("/firma", methods=["DELETE"])
@jwt_required()
def borrar():
    return jsonify(borrar_firma(get_jwt_identity())), 200
