"""Pruebas reales del módulo de usuarios.

Estas pruebas validan el flujo de registro, validación de credenciales,
serialización de datos, actualización y eliminación de usuarios usando una
colección en memoria en lugar de mocks falsos.
"""

import base64

import pytest
from bson.objectid import ObjectId

from controllers import user as ctrl
from models import User as modelo

OID = "507f1f77bcf86cd799439011"


def json_de(respuesta):
    resp, status = respuesta
    return resp.get_json(), status


def test_registrar_usuario_crea_admin_con_matricula_inicial(flask_app, memory_collections, valid_user_data):
    response, status = modelo.registrar_usuario(**valid_user_data)

    assert status == 201
    payload = response.get_json()
    assert payload["matricula"] == "000000001"
    assert payload["rol"] == "administrador"

    usuario = memory_collections["usuarios"].data[0]
    assert usuario["email"] == valid_user_data["email"]
    assert usuario["password"] != valid_user_data["password"]
    assert usuario["respuesta_seguridad"] != valid_user_data["respuesta_seguridad"]
    assert usuario["rol"] == "administrador"


def test_registrar_usuario_rechaza_contraseñas_distintas(flask_app, memory_collections, valid_user_data):
    payload, status = json_de(modelo.registrar_usuario(**{**valid_user_data, "verificar_password": "Otra#Clave123"}))

    assert status == 400
    assert payload["mensaje"] == "Las contraseñas no coinciden"
    assert memory_collections["usuarios"].data == []


@pytest.mark.parametrize("email", [
    "sin-arroba.com",
    "ana@",
    "@correo.com",
    "ana@correo",
    "ana correo@x.com",
    "",
])
def test_registrar_usuario_rechaza_email_invalido(flask_app, memory_collections, valid_user_data, email):
    payload, status = json_de(modelo.registrar_usuario(**{**valid_user_data, "email": email}))

    assert status == 400
    assert payload["mensaje"] == "Formato de correo electrónico inválido"


@pytest.mark.parametrize("password, mensaje", [
    ("Ab1!", "La contraseña debe tener al menos 12 caracteres"),
    ("abcdefghijk1!", "Debe incluir al menos una letra mayúscula"),
    ("ABCDEFGHIJK1!", "Debe incluir al menos una letra minúscula"),
    ("Abcdefghijkl!", "Debe incluir al menos un número"),
    ("Abcdefghijkl1", "Debe incluir al menos un carácter especial"),
    ("Password1234!", "Evita usar palabras comunes"),
    ("MiQWERTY1234!", "Evita usar palabras comunes"),
])
def test_registrar_usuario_rechaza_contrasena_insegura(flask_app, memory_collections, valid_user_data, password, mensaje):
    payload, status = json_de(modelo.registrar_usuario(**{**valid_user_data, "password": password, "verificar_password": password}))

    assert status == 400
    assert payload["mensaje"] == mensaje


def test_registrar_usuario_rechaza_email_duplicado(flask_app, memory_collections, valid_user_data):
    memory_collections["usuarios"].insert_one({"email": valid_user_data["email"]})

    payload, status = json_de(modelo.registrar_usuario(**valid_user_data))

    assert status == 400
    assert payload["mensaje"] == "El correo electrónico ya está registrado"


def test_registrar_usuario_guarda_imagen_si_viene_completa(flask_app, memory_collections, valid_user_data):
    modelo.registrar_usuario(
        **{**valid_user_data, "imagen_binaria": b"\x89PNG", "imagen_nombre": "foto.png", "imagen_tipo": "image/png"}
    )

    usuario = memory_collections["usuarios"].data[0]
    assert usuario["imagen_perfil"] == {
        "nombre": "foto.png",
        "tipo": "image/png",
        "contenido": b"\x89PNG",
    }


def test_registrar_usuario_ignora_imagen_incompleta(flask_app, memory_collections, valid_user_data):
    modelo.registrar_usuario(**{**valid_user_data, "imagen_nombre": "foto.png"})

    usuario = memory_collections["usuarios"].data[0]
    assert "imagen_perfil" not in usuario


def test_actualizar_contrasena_cambia_hash_y_devuelve_true(memory_collections):
    usuario_id = ObjectId()
    memory_collections["usuarios"].insert_one({"_id": usuario_id, "password": "viejo"})

    assert modelo.actualizar_contraseña(str(usuario_id), "Nueva#Clave12345") is True
    usuario = memory_collections["usuarios"].find_one({"_id": usuario_id})
    assert usuario["password"] != "viejo"
    assert usuario["password"] != "Nueva#Clave12345"


def test_obtener_usuarios_serializa_y_oculta_campos_sensibles(memory_collections):
    usuario_1 = {"_id": ObjectId(OID), "matricula": "000000001", "nombre": "Ana", "email": "ana@correo.com", "rol": "administrador", "password": "hash-secreto"}
    usuario_2 = {"_id": ObjectId(), "matricula": "000000002", "nombre": "Luis", "email": "luis@correo.com", "rol": "usuario", "password": "otro-hash"}
    memory_collections["usuarios"].insert_one(usuario_1)
    memory_collections["usuarios"].insert_one(usuario_2)

    usuarios = ctrl.obtener_usuarios()

    assert [u["nombre"] for u in usuarios] == ["Ana", "Luis"]
    assert usuarios[0]["id"] == OID
    assert "password" not in usuarios[0]
    assert "password" not in usuarios[1]


def test_obtener_usuario_por_id_devuelve_usuario_con_id_string(memory_collections):
    usuario = {"_id": ObjectId(OID), "matricula": "000000001", "nombre": "Ana", "rol": "usuario"}
    memory_collections["usuarios"].insert_one(usuario)

    resultado = ctrl.obtener_usuario_por_id(OID)

    assert resultado["id"] == OID
    assert resultado["nombre"] == "Ana"


def test_actualizar_usuario_ignora_password_y_actualiza_datos(memory_collections):
    usuario_id = ObjectId(OID)
    memory_collections["usuarios"].insert_one({"_id": usuario_id, "nombre": "Ana", "password": "viejo"})

    actualizado = ctrl.actualizar_usuario(str(usuario_id), {"nombre": "Ana Actualizada", "password": "intento"})

    assert actualizado is True
    usuario = memory_collections["usuarios"].find_one({"_id": usuario_id})
    assert usuario["nombre"] == "Ana Actualizada"
    assert usuario["password"] == "viejo"


def test_eliminar_usuario_devuelve_true_si_existe(memory_collections):
    usuario_id = ObjectId(OID)
    memory_collections["usuarios"].insert_one({"_id": usuario_id, "nombre": "Ana"})

    assert ctrl.eliminar_usuario(str(usuario_id)) is True
    assert memory_collections["usuarios"].find_one({"_id": usuario_id}) is None


def test_serializar_usuario_convierte_foto_bytes_a_base64():
    usuario = {"_id": ObjectId(OID), "foto_perfil": b"hola"}

    serializado = ctrl.serializar_usuario(usuario)

    assert serializado["foto_perfil"] == base64.b64encode(b"hola").decode("utf-8")


def test_obtener_usuarios_recientes_ordenados_por_id_desc(memory_collections):
    primer = ObjectId("507f1f77bcf86cd799439011")
    segundo = ObjectId("507f1f77bcf86cd799439012")
    memory_collections["usuarios"].insert_one({"_id": primer, "nombre": "Primero"})
    memory_collections["usuarios"].insert_one({"_id": segundo, "nombre": "Segundo"})

    usuarios = ctrl.obtener_usuarios_recientes(limit=2)

    assert [u["nombre"] for u in usuarios] == ["Segundo", "Primero"]
