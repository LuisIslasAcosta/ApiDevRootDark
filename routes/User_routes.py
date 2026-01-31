from flask import Blueprint, request, jsonify
from controllers.auth import validar_login
from controllers.user import (
    obtener_usuarios,
    obtener_usuario_por_id,
    actualizar_usuario,
    eliminar_usuario,
    actualizar_contraseña,
    registrar_usuario
)
from models.models import User

user_bp = Blueprint('user_bp', __name__)

# -------------------------------
# Login
# -------------------------------
@user_bp.route('/login', methods=['POST'])
def login():
    datos = request.json
    email = datos.get('email')
    password = datos.get('password')

    if not email or not password:
        return jsonify({"mensaje": "El correo y la contraseña son necesarios para iniciar sesión"}), 400

    resultado = validar_login(email, password)
    if resultado:
        return jsonify(resultado), 200
    else:
        return jsonify({"mensaje": "El correo o la contraseña son incorrectos"}), 401


# -------------------------------
# Registro de usuario
# -------------------------------
@user_bp.route('/registrar', methods=['POST'])
def registrar():
    datos = request.json
    resultado, status_code = registrar_usuario(
        nombre=datos.get('nombre'),
        apellidop=datos.get('apellidop'),
        apellidom=datos.get('apellidom'),
        fecha_nacimiento=datos.get('fecha_nacimiento'),
        pais=datos.get('pais'),
        ciudad=datos.get('ciudad'),
        email=datos.get('email'),
        password=datos.get('password'),
        verificar_password=datos.get('verificar_password'),
        foto_perfil=datos.get('foto_perfil'),
        pregunta_seguridad=datos.get('pregunta_seguridad'),
        respuesta_seguridad=datos.get('respuesta_seguridad'),
        telefono=datos.get('telefono')
    )
    return resultado, status_code


# -------------------------------
# Recuperar contraseña
# -------------------------------
@user_bp.route('/recuperar_contraseña/<int:usuario_id>', methods=['PUT'])
def recuperar_contraseña(usuario_id):
    datos = request.json
    nueva_contraseña = datos.get('nueva_contraseña')

    if not nueva_contraseña:
        return jsonify({"mensaje": "La nueva contraseña es requerida"}), 400

    exito = actualizar_contraseña(usuario_id, nueva_contraseña)
    if exito:
        return jsonify({"mensaje": "Contraseña actualizada correctamente"}), 200
    else:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404


# -------------------------------
# Obtener usuario por ID
# -------------------------------
@user_bp.route('/usuarios/<int:usuario_id>', methods=['GET'])
def obtener_usuario(usuario_id):
    usuario = obtener_usuario_por_id(usuario_id)
    if usuario:
        return jsonify(usuario), 200
    else:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404


# -------------------------------
# Actualizar usuario
# -------------------------------
@user_bp.route('/usuarios/<int:usuario_id>', methods=['PUT'])
def actualizar_usuario_route(usuario_id):
    datos_actualizados = request.json
    exito = actualizar_usuario(usuario_id, datos_actualizados)
    if exito:
        return jsonify({"mensaje": "Usuario actualizado correctamente"}), 200
    else:
        return jsonify({"mensaje": "No se pudo actualizar el usuario"}), 400


# -------------------------------
# Eliminar usuario
# -------------------------------
@user_bp.route('/usuarios/<int:usuario_id>', methods=['DELETE'])
def eliminar_usuario_route(usuario_id):
    exito = eliminar_usuario(usuario_id)
    if exito:
        return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200
    else:
        return jsonify({"mensaje": "No se pudo eliminar el usuario"}), 400


# -------------------------------
# Listar usuarios
# -------------------------------
@user_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = obtener_usuarios()
    return jsonify(usuarios), 200