from flask import Blueprint, jsonify, request
from controllers.analisis_progreso import analizar_progreso_curso, obtener_cursos_por_tasa_finalizacion, obtener_cursos_por_tasa_abandono, obtener_progreso_estudiante, marcar_leccion_como_vista, obtener_analitica_educativa_curso

analisis_progreso_bp = Blueprint("analisis_progreso_bp", __name__)

@analisis_progreso_bp.route("/analisis/progreso/curso/<curso_id>", methods=["GET"])
def get_progreso_curso(curso_id):
    try:
        resultado = analizar_progreso_curso(curso_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al analizar el progreso del curso: {str(e)}"}), 500

@analisis_progreso_bp.route("/analisis/progreso/cursos/top-finalizacion", methods=["GET"])
def get_top_finalizacion_cursos():
    try:
        resultado = obtener_cursos_por_tasa_finalizacion()
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener cursos con mayor finalización: {str(e)}"}), 500

@analisis_progreso_bp.route("/analisis/progreso/cursos/top-abandono", methods=["GET"])
def get_top_abandono_cursos():
    try:
        resultado = obtener_cursos_por_tasa_abandono()
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener cursos con mayor abandono: {str(e)}"}), 500

@analisis_progreso_bp.route("/analisis/progreso/estudiante/<alumno_id>/<curso_id>", methods=["GET"])
def get_progreso_estudiante_personal(alumno_id, curso_id):
    try:
        resultado = obtener_progreso_estudiante(alumno_id, curso_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al obtener progreso personal: {str(e)}"}), 500

@analisis_progreso_bp.route("/analisis/progreso/leccion/vista", methods=["POST"])
def post_marcar_vista():
    try:
        datos = request.json
        alumno_id = datos.get("alumno_id")
        leccion_id = datos.get("leccion_id")
        curso_id = datos.get("curso_id")
        
        resultado = marcar_leccion_como_vista(alumno_id, leccion_id, curso_id)
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al marcar lección como vista: {str(e)}"}), 500

@analisis_progreso_bp.route("/analisis/educativa/curso/<curso_id>", methods=["GET"])
def get_analitica_educativa(curso_id):
    try:
        resultado = obtener_analitica_educativa_curso(curso_id)
        if "error" in resultado:
            return jsonify(resultado), 400
        return jsonify(resultado), 200
    except Exception as e:
        return jsonify({"mensaje": f"Error al generar reporte de analítica: {str(e)}"}), 500