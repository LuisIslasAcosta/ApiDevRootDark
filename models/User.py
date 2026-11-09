import secrets
import re
from config.config import usuarios_collection
from utils.hash_utils import hash_contraseña
from flask import jsonify
from bson.objectid import ObjectId
from datetime import datetime
from utils.correo import (
    dominio_recibe_correo, correo_configurado, enviar_correo_verificacion
)


def buscar_por_email(email):
    """Busca un usuario por correo sin distinguir mayúsculas."""
    return usuarios_collection.find_one(
        {"email": {"$regex": f"^{re.escape((email or '').strip())}$", "$options": "i"}}
    )

def registrar_usuario(
    nombre, apellidop, apellidom, fecha_nacimiento,
    pais, ciudad, email, password, verificar_password,
    foto_perfil, pregunta_seguridad, respuesta_seguridad,
    telefono=None, imagen_binaria=None, imagen_nombre=None, imagen_tipo=None
):

    # Validar contraseñas iguales
    if password != verificar_password:
        return jsonify({"mensaje": "Las contraseñas no coinciden"}), 400

    # Validar email (formato y que el dominio realmente reciba correos)
    email = (email or "").strip().lower()
    if not re.match(r"^[\w\.+-]+@[\w\.-]+\.\w{2,}$", email):
        return jsonify({"mensaje": "Formato de correo electrónico inválido"}), 400
    if not dominio_recibe_correo(email):
        return jsonify({"mensaje": "Ese correo no existe: el dominio no recibe correos. Revisa que esté bien escrito."}), 400

    # Validar seguridad contraseña
    if len(password) < 12:
        return jsonify({"mensaje": "La contraseña debe tener al menos 12 caracteres"}), 400
    if not re.search(r"[A-Z]", password):
        return jsonify({"mensaje": "Debe incluir al menos una letra mayúscula"}), 400
    if not re.search(r"[a-z]", password):
        return jsonify({"mensaje": "Debe incluir al menos una letra minúscula"}), 400
    if not re.search(r"[0-9]", password):
        return jsonify({"mensaje": "Debe incluir al menos un número"}), 400
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return jsonify({"mensaje": "Debe incluir al menos un carácter especial"}), 400
    if "password" in password.lower() or "qwerty" in password.lower():
        return jsonify({"mensaje": "Evita usar palabras comunes"}), 400

    # Verificar correo único
    if buscar_por_email(email):
        return jsonify({"mensaje": "El correo electrónico ya está registrado"}), 400

    # Generar matrícula incremental
    ultimo = usuarios_collection.find_one({}, sort=[("matricula", -1)])
    nueva_matricula = f"{int(ultimo['matricula']) + 1:09d}" if ultimo else "000000001"

    # Asignar rol inicial
    existe_admin = usuarios_collection.find_one({"rol": "administrador"})
    rol_asignado = "usuario" if existe_admin else "administrador"

    # Hashes
    password_hash = hash_contraseña(password)
    respuesta_hash = hash_contraseña(respuesta_seguridad)

    # Construir usuario
    nuevo_usuario = {
        "matricula": nueva_matricula,
        "nombre": nombre,
        "apellidop": apellidop,
        "apellidom": apellidom,
        "fecha_nacimiento": fecha_nacimiento,
        "pais": pais,
        "ciudad": ciudad,
        "email": email,
        "telefono": telefono,
        "password": password_hash,
        "foto_perfil": foto_perfil,
        "pregunta_seguridad": pregunta_seguridad,
        "respuesta_seguridad": respuesta_hash,
        "rol": rol_asignado,
        # Si el envío de correos no está configurado, la cuenta queda activa como antes
        "verificado": not correo_configurado(),
        "fecha_registro": datetime.utcnow()
    }

    if imagen_binaria and imagen_nombre and imagen_tipo:
        nuevo_usuario["imagen_perfil"] = {
            "nombre": imagen_nombre,
            "tipo": imagen_tipo,
            "contenido": imagen_binaria
        }

    try:
        usuarios_collection.insert_one(nuevo_usuario)
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar usuario: {str(e)}"}), 500

    respuesta = {
        "matricula": nueva_matricula,
        "rol": rol_asignado,
        "email": email,
        "requiere_verificacion": not nuevo_usuario["verificado"],
    }

    if nuevo_usuario["verificado"]:
        print("ADVERTENCIA: MAIL_USERNAME/MAIL_PASSWORD no configurados; la cuenta se activó sin confirmar el correo.")
        respuesta["mensaje"] = "Usuario registrado correctamente. Ya puedes iniciar sesión."
        return jsonify(respuesta), 201

    try:
        enviar_correo_verificacion(email, nombre)
        usuarios_collection.update_one({"email": email}, {"$set": {"ultimo_envio_verificacion": datetime.utcnow()}})
        respuesta["mensaje"] = f"¡Cuenta creada! Te enviamos un correo a {email} para confirmarla. Revisa también la carpeta de spam."
        respuesta["correo_enviado"] = True
    except Exception as e:
        print(f"ERROR al enviar correo de verificación a {email}: {e}")
        respuesta["mensaje"] = ("Tu cuenta se creó, pero no pudimos enviar el correo de confirmación. "
                                "Intenta reenviarlo desde la pantalla de inicio de sesión.")
        respuesta["correo_enviado"] = False
    return jsonify(respuesta), 201


def actualizar_contraseña(usuario_id, nueva_contraseña):
    password_hash = hash_contraseña(nueva_contraseña)

    resultado = usuarios_collection.update_one(
        {"_id": ObjectId(usuario_id)},
        {"$set": {"password": password_hash}}
    )

    return resultado.modified_count > 0


def _siguiente_matricula_y_rol():
    ultimo = usuarios_collection.find_one({}, sort=[("matricula", -1)])
    matricula = f"{int(ultimo['matricula']) + 1:09d}" if ultimo else "000000001"
    rol = "usuario" if usuarios_collection.find_one({"rol": "administrador"}) else "administrador"
    return matricula, rol


def obtener_o_crear_usuario_google(datos_google):
    """
    Usa los datos verificados por Google para entrar o crear la cuenta.
    datos_google: email, given_name, family_name, name, picture, sub
    """
    email = (datos_google.get("email") or "").strip().lower()
    usuario = buscar_por_email(email)

    if usuario:
        cambios = {"google_id": datos_google.get("sub")}
        # Google ya comprobó que el correo es suyo
        if usuario.get("verificado") is False:
            cambios.update({"verificado": True, "fecha_verificacion": datetime.utcnow()})
        if not usuario.get("foto_url") and datos_google.get("picture"):
            cambios["foto_url"] = datos_google.get("picture")
        usuarios_collection.update_one({"_id": usuario["_id"]}, {"$set": cambios})
        return usuarios_collection.find_one({"_id": usuario["_id"]}), False

    apellidos = (datos_google.get("family_name") or "").split(" ", 1)
    matricula, rol = _siguiente_matricula_y_rol()
    nuevo = {
        "matricula": matricula,
        "nombre": datos_google.get("given_name") or datos_google.get("name") or email.split("@")[0],
        "apellidop": apellidos[0] if apellidos else "",
        "apellidom": apellidos[1] if len(apellidos) > 1 else "",
        "fecha_nacimiento": "",
        "pais": "",
        "ciudad": "",
        "email": email,
        "telefono": "",
        # Contraseña aleatoria: estas cuentas entran con Google
        "password": hash_contraseña(secrets.token_urlsafe(32)),
        "foto_perfil": None,
        "foto_url": datos_google.get("picture"),
        "pregunta_seguridad": "",
        "respuesta_seguridad": "",
        "rol": rol,
        "verificado": True,
        "proveedor": "google",
        "google_id": datos_google.get("sub"),
        "fecha_registro": datetime.utcnow(),
    }
    resultado = usuarios_collection.insert_one(nuevo)
    nuevo["_id"] = resultado.inserted_id
    return nuevo, True
