from bson.objectid import ObjectId
from config.config import respuestas_collection
from config.mongo_spark_conexion import get_spark_session
import numpy as np

def analizar_respuestas(alumno_id):
    spark = get_spark_session()

    if spark is None:
        return {"error": "Error al conectar con Spark. Verifica la configuración."}

    try:
        alumno_oid = ObjectId(alumno_id)
    except:
        return {"error": "Formato de alumno_id inválido."}

    # Ordenamos por _id para asegurar que el historial sea cronológico
    respuestas = list(respuestas_collection.find({"alumno_id": alumno_oid}).sort("_id", 1))
    if not respuestas:
        return {"error": "El alumno no tiene respuestas registradas."}

    # Limpieza
    for r in respuestas:
        r["_id"] = str(r["_id"])
        r["alumno_id"] = str(r["alumno_id"])
        r["examen_id"] = str(r["examen_id"])

    df = spark.createDataFrame(respuestas)

    # ================= HISTORIAL =================
    califs = df.select("calificacion").rdd.flatMap(lambda x: x).collect()
    if len(califs) == 0:
        return {"error": "Sin datos"}

    # ================= PROMEDIO =================
    promedio = sum(califs) / len(califs)

    # ================= NIVEL ACTUAL =================
    if promedio < 60:
        nivel_actual = "Básico"
    elif promedio < 80:
        nivel_actual = "Intermedio"
    else:
        nivel_actual = "Avanzado"

    # ================= PROMEDIO PONDERADO (pesos exponenciales) =================
    pesos = [2**i for i in range(len(califs))]
    promedio_ponderado = sum(c * p for c, p in zip(califs, pesos)) / sum(pesos)

    # ================= REGRESIÓN POLINÓMICA =================
    x = np.arange(len(califs))
    y = np.array(califs)

    if len(califs) > 1:
        coef = np.polyfit(x, y, 1)  # polinomio lineal: más estable para ver si mejora o empeora
        prediccion = np.polyval(coef, len(x)) # Predecimos el valor del SIGUIENTE examen (índice n)
    else:
        prediccion = promedio

    # ================= AJUSTE FINAL =================
    prediccion_final = (0.5 * promedio_ponderado) + (0.5 * prediccion)
    prediccion_final = max(0, min(100, prediccion_final))  # limitar entre 0 y 100

    # ================= NIVEL FUTURO =================
    if prediccion_final < 60:
        nivel_futuro = "Básico"
    elif prediccion_final < 80:
        nivel_futuro = "Intermedio"
    else:
        nivel_futuro = "Avanzado"

    # ================= RESPUESTA =================
    historial = df.select("examen_id", "calificacion").toPandas().to_dict("records")

    return {
        "alumno_id": alumno_id,
        "promedio_actual": round(promedio, 2),
        "promedio_ponderado": round(promedio_ponderado, 2),
        "prediccion_calificacion": round(prediccion_final, 2),
        "nivel_actual": nivel_actual,
        "nivel_futuro": nivel_futuro,
        "historial": historial
    }
