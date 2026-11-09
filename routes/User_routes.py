from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from bson.objectid import ObjectId

from controllers.auth import validar_login
from controllers.user import (
    obtener_usuarios,
    obtener_usuario_por_id,
    actualizar_usuario,
    eliminar_usuario,
    obtener_usuarios_recientes
)

from models.User import registrar_usuario, actualizar_contraseña, buscar_por_email, obtener_o_crear_usuario_google
from controllers.auth import respuesta_login
import os
from google.oauth2 import id_token as google_id_token
from google.auth.transport import requests as google_requests
from utils.correo import leer_token_verificacion, enviar_correo_verificacion, correo_configurado
from datetime import datetime, timedelta
from config.config import usuarios_collection
from utils.hash_utils import verificar_hash

user_bp = Blueprint('user_bp', __name__)

# ============================= LOGIN =============================
@user_bp.route('/login', methods=['POST'])
def login():
    datos = request.json
    email = datos.get('email')
    password = datos.get('password')

    if not email or not password:
        return jsonify({"mensaje": "El correo y la contraseña son necesarios"}), 400

    resultado = validar_login(email, password)

    if resultado and resultado.get("error") == "correo_no_verificado":
        return jsonify({
            "mensaje": "Confirma tu correo antes de iniciar sesión. Revisa tu bandeja de entrada o spam.",
            "codigo": "correo_no_verificado",
            "email": resultado.get("email"),
        }), 403

    if resultado:
        return jsonify(resultado), 200
    else:
        return jsonify({"mensaje": "Correo o contraseña incorrectos"}), 401


# ============================= LOGIN CON GOOGLE =============================
_google_request = google_requests.Request()


@user_bp.route('/login/google', methods=['POST'])
def login_google():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        return jsonify({"mensaje": "El inicio de sesión con Google no está configurado."}), 503

    credencial = (request.json or {}).get("credential")
    if not credencial:
        return jsonify({"mensaje": "Falta la credencial de Google."}), 400

    try:
        # Verifica firma, vigencia y que el token sea para ESTA aplicación
        datos = google_id_token.verify_oauth2_token(credencial, _google_request, client_id)
    except ValueError:
        return jsonify({"mensaje": "No se pudo verificar tu cuenta de Google. Intenta de nuevo."}), 401
    except Exception as e:
        print(f"ERROR al contactar a Google: {e}")
        return jsonify({"mensaje": "No se pudo contactar a Google. Intenta en un momento."}), 503

    if datos.get("iss") not in ("accounts.google.com", "https://accounts.google.com"):
        return jsonify({"mensaje": "Credencial de Google no válida."}), 401
    if not datos.get("email") or not datos.get("email_verified"):
        return jsonify({"mensaje": "Tu cuenta de Google no tiene un correo verificado."}), 401

    usuario, es_nuevo = obtener_o_crear_usuario_google(datos)
    respuesta = respuesta_login(usuario)
    respuesta["nuevo"] = es_nuevo
    return jsonify(respuesta), 201 if es_nuevo else 200


# ============================= REGISTRO =============================
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


# ============================= CONFIRMAR CORREO =============================
@user_bp.route('/verificar-correo', methods=['POST'])
def verificar_correo():
    token = (request.json or {}).get("token", "")
    email, error = leer_token_verificacion(token)

    if error == "expirado":
        return jsonify({"mensaje": "El enlace ya expiró. Pide uno nuevo desde el inicio de sesión.", "codigo": "expirado"}), 400
    if error:
        return jsonify({"mensaje": "El enlace no es válido.", "codigo": "invalido"}), 400

    usuario = buscar_por_email(email)
    if not usuario:
        return jsonify({"mensaje": "La cuenta ya no existe.", "codigo": "invalido"}), 404

    if usuario.get("verificado") is not False:
        return jsonify({"mensaje": "Tu correo ya estaba confirmado. Ya puedes iniciar sesión.", "codigo": "ya_verificado"}), 200

    usuarios_collection.update_one(
        {"_id": usuario["_id"]},
        {"$set": {"verificado": True, "fecha_verificacion": datetime.utcnow()}}
    )
    return jsonify({"mensaje": "¡Correo confirmado! Ya puedes iniciar sesión.", "codigo": "verificado"}), 200


@user_bp.route('/reenviar-verificacion', methods=['POST'])
def reenviar_verificacion():
    email = ((request.json or {}).get("email") or "").strip()
    respuesta_generica = {"mensaje": "Si la cuenta existe y no está confirmada, te enviamos un nuevo correo."}

    if not email:
        return jsonify({"mensaje": "Escribe tu correo."}), 400
    if not correo_configurado():
        return jsonify({"mensaje": "El envío de correos no está disponible en este momento."}), 503

    usuario = buscar_por_email(email)
    if not usuario or usuario.get("verificado") is not False:
        return jsonify(respuesta_generica), 200

    # Evitar abusos: un correo por minuto
    ultimo = usuario.get("ultimo_envio_verificacion")
    if ultimo and datetime.utcnow() - ultimo < timedelta(seconds=60):
        return jsonify({"mensaje": "Espera un minuto antes de pedir otro correo."}), 429

    try:
        enviar_correo_verificacion(usuario["email"], usuario.get("nombre"))
    except Exception as e:
        print(f"ERROR al reenviar verificación a {email}: {e}")
        return jsonify({"mensaje": "No se pudo enviar el correo. Intenta más tarde."}), 502

    usuarios_collection.update_one({"_id": usuario["_id"]}, {"$set": {"ultimo_envio_verificacion": datetime.utcnow()}})
    return jsonify(respuesta_generica), 200


# ============================= ADMIN: ACTUALIZAR CONTRASEÑA =============================
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
        return jsonify({"mensaje": "ID inválido"}), 400


# ============================= USUARIOS =============================
@user_bp.route('/usuarios/<usuario_id>', methods=['GET'])
def obtener_usuario(usuario_id):
    usuario = obtener_usuario_por_id(usuario_id)
    if usuario:
        return jsonify(usuario), 200
    return jsonify({"mensaje": "Usuario no encontrado"}), 404


@user_bp.route('/usuarios/<usuario_id>', methods=['PUT'])
def actualizar_usuario_route(usuario_id):
    try:
        exito = actualizar_usuario(usuario_id, request.json)
        return jsonify({"mensaje": "Usuario actualizado correctamente"}), 200 if exito else 400
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400


@user_bp.route('/usuarios/<usuario_id>', methods=['DELETE'])
def eliminar_usuario_route(usuario_id):
    try:
        exito = eliminar_usuario(usuario_id)
        return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200 if exito else 400
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400


@user_bp.route('/usuarios', methods=['GET'])
def listar_usuarios():
    return jsonify(obtener_usuarios()), 200


@user_bp.route('/usuarios/recientes', methods=['GET'])
def listar_usuarios_recientes():
    try:
        return jsonify(obtener_usuarios_recientes()), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error: {str(e)}"}), 500


# ============================= RECUPERAR CONTRASEÑA POR PREGUNTA =============================

#  Obtener pregunta por email
@user_bp.route('/recuperar/pregunta', methods=['POST'])
def obtener_pregunta():
    datos = request.json
    email = datos.get("email")

    if not email:
        return jsonify({"mensaje": "Correo requerido"}), 400

    usuario = usuarios_collection.find_one({"email": email})

    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    return jsonify({
        "usuario_id": str(usuario["_id"]),
        "pregunta_seguridad": usuario.get("pregunta_seguridad")
    }), 200


#  Verificar respuesta de seguridad
@user_bp.route('/recuperar/verificar', methods=['POST'])
def verificar_respuesta():
    datos = request.json
    usuario_id = datos.get("usuario_id")
    respuesta = datos.get("respuesta")

    if not usuario_id or not respuesta:
        return jsonify({"mensaje": "Datos incompletos"}), 400

    try:
        usuario = usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    except:
        return jsonify({"mensaje": "ID inválido"}), 400

    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    respuesta_guardada = usuario.get("respuesta_seguridad")

    #  CORREGIDO: primero texto ingresado, luego hash guardado
    if not verificar_hash(respuesta, respuesta_guardada):
        return jsonify({"mensaje": "Respuesta incorrecta"}), 401

    return jsonify({"mensaje": "Respuesta correcta"}), 200


#  Resetear contraseña SOLO si la respuesta es correcta
@user_bp.route('/recuperar/reset', methods=['PUT'])
def reset_password():
    datos = request.json
    usuario_id = datos.get("usuario_id")
    nueva_password = datos.get("nueva_password")
    respuesta = datos.get("respuesta")  #  requerimos la respuesta de seguridad

    if not usuario_id or not nueva_password or not respuesta:
        return jsonify({"mensaje": "Datos incompletos"}), 400

    try:
        usuario = usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    except:
        return jsonify({"mensaje": "ID inválido"}), 400

    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    #  Verificamos la respuesta antes de actualizar la contraseña
    if not verificar_hash(respuesta, usuario.get("respuesta_seguridad")):
        return jsonify({"mensaje": "Respuesta incorrecta"}), 401

    exito = actualizar_contraseña(usuario_id, nueva_password)
    if exito:
        return jsonify({"mensaje": "Contraseña actualizada correctamente"}), 200

    return jsonify({"mensaje": "Error al actualizar contraseña"}), 400
