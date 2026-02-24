from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt

user_bp = Blueprint('users', __name__)

@user_bp.route('/me')
@jwt_required()
def me():
    user_id = get_jwt_identity()
    claims = get_jwt()

    return jsonify({
        "id": user_id,
        "email": claims.get('email'),
        "rol": claims.get('rol')
    }), 200