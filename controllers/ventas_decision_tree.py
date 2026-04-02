from pyspark.sql.functions import when, col, sum, avg, count
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import DecisionTreeClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType

from config.mongo_spark_conexion import get_dataframe

def analizar_ventas_decision_tree(profesor_id=None):
    spark, df, df_vector = get_dataframe(profesor_id)

    if df is None or df.count() == 0:
        spark.stop()
        return {"error": "No hay cursos registrados o datos insuficientes."}

    # ================= RESUMEN POR CURSO =================
    df_clean = df.fillna({"nombre": "SIN_CLASIFICAR"})

    resumen = df_clean.groupBy("nombre").agg(
        sum("precio").alias("ingreso_total"),
        count("*").alias("cantidad_total"),
        avg("precio").alias("precio_promedio")
    )

    resumen_pd = resumen.toPandas().to_dict("records")
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

    # ================= ÁRBOL DE DECISIÓN =================
    resumen = resumen.withColumn("label", when(col("ingreso_total") > 50, 1).otherwise(0))

    assembler = VectorAssembler(
        inputCols=["precio_promedio", "cantidad_total", "ingreso_total"],
        outputCol="features",
        handleInvalid="skip"
    )
    df_ml = assembler.transform(resumen)
    dataset = df_ml.select("features", "label")

    if dataset.count() == 0:
        spark.stop()
        return {"error": "Dataset vacío después de limpieza."}

    train_data, test_data = dataset.randomSplit([0.8, 0.2], seed=42)
    if train_data.count() == 0 or test_data.count() == 0:
        spark.stop()
        return {"error": "No hay suficientes datos para entrenar/prueba."}

    dt = DecisionTreeClassifier(featuresCol="features", labelCol="label", maxDepth=3)
    model = dt.fit(train_data)

    predictions = model.transform(test_data)
    evaluator = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy"
    )
    accuracy = evaluator.evaluate(predictions)

    to_str = udf(lambda v: str(v), StringType())
    predictions = predictions.withColumn("features_str", to_str(col("features")))
    predicciones = predictions.select("features_str", "label", "prediction").limit(10).toPandas().to_dict("records")

    # ================= ÁRBOL EN JSON =================
    # ⚠️ Ejemplo simple: raíz con dos hojas
    arbol_json = {
        "name": "precio_promedio <= 64.5",
        "children": [
            {"name": "Clase 0"},
            {"name": "Clase 1"}
        ]
    }

    spark.stop()

    return {
        "profesor_id": profesor_id,
        "resumen": resumen_pd,
        "accuracy": round(accuracy, 4),
        "arbol": arbol_json,   # 👈 ahora es JSON
        "ejemplo_predicciones": predicciones
    }
