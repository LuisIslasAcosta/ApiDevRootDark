from services.authService import AuthService
from flask import Blueprint, jsonify, request
from flasgger import swag_from

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/registrar', methods=['POST'])
@swag_from('../yaml/register.yaml')
def register():
    data = request.get_json()

    if data['password'] != data['verificar_password']:
        return jsonify({"mensaje": "Las contraseñas no coinciden"}), 400

    user = AuthService.register(data)

    return jsonify({
        "mensaje": "Usuario registrado correctamente",
        "usuario": user.to_dict()
    }), 200


@auth_bp.route('/usuario/<int:user_id>', methods=['GET'])
@swag_from('../yaml/ObtenerUsuario.yaml')
def obtener_usuario(user_id):
    user = AuthService.obtener_usuario_por_id(user_id)

    if not user:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    return jsonify(user.to_dict()), 200


@auth_bp.route('/login', methods=['POST'])
@swag_from('../yaml/login.yaml')
def login():
    data = request.get_json()

    result = AuthService.login(data['email'], data['password'])

    if not result:
        return jsonify({"mensaje": "Credenciales inválidas"}), 401

    return jsonify({
        "access_token": result["access_token"],
        "usuario": result["usuario"].to_dict()
    }), 200