"""
Script para generar datos de prueba adicionales
Genera alumnos, inscripciones y respuestas con calificaciones variadas
"""
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime, timedelta
import random
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Conexión a MongoDB usando variables de entorno
mongo_user = os.getenv('MONGO_USER')
mongo_password = os.getenv('MONGO_PASSWORD')
mongo_host = os.getenv('MONGO_HOST')
mongo_db = os.getenv('MONGO_DB')

mongo_uri = f"mongodb+srv://{mongo_user}:{mongo_password}@{mongo_host}/{mongo_db}?retryWrites=true&w=majority"
client = MongoClient(mongo_uri)
db = client[mongo_db]

usuarios_collection = db['usuarios']
cursos_collection = db['cursos']
inscripciones_collection = db['inscripciones']
examenes_collection = db['examenes']
respuestas_collection = db['respuestas']

# Obtener profesor y cursos existentes
profesor_id = ObjectId("6a546880cbe1f2fb13885a6f")
cursos = list(cursos_collection.find({"profesor": str(profesor_id)}))
print(f"Cursos encontrados: {len(cursos)}")

if len(cursos) == 0:
    print("ERROR: No hay cursos para este profesor")
    exit()

# Obtener exámenes de los cursos
curso_ids = [c["_id"] for c in cursos]
examenes = list(examenes_collection.find({"curso_id": {"$in": curso_ids}}))
print(f"Exámenes encontrados: {len(examenes)}")

if len(examenes) == 0:
    print("ERROR: No hay exámenes")
    exit()

# Nombres y apellidos de ejemplo
nombres = [
    "Juan", "María", "Pedro", "Ana", "Carlos", "Laura", "Miguel", "Sofía",
    "Diego", "Valentina", "Andrés", "Camila", "Felipe", "Isabella", "Javier",
    "Lucía", "Ricardo", "Elena", "Fernando", "Gabriela", "Roberto", "Patricia",
    "Eduardo", "Sandra", "Alejandro", "Natalia", "Daniel", "Andrea", "José", "Mónica"
]

apellidos = [
    "García", "Rodríguez", "Martínez", "López", "González", "Hernández",
    "Pérez", "Sánchez", "Ramírez", "Torres", "Flores", "Rivera", "Gómez",
    "Díaz", "Reyes", "Morales", "Jiménez", "Ruiz", "Álvarez", "Castillo"
]

# Generar 20 alumnos nuevos
alumnos_creados = []
for i in range(20):
    nombre = random.choice(nombres)
    apellido = random.choice(apellidos)
    email = f"{nombre.lower()}.{apellido.lower()}{i}@gmail.com"
    
    alumno = {
        "nombre": nombre,
        "apellidop": apellido,
        "email": email,
        "password": "password123",
        "rol": "alumno",
        "fecha_creacion": datetime.utcnow() - timedelta(days=random.randint(30, 90))
    }
    
    result = usuarios_collection.insert_one(alumno)
    alumnos_creados.append(result.inserted_id)
    print(f"Alumno creado: {nombre} {apellido}")

print(f"\nTotal alumnos creados: {len(alumnos_creados)}")

# Inscribir cada alumno en 2-3 cursos aleatorios
inscripciones_creadas = 0
for alumno_id in alumnos_creados:
    num_cursos = random.randint(2, 3)
    cursos_aleatorios = random.sample(cursos, min(num_cursos, len(cursos)))
    
    for curso in cursos_aleatorios:
        inscripcion = {
            "alumno_id": str(alumno_id),
            "curso_id": str(curso["_id"]),
            "profesor_id": str(profesor_id),
            "fecha_inscripcion": datetime.utcnow() - timedelta(days=random.randint(10, 60))
        }
        inscripciones_collection.insert_one(inscripcion)
        inscripciones_creadas += 1

print(f"Inscripciones creadas: {inscripciones_creadas}")

# Generar respuestas para cada alumno
respuestas_creadas = 0
for alumno_id in alumnos_creados:
    # Cada alumno responde 5-15 exámenes
    num_respuestas = random.randint(5, 15)
    examenes_aleatorios = random.sample(examenes, min(num_respuestas, len(examenes)))
    
    for examen in examenes_aleatorios:
        # Generar calificación variada
        # 30% probabilidad de ser alumno destacado (60-100)
        # 70% probabilidad de ser alumno regular (30-70)
        if random.random() < 0.3:
            calificacion = random.randint(60, 100)
        else:
            calificacion = random.randint(30, 70)
        
        # Fecha de respuesta en los últimos 60 días
        fecha_respuesta = datetime.utcnow() - timedelta(days=random.randint(1, 60))
        
        respuesta = {
            "alumno_id": str(alumno_id),
            "examen_id": str(examen["_id"]),
            "calificacion": calificacion,
            "fecha": fecha_respuesta
        }
        
        respuestas_collection.insert_one(respuesta)
        respuestas_creadas += 1

print(f"Respuestas creadas: {respuestas_creadas}")

# Actualizar algunos alumnos para que tengan días de inactividad
print("\nActualizando fechas de última actividad...")
for alumno_id in alumnos_creados:
    # 20% de alumnos tendrán más de 15 días de inactividad
    if random.random() < 0.2:
        dias_inactivos = random.randint(20, 45)
        ultima_fecha = datetime.utcnow() - timedelta(days=dias_inactivos)
        
        # Actualizar todas las respuestas del alumno a la fecha antigua
        respuestas_collection.update_many(
            {"alumno_id": str(alumno_id)},
            {"$set": {"fecha": ultima_fecha}}
        )

print("\n✅ Datos de prueba generados exitosamente!")
print(f"   - {len(alumnos_creados)} alumnos nuevos")
print(f"   - {inscripciones_creadas} inscripciones")
print(f"   - {respuestas_creadas} respuestas con calificaciones")
print("\nAhora recarga el panel del profesor para ver las métricas actualizadas.")