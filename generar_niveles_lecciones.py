"""
Script para generar niveles y lecciones de prueba
Genera contenido educativo realista para 40 cursos
NO usa Faker - datos predefinidos y variados
"""
from config.config import niveles_collection, lecciones_collection, cursos_collection
from bson.objectid import ObjectId
import random

# ==================== DATOS PREDEFINIDOS ====================

# Tipos de cursos y sus niveles/lecciones asociadas
CONTENIDO_CURSOS = {
    "Programación": {
        "niveles": [
            {
                "titulo": "Nivel 1: Fundamentos",
                "orden": 1,
                "lecciones": [
                    {"titulo": "Introducción a la programación", "contenido": "Conceptos básicos de programación, algoritmos y lógica computacional. Aprenderás a pensar como un programador."},
                    {"titulo": "Variables y tipos de datos", "contenido": "Declaración de variables, tipos de datos primitivos, operadores y expresiones básicas."},
                    {"titulo": "Estructuras de control", "contenido": "Condicionales if/else, bucles for y while, control de flujo del programa."}
                ]
            },
            {
                "titulo": "Nivel 2: Intermedio",
                "orden": 2,
                "lecciones": [
                    {"titulo": "Funciones y modularidad", "contenido": "Definición de funciones, parámetros, retorno de valores, alcance de variables."},
                    {"titulo": "Arrays y listas", "contenido": "Manipulación de colecciones de datos, iteración, métodos comunes de arrays."},
                    {"titulo": "Manejo de errores", "contenido": "Try-catch, excepciones, debugging básico y manejo de casos edge."}
                ]
            },
            {
                "titulo": "Nivel 3: Avanzado",
                "orden": 3,
                "lecciones": [
                    {"titulo": "Programación orientada a objetos", "contenido": "Clases, objetos, herencia, polimorfismo, encapsulamiento."},
                    {"titulo": "Algoritmos avanzados", "contenido": "Ordenamiento, búsqueda, recursividad, complejidad algorítmica."},
                    {"titulo": "Proyecto final", "contenido": "Desarrollo de una aplicación completa integrando todos los conceptos aprendidos."}
                ]
            }
        ]
    },
    "Diseño Web": {
        "niveles": [
            {
                "titulo": "Nivel 1: HTML y CSS Básico",
                "orden": 1,
                "lecciones": [
                    {"titulo": "Estructura HTML", "contenido": "Etiquetas básicas, estructura del documento, semántica HTML5."},
                    {"titulo": "Selectores CSS", "contenido": "Selectores por clase, ID, atributos, pseudo-clases y pseudo-elementos."},
                    {"titulo": "Modelo de caja", "contenido": "Margin, padding, border, box-sizing, display y position."}
                ]
            },
            {
                "titulo": "Nivel 2: CSS Intermedio",
                "orden": 2,
                "lecciones": [
                    {"titulo": "Flexbox", "contenido": "Contenedores flexibles, dirección, alineación, orden y flexibilidad."},
                    {"titulo": "CSS Grid", "contenido": "Grid layout, columnas, filas, áreas, responsive design con CSS Grid."},
                    {"titulo": "Responsive Design", "contenido": "Media queries, mobile-first, breakpoints y adaptabilidad."}
                ]
            },
            {
                "titulo": "Nivel 3: Diseño Avanzado",
                "orden": 3,
                "lecciones": [
                    {"titulo": "Animaciones CSS", "contenido": "Transiciones, keyframes, transformaciones, animaciones complejas."},
                    {"titulo": "Accesibilidad web", "contenido": "ARIA labels, contraste, navegación por teclado, screen readers."},
                    {"titulo": "Optimización", "contenido": "Performance, lazy loading, minificación, mejores prácticas."}
                ]
            }
        ]
    },
    "Marketing Digital": {
        "niveles": [
            {
                "titulo": "Nivel 1: Fundamentos del Marketing",
                "orden": 1,
                "lecciones": [
                    {"titulo": "¿Qué es el marketing digital?", "contenido": "Definición, historia, evolución y diferencias con marketing tradicional."},
                    {"titulo": "Buyer persona", "contenido": "Investigación de mercado, creación de buyer persona, journey del cliente."},
                    {"titulo": "Canales digitales", "contenido": "Redes sociales, email marketing, SEO, SEM, contenido orgánico vs pagado."}
                ]
            },
            {
                "titulo": "Nivel 2: Estrategias",
                "orden": 2,
                "lecciones": [
                    {"titulo": "Marketing de contenidos", "contenido": "Creación de contenido valioso, calendario editorial, storytelling."},
                    {"titulo": "Redes sociales", "contenido": "Estrategia por plataforma, engagement, community management."},
                    {"titulo": "Email marketing", "contenido": "Listas de suscriptores, automatizaciones, copywriting, métricas."}
                ]
            },
            {
                "titulo": "Nivel 3: Análisis y Optimización",
                "orden": 3,
                "lecciones": [
                    {"titulo": "Analítica web", "contenido": "Google Analytics, métricas clave, dashboards, toma de decisiones."},
                    {"titulo": "SEO avanzado", "contenido": "SEO técnico, link building, optimización on-page y off-page."},
                    {"titulo": "CRO y optimización", "contenido": "Conversion Rate Optimization, A/B testing, mejora continua."}
                ]
            }
        ]
    },
    "Data Science": {
        "niveles": [
            {
                "titulo": "Nivel 1: Introducción a Data Science",
                "orden": 1,
                "lecciones": [
                    {"titulo": "¿Qué es Data Science?", "contenido": "Definición, aplicaciones, ciclo de vida de proyectos de datos."},
                    {"titulo": "Estadística básica", "contenido": "Media, mediana, moda, desviación estándar, distribuciones."},
                    {"titulo": "Python para datos", "contenido": "NumPy, Pandas, manipulación de DataFrames, análisis exploratorio."}
                ]
            },
            {
                "titulo": "Nivel 2: Análisis y Visualización",
                "orden": 2,
                "lecciones": [
                    {"titulo": "Visualización de datos", "contenido": "Matplotlib, Seaborn, Plotly, creación de gráficos efectivos."},
                    {"titulo": "Análisis exploratorio", "contenido": "EDA, detección de outliers, correlaciones, insights."},
                    {"titulo": "SQL para análisis", "contenido": "Consultas avanzadas, joins, agregaciones, ventanas."}
                ]
            },
            {
                "titulo": "Nivel 3: Machine Learning",
                "orden": 3,
                "lecciones": [
                    {"titulo": "Introducción a ML", "contenido": "Tipos de aprendizaje, supervised vs unsupervised, scikit-learn."},
                    {"titulo": "Modelos predictivos", "contenido": "Regresión, clasificación, árboles de decisión, random forest."},
                    {"titulo": "Proyecto integrador", "contenido": "Pipeline completo: desde datos hasta modelo deployado."}
                ]
            }
        ]
    },
    "Inteligencia Artificial": {
        "niveles": [
            {
                "titulo": "Nivel 1: Fundamentos de IA",
                "orden": 1,
                "lecciones": [
                    {"titulo": "Historia de la IA", "contenido": "Evolución de la IA, hitos importantes, invierno de la IA, deep learning."},
                    {"titulo": "Redes neuronales básicas", "contenido": "Perceptrón, capas, activaciones, backpropagation."},
                    {"titulo": "Frameworks de IA", "contenido": "TensorFlow, PyTorch, comparación, instalación y configuración."}
                ]
            },
            {
                "titulo": "Nivel 2: Deep Learning",
                "orden": 2,
                "lecciones": [
                    {"titulo": "CNNs para imágenes", "contenido": "Convoluciones, pooling, arquitecturas CNN, transfer learning."},
                    {"titulo": "RNNs y NLP", "contenido": "Procesamiento de lenguaje natural, embeddings, transformers."},
                    {"titulo": "Optimización", "contenido": "Gradient descent, optimizadores, regularización, dropout."}
                ]
            },
            {
                "titulo": "Nivel 3: Aplicaciones Avanzadas",
                "orden": 3,
                "lecciones": [
                    {"titulo": "GPT y LLMs", "contenido": "Arquitectura transformer, fine-tuning, prompt engineering."},
                    {"titulo": "Computer Vision", "contenido": "Detección de objetos, segmentación, YOLO, aplicaciones."},
                    {"titulo": "IA generativa", "contenido": "Stable Diffusion, DALL-E, generación de contenido ética."}
                ]
            }
        ]
    },
    "Desarrollo Mobile": {
        "niveles": [
            {
                "titulo": "Nivel 1: Fundamentos Mobile",
                "orden": 1,
                "lecciones": [
                    {"titulo": "Arquitectura mobile", "contenido": "Native vs cross-platform, ventajas y desventajas de cada enfoque."},
                    {"titulo": "UI/UX móvil", "contenido": "Principios de diseño móvil, patrones de navegación, guidelines."},
                    {"titulo": "Primera app", "contenido": "Configuración del entorno, Hola Mundo, estructura del proyecto."}
                ]
            },
            {
                "titulo": "Nivel 2: Desarrollo Intermedio",
                "orden": 2,
                "lecciones": [
                    {"titulo": "Navegación", "contenido": "Stack navigation, tab navigation, deep linking, routing."},
                    {"titulo": "Estado y datos", "contenido": "State management, Context API, Redux, persistencia local."},
                    {"titulo": "APIs y backend", "contenido": "Consumo de APIs, autenticación, manejo de errores, offline mode."}
                ]
            },
            {
                "titulo": "Nivel 3: Publicación y Optimización",
                "orden": 3,
                "lecciones": [
                    {"titulo": "Testing", "contenido": "Unit tests, integration tests, testing en dispositivos reales."},
                    {"titulo": "Performance", "contenido": "Optimización de imágenes, bundle size, memoria, battery usage."},
                    {"titulo": "Publicación", "contenido": "App Store, Google Play, CI/CD, métricas y analytics."}
                ]
            }
        ]
    },
    "Cloud Computing": {
        "niveles": [
            {
                "titulo": "Nivel 1: Conceptos Básicos",
                "orden": 1,
                "lecciones": [
                    {"titulo": "¿Qué es la nube?", "contenido": "IaaS, PaaS, SaaS, modelos de servicio, proveedores principales."},
                    {"titulo": "AWS Fundamentals", "contenido": "EC2, S3, IAM, VPC, región y zonas de disponibilidad."},
                    {"titulo": "Azure Fundamentals", "contenido": "Virtual Machines, Blob Storage, Azure AD, Resource Groups."}
                ]
            },
            {
                "titulo": "Nivel 2: Servicios y Arquitectura",
                "orden": 2,
                "lecciones": [
                    {"titulo": "Bases de datos en la nube", "contenido": "RDS, DynamoDB, Cosmos DB, elección según el caso de uso."},
                    {"titulo": "Serverless", "contenido": "Lambda, Functions, API Gateway, ventajas y casos de uso."},
                    {"titulo": "Contenedores", "contenido": "Docker, ECS/EKS, orquestación, microservicios."}
                ]
            },
            {
                "titulo": "Nivel 3: Arquitectura y Seguridad",
                "orden": 3,
                "lecciones": [
                    {"titulo": "Arquitectura cloud", "contenido": "Well-Architected Framework, alta disponibilidad, escalabilidad."},
                    {"titulo": "Seguridad", "contenido": "IAM, encryption, compliance, best practices de seguridad."},
                    {"titulo": "Monitoreo", "contenido": "CloudWatch, Application Insights, logging, alertas."}
                ]
            }
        ]
    },
    "Ciberseguridad": {
        "niveles": [
            {
                "titulo": "Nivel 1: Fundamentos",
                "orden": 1,
                "lecciones": [
                    {"titulo": "Introducción a ciberseguridad", "contenido": "Tipos de amenazas, CIA triad, landscape de seguridad actual."},
                    {"titulo": "Redes y protocolos", "contenido": "TCP/IP, HTTP/HTTPS, DNS, firewalls, VPNs."},
                    {"titulo": "Criptografía básica", "contenido": "Encriptación simétrica y asimétrica, hashing, certificados SSL."}
                ]
            },
            {
                "titulo": "Nivel 2: Ataques y Defensas",
                "orden": 2,
                "lecciones": [
                    {"titulo": "Tipos de ataques", "contenido": "Phishing, malware, DDoS, SQL injection, XSS, CSRF."},
                    {"titulo": "Pentesting", "contenido": "Metodologías, herramientas, ethical hacking, reportes."},
                    {"titulo": "Defensa en profundidad", "contenido": "Capa de seguridad, WAF, IDS/IPS, SIEM."}
                ]
            },
            {
                "titulo": "Nivel 3: Seguridad Avanzada",
                "orden": 3,
                "lecciones": [
                    {"titulo": "Cumplimiento normativo", "contenido": "GDPR, HIPAA, PCI DSS, ISO 27001, auditorías."},
                    {"titulo": "Incident response", "contenido": "Plan de respuesta, forense digital, recuperación, lecciones aprendidas."},
                    {"titulo": "Security operations", "contenido": "SOC, threat hunting, automatización, inteligencia de amenazas."}
                ]
            }
        ]
    },
    "DevOps": {
        "niveles": [
            {
                "titulo": "Nivel 1: Cultura y Principios",
                "orden": 1,
                "lecciones": [
                    {"titulo": "¿Qué es DevOps?", "contenido": "Historia, cultura, CALMS, DevOps vs traditional IT."},
                    {"titulo": "Control de versiones", "contenido": "Git, branching strategies, pull requests, code reviews."},
                    {"titulo": "CI/CD básico", "contenido": "Integración continua, pipelines, automatización básica."}
                ]
            },
            {
                "titulo": "Nivel 2: Herramientas",
                "orden": 2,
                "lecciones": [
                    {"titulo": "Jenkins y pipelines", "contenido": "Configuración, jobs, declarative pipeline, plugins."},
                    {"titulo": "Terraform e IaC", "contenido": "Infrastructure as Code, providers, state management."},
                    {"titulo": "Monitoreo", "contenido": "Prometheus, Grafana, logs centralizados, alertas."}
                ]
            },
            {
                "titulo": "Nivel 3: Orquestación",
                "orden": 3,
                "lecciones": [
                    {"titulo": "Kubernetes avanzado", "contenido": "Helm, operators, service mesh, multi-cluster."},
                    {"titulo": "GitOps", "contenido": "ArgoCD, Flux, declarative deployments, rollbacks."},
                    {"titulo": "SRE practices", "contenido": "SLI/SLO/SLA, error budgets, incident management."}
                ]
            }
        ]
    },
    "Blockchain": {
        "niveles": [
            {
                "titulo": "Nivel 1: Fundamentos Blockchain",
                "orden": 1,
                "lecciones": [
                    {"titulo": "¿Qué es blockchain?", "contenido": "Distributed ledger, bloques, hashing, consenso."},
                    {"titulo": "Criptomonedas", "contenido": "Bitcoin, Ethereum, tokens, wallets, exchanges."},
                    {"titulo": "Smart contracts", "contenido": "Concepto, Solidity básico, Ethereum Virtual Machine."}
                ]
            },
            {
                "titulo": "Nivel 2: Desarrollo",
                "orden": 2,
                "lecciones": [
                    {"titulo": "Solidity intermedio", "contenido": "Funciones, modifiers, events, inheritance."},
                    {"titulo": "DApps", "contenido": "Web3.js, Ethers.js, conexión frontend-blockchain."},
                    {"titulo": "Testing", "contenido": "Truffle, Hardhat, testing frameworks, coverage."}
                ]
            },
            {
                "titulo": "Nivel 3: Producción",
                "orden": 3,
                "lecciones": [
                    {"titulo": "Deploy y seguridad", "contenido": "Mainnet deployment, auditorías, vulnerabilidades comunes."},
                    {"titulo": "NFTs y tokens", "contenido": "ERC-721, ERC-20, metadata, marketplaces."},
                    {"titulo": "DeFi", "contenido": "Liquidity pools, staking, yield farming, protocolos."}
                ]
            }
        ]
    }
}

# Cursos genéricos para categorías no específicas
CONTENIDO_GENERICO = {
    "niveles": [
        {
            "titulo": "Nivel 1: Introducción",
            "orden": 1,
            "lecciones": [
                {"titulo": "Bienvenida al curso", "contenido": "Presentación del curso, objetivos, qué aprenderás y cómo está estructurado."},
                {"titulo": "Conceptos básicos", "contenido": "Fundamentos esenciales, terminología clave, contexto general del tema."},
                {"titulo": "Primeros pasos", "contenido": "Configuración inicial, herramientas necesarias, primer ejercicio práctico."}
            ]
        },
        {
            "titulo": "Nivel 2: Desarrollo",
            "orden": 2,
            "lecciones": [
                {"titulo": "Temas intermedios", "contenido": "Profundización en conceptos clave, técnicas avanzadas básicas."},
                {"titulo": "Práctica guiada", "contenido": "Ejercicios paso a paso, casos de uso reales, mejores prácticas."},
                {"titulo": "Herramientas profesionales", "contenido": "Software especializado, workflows, productividad."}
            ]
        },
        {
            "titulo": "Nivel 3: Dominio",
            "orden": 3,
            "lecciones": [
                {"titulo": "Temas avanzados", "contenido": "Conceptos complejos, optimización, técnicas expertas."},
                {"titulo": "Proyecto práctico", "contenido": "Aplicación real de todos los conocimientos, portfolio piece."},
                {"titulo": "Próximos pasos", "contenido": "Recursos adicionales, comunidad, certificaciones, carrera profesional."}
            ]
        }
    ]
}

# ==================== FUNCIONES ====================

def obtener_contenido_curso(nombre_curso):
    """Determina qué contenido usar según el nombre del curso"""
    nombre_lower = nombre_curso.lower()
    
    for categoria in CONTENIDO_CURSOS:
        if categoria.lower() in nombre_lower:
            return CONTENIDO_CURSOS[categoria]
    
    # Si no encuentra coincidencia, usar contenido genérico con variaciones
    return CONTENIDO_GENERICO

def generar_niveles_lecciones(curso_id, nombre_curso):
    """Genera niveles y lecciones para un curso específico"""
    contenido = obtener_contenido_curso(nombre_curso)
    niveles_creados = []
    
    for nivel_data in contenido["niveles"]:
        # Crear nivel - descripcion vacía como en el ejemplo
        nivel = {
            "curso_id": curso_id,
            "titulo": nivel_data["titulo"],
            "descripcion": "",  # String vacío como en el ejemplo
            "orden": nivel_data["orden"]
            # fecha_creacion se agrega automáticamente por MongoDB
        }
        
        resultado_nivel = niveles_collection.insert_one(nivel)
        nivel_id = resultado_nivel.inserted_id
        
        # Crear lecciones para este nivel
        lecciones_creadas = []
        for i, leccion_data in enumerate(nivel_data["lecciones"], 1):
            leccion = {
                "curso_id": curso_id,
                "nivel_id": nivel_id,
                "titulo": leccion_data["titulo"],
                "contenido": leccion_data["contenido"],
                "archivos": []  # Array vacío como en el ejemplo
            }
            
            resultado_leccion = lecciones_collection.insert_one(leccion)
            leccion["_id"] = resultado_leccion.inserted_id
            lecciones_creadas.append(leccion)
        
        niveles_creados.append({
            "nivel": nivel,
            "lecciones": lecciones_creadas
        })
    
    return niveles_creados

def main():
    print("=" * 70)
    print("GENERADOR DE NIVELES Y LECCIONES")
    print("=" * 70)
    print()
    
    # Obtener todos los cursos
    cursos = list(cursos_collection.find())
    
    if not cursos:
        print(" No se encontraron cursos en la base de datos")
        print("   Ejecuta primero generar_cursos_prueba.py")
        return
    
    print(f"✓ Cursos encontrados: {len(cursos)}")
    print()
    
    total_niveles = 0
    total_lecciones = 0
    
    for i, curso in enumerate(cursos, 1):
        curso_id = curso["_id"]
        nombre_curso = curso.get("nombre", "Sin nombre")
        
        print(f"[{i}/{len(cursos)}] Procesando: {nombre_curso[:50]}...")
        
        try:
            estructura = generar_niveles_lecciones(curso_id, nombre_curso)
            
            niveles_count = len(estructura)
            lecciones_count = sum(len(nivel["lecciones"]) for nivel in estructura)
            
            total_niveles += niveles_count
            total_lecciones += lecciones_count
            
            print(f"    ✓ {niveles_count} niveles, {lecciones_count} lecciones creadas")
            
        except Exception as e:
            print(f"     Error: {e}")
    
    print()
    print("=" * 70)
    print("✓ PROCESO COMPLETADO")
    print(f"✓ Total niveles creados: {total_niveles}")
    print(f"✓ Total lecciones creadas: {total_lecciones}")
    print(f"✓ Promedio: {total_lecciones / len(cursos):.1f} lecciones por curso")
    print("=" * 70)
    print()
    print("Estructura creada:")
    print("  - Cada curso tiene 3 niveles")
    print("  - Cada nivel tiene 3 lecciones")
    print("  - Contenido educativo realista y variado")
    print()
    print("Ahora puedes:")
    print("1. Ver los niveles y lecciones en el panel del profesor")
    print("2. Agregar archivos multimedia a las lecciones")
    print("3. Crear exámenes asociados a las lecciones")

if __name__ == "__main__":
    main()