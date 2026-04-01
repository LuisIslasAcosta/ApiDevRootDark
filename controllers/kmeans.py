from config.mongo_spark_conexion import get_dataframe
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator

def ejecutar_kmeans(profesor_id=None):
    spark, df, df_vector = get_dataframe(profesor_id)

    if df is None or df_vector is None:
        spark.stop()
        return {"error": "El profesor no tiene cursos para clustering."}


    total = df_vector.count()
    if total < 3:
        spark.stop()
        return {"error": "No hay suficientes datos para clustering."}

    kmeans = KMeans(k=3, seed=42, featuresCol="features", predictionCol="cluster")
    model = kmeans.fit(df_vector)
    result = model.transform(df_vector)

    evaluator = ClusteringEvaluator(featuresCol="features", predictionCol="cluster", metricName="silhouette")
    silhouette = evaluator.evaluate(result)

    centers = model.clusterCenters()
    distribucion = result.groupBy("cluster").count().collect()

    spark.stop()

    return {
        "profesor_id": profesor_id,
        "total_registros": total,
        "silhouette": round(silhouette, 4),
        "centroides": [list(center) for center in centers],
        "distribucion": [{"cluster": row["cluster"], "count": row["count"]} for row in distribucion]
    }
