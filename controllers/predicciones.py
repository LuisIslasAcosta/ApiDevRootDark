from config.config import respuestas_collection, usuarios_collection, inscripciones_collection, examenes_collection
from bson.objectid import ObjectId
from datetime import datetime

def analizar_riesgo_curso(curso_id):
    reporte_riesgo = []
    hoy = datetime.utcnow()

    try:
        c_id = ObjectId(curso_id)
    except:
        return {"error": "ID de curso inválido"}

    # 1. Definir los criterios de búsqueda para el curso (ObjectId o String)
    curso_keys = [str(curso_id), c_id]
    query_curso = {"curso_id": {"$in": curso_keys}}

    # 2. Obtener exámenes del curso una sola vez
    examenes_curso = list(examenes_collection.find(query_curso))
    total_examenes = len(examenes_curso)
    
    # Recolectar todos los posibles IDs de exámenes vinculados a este curso
    examenes_ids = []
    for e in examenes_curso:
        examenes_ids.append(e["_id"])
        examenes_ids.append(str(e["_id"]))

    # 3. Obtener alumnos inscritos
    inscripciones = list(inscripciones_collection.find(query_curso))
    
    print(f"DEBUG: Curso {curso_id} -> Alumnos inscritos: {len(inscripciones)}, Exámenes en catálogo: {total_examenes}")

    for inscripcion in inscripciones:
        alumno_id_raw = inscripcion.get("alumno_id")
        
        # Buscar el usuario (alumno)
        try:
            alumno = usuarios_collection.find_one({"_id": ObjectId(alumno_id_raw)})
        except:
            alumno = None
        
        if not alumno:
            continue

        # 4. Buscar respuestas del alumno para los exámenes de este curso
        alumno_keys = [str(alumno_id_raw), ObjectId(alumno_id_raw)]
        
        # Filtro de respuestas: del alumno Y que pertenezcan a los exámenes del curso
        filtro_respuestas = {
            "alumno_id": {"$in": alumno_keys},
            "examen_id": {"$in": examenes_ids}
        }
        
        respuestas = list(respuestas_collection.find(filtro_respuestas))
        print(f"DEBUG: Alumno {alumno.get('nombre')} - Respuestas encontradas en este curso: {len(respuestas)}")

        # --- CÁLCULO DE VARIABLES ---
        num_intentos = len(respuestas)
        promedio = sum([r.get("calificacion", 0) for r in respuestas]) / num_intentos if num_intentos > 0 else 0
        
        # Progreso: cuántos exámenes únicos ha completado (normalizando IDs a string)
        set_examenes = set([str(r.get("examen_id")) for r in respuestas])
        examenes_completados = len(set_examenes)
        progreso = (examenes_completados / total_examenes * 100) if total_examenes > 0 else 0

        # Tiempo sin ingresar: Buscamos la fecha de su última respuesta
        dias_inactivo = 999  # Por defecto si no hay actividad
        ultima_rta = respuestas_collection.find_one(
            filtro_respuestas, 
            sort=[("_id", -1)] # Usamos _id para ordenar cronológicamente si 'fecha' falta
        )
        
        if ultima_rta:
            fecha_act = ultima_rta.get("fecha")
            
            # Si no hay campo fecha, extraemos el timestamp del ObjectId del documento
            if not fecha_act and isinstance(ultima_rta["_id"], ObjectId):
                fecha_act = ultima_rta["_id"].generation_time

            if isinstance(fecha_act, str):
                try:
                    fecha_act = datetime.fromisoformat(fecha_act.replace("Z", "+00:00")).replace(tzinfo=None)
                except:
                    fecha_act = None # Si no se puede parsear, se mantiene como inactivo
            elif fecha_act and fecha_act.tzinfo:
                fecha_act = fecha_act.replace(tzinfo=None) # Normalizar a naive UTC
            
            if fecha_act: # Solo calcular si la fecha es válida
                dias_inactivo = (hoy - fecha_act).days

        # --- LÓGICA DE RIESGO ---
        nivel_riesgo = "Bajo"
        motivo = "Estudiante activo"

        if dias_inactivo > 10:
            nivel_riesgo = "Alto"
            motivo = f"Inactividad prolongada ({dias_inactivo} días)"
        elif promedio < 70 and progreso < 50 and num_intentos > 0:
            nivel_riesgo = "Medio"
            motivo = "Bajo promedio y poco progreso"
        elif num_intentos == 0 and total_examenes > 0:
            nivel_riesgo = "Alto"
            motivo = "Sin actividad en el curso"
        elif num_intentos > (examenes_completados * 3) and num_intentos > 0: # Ejemplo: demasiados intentos por examen
            nivel_riesgo = "Medio"
            motivo = "Número de intentos inusual"

        reporte_riesgo.append({
            "alumno": f"{alumno.get('nombre')} {alumno.get('apellidop')}",
            "email": alumno.get("email"),
            "progreso": f"{progreso:.1f}%",
            "promedio": f"{promedio:.1f}",
            "intentos": num_intentos,
            "dias_inactivo": dias_inactivo,
            "riesgo": nivel_riesgo,
            "motivo": motivo
        })

    return reporte_riesgo