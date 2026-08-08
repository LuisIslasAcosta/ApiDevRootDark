"""
Script para generar exámenes por nivel
Genera 1 examen por nivel SOLO para los niveles especificados
NO usa lecciones, solo nivel_id
"""
from config.config import examenes_collection, niveles_collection, cursos_collection
from bson.objectid import ObjectId

# IDs de niveles específicos de las imágenes
NIVELES_ESPECIFICOS = [
    "6a56677a2b392702b75b8e35",
    "6a56677b2b392702b75b8e39",
    "6a56677b2b392702b75b8e3d",
    "6a56677c2b392702b75b8e41",
    "6a56677c2b392702b75b8e45",
    "6a56677c2b392702b75b8e49",
    "6a56677d2b392702b75b8e4d",
    "6a56677d2b392702b75b8e51",
    "6a56677e2b392702b75b8e55",
    "6a56677e2b392702b75b8e59",
    "6a56677f2b392702b75b8e5d",
    "6a56677f2b392702b75b8e61",
    "6a5667802b392702b75b8e65",
    "6a5667802b392702b75b8e69",
    "6a5667812b392702b75b8e6d",
    "6a5667822b392702b75b8e71",
    "6a5667822b392702b75b8e75",
    "6a5667822b392702b75b8e79",
    "6a5667832b392702b75b8e7d",
    "6a5667832b392702b75b8e81",
    "6a5667842b392702b75b8e85",
    "6a5667842b392702b75b8e89",
    "6a5667852b392702b75b8e8d",
    "6a5667852b392702b75b8e91",
    "6a5667862b392702b75b8e95",
    "6a5667862b392702b75b8e99",
    "6a5667872b392702b75b8e9d",
    "6a5667872b392702b75b8ea1",
    "6a5667872b392702b75b8ea5",
    "6a5667882b392702b75b8ea9",
    "6a5667882b392702b75b8ead",
    "6a5667892b392702b75b8eb1",
    "6a5667892b392702b75b8eb5",
    "6a56678a2b392702b75b8eb9",
    "6a56678a2b392702b75b8ebd",
    "6a56678b2b392702b75b8ec1",
    "6a56678b2b392702b75b8ec5",
    "6a56678c2b392702b75b8ec9",
    "6a56678c2b392702b75b8ecd",
    "6a56678c2b392702b75b8ed1",
    "6a56678d2b392702b75b8ed5",
    "6a56678d2b392702b75b8ed9",
    "6a56678e2b392702b75b8edd",
    "6a56678e2b392702b75b8ee1",
    "6a56678f2b392702b75b8ee5",
    "6a56678f2b392702b75b8ee9",
    "6a5667902b392702b75b8eed",
    "6a5667902b392702b75b8ef1",
    "6a5667912b392702b75b8ef5",
    "6a5667912b392702b75b8ef9"
]

# Preguntas de ejemplo por categoría
PREGUNTAS_POR_CATEGORIA = {
    "Programación": [
        {"enunciado": "¿Qué es una variable?", "opciones": ["Un contenedor de datos", "Una función", "Un bucle", "Un error"], "respuesta_correcta": "Un contenedor de datos"},
        {"enunciado": "¿Cuál es un lenguaje de programación?", "opciones": ["Python", "HTML", "CSS", "SQL"], "respuesta_correcta": "Python"},
        {"enunciado": "¿Qué es un bucle for?", "opciones": ["Estructura de repetición", "Una variable", "Una función", "Un condicional"], "respuesta_correcta": "Estructura de repetición"},
        {"enunciado": "¿Qué es una función?", "opciones": ["Bloque de código reutilizable", "Una variable", "Un error", "Un bucle"], "respuesta_correcta": "Bloque de código reutilizable"},
        {"enunciado": "¿Qué es un condicional if?", "opciones": ["Estructura de decisión", "Un bucle", "Una variable", "Una función"], "respuesta_correcta": "Estructura de decisión"}
    ],
    "Diseño Web": [
        {"enunciado": "¿Qué es HTML?", "opciones": ["Lenguaje de marcado", "Lenguaje de programación", "Una base de datos", "Un servidor"], "respuesta_correcta": "Lenguaje de marcado"},
        {"enunciado": "¿Para qué sirve CSS?", "opciones": ["Estilos y diseño", "Estructura", "Base de datos", "Lógica"], "respuesta_correcta": "Estilos y diseño"},
        {"enunciado": "¿Qué es Flexbox?", "opciones": ["Modelo de layout", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Modelo de layout"},
        {"enunciado": "¿Qué es responsive design?", "opciones": ["Adaptación a dispositivos", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Adaptación a dispositivos"},
        {"enunciado": "¿Qué es un selector CSS?", "opciones": ["Identifica elementos HTML", "Una función", "Una variable", "Un error"], "respuesta_correcta": "Identifica elementos HTML"}
    ],
    "Marketing Digital": [
        {"enunciado": "¿Qué es SEO?", "opciones": ["Optimización para motores de búsqueda", "Una red social", "Un email", "Una página web"], "respuesta_correcta": "Optimización para motores de búsqueda"},
        {"enunciado": "¿Qué es un buyer persona?", "opciones": ["Representación del cliente ideal", "Un producto", "Una página web", "Un email"], "respuesta_correcta": "Representación del cliente ideal"},
        {"enunciado": "¿Qué es el marketing de contenidos?", "opciones": ["Creación de contenido valioso", "Vender productos", "Una red social", "Un email"], "respuesta_correcta": "Creación de contenido valioso"},
        {"enunciado": "¿Qué es CRO?", "opciones": ["Optimización de conversiones", "Una red social", "Un email", "Una página web"], "respuesta_correcta": "Optimización de conversiones"},
        {"enunciado": "¿Qué es el email marketing?", "opciones": ["Envío de emails promocionales", "Una red social", "Una página web", "Un producto"], "respuesta_correcta": "Envío de emails promocionales"}
    ],
    "Data Science": [
        {"enunciado": "¿Qué es Pandas?", "opciones": ["Librería de análisis de datos", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Librería de análisis de datos"},
        {"enunciado": "¿Qué es Machine Learning?", "opciones": ["Aprendizaje automático", "Una base de datos", "Un lenguaje", "Un servidor"], "respuesta_correcta": "Aprendizaje automático"},
        {"enunciado": "¿Qué es un DataFrame?", "opciones": ["Estructura de datos tabular", "Una función", "Una variable", "Un error"], "respuesta_correcta": "Estructura de datos tabular"},
        {"enunciado": "¿Qué es la visualización de datos?", "opciones": ["Representación gráfica de datos", "Una base de datos", "Un lenguaje", "Un servidor"], "respuesta_correcta": "Representación gráfica de datos"},
        {"enunciado": "¿Qué es SQL?", "opciones": ["Lenguaje de consultas", "Un lenguaje de programación", "Una base de datos", "Un servidor"], "respuesta_correcta": "Lenguaje de consultas"}
    ],
    "Inteligencia Artificial": [
        {"enunciado": "¿Qué es una red neuronal?", "opciones": ["Modelo inspirado en el cerebro", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Modelo inspirado en el cerebro"},
        {"enunciado": "¿Qué es Deep Learning?", "opciones": ["Redes neuronales profundas", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Redes neuronales profundas"},
        {"enunciado": "¿Qué es TensorFlow?", "opciones": ["Framework de IA", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Framework de IA"},
        {"enunciado": "¿Qué es un modelo predictivo?", "opciones": ["Modelo que predice resultados", "Una base de datos", "Un lenguaje", "Un servidor"], "respuesta_correcta": "Modelo que predice resultados"},
        {"enunciado": "¿Qué es NLP?", "opciones": ["Procesamiento de lenguaje natural", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Procesamiento de lenguaje natural"}
    ],
    "Desarrollo Mobile": [
        {"enunciado": "¿Qué es Flutter?", "opciones": ["Framework de desarrollo mobile", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Framework de desarrollo mobile"},
        {"enunciado": "¿Qué es React Native?", "opciones": ["Framework de desarrollo mobile", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Framework de desarrollo mobile"},
        {"enunciado": "¿Qué es una app nativa?", "opciones": ["Desarrollada para una plataforma específica", "Una web", "Una base de datos", "Un servidor"], "respuesta_correcta": "Desarrollada para una plataforma específica"},
        {"enunciado": "¿Qué es el estado en una app?", "opciones": ["Datos que cambian en la interfaz", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Datos que cambian en la interfaz"},
        {"enunciado": "¿Qué es una API?", "opciones": ["Interfaz de programación", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Interfaz de programación"}
    ],
    "Cloud Computing": [
        {"enunciado": "¿Qué es AWS?", "opciones": ["Servicio de computación en la nube", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Servicio de computación en la nube"},
        {"enunciado": "¿Qué es IaaS?", "opciones": ["Infraestructura como servicio", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Infraestructura como servicio"},
        {"enunciado": "¿Qué es un servidor?", "opciones": ["Computadora que proporciona servicios", "Un lenguaje", "Una base de datos", "Una app"], "respuesta_correcta": "Computadora que proporciona servicios"},
        {"enunciado": "¿Qué es Docker?", "opciones": ["Plataforma de contenedores", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Plataforma de contenedores"},
        {"enunciado": "¿Qué es Kubernetes?", "opciones": ["Orquestador de contenedores", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Orquestador de contenedores"}
    ],
    "Ciberseguridad": [
        {"enunciado": "¿Qué es un firewall?", "opciones": ["Filtro de tráfico de red", "Un virus", "Un lenguaje", "Una base de datos"], "respuesta_correcta": "Filtro de tráfico de red"},
        {"enunciado": "¿Qué es el phishing?", "opciones": ["Ataque de ingeniería social", "Un virus", "Un lenguaje", "Una base de datos"], "respuesta_correcta": "Ataque de ingeniería social"},
        {"enunciado": "¿Qué es un malware?", "opciones": ["Software malicioso", "Un firewall", "Un lenguaje", "Una base de datos"], "respuesta_correcta": "Software malicioso"},
        {"enunciado": "¿Qué es la encriptación?", "opciones": ["Protección de datos", "Un virus", "Un lenguaje", "Una base de datos"], "respuesta_correcta": "Protección de datos"},
        {"enunciado": "¿Qué es un VPN?", "opciones": ["Red privada virtual", "Un virus", "Un lenguaje", "Una base de datos"], "respuesta_correcta": "Red privada virtual"}
    ],
    "DevOps": [
        {"enunciado": "¿Qué es CI/CD?", "opciones": ["Integración y despliegue continuo", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Integración y despliegue continuo"},
        {"enunciado": "¿Qué es Jenkins?", "opciones": ["Herramienta de automatización", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Herramienta de automatización"},
        {"enunciado": "¿Qué es Git?", "opciones": ["Sistema de control de versiones", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Sistema de control de versiones"},
        {"enunciado": "¿Qué es un pipeline?", "opciones": ["Flujo de trabajo automatizado", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Flujo de trabajo automatizado"},
        {"enunciado": "¿Qué es IaC?", "opciones": ["Infraestructura como código", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Infraestructura como código"}
    ],
    "Blockchain": [
        {"enunciado": "¿Qué es blockchain?", "opciones": ["Cadena de bloques", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Cadena de bloques"},
        {"enunciado": "¿Qué es Bitcoin?", "opciones": ["Criptomoneda", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Criptomoneda"},
        {"enunciado": "¿Qué es un smart contract?", "opciones": ["Contrato inteligente", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Contrato inteligente"},
        {"enunciado": "¿Qué es Ethereum?", "opciones": ["Plataforma de blockchain", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Plataforma de blockchain"},
        {"enunciado": "¿Qué es un token?", "opciones": ["Activo digital", "Un lenguaje", "Una base de datos", "Un servidor"], "respuesta_correcta": "Activo digital"}
    ]
}

# Preguntas genéricas para cursos que no coinciden
PREGUNTAS_GENERICAS = [
    {"enunciado": "¿Cuál es el objetivo principal del curso?", "opciones": ["Aprender conceptos básicos", "Dominio avanzado", "Certificación", "Proyecto práctico"], "respuesta_correcta": "Aprender conceptos básicos"},
    {"enunciado": "¿Qué herramienta se utiliza en este curso?", "opciones": ["Software especializado", "Lenguaje de programación", "Base de datos", "Servidor"], "respuesta_correcta": "Software especializado"},
    {"enunciado": "¿Cuál es la metodología de enseñanza?", "opciones": ["Teórico-práctica", "Solo teoría", "Solo práctica", "Autoestudio"], "respuesta_correcta": "Teórico-práctica"},
    {"enunciado": "¿Qué se necesita para aprobar?", "opciones": ["Completar todas las lecciones", "Solo leer", "Solo practicar", "Nada"], "respuesta_correcta": "Completar todas las lecciones"},
    {"enunciado": "¿Cuál es el nivel del curso?", "opciones": ["Principiante", "Intermedio", "Avanzado", "Experto"], "respuesta_correcta": "Principiante"}
]

def obtener_preguntas_curso(nombre_curso):
    """Obtiene preguntas según la categoría del curso"""
    nombre_lower = nombre_curso.lower()
    
    for categoria in PREGUNTAS_POR_CATEGORIA:
        if categoria.lower() in nombre_lower:
            return PREGUNTAS_POR_CATEGORIA[categoria]
    
    return PREGUNTAS_GENERICAS

def generar_examenes_por_nivel():
    """Genera 1 examen por nivel SOLO para los niveles especificados"""
    print("=" * 70)
    print("GENERADOR DE EXÁMENES POR NIVEL (ESPECÍFICOS)")
    print("=" * 70)
    print()
    
    total_examenes = 0
    
    for i, nivel_id_str in enumerate(NIVELES_ESPECIFICOS, 1):
        try:
            # Obtener el nivel
            nivel_id = ObjectId(nivel_id_str)
            nivel = niveles_collection.find_one({"_id": nivel_id})
            
            if not nivel:
                print(f"[{i}/{len(NIVELES_ESPECIFICOS)}]  Nivel no encontrado: {nivel_id_str}")
                continue
            
            curso_id = nivel["curso_id"]
            nivel_titulo = nivel["titulo"]
            
            # Obtener el curso para saber la categoría
            curso = cursos_collection.find_one({"_id": ObjectId(curso_id)})
            if not curso:
                print(f"[{i}/{len(NIVELES_ESPECIFICOS)}]  Curso no encontrado para nivel: {nivel_titulo}")
                continue
                
            nombre_curso = curso.get("nombre", "")
            
            print(f"[{i}/{len(NIVELES_ESPECIFICOS)}] Generando examen para: {nivel_titulo}")
            print(f"    Curso: {nombre_curso[:50]}...")
            
            # Obtener preguntas según la categoría
            preguntas = obtener_preguntas_curso(nombre_curso)
            
            # Crear examen SOLO por nivel (sin leccion_id)
            examen = {
                "curso_id": curso_id,
                "nivel_id": nivel_id,
                "leccion_id": None,  # SIN lección - solo por nivel
                "titulo": f"Examen: {nivel_titulo}",
                "fecha": "2026-07-14",
                "preguntas": preguntas
            }
            
            examenes_collection.insert_one(examen)
            total_examenes += 1
            print(f"    ✓ Examen creado con {len(preguntas)} preguntas")
            
        except Exception as e:
            print(f"[{i}/{len(NIVELES_ESPECIFICOS)}]  Error: {e}")
    
    print()
    print("=" * 70)
    print("✓ PROCESO COMPLETADO")
    print(f"✓ Total exámenes creados: {total_examenes}")
    print("=" * 70)
    print()
    print("Características:")
    print("  - Exámenes SOLO por nivel (no por lección)")
    print("  - Cada examen tiene 5 preguntas de opción múltiple")
    print("  - Preguntas específicas según la categoría del curso")
    print("  - Cuentan en el progreso del estudiante")
    print()
    print("Ahora puedes:")
    print("1. Ver los exámenes en el panel del profesor")
    print("2. Los alumnos pueden realizar los exámenes desde la vista del curso")
    print("3. Los exámenes aparecen en la sección de evaluaciones de cada lección")

if __name__ == "__main__":
    generar_examenes_por_nivel()