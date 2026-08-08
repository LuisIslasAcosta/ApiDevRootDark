from config.config import respuestas_collection, preguntas_collection, examenes_collection, lecciones_collection, niveles_collection
from bson.objectid import ObjectId
from datetime import datetime

def analizar_dificultad_curso(curso_id):
    try:
        c_id = ObjectId(curso_id)
    except:
        return {"error": "ID de curso inválido"}

    curso_keys = [str(curso_id), c_id, str(c_id)]
    query_curso = {"curso_id": {"$in": curso_keys}}

    # --- 1. Identificación de preguntas más falladas ---
    preguntas_falladas_report = []

    # Obtener todos los exámenes del curso
    examenes_del_curso = list(examenes_collection.find(query_curso))
    print(f"DEBUG Dificultad: Exámenes encontrados para el curso {curso_id}: {len(examenes_del_curso)}")

    examenes_ids_str = [str(e["_id"]) for e in examenes_del_curso]
    examenes_ids_obj = [e["_id"] for e in examenes_del_curso]
    all_exam_ids_for_query = examenes_ids_str + examenes_ids_obj

    if not examenes_del_curso:
        # Si no hay exámenes, no hay preguntas ni respuestas para analizar
        return {
            "preguntas_mas_falladas": [],
            "lecciones_baja_aprobacion": []
        }

    # Obtener todas las preguntas de esos exámenes
    preguntas_del_curso = list(preguntas_collection.find({"examen_id": {"$in": all_exam_ids_for_query}}))
    
    # Mapear preguntas por ID para fácil acceso
    preguntas_lookup = {}
    for p in preguntas_del_curso:
        preguntas_lookup[str(p["_id"])] = {
            "enunciado": p.get("enunciado", "Sin enunciado"),
            "respuesta_correcta": str(p.get("respuesta_correcta", "")).strip().lower(),
            "examen_id": str(p.get("examen_id"))
        }
    
    # Inicializar contadores para cada pregunta
    question_stats = {}
    for p_id_str, p_data in preguntas_lookup.items():
        question_stats[p_id_str] = {
            "enunciado": p_data["enunciado"],
            "examen_id": p_data["examen_id"],
            "failed_count": 0,
            "total_attempts": 0
        }

    # Obtener todas las respuestas de los alumnos para los exámenes del curso
    respuestas_del_curso = list(respuestas_collection.find({"examen_id": {"$in": all_exam_ids_for_query}}))
    print(f"DEBUG Dificultad: Respuestas encontradas para estos exámenes: {len(respuestas_del_curso)}")

    for rta in respuestas_del_curso:
        alumno_respuestas = rta.get("respuestas", {}) 
        if not isinstance(alumno_respuestas, dict):
            continue

        for p_id_str, student_answer in alumno_respuestas.items():
            if p_id_str in question_stats:
                question_stats[p_id_str]["total_attempts"] += 1
                
                correct_answer = preguntas_lookup[p_id_str]["respuesta_correcta"]
                
                if str(student_answer).strip().lower() != correct_answer:
                    question_stats[p_id_str]["failed_count"] += 1
    
    # Calcular porcentaje de fallo y preparar el reporte
    for p_id_str, stats in question_stats.items():
        if stats["total_attempts"] > 0:
            failure_percentage = (stats["failed_count"] / stats["total_attempts"]) * 100
            preguntas_falladas_report.append({
                "pregunta_id": p_id_str,
                "enunciado": stats["enunciado"],
                "examen_id": stats["examen_id"],
                "porcentaje_fallo": f"{failure_percentage:.1f}%",
                "fallos": stats["failed_count"],
                "intentos_totales": stats["total_attempts"]
            })
    
    # Ordenar por porcentaje de fallo descendente
    preguntas_falladas_report.sort(key=lambda x: float(x["porcentaje_fallo"].replace('%', '')), reverse=True)

    # --- 2. Identificación de lecciones con menor aprobación ---
    lecciones_baja_aprobacion_report = []

    # Obtener todos los niveles del curso
    niveles_del_curso = list(niveles_collection.find(query_curso))
    niveles_ids_str = [str(n["_id"]) for n in niveles_del_curso]
    niveles_ids_obj = [n["_id"] for n in niveles_del_curso]
    all_nivel_ids_for_query = niveles_ids_str + niveles_ids_obj

    # Obtener todas las lecciones de esos niveles
    lecciones_del_curso = list(lecciones_collection.find({"nivel_id": {"$in": all_nivel_ids_for_query}}))
    
    # Mapear lecciones por ID y asociar exámenes
    lecciones_stats = {}
    for lec in lecciones_del_curso:
        lecciones_stats[str(lec["_id"])] = {
            "titulo": lec.get("titulo", "Sin título"),
            "exam_ids": [],
            "total_calificaciones": 0,
            "num_calificaciones": 0,
            "average_score": 0.0
        }
    
    # Asociar exámenes a sus lecciones y calcular el promedio de calificaciones
    for examen in examenes_del_curso:
        leccion_id = examen.get("leccion_id")
        if leccion_id and str(leccion_id) in lecciones_stats:
            lecciones_stats[str(leccion_id)]["exam_ids"].append(str(examen["_id"]))
            # Sumar calificaciones de todas las respuestas para este examen
            respuestas_examen = list(respuestas_collection.find({"examen_id": {"$in": [str(examen["_id"]), examen["_id"]]}}))
            for rta in respuestas_examen:
                calificacion = rta.get("calificacion")
                if isinstance(calificacion, (int, float)):
                    lecciones_stats[str(leccion_id)]["total_calificaciones"] += calificacion
                    lecciones_stats[str(leccion_id)]["num_calificaciones"] += 1
    
    # Calcular el promedio final y preparar el reporte
    for lec_id_str, stats in lecciones_stats.items():
        if stats["num_calificaciones"] > 0:
            stats["average_score"] = stats["total_calificaciones"] / stats["num_calificaciones"]
            lecciones_baja_aprobacion_report.append({
                "leccion_id": lec_id_str,
                "titulo": stats["titulo"],
                "calificacion_promedio": f"{stats['average_score']:.1f}",
                "examenes_evaluados": stats["num_calificaciones"]
            })
    
    # Ordenar por calificación promedio ascendente
    lecciones_baja_aprobacion_report.sort(key=lambda x: float(x["calificacion_promedio"]))

    print(f"DEBUG Dificultad: Enviando {len(preguntas_falladas_report)} preguntas y {len(lecciones_baja_aprobacion_report)} lecciones.")

    return {
        "preguntas_mas_falladas": preguntas_falladas_report,
        "lecciones_baja_aprobacion": lecciones_baja_aprobacion_report
    }