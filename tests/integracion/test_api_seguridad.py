"""Pruebas del reporte de seguridad: control de acceso en el servidor, sesiones y archivos."""
from conftest import CLAVE, PNG, archivo


# ---------------- V-01: el rol se valida en el servidor ----------------
def test_alumno_no_puede_hacerse_admin_editando_su_perfil(api):
    c, ids, t = api
    r = c.put(f"/api/usuarios/{ids['alumno']}", json={"nombre": "Ana", "rol": "administrador"}, headers=t["alumno"])
    assert r.status_code in (200, 400)
    assert c.get("/api/me", headers=t["alumno"]).get_json()["rol"] == "usuario"


def test_alumno_no_puede_editar_ni_ver_a_otro(api):
    c, ids, t = api
    assert c.put(f"/api/usuarios/{ids['admin']}", json={"nombre": "x"}, headers=t["alumno"]).status_code == 403
    assert c.get(f"/api/usuarios/{ids['intruso']}", headers=t["alumno"]).status_code == 403


def test_rutas_de_admin_rechazan_a_quien_no_es_admin(api):
    c, ids, t = api
    for ruta in ("/api/usuarios", "/api/usuarios/recientes", "/api/estadisticas", "/api/preguntas"):
        assert c.get(ruta).status_code == 401, ruta
        assert c.get(ruta, headers=t["alumno"]).status_code == 403, ruta
        assert c.get(ruta, headers=t["profe"]).status_code == 403, ruta
    assert c.get("/api/usuarios", headers=t["admin"]).status_code == 200


def test_cambiar_contrasena_por_id_exige_admin(api):
    c, ids, t = api
    assert c.put(f"/api/recuperar_contraseña/{ids['admin']}", json={"nueva_password": "Otra#Clave2026"}).status_code == 401
    assert c.delete(f"/api/usuarios/{ids['admin']}", headers=t["alumno"]).status_code == 403


def test_me_no_expone_contrasena(api):
    c, ids, t = api
    datos = c.get("/api/me", headers=t["profe"]).get_json()
    assert datos["rol"] == "profesor" and "password" not in datos


def test_solo_el_profesor_dueno_gestiona_su_curso(api):
    c, ids, t = api
    curso = ids["curso"]
    assert c.delete(f"/api/cursos/{curso}").status_code == 401
    assert c.delete(f"/api/cursos/{curso}", headers=t["alumno"]).status_code == 403
    assert c.delete(f"/api/cursos/{curso}", headers=t["otro_profe"]).status_code == 403
    assert c.put(f"/api/cursos/{curso}", data={"nombre": "Hack"}, headers=t["otro_profe"]).status_code == 403
    assert c.post("/api/niveles", json={"curso_id": curso, "titulo": "X"}, headers=t["otro_profe"]).status_code == 403
    assert c.delete(f"/api/lecciones/{ids['leccion']}", headers=t["otro_profe"]).status_code == 403
    assert c.delete(f"/api/examenes/{ids['examen']}", headers=t["alumno"]).status_code == 403
    assert c.get(f"/api/cursos/{curso}/alumnos", headers=t["otro_profe"]).status_code == 403
    assert c.get(f"/api/analisis/segmentacion/{curso}", headers=t["otro_profe"]).status_code == 403
    assert c.post("/api/cursos", data={"nombre": "Nuevo"}, headers=t["alumno"]).status_code == 403
    assert c.post("/api/niveles", json={"curso_id": curso, "titulo": "N2"}, headers=t["profe"]).status_code in (200, 201)


def test_contenido_del_curso_solo_para_inscritos(api):
    c, ids, t = api
    ruta = f"/api/niveles/curso/{ids['curso']}/con_lecciones"
    assert c.get(ruta).status_code == 401
    assert c.get(ruta, headers=t["intruso"]).status_code == 403
    assert c.get(f"/api/preguntas/examen/{ids['examen']}", headers=t["intruso"]).status_code == 403
    niveles = c.get(ruta, headers=t["alumno"]).get_json()
    assert niveles[0]["lecciones"][0]["acceso"]


def test_examen_nunca_envia_respuestas(api):
    c, ids, t = api
    examenes = c.get(f"/api/examenes/leccion/{ids['leccion']}", headers=t["alumno"]).get_json()
    assert examenes and all("respuesta_correcta" not in p for p in examenes[0]["preguntas"])
    assert c.get(f"/api/examenes/leccion/{ids['leccion']}", headers=t["intruso"]).get_json() == []


def test_alumno_no_puede_ver_datos_de_otro_alumno(api):
    c, ids, t = api
    assert c.get(f"/api/respuestas/alumno/{ids['alumno']}", headers=t["intruso"]).status_code == 403
    assert c.get(f"/api/inscripciones/alumno/{ids['alumno']}", headers=t["intruso"]).status_code == 403
    assert c.get(f"/api/respuestas/alumno/{ids['alumno']}", headers=t["alumno"]).status_code == 200
    # El profesor del curso sí puede ver a su alumno
    assert c.get(f"/api/inscripciones/alumno/{ids['alumno']}", headers=t["profe"]).status_code == 200
    assert c.get("/api/inscripciones", headers=t["alumno"]).status_code == 403


def test_inscripcion_usa_el_alumno_del_token(api):
    c, ids, t = api
    assert c.post("/api/inscripciones", json={"curso_id": ids["curso"]}).status_code == 401
    r = c.post("/api/inscripciones", json={"curso_id": ids["curso"], "alumno_id": ids["alumno"]}, headers=t["intruso"])
    assert r.status_code in (200, 201)
    from config import config as cfg
    assert cfg.inscripciones_collection.find_one({"alumno_id": ids["intruso"]})
    assert cfg.inscripciones_collection.count_documents({"alumno_id": ids["alumno"]}) == 1


# ---------------- V-02: sesiones cortas, renovables y revocables ----------------
def test_login_da_refresh_que_rota_y_se_revoca(api):
    c, ids, t = api
    r = c.post("/api/login", json={"email": "alumno@example.com", "password": CLAVE})
    assert r.status_code == 200
    refresh = r.get_json()["refresh_token"]
    renovado = c.post("/api/token/renovar", headers={"Authorization": f"Bearer {refresh}"})
    assert renovado.status_code == 200
    nuevo = renovado.get_json()["refresh_token"]
    # El refresh anterior ya no sirve (rotación)
    assert c.post("/api/token/renovar", headers={"Authorization": f"Bearer {refresh}"}).status_code == 401
    # Cerrar sesión revoca el nuevo
    acceso = {"Authorization": f"Bearer {renovado.get_json()['access_token']}"}
    assert c.post("/api/logout", json={"refresh_token": nuevo}, headers=acceso).status_code == 200
    assert c.post("/api/token/renovar", headers={"Authorization": f"Bearer {nuevo}"}).status_code == 401


def test_login_limita_intentos_y_rechaza_inyeccion(api):
    c, ids, t = api
    assert c.post("/api/login", json={"email": {"$ne": ""}, "password": {"$ne": ""}}).status_code == 400
    for _ in range(5):
        assert c.post("/api/login", json={"email": "profe@example.com", "password": "mala"}).status_code == 401
    assert c.post("/api/login", json={"email": "profe@example.com", "password": CLAVE}).status_code == 429


def test_registro_exige_contrasena_robusta(api):
    c, ids, t = api
    r = c.post("/api/registrar", json={"nombre": "N", "email": "n@example.com", "password": "123456", "verificar_password": "123456"})
    assert r.status_code == 400


# ---------------- V-04: cabeceras ----------------
def test_cabeceras_de_seguridad(api):
    c, ids, t = api
    h = c.get("/api/cursos").headers
    assert h["X-Content-Type-Options"] == "nosniff"
    assert h["X-Frame-Options"] == "DENY"
    assert "Referrer-Policy" in h


# ---------------- V-05: archivos ----------------
def test_archivos_de_leccion_requieren_permiso_del_curso(api):
    c, ids, t = api
    assert c.get("/api/uploads/imagenes/secreto.png").status_code == 403
    assert c.get("/api/uploads/imagenes/secreto.png?acceso=falso").status_code == 403
    niveles = c.get(f"/api/niveles/curso/{ids['curso']}/con_lecciones", headers=t["alumno"]).get_json()
    permiso = niveles[0]["lecciones"][0]["acceso"]
    assert c.get(f"/api/uploads/imagenes/secreto.png?acceso={permiso}").status_code == 200
    assert c.get("/api/uploads/../app.py").status_code == 404
    assert c.get("/api/uploads/.env").status_code == 404


def test_subida_valida_tipo_real_y_usa_nombre_aleatorio(api):
    c, ids, t = api
    falso = c.post("/api/lecciones", data={"curso_id": ids["curso"], "titulo": "L",
                                           "archivos": archivo(b"<script>alert(1)</script>", "foto.png")},
                   headers=t["profe"], content_type="multipart/form-data")
    assert falso.status_code == 400
    bueno = c.post("/api/lecciones", data={"curso_id": ids["curso"], "titulo": "L",
                                           "archivos": archivo(PNG, "mi foto.png")},
                   headers=t["profe"], content_type="multipart/form-data")
    assert bueno.status_code == 201
    nombre = bueno.get_json()["archivos"][0]
    assert nombre.endswith(".png") and "foto" not in nombre and len(nombre) == 36
    otro = c.post("/api/lecciones", data={"curso_id": ids["curso"], "titulo": "L", "archivos": archivo(PNG, "a.png")},
                  headers=t["otro_profe"], content_type="multipart/form-data")
    assert otro.status_code == 403


def test_token_vencido_avisa_para_renovar(api):
    from datetime import timedelta
    from flask_jwt_extended import create_access_token
    import app as aplicacion
    c, ids, t = api
    with aplicacion.app.app_context():
        vencido = create_access_token(identity=ids["alumno"], expires_delta=timedelta(seconds=-5))
    r = c.get("/api/me", headers={"Authorization": f"Bearer {vencido}"})
    assert r.status_code == 401 and r.get_json()["codigo"] == "token_expirado"
