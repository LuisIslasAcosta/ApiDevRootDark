import os
import subprocess
from flask import send_file, jsonify, request
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime

BACKUP_DIR = "backups"
os.makedirs(BACKUP_DIR, exist_ok=True)

scheduler = BackgroundScheduler()
scheduler.start()
config = {"carpeta": BACKUP_DIR, "intervalo": 24}

DB_NAME = "DevRootDark"
DB_USER = "root"
DB_PASS = ""  # pon tu contraseña

def generar_respaldo():
    try:
        backup_file = os.path.join(
            config["carpeta"],
            f"respaldo-{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.sql"
        )
        comando = f"mysqldump -u {DB_USER} -p{DB_PASS} {DB_NAME} > {backup_file}"
        subprocess.run(comando, shell=True, check=True)
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
        comando = f"mysql -u {DB_USER} -p{DB_PASS} {DB_NAME} < {filepath}"
        subprocess.run(comando, shell=True, check=True)
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