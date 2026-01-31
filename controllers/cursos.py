from models.models import Curso, Imagen, Video
from extensions import db

def serializar_curso(curso: Curso):
    return {
        "id": curso.id,
        "nombre": curso.nombre,
        "descripcion": curso.descripcion,
        "profesor_id": curso.profesor_id,
        "fecha_inicio": curso.fecha_inicio,
        "fecha_fin": curso.fecha_fin,
        "imagenes": [{"id": i.id, "nombre": i.nombre, "tipo": i.tipo} for i in curso.imagenes],
        "videos": [{"id": v.id, "titulo": v.titulo, "url": v.url} for v in curso.videos]
    }

def obtener_cursos():
    cursos = Curso.query.all()
    return [serializar_curso(c) for c in cursos]

def obtener_curso_por_id(curso_id):
    curso = Curso.query.get(curso_id)
    return serializar_curso(curso) if curso else None

def actualizar_curso(curso_id, datos_actualizados):
    curso = Curso.query.get(curso_id)
    if not curso:
        return False
    for campo, valor in datos_actualizados.items():
        if hasattr(curso, campo):
            setattr(curso, campo, valor)
    db.session.commit()
    return True

def eliminar_curso(curso_id):
    curso = Curso.query.get(curso_id)
    if not curso:
        return False
    db.session.delete(curso)
    db.session.commit()
    return True

# 🔹 Crear curso
def registrar_curso(nombre, descripcion, profesor_id, fecha_inicio, fecha_fin, imagenes=None, videos=None):
    # Verificar si ya existe un curso con el mismo nombre
    if Curso.query.filter_by(nombre=nombre).first():
        return {"mensaje": "El curso ya existe"}, 400

    nuevo_curso = Curso(
        nombre=nombre,
        descripcion=descripcion,
        profesor_id=profesor_id,
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin
    )

    # Agregar imágenes si vienen en la petición
    if imagenes:
        for img in imagenes:
            nueva_img = Imagen(
                nombre=img.get("nombre"),
                tipo=img.get("tipo"),
                contenido=img.get("contenido")
            )
            nuevo_curso.imagenes.append(nueva_img)

    # Agregar videos si vienen en la petición
    if videos:
        for vid in videos:
            nuevo_vid = Video(
                titulo=vid.get("titulo"),
                url=vid.get("url"),
                descripcion=vid.get("descripcion")
            )
            nuevo_curso.videos.append(nuevo_vid)

    db.session.add(nuevo_curso)
    try:
        db.session.commit()
        return {"mensaje": "Curso registrado correctamente", "curso": serializar_curso(nuevo_curso)}, 201
    except Exception as e:
        db.session.rollback()
        return {"mensaje": f"Error al registrar curso: {str(e)}"}, 500