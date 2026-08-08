import requests
import json

curso_id = "6a55c171ce2d5284c8bb09e3"

print("=== PRUEBA DE ENDPOINTS ===\n")

# Probar endpoint de niveles
url_niveles = f"http://127.0.0.1:5000/api/niveles/curso/{curso_id}"
print(f"GET {url_niveles}")
try:
    response = requests.get(url_niveles)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        niveles = response.json()
        print(f"✓ Niveles encontrados: {len(niveles)}")
        for nivel in niveles:
            print(f"  - {nivel['titulo']} (orden: {nivel['orden']})")
    else:
        print(f"✗ Error: {response.text}")
except Exception as e:
    print(f"✗ Error de conexión: {e}")

print()

# Probar endpoint de niveles con lecciones
url_niveles_lecciones = f"http://127.0.0.1:5000/api/niveles/curso/{curso_id}/con_lecciones"
print(f"GET {url_niveles_lecciones}")
try:
    response = requests.get(url_niveles_lecciones)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        niveles = response.json()
        print(f"✓ Niveles encontrados: {len(niveles)}")
        for nivel in niveles:
            print(f"  - {nivel['titulo']}")
            print(f"    Lecciones: {len(nivel.get('lecciones', []))}")
            for leccion in nivel.get('lecciones', [])[:2]:
                print(f"      * {leccion['titulo']}")
    else:
        print(f"✗ Error: {response.text}")
except Exception as e:
    print(f"✗ Error de conexión: {e}")

print("\n=== PRUEBA COMPLETADA ===")