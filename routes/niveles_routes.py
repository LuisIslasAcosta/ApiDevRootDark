from flask import Blueprint, request, jsonify
from models.Nivel import crear_nivel
from controllers.niveles import obtener_niveles_por_curso, eliminar_nivel
from controllers.lecciones import obtener_lecciones_por_nivel

nivel_bp = Blueprint("nivel_bp", __name__)

# =========================
# CREAR UN NUEVO NIVEL
# =========================
@nivel_bp.route("/niveles", methods=["POST"])
def registrar():
    datos = request.json
    return crear_nivel(
        curso_id=datos.get("curso_id"),
        titulo=datos.get("titulo"),
        descripcion=datos.get("descripcion", ""),
        orden=datos.get("orden", 1)
    )

# =========================
# LISTAR NIVELES DE UN CURSO
# =========================
@nivel_bp.route("/niveles/curso/<curso_id>", methods=["GET"])
def listar_por_curso(curso_id):
    return jsonify(obtener_niveles_por_curso(curso_id)), 200

# =========================
# LISTAR NIVELES CON SUS LECCIONES
# =========================
@nivel_bp.route("/niveles/curso/<curso_id>/con_lecciones", methods=["GET"])
def listar_por_curso_con_lecciones(curso_id):
    niveles = obtener_niveles_por_curso(curso_id)
    
    for nivel in niveles:
        # Obtener todas las lecciones de este nivel
        lecciones = obtener_lecciones_por_nivel(nivel["id"])
        nivel["lecciones"] = lecciones  # agregar las lecciones dentro del nivel
    
    return jsonify(niveles), 200

# =========================
# ELIMINAR UN NIVEL
# =========================
@nivel_bp.route("/niveles/<nivel_id>", methods=["DELETE"])
def eliminar_nivel_route(nivel_id):
    ok = eliminar_nivel(nivel_id)
    return jsonify({"ok": ok})
