"""Pruebas de la música predeterminada de DevRootMusic."""
import io

import mongomock
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


@pytest.fixture
def entorno(monkeypatch, tmp_path):
    db = mongomock.MongoClient()["pruebas"]
    import utils.seguridad as seguridad
    import routes.musica_routes as rutas
    monkeypatch.setattr(seguridad, "usuarios_collection", db["usuarios"])
    monkeypatch.setattr(seguridad, "auditoria_collection", db["auditoria"])
    monkeypatch.setattr(rutas, "CARPETA_MUSICA", str(tmp_path))

    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "clave-de-pruebas-con-mas-de-32-caracteres"
    JWTManager(app)
    app.register_blueprint(rutas.musica_bp, url_prefix="/api")
    admin = str(db["usuarios"].insert_one({"rol": "administrador", "email": "a@x.com"}).inserted_id)
    alumno = str(db["usuarios"].insert_one({"rol": "usuario", "email": "b@x.com"}).inserted_id)
    with app.app_context():
        t = {k: {"Authorization": f"Bearer {create_access_token(identity=v)}"} for k, v in (("admin", admin), ("alumno", alumno))}
    return app.test_client(), t, tmp_path


def test_lista_junta_audio_y_video_de_la_misma_cancion(entorno):
    cliente, _, carpeta = entorno
    for n in ("Rain_Against_The_Pane.mp3", "Rain_Against_The_Pane.mp4", "The_Giant_Falls.mp3", "notas.txt"):
        (carpeta / n).write_bytes(b"x")
    lista = cliente.get("/api/musica").get_json()
    assert [c["titulo"] for c in lista] == ["Rain Against The Pane", "The Giant Falls"]
    assert lista[0]["audio"] == "musica/Rain_Against_The_Pane.mp3" and lista[0]["video"].endswith(".mp4")
    assert lista[1]["video"] is None


def test_solo_el_admin_sube_y_borra(entorno):
    cliente, t, carpeta = entorno
    datos = lambda: {"archivos": [(io.BytesIO(b"ID3"), "Nueva cancion.mp3"), (io.BytesIO(b"x"), "virus.exe")]}
    assert cliente.post("/api/musica", data=datos(), headers=t["alumno"], content_type="multipart/form-data").status_code == 403
    r = cliente.post("/api/musica", data=datos(), headers=t["admin"], content_type="multipart/form-data")
    assert r.status_code == 201
    assert r.get_json()["guardados"] == ["Nueva_cancion.mp3"] and r.get_json()["rechazados"] == ["virus.exe"]
    assert (carpeta / "Nueva_cancion.mp3").exists()
    assert cliente.delete("/api/musica/Nueva_cancion.mp3", headers=t["alumno"]).status_code == 403
    assert cliente.delete("/api/musica/Nueva_cancion.mp3", headers=t["admin"]).status_code == 200
    assert not (carpeta / "Nueva_cancion.mp3").exists()
    # No se puede salir de la carpeta de música
    assert cliente.delete("/api/musica/..%2Fapp.py", headers=t["admin"]).status_code in (404, 405)
