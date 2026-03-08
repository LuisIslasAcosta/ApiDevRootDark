import os
import json
import traceback
from datetime import datetime
from flask import send_file, jsonify, request
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from bson import json_util
from dotenv import load_dotenv

load_dotenv()

# ===============================
# CONFIGURACIÓN MONGO
# ===============================

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")
MONGO_HOST = os.getenv("MONGO_HOST")
MONGO_PORT = os.getenv("MONGO_PORT")
MONGO_DB = os.getenv("MONGO_DB")
MONGO_APPNAME = os.getenv("MONGO_APPNAME")

# Detectar si es local o Atlas
if MONGO_USER and MONGO_PASSWORD:
    # MongoDB Atlas
    MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}/{MONGO_DB}?retryWrites=true&w=majority&appName={MONGO_APPNAME}"
else:
    # MongoDB Local
    MONGO_URI = f"mongodb://{MONGO_HOST}:{MONGO_PORT}/{MONGO_DB}"


def get_database():
    client = MongoClient(MONGO_URI)
    return client[MONGO_DB]

# ===============================
# CARPETAS DE RESPALDOS
# ===============================
BASE_DIR = "backups"
FULL_DIR = os.path.join(BASE_DIR, "completos")
INCREMENTAL_DIR = os.path.join(BASE_DIR, "incrementales")
DIFFERENTIAL_DIR = os.path.join(BASE_DIR, "diferenciales")

os.makedirs(FULL_DIR, exist_ok=True)
os.makedirs(INCREMENTAL_DIR, exist_ok=True)
os.makedirs(DIFFERENTIAL_DIR, exist_ok=True)

# ===============================
# ARCHIVOS PARA FECHAS
# ===============================
ULTIMO_RESPALDO_FILE = os.path.join(BASE_DIR, "ultimo_respaldo.txt")
ULTIMO_COMPLETO_FILE = os.path.join(BASE_DIR, "ultimo_completo.txt")

def leer_fecha(path):
    try:
        with open(path) as f:
            return datetime.fromisoformat(f.read())
    except:
        return None

def guardar_fecha(path, fecha):
    with open(path, "w") as f:
        f.write(fecha.isoformat())

ultimo_respaldo = leer_fecha(ULTIMO_RESPALDO_FILE)
ultimo_completo = leer_fecha(ULTIMO_COMPLETO_FILE)

scheduler = BackgroundScheduler()
if not scheduler.running:
    scheduler.start()

# ===============================
# GENERAR RESPALDO
# ===============================
def generar_respaldo(tipo="completo"):
    global ultimo_respaldo, ultimo_completo
    try:
        db = get_database()
        fecha = datetime.now()
        nombre = f"{tipo}-{fecha.strftime('%Y-%m-%d_%H-%M-%S')}.json"

        if tipo == "completo":
            carpeta = FULL_DIR
        elif tipo == "incremental":
            carpeta = INCREMENTAL_DIR
        elif tipo == "diferencial":
            carpeta = DIFFERENTIAL_DIR
        else:
            return jsonify({"error": "Tipo inválido"}), 400

        ruta = os.path.join(carpeta, nombre)
        data = {}

        for collection_name in db.list_collection_names():
            collection = db[collection_name]

            # Asegurarse de que todos los documentos tengan fecha_actualizacion
            collection.update_many(
                {"fecha_actualizacion": {"$exists": False}},
                {"$set": {"fecha_actualizacion": fecha}}
            )

            if tipo == "completo":
                docs = list(collection.find({}))
            elif tipo == "incremental":
                filtro = {"fecha_actualizacion": {"$gt": ultimo_respaldo}} if ultimo_respaldo else {}
                docs = list(collection.find(filtro))
            elif tipo == "diferencial":
                filtro = {"fecha_actualizacion": {"$gt": ultimo_completo}} if ultimo_completo else {}
                docs = list(collection.find(filtro))

            data[collection_name] = docs

        # Guardar respaldo
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(json_util.dumps(data, indent=2, ensure_ascii=False))

        # Actualizar fechas
        if tipo == "completo":
            ultimo_completo = fecha
            guardar_fecha(ULTIMO_COMPLETO_FILE, fecha)

        ultimo_respaldo = fecha
        guardar_fecha(ULTIMO_RESPALDO_FILE, fecha)

        return send_file(ruta, as_attachment=True)
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ===============================
# LISTAR RESPALDOS
# ===============================
def listar_respaldos():
    resultado = []
    for tipo, carpeta in {
        "completo": FULL_DIR,
        "incremental": INCREMENTAL_DIR,
        "diferencial": DIFFERENTIAL_DIR
    }.items():
        for archivo in os.listdir(carpeta):
            resultado.append({"nombre": archivo, "tipo": tipo})
    return jsonify(resultado)

# ===============================
# RESTAURAR RESPALDO SUBIDO
# ===============================
def restaurar_respaldo():
    try:
        if "file" not in request.files:
            return jsonify({"error": "No se envió archivo"}), 400
        file = request.files["file"]
        contenido = json_util.loads(file.read())
        db = get_database()
        for collection_name, docs in contenido.items():
            db[collection_name].delete_many({})
            if docs:
                db[collection_name].insert_many(docs)
        return jsonify({"message": "Base de datos restaurada correctamente"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ===============================
# RESTAURAR DESDE LISTA
# ===============================
def restaurar_respaldo_lista(nombre, tipo):
    try:
        if tipo == "completo":
            carpeta = FULL_DIR
        elif tipo == "incremental":
            carpeta = INCREMENTAL_DIR
        elif tipo == "diferencial":
            carpeta = DIFFERENTIAL_DIR
        else:
            return jsonify({"error": "Tipo inválido"}), 400

        ruta = os.path.join(carpeta, nombre)
        if not os.path.exists(ruta):
            return jsonify({"error": "Archivo no encontrado"}), 404

        with open(ruta, "r", encoding="utf-8") as f:
            contenido = json.load(f)

        db = get_database()
        for collection_name, docs in contenido.items():
            if tipo == "completo":
                # Borra todo para respaldo completo
                db[collection_name].delete_many({})
                if docs:
                    db[collection_name].insert_many(docs)
            else:
                # Incremental/diferencial: actualizar o insertar sin borrar todo
                for doc in docs:
                    _id = doc.get("_id")
                    if _id:
                        db[collection_name].replace_one({"_id": _id}, doc, upsert=True)
                    else:
                        db[collection_name].insert_one(doc)

        return jsonify({"message": f"Respaldo '{nombre}' restaurado correctamente"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ===============================
# ELIMINAR RESPALDO
# ===============================
def eliminar_respaldo(nombre, tipo):
    try:
        if tipo == "completo":
            carpeta = FULL_DIR
        elif tipo == "incremental":
            carpeta = INCREMENTAL_DIR
        elif tipo == "diferencial":
            carpeta = DIFFERENTIAL_DIR
        else:
            return jsonify({"error": "Tipo inválido"}), 400

        ruta = os.path.join(carpeta, nombre)
        if not os.path.exists(ruta):
            return jsonify({"error": "Archivo no encontrado"}), 404

        os.remove(ruta)
        return jsonify({"message": f"Respaldo '{nombre}' eliminado correctamente"})
    except Exception as e:
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# ===============================
# CONFIGURAR RESPALDO AUTOMÁTICO
# ===============================
def configurar_respaldo():
    datos = request.get_json()
    tipo_respaldo = datos.get("tipo_respaldo", "completo")
    intervalo = datos.get("intervalo", "horas")
    valor = int(datos.get("valor", 24))

    scheduler.remove_all_jobs()

    if intervalo == "horas":
        scheduler.add_job(lambda: generar_respaldo(tipo_respaldo), "interval", hours=valor)
    elif intervalo == "diario":
        scheduler.add_job(lambda: generar_respaldo(tipo_respaldo), "cron", hour=0)
    elif intervalo == "semanal":
        scheduler.add_job(lambda: generar_respaldo(tipo_respaldo), "cron", day_of_week="sun", hour=0)
    elif intervalo == "mensual":
        scheduler.add_job(lambda: generar_respaldo(tipo_respaldo), "cron", day=1, hour=0)

    return jsonify({"message": "Respaldo automático configurado correctamente"})