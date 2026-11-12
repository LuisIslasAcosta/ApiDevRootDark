"""
Chat registrado entre profesor y alumno.

Reglas de seguridad:
- Solo pueden conversar un profesor y un alumno inscrito (aceptado) en uno de sus cursos.
- Todos los mensajes quedan registrados: no existe forma de editarlos ni borrarlos.
- Cualquiera de los dos puede reportar la conversación; el reporte llega al administrador.
- El administrador solo puede leer conversaciones que tienen un reporte, y cada vez que
  las abre queda registrado quién y cuándo.
- El administrador decide y puede cerrar la conversación.
"""
from datetime import datetime, timezone

from bson.objectid import ObjectId

from config.config import db, usuarios_collection, cursos_collection, inscripciones_collection

conversaciones_collection = db["chat_conversaciones"]
mensajes_collection = db["chat_mensajes"]
reportes_collection = db["chat_reportes"]

MAX_CARACTERES = 2000

MOTIVOS_REPORTE = {
    "insinuacion": "Insinuación o comentario de tipo sexual",
    "acoso": "Acoso, presión o amenazas",
    "ofensivo": "Lenguaje ofensivo o discriminatorio",
    "datos_personales": "Pide datos personales o contacto fuera de la plataforma",
    "otro": "Otro motivo",
}

DECISIONES = {
    "sin_falta": "No se encontró una falta",
    "advertencia": "Conducta inapropiada: se envió una advertencia",
    "conducta_grave": "Conducta grave: se cerró la conversación",
}


# ======================================================================
# Utilidades
# ======================================================================

class ErrorChat(Exception):
    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


def _ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _iso(fecha):
    return fecha.isoformat() + "Z" if isinstance(fecha, datetime) else fecha


def _oid(valor):
    try:
        return ObjectId(str(valor))
    except Exception:
        raise ErrorChat("Identificador inválido", 400)


def _variantes(valor):
    variantes = [str(valor)]
    try:
        variantes.append(ObjectId(str(valor)))
    except Exception:
        pass
    return variantes


def _usuario(usuario_id):
    try:
        return usuarios_collection.find_one({"_id": ObjectId(str(usuario_id))})
    except Exception:
        return None


def _nombre(usuario):
    if not usuario:
        return "Usuario eliminado"
    partes = [usuario.get("nombre"), usuario.get("apellidop"), usuario.get("apellidom")]
    return " ".join(p for p in partes if p) or usuario.get("email", "Sin nombre")


def _rol(usuario):
    rol = (usuario or {}).get("rol", "usuario")
    if rol == "administrador":
        return "administrador"
    if rol == "profesor":
        return "profesor"
    return "alumno"


def _usuario_actual(usuario_id):
    usuario = _usuario(usuario_id)
    if not usuario:
        raise ErrorChat("Usuario no encontrado", 401)
    return usuario


def _inscripcion_aceptada(alumno_id, curso_id):
    for ins in inscripciones_collection.find({
        "alumno_id": {"$in": _variantes(alumno_id)},
        "curso_id": {"$in": _variantes(curso_id)},
    }):
        if ins.get("estado", "aceptada") == "aceptada":
            return True
    return False


def _serializar_conversacion(conv, yo_id):
    yo = str(yo_id)
    soy_profesor = yo == conv["profesor_id"]
    otro_id = conv["alumno_id"] if soy_profesor else conv["profesor_id"]
    otro = _usuario(otro_id)
    leido = (conv.get("leido_por") or {}).get(yo)
    filtro_no_leidos = {"conversacion_id": str(conv["_id"]), "autor_id": {"$ne": yo}, "tipo": "mensaje"}
    if leido:
        filtro_no_leidos["fecha"] = {"$gt": leido}
    ultimo = mensajes_collection.find_one({"conversacion_id": str(conv["_id"])}, sort=[("fecha", -1)])
    return {
        "id": str(conv["_id"]),
        "curso_id": conv["curso_id"],
        "curso": conv.get("curso_nombre", ""),
        "estado": conv.get("estado", "abierta"),
        "con": {
            "id": otro_id,
            "nombre": _nombre(otro),
            "rol": "alumno" if soy_profesor else "profesor",
            "foto": (otro or {}).get("foto_perfil") if otro and str((otro or {}).get("foto_perfil", "")).startswith("http") else None,
        },
        "ultimo_mensaje": {
            "texto": (ultimo or {}).get("texto", ""),
            "fecha": _iso((ultimo or {}).get("fecha")),
            "mio": (ultimo or {}).get("autor_id") == yo,
            "tipo": (ultimo or {}).get("tipo", "mensaje"),
        } if ultimo else None,
        "no_leidos": mensajes_collection.count_documents(filtro_no_leidos),
        "reportada_por_mi": reportes_collection.count_documents({"conversacion_id": str(conv["_id"]), "reportado_por": yo}) > 0,
        "creada": _iso(conv.get("creada")),
    }


def _serializar_mensaje(m, yo_id=None):
    return {
        "id": str(m["_id"]),
        "autor_id": m.get("autor_id"),
        "autor_nombre": m.get("autor_nombre", ""),
        "autor_rol": m.get("autor_rol", ""),
        "texto": m.get("texto", ""),
        "tipo": m.get("tipo", "mensaje"),  # mensaje | sistema
        "fecha": _iso(m.get("fecha")),
        "mio": yo_id is not None and m.get("autor_id") == str(yo_id),
    }


def _conversacion_de_participante(conversacion_id, usuario_id):
    conv = conversaciones_collection.find_one({"_id": _oid(conversacion_id)})
    if not conv:
        raise ErrorChat("Conversación no encontrada", 404)
    if str(usuario_id) not in (conv["profesor_id"], conv["alumno_id"]):
        raise ErrorChat("No tienes acceso a esta conversación", 403)
    return conv


def _mensaje_sistema(conversacion_id, texto):
    mensajes_collection.insert_one({
        "conversacion_id": str(conversacion_id),
        "autor_id": None,
        "autor_nombre": "DevRootDark",
        "autor_rol": "sistema",
        "texto": texto,
        "tipo": "sistema",
        "fecha": _ahora(),
    })


# ======================================================================
# Alumno y profesor
# ======================================================================

def contactos(usuario_id):
    """Con quién puede abrir una conversación el usuario."""
    usuario = _usuario_actual(usuario_id)
    rol = _rol(usuario)
    resultado = []

    if rol == "profesor":
        for curso in cursos_collection.find({"profesor": {"$in": _variantes(usuario_id)}}):
            for ins in inscripciones_collection.find({"curso_id": {"$in": _variantes(curso["_id"])}}):
                if ins.get("estado", "aceptada") != "aceptada":
                    continue
                alumno = _usuario(ins.get("alumno_id"))
                if not alumno:
                    continue
                resultado.append({
                    "curso_id": str(curso["_id"]),
                    "curso": curso.get("nombre", "Curso"),
                    "usuario_id": str(alumno["_id"]),
                    "nombre": _nombre(alumno),
                    "rol": "alumno",
                })
    elif rol == "alumno":
        for ins in inscripciones_collection.find({"alumno_id": {"$in": _variantes(usuario_id)}}):
            if ins.get("estado", "aceptada") != "aceptada":
                continue
            try:
                curso = cursos_collection.find_one({"_id": ObjectId(str(ins.get("curso_id")))})
            except Exception:
                curso = None
            if not curso:
                continue
            profesor = _usuario(curso.get("profesor"))
            if not profesor:
                continue
            resultado.append({
                "curso_id": str(curso["_id"]),
                "curso": curso.get("nombre", "Curso"),
                "usuario_id": str(profesor["_id"]),
                "nombre": _nombre(profesor),
                "rol": "profesor",
            })

    vistos, unicos = set(), []
    for c in resultado:
        clave = (c["curso_id"], c["usuario_id"])
        if clave not in vistos:
            vistos.add(clave)
            unicos.append(c)
    unicos.sort(key=lambda c: (c["curso"], c["nombre"]))
    return {"rol": rol, "contactos": unicos}


def abrir_conversacion(usuario_id, curso_id, otro_id=None):
    """Obtiene o crea la conversación profesor–alumno de un curso."""
    usuario = _usuario_actual(usuario_id)
    rol = _rol(usuario)
    curso = cursos_collection.find_one({"_id": _oid(curso_id)})
    if not curso:
        raise ErrorChat("Curso no encontrado", 404)
    profesor_id = str(curso.get("profesor"))

    if rol == "profesor":
        if profesor_id != str(usuario_id):
            raise ErrorChat("Solo puedes escribir a alumnos de tus cursos", 403)
        if not otro_id:
            raise ErrorChat("Indica el alumno", 400)
        alumno_id = str(otro_id)
    elif rol == "alumno":
        alumno_id = str(usuario_id)
    else:
        raise ErrorChat("El administrador no participa en las conversaciones", 403)

    if not _inscripcion_aceptada(alumno_id, curso_id):
        raise ErrorChat("El alumno no está inscrito en este curso", 403)

    conv = conversaciones_collection.find_one({
        "curso_id": str(curso["_id"]),
        "profesor_id": profesor_id,
        "alumno_id": alumno_id,
    })
    if not conv:
        ahora = _ahora()
        conv = {
            "curso_id": str(curso["_id"]),
            "curso_nombre": curso.get("nombre", "Curso"),
            "profesor_id": profesor_id,
            "alumno_id": alumno_id,
            "estado": "abierta",
            "creada": ahora,
            "creada_por": str(usuario_id),
            "leido_por": {},
        }
        conv["_id"] = conversaciones_collection.insert_one(conv).inserted_id
        _mensaje_sistema(
            conv["_id"],
            "Conversación iniciada. Todos los mensajes quedan registrados y no se pueden borrar. "
            "Si algo te hace sentir incómodo, usa el botón Reportar.",
        )
    return _serializar_conversacion(conv, usuario_id)


def mis_conversaciones(usuario_id):
    _usuario_actual(usuario_id)
    yo = str(usuario_id)
    convs = list(conversaciones_collection.find({"$or": [{"profesor_id": yo}, {"alumno_id": yo}]}))
    lista = [_serializar_conversacion(c, yo) for c in convs]
    lista.sort(key=lambda c: (c["ultimo_mensaje"] or {}).get("fecha") or c["creada"] or "", reverse=True)
    return {"conversaciones": lista}


def mensajes(usuario_id, conversacion_id):
    conv = _conversacion_de_participante(conversacion_id, usuario_id)
    lista = [
        _serializar_mensaje(m, usuario_id)
        for m in mensajes_collection.find({"conversacion_id": str(conv["_id"])}).sort("fecha", 1)
    ]
    conversaciones_collection.update_one({"_id": conv["_id"]}, {"$set": {f"leido_por.{usuario_id}": _ahora()}})
    return {"conversacion": _serializar_conversacion(conv, usuario_id), "mensajes": lista}


def enviar_mensaje(usuario_id, conversacion_id, texto):
    conv = _conversacion_de_participante(conversacion_id, usuario_id)
    if conv.get("estado") == "cerrada":
        raise ErrorChat("Esta conversación fue cerrada por el administrador", 403)
    texto = (texto or "").strip()
    if not texto:
        raise ErrorChat("El mensaje está vacío", 400)
    if len(texto) > MAX_CARACTERES:
        raise ErrorChat(f"El mensaje no puede tener más de {MAX_CARACTERES} caracteres", 400)

    usuario = _usuario_actual(usuario_id)
    ahora = _ahora()
    mensaje = {
        "conversacion_id": str(conv["_id"]),
        "autor_id": str(usuario_id),
        "autor_nombre": _nombre(usuario),
        "autor_rol": "profesor" if str(usuario_id) == conv["profesor_id"] else "alumno",
        "texto": texto,
        "tipo": "mensaje",
        "fecha": ahora,
    }
    mensaje["_id"] = mensajes_collection.insert_one(mensaje).inserted_id
    conversaciones_collection.update_one({"_id": conv["_id"]}, {"$set": {f"leido_por.{usuario_id}": ahora, "actualizada": ahora}})
    return _serializar_mensaje(mensaje, usuario_id)


def reportar(usuario_id, conversacion_id, motivo, descripcion, mensaje_id=None):
    conv = _conversacion_de_participante(conversacion_id, usuario_id)
    if motivo not in MOTIVOS_REPORTE:
        raise ErrorChat("Elige un motivo válido", 400)
    descripcion = (descripcion or "").strip()[:MAX_CARACTERES]

    mensaje_reportado = None
    if mensaje_id:
        m = mensajes_collection.find_one({"_id": _oid(mensaje_id), "conversacion_id": str(conv["_id"])})
        if m:
            mensaje_reportado = str(m["_id"])

    yo = str(usuario_id)
    reportado = conv["alumno_id"] if yo == conv["profesor_id"] else conv["profesor_id"]
    reporte = {
        "conversacion_id": str(conv["_id"]),
        "curso_id": conv["curso_id"],
        "curso_nombre": conv.get("curso_nombre", ""),
        "reportado_por": yo,
        "rol_reporta": "profesor" if yo == conv["profesor_id"] else "alumno",
        "usuario_reportado": reportado,
        "motivo": motivo,
        "descripcion": descripcion,
        "mensaje_id": mensaje_reportado,
        "estado": "pendiente",  # pendiente | resuelto
        "fecha": _ahora(),
        "accesos_admin": [],
    }
    reporte["_id"] = reportes_collection.insert_one(reporte).inserted_id
    # A la otra persona no se le avisa del reporte, para evitar represalias.
    conversaciones_collection.update_one({"_id": conv["_id"]}, {"$set": {"reportada": True}})
    return {"mensaje": "Reporte enviado al administrador. Gracias por avisar.", "reporte_id": str(reporte["_id"])}


# ======================================================================
# Administrador
# ======================================================================

def _exigir_admin(usuario_id):
    if _rol(_usuario_actual(usuario_id)) != "administrador":
        raise ErrorChat("Solo el administrador puede ver los reportes", 403)


def _serializar_reporte(r):
    reporta = _usuario(r["reportado_por"])
    reportado = _usuario(r["usuario_reportado"])
    return {
        "id": str(r["_id"]),
        "conversacion_id": r["conversacion_id"],
        "curso": r.get("curso_nombre", ""),
        "motivo": r["motivo"],
        "motivo_texto": MOTIVOS_REPORTE.get(r["motivo"], r["motivo"]),
        "descripcion": r.get("descripcion", ""),
        "mensaje_id": r.get("mensaje_id"),
        "estado": r.get("estado", "pendiente"),
        "fecha": _iso(r.get("fecha")),
        "reporta": {"id": r["reportado_por"], "nombre": _nombre(reporta), "rol": r.get("rol_reporta"), "email": (reporta or {}).get("email", "")},
        "reportado": {
            "id": r["usuario_reportado"],
            "nombre": _nombre(reportado),
            "rol": "alumno" if r.get("rol_reporta") == "profesor" else "profesor",
            "email": (reportado or {}).get("email", ""),
        },
        "decision": r.get("decision"),
        "decision_texto": DECISIONES.get(r.get("decision"), ""),
        "nota_admin": r.get("nota_admin", ""),
        "resuelto_por": _nombre(_usuario(r["resuelto_por"])) if r.get("resuelto_por") else "",
        "fecha_resolucion": _iso(r.get("fecha_resolucion")),
        "accesos_admin": [
            {"admin": _nombre(_usuario(a.get("admin_id"))), "fecha": _iso(a.get("fecha"))}
            for a in r.get("accesos_admin", [])
        ],
    }


def admin_reportes(usuario_id, estado=None):
    _exigir_admin(usuario_id)
    filtro = {"estado": estado} if estado in ("pendiente", "resuelto") else {}
    lista = [_serializar_reporte(r) for r in reportes_collection.find(filtro).sort("fecha", -1)]
    return {
        "pendientes": reportes_collection.count_documents({"estado": "pendiente"}),
        "motivos": MOTIVOS_REPORTE,
        "decisiones": DECISIONES,
        "reportes": lista,
    }


def admin_detalle_reporte(usuario_id, reporte_id):
    """Reporte + conversación completa. Cada consulta queda registrada."""
    _exigir_admin(usuario_id)
    reporte = reportes_collection.find_one({"_id": _oid(reporte_id)})
    if not reporte:
        raise ErrorChat("Reporte no encontrado", 404)
    reportes_collection.update_one(
        {"_id": reporte["_id"]},
        {"$push": {"accesos_admin": {"admin_id": str(usuario_id), "fecha": _ahora()}}},
    )
    reporte = reportes_collection.find_one({"_id": reporte["_id"]})
    conv = conversaciones_collection.find_one({"_id": _oid(reporte["conversacion_id"])})
    msgs = [_serializar_mensaje(m) for m in mensajes_collection.find({"conversacion_id": reporte["conversacion_id"]}).sort("fecha", 1)]
    otros = [
        _serializar_reporte(r)
        for r in reportes_collection.find({"conversacion_id": reporte["conversacion_id"], "_id": {"$ne": reporte["_id"]}}).sort("fecha", -1)
    ]
    return {
        "reporte": _serializar_reporte(reporte),
        "conversacion": {
            "id": str(conv["_id"]) if conv else reporte["conversacion_id"],
            "estado": (conv or {}).get("estado", "abierta"),
            "curso": (conv or {}).get("curso_nombre", ""),
            "profesor": _nombre(_usuario((conv or {}).get("profesor_id"))),
            "alumno": _nombre(_usuario((conv or {}).get("alumno_id"))),
            "profesor_id": (conv or {}).get("profesor_id"),
            "alumno_id": (conv or {}).get("alumno_id"),
        },
        "mensajes": msgs,
        "otros_reportes": otros,
    }


def admin_resolver(usuario_id, reporte_id, decision, nota):
    _exigir_admin(usuario_id)
    if decision not in DECISIONES:
        raise ErrorChat("Elige una decisión válida", 400)
    reporte = reportes_collection.find_one({"_id": _oid(reporte_id)})
    if not reporte:
        raise ErrorChat("Reporte no encontrado", 404)

    ahora = _ahora()
    reportes_collection.update_one({"_id": reporte["_id"]}, {"$set": {
        "estado": "resuelto",
        "decision": decision,
        "nota_admin": (nota or "").strip()[:MAX_CARACTERES],
        "resuelto_por": str(usuario_id),
        "fecha_resolucion": ahora,
    }})

    conv_id = reporte["conversacion_id"]
    if decision == "advertencia":
        _mensaje_sistema(conv_id, "El administrador revisó esta conversación y recuerda mantener un trato respetuoso y profesional. Los mensajes siguen registrándose.")
    elif decision == "conducta_grave":
        conversaciones_collection.update_one({"_id": _oid(conv_id)}, {"$set": {"estado": "cerrada", "cerrada": ahora, "cerrada_por": str(usuario_id)}})
        _mensaje_sistema(conv_id, "El administrador cerró esta conversación después de revisar un reporte. Ya no se pueden enviar mensajes.")

    return {"mensaje": "Decisión registrada", "reporte": _serializar_reporte(reportes_collection.find_one({"_id": reporte["_id"]}))}
