from flask import Blueprint, request, jsonify, send_from_directory
from controllers.cursos import (
    obtener_cursos,
    obtener_curso_por_id,
    actualizar_curso,
    eliminar_curso,
    registrar_curso
)
from werkzeug.utils import secure_filename
from datetime import datetime
import os

curso_bp = Blueprint('curso_bp', __name__)

# Carpetas de subida
UPLOAD_FOLDER_VIDEOS = "uploads/videos"
UPLOAD_FOLDER_IMAGENES = "uploads/imagenes"
os.makedirs(UPLOAD_FOLDER_VIDEOS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_IMAGENES, exist_ok=True)

# -------------------------------
# Crear curso
# -------------------------------
@curso_bp.route('/cursos', methods=['POST'])
def registrar():
    print("Form recibido:", request.form)
    print("Archivos recibidos:", request.files)

    # Caso JSON (Postman o frontend que mande JSON)
    if request.is_json:
        datos = request.json
        return registrar_curso(
            nombre=datos.get('nombre'),
            descripcion=datos.get('descripcion'),
            profesor_id=datos.get('profesor_id'),  # debe ser un número
            fecha_inicio=datos.get('fecha_inicio'),
            fecha_fin=datos.get('fecha_fin'),
            imagenes=datos.get('imagenes'),
            videos=datos.get('videos')
        )
    # Caso FormData (frontend React con archivos)
    else:
        nombre = request.form.get("nombre")
        descripcion = request.form.get("descripcion")
        profesor_id = request.form.get("profesor")  # tu frontend manda "profesor"

        # Validar profesor_id
        try:
            profesor_id = int(profesor_id)
        except Exception:
            return {"mensaje": "El profesor_id debe ser un número"}, 400

        fecha_inicio = request.form.get("fecha_inicio")
        fecha_fin = request.form.get("fecha_fin")

        # Convertir fechas si vienen
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, "%Y-%m-%d").date() if fecha_inicio else None
            fecha_fin = datetime.strptime(fecha_fin, "%Y-%m-%d").date() if fecha_fin else None
        except Exception:
            return {"mensaje": "Formato de fecha inválido, usa YYYY-MM-DD"}, 400

        # Guardar imágenes
        imagenes_guardadas = []
        for i, img in enumerate(request.files.getlist("imagenes"), start=1):
            filename = secure_filename(f"{nombre}_imagen{i}.png")
            filepath = os.path.join(UPLOAD_FOLDER_IMAGENES, filename)
            img.save(filepath)
            imagenes_guardadas.append({
                "nombre": filename,
                "tipo": "png",
                "contenido": None
            })

        # Guardar videos
        videos_guardados = []
        for i, vid in enumerate(request.files.getlist("videos"), start=1):
            filename = secure_filename(f"{nombre}_video{i}.mp4")
            filepath = os.path.join(UPLOAD_FOLDER_VIDEOS, filename)
            vid.save(filepath)
            videos_guardados.append({
                "titulo": filename,
                "url": filepath,
                "descripcion": None
            })

        return registrar_curso(
            nombre=nombre,
            descripcion=descripcion,
            profesor_id=profesor_id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            imagenes=imagenes_guardadas,
            videos=videos_guardados
        )

# -------------------------------
# Listar cursos
# -------------------------------
@curso_bp.route('/cursos', methods=['GET'])
def listar():
    return jsonify(obtener_cursos()), 200

# -------------------------------
# Obtener curso por ID
# -------------------------------
@curso_bp.route('/cursos/<int:curso_id>', methods=['GET'])
def obtener(curso_id):
    curso = obtener_curso_por_id(curso_id)
    return jsonify(curso), 200 if curso else ({"mensaje": "Curso no encontrado"}, 404)

# -------------------------------
# Actualizar curso
# -------------------------------
@curso_bp.route('/cursos/<int:curso_id>', methods=['PUT'])
def actualizar(curso_id):
    datos = request.json
    exito = actualizar_curso(curso_id, datos)
    return ({"mensaje": "Curso actualizado"}, 200) if exito else ({"mensaje": "No se pudo actualizar"}, 400)

# -------------------------------
# Eliminar curso
# -------------------------------
@curso_bp.route('/cursos/<int:curso_id>', methods=['DELETE'])
def eliminar(curso_id):
    exito = eliminar_curso(curso_id)
    return ({"mensaje": "Curso eliminado"}, 200) if exito else ({"mensaje": "No se pudo eliminar"}, 400)

# -------------------------------
# Servir archivos subidos
# -------------------------------
@curso_bp.route("/uploads/imagenes/<filename>")
def get_imagen(filename):
    return send_from_directory(UPLOAD_FOLDER_IMAGENES, filename)

@curso_bp.route("/uploads/videos/<filename>")
def get_video(filename):
    return send_from_directory(UPLOAD_FOLDER_VIDEOS, filename)