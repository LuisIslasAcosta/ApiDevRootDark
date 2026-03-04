import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Reconstruir la URI con las variables
mongo_uri = (
    f"mongodb+srv://{os.getenv('MONGO_USER')}:{os.getenv('MONGO_PASSWORD')}"
    f"@{os.getenv('MONGO_HOST')}/?appName={os.getenv('MONGO_APPNAME')}"
)

# Conectar al cliente
client = MongoClient(mongo_uri)

# Seleccionar la base de datos
db = client[os.getenv("MONGO_DB")]

# Colecciones
usuarios_collection = db["usuarios"]
cursos_collection = db["cursos"]
examenes_collection = db["examenes"]
inscripciones_collection = db["inscripciones"]
preguntas_collection = db["preguntas"]
lecciones_collection = db["lecciones"]
respuestas_collection = db["respuestas"]
niveles_collection = db["niveles"]

##client = MongoClient("mongodb://100.68.178.91:27017/")
##client = MongoClient("mongodb://192.168.155.14:27017/")

