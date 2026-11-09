from config.config import respuestas_collection, usuarios_collection, examenes_collection, cursos_collection
from bson.objectid import ObjectId


def _con_objectid(valores):
    """Devuelve cada id como texto y como ObjectId (la BD tiene ambos formatos)."""
    salida = []
    for v in valores:
        salida.append(str(v))
        try:
            salida.append(ObjectId(str(v)))
        except Exception:
            pass
    return salida


def obtener_reportes_profesor(profesor_id):
    """Resultados de exámenes de los cursos del profesor (consultas en lote)."""
    try:
        ObjectId(str(profesor_id))
    except Exception:
        print(" profesor_id inválido")
        return []

    # 1) Cursos del profesor
    cursos = {
        str(c["_id"]): c
        for c in cursos_collection.find(
            {"profesor": {"$in": _con_objectid([profesor_id])}},
            {"nombre": 1})
    }
    if not cursos:
        return []

    # 2) Exámenes de esos cursos
    examenes = {
        str(e["_id"]): e
        for e in examenes_collection.find(
            {"curso_id": {"$in": _con_objectid(cursos.keys())}},
            {"titulo": 1, "curso_id": 1, "fecha": 1})
    }
    if not examenes:
        return []

    # 3) Respuestas de esos exámenes
    respuestas = list(respuestas_collection.find(
        {"examen_id": {"$in": _con_objectid(examenes.keys())}}))

    # 4) Alumnos involucrados
    alumnos_ids = {str(r.get("alumno_id")) for r in respuestas if r.get("alumno_id")}
    alumnos = {
        str(u["_id"]): u
        for u in usuarios_collection.find(
            {"_id": {"$in": [ObjectId(a) for a in alumnos_ids if ObjectId.is_valid(a)]}},
            {"nombre": 1, "email": 1})
    }

    reportes = []
    for r in respuestas:
        examen = examenes.get(str(r.get("examen_id")))
        if not examen:
            continue
        curso = cursos.get(str(examen.get("curso_id")))
        if not curso:
            continue
        alumno = alumnos.get(str(r.get("alumno_id")))

        reportes.append({
            "alumno": alumno.get("nombre", "Usuario eliminado") if alumno else "Usuario eliminado",
            "email": alumno.get("email", "") if alumno else "",
            "curso": curso.get("nombre", "Curso sin nombre"),
            "examen": examen.get("titulo", "Examen sin título"),
            "correctas": r.get("correctas", 0),
            "total": r.get("total", 0),
            "calificacion": r.get("calificacion", 0),
            "fecha": examen.get("fecha", "")
        })

    print(" REPORTES ENVIADOS:", len(reportes))
    return reportes
