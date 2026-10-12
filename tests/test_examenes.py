"""Pruebas reales del módulo de exámenes.

Valida que los exámenes se registren con la estructura correcta y que se puedan
eliminar sin depender de falsos mocks de la base de datos.
"""

from bson.objectid import ObjectId

from models.Examen import eliminar_examen, registrar_examen


def test_registrar_examen_guarda_documento_y_devuelve_id(flask_app, memory_collections):
    response, status = registrar_examen(
        curso_id="curso_123",
        titulo="Examen 1",
        fecha="2026-10-11",
        leccion_id="leccion_1",
        nivel_id="nivel_1",
        preguntas=[{"enunciado": "¿Cuánto es 2 + 2?"}],
    )

    assert status == 201
    payload = response.get_json()
    assert ObjectId.is_valid(payload["examen_id"]) is True

    examen = memory_collections["examenes"].data[0]
    assert examen["curso_id"] == "curso_123"
    assert examen["titulo"] == "Examen 1"
    assert examen["preguntas"][0]["enunciado"] == "¿Cuánto es 2 + 2?"


def test_eliminar_examen_devuelve_true_y_borra_doc(memory_collections):
    examen_id = ObjectId("507f1f77bcf86cd799439016")
    memory_collections["examenes"].insert_one({"_id": examen_id, "titulo": "Examen 2"})

    assert eliminar_examen(str(examen_id)) is True
    assert memory_collections["examenes"].find_one({"_id": examen_id}) is None
