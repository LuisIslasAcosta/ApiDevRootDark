"""Pruebas del flujo de inscripción con pago, comprobante y validación del profesor.

Usan mongomock (MongoDB en memoria), así que no necesitan una base de datos real.
"""
import io

import mongomock
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    db = mongomock.MongoClient()["pruebas"]
    colecciones = {
        "usuarios_collection": db["usuarios"],
        "cursos_collection": db["cursos"],
        "inscripciones_collection": db["inscripciones"],
    }
    import models.Inscripciones as modelo
    import controllers.inscripciones as controlador
    import routes.inscripciones_routes as rutas

    for modulo in (modelo, controlador, rutas):
        for nombre, coleccion in colecciones.items():
            monkeypatch.setattr(modulo, nombre, coleccion, raising=False)
    monkeypatch.setattr(rutas, "CARPETA_COMPROBANTES", str(tmp_path))

    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "clave-de-pruebas-con-mas-de-32-caracteres"
    JWTManager(app)
    app.register_blueprint(rutas.inscripcion_bp, url_prefix="/api")

    usuarios, cursos = colecciones["usuarios_collection"], colecciones["cursos_collection"]
    ids = {
        "profesor": str(usuarios.insert_one({"nombre": "Profe", "rol": "profesor"}).inserted_id),
        "alumno": str(usuarios.insert_one({"nombre": "Ana", "rol": "usuario", "email": "ana@example.com"}).inserted_id),
        "otro": str(usuarios.insert_one({"nombre": "Otro", "rol": "usuario"}).inserted_id),
    }
    ids["curso"] = str(cursos.insert_one({"nombre": "React", "precio": 499, "profesor": ids["profesor"],
                                          "instrucciones_pago": "CLABE 0123"}).inserted_id)
    ids["gratis"] = str(cursos.insert_one({"nombre": "Gratis", "precio": 0, "profesor": ids["profesor"]}).inserted_id)

    with app.app_context():
        tokens = {k: {"Authorization": f"Bearer {create_access_token(identity=ids[k])}"}
                  for k in ("profesor", "alumno", "otro")}
    return app.test_client(), ids, tokens


def subir(cliente, inscripcion_id, token, contenido=b"%PDF-1.4", nombre="comprobante.pdf"):
    return cliente.post(f"/api/inscripciones/{inscripcion_id}/comprobante",
                        data={"comprobante": (io.BytesIO(contenido), nombre), "fecha_pago": "2026-11-12"},
                        headers=token, content_type="multipart/form-data")


def test_inscripcion_genera_referencia_unica_y_queda_pendiente(entorno):
    cliente, ids, t = entorno
    r = cliente.post("/api/inscripciones", json={"curso_id": ids["curso"]}, headers=t["alumno"])
    assert r.status_code == 201
    ins = r.get_json()["inscripcion"]
    assert ins["estado"] == "pendiente_pago"
    assert ins["referencia_pago"].startswith("DRD-") and len(ins["referencia_pago"]) == 12
    assert ins["monto"] == 499 and ins["instrucciones_pago"] == "CLABE 0123"

    repetida = cliente.post("/api/inscripciones", json={"curso_id": ids["curso"]}, headers=t["alumno"])
    assert repetida.status_code == 200
    assert repetida.get_json()["inscripcion"]["referencia_pago"] == ins["referencia_pago"]


def test_curso_gratuito_se_acepta_directo(entorno):
    cliente, ids, t = entorno
    r = cliente.post("/api/inscripciones", json={"curso_id": ids["gratis"]}, headers=t["alumno"])
    assert r.get_json()["inscripcion"]["estado"] == "aceptada"


def test_flujo_completo_rechazo_y_aceptacion(entorno):
    cliente, ids, t = entorno
    iid = cliente.post("/api/inscripciones", json={"curso_id": ids["curso"]}, headers=t["alumno"]).get_json()["inscripcion"]["id"]

    assert subir(cliente, iid, t["alumno"]).get_json()["inscripcion"]["estado"] == "en_revision"

    pagos = cliente.get("/api/inscripciones/profesor/pagos", headers=t["profesor"]).get_json()
    assert pagos[0]["estado"] == "en_revision" and pagos[0]["tiene_comprobante"]
    assert cliente.get(f"/api/inscripciones/{iid}/comprobante", headers=t["profesor"]).data == b"%PDF-1.4"

    rechazo = cliente.put(f"/api/inscripciones/{iid}/validar", json={"accion": "rechazar", "motivo": "No llegó"},
                          headers=t["profesor"])
    assert rechazo.get_json()["inscripcion"]["estado"] == "rechazada"

    subir(cliente, iid, t["alumno"], b"\x89PNG", "comprobante.png")
    acepta = cliente.put(f"/api/inscripciones/{iid}/validar", json={"accion": "aceptar"}, headers=t["profesor"])
    assert acepta.get_json()["inscripcion"]["estado"] == "aceptada"

    mis = cliente.get("/api/inscripciones/mis-inscripciones", headers=t["alumno"]).get_json()
    assert [m["estado"] for m in mis] == ["aceptada"]


def test_permisos(entorno):
    cliente, ids, t = entorno
    iid = cliente.post("/api/inscripciones", json={"curso_id": ids["curso"]}, headers=t["alumno"]).get_json()["inscripcion"]["id"]
    assert subir(cliente, iid, t["otro"]).status_code == 403
    subir(cliente, iid, t["alumno"])
    assert cliente.get(f"/api/inscripciones/{iid}/comprobante", headers=t["otro"]).status_code == 403
    assert cliente.put(f"/api/inscripciones/{iid}/validar", json={"accion": "aceptar"}, headers=t["otro"]).status_code == 403


def test_validaciones_de_archivo_y_motivo(entorno):
    cliente, ids, t = entorno
    iid = cliente.post("/api/inscripciones", json={"curso_id": ids["curso"]}, headers=t["alumno"]).get_json()["inscripcion"]["id"]
    assert subir(cliente, iid, t["alumno"], b"MZ", "virus.exe").status_code == 400
    assert subir(cliente, iid, t["alumno"], b"", "vacio.pdf").status_code == 400
    subir(cliente, iid, t["alumno"])
    sin_motivo = cliente.put(f"/api/inscripciones/{iid}/validar", json={"accion": "rechazar"}, headers=t["profesor"])
    assert sin_motivo.status_code == 400
