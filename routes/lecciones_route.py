import os
from flask import Blueprint, request, jsonify, current_app, make_response
from werkzeug.utils import secure_filename
from models.Leccion import crear_leccion, eliminar_leccion
from controllers.lecciones import obtener_lecciones_por_curso, obtener_lecciones_por_nivel

leccion_bp = Blueprint("leccion_bp", __name__)

# =========================
# CONFIG ARCHIVOS
# =========================
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "mp4", "pdf"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# =========================
# CREAR LECCIÓN
# =========================
@leccion_bp.route("/lecciones", methods=["POST", "OPTIONS"])
def registrar():
    if request.method == "OPTIONS":
        return _preflight_response()
    
    curso_id = request.form.get("curso_id")
    nivel_id = request.form.get("nivel_id")
    titulo = request.form.get("titulo")
    contenido = request.form.get("contenido", "")

    if not curso_id or not titulo:
        return jsonify({"mensaje": "curso_id y titulo son obligatorios"}), 400

    archivos_subidos = []
    if "archivos" in request.files:
        for f in request.files.getlist("archivos"):
            if f and allowed_file(f.filename):
                filename = secure_filename(f.filename)
                
                # Carpeta según tipo
                ext = filename.split(".")[-1].lower()
                if ext in ["png","jpg","jpeg","gif"]:
                    carpeta_destino = os.path.join(current_app.root_path, "uploads", "imagenes")
                elif ext in ["mp4"]:
                    carpeta_destino = os.path.join(current_app.root_path, "uploads", "videos")
                elif ext in ["pdf"]:
                    carpeta_destino = os.path.join(current_app.root_path, "uploads", "pdfs")
                else:
                    carpeta_destino = os.path.join(current_app.root_path, "uploads")

                os.makedirs(carpeta_destino, exist_ok=True)
                ruta = os.path.join(carpeta_destino, filename)
                f.save(ruta)
                archivos_subidos.append(filename)

    leccion = crear_leccion(curso_id, titulo, contenido, archivos_subidos, nivel_id)
    return jsonify(leccion), 201

# =========================
# LISTAR POR CURSO
# =========================
@leccion_bp.route("/lecciones/curso/<curso_id>", methods=["GET", "OPTIONS"])
def listar_por_curso(curso_id):
    if request.method == "OPTIONS":
        return _preflight_response()
    
    lecciones = obtener_lecciones_por_curso(curso_id)
    return jsonify(lecciones), 200

# =========================
# LISTAR POR NIVEL
# =========================
@leccion_bp.route("/lecciones/nivel/<nivel_id>", methods=["GET", "OPTIONS"])
def listar_por_nivel(nivel_id):
    if request.method == "OPTIONS":
        return _preflight_response()
    
    lecciones = obtener_lecciones_por_nivel(nivel_id)
    return jsonify(lecciones), 200

# =========================
# ELIMINAR LECCIÓN
# =========================
@leccion_bp.route("/lecciones/<leccion_id>", methods=["DELETE", "OPTIONS"])
def eliminar(leccion_id):
    if request.method == "OPTIONS":
        return _preflight_response()
    
    exito = eliminar_leccion(leccion_id)
    if exito:
        return jsonify({"mensaje": "Lección eliminada correctamente"}), 200
    else:
        return jsonify({"mensaje": "No se pudo eliminar la lección"}), 400

# =========================
# FUNCIÓN PREFLIGHT
# =========================
def _preflight_response():
    response = make_response()
    response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
    response.headers.add("Access-Control-Allow-Headers", "Content-Type,Authorization")
    response.headers.add("Access-Control-Allow-Methods", "GET,POST,DELETE,OPTIONS")
    return response
