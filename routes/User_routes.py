from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from controllers.auth import validar_login
from models.User import registrar_usuario, actualizar_contraseña
from controllers.user import obtener_usuarios, obtener_usuario_por_id, actualizar_usuario, eliminar_usuario, obtener_usuarios_recientes

user_bp = Blueprint('user_bp', __name__)

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
    
@user_bp.route('/registrar', methods=['POST'])
def registrar():
    datos = request.json
    nombre = datos.get('nombre')
    apellidop = datos.get('apellidop')
    apellidom = datos.get('apellidom')
    fecha_nacimiento = datos.get('fecha_nacimiento')
    pais = datos.get('pais')
    ciudad = datos.get('ciudad')
    email = datos.get('email')
    password = datos.get('password')
    verificar_password = datos.get('verificar_password')
    foto_perfil = datos.get('foto_perfil', None)
    pregunta_seguridad = datos.get('pregunta_seguridad')
    respuesta_seguridad = datos.get('respuesta_seguridad')
    telefono = datos.get('telefono')

    resultado, status_code = registrar_usuario(
        nombre=nombre,
        apellidop=apellidop,
        apellidom=apellidom,
        fecha_nacimiento=fecha_nacimiento,
        pais=pais,
        ciudad=ciudad,
        email=email,
        password=password,
        verificar_password=verificar_password,
        foto_perfil=foto_perfil,
        pregunta_seguridad=pregunta_seguridad,
        respuesta_seguridad=respuesta_seguridad,
        telefono=telefono
    )

    return resultado, status_code

@user_bp.route('/recuperar_contraseña/<usuario_id>', methods=['PUT'])
def recuperar_contraseña(usuario_id):
    datos = request.json
    nueva_contraseña = datos.get('nueva_contraseña')

    if not nueva_contraseña:
        return jsonify({"mensaje": "La nueva contraseña es requerida"}), 400

    try:
        exito = actualizar_contraseña(usuario_id, nueva_contraseña)
        if exito:
            return jsonify({"mensaje": "Contraseña actualizada correctamente"}), 200
        else:
            return jsonify({"mensaje": "No se pudo actualizar la contraseña"}), 400
    except InvalidId:
        return jsonify({"mensaje": "ID de usuario inválido"}), 400

@user_bp.route('/usuarios/<usuario_id>', methods=['GET'])
def obtener_usuario(usuario_id):
    usuario = obtener_usuario_por_id(usuario_id)
    if usuario:
        return jsonify(usuario), 200
    else:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    

@user_bp.route('/usuarios/<usuario_id>', methods=['PUT'])
def actualizar_usuario_route(usuario_id):
    datos_actualizados = request.json
    try:
        exito = actualizar_usuario(usuario_id, datos_actualizados)
        if exito:
            return jsonify({"mensaje": "Usuario actualizado correctamente"}), 200
        else:
            return jsonify({"mensaje": "No se pudo actualizar el usuario"}), 400
    except InvalidId:
        return jsonify({"mensaje": "ID de usuario inválido"}), 400
    
@user_bp.route('/usuarios/<usuario_id>', methods=['DELETE'])
def eliminar_usuario_route(usuario_id):
    try:
        exito = eliminar_usuario(usuario_id)
        if exito:
            return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200
        else:
            return jsonify({"mensaje": "No se pudo eliminar el usuario"}), 400
    except InvalidId:
        return jsonify({"mensaje": "ID de usuario inválido"}), 400

@user_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = obtener_usuarios()
    return jsonify(usuarios), 200

@user_bp.route('/usuarios/recientes', methods=['GET'])
def listar_usuarios_recientes():
    try:
        usuarios = obtener_usuarios_recientes()
        return jsonify(usuarios), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener usuarios recientes: {str(e)}"}), 500
