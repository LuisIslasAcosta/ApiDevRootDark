"""
Script para generar cursos de prueba con Faker
Genera 20 cursos para cada profesor en la base de datos
"""
from faker import Faker
import random
from config.config import cursos_collection, usuarios_collection
from bson.objectid import ObjectId

# Inicializar Faker en español
fake = Faker('es_MX')

# Lista de profesores encontrados en la base de datos
profesores = [
    "6a546880cbe1f2fb13885a6f",  # Julio Cesar Islas
    "6a546880cbe1f2fb13885a6f"   # Sergio Islas (mismo ID en la imagen)
]

# Cursos de ejemplo por categoría
categorias_cursos = [
    "Programación", "Diseño Web", "Marketing Digital", "Data Science",
    "Inteligencia Artificial", "Desarrollo Mobile", "Cloud Computing",
    "Ciberseguridad", "DevOps", "Blockchain", "IoT", "Machine Learning",
    "React", "Python", "JavaScript", "Angular", "Vue.js", "Node.js",
    "Docker", "Kubernetes", "SQL", "MongoDB", "API REST", "GraphQL",
    "Flutter", "iOS", "Android", "Unity", "Photoshop", "Illustrator"
]

def generar_cursos_para_profesor(profesor_id, cantidad=20):
    """Genera cursos de prueba para un profesor específico"""
    cursos_creados = []
    
    for i in range(cantidad):
        # Generar datos del curso
        categoria = random.choice(categorias_cursos)
        nombre_curso = f"{categoria} - {fake.catch_phrase()}"
        
        curso = {
            "nombre": nombre_curso[:100],  # Limitar a 100 caracteres
            "descripcion": fake.text(max_nb_chars=300),
            "profesor": profesor_id,
            "precio": random.choice([0, 99, 149, 199, 299, 399, 499, 799, 999]),
            "imagenes": [],  # Sin imágenes por ahora (las agregarás manualmente)
            "videos": []     # Sin videos por ahora
        }
        
        # Insertar en la base de datos
        resultado = cursos_collection.insert_one(curso)
        curso["_id"] = str(resultado.inserted_id)
        cursos_creados.append(curso)
        
        print(f"✓ Curso {i+1}/{cantidad} creado: {nombre_curso}")
    
    return cursos_creados

def main():
    print("=" * 60)
    print("GENERADOR DE CURSOS DE PRUEBA")
    print("=" * 60)
    print()
    
    # Verificar profesores en la base de datos
    print("Profesores encontrados:")
    profesores_db = list(usuarios_collection.find({"rol": "profesor"}))
    
    if not profesores_db:
        print(" No se encontraron profesores en la base de datos")
        return
    
    for prof in profesores_db:
        print(f"  - {prof.get('nombre')} {prof.get('apellidop')} (ID: {prof['_id']})")
    
    print()
    print(f"Generando 20 cursos para cada profesor...")
    print()
    
    total_cursos = 0
    
    for profesor in profesores_db:
        profesor_id = str(profesor["_id"])
        nombre_profesor = f"{profesor.get('nombre')} {profesor.get('apellidop')}"
        
        print(f"\nProfesor: {nombre_profesor}")
        print("-" * 60)
        
        cursos = generar_cursos_para_profesor(profesor_id, cantidad=20)
        total_cursos += len(cursos)
        
        print(f"✓ {len(cursos)} cursos creados para {nombre_profesor}")
    
    print()
    print("=" * 60)
    print(f"✓ PROCESO COMPLETADO")
    print(f"✓ Total de cursos creados: {total_cursos}")
    print("=" * 60)
    print()
    print("Ahora puedes:")
    print("1. Agregar imágenes a los cursos desde el panel de profesor")
    print("2. Usar URLs de imágenes externas (Imgur, Cloudinary, etc.)")
    print("3. Agregar videos de YouTube")

if __name__ == "__main__":
    main()