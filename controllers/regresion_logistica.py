from pyspark.sql.functions import when, col, sum, avg, count
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import LogisticRegression
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.sql.functions import udf
from pyspark.sql.types import StringType
import numpy as np

from config.mongo_spark_conexion import get_dataframe


def analizar_regresion_logistica(profesor_id=None):
    spark, df, df_vector = get_dataframe(profesor_id)

    if df is None or df.count() == 0:
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

    # ================= REGRESIÓN LOGÍSTICA =================
    resumen = resumen.withColumn("label", when(col("ingreso_total") > 50, 1).otherwise(0))

    assembler = VectorAssembler(
        inputCols=["precio_promedio", "cantidad_total", "ingreso_total"],
        outputCol="features",
        handleInvalid="skip"
    )
    df_ml = assembler.transform(resumen)
    dataset = df_ml.select("features", "label")

    if dataset.count() == 0:
        return {"error": "Dataset vacío después de limpieza."}

    train_data, test_data = dataset.randomSplit([0.8, 0.2], seed=42)
    if train_data.count() == 0 or test_data.count() == 0:
        return {"error": "No hay suficientes datos para entrenar/prueba."}

    lr = LogisticRegression(featuresCol="features", labelCol="label", maxIter=10)
    model = lr.fit(train_data)

    predictions = model.transform(test_data)
    evaluator = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy"
    )
    accuracy = evaluator.evaluate(predictions)

    to_str = udf(lambda v: str(v), StringType())
    predictions = predictions.withColumn("features_str", to_str(col("features")))
    predicciones = predictions.select("features_str", "label", "prediction").limit(10).toPandas().to_dict("records")

    # ================= MATRIZ DE CONFUSIÓN Y MÉTRICAS =================
    # Convertir a arrays de numpy
    y_true = np.array(predictions.select("label").collect())
    y_pred = np.array(predictions.select("prediction").collect())
    
    # Calcular matriz de confusión
    tp = int(np.sum((y_true == 1) & (y_pred == 1)))
    tn = int(np.sum((y_true == 0) & (y_pred == 0)))
    fp = int(np.sum((y_true == 0) & (y_pred == 1)))
    fn = int(np.sum((y_true == 1) & (y_pred == 0)))
    
    # Calcular métricas adicionales
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0
    f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
    
    # ================= COEFICIENTES DEL MODELO =================
    coeficientes = model.coefficients.toArray().tolist()
    intercepto = float(model.intercept)

    return {
        "profesor_id": profesor_id,
        "resumen": resumen_pd,
        "accuracy": round(accuracy, 4),
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1_score": round(f1_score, 4),
        "matriz_confusion": {
            "TP": tp,  # Verdaderos Positivos
            "TN": tn,  # Verdaderos Negativos
            "FP": fp,  # Falsos Positivos
            "FN": fn   # Falsos Negativos
        },
        "coeficientes": coeficientes,
        "intercepto": round(intercepto, 4),
        "ejemplo_predicciones": predicciones
    }
