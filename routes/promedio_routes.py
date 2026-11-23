from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt_identity
from utils.seguridad import staff_requerido
from analytics.examenes_spark import promedio_por_examen_profesor

spark_bp = Blueprint("spark", __name__)

@spark_bp.route("/promedio-examen-profesor", methods=["GET"])
@staff_requerido
def obtener_promedio_examen():

    try:
        # profesor que inició sesión
        profesor_id = get_jwt_identity()

        promedios = promedio_por_examen_profesor(profesor_id)

        return jsonify(promedios), 200

    except Exception as e:
        return jsonify({
            "mensaje": f"Error obteniendo promedios: {str(e)}"
        }), 500