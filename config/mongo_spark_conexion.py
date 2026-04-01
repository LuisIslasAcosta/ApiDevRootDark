from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv
from config.config import cursos_collection
from pyspark.sql.functions import size, col
from pyspark.ml.feature import VectorAssembler

load_dotenv()

def get_spark_session():
    mongo_uri = (
        f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}"
        f"@{os.getenv('MONGO_HOST')}/{os.getenv('MONGO_DB')}"
    )

    spark = SparkSession.builder \
        .appName("DevRootDarkAnalytics") \
        .master("local[*]") \
        .config("spark.mongodb.read.connection.uri", mongo_uri) \
        .config("spark.mongodb.write.connection.uri", mongo_uri) \
        .getOrCreate()

    return spark

def get_dataframe(profesor_id=None):
    spark = get_spark_session()

    # Filtrar cursos por profesor si se pasa el ID
    query = {}
    if profesor_id:
        query["profesor"] = profesor_id

    cursos = list(cursos_collection.find(query))

    if not cursos:
        return spark, None, None

    # Convertir _id a string
    for c in cursos:
        c["_id"] = str(c["_id"])

    # Crear DataFrame
    df = spark.createDataFrame(cursos)

    # Crear columna con número de videos
    df = df.withColumn("num_videos", size(df["videos"]))

    # Asegurar que precio sea double y reemplazar nulos
    df = df.withColumn("precio", col("precio").cast("double"))
    df = df.na.fill({"precio": 0, "num_videos": 0})

    # VectorAssembler tolerante
    assembler = VectorAssembler(
        inputCols=["precio", "num_videos"],
        outputCol="features",
        handleInvalid="skip"
    )
    df_vector = assembler.transform(df)

    return spark, df, df_vector
