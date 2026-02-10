from flask import Blueprint, request, jsonify, send_from_directory
from models.Curso import registrar_curso
from config.config import cursos_collection
from controllers.cursos import serializar_curso, obtener_cursos, obtener_curso_por_id, actualizar_curso, eliminar_curso, obtener_cursos_recientes
from flask_jwt_extended import jwt_required, get_jwt_identity
from werkzeug.utils import secure_filename
import os

curso_bp = Blueprint('curso_bp', __name__)

# Carpetas de subida
UPLOAD_FOLDER_VIDEOS = "uploads/videos"
UPLOAD_FOLDER_IMAGENES = "uploads/imagenes"
os.makedirs(UPLOAD_FOLDER_VIDEOS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_IMAGENES, exist_ok=True)

@curso_bp.route('/cursos', methods=['POST'])
@jwt_required()
def registrar():
    profesor = str(get_jwt_identity())  # 👈 profesor autenticado desde el token

    if request.is_json:
        datos = request.json
        return registrar_curso(
            nombre=datos.get('nombre'),
            descripcion=datos.get('descripcion'),
            profesor=profesor,
            imagenes=datos.get('imagenes', []),
            videos=datos.get('videos', [])
        )
    else:
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")

        # Guardar imágenes
        imagenes_guardadas = []
        for i, img in enumerate(request.files.getlist("imagenes"), start=1):
            filename = secure_filename(f"{nombre}_imagen{i}.png")
            filepath = os.path.join(UPLOAD_FOLDER_IMAGENES, filename)
            img.save(filepath)
            imagenes_guardadas.append(filename)

        # Guardar videos
        videos_guardados = []
        for i, vid in enumerate(request.files.getlist("videos"), start=1):
            filename = secure_filename(f"{nombre}_video{i}.mp4")
            filepath = os.path.join(UPLOAD_FOLDER_VIDEOS, filename)
            vid.save(filepath)
            videos_guardados.append(filename)

        return registrar_curso(
            nombre=nombre,
            descripcion=descripcion,
            profesor=profesor,
            imagenes=imagenes_guardadas,
            videos=videos_guardados
        )

@curso_bp.route('/cursos', methods=['GET'])
def listar():
    return jsonify(obtener_cursos()), 200

@curso_bp.route('/cursos/<curso_id>', methods=['GET'])
def obtener(curso_id):
    curso = obtener_curso_por_id(curso_id)
    return jsonify(curso), 200 if curso else ({"mensaje": "Curso no encontrado"}, 404)

@curso_bp.route('/cursos/<curso_id>', methods=['PUT'])
def actualizar(curso_id):
    datos = request.json
    exito = actualizar_curso(curso_id, datos)
    return ({"mensaje": "Curso actualizado"}, 200) if exito else ({"mensaje": "No se pudo actualizar"}, 400)

@curso_bp.route('/cursos/<curso_id>', methods=['DELETE'])
def eliminar(curso_id):
    exito = eliminar_curso(curso_id)
    return ({"mensaje": "Curso eliminado"}, 200) if exito else ({"mensaje": "No se pudo eliminar"}, 400)

# Servir archivos estáticos
@curso_bp.route("/uploads/imagenes/<filename>")
def get_imagen(filename):
    return send_from_directory(UPLOAD_FOLDER_IMAGENES, filename)

@curso_bp.route("/uploads/videos/<filename>")
def get_video(filename):
    return send_from_directory(UPLOAD_FOLDER_VIDEOS, filename)

@curso_bp.route('/cursos/recientes', methods=['GET'])
def listar_recientes():
    return jsonify(obtener_cursos_recientes()), 200

@curso_bp.route('/mis_cursos', methods=['GET'])
@jwt_required()
def mis_cursos():
    profesor = str(get_jwt_identity())  # 👈 email o id del profesor en el token
    print("Filtro profesor:", profesor)  # 👈 depuración
    cursos = cursos_collection.find({"profesor": profesor})
    lista = [serializar_curso(curso) for curso in cursos]
    return jsonify(lista), 200