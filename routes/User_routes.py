from flask import Blueprint, request, jsonify
from bson.errors import InvalidId
from bson.objectid import ObjectId

from controllers.auth import validar_login, revisar_terminos
from flask_jwt_extended import jwt_required, get_jwt_identity
from utils.terminos import version_vigente, terminos_pendientes, info_pendiente, registrar_aceptacion
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
from flask_jwt_extended import get_jwt
from models.User import problema_contrasena
from controllers.sesiones import (
    bloqueado, registrar_fallo, limpiar_intentos,
    renovacion_vigente, rotar, revocar_token, revocar_todas,
)
from controllers.user import serializar_usuario
from utils.seguridad import (
    error, texto, ip_cliente, rol_requerido, sesion_requerida, solo_admin,
    usuario_sesion, es_admin, es_staff, puede_ver_alumno,
)

user_bp = Blueprint('user_bp', __name__)

# ============================= LOGIN =============================
@user_bp.route('/login', methods=['POST'])
def login():
    datos = request.get_json(silent=True) or {}
    email = texto(datos.get('email'), 254).lower()
    password = datos.get('password') if isinstance(datos.get('password'), str) else ""

    if not email or not password:
        return jsonify({"mensaje": "El correo y la contraseña son necesarios"}), 400

    # Límite de intentos fallidos por correo y por dirección IP (contra fuerza bruta)
    espera = max(bloqueado("login", email), bloqueado("login_ip", ip_cliente()))
    if espera:
        return jsonify({"mensaje": f"Demasiados intentos fallidos. Intenta de nuevo en {espera} minutos."}), 429

    resultado = validar_login(email, password, datos.get('acepta_terminos') is True)

    if resultado and resultado.get("error") == "terminos_pendientes":
        resultado.pop("error")
        return jsonify(resultado), 403

    if resultado and resultado.get("error") == "correo_no_verificado":
        return jsonify({
            "mensaje": "Confirma tu correo antes de iniciar sesión. Revisa tu bandeja de entrada o spam.",
            "codigo": "correo_no_verificado",
            "email": resultado.get("email"),
        }), 403

    if resultado:
        limpiar_intentos("login", email)
        return jsonify(resultado), 200

    registrar_fallo("login", email)
    registrar_fallo("login_ip", ip_cliente())
    return jsonify({"mensaje": "Correo o contraseña incorrectos"}), 401


# ============================= SESIÓN =============================
@user_bp.route('/me', methods=['GET'])
@sesion_requerida
def yo():
    """Datos y rol del usuario según el servidor (el frontend no debe confiar en su propia copia)."""
    return jsonify(serializar_usuario(usuario_sesion())), 200


@user_bp.route('/token/renovar', methods=['POST'])
@jwt_required(refresh=True)
def renovar_token():
    """Cambia el token de renovación por uno nuevo y entrega un token de acceso nuevo."""
    datos = get_jwt()
    if not renovacion_vigente(datos["jti"]):
        return jsonify({"mensaje": "La sesión se cerró. Inicia sesión de nuevo."}), 401
    usuario_id = get_jwt_identity()
    if not ObjectId.is_valid(str(usuario_id)) or not usuarios_collection.find_one({"_id": ObjectId(str(usuario_id))}, {"_id": 1}):
        return jsonify({"mensaje": "La cuenta ya no existe."}), 401
    acceso, renovacion = rotar(datos["jti"], usuario_id)
    return jsonify({"access_token": acceso, "refresh_token": renovacion}), 200


@user_bp.route('/logout', methods=['POST'])
def logout():
    """Revoca el token de renovación: aunque alguien lo haya copiado, ya no sirve."""
    token = (request.get_json(silent=True) or {}).get("refresh_token")
    if isinstance(token, str) and token:
        revocar_token(token)
    return jsonify({"mensaje": "Sesión cerrada"}), 200


# ============================= LOGIN CON GOOGLE =============================
_google_request = google_requests.Request()


@user_bp.route('/login/google', methods=['POST'])
def login_google():
    client_id = os.getenv("GOOGLE_CLIENT_ID")
    if not client_id:
        return jsonify({"mensaje": "El inicio de sesión con Google no está configurado."}), 503

    credencial = (request.json or {}).get("credential")
    acepta_terminos = (request.json or {}).get("acepta_terminos") is True
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
    pendiente = revisar_terminos(usuario, acepta_terminos)
    if pendiente:
        pendiente.pop("error")
        return jsonify(pendiente), 403
    respuesta = respuesta_login(usuario)
    respuesta["nuevo"] = es_nuevo
    return jsonify(respuesta), 201 if es_nuevo else 200


# ============================= REGISTRO =============================
@user_bp.route('/registrar', methods=['POST'])
def registrar():
    crudo = request.get_json(silent=True) or {}
    datos = {k: (v if k in ("foto_perfil", "password", "verificar_password") and isinstance(v, str) else texto(v, 254)) for k, v in crudo.items()
             if k != "acepta_terminos"}
    datos["acepta_terminos"] = crudo.get("acepta_terminos")

    if datos.get('acepta_terminos') is not True:
        return jsonify({"mensaje": "Debes aceptar los términos y condiciones para crear tu cuenta.",
                        "codigo": "terminos_requeridos"}), 400

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

    if status_code == 201:
        nuevo = buscar_por_email((datos.get('email') or '').strip())
        if nuevo:
            registrar_aceptacion(nuevo["_id"])

    return resultado, status_code


# ============================= TÉRMINOS Y CONDICIONES =============================
@user_bp.route('/terminos', methods=['GET'])
def terminos_vigentes():
    return jsonify({"version": version_vigente()}), 200


@user_bp.route('/terminos/estado', methods=['GET'])
@jwt_required()
def terminos_estado():
    try:
        usuario = usuarios_collection.find_one({"_id": ObjectId(str(get_jwt_identity()))})
    except (InvalidId, TypeError):
        usuario = None
    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404
    if terminos_pendientes(usuario):
        return jsonify({"pendiente": True, **info_pendiente(usuario)}), 200
    return jsonify({"pendiente": False, "version": version_vigente()}), 200


@user_bp.route('/terminos/aceptar', methods=['POST'])
@jwt_required()
def terminos_aceptar():
    if (request.json or {}).get('acepta_terminos') is not True:
        return jsonify({"mensaje": "Marca la casilla para aceptar los términos."}), 400
    try:
        version = registrar_aceptacion(get_jwt_identity())
    except (InvalidId, TypeError):
        return jsonify({"mensaje": "Usuario no válido"}), 400
    return jsonify({"mensaje": "Términos aceptados", "version": version}), 200


# ============================= CONFIRMAR CORREO =============================
@user_bp.route('/verificar-correo', methods=['POST'])
def verificar_correo():
    token = texto((request.get_json(silent=True) or {}).get("token", ""), 1000)
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
    email = texto((request.get_json(silent=True) or {}).get("email"), 254)
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
@rol_requerido("administrador", fresco=True)
def recuperar_contraseña(usuario_id):
    datos = request.get_json(silent=True) or {}
    nueva_contraseña = datos.get('nueva_contraseña')

    problema = problema_contrasena(nueva_contraseña)
    if problema:
        return jsonify({"mensaje": problema}), 400

    try:
        exito = actualizar_contraseña(usuario_id, nueva_contraseña)
        if exito:
            revocar_todas(usuario_id)
            return jsonify({"mensaje": "Contraseña actualizada correctamente"}), 200
        else:
            return jsonify({"mensaje": "No se pudo actualizar la contraseña"}), 400
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400


# ============================= USUARIOS =============================
@user_bp.route('/usuarios/<usuario_id>', methods=['GET'])
@sesion_requerida
def obtener_usuario(usuario_id):
    # El propio usuario, el administrador o un profesor con ese alumno en sus cursos
    if not puede_ver_alumno(usuario_sesion(), usuario_id):
        return error(403, "No tienes permiso para ver este usuario.")
    try:
        usuario = obtener_usuario_por_id(usuario_id)
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400
    if usuario:
        return jsonify(usuario), 200
    return jsonify({"mensaje": "Usuario no encontrado"}), 404


@user_bp.route('/usuarios/<usuario_id>', methods=['PUT'])
@sesion_requerida
def actualizar_usuario_route(usuario_id):
    """El usuario edita su perfil; el administrador además puede cambiar rol y contraseña."""
    yo_mismo = usuario_sesion()
    admin = es_admin(yo_mismo)
    if str(yo_mismo["_id"]) != str(usuario_id) and not admin:
        return error(403, "Solo puedes editar tu propio perfil.")
    datos = request.get_json(silent=True) or {}
    try:
        objetivo = usuarios_collection.find_one({"_id": ObjectId(usuario_id)}, {"rol": 1})
    except (InvalidId, TypeError):
        return jsonify({"mensaje": "ID inválido"}), 400
    if not objetivo:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    # No dejar el sistema sin administradores
    if admin and objetivo.get("rol") == "administrador" and datos.get("rol") not in (None, "administrador"):
        if usuarios_collection.count_documents({"rol": "administrador"}) <= 1:
            return jsonify({"mensaje": "Debe quedar al menos un administrador."}), 400

    cambios = False
    if admin and datos.get("password"):
        problema = problema_contrasena(datos.get("password"))
        if problema:
            return jsonify({"mensaje": problema}), 400
        actualizar_contraseña(usuario_id, datos["password"])
        revocar_todas(usuario_id)
        cambios = True

    exito = actualizar_usuario(usuario_id, datos, como_admin=admin) or cambios
    return jsonify({"mensaje": "Usuario actualizado correctamente" if exito else "No hubo cambios"}), 200 if exito else 400


@user_bp.route('/usuarios/<usuario_id>', methods=['DELETE'])
@solo_admin
def eliminar_usuario_route(usuario_id):
    if str(usuario_sesion()["_id"]) == str(usuario_id):
        return jsonify({"mensaje": "No puedes eliminar tu propia cuenta de administrador."}), 400
    try:
        exito = eliminar_usuario(usuario_id)
        if exito:
            revocar_todas(usuario_id)
        return jsonify({"mensaje": "Usuario eliminado correctamente"}), 200 if exito else 400
    except InvalidId:
        return jsonify({"mensaje": "ID inválido"}), 400


@user_bp.route('/usuarios', methods=['GET'])
@solo_admin
def listar_usuarios():
    return jsonify(obtener_usuarios()), 200


@user_bp.route('/usuarios/recientes', methods=['GET'])
@solo_admin
def listar_usuarios_recientes():
    try:
        return jsonify(obtener_usuarios_recientes()), 200
    except Exception as e:
        print(f"ERROR usuarios recientes: {e}")
        return jsonify({"mensaje": "No se pudieron obtener los usuarios"}), 500


# ============================= RECUPERAR CONTRASEÑA POR PREGUNTA =============================

#  Obtener pregunta por email
@user_bp.route('/recuperar/pregunta', methods=['POST'])
def obtener_pregunta():
    datos = request.get_json(silent=True) or {}
    email = texto(datos.get("email"), 254)

    if not email:
        return jsonify({"mensaje": "Correo requerido"}), 400
    if bloqueado("recuperar_ip", ip_cliente()):
        return jsonify({"mensaje": "Demasiados intentos. Espera unos minutos."}), 429

    usuario = buscar_por_email(email)

    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    return jsonify({
        "usuario_id": str(usuario["_id"]),
        "pregunta_seguridad": usuario.get("pregunta_seguridad")
    }), 200


#  Verificar respuesta de seguridad
@user_bp.route('/recuperar/verificar', methods=['POST'])
def verificar_respuesta():
    datos = request.get_json(silent=True) or {}
    usuario_id = texto(datos.get("usuario_id"), 40)
    respuesta = texto(datos.get("respuesta"), 200)

    if not usuario_id or not respuesta:
        return jsonify({"mensaje": "Datos incompletos"}), 400
    espera = max(bloqueado("recuperar", usuario_id), bloqueado("recuperar_ip", ip_cliente()))
    if espera:
        return jsonify({"mensaje": f"Demasiados intentos. Intenta de nuevo en {espera} minutos."}), 429

    try:
        usuario = usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    except Exception:
        return jsonify({"mensaje": "ID inválido"}), 400

    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    respuesta_guardada = usuario.get("respuesta_seguridad")

    if not respuesta_guardada or not verificar_hash(respuesta, respuesta_guardada):
        registrar_fallo("recuperar", usuario_id)
        registrar_fallo("recuperar_ip", ip_cliente())
        return jsonify({"mensaje": "Respuesta incorrecta"}), 401

    return jsonify({"mensaje": "Respuesta correcta"}), 200


#  Resetear contraseña SOLO si la respuesta es correcta
@user_bp.route('/recuperar/reset', methods=['PUT'])
def reset_password():
    datos = request.get_json(silent=True) or {}
    usuario_id = texto(datos.get("usuario_id"), 40)
    nueva_password = datos.get("nueva_password") if isinstance(datos.get("nueva_password"), str) else ""
    respuesta = texto(datos.get("respuesta"), 200)  #  requerimos la respuesta de seguridad

    if not usuario_id or not nueva_password or not respuesta:
        return jsonify({"mensaje": "Datos incompletos"}), 400
    espera = max(bloqueado("recuperar", usuario_id), bloqueado("recuperar_ip", ip_cliente()))
    if espera:
        return jsonify({"mensaje": f"Demasiados intentos. Intenta de nuevo en {espera} minutos."}), 429

    try:
        usuario = usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    except Exception:
        return jsonify({"mensaje": "ID inválido"}), 400

    if not usuario:
        return jsonify({"mensaje": "Usuario no encontrado"}), 404

    #  Verificamos la respuesta antes de actualizar la contraseña
    if not usuario.get("respuesta_seguridad") or not verificar_hash(respuesta, usuario.get("respuesta_seguridad")):
        registrar_fallo("recuperar", usuario_id)
        registrar_fallo("recuperar_ip", ip_cliente())
        return jsonify({"mensaje": "Respuesta incorrecta"}), 401

    problema = problema_contrasena(nueva_password)
    if problema:
        return jsonify({"mensaje": problema}), 400

    exito = actualizar_contraseña(usuario_id, nueva_password)
    if exito:
        limpiar_intentos("recuperar", usuario_id)
        revocar_todas(usuario_id)  # cierra las sesiones abiertas con la contraseña anterior
        return jsonify({"mensaje": "Contraseña actualizada correctamente"}), 200

    return jsonify({"mensaje": "Error al actualizar contraseña"}), 400
