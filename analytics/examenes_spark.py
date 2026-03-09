from config.mongo_spark_conexion import get_spark_session
from config.config import respuestas_collection, examenes_collection
from pyspark.sql.functions import avg


def promedio_por_examen_profesor(profesor_id):

    spark = get_spark_session()

    respuestas = list(respuestas_collection.find())
    examenes = list(examenes_collection.find())

    if not respuestas:
        return []

    # convertir ids
    for r in respuestas:
        r["_id"] = str(r["_id"])
        r["examen_id"] = str(r["examen_id"])
        r["alumno_id"] = str(r["alumno_id"])

    for e in examenes:
        e["_id"] = str(e["_id"])

    # DataFrames
    df_respuestas = spark.createDataFrame(respuestas)
    df_examenes = spark.createDataFrame(examenes)

    # JOIN
    df_join = df_respuestas.join(
        df_examenes,
        df_respuestas.examen_id == df_examenes._id,
        "left"
    )

    # Agrupar
    resultado = df_join.groupBy(
        "titulo"
    ).agg(
        avg("calificacion").alias("promedio")
    )

    data_json = [row.asDict() for row in resultado.collect()]

    spark.stop()

    return data_json