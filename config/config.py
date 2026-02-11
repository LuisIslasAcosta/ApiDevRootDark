from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
##client = MongoClient("mongodb://100.68.178.91:27017/")
db = client["DevRootDark"]
usuarios_collection = db["usuarios"]
cursos_collection = db["cursos"]
examenes_collection = db["examenes"]
inscripciones_collection = db["inscripciones"]
preguntas_collection = db["preguntas"]
lecciones_collection = db["lecciones"]
respuestas_collection = db["respuestas"]
niveles_collection = db["niveles"]

