from config.config import respuestas_collection, usuarios_collection, inscripciones_collection, examenes_collection
from bson.objectid import ObjectId
from datetime import datetime

def segmentar_estudiantes_curso(curso_id):
    grupos = {
        "Grupo A (Destacados)": [],
        "Grupo B (Regulares)": [],
        "Grupo C (Riesgo Académico)": []
    }
    
    hoy = datetime.utcnow()
    
    try:
        c_id = ObjectId(curso_id)
    except:
        return {"error": "ID de curso inválido"}

    curso_keys = [str(curso_id), c_id]
    query_curso = {"curso_id": {"$in": curso_keys}}

    # Obtener info base del curso
    examenes_curso = list(examenes_collection.find(query_curso))
    total_examenes = len(examenes_curso)
    examenes_ids = [e["_id"] for e in examenes_curso] + [str(e["_id"]) for e in examenes_curso]

    inscripciones = list(inscripciones_collection.find(query_curso))

    for inscripcion in inscripciones:
        alumno_id_raw = inscripcion.get("alumno_id")
        alumno = usuarios_collection.find_one({"_id": ObjectId(alumno_id_raw)})
        
        if not alumno: continue

        # Metricas del alumno
        alumno_keys = [str(alumno_id_raw), ObjectId(alumno_id_raw)]
        respuestas = list(respuestas_collection.find({
            "alumno_id": {"$in": alumno_keys},
            "examen_id": {"$in": examenes_ids}
        }))

        num_intentos = len(respuestas)
        promedio = sum([r.get("calificacion", 0) for r in respuestas]) / num_intentos if num_intentos > 0 else 0
        examenes_completados = len(set([str(r.get("examen_id")) for r in respuestas]))
        progreso = (examenes_completados / total_examenes * 100) if total_examenes > 0 else 0

        # Calculo de inactividad
        dias_inactivo = 999
        ultima_rta = respuestas_collection.find_one({
            "alumno_id": {"$in": alumno_keys},
            "examen_id": {"$in": examenes_ids}
        }, sort=[("_id", -1)])
        
        if ultima_rta:
            fecha_act = ultima_rta.get("fecha") or ultima_rta["_id"].generation_time
            if isinstance(fecha_act, str):
                try: fecha_act = datetime.fromisoformat(fecha_act.replace("Z", "+00:00")).replace(tzinfo=None)
                except: fecha_act = None
            elif hasattr(fecha_act, 'tzinfo') and fecha_act.tzinfo:
                fecha_act = fecha_act.replace(tzinfo=None)
            
            if fecha_act: dias_inactivo = (hoy - fecha_act).days

        perfil = {
            "alumno": f"{alumno.get('nombre')} {alumno.get('apellidop')}",
            "email": alumno.get("email"),
            "progreso": f"{progreso:.1f}%",
            "promedio": f"{promedio:.1f}",
            "dias_inactivo": dias_inactivo
        }

        # --- Lógica de Clasificación ---
        
        # GRUPO C: Riesgo (Inactividad > 10, o mal rendimiento con poco progreso)
        if dias_inactivo > 10 or (num_intentos > 0 and promedio < 70 and progreso < 50) or (num_intentos == 0):
            motivo = "Inactividad" if dias_inactivo > 10 else "Bajo rendimiento"
            if num_intentos == 0: motivo = "Sin inicio de actividades"
            
            perfil["motivo"] = motivo
            # Medidas para evitar deserción
            if "Inactividad" in motivo or "Sin inicio" in motivo:
                perfil["medidas_sugeridas"] = [
                    "Enviar correo automático de motivación.",
                    "Notificación push: 'Te extrañamos, ¡continúa donde te quedaste!'.",
                    "Llamada de seguimiento por parte de soporte técnico."
                ]
            else:
                perfil["medidas_sugeridas"] = [
                    "Ofrecer sesión de asesoría 1 a 1.",
                    "Sugerir revisión de lecciones con menor aprobación del curso.",
                    "Desbloquear material de refuerzo simplificado."
                ]
            grupos["Grupo C (Riesgo Académico)"].append(perfil)

        # GRUPO A: Destacados (Promedio alto, progreso constante y activo)
        elif promedio >= 85 and progreso >= 60 and dias_inactivo <= 3:
            perfil["reconocimiento"] = "Candidato a monitor o certificado de excelencia."
            grupos["Grupo A (Destacados)"].append(perfil)

        # GRUPO B: Regulares (El resto)
        else:
            perfil["recomendacion"] = "Mantener el ritmo actual."
            grupos["Grupo B (Regulares)"].append(perfil)

    return grupos