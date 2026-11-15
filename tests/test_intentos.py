"""Pruebas de los intentos de examen seguros (en línea y sin conexión).

Usan mongomock, así que no necesitan una base de datos real.
"""
import time

import mongomock
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token


@pytest.fixture
def entorno(monkeypatch):
    db = mongomock.MongoClient()["pruebas"]
    import controllers.intentos as ctl
    import routes.intentos_routes as rutas
    import routes.respuestas_route as rutas_resp
    import models.Respuesta as modelo_resp

    colecciones = {
        "usuarios_collection": db["usuarios"],
        "examenes_collection": db["examenes"],
        "inscripciones_collection": db["inscripciones"],
        "preguntas_collection": db["preguntas"],
        "respuestas_collection": db["respuestas"],
        "intentos_collection": db["intentos_examen"],
    }
    for modulo in (ctl, modelo_resp):
        for nombre, coleccion in colecciones.items():
            monkeypatch.setattr(modulo, nombre, coleccion, raising=False)

    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = "clave-de-pruebas-con-mas-de-32-caracteres"
    JWTManager(app)
    app.register_blueprint(rutas.intento_bp, url_prefix="/api")
    app.register_blueprint(rutas_resp.respuesta_bp, url_prefix="/api")

    u = colecciones["usuarios_collection"]
    ids = {
        "alumno": str(u.insert_one({"nombre": "Ana", "rol": "usuario"}).inserted_id),
        "intruso": str(u.insert_one({"nombre": "Beto", "rol": "usuario"}).inserted_id),
        "profesor": str(u.insert_one({"nombre": "Profe", "rol": "profesor"}).inserted_id),
    }
    curso = "6560c0ffee00000000000001"
    ids["examen"] = str(colecciones["examenes_collection"].insert_one(
        {"curso_id": curso, "titulo": "Parcial", "intentos_max": 2, "duracion_minutos": 10}).inserted_id)
    colecciones["preguntas_collection"].insert_many([
        {"examen_id": ids["examen"], "enunciado": "2+2", "opciones": ["3", "4", "5"], "respuesta_correcta": "4"},
        {"examen_id": ids["examen"], "enunciado": "Capital de México", "opciones": ["CDMX", "Toluca"], "respuesta_correcta": "CDMX"},
    ])
    colecciones["inscripciones_collection"].insert_one({"curso_id": curso, "alumno_id": ids["alumno"], "estado": "aceptada"})
    colecciones["inscripciones_collection"].insert_one({"curso_id": curso, "alumno_id": ids["intruso"], "estado": "en_revision"})

    with app.app_context():
        tokens = {k: {"Authorization": f"Bearer {create_access_token(identity=ids[k])}"} for k in ("alumno", "intruso", "profesor")}
    return app.test_client(), ids, tokens, colecciones


def correctas(paquete):
    mapa = {"2+2": "4", "Capital de México": "CDMX"}
    return {p["id"]: mapa[p["enunciado"]] for p in paquete["preguntas"]}


def ahora_ms():
    return int(time.time() * 1000)


def test_paquete_no_trae_respuestas_y_se_reutiliza(entorno):
    cliente, ids, t, _ = entorno
    r = cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"])
    assert r.status_code == 201
    paquete = r.get_json()
    assert "respuesta_correcta" not in str(paquete)
    assert paquete["clave_envio"] and paquete["intentos_max"] == 2

    otra = cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"]).get_json()
    assert otra["intento_id"] == paquete["intento_id"]  # no se puede pedir otro hasta enviar este
    assert [p["id"] for p in otra["preguntas"]] == [p["id"] for p in paquete["preguntas"]]


def test_sin_inscripcion_aceptada_no_puede_presentar(entorno):
    cliente, ids, t, _ = entorno
    r = cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["intruso"])
    assert r.status_code == 403


def test_envio_sin_conexion_con_clave_y_reenvio_idempotente(entorno):
    cliente, ids, t, col = entorno
    paquete = cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"]).get_json()
    inicio = ahora_ms()
    cuerpo = {
        "clave_envio": paquete["clave_envio"], "respuestas": correctas(paquete), "sin_conexion": True,
        "iniciado_cliente": inicio, "finalizado_cliente": inicio + 60000, "duracion_ms": 60000,
        "reloj_cliente": ahora_ms(), "eventos": [],
    }
    # Sin token (caducó mientras estaba sin señal): vale la clave del intento
    r = cliente.post(f"/api/intentos/{paquete['intento_id']}/enviar", json=cuerpo)
    assert r.status_code == 201
    assert r.get_json()["calificacion"] == 100
    assert r.get_json()["requiere_revision"] is False

    # Al reconectar se puede reenviar: no se califica dos veces
    otra = cliente.post(f"/api/intentos/{paquete['intento_id']}/enviar", json={**cuerpo, "respuestas": {}})
    assert otra.status_code == 200 and otra.get_json()["calificacion"] == 100
    assert col["respuestas_collection"].count_documents({}) == 1


def test_otro_alumno_no_puede_enviar_intento_ajeno(entorno):
    cliente, ids, t, _ = entorno
    paquete = cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"]).get_json()
    r = cliente.post(f"/api/intentos/{paquete['intento_id']}/enviar", headers=t["intruso"],
                     json={"respuestas": correctas(paquete)})
    assert r.status_code == 403
    r = cliente.post(f"/api/intentos/{paquete['intento_id']}/enviar", json={"clave_envio": "inventada"})
    assert r.status_code == 403


def test_respuesta_inventada_no_cuenta_y_se_marca(entorno):
    cliente, ids, t, _ = entorno
    paquete = cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"]).get_json()
    resp = correctas(paquete)
    primera = paquete["preguntas"][0]["id"]
    resp[primera] = "<script>"
    r = cliente.post(f"/api/intentos/{paquete['intento_id']}/enviar", headers=t["alumno"],
                     json={"respuestas": resp, "duracion_ms": 1000, "reloj_cliente": ahora_ms()}).get_json()
    assert r["calificacion"] == 50 and r["requiere_revision"] is True


def test_reloj_alterado_y_tiempo_excedido_quedan_para_revision(entorno):
    cliente, ids, t, col = entorno
    paquete = cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"]).get_json()
    atrasado = ahora_ms() - 3 * 3600 * 1000  # el alumno atrasó el reloj 3 horas
    cliente.post(f"/api/intentos/{paquete['intento_id']}/enviar", headers=t["alumno"], json={
        "respuestas": correctas(paquete), "sin_conexion": True, "reloj_cliente": atrasado,
        "iniciado_cliente": atrasado - 60000, "finalizado_cliente": atrasado, "duracion_ms": 45 * 60000,
    })
    intento = col["intentos_collection"].find_one({})
    assert "reloj_del_dispositivo_alterado" in intento["banderas"]
    assert "tiempo_excedido" in intento["banderas"]
    assert intento["requiere_revision"] is True


def test_limite_de_intentos_tambien_en_ruta_anterior(entorno):
    cliente, ids, t, _ = entorno
    for _ in range(2):
        p = cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"]).get_json()
        cliente.post(f"/api/intentos/{p['intento_id']}/enviar", headers=t["alumno"], json={"respuestas": {}})
    assert cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"]).status_code == 409
    # La ruta vieja ya no deja saltarse el límite ni enviar sin sesión
    assert cliente.post("/api/respuestas", json={"examen_id": ids["examen"], "alumno_id": ids["alumno"]}).status_code == 401
    r = cliente.post("/api/respuestas", headers=t["alumno"], json={"examen_id": ids["examen"], "respuestas": {}})
    assert r.status_code == 409


def test_inicio_en_linea_usa_hora_del_servidor_y_profesor_ve_alertas(entorno):
    cliente, ids, t, _ = entorno
    p = cliente.post(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"]).get_json()
    assert cliente.post(f"/api/intentos/{p['intento_id']}/iniciar", headers=t["alumno"], json={}).status_code == 200
    cliente.post(f"/api/intentos/{p['intento_id']}/enviar", headers=t["alumno"], json={
        "respuestas": correctas(p), "duracion_ms": 5000, "reloj_cliente": ahora_ms(),
        "eventos": [{"tipo": "cambio_de_pestana", "en": ahora_ms()}], "motivo": "Cambiaste de pestaña",
    })
    assert cliente.get(f"/api/intentos/examen/{ids['examen']}", headers=t["alumno"]).status_code == 403
    lista = cliente.get(f"/api/intentos/examen/{ids['examen']}", headers=t["profesor"]).get_json()
    assert lista[0]["alumno"] == "Ana"
    assert "salio_del_examen" in lista[0]["banderas"] and "enviado_automaticamente" in lista[0]["banderas"]
