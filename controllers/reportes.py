from config.config import respuestas_collection, usuarios_collection, examenes_collection, cursos_collection
from bson.objectid import ObjectId

def obtener_reportes_profesor(profesor_id):
    reportes = []

    try:
        profesor_object_id = ObjectId(profesor_id)
    except:
        print(" profesor_id inválido")
        return []

    respuestas = respuestas_collection.find()

    for r in respuestas:
        #  Convertir examen_id correctamente
        try:
            examen_id = ObjectId(r["examen_id"])
        except:
            print(" examen_id inválido:", r.get("examen_id"))
            continue

        examen = examenes_collection.find_one({"_id": examen_id})
        if not examen:
            print(" examen no encontrado")
            continue

        #  Convertir curso_id correctamente
        try:
            curso_id = ObjectId(examen["curso_id"])
        except:
            print(" curso_id inválido")
            continue

        curso = cursos_collection.find_one({"_id": curso_id})
        if not curso:
            print(" curso no encontrado")
            continue

        #  CAMPO REAL DE LA DB
        curso_profesor = curso.get("profesor")

        try:
            curso_profesor = ObjectId(curso_profesor)
        except:
            print(" profesor inválido en curso")
            continue

        #  Si no coincide → ignorar
        if curso_profesor != profesor_object_id:
            continue

        #  Buscar alumno
        try:
            alumno_id = ObjectId(r["alumno_id"])
        except:
            alumno_id = None

        alumno = usuarios_collection.find_one({"_id": alumno_id}) if alumno_id else None

        reportes.append({
            "alumno": alumno.get("nombre", "Usuario eliminado") if alumno else "Usuario eliminado",
            "email": alumno.get("email", "") if alumno else "",
            "curso": curso.get("nombre", "Curso sin nombre"),
            "examen": examen.get("titulo", "Examen sin título"),
            "correctas": r.get("correctas", 0),
            "total": r.get("total", 0),
            "calificacion": r.get("calificacion", 0),
            "fecha": examen.get("fecha", "")
        })

    print(" REPORTES ENVIADOS:", len(reportes))
    return reportes
