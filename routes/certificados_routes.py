from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from controllers import certificados

certificados_bp = Blueprint("certificados_bp", __name__)


def _responder(funcion, *args):
    try:
        return jsonify(funcion(*args)), 200
    except certificados.ErrorCertificado as e:
        return jsonify({"mensaje": e.mensaje, **e.extra}), e.codigo
    except Exception as e:
        print("ERROR certificados:", e)
        return jsonify({"mensaje": "Error al procesar el certificado"}), 500


@certificados_bp.route("/certificados/curso/<curso_id>", methods=["GET"])
@jwt_required()
def get_estado(curso_id):
    """¿Ya tiene certificado este alumno o qué le falta?"""
    return _responder(certificados.estado_certificado, str(get_jwt_identity()), curso_id)


@certificados_bp.route("/certificados/curso/<curso_id>", methods=["POST"])
@jwt_required()
def post_emitir(curso_id):
    """Emite (o devuelve) el certificado si el alumno terminó y aprobó el curso."""
    return _responder(certificados.emitir_certificado, str(get_jwt_identity()), curso_id)


@certificados_bp.route("/certificados/mis", methods=["GET"])
@jwt_required()
def get_mis():
    return _responder(certificados.mis_certificados, str(get_jwt_identity()))


@certificados_bp.route("/certificados/verificar/<folio>", methods=["GET"])
def get_verificar(folio):
    """Pública: cualquiera puede comprobar que un certificado es auténtico."""
    return _responder(certificados.verificar, folio)
