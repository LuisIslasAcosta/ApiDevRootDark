from bson.objectid import ObjectId

from config.config import inscripciones_collection, cursos_collection, usuarios_collection


def _buscar(coleccion, id_texto):
    id_texto = str(id_texto)
    if not ObjectId.is_valid(id_texto):
        return None
    return coleccion.find_one({"_id": ObjectId(id_texto)})


def _variantes_id(id_texto):
    """Algunas inscripciones guardan el ID como texto y otras como ObjectId: se buscan ambas."""
    id_texto = str(id_texto)
    return [id_texto] + ([ObjectId(id_texto)] if ObjectId.is_valid(id_texto) else [])


def serializar_inscripcion(inscripcion):
    curso_id = str(inscripcion.get("curso_id", ""))
    alumno_id = str(inscripcion.get("alumno_id", ""))
    curso = _buscar(cursos_collection, curso_id)
    alumno = _buscar(usuarios_collection, alumno_id)
    comprobante = inscripcion.get("comprobante") or {}

    nombre_alumno = "Usuario eliminado"
    if alumno:
        nombre_alumno = " ".join(filter(None, [alumno.get("nombre"), alumno.get("apellidop"), alumno.get("apellidom")])) or "Sin nombre"

    return {
        "id": str(inscripcion["_id"]),
        "curso_id": curso_id,
        "curso_nombre": curso["nombre"] if curso else "Desconocido",
        "curso_precio": float(curso.get("precio") or 0) if curso else 0,
        "instrucciones_pago": curso.get("instrucciones_pago", "") if curso else "",
        "profesor_id": inscripcion.get("profesor_id") or (str(curso.get("profesor", "")) if curso else ""),
        "alumno_id": alumno_id,
        "alumno_nombre": nombre_alumno,
        "alumno_email": alumno.get("email", "") if alumno else "",
        "alumno_matricula": alumno.get("matricula", "") if alumno else "",
        # ---- pago ----
        "estado": inscripcion.get("estado", "aceptada"),
        "referencia_pago": inscripcion.get("referencia_pago", ""),
        "monto": inscripcion.get("monto", float(curso.get("precio") or 0) if curso else 0),
        "fecha_inscripcion": inscripcion.get("fecha_inscripcion"),
        "fecha_comprobante": inscripcion.get("fecha_comprobante"),
        "fecha_validacion": inscripcion.get("fecha_validacion"),
        "motivo_rechazo": inscripcion.get("motivo_rechazo"),
        "tiene_comprobante": bool(comprobante),
        "comprobante_nombre": comprobante.get("nombre_original", ""),
        "comprobante_tipo": comprobante.get("tipo", ""),
        "datos_pago_alumno": inscripcion.get("datos_pago_alumno") or {},
    }


def obtener_inscripcion(inscripcion_id):
    return _buscar(inscripciones_collection, inscripcion_id)


def obtener_inscripciones():
    return [serializar_inscripcion(ins) for ins in inscripciones_collection.find()]


def obtener_inscripciones_por_curso(curso_id, solo_aceptadas=False):
    resultado = []
    for ins in inscripciones_collection.find({"curso_id": {"$in": _variantes_id(curso_id)}}):
        if solo_aceptadas and ins.get("estado", "aceptada") != "aceptada":
            continue
        resultado.append(serializar_inscripcion(ins))
    return resultado


def obtener_inscripciones_por_alumno(alumno_id):
    return [serializar_inscripcion(ins) for ins in inscripciones_collection.find({"alumno_id": {"$in": _variantes_id(alumno_id)}})]


def obtener_pagos_profesor(profesor_id, estado=None):
    """Inscripciones de todos los cursos del profesor, las más recientes primero."""
    ids_cursos = [str(c["_id"]) for c in cursos_collection.find({"profesor": profesor_id})]
    if not ids_cursos:
        return []
    filtro = {"curso_id": {"$in": [v for cid in ids_cursos for v in _variantes_id(cid)]}}
    lista = [serializar_inscripcion(ins) for ins in inscripciones_collection.find(filtro)]
    if estado:
        lista = [i for i in lista if i["estado"] == estado]
    orden = {"en_revision": 0, "pendiente_pago": 1, "rechazada": 2, "aceptada": 3}
    lista.sort(key=lambda i: i.get("fecha_comprobante") or i.get("fecha_inscripcion") or "", reverse=True)
    lista.sort(key=lambda i: orden.get(i["estado"], 9))
    return lista
