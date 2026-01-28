import re
from config.config import usuarios_collection
from utils.hash_utils import hash_contraseña
from flask import jsonify

def registrar_usuario(nombre, apellidop, apellidom, fecha_nacimiento, pais, ciudad, email, password, verificar_password, foto_perfil,
                pregunta_seguridad, respuesta_seguridad,telefono=None, imagen_binaria=None, imagen_nombre=None, imagen_tipo=None):
    """Registra un nuevo usuario en la base de datos con matrícula, rol y pregunta de seguridad."""

    if password != verificar_password:
        return jsonify({"mensaje": "Las contraseñas no coinciden"}), 400

    if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
        return jsonify({"mensaje": "Formato de correo electrónico inválido"}), 400

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
        return jsonify({"mensaje": "Evita usar palabras comunes como 'password' o 'qwerty'"}), 400

    if usuarios_collection.find_one({"email": email}):
        return jsonify({"mensaje": "El correo electrónico ya está registrado"}), 400

    ultimo_usuario = usuarios_collection.find_one({}, sort=[("matricula", -1)])
    nueva_matricula = f"{int(ultimo_usuario['matricula']) + 1:09d}" if ultimo_usuario else "000000001"

    existe_admin = usuarios_collection.find_one({"rol": "administrador"})
    rol_asignado = "usuario" if existe_admin else "administrador"

    contraseña_hash = hash_contraseña(password)
    respuesta_hash = hash_contraseña(respuesta_seguridad)

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
        "password": contraseña_hash,
        "foto_perfil": foto_perfil,
        "pregunta_seguridad": pregunta_seguridad,
        "respuesta_seguridad": respuesta_hash,
        "rol": rol_asignado
    }

    if imagen_binaria and imagen_nombre and imagen_tipo:
        nuevo_usuario["imagen_perfil"] = {
            "nombre": imagen_nombre,
            "tipo": imagen_tipo,
            "contenido": imagen_binaria
        }

    try:
        usuarios_collection.insert_one(nuevo_usuario)
        return jsonify({
            "mensaje": f"Usuario registrado correctamente con matrícula {nueva_matricula} y rol '{rol_asignado}'",
            "id": nueva_matricula
        }), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar usuario: {str(e)}"}), 500
    
def actualizar_contraseña(usuario_id, nueva_contraseña):
    """Actualiza la contraseña de un usuario."""
    contraseña_hash = hash_contraseña(nueva_contraseña)
    resultado = usuarios_collection.update_one(
        {"_id": usuario_id},
        {"$set": {"password": contraseña_hash}}
    )
    return resultado.modified_count > 0

