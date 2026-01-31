import base64
from models.models import User
from extensions import db
from utils.hash_utils import hash_contraseña
from datetime import datetime
from uuid import uuid4

def serializar_usuario(usuario: User):
    """Convierte un objeto User en diccionario."""
    foto_perfil = usuario.foto_perfil
    if isinstance(foto_perfil, (bytes, bytearray)):
        foto_perfil = base64.b64encode(foto_perfil).decode("utf-8")

    return {
        "id": usuario.id,
        "matricula": usuario.matricula,
        "nombre": usuario.nombre,
        "email": usuario.email,
        "password": usuario.password,
        "foto_perfil": foto_perfil,
        "rol": usuario.rol
    }
    
def registrar_usuario(nombre, apellidop, apellidom, fecha_nacimiento, pais, ciudad,
                      email, password, verificar_password, foto_perfil,
                      pregunta_seguridad, respuesta_seguridad, telefono):
    # Validar contraseñas
    if password != verificar_password:
        return {"mensaje": "Las contraseñas no coinciden"}, 400

    # Validar si el correo ya existe
    if User.query.filter_by(email=email).first():
        return {"mensaje": "El correo ya está registrado"}, 400

    # Convertir fecha
    try:
        fecha_nacimiento = datetime.strptime(fecha_nacimiento, "%Y-%m-%d").date()
    except Exception:
        return {"mensaje": "Formato de fecha inválido, usa YYYY-MM-DD"}, 400

    # Normalizar foto_perfil
    if foto_perfil:
        try:
            if isinstance(foto_perfil, str) and foto_perfil.strip() != "":
                foto_perfil = base64.b64decode(foto_perfil)
            else:
                foto_perfil = None
        except Exception:
            foto_perfil = None
    else:
        foto_perfil = None

    nuevo_usuario = User(
        matricula=str(uuid4())[:9],
        nombre=nombre,
        apellidop=apellidop,
        apellidom=apellidom,
        fecha_nacimiento=fecha_nacimiento,
        pais=pais,
        ciudad=ciudad,
        email=email,
        telefono=telefono,
        password=hash_contraseña(password),
        foto_perfil=foto_perfil,
        pregunta_seguridad=pregunta_seguridad,
        respuesta_seguridad=hash_contraseña(respuesta_seguridad),
        rol="usuario"
    )

    db.session.add(nuevo_usuario)
    try:
        db.session.commit()
        return {"mensaje": "Usuario registrado correctamente", "usuario": {"id": nuevo_usuario.id, "email": nuevo_usuario.email}}, 201
    except Exception as e:
        db.session.rollback()
        return {"mensaje": f"Error al registrar usuario: {str(e)}"}, 500



def obtener_usuarios():
    usuarios = User.query.all()
    return [serializar_usuario(u) for u in usuarios]

def obtener_usuario_por_id(usuario_id):
    usuario = User.query.get(usuario_id)
    return serializar_usuario(usuario) if usuario else None

def actualizar_usuario(usuario_id, datos_actualizados):
    usuario = User.query.get(usuario_id)
    if not usuario:
        return False
    for campo, valor in datos_actualizados.items():
        if hasattr(usuario, campo):
            setattr(usuario, campo, valor)
    db.session.commit()
    return True

def eliminar_usuario(usuario_id):
    usuario = User.query.get(usuario_id)
    if not usuario:
        return False
    db.session.delete(usuario)
    db.session.commit()
    return True

def actualizar_contraseña(usuario_id, nueva_contraseña):
    usuario = User.query.get(usuario_id)
    if not usuario:
        return False
    usuario.set_password(nueva_contraseña)
    db.session.commit()
    return True
