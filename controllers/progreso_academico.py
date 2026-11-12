"""
Progreso académico por curso, riesgo de reprobar / abandono y recomendaciones.

- Alumno:   progreso de cada curso (lecciones + exámenes), calificaciones, nivel,
            alertas de riesgo, consejos y cursos recomendados según lo que terminó.
- Profesor: alumnos de sus cursos en riesgo de reprobar o de abandono (más de
            DIAS_ABANDONO días sin actividad) con recomendaciones de qué hacer.
"""
import re
from datetime import datetime, timezone
from collections import Counter

from bson.objectid import ObjectId

from config.config import (
    cursos_collection,
    examenes_collection,
    inscripciones_collection,
    lecciones_collection,
    lecciones_vistas_collection,
    niveles_collection,
    respuestas_collection,
    usuarios_collection,
)

CALIFICACION_APROBATORIA = 70
DIAS_ABANDONO = 5


# ======================================================================
# Utilidades
# ======================================================================

def _variantes_id(valor):
    """Un id puede estar guardado como texto o como ObjectId."""
    variantes = [str(valor)]
    try:
        variantes.append(ObjectId(str(valor)))
    except Exception:
        pass
    return variantes


def _ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _a_fecha(valor):
    """Convierte datetime, texto ISO o ObjectId a datetime UTC sin zona."""
    if valor is None:
        return None
    if isinstance(valor, ObjectId):
        return valor.generation_time.replace(tzinfo=None)
    if isinstance(valor, datetime):
        if valor.tzinfo:
            return valor.astimezone(timezone.utc).replace(tzinfo=None)
        return valor
    if isinstance(valor, str) and valor.strip():
        texto = valor.strip().replace("Z", "+00:00")
        try:
            fecha = datetime.fromisoformat(texto)
            return _a_fecha(fecha)
        except ValueError:
            for formato in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                try:
                    return datetime.strptime(texto[:19], formato)
                except ValueError:
                    continue
    return None


def _iso(fecha):
    return fecha.isoformat() + "Z" if fecha else None


def _nombre_usuario(usuario):
    if not usuario:
        return "Usuario eliminado"
    partes = [usuario.get("nombre"), usuario.get("apellidop"), usuario.get("apellidom")]
    return " ".join(p for p in partes if p) or "Sin nombre"


def nivel_desempeno(promedio):
    if promedio is None:
        return "Sin evaluar"
    if promedio >= 90:
        return "Excelente"
    if promedio >= 80:
        return "Bueno"
    if promedio >= CALIFICACION_APROBATORIA:
        return "Suficiente"
    if promedio >= 50:
        return "En riesgo"
    return "Crítico"


def _imagen_curso(curso):
    imagenes = curso.get("imagenes") or []
    return imagenes[0] if imagenes else None


# ======================================================================
# Rutas de aprendizaje: qué curso conviene después de cada tema
# ======================================================================

# Cada tema: cómo reconocerlo en el nombre/descripción del curso y a qué temas lleva.
TEMAS = {
    "cpp": {"nombre": "C++", "patron": r"c\+\+|\bcpp\b"},
    "c": {"nombre": "C", "patron": r"(?<![\w#+])lenguaje c\b|\bprogramaci[oó]n en c\b"},
    "iot": {"nombre": "IoT y Arduino", "patron": r"\biot\b|arduino|internet de las cosas|esp32|esp8266|raspberry|microcontrolador|embebid|electr[oó]nica"},
    "robotica": {"nombre": "Robótica", "patron": r"rob[oó]tic"},
    "python": {"nombre": "Python", "patron": r"\bpython\b"},
    "datos": {"nombre": "Ciencia de datos", "patron": r"ciencia de datos|an[aá]lisis de datos|\bdata\b|pandas|estad[ií]stica|big data|spark"},
    "ia": {"nombre": "Inteligencia artificial", "patron": r"inteligencia artificial|machine learning|aprendizaje autom[aá]tico|deep learning|\bia\b|redes neuronales"},
    "web_basico": {"nombre": "HTML, CSS y JavaScript", "patron": r"\bhtml\b|\bcss\b|javascript|\bjs\b|desarrollo web|p[aá]ginas web"},
    "react": {"nombre": "React", "patron": r"\breact\b(?! native)|\bvue\b|angular|frontend"},
    "movil": {"nombre": "Apps móviles", "patron": r"react native|m[oó]vil|android|\bios\b|flutter|kotlin|expo"},
    "backend": {"nombre": "Backend y APIs", "patron": r"node|express|backend|\bapi\b|apis|django|flask|fastapi|servidor"},
    "bd": {"nombre": "Bases de datos", "patron": r"mongo|\bsql\b|mysql|postgres|bases? de datos|nosql"},
    "git": {"nombre": "Git y GitHub", "patron": r"\bgit\b|github|gitlab|control de versiones"},
    "devops": {"nombre": "DevOps", "patron": r"docker|devops|kubernetes|ci/cd|despliegue|linux|nube|cloud|aws|azure"},
    "java": {"nombre": "Java", "patron": r"\bjava\b(?!script)"},
    "seguridad": {"nombre": "Ciberseguridad", "patron": r"seguridad|ciberseguridad|hacking|redes"},
}

# Tema terminado -> [(tema siguiente, por qué conviene)]
RUTAS = {
    "cpp": [
        ("iot", "Ya dominas C++, el lenguaje con el que se programan los Arduino: en «{curso}» aprenderás a configurar uno y conectar sensores."),
        ("robotica", "Con C++ puedes controlar motores y sensores: «{curso}» es el siguiente paso para llevarlo a la robótica."),
    ],
    "c": [
        ("cpp", "Ya conoces C; «{curso}» te enseña la programación orientada a objetos sobre la misma base."),
        ("iot", "Con C puedes programar microcontroladores: en «{curso}» lo aplicarás a un Arduino."),
    ],
    "iot": [
        ("robotica", "Ya sabes conectar sensores y placas; en «{curso}» harás que se muevan."),
        ("backend", "Tus dispositivos pueden mandar datos a internet: en «{curso}» aprenderás a crear la API que los recibe."),
    ],
    "python": [
        ("datos", "Ya sabes Python, el lenguaje más usado para analizar datos: «{curso}» es tu siguiente paso."),
        ("ia", "Con Python puedes entrenar tus primeros modelos de inteligencia artificial en «{curso}»."),
        ("backend", "Usa tu Python para crear APIs y servidores web en «{curso}»."),
    ],
    "datos": [
        ("ia", "Ya sabes analizar datos; en «{curso}» harás que una computadora aprenda de ellos."),
    ],
    "web_basico": [
        ("react", "Ya dominas HTML, CSS y JavaScript: con «{curso}» harás interfaces modernas y rápidas."),
        ("backend", "Ya haces la parte visual; en «{curso}» aprenderás el servidor para tener una app completa."),
    ],
    "react": [
        ("movil", "Con lo que sabes de React puedes crear apps para celular en «{curso}»."),
        ("backend", "Completa tus proyectos de React con tu propio servidor en «{curso}»."),
    ],
    "backend": [
        ("bd", "Toda API necesita guardar información: en «{curso}» aprenderás a diseñar la base de datos."),
        ("devops", "Ya tienes tu servidor; en «{curso}» aprenderás a publicarlo en internet."),
    ],
    "bd": [
        ("backend", "Ya sabes guardar datos; en «{curso}» crearás la API que los usa."),
        ("datos", "Con tus bases de datos puedes sacar conclusiones en «{curso}»."),
    ],
    "git": [
        ("devops", "Ya trabajas en equipo con Git; en «{curso}» automatizarás pruebas y despliegues."),
        ("web_basico", "Pon a prueba tu flujo con Git en un proyecto real con «{curso}»."),
        ("python", "Pon a prueba tu flujo con Git en un proyecto real con «{curso}»."),
    ],
    "java": [
        ("movil", "Con Java puedes crear apps Android en «{curso}»."),
        ("backend", "Usa Java para crear servidores y APIs en «{curso}»."),
    ],
    "movil": [("backend", "Tus apps necesitan un servidor: créalo en «{curso}».")],
    "ia": [("devops", "Aprende a poner tus modelos en producción con «{curso}».")],
    "devops": [("seguridad", "Protege los sistemas que despliegas con «{curso}».")],
    "robotica": [("ia", "Dale inteligencia a tus robots con «{curso}».")],
}


def _texto_curso(curso):
    return f"{curso.get('nombre', '')} {curso.get('descripcion', '')}".lower()


def temas_de_curso(curso):
    """Temas que trata un curso, ordenados por cuánto aparecen en su nombre."""
    nombre = (curso.get("nombre") or "").lower()
    texto = _texto_curso(curso)
    encontrados = []
    for clave, tema in TEMAS.items():
        if re.search(tema["patron"], nombre):
            encontrados.append((0, clave))
        elif re.search(tema["patron"], texto):
            encontrados.append((1, clave))
    encontrados.sort()
    return [clave for _, clave in encontrados]


def recomendar_cursos(cursos_base, cursos_inscritos_ids, catalogo, limite=4):
    """
    Recomienda cursos del catálogo según los cursos base (los que el alumno terminó
    o está por terminar). Devuelve el curso, de qué curso viene y por qué.
    """
    recomendaciones = []
    usados = set(cursos_inscritos_ids)

    for curso_base in cursos_base:
        for tema_base in temas_de_curso(curso_base):
            for tema_siguiente, razon in RUTAS.get(tema_base, []):
                patron = TEMAS[tema_siguiente]["patron"]
                candidatos = [
                    c for c in catalogo
                    if str(c["_id"]) not in usados and re.search(patron, _texto_curso(c))
                ]
                # Primero los que lo mencionan en el nombre
                candidatos.sort(key=lambda c: 0 if re.search(patron, (c.get("nombre") or "").lower()) else 1)
                for c in candidatos[:1]:
                    usados.add(str(c["_id"]))
                    recomendaciones.append({
                        "curso_id": str(c["_id"]),
                        "nombre": c.get("nombre", "Curso"),
                        "descripcion": c.get("descripcion", ""),
                        "imagen": _imagen_curso(c),
                        "precio": float(c.get("precio") or 0),
                        "basado_en": curso_base.get("nombre", ""),
                        "tema": TEMAS[tema_siguiente]["nombre"],
                        "razon": razon.format(curso=c.get("nombre", "este curso")),
                    })
                if len(recomendaciones) >= limite:
                    return recomendaciones

    # Respaldo: cursos que tomaron otros alumnos de los mismos cursos
    if len(recomendaciones) < limite and cursos_base:
        ids_base = [str(c["_id"]) for c in cursos_base]
        variantes = [v for i in ids_base for v in _variantes_id(i)]
        companeros = {str(i.get("alumno_id")) for i in inscripciones_collection.find({"curso_id": {"$in": variantes}})}
        conteo = Counter()
        if companeros:
            variantes_alumnos = [v for a in companeros for v in _variantes_id(a)]
            for ins in inscripciones_collection.find({"alumno_id": {"$in": variantes_alumnos}}):
                cid = str(ins.get("curso_id"))
                if cid not in usados:
                    conteo[cid] += 1
        por_id = {str(c["_id"]): c for c in catalogo}
        for cid, _ in conteo.most_common():
            c = por_id.get(cid)
            if not c:
                continue
            usados.add(cid)
            recomendaciones.append({
                "curso_id": cid,
                "nombre": c.get("nombre", "Curso"),
                "descripcion": c.get("descripcion", ""),
                "imagen": _imagen_curso(c),
                "precio": float(c.get("precio") or 0),
                "basado_en": cursos_base[0].get("nombre", ""),
                "tema": "Popular",
                "razon": f"Otros alumnos que tomaron «{cursos_base[0].get('nombre', '')}» también tomaron este curso.",
            })
            if len(recomendaciones) >= limite:
                break

    return recomendaciones


# ======================================================================
# Cálculo del progreso de un alumno en un curso
# ======================================================================

def _datos_curso(curso):
    """Lecciones, exámenes y niveles de un curso (se reutiliza para varios alumnos)."""
    variantes = _variantes_id(curso["_id"])
    niveles = {str(n["_id"]): n.get("titulo", "Nivel") for n in niveles_collection.find({"curso_id": {"$in": variantes}})}
    lecciones = list(lecciones_collection.find({"curso_id": {"$in": variantes}}))
    examenes = list(examenes_collection.find({"curso_id": {"$in": variantes}}))
    return {"curso": curso, "niveles": niveles, "lecciones": lecciones, "examenes": examenes}


def calcular_progreso(alumno_id, datos, inscripcion=None):
    curso = datos["curso"]
    lecciones = datos["lecciones"]
    examenes = datos["examenes"]
    alumno_vars = _variantes_id(alumno_id)
    curso_vars = _variantes_id(curso["_id"])

    examenes_por_id = {str(e["_id"]): e for e in examenes}
    ids_examenes = [v for e in examenes for v in _variantes_id(e["_id"])]

    respuestas = list(respuestas_collection.find({
        "alumno_id": {"$in": alumno_vars},
        "examen_id": {"$in": ids_examenes},
    })) if ids_examenes else []

    vistas = list(lecciones_vistas_collection.find({
        "alumno_id": {"$in": alumno_vars},
        "curso_id": {"$in": curso_vars},
    }))

    # ---- Exámenes: mejor intento de cada uno ----
    por_examen = {}
    for r in respuestas:
        eid = str(r.get("examen_id"))
        cal = float(r.get("calificacion") or 0)
        fecha = _a_fecha(r.get("fecha")) or _a_fecha(r["_id"])
        info = por_examen.setdefault(eid, {"mejor": cal, "ultima": cal, "fecha": fecha, "intentos": 0})
        info["intentos"] += 1
        info["mejor"] = max(info["mejor"], cal)
        if fecha and (info["fecha"] is None or fecha >= info["fecha"]):
            info["fecha"], info["ultima"] = fecha, cal

    calificaciones = []
    for e in examenes:
        eid = str(e["_id"])
        info = por_examen.get(eid)
        calificaciones.append({
            "examen_id": eid,
            "titulo": e.get("titulo", "Examen"),
            "nivel": datos["niveles"].get(str(e.get("nivel_id")), ""),
            "calificacion": round(info["mejor"], 1) if info else None,
            "intentos": info["intentos"] if info else 0,
            "fecha": _iso(info["fecha"]) if info else None,
            "aprobado": bool(info and info["mejor"] >= CALIFICACION_APROBATORIA),
        })

    presentados = [c for c in calificaciones if c["calificacion"] is not None]
    promedio = round(sum(c["calificacion"] for c in presentados) / len(presentados), 1) if presentados else None
    reprobados = [c for c in presentados if not c["aprobado"]]

    # ---- Lecciones ----
    lecciones_vistas = {str(v.get("leccion_id")) for v in vistas}
    for eid in por_examen:
        leccion = examenes_por_id.get(eid, {}).get("leccion_id")
        if leccion:
            lecciones_vistas.add(str(leccion))
    ids_lecciones = {str(l["_id"]) for l in lecciones}
    lecciones_vistas &= ids_lecciones if ids_lecciones else lecciones_vistas

    total_lecciones, total_examenes = len(lecciones), len(examenes)
    total_items = total_lecciones + total_examenes
    hechos = len(lecciones_vistas) + len(presentados)
    progreso = round(hechos / total_items * 100, 1) if total_items else 0.0

    siguiente_leccion = next(
        (l.get("titulo", "Lección") for l in lecciones if str(l["_id"]) not in lecciones_vistas), None
    )
    siguiente_examen = next((c["titulo"] for c in calificaciones if c["calificacion"] is None), None)

    # ---- Última actividad ----
    fechas = [_a_fecha(v.get("fecha_vista")) for v in vistas] + [i["fecha"] for i in por_examen.values()]
    fechas = [f for f in fechas if f]
    inicio = None
    if inscripcion:
        inicio = _a_fecha(inscripcion.get("fecha_validacion")) or _a_fecha(inscripcion.get("fecha_inscripcion")) or _a_fecha(inscripcion.get("_id"))
    ultima = max(fechas) if fechas else inicio
    dias_inactivo = (_ahora() - ultima).days if ultima else None

    terminado = total_items > 0 and hechos >= total_items
    terminado_aprobado = terminado and promedio is not None and promedio >= CALIFICACION_APROBATORIA

    # ---- Riesgos ----
    riesgo_reprobar = None
    if promedio is not None and promedio < CALIFICACION_APROBATORIA:
        riesgo_reprobar = "alto" if promedio < 50 else "medio"
    elif reprobados:
        riesgo_reprobar = "bajo"

    riesgo_abandono = None
    if not terminado and dias_inactivo is not None and dias_inactivo > DIAS_ABANDONO:
        riesgo_abandono = "alto" if dias_inactivo > DIAS_ABANDONO * 3 else "medio"

    return {
        "curso_id": str(curso["_id"]),
        "curso": curso.get("nombre", "Curso"),
        "imagen": _imagen_curso(curso),
        "progreso": progreso,
        "lecciones_vistas": len(lecciones_vistas),
        "total_lecciones": total_lecciones,
        "examenes_presentados": len(presentados),
        "total_examenes": total_examenes,
        "promedio": promedio,
        "nivel": nivel_desempeno(promedio),
        "calificaciones": calificaciones,
        "examenes_reprobados": [c["titulo"] for c in reprobados],
        "siguiente_leccion": siguiente_leccion,
        "siguiente_examen": siguiente_examen,
        "ultima_actividad": _iso(ultima),
        "dias_inactivo": dias_inactivo,
        "terminado": terminado,
        "terminado_aprobado": terminado_aprobado,
        "riesgo_reprobar": riesgo_reprobar,
        "riesgo_abandono": riesgo_abandono,
        "en_riesgo": bool(riesgo_reprobar in ("medio", "alto") or riesgo_abandono),
    }


# ======================================================================
# Consejos en lenguaje sencillo
# ======================================================================

def consejos_para_alumno(p):
    consejos = []
    if p["riesgo_reprobar"] in ("medio", "alto"):
        peor = min((c for c in p["calificaciones"] if c["calificacion"] is not None), key=lambda c: c["calificacion"])
        consejos.append(
            f"Tu promedio en {p['curso']} es {p['promedio']}%, debajo del {CALIFICACION_APROBATORIA}% para aprobar. "
            f"Repasa las lecciones de «{peor['titulo']}» ({peor['calificacion']}%) y vuelve a presentarlo."
        )
        consejos.append("Escríbele a tu profesor si hay un tema que no te quedó claro; pedir ayuda a tiempo hace la diferencia.")
    elif p["riesgo_reprobar"] == "bajo":
        consejos.append(f"Vas aprobando, pero reprobaste {', '.join('«' + t + '»' for t in p['examenes_reprobados'])}. Repásalo para asegurar el curso.")

    if p["riesgo_abandono"]:
        siguiente = p["siguiente_leccion"] or p["siguiente_examen"]
        texto = f"Llevas {p['dias_inactivo']} días sin avanzar en {p['curso']}."
        if siguiente:
            texto += f" Retómalo hoy con «{siguiente}»: con 20 minutos al día terminas más rápido de lo que crees."
        consejos.append(texto)
    elif not p["terminado"]:
        faltan_l = p["total_lecciones"] - p["lecciones_vistas"]
        faltan_e = p["total_examenes"] - p["examenes_presentados"]
        partes = []
        if faltan_l > 0:
            partes.append(f"{faltan_l} {'lección' if faltan_l == 1 else 'lecciones'}")
        if faltan_e > 0:
            partes.append(f"{faltan_e} {'examen' if faltan_e == 1 else 'exámenes'}")
        if partes:
            sig = f" Sigue con «{p['siguiente_leccion']}»." if p["siguiente_leccion"] else ""
            consejos.append(f"Te faltan {' y '.join(partes)} para terminar.{sig}")

    if p["terminado_aprobado"]:
        consejos.append(f"¡Terminaste {p['curso']} con {p['promedio']}%! Revisa los cursos recomendados para seguir aprendiendo.")
    elif p["terminado"] and p["promedio"] is not None:
        consejos.append("Ya presentaste todo, pero tu promedio no alcanza para aprobar. Repite los exámenes reprobados.")

    if not consejos and p["promedio"] is not None and p["promedio"] >= 90:
        consejos.append("¡Excelente ritmo! Sigue así.")
    return consejos


def recomendaciones_para_profesor(p, alumno):
    nombre = alumno["nombre"].split(" ")[0]
    acciones = []

    if p["riesgo_reprobar"] in ("medio", "alto"):
        peores = sorted((c for c in p["calificaciones"] if c["calificacion"] is not None), key=lambda c: c["calificacion"])[:2]
        temas = " y ".join(f"«{c['titulo']}» ({c['calificacion']}%)" for c in peores)
        acciones.append(f"Agenda una asesoría breve con {nombre} para repasar {temas}.")
        acciones.append("Compártele material de refuerzo (un video corto o ejercicios resueltos) de esos temas.")
        if any(c["intentos"] <= 1 for c in peores):
            acciones.append("Permítele un nuevo intento del examen después de repasar.")
        if p["riesgo_reprobar"] == "alto":
            acciones.append("Riesgo alto: revisa si tiene las bases del curso o si necesita empezar por un nivel anterior.")

    if p["riesgo_abandono"]:
        dias = p["dias_inactivo"]
        contacto = f" ({alumno['email']})" if alumno.get("email") else ""
        if p["progreso"] == 0:
            acciones.append(f"{nombre} se inscribió hace {dias} días y no ha empezado. Envíale un mensaje de bienvenida{contacto} con la primera lección.")
        else:
            acciones.append(f"Envíale un mensaje{contacto}: lleva {dias} días sin entrar. Pregúntale si tiene algún problema con el curso.")
            if p["siguiente_leccion"]:
                acciones.append(f"Recuérdale que va en {p['progreso']}% y que lo siguiente es «{p['siguiente_leccion']}».")
        if p["riesgo_reprobar"] in ("medio", "alto"):
            acciones.append("Las calificaciones bajas pueden estar afectando su motivación: al contactarle, reconoce lo que sí ha logrado.")

    return acciones


# ======================================================================
# Endpoints
# ======================================================================

def progreso_alumno(alumno_id):
    try:
        inscripciones = [
            i for i in inscripciones_collection.find({"alumno_id": {"$in": _variantes_id(alumno_id)}})
            if i.get("estado", "aceptada") == "aceptada"
        ]
        catalogo = list(cursos_collection.find({}))
        cursos_por_id = {str(c["_id"]): c for c in catalogo}

        cursos = []
        vistos = set()
        for ins in inscripciones:
            cid = str(ins.get("curso_id"))
            curso = cursos_por_id.get(cid)
            if not curso or cid in vistos:
                continue
            vistos.add(cid)
            p = calcular_progreso(alumno_id, _datos_curso(curso), ins)
            profesor = None
            try:
                profesor = usuarios_collection.find_one({"_id": ObjectId(str(curso.get("profesor")))})
            except Exception:
                pass
            p["profesor"] = _nombre_usuario(profesor) if profesor else ""
            p["consejos"] = consejos_para_alumno(p)
            cursos.append(p)

        cursos.sort(key=lambda c: (not c["en_riesgo"], c["terminado"], -c["progreso"]))

        # Recomendaciones: primero por cursos terminados; si no hay, por los más avanzados
        terminados = [cursos_por_id[c["curso_id"]] for c in cursos if c["terminado"]]
        base = terminados or [cursos_por_id[c["curso_id"]] for c in sorted(cursos, key=lambda c: -c["progreso"])]
        recomendados = recomendar_cursos(base, vistos, catalogo)
        for r in recomendados:
            r["motivo"] = "terminado" if terminados else "en_curso"

        evaluados = [c["promedio"] for c in cursos if c["promedio"] is not None]
        promedio_general = round(sum(evaluados) / len(evaluados), 1) if evaluados else None
        progreso_general = round(sum(c["progreso"] for c in cursos) / len(cursos), 1) if cursos else 0

        return {
            "resumen": {
                "cursos": len(cursos),
                "terminados": sum(1 for c in cursos if c["terminado"]),
                "en_riesgo": sum(1 for c in cursos if c["en_riesgo"]),
                "progreso_general": progreso_general,
                "promedio_general": promedio_general,
                "nivel_general": nivel_desempeno(promedio_general),
                "calificacion_aprobatoria": CALIFICACION_APROBATORIA,
                "dias_abandono": DIAS_ABANDONO,
            },
            "cursos": cursos,
            "recomendados": recomendados,
        }
    except Exception as e:
        return {"error": str(e)}


def alumnos_en_riesgo_profesor(profesor_id, incluir_todos=False):
    try:
        cursos = list(cursos_collection.find({"profesor": {"$in": _variantes_id(profesor_id)}}))
        alumnos = []
        resumen_cursos = []

        for curso in cursos:
            datos = _datos_curso(curso)
            inscritos = [
                i for i in inscripciones_collection.find({"curso_id": {"$in": _variantes_id(curso["_id"])}})
                if i.get("estado", "aceptada") == "aceptada"
            ]
            en_riesgo_curso = 0
            for ins in inscritos:
                aid = str(ins.get("alumno_id"))
                usuario = None
                try:
                    usuario = usuarios_collection.find_one({"_id": ObjectId(aid)})
                except Exception:
                    pass
                alumno = {"id": aid, "nombre": _nombre_usuario(usuario), "email": (usuario or {}).get("email", "")}
                p = calcular_progreso(aid, datos, ins)
                if p["en_riesgo"]:
                    en_riesgo_curso += 1
                if not (p["en_riesgo"] or incluir_todos):
                    continue
                motivos = []
                if p["riesgo_reprobar"] in ("medio", "alto"):
                    motivos.append("reprobar")
                if p["riesgo_abandono"]:
                    motivos.append("abandono")
                gravedad = "alta" if "alto" in (p["riesgo_reprobar"], p["riesgo_abandono"]) or len(motivos) == 2 else "media"
                alumnos.append({
                    "alumno": alumno,
                    "curso_id": p["curso_id"],
                    "curso": p["curso"],
                    "progreso": p["progreso"],
                    "promedio": p["promedio"],
                    "nivel": p["nivel"],
                    "dias_inactivo": p["dias_inactivo"],
                    "ultima_actividad": p["ultima_actividad"],
                    "examenes_reprobados": p["examenes_reprobados"],
                    "calificaciones": p["calificaciones"],
                    "motivos": motivos,
                    "gravedad": gravedad if motivos else "ninguna",
                    "recomendaciones": recomendaciones_para_profesor(p, alumno),
                })
            resumen_cursos.append({
                "curso_id": str(curso["_id"]),
                "curso": curso.get("nombre", "Curso"),
                "inscritos": len(inscritos),
                "en_riesgo": en_riesgo_curso,
            })

        orden = {"alta": 0, "media": 1, "ninguna": 2}
        alumnos.sort(key=lambda a: (orden[a["gravedad"]], -(a["dias_inactivo"] or 0)))

        return {
            "criterios": {"calificacion_aprobatoria": CALIFICACION_APROBATORIA, "dias_abandono": DIAS_ABANDONO},
            "resumen": {
                "alumnos_en_riesgo": len({(a["alumno"]["id"]) for a in alumnos if a["motivos"]}),
                "riesgo_reprobar": sum(1 for a in alumnos if "reprobar" in a["motivos"]),
                "riesgo_abandono": sum(1 for a in alumnos if "abandono" in a["motivos"]),
                "cursos": resumen_cursos,
            },
            "alumnos": alumnos,
        }
    except Exception as e:
        return {"error": str(e)}
