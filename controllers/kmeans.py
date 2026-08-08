from config.mongo_spark_conexion import get_dataframe
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
import numpy as np

def ejecutar_kmeans(profesor_id=None, k=3):
    spark, df, df_vector = get_dataframe(profesor_id)

    if spark is None or df is None or df_vector is None:
        error_msg = "El profesor no tiene cursos para clustering."
        if spark is None:
            error_msg = "Error al conectar con Spark. Verifica la configuración."
        return {"error": error_msg}

    # Reducir logs de Spark
    try:
        spark.sparkContext.setLogLevel("ERROR")
    except:
        pass

    try:
        total = df_vector.count()
    except Exception as e:
        try:
            spark.stop()
        except:
            pass
        return {"error": f"Error al contar datos: {str(e)}"}
    
    if total < 3:
        try:
            spark.stop()
        except:
            pass
        return {"error": f"No hay suficientes datos para clustering. Se necesitan al menos 3, encontrados: {total}"}

    try:
        kmeans = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster")
        model = kmeans.fit(df_vector)
        result = model.transform(df_vector)

        evaluator = ClusteringEvaluator(featuresCol="features", predictionCol="cluster", metricName="silhouette")
        silhouette = evaluator.evaluate(result)

        centers = model.clusterCenters()
        distribucion = result.groupBy("cluster").count().collect()

        # Calcular WCSS (Within-Cluster Sum of Squares)
        wcss = 0.0
        distancias_por_cluster = {}
        
        # Obtener los datos con sus predicciones
        rows = result.collect()
        
        for row in rows:
            cluster = row['cluster']
            features = np.array(row['features'].toArray())
            center = centers[cluster]
            
            # Calcular distancia euclidiana al centroide
            distancia = np.linalg.norm(features - center)
            wcss += distancia ** 2
            
            # Acumular distancias por cluster
            if cluster not in distancias_por_cluster:
                distancias_por_cluster[cluster] = []
            distancias_por_cluster[cluster].append(distancia)
        
        # Calcular distancia promedio por cluster
        distancias_promedio = {}
        for cluster, distancias in distancias_por_cluster.items():
            distancias_promedio[str(cluster)] = round(float(np.mean(distancias)), 2)

        resultado = {
            "profesor_id": profesor_id,
            "total_registros": total,
            "k": k,
            "silhouette": round(silhouette, 4),
            "wcss": round(float(wcss), 2),
            "centroides": [list(center) for center in centers],
            "distribucion": [{"cluster": row["cluster"], "count": row["count"]} for row in distribucion],
            "distancias_por_cluster": distancias_promedio
        }
    except Exception as e:
        return {"error": f"Error en el análisis K-Means: {str(e)}"}

    return resultado


def metodo_codo(profesor_id=None, k_range=(2, 10)):
    """
    Implementa el método del codo para determinar el k óptimo.
    Usa el Silhouette Score como métrica alternativa (más estable en PySpark 3.0+).
    """
    spark, df, df_vector = get_dataframe(profesor_id)

    if spark is None or df is None or df_vector is None:
        error_msg = "El profesor no tiene cursos para clustering."
        if spark is None:
            error_msg = "Error al conectar con Spark. Verifica la configuración."
        return {"error": error_msg}

    # Reducir logs de Spark
    try:
        spark.sparkContext.setLogLevel("ERROR")
    except:
        pass

    try:
        total = df_vector.count()
    except Exception as e:
        try:
            spark.stop()
        except:
            pass
        return {"error": f"Error al contar datos: {str(e)}"}
    
    if total < 3:
        try:
            spark.stop()
        except:
            pass
        return {"error": f"No hay suficientes datos para clustering. Se necesitan al menos 3, encontrados: {total}"}

    # Calcular Silhouette Score para cada k 
    silhouette_scores = []
    k_values = list(range(k_range[0], k_range[1] + 1))
    
    for k in k_values:
        try:
            kmeans = KMeans(k=k, seed=42, featuresCol="features", predictionCol="cluster")
            model = kmeans.fit(df_vector)
            result = model.transform(df_vector)
            
            # Calcular Silhouette Score
            evaluator = ClusteringEvaluator(featuresCol="features", predictionCol="cluster", metricName="silhouette")
            silhouette = evaluator.evaluate(result)
            silhouette_scores.append(float(silhouette))
            
        except Exception as e:
            print(f"Error con k={k}: {str(e)}")
            silhouette_scores.append(0.0)
    
    k_optimo = k_values[0]
    max_silhouette = 0.0
    if silhouette_scores:
        max_idx = silhouette_scores.index(max(silhouette_scores))
        k_optimo = k_values[max_idx]
        max_silhouette = silhouette_scores[max_idx]
    
    deltas = []
    for i in range(1, len(silhouette_scores) - 1):
        if silhouette_scores[i] is not None and silhouette_scores[i-1] is not None and silhouette_scores[i+1] is not None:
            
            delta_prev = abs(silhouette_scores[i] - silhouette_scores[i-1])
            delta_next = abs(silhouette_scores[i+1] - silhouette_scores[i])
            delta = abs(delta_prev - delta_next)
            deltas.append({"k": k_values[i], "delta": delta})
        else:
            deltas.append({"k": k_values[i], "delta": 0})
    
    resultado = {
        "profesor_id": profesor_id,
        "total_registros": total,
        "k_values": k_values,
        "silhouette_scores": silhouette_scores,
        "deltas": deltas,
        "k_optimo": k_optimo,
        "max_silhouette": max_silhouette,
        "metodo": "Silhouette Score"
    }
    
    try:
        spark.stop()
    except:
        pass
    
    return resultado
