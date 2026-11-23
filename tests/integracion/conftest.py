"""App completa con MongoDB en memoria (mongomock) para probar el control de acceso."""
import io
import os
import sys
import tempfile
from unittest import mock

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT)
os.environ["JWT_SECRET_KEY"] = "clave-de-pruebas-integracion-con-mas-de-32-caracteres"
os.environ["MONGO_DB"] = "integracion"
os.environ["UPLOADS_DIR"] = tempfile.mkdtemp(prefix="drd-uploads-")

# PySpark no es necesario para estas pruebas
for _m in ["pyspark", "pyspark.sql", "pyspark.sql.functions", "pyspark.sql.types", "pyspark.ml",
           "pyspark.ml.feature", "pyspark.ml.clustering", "pyspark.ml.classification", "pyspark.ml.evaluation"]:
    sys.modules.setdefault(_m, mock.MagicMock())

import mongomock  # noqa: E402
import pymongo  # noqa: E402

pymongo.MongoClient = mongomock.MongoClient

import pytest  # noqa: E402
from flask_jwt_extended import create_access_token  # noqa: E402

import app as aplicacion  # noqa: E402
from config import config as cfg  # noqa: E402
from utils.hash_utils import hash_contraseña  # noqa: E402
from utils.terminos import version_vigente  # noqa: E402

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
CLAVE = "Clave#Segura2026"


@pytest.fixture()
def api():
    for nombre in cfg.db.list_collection_names():
        cfg.db.drop_collection(nombre)
    usuarios = cfg.usuarios_collection

    def usuario(nombre, rol):
        return str(usuarios.insert_one({
            "nombre": nombre, "email": f"{nombre}@example.com", "rol": rol,
            "password": hash_contraseña(CLAVE), "terminos_version": version_vigente(),
        }).inserted_id)

    ids = {
        "admin": usuario("admin", "administrador"),
        "profe": usuario("profe", "profesor"),
        "otro_profe": usuario("otroprofe", "profesor"),
        "alumno": usuario("alumno", "usuario"),
        "intruso": usuario("intruso", "usuario"),
    }
    ids["curso"] = str(cfg.cursos_collection.insert_one(
        {"nombre": "React", "descripcion": "Curso", "precio": 0, "profesor": ids["profe"], "imagenes": [], "videos": []}).inserted_id)
    ids["nivel"] = str(cfg.niveles_collection.insert_one({"curso_id": ids["curso"], "titulo": "N1", "orden": 1}).inserted_id)
    ids["leccion"] = str(cfg.lecciones_collection.insert_one(
        {"curso_id": ids["curso"], "nivel_id": ids["nivel"], "titulo": "Intro", "archivos": ["secreto.png"]}).inserted_id)
    with open(os.path.join(os.environ["UPLOADS_DIR"], "imagenes", "secreto.png"), "wb") as f:
        f.write(PNG)
    ids["examen"] = str(cfg.examenes_collection.insert_one(
        {"curso_id": ids["curso"], "leccion_id": ids["leccion"], "titulo": "Parcial", "fecha": "2026-11-20",
         "preguntas": [{"enunciado": "2+2", "opciones": ["3", "4"], "respuesta_correcta": "4"}]}).inserted_id)
    cfg.inscripciones_collection.insert_one({"curso_id": ids["curso"], "alumno_id": ids["alumno"], "estado": "aceptada"})

    with aplicacion.app.app_context():
        tokens = {k: {"Authorization": f"Bearer {create_access_token(identity=ids[k])}"}
                  for k in ("admin", "profe", "otro_profe", "alumno", "intruso")}
    aplicacion.app.config["TESTING"] = True
    return aplicacion.app.test_client(), ids, tokens


def archivo(contenido, nombre):
    return (io.BytesIO(contenido), nombre)
