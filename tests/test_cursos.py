"""Pruebas reales del módulo de cursos.

Se verifican las operaciones principales de creación, lectura, actualización y
borrado de cursos, así como la validación de duplicados y serialización del
profesor asociado.
"""

from bson.objectid import ObjectId

from controllers.cursos import actualizar_curso, eliminar_curso, obtener_curso_por_id, obtener_cursos
from models.Curso import registrar_curso


def test_registrar_curso_crea_documento_con_datos_validos(flask_app, memory_collections):
    response, status = registrar_curso(
        nombre="Python desde cero",
        descripcion="Curso práctico de Python",
        profesor="507f1f77bcf86cd799439011",
        precio="299.99",
        imagenes=["a.png"],
        videos=["intro.mp4"],
    )

    assert status == 201
    payload = response.get_json()
    assert payload["mensaje"] == "Curso registrado correctamente"
    assert payload["curso"]["nombre"] == "Python desde cero"
    assert payload["curso"]["precio"] == 299.99

    curso = memory_collections["cursos"].data[0]
    assert curso["nombre"] == "Python desde cero"
    assert curso["precio"] == 299.99
    assert curso["videos"] == ["intro.mp4"]


def test_registrar_curso_rechaza_nombre_duplicado(flask_app, memory_collections):
    memory_collections["cursos"].insert_one({"nombre": "Python desde cero"})

    response, status = registrar_curso(
        nombre="Python desde cero",
        descripcion="Otro curso",
        profesor="507f1f77bcf86cd799439011",
        precio="150",
    )

    assert status == 400
    assert response.get_json()["mensaje"] == "El curso ya existe"


def test_obtener_cursos_devuelve_lista_serializada(memory_collections):
    profesor_id = ObjectId("507f1f77bcf86cd799439011")
    memory_collections["usuarios"].insert_one({"_id": profesor_id, "nombre": "Ana", "apellidop": "Pérez"})
    memory_collections["cursos"].insert_one({
        "_id": ObjectId("507f1f77bcf86cd799439012"),
        "nombre": "Curso A",
        "descripcion": "desc",
        "profesor": profesor_id,
        "precio": 199,
        "imagenes": [],
        "videos": [],
    })

    cursos = obtener_cursos()

    assert len(cursos) == 1
    assert cursos[0]["nombre"] == "Curso A"
    assert cursos[0]["profesor"] == "Ana Pérez"
    assert cursos[0]["profesor_id"] == "507f1f77bcf86cd799439011"


def test_obtener_curso_por_id_retorna_curso_correcto(memory_collections):
    curso_id = ObjectId("507f1f77bcf86cd799439013")
    profesor_id = ObjectId("507f1f77bcf86cd799439011")
    memory_collections["usuarios"].insert_one({"_id": profesor_id, "nombre": "Luis", "apellidop": "García"})
    memory_collections["cursos"].insert_one({
        "_id": curso_id,
        "nombre": "Curso B",
        "descripcion": "descripcion",
        "profesor": profesor_id,
        "precio": 250,
    })

    curso = obtener_curso_por_id(str(curso_id))

    assert curso is not None
    assert curso["nombre"] == "Curso B"
    assert curso["profesor"] == "Luis García"


def test_actualizar_curso_cambia_datos_reales(memory_collections):
    curso_id = ObjectId("507f1f77bcf86cd799439014")
    memory_collections["cursos"].insert_one({
        "_id": curso_id,
        "nombre": "Curso C",
        "descripcion": "viejo",
        "precio": 100,
    })

    actualizado = actualizar_curso(str(curso_id), {"descripcion": "nuevo", "precio": 199})

    assert actualizado is True
    curso = memory_collections["cursos"].find_one({"_id": curso_id})
    assert curso["descripcion"] == "nuevo"
    assert curso["precio"] == 199


def test_eliminar_curso_devuelve_true_y_lo_quita(memory_collections):
    curso_id = ObjectId("507f1f77bcf86cd799439015")
    memory_collections["cursos"].insert_one({"_id": curso_id, "nombre": "Curso D"})

    assert eliminar_curso(str(curso_id)) is True
    assert memory_collections["cursos"].find_one({"_id": curso_id}) is None
