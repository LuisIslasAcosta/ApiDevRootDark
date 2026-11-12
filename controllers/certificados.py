"""
Certificados de término de curso.

- Se emite solo si el alumno terminó todo el curso (lecciones y exámenes) y su
  promedio es aprobatorio.
- Cada certificado tiene un folio único que cualquiera puede verificar en la
  página pública /verificar/<folio>.
- Si el alumno vuelve a pedirlo, recibe el mismo certificado (no se duplica).
"""
import secrets
from datetime import datetime, timezone

from bson.objectid import ObjectId

from config.config import db, cursos_collection, usuarios_collection
from controllers.progreso_academico import progreso_alumno_curso, CALIFICACION_APROBATORIA

certificados_collection = db["certificados"]

_ALFABETO = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"  # sin 0/O ni 1/I para que se lea bien


class ErrorCertificado(Exception):
    def __init__(self, mensaje, codigo=400, extra=None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo
        self.extra = extra or {}


def _ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _nuevo_folio():
    while True:
        codigo = "".join(secrets.choice(_ALFABETO) for _ in range(8))
        folio = f"DRD-{_ahora().year}-{codigo[:4]}-{codigo[4:]}"
        if not certificados_collection.find_one({"folio": folio}):
            return folio


def _nombre_completo(usuario):
    if not usuario:
        return ""
    partes = [usuario.get("nombre"), usuario.get("apellidop"), usuario.get("apellidom")]
    return " ".join(p.strip() for p in partes if p and p.strip())


def _serializar(c, publico=False):
    datos = {
        "folio": c["folio"],
        "alumno": c["alumno_nombre"],
        "curso": c["curso_nombre"],
        "profesor": c.get("profesor_nombre", ""),
        "promedio": c.get("promedio"),
        "lecciones": c.get("lecciones", 0),
        "examenes": c.get("examenes", 0),
        "fecha_emision": c["fecha_emision"].isoformat() + "Z",
        "valido": not c.get("revocado", False),
    }
    if not publico:
        datos["curso_id"] = c["curso_id"]
    return datos


def emitir_certificado(alumno_id, curso_id):
    """Devuelve el certificado del alumno en el curso, creándolo si ya cumple los requisitos."""
    existente = certificados_collection.find_one({"alumno_id": str(alumno_id), "curso_id": str(curso_id)})
    if existente:
        return _serializar(existente)

    progreso = progreso_alumno_curso(alumno_id, curso_id)
    if "error" in progreso:
        raise ErrorCertificado(progreso["error"], 404)

    faltan_lecciones = progreso["total_lecciones"] - progreso["lecciones_vistas"]
    faltan_examenes = progreso["total_examenes"] - progreso["examenes_presentados"]
    if not progreso["terminado"]:
        raise ErrorCertificado(
            "Aún no terminas el curso.",
            403,
            {"faltan_lecciones": max(0, faltan_lecciones), "faltan_examenes": max(0, faltan_examenes)},
        )
    if progreso["promedio"] is None or progreso["promedio"] < CALIFICACION_APROBATORIA:
        raise ErrorCertificado(
            f"Necesitas un promedio de {CALIFICACION_APROBATORIA}% o más para obtener el certificado.",
            403,
            {"promedio": progreso["promedio"], "examenes_reprobados": progreso["examenes_reprobados"]},
        )

    try:
        alumno = usuarios_collection.find_one({"_id": ObjectId(str(alumno_id))})
        curso = cursos_collection.find_one({"_id": ObjectId(str(curso_id))})
    except Exception:
        alumno, curso = None, None
    if not alumno or not curso:
        raise ErrorCertificado("No se encontró el alumno o el curso.", 404)

    certificado = {
        "folio": _nuevo_folio(),
        "alumno_id": str(alumno_id),
        "alumno_nombre": _nombre_completo(alumno) or alumno.get("email", "Alumno"),
        "curso_id": str(curso_id),
        "curso_nombre": curso.get("nombre", "Curso"),
        "profesor_nombre": progreso.get("profesor", ""),
        "promedio": progreso["promedio"],
        "lecciones": progreso["total_lecciones"],
        "examenes": progreso["total_examenes"],
        "fecha_emision": _ahora(),
        "revocado": False,
    }
    certificados_collection.insert_one(certificado)
    return _serializar(certificado)


def estado_certificado(alumno_id, curso_id):
    """Si el alumno ya tiene certificado, o qué le falta para obtenerlo (sin emitirlo)."""
    existente = certificados_collection.find_one({"alumno_id": str(alumno_id), "curso_id": str(curso_id)})
    if existente:
        return {"disponible": True, "emitido": True, "certificado": _serializar(existente)}
    p = progreso_alumno_curso(alumno_id, curso_id)
    if "error" in p:
        raise ErrorCertificado(p["error"], 404)
    aprobado = p["promedio"] is not None and p["promedio"] >= CALIFICACION_APROBATORIA
    return {
        "disponible": bool(p["terminado"] and aprobado),
        "emitido": False,
        "terminado": p["terminado"],
        "promedio": p["promedio"],
        "calificacion_aprobatoria": CALIFICACION_APROBATORIA,
        "faltan_lecciones": max(0, p["total_lecciones"] - p["lecciones_vistas"]),
        "faltan_examenes": max(0, p["total_examenes"] - p["examenes_presentados"]),
        "examenes_reprobados": p["examenes_reprobados"],
    }


def mis_certificados(alumno_id):
    lista = certificados_collection.find({"alumno_id": str(alumno_id)}).sort("fecha_emision", -1)
    return {"certificados": [_serializar(c) for c in lista]}


def verificar(folio):
    """Verificación pública: solo muestra los datos impresos en el certificado."""
    folio = (folio or "").strip().upper()
    c = certificados_collection.find_one({"folio": folio})
    if not c:
        return {"valido": False, "folio": folio, "mensaje": "No existe un certificado con este folio."}
    datos = _serializar(c, publico=True)
    if not datos["valido"]:
        datos["mensaje"] = "Este certificado fue revocado."
    return datos
