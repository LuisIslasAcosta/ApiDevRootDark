import os
from pymongo import MongoClient
from dotenv import load_dotenv

# Cargar variables del archivo .env
load_dotenv()

# Detectar si es conexión local o remota
mongo_user = os.getenv('MONGO_USER', '')
mongo_password = os.getenv('MONGO_PASSWORD', '')
mongo_host = os.getenv('MONGO_HOST', 'localhost')
mongo_port = os.getenv('MONGO_PORT', '27017')
mongo_appname = os.getenv('MONGO_APPNAME', 'DevRootDark')
mongo_db = os.getenv('MONGO_DB', 'DevRootDark')

# Determinar si es conexión local (sin usuario/contraseña o host localhost)
is_local = (
    (not mongo_user or not mongo_password) or 
    mongo_host in ['localhost', '127.0.0.1'] or
    'localhost' in mongo_host
)

if is_local:
    # Conexión local sin autenticación
    if mongo_port:
        mongo_uri = f"mongodb://{mongo_host}:{mongo_port}/"
    else:
        mongo_uri = f"mongodb://{mongo_host}/"
else:
    # Conexión remota a MongoDB Atlas con autenticación
    mongo_uri = (
        f"mongodb+srv://{mongo_user}:{mongo_password}"
        f"@{mongo_host}/?appName={mongo_appname}"
    )

print(f"Conectando a MongoDB: {'LOCAL' if is_local else 'REMOTO'}")
print(f"URI: {mongo_uri.replace(mongo_password, '***') if mongo_password else mongo_uri}")

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
lecciones_vistas_collection = db["lecciones_vistas"]

##client = MongoClient("mongodb://100.68.178.91:27017/")
##client = MongoClient("mongodb://192.168.155.14:27017/")
