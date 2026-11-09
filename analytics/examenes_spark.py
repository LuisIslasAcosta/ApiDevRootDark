from bson.objectid import ObjectId
from config.mongo_spark_conexion import get_spark_session
from config.config import respuestas_collection, examenes_collection, cursos_collection
from pyspark.sql.types import StructType, StructField, StringType, DoubleType
from pyspark.sql.functions import avg, count, round as spark_round


def _ids_cursos_profesor(profesor_id):
    valores = [str(profesor_id)]
    try:
        valores.append(ObjectId(str(profesor_id)))
    except Exception:
        pass
    cursos = cursos_collection.find({"profesor": {"$in": valores}}, {"_id": 1})
    return [str(c["_id"]) for c in cursos]


def promedio_por_examen_profesor(profesor_id):
    """Promedio de calificación por examen, solo de los cursos del profesor (con Spark)."""

    cursos_ids = _ids_cursos_profesor(profesor_id)
    if not cursos_ids:
        return []

    # Exámenes de esos cursos (curso_id puede estar como texto u ObjectId)
    filtro_cursos = cursos_ids + [ObjectId(c) for c in cursos_ids]
    examenes = list(examenes_collection.find(
        {"curso_id": {"$in": filtro_cursos}}, {"_id": 1, "titulo": 1}))
    if not examenes:
        return []

    titulos = {str(e["_id"]): str(e.get("titulo") or "Examen") for e in examenes}

    # Respuestas de esos exámenes (examen_id puede estar como texto u ObjectId)
    filtro_examenes = list(titulos.keys()) + [ObjectId(i) for i in titulos.keys()]
    respuestas = respuestas_collection.find(
        {"examen_id": {"$in": filtro_examenes}}, {"examen_id": 1, "calificacion": 1})

    # Solo los campos necesarios, con tipos fijos (Spark no entiende ObjectId)
    filas = []
    for r in respuestas:
        try:
            calificacion = float(r.get("calificacion") or 0)
        except (TypeError, ValueError):
            continue
        filas.append((str(r["examen_id"]), calificacion))

    if not filas:
        return []

    spark = get_spark_session()
    if spark is None:
        raise RuntimeError("No se pudo iniciar Spark. Verifica que Java esté instalado.")

    esquema_resp = StructType([
        StructField("examen_id", StringType(), False),
        StructField("calificacion", DoubleType(), False),
    ])
    esquema_ex = StructType([
        StructField("examen_id", StringType(), False),
        StructField("titulo", StringType(), False),
    ])

    df_respuestas = spark.createDataFrame(filas, schema=esquema_resp)
    df_examenes = spark.createDataFrame(list(titulos.items()), schema=esquema_ex)

    resultado = (
        df_respuestas.join(df_examenes, on="examen_id", how="inner")
        .groupBy("examen_id", "titulo")
        .agg(
            spark_round(avg("calificacion"), 2).alias("promedio"),
            count("*").alias("intentos"),
        )
        .orderBy("titulo")
    )

    return [
        {
            "examen_id": row["examen_id"],
            "titulo": row["titulo"],
            "promedio": float(row["promedio"]),
            "intentos": int(row["intentos"]),
        }
        for row in resultado.collect()
    ]
