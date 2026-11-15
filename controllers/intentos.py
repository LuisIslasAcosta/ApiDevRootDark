"""Intentos de examen seguros, también para responder sin conexión.

Cómo se evita la trampa:
- El servidor nunca manda la respuesta correcta; califica él mismo al recibir el examen.
- Cada intento se crea en línea, queda ligado al alumno y tiene sus preguntas y opciones
  en un orden propio. Se guarda en el servidor, así que el alumno no puede inventarlo.
- El envío es idempotente: el mismo intento solo se califica una vez, aunque se reenvíe.
- Hay límite de intentos por examen y un solo intento abierto a la vez.
- Se valida que cada respuesta sea una opción real de esa pregunta.
- Se registran las horas del servidor y del dispositivo; si el reloj del dispositivo se
  movió, si se pasó del tiempo o si salió de la ventana, el intento queda marcado para que
  el profesor lo revise.
"""
import hashlib
import hmac
import random
import secrets
from datetime import datetime, timedelta, timezone

from bson.objectid import ObjectId

from config.config import (
    db,
    examenes_collection,
    inscripciones_collection,
    preguntas_collection,
    respuestas_collection,
    usuarios_collection,
)

intentos_collection = db["intentos_examen"]

# Valores por omisión (cada examen puede traer los suyos)
DURACION_MINUTOS = 60          # tiempo para responder una vez que empieza
INTENTOS_MAXIMOS = 3           # intentos calificados por examen
DIAS_SIN_CONEXION = 7          # días que dura el examen descargado sin empezar
GRACIA_SEGUNDOS = 120          # tolerancia por red lenta o reloj ligeramente distinto
DESFASE_RELOJ_SEGUNDOS = 300   # diferencia de reloj que ya se considera sospechosa
SALIDAS_PERMITIDAS = 0         # salidas de la ventana que se toleran sin marcar


class ErrorIntento(Exception):
    def __init__(self, mensaje, codigo=400):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


# ================= UTILIDADES =================
def ahora():
    return datetime.now(timezone.utc)


def _utc(fecha):
    """Mongo regresa fechas sin zona horaria: se interpretan como UTC."""
    if fecha is None:
        return None
    return fecha if fecha.tzinfo else fecha.replace(tzinfo=timezone.utc)


def _iso(fecha):
    return _utc(fecha).isoformat() if fecha else None


def _desde_ms(ms):
    try:
        return datetime.fromtimestamp(float(ms) / 1000, tz=timezone.utc)
    except (TypeError, ValueError, OverflowError, OSError):
        return None


def _variantes(valor):
    valor = str(valor)
    return [valor] + ([ObjectId(valor)] if ObjectId.is_valid(valor) else [])


def _hash(clave):
    return hashlib.sha256(clave.encode()).hexdigest()


def _entero(valor, defecto, minimo=1):
    try:
        return max(minimo, int(valor))
    except (TypeError, ValueError):
        return defecto


def configuracion_examen(examen):
    return {
        "duracion_minutos": _entero(examen.get("duracion_minutos"), DURACION_MINUTOS),
        "intentos_max": _entero(examen.get("intentos_max"), INTENTOS_MAXIMOS),
        "dias_sin_conexion": _entero(examen.get("dias_sin_conexion"), DIAS_SIN_CONEXION),
    }


def buscar_examen(examen_id):
    if not ObjectId.is_valid(str(examen_id)):
        return None
    return examenes_collection.find_one({"_id": ObjectId(str(examen_id))})


def preguntas_con_respuesta(examen_id):
    """Preguntas con su respuesta correcta (solo para uso interno del servidor).

    Los ids coinciden con los que entrega /preguntas/examen/<id>.
    """
    examen_id = str(examen_id)
    preguntas = list(preguntas_collection.find({"examen_id": examen_id}))
    if preguntas:
        return [{
            "id": str(p.get("id") if p.get("id") is not None else p["_id"]),
            "enunciado": p.get("enunciado", ""),
            "opciones": [o for o in p.get("opciones", []) if str(o or "").strip()],
            "respuesta_correcta": str(p.get("respuesta_correcta") or ""),
        } for p in preguntas]

    examen = buscar_examen(examen_id)
    return [{
        "id": str(i),
        "enunciado": p.get("enunciado", ""),
        "opciones": [o for o in p.get("opciones", []) if str(o or "").strip()],
        "respuesta_correcta": str(p.get("respuesta_correcta") or ""),
    } for i, p in enumerate((examen or {}).get("preguntas", []))]


def calificar(preguntas, respuestas):
    """Califica en el servidor. Las respuestas que no son una opción real cuentan como incorrectas."""
    respuestas = respuestas if isinstance(respuestas, dict) else {}
    correctas, invalidas = 0, 0
    for p in preguntas:
        dada = respuestas.get(p["id"])
        if dada is None:
            continue
        dada = str(dada)
        if dada not in p["opciones"]:
            invalidas += 1
            continue
        if p["respuesta_correcta"] and dada.strip().lower() == p["respuesta_correcta"].strip().lower():
            correctas += 1
    total = len(preguntas)
    calificacion = round(correctas / total * 100) if total else 0
    return {"correctas": correctas, "total": total, "calificacion": calificacion, "invalidas": invalidas}


def alumno_tiene_acceso(alumno_id, curso_id):
    """Solo alumnos con inscripción aceptada (las anteriores al módulo de pagos cuentan como aceptadas)."""
    inscripcion = inscripciones_collection.find_one({
        "curso_id": {"$in": _variantes(curso_id)},
        "alumno_id": {"$in": _variantes(alumno_id)},
    })
    return bool(inscripcion) and inscripcion.get("estado", "aceptada") == "aceptada"


def intentos_usados(alumno_id, examen_id):
    """Exámenes ya calificados de este alumno (incluye los enviados con el sistema anterior)."""
    return len(list(respuestas_collection.find({
        "alumno_id": {"$in": _variantes(alumno_id)},
        "examen_id": {"$in": _variantes(examen_id)},
    })))


def rol_de(usuario_id):
    if not ObjectId.is_valid(str(usuario_id)):
        return None
    usuario = usuarios_collection.find_one({"_id": ObjectId(str(usuario_id))})
    return (usuario or {}).get("rol")


# ================= PAQUETE PARA EL ALUMNO =================
def _paquete(intento, examen, preguntas, clave=None):
    """Lo que se le manda al alumno: preguntas en su orden, sin respuestas."""
    por_id = {p["id"]: p for p in preguntas}
    lista = []
    for pid in intento["orden_preguntas"]:
        p = por_id.get(pid)
        if not p:
            continue
        orden = intento["orden_opciones"].get(pid, list(range(len(p["opciones"]))))
        opciones = [p["opciones"][i] for i in orden if i < len(p["opciones"])]
        lista.append({"id": pid, "enunciado": p["enunciado"], "opciones": opciones})

    paquete = {
        "intento_id": str(intento["_id"]),
        "examen_id": intento["examen_id"],
        "curso_id": intento.get("curso_id"),
        "titulo": examen.get("titulo", "Examen"),
        "preguntas": lista,
        "duracion_minutos": intento["duracion_minutos"],
        "creado_en": _iso(intento["creado_en"]),
        "expira_en": _iso(intento["expira_en"]),
        "iniciado_en": _iso(intento.get("iniciado_en")),
        "intento_numero": intento["numero"],
        "intentos_max": intento["intentos_max"],
        "estado": intento["estado"],
        "hora_servidor": _iso(ahora()),
    }
    if clave:
        paquete["clave_envio"] = clave
    return paquete


def obtener_o_crear_intento(alumno_id, examen_id):
    examen = buscar_examen(examen_id)
    if not examen:
        raise ErrorIntento("El examen no existe", 404)

    examen_id = str(examen["_id"])
    curso_id = str(examen.get("curso_id", ""))
    if not alumno_tiene_acceso(alumno_id, curso_id):
        raise ErrorIntento("Necesitas una inscripción aceptada en este curso para presentar el examen", 403)

    preguntas = preguntas_con_respuesta(examen_id)
    if not preguntas:
        raise ErrorIntento("Este examen todavía no tiene preguntas", 409)

    config = configuracion_examen(examen)
    momento = ahora()

    # ¿Ya hay uno abierto? Se regresa el mismo (mismas preguntas, mismo orden, mismo tiempo)
    abierto = intentos_collection.find_one({"alumno_id": str(alumno_id), "examen_id": examen_id, "estado": "abierto"})
    if abierto:
        sin_empezar_vencido = not abierto.get("iniciado_en") and _utc(abierto["expira_en"]) < momento
        if not sin_empezar_vencido:
            # Si se perdió la clave (borró los datos del navegador), se genera una nueva
            clave = secrets.token_urlsafe(32)
            intentos_collection.update_one({"_id": abierto["_id"]}, {"$set": {"clave_hash": _hash(clave)},
                                                                     "$inc": {"descargas": 1}})
            abierto["descargas"] = abierto.get("descargas", 1) + 1
            return _paquete(abierto, examen, preguntas, clave), 200
        intentos_collection.update_one({"_id": abierto["_id"]}, {"$set": {"estado": "vencido"}})

    usados = intentos_usados(alumno_id, examen_id)
    if usados >= config["intentos_max"]:
        raise ErrorIntento(f"Ya usaste tus {config['intentos_max']} intentos de este examen", 409)

    orden_preguntas = [p["id"] for p in preguntas]
    random.shuffle(orden_preguntas)
    orden_opciones = {}
    for p in preguntas:
        indices = list(range(len(p["opciones"])))
        random.shuffle(indices)
        orden_opciones[p["id"]] = indices

    clave = secrets.token_urlsafe(32)
    intento = {
        "alumno_id": str(alumno_id),
        "examen_id": examen_id,
        "curso_id": curso_id,
        "numero": usados + 1,
        "intentos_max": config["intentos_max"],
        "duracion_minutos": config["duracion_minutos"],
        "orden_preguntas": orden_preguntas,
        "orden_opciones": orden_opciones,
        "clave_hash": _hash(clave),
        "estado": "abierto",
        "creado_en": momento,
        "expira_en": momento + timedelta(days=config["dias_sin_conexion"]),
        "iniciado_en": None,
        "descargas": 1,
    }
    intento["_id"] = intentos_collection.insert_one(intento).inserted_id
    return _paquete(intento, examen, preguntas, clave), 201


# ================= AUTORIZACIÓN DEL ENVÍO =================
def buscar_intento(intento_id):
    if not ObjectId.is_valid(str(intento_id)):
        raise ErrorIntento("Intento no válido", 404)
    intento = intentos_collection.find_one({"_id": ObjectId(str(intento_id))})
    if not intento:
        raise ErrorIntento("Intento no encontrado", 404)
    return intento


def autorizar(intento, usuario_id=None, clave=None):
    """Vale la sesión del alumno dueño o la clave del intento.

    La clave sirve para sincronizar cuando el token de sesión ya caducó mientras estaba
    sin conexión. Solo permite enviar ESE intento una vez.
    """
    if usuario_id and str(usuario_id) == intento["alumno_id"]:
        return True
    if clave and hmac.compare_digest(_hash(str(clave)), intento.get("clave_hash", "")):
        return True
    raise ErrorIntento("No puedes enviar este intento", 403)


def marcar_inicio(intento, hora_cliente_ms=None, reloj_cliente_ms=None):
    """Registra cuándo empezó. Si llega estando en línea se usa la hora del servidor."""
    if intento.get("iniciado_en"):
        return intento["iniciado_en"]
    momento = ahora()
    inicio = momento
    if hora_cliente_ms is not None:
        # Llega tarde porque se empezó sin conexión: se corrige con el desfase del reloj del dispositivo
        desfase = _desfase(reloj_cliente_ms, momento)
        inicio_cliente = _desde_ms(hora_cliente_ms)
        if inicio_cliente:
            inicio = min(momento, inicio_cliente + desfase)
    intentos_collection.update_one({"_id": intento["_id"], "iniciado_en": None},
                                   {"$set": {"iniciado_en": inicio, "inicio_registrado_en": momento}})
    return inicio


def _desfase(reloj_cliente_ms, momento):
    """Diferencia entre la hora del servidor y la del dispositivo en el momento del envío."""
    reloj = _desde_ms(reloj_cliente_ms)
    return (momento - reloj) if reloj else timedelta(0)


# ================= ENVÍO Y CALIFICACIÓN =================
def enviar_intento(intento_id, datos, usuario_id=None):
    datos = datos or {}
    intento = buscar_intento(intento_id)
    autorizar(intento, usuario_id, datos.get("clave_envio"))

    # Idempotente: si ya se calificó (por ejemplo, se reenvió al reconectar) se regresa lo mismo
    if intento["estado"] == "enviado":
        return _resultado(intento), 200
    if intento["estado"] != "abierto":
        raise ErrorIntento("Este intento ya no está disponible", 409)

    # Se aparta el intento para que dos envíos simultáneos no lo califiquen dos veces
    apartado = intentos_collection.find_one_and_update(
        {"_id": intento["_id"], "estado": "abierto"},
        {"$set": {"estado": "calificando"}},
    )
    if not apartado:
        return _resultado(buscar_intento(intento_id)), 200

    try:
        return _calificar_intento(apartado, datos), 201
    except Exception:
        intentos_collection.update_one({"_id": intento["_id"]}, {"$set": {"estado": "abierto"}})
        raise


def _calificar_intento(intento, datos):
    momento = ahora()
    preguntas = preguntas_con_respuesta(intento["examen_id"])
    ids_validos = set(intento["orden_preguntas"])
    preguntas = [p for p in preguntas if p["id"] in ids_validos]
    respuestas = {str(k): v for k, v in (datos.get("respuestas") or {}).items() if str(k) in ids_validos}
    resultado = calificar(preguntas, respuestas)

    sin_conexion = bool(datos.get("sin_conexion"))
    desfase = _desfase(datos.get("reloj_cliente"), momento)
    eventos = [e for e in (datos.get("eventos") or []) if isinstance(e, dict)][:200]

    inicio_servidor = _utc(intento.get("iniciado_en"))
    inicio_cliente = _desde_ms(datos.get("iniciado_cliente"))
    fin_cliente = _desde_ms(datos.get("finalizado_cliente"))
    inicio_corregido = (inicio_cliente + desfase) if inicio_cliente else None
    fin_corregido = (fin_cliente + desfase) if fin_cliente else momento
    inicio = inicio_servidor or inicio_corregido or momento

    limite = timedelta(minutes=intento["duracion_minutos"]) + timedelta(seconds=GRACIA_SEGUNDOS)
    banderas = []

    if abs(desfase.total_seconds()) > DESFASE_RELOJ_SEGUNDOS:
        banderas.append("reloj_del_dispositivo_alterado")

    # Duración medida con el cronómetro interno del navegador (no depende del reloj del sistema)
    try:
        duracion_ms = max(0, float(datos.get("duracion_ms") or 0))
    except (TypeError, ValueError):
        duracion_ms = 0
    if duracion_ms > limite.total_seconds() * 1000:
        banderas.append("tiempo_excedido")

    # Con hora del servidor: se mide del inicio real hasta que terminó (o llegó, si fue en línea)
    fin_real = momento if not sin_conexion else fin_corregido
    if fin_real - inicio > limite and "tiempo_excedido" not in banderas:
        banderas.append("tiempo_excedido")
    if inicio_cliente and inicio_corregido and inicio_corregido > _utc(intento["expira_en"]):
        banderas.append("empezado_despues_de_vencer")
    if inicio_servidor and inicio_corregido and abs((inicio_corregido - inicio_servidor).total_seconds()) > DESFASE_RELOJ_SEGUNDOS:
        banderas.append("inicio_no_coincide")
    if resultado["invalidas"]:
        banderas.append("respuestas_no_validas")
    if intento.get("descargas", 1) > 1:
        banderas.append("examen_descargado_varias_veces")

    salidas = sum(1 for e in eventos if e.get("tipo") in {"salio_de_ventana", "cambio_de_pestana", "salio_de_pantalla_completa"})
    if salidas > SALIDAS_PERMITIDAS:
        banderas.append("salio_del_examen")
    motivo = str(datos.get("motivo") or "")[:300]
    if motivo:
        banderas.append("enviado_automaticamente")

    revision = any(b in banderas for b in (
        "reloj_del_dispositivo_alterado", "tiempo_excedido", "empezado_despues_de_vencer",
        "inicio_no_coincide", "respuestas_no_validas",
    ))

    registro = {
        "alumno_id": ObjectId(intento["alumno_id"]) if ObjectId.is_valid(intento["alumno_id"]) else intento["alumno_id"],
        "examen_id": intento["examen_id"],
        "correctas": resultado["correctas"],
        "total": resultado["total"],
        "calificacion": resultado["calificacion"],
        "fecha": momento,
        "intento_id": str(intento["_id"]),
        "intento_numero": intento["numero"],
        "sin_conexion": sin_conexion,
        "banderas": banderas,
        "requiere_revision": revision,
    }
    respuestas_collection.insert_one(registro)

    cambios = {
        "estado": "enviado",
        "respuestas": respuestas,
        "recibido_en": momento,
        "iniciado_en": inicio,
        "finalizado_en": fin_real,
        "duracion_ms": duracion_ms,
        "desfase_reloj_segundos": round(desfase.total_seconds()),
        "sin_conexion": sin_conexion,
        "eventos": eventos,
        "motivo_envio": motivo,
        "banderas": banderas,
        "requiere_revision": revision,
        "correctas": resultado["correctas"],
        "total": resultado["total"],
        "calificacion": resultado["calificacion"],
    }
    intentos_collection.update_one({"_id": intento["_id"]}, {"$set": cambios})
    return _resultado({**intento, **cambios})


def _resultado(intento):
    return {
        "mensaje": "Examen recibido",
        "intento_id": str(intento["_id"]),
        "examen_id": intento["examen_id"],
        "calificacion": intento.get("calificacion"),
        "correctas": intento.get("correctas"),
        "total": intento.get("total"),
        "intento_numero": intento.get("numero"),
        "intentos_max": intento.get("intentos_max"),
        "requiere_revision": intento.get("requiere_revision", False),
        "recibido_en": _iso(intento.get("recibido_en")),
    }


# ================= VISTA DEL PROFESOR =================
def intentos_de_examen(examen_id):
    usuarios = {}
    lista = []
    for i in intentos_collection.find({"examen_id": str(examen_id)}):
        aid = i["alumno_id"]
        if aid not in usuarios:
            u = usuarios_collection.find_one({"_id": ObjectId(aid)}) if ObjectId.is_valid(aid) else None
            usuarios[aid] = " ".join(filter(None, [(u or {}).get("nombre"), (u or {}).get("apellidop")])) or "Alumno"
        lista.append({
            "intento_id": str(i["_id"]),
            "alumno_id": aid,
            "alumno": usuarios[aid],
            "numero": i.get("numero"),
            "estado": i.get("estado"),
            "calificacion": i.get("calificacion"),
            "sin_conexion": i.get("sin_conexion", False),
            "banderas": i.get("banderas", []),
            "requiere_revision": i.get("requiere_revision", False),
            "iniciado_en": _iso(i.get("iniciado_en")),
            "recibido_en": _iso(i.get("recibido_en")),
            "duracion_ms": i.get("duracion_ms"),
            "desfase_reloj_segundos": i.get("desfase_reloj_segundos"),
            "eventos": i.get("eventos", []),
            "motivo_envio": i.get("motivo_envio", ""),
        })
    lista.sort(key=lambda x: x["recibido_en"] or x["iniciado_en"] or "", reverse=True)
    return lista
