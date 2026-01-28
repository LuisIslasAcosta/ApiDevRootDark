from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017/")
db = client["DevRootDark"]
usuarios_collection = db["usuarios"]
cursos_collection = db["cursos"]