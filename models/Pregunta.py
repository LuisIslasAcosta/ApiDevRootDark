def crear_pregunta(examen_id, tipo, enunciado, opciones, respuesta_correcta, preguntas_collection):
    nueva = {
        "examen_id": examen_id,
        "tipo": tipo,
        "enunciado": enunciado,
        "opciones": opciones,
        "respuesta_correcta": respuesta_correcta
    }
    preguntas_collection.insert_one(nueva)
    return {"mensaje": "Pregunta creada"}