"""Las rutas de respaldos solo deben funcionar para un administrador autenticado."""
import mongomock
import pytest
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token


@pytest.fixture
def cliente(monkeypatch):
    db = mongomock.MongoClient()["pruebas"]
    import utils.seguridad as seguridad
    import routes.respaldo_routes as rutas

    monkeypatch.setattr(seguridad, "usuarios_collection", db["usuarios"])
    monkeypatch.setattr(seguridad, "auditoria_collection", db["auditoria"])
    monkeypatch.setattr(rutas, "auditoria_collection", db["auditoria"])
    monkeypatch.setattr(rutas, "listar_respaldos", lambda: (jsonify([{"nombre": "r.json"}]), 200))
    monkeypatch.setattr(rutas, "generar_respaldo", lambda tipo: (jsonify({"tipo": tipo}), 200))
    monkeypatch.setattr(rutas, "eliminar_respaldo", lambda nombre, tipo: (jsonify({"message": "ok"}), 200))

    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "clave-de-pruebas-con-mas-de-32-caracteres"
    JWTManager(app)
    app.register_blueprint(rutas.respaldo_bp, url_prefix="/api")

    admin = str(db["usuarios"].insert_one({"rol": "administrador", "email": "admin@x.com"}).inserted_id)
    alumno = str(db["usuarios"].insert_one({"rol": "usuario", "email": "alumno@x.com"}).inserted_id)
    with app.app_context():
        tokens = {"admin": create_access_token(identity=admin), "alumno": create_access_token(identity=alumno)}
    return app.test_client(), tokens, db["auditoria"]


@pytest.mark.parametrize("metodo,ruta", [
    ("get", "/api/respaldos"),
    ("get", "/api/respaldo/completo"),
    ("post", "/api/respaldo"),
    ("post", "/api/config-respaldo"),
    ("post", "/api/respaldo/restaurar/completo/r.json"),
    ("delete", "/api/respaldo/completo/r.json"),
    ("get", "/api/respaldos/auditoria"),
])
def test_sin_token_responde_401(cliente, metodo, ruta):
    c, _, _ = cliente
    assert getattr(c, metodo)(ruta).status_code == 401


def test_usuario_normal_recibe_403_y_queda_en_bitacora(cliente):
    c, t, auditoria = cliente
    r = c.get("/api/respaldo/completo", headers={"Authorization": f"Bearer {t['alumno']}"})
    assert r.status_code == 403
    registro = auditoria.find_one({"email": "alumno@x.com"})
    assert registro and registro["exito"] is False


def test_admin_si_puede_y_queda_en_bitacora(cliente):
    c, t, auditoria = cliente
    h = {"Authorization": f"Bearer {t['admin']}"}
    assert c.get("/api/respaldos", headers=h).status_code == 200
    assert c.get("/api/respaldo/completo", headers=h).get_json() == {"tipo": "completo"}
    assert auditoria.count_documents({"email": "admin@x.com", "exito": True}) == 2
    assert len(c.get("/api/respaldos/auditoria", headers=h).get_json()) >= 2
