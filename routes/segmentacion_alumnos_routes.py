from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from controllers.segmentacion_alumnos import segmentar_alumnos, predecir_cluster_alumno

segmentacion_alumnos_bp = Blueprint("segmentacion_alumnos_bp", __name__)


@segmentacion_alumnos_bp.route("/segmentacion/alumnos", methods=["GET"])
@jwt_required()
def segmentacion_alumnos_route():
    """
    Segmenta a todos los alumnos del profesor usando K-Means + Random Forest
    """
    try:
        profesor_id = get_jwt_identity()
        print(f"DEBUG: Profesor ID del token: {profesor_id}")
    except Exception as e:
        profesor_id = None
        print(f"DEBUG: Error al obtener token: {str(e)}")

    try:
        resultado = segmentar_alumnos(profesor_id)
        print(f"DEBUG: Resultado: {resultado.keys() if isinstance(resultado, dict) else 'lista'}")
        
        if "error" in resultado:
            print(f"DEBUG: Error en segmentación: {resultado['error']}")
            return jsonify(resultado), 400

        return jsonify(resultado), 200
    except Exception as e:
        print(f"DEBUG: Excepción no manejada: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error interno: {str(e)}"}), 500


@segmentacion_alumnos_bp.route("/segmentacion/alumno/<alumno_id>", methods=["GET"])
@jwt_required()
def predecir_cluster_route(alumno_id):
    """
    Predice el cluster de un alumno específico
    """
    resultado = predecir_cluster_alumno(alumno_id)

    if "error" in resultado:
        return jsonify(resultado), 400

    return jsonify(resultado), 200