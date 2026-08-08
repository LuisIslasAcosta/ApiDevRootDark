from config.config import inscripciones_collection, cursos_collection
from bson.objectid import ObjectId
from collections import Counter
from itertools import combinations

def generar_recomendaciones_por_curso(curso_id_referencia):
    """
    Busca qué otros cursos han tomado los alumnos que se inscribieron en el curso dado.
    Implementación simplificada de reglas de asociación.
    """
    try:
        # 1. Encontrar a todos los alumnos inscritos en el curso de referencia
        inscritos_referencia = list(inscripciones_collection.find({"curso_id": curso_id_referencia}))
        alumnos_ids = [ins["alumno_id"] for ins in inscritos_referencia]

        if not alumnos_ids:
            return {"mensaje": "No hay suficientes datos para generar recomendaciones", "recomendaciones": []}

        # 2. Buscar qué otros cursos han tomado esos mismos alumnos
        todas_las_inscripciones = list(inscripciones_collection.find({"alumno_id": {"$in": alumnos_ids}}))
        
        # Contar frecuencias de los otros cursos
        conteo_cursos = Counter()
        for ins in todas_las_inscripciones:
            c_id = ins["curso_id"]
            if c_id != curso_id_referencia:
                conteo_cursos[c_id] += 1

        # 3. Obtener los 3 cursos más frecuentes
        top_cursos = conteo_cursos.most_common(3)
        
        recomendaciones = []
        for c_id, frecuencia in top_cursos:
            try:
                curso_data = cursos_collection.find_one({"_id": ObjectId(c_id)})
                if not curso_data: # Probar como string si no es ObjectId
                    curso_data = cursos_collection.find_one({"_id": c_id})
                
                if curso_data:
                    recomendaciones.append({
                        "curso_id": str(curso_data["_id"]),
                        "nombre": curso_data.get("nombre"),
                        "descripcion": curso_data.get("descripcion"),
                        "frecuencia_asociacion": frecuencia
                    })
            except:
                continue

        return {
            "curso_base": curso_id_referencia,
            "recomendaciones": recomendaciones
        }
    except Exception as e:
        return {"error": str(e)}

def generar_recomendaciones_para_alumno(alumno_id):
    """
    Genera recomendaciones de cursos para un alumno específico
    basándose en los cursos que ya ha tomado y los patrones de otros alumnos.
    """
    try:
        # 1. Obtener los cursos que el alumno ya ha tomado
        # Asumimos que una inscripción significa que el curso ha sido "tomado" o está en progreso.
        # Una mejora futura sería considerar solo cursos "completados".
        alumno_inscripciones = list(inscripciones_collection.find({"alumno_id": alumno_id}))
        cursos_tomados_ids = {ins["curso_id"] for ins in alumno_inscripciones} # Usar un set para búsqueda eficiente

        if not cursos_tomados_ids:
            return {"mensaje": "El alumno no ha tomado cursos para generar recomendaciones", "recomendaciones": []}

        conteo_recomendaciones = Counter()

        # 2. Para cada curso que el alumno ha tomado, encontrar qué otros cursos
        # han tomado los alumnos que también tomaron ese curso.
        for curso_id_tomado in cursos_tomados_ids:
            # Encontrar a todos los alumnos (excepto el actual) que tomaron este curso
            otros_alumnos_en_curso = list(inscripciones_collection.find({"curso_id": curso_id_tomado, "alumno_id": {"$ne": alumno_id}}))
            otros_alumnos_ids = {ins["alumno_id"] for ins in otros_alumnos_en_curso}

            if not otros_alumnos_ids:
                continue

            # Para cada uno de esos "otros alumnos", ver qué cursos tomaron
            inscripciones_de_otros_alumnos = list(inscripciones_collection.find({"alumno_id": {"$in": list(otros_alumnos_ids)}}))
            
            for ins_otro_alumno in inscripciones_de_otros_alumnos:
                curso_recomendado_id = ins_otro_alumno["curso_id"]
                # Solo considerar cursos que el alumno actual NO ha tomado
                if curso_recomendado_id not in cursos_tomados_ids:
                    conteo_recomendaciones[curso_recomendado_id] += 1

        # 3. Obtener los 5 cursos más frecuentemente recomendados
        top_cursos_recomendados = conteo_recomendaciones.most_common(5)
        
        recomendaciones_finales = []
        for c_id, frecuencia in top_cursos_recomendados:
            try:
                # Intentar convertir a ObjectId, si falla, usar como string
                try:
                    curso_obj_id = ObjectId(c_id)
                except:
                    curso_obj_id = c_id

                curso_data = cursos_collection.find_one({"_id": curso_obj_id})
                
                if curso_data:
                    recomendaciones_finales.append({
                        "curso_id": str(curso_data["_id"]),
                        "nombre": curso_data.get("nombre", "Nombre Desconocido"),
                        "descripcion": curso_data.get("descripcion", "Sin descripción"),
                        "frecuencia_asociacion": frecuencia # Indica cuántas veces apareció en el conteo
                    })
            except Exception as e_curso_data:
                print(f"Error al obtener datos del curso {c_id}: {e_curso_data}")
                continue

        return {
            "alumno_id": alumno_id,
            "recomendaciones": recomendaciones_finales
        }
    except Exception as e:
        return {"error": str(e)}