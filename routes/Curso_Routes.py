from bson.objectid import ObjectId
from flask import Blueprint, request, jsonify
from models.Curso import registrar_curso
from config.config import cursos_collection, usuarios_collection
from controllers.cursos import (
    serializar_curso,
    obtener_cursos,
    obtener_curso_por_id,
    actualizar_curso,
    eliminar_curso,
    obtener_cursos_recientes
)
from utils.archivos import IMAGENES, VIDEOS, ArchivoInvalido, entregar, guardar_varios
from utils.seguridad import (
    curso_por_id, error, puede_gestionar_curso, staff_requerido, texto, usuario_sesion,
)

curso_bp = Blueprint('curso_bp', __name__)


def _urls(campo):
    """Lista de URLs externas (solo http/https)."""
    valor = texto(request.form.get(campo, ""), 5000)
    return [u.strip() for u in valor.split(",") if u.strip().lower().startswith(("http://", "https://"))]


def _profesor_destino(usuario):
    """El profesor crea cursos a su nombre; el administrador puede asignar un profesor."""
    if usuario.get("rol") == "administrador":
        elegido = texto(request.form.get("profesor") or (request.get_json(silent=True) or {}).get("profesor"))
        if ObjectId.is_valid(elegido) and usuarios_collection.find_one({"_id": ObjectId(elegido), "rol": "profesor"}):
            return elegido
    return str(usuario["_id"])


@curso_bp.route('/cursos', methods=['POST'])
@staff_requerido
def registrar():
    usuario = usuario_sesion()
    profesor = _profesor_destino(usuario)

    if request.is_json:
        datos = request.get_json(silent=True) or {}
        lista = lambda c: [u for u in (datos.get(c) or []) if isinstance(u, str) and u.lower().startswith(("http://", "https://"))]
        return registrar_curso(
            nombre=texto(datos.get('nombre'), 200),
            descripcion=texto(datos.get('descripcion'), 5000),
            profesor=profesor,
            precio=texto(datos.get('precio'), 20),
            imagenes=lista('imagenes'),
            videos=lista('videos'),
        )

    try:
        imagenes = guardar_varios(request.files.getlist("imagenes"), IMAGENES)
        videos = guardar_varios(request.files.getlist("videos"), VIDEOS)
    except ArchivoInvalido as e:
        return error(400, str(e))

    return registrar_curso(
        nombre=texto(request.form.get("nombre"), 200),
        descripcion=texto(request.form.get("descripcion"), 5000),
        profesor=profesor,
        precio=texto(request.form.get("precio"), 20),
        imagenes=imagenes + _urls("imagenes_url"),
        videos=videos + _urls("videos_url"),
    )


@curso_bp.route('/cursos', methods=['GET'])
def listar():
    return jsonify(obtener_cursos()), 200


@curso_bp.route('/cursos/<curso_id>', methods=['GET'])
def obtener(curso_id):

    curso = obtener_curso_por_id(curso_id)

    if curso:
        return jsonify(curso), 200
    else:
        return jsonify({"mensaje": "Curso no encontrado"}), 404


@curso_bp.route('/cursos/<curso_id>', methods=['PUT'])
@staff_requerido
def actualizar(curso_id):
    curso = curso_por_id(curso_id)
    if not curso:
        return error(404, "Curso no encontrado")
    if not puede_gestionar_curso(usuario_sesion(), curso):
        return error(403, "Solo el profesor del curso o un administrador pueden editarlo")

    try:
        imagenes = guardar_varios(request.files.getlist("imagenes"), IMAGENES) + _urls("imagenes_url")
        videos = guardar_varios(request.files.getlist("videos"), VIDEOS) + _urls("videos_url")
    except ArchivoInvalido as e:
        return error(400, str(e))

    precio = texto(request.form.get("precio"), 20)
    try:
        precio = float(precio) if precio else None
    except ValueError:
        return error(400, "Precio inválido")

    update_data = {
        "nombre": texto(request.form.get("nombre"), 200) or None,
        "descripcion": texto(request.form.get("descripcion"), 5000) or None,
        "precio": precio,
        # Datos de pago que verá el alumno al inscribirse (banco, CLABE, titular...)
        "instrucciones_pago": texto(request.form.get("instrucciones_pago"), 2000) if "instrucciones_pago" in request.form else None,
    }
    if imagenes:
        update_data["imagenes"] = imagenes
    if videos:
        update_data["videos"] = videos
    update_data = {k: v for k, v in update_data.items() if v is not None}

    if actualizar_curso(curso_id, update_data):
        return jsonify({"mensaje": "Curso actualizado"}), 200
    return jsonify({"mensaje": "No se pudo actualizar"}), 400


@curso_bp.route('/cursos/<curso_id>', methods=['DELETE'])
@staff_requerido
def eliminar(curso_id):
    curso = curso_por_id(curso_id)
    if not curso:
        return error(404, "Curso no encontrado")
    if not puede_gestionar_curso(usuario_sesion(), curso):
        return error(403, "Solo el profesor del curso o un administrador pueden eliminarlo")
    if eliminar_curso(curso_id):
        return jsonify({"mensaje": "Curso eliminado"}), 200
    return jsonify({"mensaje": "No se pudo eliminar"}), 400


@curso_bp.route("/uploads/imagenes/<filename>")
def get_imagen(filename):
    return entregar(f"imagenes/{filename}")


@curso_bp.route("/uploads/videos/<filename>")
def get_video(filename):
    return entregar(f"videos/{filename}")


@curso_bp.route("/uploads/pdfs/<filename>")
def get_pdf(filename):
    return entregar(f"pdfs/{filename}")


@curso_bp.route('/cursos/recientes', methods=['GET'])
def listar_recientes():
    return jsonify(obtener_cursos_recientes()), 200


@curso_bp.route('/mis_cursos', methods=['GET'])
@staff_requerido
def mis_cursos():

    profesor = str(usuario_sesion()["_id"])

    cursos = cursos_collection.find({"profesor": profesor})

    lista = [serializar_curso(curso) for curso in cursos]

    return jsonify(lista), 200


@curso_bp.route("/cursos/<curso_id>/alumnos", methods=["GET"])
@staff_requerido
def alumnos_curso(curso_id):
    if not puede_gestionar_curso(usuario_sesion(), curso_por_id(curso_id)):
        return error(403, "Solo el profesor del curso o un administrador pueden ver sus alumnos")

    from controllers.inscripciones import obtener_inscripciones_por_curso

    # Solo alumnos con el pago aceptado cuentan como inscritos
    return jsonify(obtener_inscripciones_por_curso(curso_id, solo_aceptadas=True)), 200