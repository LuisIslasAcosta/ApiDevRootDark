from config.config import inscripciones_collection, cursos_collection, examenes_collection, respuestas_collection, niveles_collection, lecciones_collection, lecciones_vistas_collection
from bson.objectid import ObjectId
from datetime import datetime, timedelta

def analizar_progreso_curso(curso_id):
    try:
        c_id = ObjectId(curso_id)
    except:
        return {"error": "ID de curso inválido"}

    try:
        curso_keys = [str(curso_id), c_id]
        query_curso = {"curso_id": {"$in": curso_keys}}

        # 1. Obtener todos los exámenes del curso
        all_examenes_curso = list(examenes_collection.find(query_curso))
        total_examenes_curso = len(all_examenes_curso)
        all_examenes_ids_str = {str(e["_id"]) for e in all_examenes_curso}

        if total_examenes_curso == 0:
            return {"mensaje": "El curso no tiene exámenes para analizar el progreso.", "analisis": {}}

        # 2. Obtener todas las inscripciones para este curso
        inscripciones = list(inscripciones_collection.find(query_curso))
        total_alumnos_inscritos = len(inscripciones)

        if total_alumnos_inscritos == 0:
            return {"mensaje": "No hay alumnos inscritos en este curso.", "analisis": {}}

        # Inicializar contadores
        completados_count = 0
        abandonados_count = 0
        en_progreso_count = 0
        suma_progresos_porcentual = 0

        # Para duración por módulo
        niveles_curso = list(niveles_collection.find(query_curso))
        niveles_data = {} # {nivel_id: {titulo: "", examenes_ids: set(), duraciones: []}}

        for nivel in niveles_curso:
            nivel_id_str = str(nivel["_id"])
            lecciones_nivel = list(lecciones_collection.find({"nivel_id": nivel_id_str}))
            lecciones_ids_str = {str(l["_id"]) for l in lecciones_nivel}

            examenes_nivel = [e for e in all_examenes_curso if str(e.get("leccion_id")) in lecciones_ids_str]
            examenes_nivel_ids_str = {str(e["_id"]) for e in examenes_nivel}

            if examenes_nivel_ids_str: # Solo si el nivel tiene exámenes
                niveles_data[nivel_id_str] = {
                    "titulo": nivel.get("titulo", "Nivel sin título"),
                    "examenes_ids": examenes_nivel_ids_str,
                    "duraciones": [] # Para almacenar las duraciones de cada alumno en este nivel
                }

        # 3. Analizar el progreso de cada alumno
        hoy = datetime.utcnow()
        for inscripcion in inscripciones:
            alumno_id = inscripcion["alumno_id"]
            alumno_keys = [str(alumno_id), ObjectId(alumno_id)]

            # Obtener todas las respuestas del alumno para los exámenes de este curso
            respuestas_alumno_curso = list(respuestas_collection.find({
                "alumno_id": {"$in": alumno_keys},
                "examen_id": {"$in": list(all_examenes_ids_str)} # Convertir set a list para $in
            }))

            examenes_respondidos_ids = {str(r["examen_id"]) for r in respuestas_alumno_curso}
            num_examenes_respondidos = len(examenes_respondidos_ids)

            # Calcular progreso
            progreso_porcentaje = (num_examenes_respondidos / total_examenes_curso * 100) if total_examenes_curso > 0 else 0
            suma_progresos_porcentual += progreso_porcentaje

            # Determinar última actividad
            ultima_actividad = None
            if respuestas_alumno_curso:
                # Ordenar por _id (que contiene el timestamp) para encontrar la última respuesta
                ultima_respuesta = max(respuestas_alumno_curso, key=lambda x: x["_id"].generation_time)
                ultima_actividad = ultima_respuesta["_id"].generation_time.replace(tzinfo=None) # Normalizar a naive UTC

            dias_inactivo = (hoy - ultima_actividad).days if ultima_actividad else (hoy - inscripcion["_id"].generation_time.replace(tzinfo=None)).days # Si no hay respuestas, usar fecha de inscripción

            # Criterios de finalización y abandono
            if progreso_porcentaje >= 90: # Considerar completado si ha respondido al 90% o más de los exámenes
                completados_count += 1
            elif progreso_porcentaje < 20 and dias_inactivo > 30: # Considerar abandonado si bajo progreso y mucha inactividad
                abandonados_count += 1
            else:
                en_progreso_count += 1

            # Calcular duración por nivel para este alumno
            for nivel_id, nivel_info in niveles_data.items():
                examenes_nivel_ids = nivel_info["examenes_ids"]
                
                # Respuestas del alumno para los exámenes de este nivel
                respuestas_alumno_nivel = [
                    r for r in respuestas_alumno_curso if str(r["examen_id"]) in examenes_nivel_ids
                ]

                if respuestas_alumno_nivel:
                    primera_actividad_nivel = min(respuestas_alumno_nivel, key=lambda x: x["_id"].generation_time)["_id"].generation_time.replace(tzinfo=None)
                    ultima_actividad_nivel = max(respuestas_alumno_nivel, key=lambda x: x["_id"].generation_time)["_id"].generation_time.replace(tzinfo=None)
                    
                    duracion_nivel = (ultima_actividad_nivel - primera_actividad_nivel).total_seconds() / 3600 # Duración en horas
                    if duracion_nivel >= 0: # Asegurarse de que la duración no sea negativa (aunque no debería)
                        nivel_info["duraciones"].append(duracion_nivel)

        # 4. Calcular tasas
        tasa_finalizacion = (completados_count / total_alumnos_inscritos * 100) if total_alumnos_inscritos > 0 else 0
        tasa_abandono = (abandonados_count / total_alumnos_inscritos * 100) if total_alumnos_inscritos > 0 else 0
        promedio_avance_alumnos = (suma_progresos_porcentual / total_alumnos_inscritos) if total_alumnos_inscritos > 0 else 0

        # 5. Calcular duración promedio por módulo (nivel)
        duracion_promedio_por_nivel = []
        for nivel_id, nivel_info in niveles_data.items():
            if nivel_info["duraciones"]:
                avg_duration_hours = sum(nivel_info["duraciones"]) / len(nivel_info["duraciones"])
                duracion_promedio_por_nivel.append({
                    "nivel_id": nivel_id,
                    "titulo": nivel_info["titulo"],
                    "duracion_promedio_horas": round(avg_duration_hours, 2)
                })
            else:
                duracion_promedio_por_nivel.append({
                    "nivel_id": nivel_id,
                    "titulo": nivel_info["titulo"],
                    "duracion_promedio_horas": "No hay datos de actividad"
                })

        return {
            "curso_id": curso_id,
            "total_alumnos_inscritos": total_alumnos_inscritos,
            "alumnos_completados": completados_count,
            "alumnos_abandonados": abandonados_count,
            "alumnos_en_progreso": en_progreso_count,
            "tasa_finalizacion": round(tasa_finalizacion, 2),
            "tasa_abandono": round(tasa_abandono, 2),
            "avance_promedio_general": round(promedio_avance_alumnos, 2),
            "duracion_promedio_por_nivel": duracion_promedio_por_nivel
        }
    except Exception as e:
        return {"error": str(e)}

def obtener_cursos_por_tasa_finalizacion(limit=5):
    """
    Obtiene los cursos con la mayor tasa de finalización.
    Requiere iterar sobre todos los cursos y calcular sus tasas.
    """
    cursos_con_tasas = []
    all_cursos = list(cursos_collection.find({}))

    for curso in all_cursos:
        curso_id = str(curso["_id"])
        resultado_analisis = analizar_progreso_curso(curso_id)
        # Asegurarse de que el resultado no sea un error y contenga datos de análisis
        if "error" not in resultado_analisis and "analisis" not in resultado_analisis: 
            tasa = resultado_analisis.get("tasa_finalizacion", 0)
            cursos_con_tasas.append({
                "curso_id": curso_id,
                "nombre_curso": curso.get("nombre", "Curso sin nombre"),
                "tasa_finalizacion": tasa
            })
    
    cursos_con_tasas.sort(key=lambda x: x["tasa_finalizacion"], reverse=True)
    return cursos_con_tasas[:limit]

def obtener_cursos_por_tasa_abandono(limit=5):
    """
    Obtiene los cursos con la mayor tasa de abandono.
    Requiere iterar sobre todos los cursos y calcular sus tasas.
    """
    cursos_con_tasas = []
    all_cursos = list(cursos_collection.find({}))

    for curso in all_cursos:
        curso_id = str(curso["_id"])
        resultado_analisis = analizar_progreso_curso(curso_id)
        # Asegurarse de que el resultado no sea un error y contenga datos de análisis
        if "error" not in resultado_analisis and "analisis" not in resultado_analisis:
            tasa = resultado_analisis.get("tasa_abandono", 0)
            cursos_con_tasas.append({
                "curso_id": curso_id,
                "nombre_curso": curso.get("nombre", "Curso sin nombre"),
                "tasa_abandono": tasa
            })
    
    cursos_con_tasas.sort(key=lambda x: x["tasa_abandono"], reverse=True)
    return cursos_con_tasas[:limit]

def marcar_leccion_como_vista(alumno_id, leccion_id, curso_id):
    """
    Registra que un alumno ha visto una lección específica.
    """
    try:
        lecciones_vistas_collection.update_one(
            {"alumno_id": alumno_id, "leccion_id": leccion_id},
            {"$set": {
                "alumno_id": alumno_id,
                "leccion_id": leccion_id,
                "curso_id": curso_id,
                "fecha_vista": datetime.utcnow()
            }},
            upsert=True
        )
        return {"mensaje": "Lección marcada como vista con éxito"}
    except Exception as e:
        return {"error": str(e)}

def obtener_progreso_estudiante(alumno_id, curso_id):
    """
    Calcula el progreso individual de un alumno en un curso específico
    basado en lecciones cubiertas y exámenes realizados.
    """
    try:
        c_id = ObjectId(curso_id)
        a_id = ObjectId(alumno_id)
        
        query_curso = {"curso_id": {"$in": [str(curso_id), c_id]}}
        alumno_keys = [str(alumno_id), a_id]

        # 1. Obtener totales del curso
        lecciones_curso = list(lecciones_collection.find(query_curso))
        total_lecciones = len(lecciones_curso)
        examenes_curso = list(examenes_collection.find(query_curso))
        total_examenes = len(examenes_curso)
        
        examenes_ids = [str(e["_id"]) for e in examenes_curso] + [e["_id"] for e in examenes_curso]

        # 2. Obtener lo que el alumno ha hecho (Exámenes)
        respuestas_alumno = list(respuestas_collection.find({
            "alumno_id": {"$in": alumno_keys},
            "examen_id": {"$in": examenes_ids}
        }))
        examenes_completados_ids = {str(r["examen_id"]) for r in respuestas_alumno}
        num_examenes_hechos = len(examenes_completados_ids)

        # 3. Obtener lecciones vistas realmente (Tracking directo)
        vistas_alumno = list(lecciones_vistas_collection.find({
            "alumno_id": {"$in": alumno_keys},
            "curso_id": {"$in": [str(curso_id), c_id]}
        }))
        lecciones_vistas_ids = {str(v["leccion_id"]) for v in vistas_alumno}
        
        # Respaldo: si hizo el examen de una lección, también la contamos como vista
        for ex in examenes_curso:
            if str(ex["_id"]) in examenes_completados_ids and ex.get("leccion_id"):
                lecciones_vistas_ids.add(str(ex["leccion_id"]))
        
        num_lecciones_vistas = len(lecciones_vistas_ids)

        # 4. Cálculo de porcentajes para la BARRA DE PROGRESO
        progreso_examenes = (num_examenes_hechos / total_examenes * 100) if total_examenes > 0 else 0
        progreso_lecciones = (num_lecciones_vistas / total_lecciones * 100) if total_lecciones > 0 else 0
        
        total_items = total_lecciones + total_examenes
        items_completados = num_lecciones_vistas + num_examenes_hechos
        progreso_global = (items_completados / total_items * 100) if total_items > 0 else 0

        return {
            "curso_id": curso_id,
            "alumno_id": alumno_id,
            "resumen": {
                "progreso_global": round(progreso_global, 2), # <--- ESTE VALOR VA A LA BARRA
                "lecciones_completadas": f"{num_lecciones_vistas}/{total_lecciones}",
                "examenes_realizados": f"{num_examenes_hechos}/{total_examenes}",
                "porcentaje_lecciones": round(progreso_lecciones, 2),
                "porcentaje_examenes": round(progreso_examenes, 2)
            }
        }
    except Exception as e:
        return {"error": str(e)}

def obtener_analitica_educativa_curso(curso_id):
    """
    Consolida todos los indicadores de analítica educativa en un solo reporte.
    """
    from controllers.analisis_dificultad import analizar_dificultad_curso
    from controllers.segmentacion import segmentar_estudiantes_curso

    try:
        progreso = analizar_progreso_curso(curso_id)
        dificultad = analizar_dificultad_curso(curso_id)
        segmentacion = segmentar_estudiantes_curso(curso_id)

        if "error" in progreso: return progreso

        # Resumen de comportamiento de aprendizaje (Conteos por grupo)
        comportamiento = {
            "destacados": len(segmentacion.get("Grupo A (Destacados)", [])),
            "regulares": len(segmentacion.get("Grupo B (Regulares)", [])),
            "en_riesgo": len(segmentacion.get("Grupo C (Riesgo Académico)", []))
        }

        return {
            "curso_id": curso_id,
            "indicadores": {
                "avance_promedio_curso": progreso.get("avance_promedio_general"),
                "tasa_finalizacion": progreso.get("tasa_finalizacion"),
                "tasa_abandono": progreso.get("tasa_abandono"),
                "total_alumnos": progreso.get("total_alumnos_inscritos")
            },
            "desempeño_por_tema": dificultad.get("lecciones_baja_aprobacion", [])[:3],
            "efectividad_evaluaciones": dificultad.get("preguntas_mas_falladas", [])[:5],
            "comportamiento_aprendizaje": comportamiento
        }
    except Exception as e:
        return {"error": str(e)}