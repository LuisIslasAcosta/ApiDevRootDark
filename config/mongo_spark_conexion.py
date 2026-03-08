from pyspark.sql import SparkSession
import os
from dotenv import load_dotenv

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