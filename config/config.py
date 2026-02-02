from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["DevRootDark"]
usuarios_collection = db["usuarios"]
cursos_collection = db["cursos"]
examenes_collection = db["examenes"]
inscripciones_collection = db["inscripciones"]
preguntas_collection = db["preguntas"]