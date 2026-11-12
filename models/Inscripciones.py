import secrets
import string
from datetime import datetime, timezone

from bson.objectid import ObjectId
from flask import jsonify

from config.config import inscripciones_collection, cursos_collection

# ===================== ESTADOS DE UNA INSCRIPCIÓN =====================
# pendiente_pago -> el alumno se inscribió y debe pagar y subir su comprobante
# en_revision    -> el alumno subió el comprobante; el profesor debe validarlo
# aceptada       -> el profesor confirmó el pago; el alumno ya tiene acceso al curso
# rechazada      -> el profesor no encontró el pago; el alumno puede subir otro comprobante
ESTADOS = ("pendiente_pago", "en_revision", "aceptada", "rechazada")


def ahora():
    return datetime.now(timezone.utc).isoformat()


def estado_de(inscripcion):
    """Las inscripciones anteriores al módulo de pagos no tienen estado: se toman como aceptadas."""
    return inscripcion.get("estado", "aceptada")


def generar_referencia():
    """ID único de pago con formato DRD-XXXXXXXX (sin caracteres que se confundan como 0/O o 1/I)."""
    alfabeto = "".join(c for c in string.ascii_uppercase + string.digits if c not in "0O1I")
    while True:
        referencia = "DRD-" + "".join(secrets.choice(alfabeto) for _ in range(8))
        if not inscripciones_collection.find_one({"referencia_pago": referencia}):
            return referencia


def registrar_inscripcion(curso_id, alumno_id):
    from controllers.inscripciones import serializar_inscripcion

    try:
        curso = cursos_collection.find_one({"_id": ObjectId(curso_id)})
    except Exception:
        curso = None
    if not curso:
        return jsonify({"mensaje": "Curso no encontrado"}), 404

    # Si ya existe una inscripción para este alumno y curso, se regresa la misma (misma referencia)
    ids_curso = [curso_id] + ([ObjectId(curso_id)] if ObjectId.is_valid(curso_id) else [])
    ids_alumno = [alumno_id] + ([ObjectId(alumno_id)] if ObjectId.is_valid(alumno_id) else [])
    existente = inscripciones_collection.find_one({"curso_id": {"$in": ids_curso}, "alumno_id": {"$in": ids_alumno}})
    if existente:
        return jsonify({
            "mensaje": "Ya tienes una inscripción para este curso",
            "inscripcion": serializar_inscripcion(existente)
        }), 200

    precio = float(curso.get("precio") or 0)
    gratuito = precio <= 0

    nueva_inscripcion = {
        "curso_id": curso_id,
        "alumno_id": alumno_id,
        "profesor_id": str(curso.get("profesor", "")),
        "referencia_pago": generar_referencia(),
        "monto": precio,
        "estado": "aceptada" if gratuito else "pendiente_pago",
        "fecha_inscripcion": ahora(),
        "fecha_comprobante": None,
        "fecha_validacion": ahora() if gratuito else None,
        "comprobante": None,
        "motivo_rechazo": None,
        "historial": [{"estado": "aceptada" if gratuito else "pendiente_pago", "fecha": ahora()}],
    }

    try:
        resultado = inscripciones_collection.insert_one(nueva_inscripcion)
        nueva_inscripcion["_id"] = resultado.inserted_id
        mensaje = ("Inscripción realizada: el curso es gratuito" if gratuito
                   else "Inscripción registrada. Realiza tu pago y sube tu comprobante")
        return jsonify({"mensaje": mensaje, "inscripcion": serializar_inscripcion(nueva_inscripcion)}), 201
    except Exception as e:
        return jsonify({"mensaje": f"Error al registrar inscripción: {str(e)}"}), 500


def guardar_comprobante(inscripcion_id, archivo_info, datos_pago):
    """archivo_info: dict con nombre, tipo y ruta del archivo guardado."""
    inscripciones_collection.update_one(
        {"_id": ObjectId(inscripcion_id)},
        {
            "$set": {
                "estado": "en_revision",
                "fecha_comprobante": ahora(),
                "comprobante": archivo_info,
                "datos_pago_alumno": datos_pago,
                "motivo_rechazo": None,
            },
            "$push": {"historial": {"estado": "en_revision", "fecha": ahora()}},
        },
    )


def validar_pago(inscripcion_id, aceptar, motivo, validador_id):
    nuevo_estado = "aceptada" if aceptar else "rechazada"
    inscripciones_collection.update_one(
        {"_id": ObjectId(inscripcion_id)},
        {
            "$set": {
                "estado": nuevo_estado,
                "fecha_validacion": ahora(),
                "validado_por": validador_id,
                "motivo_rechazo": None if aceptar else (motivo or "El pago no se pudo verificar"),
            },
            "$push": {"historial": {"estado": nuevo_estado, "fecha": ahora(), "motivo": motivo}},
        },
    )
    return nuevo_estado


def eliminar_inscripcion(inscripcion_id):
    resultado = inscripciones_collection.delete_one({"_id": ObjectId(inscripcion_id)})
    return resultado.deleted_count > 0
