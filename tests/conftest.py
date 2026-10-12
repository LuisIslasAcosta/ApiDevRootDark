import os
import sys
from types import SimpleNamespace

import pytest
from bson.objectid import ObjectId
from flask import Flask

os.environ.setdefault("MONGO_DB", "test_db")

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


class MemoryCollection:
    def __init__(self):
        self.data = []

    def _matches(self, documento, filtro):
        if not filtro:
            return True
        for clave, valor in filtro.items():
            if clave == "_id":
                if isinstance(valor, dict):
                    if "$in" in valor and documento.get("_id") not in valor["$in"]:
                        return False
                    if "$ne" in valor and documento.get("_id") == valor["$ne"]:
                        return False
                elif documento.get("_id") != valor:
                    return False
            elif documento.get(clave) != valor:
                return False
        return True

    def _sort_key(self, valor):
        if isinstance(valor, (int, float)):
            return valor
        if isinstance(valor, str):
            return valor
        return str(valor)

    def find_one(self, filtro=None, sort=None):
        filtro = filtro or {}
        coincidencias = [doc for doc in self.data if self._matches(doc, filtro)]
        if sort:
            for campo, direccion in reversed(sort):
                coincidencias = sorted(
                    coincidencias,
                    key=lambda doc: self._sort_key(doc.get(campo)),
                    reverse=(direccion == -1),
                )
        return coincidencias[0] if coincidencias else None

    def find(self):
        return MemoryCursor(self.data)

    def insert_one(self, documento):
        doc = dict(documento)
        if "_id" not in doc:
            doc["_id"] = ObjectId()
        self.data.append(doc)
        return SimpleNamespace(inserted_id=doc["_id"])

    def update_one(self, filtro, cambio):
        actualizados = 0
        for documento in self.data:
            if self._matches(documento, filtro):
                if "$set" in cambio:
                    documento.update(cambio["$set"])
                actualizados += 1
        return SimpleNamespace(modified_count=actualizados)

    def delete_one(self, filtro):
        for indice, documento in enumerate(self.data):
            if self._matches(documento, filtro):
                del self.data[indice]
                return SimpleNamespace(deleted_count=1)
        return SimpleNamespace(deleted_count=0)


class MemoryCursor:
    def __init__(self, documentos):
        self.documentos = list(documentos)

    def sort(self, *args):
        if not args:
            return self
        if len(args) == 1 and isinstance(args[0], list):
            orden = args[0]
        elif len(args) == 2:
            orden = [(args[0], args[1])]
        else:
            orden = list(args)

        for campo, direccion in reversed(orden):
            self.documentos = sorted(
                self.documentos,
                key=lambda doc: str(doc.get(campo, "")),
                reverse=(direccion == -1),
            )
        return self

    def limit(self, cantidad):
        self.documentos = self.documentos[:cantidad]
        return self

    def __iter__(self):
        return iter(self.documentos)


@pytest.fixture
def flask_app():
    """App mínima de Flask para que jsonify() funcione fuera de una petición."""
    app = Flask(__name__)
    with app.app_context():
        yield app


@pytest.fixture
def memory_collections(monkeypatch):
    """Colecciones reales en memoria, sin mocks ni assertions sobre llamadas."""
    usuarios = MemoryCollection()
    cursos = MemoryCollection()
    examenes = MemoryCollection()

    monkeypatch.setattr("config.config.usuarios_collection", usuarios, raising=False)
    monkeypatch.setattr("config.config.cursos_collection", cursos, raising=False)
    monkeypatch.setattr("config.config.examenes_collection", examenes, raising=False)

    monkeypatch.setattr("models.User.usuarios_collection", usuarios, raising=False)
    monkeypatch.setattr("controllers.user.usuarios_collection", usuarios, raising=False)

    monkeypatch.setattr("models.Curso.cursos_collection", cursos, raising=False)
    monkeypatch.setattr("controllers.cursos.cursos_collection", cursos, raising=False)
    monkeypatch.setattr("controllers.cursos.usuarios_collection", usuarios, raising=False)

    monkeypatch.setattr("models.Examen.examenes_collection", examenes, raising=False)
    monkeypatch.setattr("controllers.examenes.examenes_collection", examenes, raising=False)

    return {"usuarios": usuarios, "cursos": cursos, "examenes": examenes}


@pytest.fixture
def valid_user_data():
    return {
        "nombre": "Ana",
        "apellidop": "Pérez",
        "apellidom": "López",
        "fecha_nacimiento": "2000-01-01",
        "pais": "México",
        "ciudad": "Toluca",
        "email": "ana@correo.com",
        "password": "Segura#Clave123",
        "verificar_password": "Segura#Clave123",
        "foto_perfil": None,
        "pregunta_seguridad": "¿Mascota?",
        "respuesta_seguridad": "firulais",
        "telefono": "7221234567",
    }