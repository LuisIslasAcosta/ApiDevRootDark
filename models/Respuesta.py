from config.config import preguntas_collection, respuestas_collection, examenes_collection
from bson.objectid import ObjectId
from flask import jsonify

def guardar_respuestas(alumno_id, examen_id, respuestas):
    print(f"DEBUG: Guardando respuestas para examen {examen_id}")
    print(f"DEBUG: Respuestas recibidas: {respuestas}")

    # Primero buscar en la colección de preguntas separada
    preguntas = list(preguntas_collection.find({"examen_id": examen_id}))
    print(f"DEBUG: Preguntas en colección separada: {len(preguntas)}")
    
    # Si no hay preguntas en la colección separada, buscar en el campo del examen
    if not preguntas:
        try:
            examen = examenes_collection.find_one({"_id": ObjectId(examen_id)})
            if examen and examen.get("preguntas"):
                print(f"DEBUG: Usando preguntas del campo embebido del examen")
                preguntas = examen["preguntas"]
        except Exception as e:
            print(f"DEBUG: Error al buscar examen: {e}")
            pass

    correctas = 0
    total = len(preguntas)
    print(f"DEBUG: Total preguntas a evaluar: {total}")

    for idx, pregunta in enumerate(preguntas):
        # Usar el campo 'id' que coincide con lo que envía el frontend
        pregunta_id = str(pregunta.get("id", pregunta.get("_id", idx)))
        respuesta_usuario = respuestas.get(pregunta_id)
        respuesta_correcta = pregunta.get("respuesta_correcta")
        
        print(f"DEBUG: Pregunta {idx}: respuesta_usuario={respuesta_usuario}, correcta={respuesta_correcta}")

        if respuesta_usuario and respuesta_correcta:
            if respuesta_usuario.strip().lower() == respuesta_correcta.strip().lower():
                correctas += 1
                print(f"DEBUG: ✓ Correcta")

    calificacion = 0

    if total > 0:
        calificacion = round((correctas / total) * 100)

    print(f"DEBUG: Calificación final: {calificacion}%")

    respuestas_collection.insert_one({
        "alumno_id": ObjectId(alumno_id),
        "examen_id": examen_id,
        "correctas": correctas,
        "total": total,
        "calificacion": calificacion
    })

    return jsonify({
        "mensaje": "Examen enviado",
        "correctas": correctas,
        "total": total,
        "calificacion": calificacion
    }), 201
