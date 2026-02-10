# controllers/respaldo_controller.py
import os, json
from flask import send_file, jsonify, request
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

# Scheduler y configuración global
scheduler = BackgroundScheduler()
scheduler.start()
config = {"carpeta": BACKUP_DIR, "intervalo": 24}

def generar_respaldo():
    try:
        client = MongoClient("mongodb://127.0.0.1:27017/")
        ##client = MongoClient("mongodb://100.68.178.91:27017/")
        db = client["DevRootDark"]

        backup_file = os.path.join(
            config["carpeta"],
            f"respaldo-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        )

        data = {}
        for collection_name in db.list_collection_names():
            collection = db[collection_name]
            data[collection_name] = list(collection.find({}, {"_id": False}))

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return send_file(backup_file, as_attachment=True)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def restaurar_respaldo():
    if "file" not in request.files:
        return jsonify({"error": "No se envió archivo"}), 400

    file = request.files["file"]
    filepath = os.path.join(config["carpeta"], file.filename)
    file.save(filepath)

    try:
        client = MongoClient("mongodb://127.0.0.1:27017/")
        ##client = MongoClient("mongodb://100.68.178.91:27017/")
        db = client["DevRootDark"]

        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        for collection_name, docs in data.items():
            db[collection_name].delete_many({})
            if docs:
                db[collection_name].insert_many(docs)

        return jsonify({"message": "Base de datos restaurada correctamente"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

def configurar_respaldo():
    global config
    datos = request.get_json()
    config["carpeta"] = datos.get("carpeta", config["carpeta"])
    tipo = datos.get("intervalo", "horas")
    valor = datos.get("valor", 24)

    os.makedirs(config["carpeta"], exist_ok=True)

    scheduler.remove_all_jobs()

    if tipo == "horas":
        scheduler.add_job(func=generar_respaldo, trigger="interval", hours=int(valor))
    elif tipo == "diario":
        scheduler.add_job(func=generar_respaldo, trigger="cron", hour=0)
    elif tipo == "semanal":
        scheduler.add_job(func=generar_respaldo, trigger="cron", day_of_week="sun", hour=0)
    elif tipo == "mensual":
        scheduler.add_job(func=generar_respaldo, trigger="cron", day=1, hour=0)

    return jsonify({"message": f"Respaldo configurado: {tipo} en {config['carpeta']}"})