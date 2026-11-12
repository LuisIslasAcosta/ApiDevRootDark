"""
Registra los 20 usuarios de prueba de DevRootDark usando el endpoint /api/registrar.
Uso:  python registrar_usuarios_prueba.py
Necesita el archivo usuarios_prueba.json en la misma carpeta. Solo usa la biblioteca estándar.
"""
import json
import time
import urllib.request
import urllib.error
from pathlib import Path

import sys

# URL de tu API (se puede cambiar pasándola como argumento):
#   python registrar_usuarios_prueba.py https://otra-url/api
BASE = (sys.argv[1] if len(sys.argv) > 1 else "https://luis444.tailceb0e5.ts.net/api").rstrip("/")
API_URL = f"{BASE}/registrar"
usuarios = json.loads((Path(__file__).parent / "usuarios_prueba.json").read_text(encoding="utf-8"))


def registrar(usuario):
    datos = json.dumps(usuario).encode("utf-8")
    req = urllib.request.Request(API_URL, data=datos, method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.status, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode("utf-8") or "{}")


print(f"Registrando usuarios en {API_URL} ...")
ok = 0
for i, u in enumerate(usuarios, 1):
    try:
        status, resp = registrar(u)
    except Exception as e:  # red caída o timeout
        status, resp = "ERROR", {"mensaje": str(e)}
    marca = "OK " if status in (200, 201) else "ERR"
    if marca == "OK ":
        ok += 1
    print(f"[{marca}] {i:02d} {u['email']:<28} -> {status} {resp.get('mensaje', resp)}")
    time.sleep(0.5)

print(f"\nRegistrados: {ok} de {len(usuarios)}")
