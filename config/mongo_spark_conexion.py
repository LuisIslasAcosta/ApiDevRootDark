from pyspark.sql import SparkSession
from pyspark.sql.types import StructType, StructField, StringType, DoubleType, IntegerType, ArrayType, BooleanType
import os
from dotenv import load_dotenv
from config.config import cursos_collection
from pyspark.sql.functions import size, col
from pyspark.ml.feature import VectorAssembler

load_dotenv()

def get_spark_session():
    """Obtiene o crea una sesión de Spark reutilizable"""
    try:
        # Intentar obtener la sesión existente
        try:
            spark = SparkSession.builder.getOrCreate()
            # Verificar que esté activa (no detenida)
            if spark.sparkContext._jsc is not None and not spark.sparkContext._jsc.isStopped():
                spark.sparkContext.setLogLevel("ERROR")
                return spark
        except:
            pass

        # Si no existe o está detenida, crear nueva
        mongo_uri = (
            f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}"
            f"@{os.getenv('MONGO_HOST')}/{os.getenv('MONGO_DB')}"
        )

        spark = SparkSession.builder \
            .appName("DevRootDarkAnalytics") \
            .master("local[*]") \
            .config("spark.mongodb.read.connection.uri", mongo_uri) \
            .config("spark.mongodb.write.connection.uri", mongo_uri) \
            .config("spark.driver.allowMultipleContexts", "true") \
            .getOrCreate()

        # Verificar que esté activa
        if spark.sparkContext._jsc is None:
            raise Exception("SparkContext no se inicializó correctamente")

        # Reducir logs
        spark.sparkContext.setLogLevel("ERROR")
        
        return spark
    except Exception as e:
        print(f"ERROR al crear SparkSession: {str(e)}")
        return None

def get_dataframe(profesor_id=None):
    spark = get_spark_session()

    if spark is None:
        return None, None, None

    # Filtrar cursos por profesor si se pasa el ID
    query = {}
    if profesor_id:
        query["profesor"] = profesor_id

    try:
        cursos = list(cursos_collection.find(query))
    except Exception as e:
        print(f"ERROR al obtener cursos de MongoDB: {str(e)}")
        try:
            spark.stop()
        except:
            pass
        return None, None, None

    if not cursos:
        try:
            spark.stop()
        except:
            pass
        return spark, None, None

    # Seleccionar y normalizar solo los campos necesarios
    cursos_normalizados = []
    for c in cursos:
        curso_norm = {
            "_id": str(c["_id"]),
            "nombre": str(c.get("nombre", "")),
            "descripcion": str(c.get("descripcion", "")),
            "profesor": str(c.get("profesor", "")),
            "nivel": str(c.get("nivel", "")),
            "categoria": str(c.get("categoria", "")),
            "precio": float(c["precio"]) if c.get("precio") is not None else 0.0,
            "num_videos": int(len(c["videos"])) if c.get("videos") is not None and isinstance(c["videos"], list) else 0
        }
        cursos_normalizados.append(curso_norm)

    # Definir schema explícito para evitar problemas de inferencia
    schema = StructType([
        StructField("_id", StringType(), True),
        StructField("nombre", StringType(), True),
        StructField("descripcion", StringType(), True),
        StructField("profesor", StringType(), True),
        StructField("nivel", StringType(), True),
        StructField("categoria", StringType(), True),
        StructField("precio", DoubleType(), True),
        StructField("num_videos", IntegerType(), True)
    ])

    # Crear DataFrame con schema explícito
    df = spark.createDataFrame(cursos_normalizados, schema=schema)

    # num_videos ya está calculado, no necesitamos recalcular

    # Reemplazar nulos si existen
    df = df.na.fill({"precio": 0.0, "num_videos": 0})

    # VectorAssembler tolerante
    assembler = VectorAssembler(
        inputCols=["precio", "num_videos"],
        outputCol="features",
        handleInvalid="skip"
    )
    df_vector = assembler.transform(df)

    return spark, df, df_vector