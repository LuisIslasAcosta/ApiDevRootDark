from config.config import niveles_collection, lecciones_collection, cursos_collection

curso_id = "6a55c171ce2d5284c8bb09e3"

print("=== VERIFICACIÓN DE DATOS ===\n")

# Verificar niveles
niveles = list(niveles_collection.find({"curso_id": curso_id}))
print(f"Niveles encontrados para el curso: {len(niveles)}")
for n in niveles:
    print(f"  - {n['titulo']} (orden: {n['orden']})")

print()

# Verificar lecciones
lecciones = list(lecciones_collection.find({"curso_id": curso_id}))
print(f"Lecciones encontradas para el curso: {len(lecciones)}")
for l in lecciones[:5]:  # Mostrar solo las primeras 5
    print(f"  - {l['titulo']} (nivel_id: {l['nivel_id']})")

if len(lecciones) > 5:
    print(f"  ... y {len(lecciones) - 5} más")

print("\n=== PRUEBA DE ENDPOINT ===")
print(f"URL: http://127.0.0.1:5000/api/niveles/curso/{curso_id}")
print(f"URL: http://127.0.0.1:5000/api/niveles/curso/{curso_id}/con_lecciones")