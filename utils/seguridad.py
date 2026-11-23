"""Seguridad de la API.

- Todo el control de acceso se decide AQUÍ, en el servidor, con el usuario del token
  firmado (JWT). El rol nunca se toma de lo que manda el navegador.
- rol_requerido(...)  exige sesión y, opcionalmente, ciertos roles.
- admin_requerido(...) exige administrador y registra la acción en la bitácora.
- Funciones para saber si un usuario puede gestionar un curso, ver su contenido o
  consultar los datos de un alumno.
"""
from datetime import datetime, timezone
from functools import wraps

from bson.objectid import ObjectId
from flask import g, jsonify, request
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request
from flask_jwt_extended.exceptions import FreshTokenRequired
from jwt.exceptions import ExpiredSignatureError

from config.config import cursos_collection, db, inscripciones_collection, usuarios_collection

auditoria_collection = db["auditoria_respaldos"]

ROLES_STAFF = ("profesor", "administrador")
# Campos que nunca salen del servidor al cargar el usuario de la sesión
_OCULTOS = {"password": 0, "respuesta_seguridad": 0}


# ================= UTILIDADES =================
def error(codigo, mensaje, clave=None):
    """Respuesta de error con los dos nombres de campo que usa el frontend.

    clave: código corto para el frontend (p. ej. "token_expirado" para renovar la sesión).
    """
    datos = {"mensaje": mensaje, "message": mensaje}
    if clave:
        datos["codigo"] = clave
    return jsonify(datos), codigo


def texto(valor, maximo=500):
    """Convierte la entrada a texto plano (evita inyección NoSQL con objetos como {"$ne": ...})."""
    if isinstance(valor, (dict, list, tuple, set)) or valor is None:
        return ""
    return str(valor).strip()[:maximo]


def variantes_id(valor):
    valor = str(valor)
    return [valor] + ([ObjectId(valor)] if ObjectId.is_valid(valor) else [])


def ip_cliente():
    return (request.headers.get("X-Forwarded-For", request.remote_addr) or "").split(",")[0].strip()


def _usuario_actual():
    usuario_id = str(get_jwt_identity() or "")
    if not ObjectId.is_valid(usuario_id):
        return None
    return usuarios_collection.find_one({"_id": ObjectId(usuario_id)}, _OCULTOS)


def usuario_sesion():
    """Usuario de la petición actual (después de rol_requerido)."""
    return getattr(g, "usuario", None)


def es_admin(usuario):
    return bool(usuario) and usuario.get("rol") == "administrador"


def es_staff(usuario):
    return bool(usuario) and usuario.get("rol") in ROLES_STAFF


# ================= DECORADORES =================
def rol_requerido(*roles, fresco=False):
    """Exige un token válido; si se indican roles, el usuario debe tener uno de ellos.

    fresco=True exige un token emitido al iniciar sesión con contraseña hace poco
    (reautenticación), no uno renovado automáticamente.
    """
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            if request.method == "OPTIONS":
                return funcion(*args, **kwargs)
            try:
                verify_jwt_in_request(fresh=fresco)
            except FreshTokenRequired:
                return error(401, "Por seguridad, vuelve a escribir tu contraseña para continuar.", "requiere_contrasena")
            except ExpiredSignatureError:
                return error(401, "Tu sesión expiró.", "token_expirado")
            except Exception:
                return error(401, "Inicia sesión para continuar.", "sin_sesion")
            usuario = _usuario_actual()
            if not usuario:
                return error(401, "Tu sesión ya no es válida. Inicia sesión de nuevo.")
            if roles and usuario.get("rol") not in roles:
                return error(403, "No tienes permiso para realizar esta acción.")
            g.usuario = usuario
            return funcion(*args, **kwargs)
        return envoltura
    return decorador


sesion_requerida = rol_requerido()
staff_requerido = rol_requerido(*ROLES_STAFF)
solo_admin = rol_requerido("administrador")


def registrar_auditoria(accion, detalle="", exito=True):
    """Guarda quién hizo qué, cuándo y desde dónde (no debe romper la petición si falla)."""
    try:
        usuario = usuario_sesion() or _usuario_actual() or {}
    except Exception:  # token rechazado (p. ej. no fresco): se registra sin usuario
        usuario = {}
    try:
        auditoria_collection.insert_one({
            "accion": accion,
            "detalle": detalle,
            "exito": exito,
            "usuario_id": str(usuario.get("_id", "")),
            "email": usuario.get("email", ""),
            "ip": ip_cliente(),
            "fecha": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:  # la bitácora nunca debe tumbar la operación
        print(f"No se pudo registrar la auditoría: {e}")


def admin_requerido(accion, fresco=False):
    """Exige token JWT válido y rol administrador. Registra cada intento en la bitácora."""
    def decorador(funcion):
        @wraps(funcion)
        def envoltura(*args, **kwargs):
            try:
                verify_jwt_in_request(fresh=fresco)
            except FreshTokenRequired:
                registrar_auditoria(accion, "Denegado: se requiere volver a escribir la contraseña", exito=False)
                return error(401, "Por seguridad, vuelve a iniciar sesión con tu contraseña para usar los respaldos.", "requiere_contrasena")
            except ExpiredSignatureError:
                return error(401, "Tu sesión expiró.", "token_expirado")
            except Exception:
                return error(401, "Inicia sesión como administrador")

            usuario = _usuario_actual()
            if not usuario or usuario.get("rol") != "administrador":
                registrar_auditoria(accion, "Acceso denegado: el usuario no es administrador", exito=False)
                return error(403, "Solo el administrador puede realizar esta acción")
            g.usuario = usuario

            respuesta = funcion(*args, **kwargs)
            codigo = respuesta[1] if isinstance(respuesta, tuple) and len(respuesta) > 1 else getattr(respuesta, "status_code", 200)
            registrar_auditoria(accion, str(kwargs) if kwargs else "", exito=int(codigo) < 400)
            return respuesta
        return envoltura
    return decorador


# ================= PERMISOS SOBRE CURSOS Y ALUMNOS =================
def curso_por_id(curso_id):
    if not ObjectId.is_valid(str(curso_id)):
        return None
    return cursos_collection.find_one({"_id": ObjectId(str(curso_id))})


def puede_gestionar_curso(usuario, curso):
    """Administrador, o el profesor dueño del curso."""
    if not usuario or not curso:
        return False
    return es_admin(usuario) or (usuario.get("rol") == "profesor" and str(curso.get("profesor", "")) == str(usuario["_id"]))


def inscripcion_aceptada(alumno_id, curso_id):
    """Las inscripciones anteriores al módulo de pagos no tienen estado: cuentan como aceptadas."""
    inscripcion = inscripciones_collection.find_one({
        "curso_id": {"$in": variantes_id(curso_id)},
        "alumno_id": {"$in": variantes_id(alumno_id)},
    })
    return bool(inscripcion) and inscripcion.get("estado", "aceptada") == "aceptada"


def tiene_acceso_curso(usuario, curso_id):
    """Puede ver el contenido del curso: administrador, profesor dueño o alumno aceptado."""
    curso = curso_por_id(curso_id)
    if not curso or not usuario:
        return False
    return puede_gestionar_curso(usuario, curso) or inscripcion_aceptada(usuario["_id"], curso["_id"])


def puede_ver_alumno(usuario, alumno_id):
    """El propio alumno, un administrador o un profesor que tenga al alumno en alguno de sus cursos."""
    if not usuario:
        return False
    if str(usuario["_id"]) == str(alumno_id) or es_admin(usuario):
        return True
    if usuario.get("rol") != "profesor":
        return False
    mis_cursos = [c["_id"] for c in cursos_collection.find({"profesor": {"$in": variantes_id(usuario["_id"])}}, {"_id": 1})]
    if not mis_cursos:
        return False
    ids_cursos = [v for c in mis_cursos for v in variantes_id(c)]
    return inscripciones_collection.find_one({
        "curso_id": {"$in": ids_cursos},
        "alumno_id": {"$in": variantes_id(alumno_id)},
    }) is not None


def exigir_gestion_curso(curso_id):
    """None si el usuario de la sesión puede gestionar el curso; si no, la respuesta de error."""
    curso = curso_por_id(curso_id)
    if not curso:
        return error(404, "Curso no encontrado")
    if not puede_gestionar_curso(usuario_sesion(), curso):
        return error(403, "Solo el profesor del curso o un administrador pueden hacer esto")
    return None


def exigir_acceso_curso(curso_id):
    """None si el usuario de la sesión puede ver el contenido del curso."""
    if not curso_por_id(curso_id):
        return error(404, "Curso no encontrado")
    if not tiene_acceso_curso(usuario_sesion(), curso_id):
        return error(403, "Necesitas estar inscrito en el curso")
    return None


def exigir_ver_alumno(alumno_id):
    if not puede_ver_alumno(usuario_sesion(), alumno_id):
        return error(403, "No puedes consultar la información de este alumno")
    return None
