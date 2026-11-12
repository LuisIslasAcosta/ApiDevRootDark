"""Borra el PRIMER intento de examen de los 20 alumnos de prueba (alumnoNN.drd@example.com)
cuando tienen dos intentos del mismo examen. Esos primeros intentos se enviaron mal (respuestas al azar).
Uso:  venv/bin/python scripts/borrar_primer_intento_prueba.py            (solo muestra)
      venv/bin/python scripts/borrar_primer_intento_prueba.py --aplicar  (borra)
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import usuarios_collection, respuestas_collection

aplicar = "--aplicar" in sys.argv
alumnos = list(usuarios_collection.find({"email": {"$regex": r"^alumno\d\d\.drd@example\.com$"}}, {"_id": 1}))
borrar = []
for a in alumnos:
    por_examen = {}
    for r in respuestas_collection.find({"alumno_id": a["_id"]}).sort("_id", 1):
        por_examen.setdefault(r["examen_id"], []).append(r)
    for lista in por_examen.values():
        if len(lista) >= 2:
            borrar.append(lista[0]["_id"])
print(f"Alumnos de prueba: {len(alumnos)} | intentos a borrar: {len(borrar)}")
if aplicar and borrar:
    print("Borrados:", respuestas_collection.delete_many({"_id": {"$in": borrar}}).deleted_count)
elif not aplicar:
    print("Nada se borró. Ejecuta con --aplicar para borrar.")
