"""Pruebas de la firma del profesor y de su uso en los certificados (mongomock)."""
import base64
import struct
import zlib

import mongomock
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


def png(ancho=200, alto=80):
    """PNG mínimo válido (transparente) hecho a mano para no depender de Pillow."""
    def bloque(tipo, datos):
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
    filas = b"".join(b"\x00" + b"\x00" * (ancho * 4) for _ in range(alto))
    crudo = (b"\x89PNG\r\n\x1a\n" + bloque(b"IHDR", struct.pack(">IIBBBBB", ancho, alto, 8, 6, 0, 0, 0))
             + bloque(b"IDAT", zlib.compress(filas)) + bloque(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(crudo).decode()


@pytest.fixture
def entorno(monkeypatch):
    db = mongomock.MongoClient()["pruebas"]
    import controllers.firmas as firmas
    import controllers.certificados as certificados
    import routes.firmas_routes as rutas

    monkeypatch.setattr(firmas, "firmas_collection", db["firmas"])
    monkeypatch.setattr(firmas, "usuarios_collection", db["usuarios"])
    monkeypatch.setattr(certificados, "certificados_collection", db["certificados"])
    monkeypatch.setattr(certificados, "usuarios_collection", db["usuarios"])
    monkeypatch.setattr(certificados, "cursos_collection", db["cursos"])

    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "clave-de-pruebas-con-mas-de-32-caracteres"
    JWTManager(app)
    app.register_blueprint(rutas.firmas_bp, url_prefix="/api")

    ids = {
        "profesor": str(db["usuarios"].insert_one({"nombre": "Rafa", "rol": "profesor"}).inserted_id),
        "alumno": str(db["usuarios"].insert_one({"nombre": "Ana", "apellidop": "López", "rol": "usuario"}).inserted_id),
    }
    ids["curso"] = str(db["cursos"].insert_one({"nombre": "React", "profesor": ids["profesor"]}).inserted_id)

    # El alumno ya terminó y aprobó el curso
    monkeypatch.setattr(certificados, "progreso_alumno_curso", lambda a, c: {
        "terminado": True, "promedio": 95, "total_lecciones": 3, "lecciones_vistas": 3,
        "total_examenes": 1, "examenes_presentados": 1, "examenes_reprobados": [], "profesor": "Rafa",
    })
    with app.app_context():
        tokens = {k: {"Authorization": f"Bearer {create_access_token(identity=ids[k])}"} for k in ("profesor", "alumno")}
    return app.test_client(), ids, tokens, certificados


def test_profesor_guarda_su_firma_y_alumno_no_puede(entorno):
    cliente, _, t, _ = entorno
    r = cliente.put("/api/firma", json={"imagen": png()}, headers=t["profesor"])
    assert r.status_code == 200 and len(r.get_json()["huella"]) == 12
    assert cliente.get("/api/firma", headers=t["profesor"]).get_json()["firma"].startswith("data:image/png")
    assert cliente.put("/api/firma", json={"imagen": png()}, headers=t["alumno"]).status_code == 403


@pytest.mark.parametrize("imagen", [
    None,
    "data:image/jpeg;base64,AAAA",
    "data:image/png;base64,no-es-base64!!",
    "data:image/png;base64," + base64.b64encode(b"<svg onload=alert(1)>").decode(),
])
def test_rechaza_firmas_que_no_son_png(entorno, imagen):
    cliente, _, t, _ = entorno
    assert cliente.put("/api/firma", json={"imagen": imagen}, headers=t["profesor"]).status_code == 400


def test_certificado_conserva_la_firma_con_la_que_se_emitio(entorno):
    cliente, ids, t, certificados = entorno
    primera = png(200, 80)
    cliente.put("/api/firma", json={"imagen": primera}, headers=t["profesor"])
    cert = certificados.emitir_certificado(ids["alumno"], ids["curso"])
    assert cert["firma_profesor"] == primera and len(cert["firma_codigo"]) == 10

    # El profesor cambia su firma: el certificado ya emitido no cambia
    cliente.put("/api/firma", json={"imagen": png(300, 90)}, headers=t["profesor"])
    verificado = certificados.verificar(cert["folio"])
    assert verificado["firma_profesor"] == primera
    assert verificado["firma_codigo"] == cert["firma_codigo"]


def test_certificado_sin_firma_sigue_funcionando(entorno):
    _, ids, _, certificados = entorno
    cert = certificados.emitir_certificado(ids["alumno"], ids["curso"])
    assert cert["firma_profesor"] is None and cert["firma_codigo"] is None
