from config.config import preguntas_collection

def calificar_examen(examen_id, respuestas_alumno):
    preguntas = preguntas_collection.find({"examen_id": examen_id})

    correctas = 0
    total = 0

    for p in preguntas:
        total += 1
        pid = str(p["_id"])
        correcta = p["respuesta_correcta"]

        if respuestas_alumno.get(pid) == correcta:
            correctas += 1

    calificacion = round((correctas / total) * 100, 2) if total > 0 else 0
    return calificacion
