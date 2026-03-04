import os
import traceback
from datetime import datetime
from flask import send_file, jsonify, request
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from bson import json_util
from dotenv import load_dotenv

load_dotenv()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_DB = os.getenv("MONGO_DB")

MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}/{MONGO_DB}?retryWrites=true&w=majority"

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

config = {"carpeta": BACKUP_DIR}

scheduler = BackgroundScheduler()
if not scheduler.running:
    scheduler.start()

def get_database():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB]

# ===============================
# GENERAR RESPALDO (SOLO CREA ARCHIVO)
# ===============================

def generar_respaldo():
    try:
        db = get_database()

        backup_file = os.path.join(
            config["carpeta"],
            f"respaldo-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        )

        data = {}
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            data[collection_name] = list(collection.find({}))

        with open(backup_file, "w", encoding="utf-8") as f:
            f.write(json_util.dumps(data, indent=2, ensure_ascii=False))

        return send_file(backup_file, as_attachment=True)

    except Exception as e:
        print("Error en generar_respaldo:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ===============================
# DESCARGAR RESPALDO
# ===============================

def descargar_respaldo():
    archivo = generar_respaldo()

    if archivo and os.path.exists(archivo):
        return send_file(
            archivo,
            as_attachment=True,
            download_name=os.path.basename(archivo)
        )
    else:
        return jsonify({"error": "No se pudo generar el respaldo"}), 500

# ===============================
# RESTAURAR RESPALDO
# ===============================

def restaurar_respaldo():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No se envió archivo"}), 400

        file = request.files["file"]

        if file.filename == "":
            return jsonify({"error": "Archivo sin nombre"}), 400

        contenido_bytes = file.read()

        if not contenido_bytes:
            return jsonify({"error": "El archivo está vacío"}), 400

        try:
            contenido_str = contenido_bytes.decode("utf-8")
        except Exception:
            return jsonify({"error": "No se pudo decodificar el archivo"}), 400

        try:
            data = json_util.loads(contenido_str)
        except Exception as e:
            print("Error parseando JSON:", e)
            return jsonify({"error": "El archivo no contiene un JSON válido"}), 400

        if not isinstance(data, dict):
            return jsonify({"error": "Formato de respaldo inválido"}), 400

        db = get_database()

        for collection_name, docs in data.items():

            if not isinstance(docs, list):
                continue

            if isinstance(docs, list) and docs:
                db[collection_name].delete_many({})
                db[collection_name].insert_many(docs)

        return jsonify({"message": "Base de datos restaurada correctamente"})

    except Exception as e:
        print("Error restaurando respaldo:", e)
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ===============================
# CONFIGURAR RESPALDO AUTOMÁTICO
# ===============================

def configurar_respaldo():
    global config

    datos = request.get_json()

    config["carpeta"] = datos.get("carpeta", config["carpeta"])
    tipo = datos.get("intervalo", "horas")
    valor = datos.get("valor", 24)

    scheduler.remove_all_jobs()

    if tipo == "horas":
        scheduler.add_job(generar_respaldo, "interval", hours=int(valor))
    elif tipo == "diario":
        scheduler.add_job(generar_respaldo, "cron", hour=0)
    elif tipo == "semanal":
        scheduler.add_job(generar_respaldo, "cron", day_of_week="sun", hour=0)
    elif tipo == "mensual":
        scheduler.add_job(generar_respaldo, "cron", day=1, hour=0)

    return jsonify({"message": "Respaldo configurado correctamente"})