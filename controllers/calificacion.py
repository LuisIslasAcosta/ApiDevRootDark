from config.config import preguntas_collection

def calificar_examen(examen_id, respuestas_alumno):

    preguntas = list(preguntas_collection.find({"examen_id": str(examen_id)}))

    correctas = 0
    total = len(preguntas)

    print("RESPUESTAS ALUMNO:", respuestas_alumno)

    for p in preguntas:

        pid = str(p["_id"])
        correcta = str(p.get("respuesta_correcta", "")).strip().lower()

        respuesta_usuario = respuestas_alumno.get(pid)

        print("Pregunta:", pid)
        print("Correcta:", correcta)
        print("Alumno:", respuesta_usuario)

        if respuesta_usuario:
            respuesta_usuario = str(respuesta_usuario).strip().lower()

            if respuesta_usuario == correcta:
                correctas += 1

    calificacion = round((correctas / total) * 100, 2) if total > 0 else 0

    print("CORRECTAS:", correctas)
    print("TOTAL:", total)
    print("CALIFICACION:", calificacion)

    return calificacion