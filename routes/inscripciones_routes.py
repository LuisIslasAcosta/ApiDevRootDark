import os
from datetime import datetime

from bson.errors import InvalidId
from bson.objectid import ObjectId
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.utils import secure_filename

from config.config import usuarios_collection, cursos_collection
from models.Inscripciones import (
    registrar_inscripcion, eliminar_inscripcion, guardar_comprobante, validar_pago, estado_de
)
from utils.archivos import detectar_tipo
from utils.seguridad import (
    curso_por_id, error, es_admin, exigir_gestion_curso, exigir_ver_alumno, puede_gestionar_curso,
    sesion_requerida, staff_requerido, texto, usuario_sesion, variantes_id,
)
from controllers.inscripciones import (
    obtener_inscripciones, obtener_inscripciones_por_curso, obtener_inscripciones_por_alumno,
    obtener_inscripcion, obtener_pagos_profesor, serializar_inscripcion
)

inscripcion_bp = Blueprint("inscripcion_bp", __name__)

# Los comprobantes NO se guardan en uploads/ porque esa carpeta es pública.
CARPETA_COMPROBANTES = os.getenv("COMPROBANTES_DIR") or os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "comprobantes")
os.makedirs(CARPETA_COMPROBANTES, exist_ok=True)

EXTENSIONES_PERMITIDAS = {"pdf": "application/pdf", "png": "image/png", "jpg": "image/jpeg",
                          "jpeg": "image/jpeg", "webp": "image/webp"}
TAMANO_MAXIMO = 5 * 1024 * 1024  # 5 MB


def _rol(usuario_id):
    try:
        usuario = usuarios_collection.find_one({"_id": ObjectId(usuario_id)})
    except Exception:
        usuario = None
    return usuario.get("rol") if usuario else None


def _es_profesor_del_curso(usuario_id, curso_id):
    try:
        curso = cursos_collection.find_one({"_id": ObjectId(curso_id)})
    except Exception:
        return False
    return bool(curso) and str(curso.get("profesor")) == str(usuario_id)


# ============================= INSCRIBIRSE =============================
@inscripcion_bp.route("/inscripciones", methods=["POST"])
@sesion_requerida
def registrar():
    datos = request.get_json(silent=True) or {}
    curso_id = texto(datos.get("curso_id"))
    # El alumno siempre es el del token: nadie puede inscribir a otra persona
    alumno_id = str(usuario_sesion()["_id"])
    if not curso_por_id(curso_id):
        return error(404, "Curso no encontrado")

    if not curso_id or not alumno_id:
        return jsonify({"mensaje": "Curso y alumno son obligatorios"}), 400

    return registrar_inscripcion(curso_id, alumno_id)


# ============================= ALUMNO: MIS INSCRIPCIONES =============================
@inscripcion_bp.route("/inscripciones/mis-inscripciones", methods=["GET"])
@jwt_required()
def mis_inscripciones():
    return jsonify(obtener_inscripciones_por_alumno(str(get_jwt_identity()))), 200


# ============================= ALUMNO: SUBIR COMPROBANTE =============================
@inscripcion_bp.route("/inscripciones/<inscripcion_id>/comprobante", methods=["POST"])
@jwt_required()
def subir_comprobante(inscripcion_id):
    usuario_id = str(get_jwt_identity())
    inscripcion = obtener_inscripcion(inscripcion_id)
    if not inscripcion:
        return jsonify({"mensaje": "Inscripción no encontrada"}), 404
    if str(inscripcion["alumno_id"]) != usuario_id:
        return jsonify({"mensaje": "Solo el alumno de esta inscripción puede subir el comprobante"}), 403
    if estado_de(inscripcion) not in ("pendiente_pago", "rechazada", "en_revision"):
        return jsonify({"mensaje": "Esta inscripción ya fue aceptada"}), 400

    archivo = request.files.get("comprobante")
    if not archivo or not archivo.filename:
        return jsonify({"mensaje": "Adjunta el comprobante de pago (PDF o imagen)"}), 400

    extension = archivo.filename.rsplit(".", 1)[-1].lower() if "." in archivo.filename else ""
    if extension not in EXTENSIONES_PERMITIDAS:
        return jsonify({"mensaje": "Formato no permitido. Usa PDF, PNG, JPG o WEBP"}), 400

    contenido = archivo.read()
    tipo_real = detectar_tipo(contenido[:16])
    if tipo_real != {"jpeg": "jpg"}.get(extension, extension):
        return jsonify({"mensaje": "El archivo no es un PDF o imagen válido"}), 400
    if len(contenido) > TAMANO_MAXIMO:
        return jsonify({"mensaje": "El comprobante no debe pesar más de 5 MB"}), 400
    if len(contenido) == 0:
        return jsonify({"mensaje": "El archivo está vacío"}), 400

    referencia = inscripcion.get("referencia_pago") or inscripcion_id
    nombre_guardado = secure_filename(f"{referencia}_{datetime.now().strftime('%Y%m%d%H%M%S')}.{extension}")
    with open(os.path.join(CARPETA_COMPROBANTES, nombre_guardado), "wb") as f:
        f.write(contenido)

    datos_pago = {
        "fecha_pago": request.form.get("fecha_pago", ""),
        "monto_pagado": request.form.get("monto_pagado", ""),
        "nota": request.form.get("nota", "")[:500],
    }
    guardar_comprobante(inscripcion_id, {
        "archivo": nombre_guardado,
        "nombre_original": archivo.filename,
        "tipo": EXTENSIONES_PERMITIDAS[extension],
        "tamano": len(contenido),
    }, datos_pago)

    return jsonify({
        "mensaje": "Comprobante enviado. Tu profesor revisará el pago",
        "inscripcion": serializar_inscripcion(obtener_inscripcion(inscripcion_id)),
    }), 200


# ============================= VER COMPROBANTE (alumno dueño, profesor del curso o admin) =============================
@inscripcion_bp.route("/inscripciones/<inscripcion_id>/comprobante", methods=["GET"])
@jwt_required()
def ver_comprobante(inscripcion_id):
    usuario_id = str(get_jwt_identity())
    inscripcion = obtener_inscripcion(inscripcion_id)
    if not inscripcion or not inscripcion.get("comprobante"):
        return jsonify({"mensaje": "No hay comprobante para esta inscripción"}), 404

    permitido = (str(inscripcion["alumno_id"]) == usuario_id
                 or _es_profesor_del_curso(usuario_id, str(inscripcion["curso_id"]))
                 or _rol(usuario_id) == "administrador")
    if not permitido:
        return jsonify({"mensaje": "No tienes permiso para ver este comprobante"}), 403

    comprobante = inscripcion["comprobante"]
    ruta = os.path.join(CARPETA_COMPROBANTES, comprobante["archivo"])
    if not os.path.exists(ruta):
        return jsonify({"mensaje": "El archivo del comprobante ya no existe en el servidor"}), 404
    return send_file(ruta, mimetype=comprobante.get("tipo"), download_name=comprobante.get("nombre_original"))


# ============================= PROFESOR: PAGOS DE SUS CURSOS =============================
@inscripcion_bp.route("/inscripciones/profesor/pagos", methods=["GET"])
@jwt_required()
def pagos_profesor():
    estado = request.args.get("estado")
    return jsonify(obtener_pagos_profesor(str(get_jwt_identity()), estado)), 200


# ============================= PROFESOR: VALIDAR PAGO =============================
@inscripcion_bp.route("/inscripciones/<inscripcion_id>/validar", methods=["PUT"])
@jwt_required()
def validar(inscripcion_id):
    usuario_id = str(get_jwt_identity())
    inscripcion = obtener_inscripcion(inscripcion_id)
    if not inscripcion:
        return jsonify({"mensaje": "Inscripción no encontrada"}), 404
    if not (_es_profesor_del_curso(usuario_id, str(inscripcion["curso_id"])) or _rol(usuario_id) == "administrador"):
        return jsonify({"mensaje": "Solo el profesor del curso puede validar el pago"}), 403

    datos = request.json or {}
    accion = datos.get("accion")
    if accion not in ("aceptar", "rechazar"):
        return jsonify({"mensaje": "La acción debe ser 'aceptar' o 'rechazar'"}), 400
    if accion == "rechazar" and not (datos.get("motivo") or "").strip():
        return jsonify({"mensaje": "Indica el motivo del rechazo para que el alumno lo sepa"}), 400

    nuevo_estado = validar_pago(inscripcion_id, accion == "aceptar", (datos.get("motivo") or "").strip(), usuario_id)
    mensaje = "Pago validado: el alumno ya tiene acceso al curso" if nuevo_estado == "aceptada" else "Pago rechazado"
    return jsonify({"mensaje": mensaje, "inscripcion": serializar_inscripcion(obtener_inscripcion(inscripcion_id))}), 200


# ============================= EXISTENTES =============================
@inscripcion_bp.route("/inscripciones/<inscripcion_id>", methods=["DELETE"])
@staff_requerido
def eliminar(inscripcion_id):
    inscripcion = obtener_inscripcion(inscripcion_id) if ObjectId.is_valid(inscripcion_id) else None
    if not inscripcion:
        return error(404, "Inscripción no encontrada")
    problema = exigir_gestion_curso(inscripcion.get("curso_id"))
    if problema:
        return problema
    try:
        if eliminar_inscripcion(inscripcion_id):
            return jsonify({"mensaje": "Inscripción eliminada correctamente"}), 200
        return jsonify({"mensaje": "No se pudo eliminar la inscripción"}), 400
    except InvalidId:
        return jsonify({"mensaje": "ID de inscripción inválido"}), 400


@inscripcion_bp.route("/inscripciones", methods=["GET"])
@staff_requerido
def listar():
    usuario = usuario_sesion()
    todas = obtener_inscripciones()
    if es_admin(usuario):
        return jsonify(todas), 200
    # El profesor solo ve las de sus cursos
    mis_cursos = {str(c["_id"]) for c in cursos_collection.find({"profesor": {"$in": variantes_id(usuario["_id"])}}, {"_id": 1})}
    return jsonify([i for i in todas if str(i.get("curso_id")) in mis_cursos]), 200


@inscripcion_bp.route("/inscripciones/curso/<curso_id>", methods=["GET"])
@staff_requerido
def listar_por_curso(curso_id):
    problema = exigir_gestion_curso(curso_id)
    if problema:
        return problema
    return jsonify(obtener_inscripciones_por_curso(curso_id)), 200


@inscripcion_bp.route("/inscripciones/alumno/<alumno_id>", methods=["GET"])
@sesion_requerida
def listar_por_alumno(alumno_id):
    problema = exigir_ver_alumno(alumno_id)
    if problema:
        return problema
    return jsonify(obtener_inscripciones_por_alumno(alumno_id)), 200
