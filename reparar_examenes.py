"""
Repara los exámenes creados antes de la corrección, que se guardaron con los
campos en desorden (titulo = id de la lección, fecha = título, leccion_id = fecha).

Uso (en la carpeta de la API, con el venv activado):
    python reparar_examenes.py           -> solo muestra qué cambiaría
    python reparar_examenes.py --aplicar -> guarda los cambios
"""
import re
import sys
from bson.objectid import ObjectId
from config.config import examenes_collection, lecciones_collection

FECHA = re.compile(r"^\d{4}-\d{2}-\d{2}")
aplicar = "--aplicar" in sys.argv
reparados = 0

for ex in examenes_collection.find():
    titulo = str(ex.get("titulo") or "")
    fecha = str(ex.get("fecha") or "")
    leccion = str(ex.get("leccion_id") or "")

    # Patrón del error: el "título" es un ObjectId y la "lección" es una fecha
    if ObjectId.is_valid(titulo) and FECHA.match(leccion):
        nuevo = {"titulo": fecha, "fecha": leccion, "leccion_id": titulo}
        if not ex.get("nivel_id"):
            lec = lecciones_collection.find_one({"_id": ObjectId(titulo)})
            if lec and lec.get("nivel_id"):
                nuevo["nivel_id"] = str(lec["nivel_id"])
        print(f"{ex['_id']}: «{titulo}» -> título «{fecha}», fecha {leccion}")
        if aplicar:
            examenes_collection.update_one({"_id": ex["_id"]}, {"$set": nuevo})
        reparados += 1

if reparados == 0:
    print("No hay exámenes que reparar.")
elif aplicar:
    print(f"Listo: {reparados} exámenes reparados.")
else:
    print(f"\n{reparados} exámenes por reparar. Ejecuta con --aplicar para guardar los cambios.")
