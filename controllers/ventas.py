from config.mongo_spark_conexion import get_dataframe
from pyspark.sql.functions import sum, avg, count

def analizar_ventas(profesor_id=None):
    spark, df, df_vector = get_dataframe(profesor_id)

    if df is None:
        spark.stop()
        return {"error": "No hay cursos registrados."}

    # Reclasificación de nulos
    df_clean = df.fillna({"nombre": "SIN_CLASIFICAR"})

    # MapReduce: resumen por curso
    resumen = df_clean.groupBy("nombre").agg(
        sum("precio").alias("ingreso_total"),
        count("*").alias("cantidad_total"),
        avg("precio").alias("precio_promedio")
    )

    # Convertir a dict para JSON
    resumen_pd = resumen.toPandas().to_dict("records")

    # Interpretación automática
    if resumen_pd:
        max_ingreso = max(r["ingreso_total"] for r in resumen_pd)
        max_cantidad = max(r["cantidad_total"] for r in resumen_pd)

        for r in resumen_pd:
            tipo = "Curso Secundario"
            if r["ingreso_total"] == max_ingreso:
                tipo = "Curso Estrella (Mayor ingreso)"
            elif r["cantidad_total"] == max_cantidad:
                tipo = "Curso de Alta Rotación"
            r["clasificacion"] = tipo

    spark.stop()

    return {
        "profesor_id": profesor_id,
        "resumen": resumen_pd
    }
