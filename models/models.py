from extensions import db
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.mysql import LONGTEXT
from utils.hash_utils import hash_contraseña

# -------------------------------
# Usuarios
# -------------------------------
class User(db.Model):
    __tablename__ = 'usuarios'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    matricula = db.Column(db.String(9), unique=True, nullable=False)
    nombre = db.Column(db.String(100), nullable=False)
    apellidop = db.Column(db.String(100), nullable=False)
    apellidom = db.Column(db.String(100), nullable=False)
    fecha_nacimiento = db.Column(db.Date, nullable=False)
    pais = db.Column(db.String(100), nullable=False)
    ciudad = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    telefono = db.Column(db.String(20))
    password = db.Column(db.String(255), nullable=False)
    foto_perfil = db.Column(db.LargeBinary)  # imagen binaria
    pregunta_seguridad = db.Column(db.String(255), nullable=False)
    respuesta_seguridad = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), nullable=False)

    # Relaciones
    cursos = relationship("Curso", back_populates="profesor_rel")
    inscripciones = relationship("Inscripcion", back_populates="usuario")
    intentos = relationship("IntentoExamen", back_populates="usuario")

    def set_password(self, nueva_contraseña):
        self.password = hash_contraseña(nueva_contraseña)



# -------------------------------
# Cursos
# -------------------------------
class Curso(db.Model):
    __tablename__ = 'cursos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False)
    descripcion = db.Column(db.Text)
    fecha_inicio = db.Column(db.Date)
    fecha_fin = db.Column(db.Date)

    profesor_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    profesor_rel = relationship("User", back_populates="cursos")

    # Relaciones
    imagenes = relationship("Imagen", back_populates="curso", cascade="all, delete-orphan")
    videos = relationship("Video", back_populates="curso", cascade="all, delete-orphan")
    lecciones = relationship("Leccion", back_populates="curso", cascade="all, delete-orphan")
    inscripciones = relationship("Inscripcion", back_populates="curso")
    examenes = relationship("Examen", back_populates="curso")


# -------------------------------
# Imágenes de curso
# -------------------------------
class Imagen(db.Model):
    __tablename__ = 'imagenes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nombre = db.Column(db.String(150))
    tipo = db.Column(db.String(50))  # jpg, png, etc.
    contenido = db.Column(db.LargeBinary)

    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'))
    curso = relationship("Curso", back_populates="imagenes")


# -------------------------------
# Videos de curso
# -------------------------------
class Video(db.Model):
    __tablename__ = 'videos'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(150))
    url = db.Column(db.String(255))
    descripcion = db.Column(db.Text)

    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'))
    curso = relationship("Curso", back_populates="videos")


# -------------------------------
# Lecciones
# -------------------------------
class Leccion(db.Model):
    __tablename__ = 'lecciones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(150), nullable=False)
    contenido = db.Column(LONGTEXT)

    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'))
    curso = relationship("Curso", back_populates="lecciones")

    examenes = relationship("Examen", back_populates="leccion")


# -------------------------------
# Exámenes
# -------------------------------
class Examen(db.Model):
    __tablename__ = 'examenes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(150), nullable=False)

    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'))
    curso = relationship("Curso", back_populates="examenes")

    leccion_id = db.Column(db.Integer, db.ForeignKey('lecciones.id'))
    leccion = relationship("Leccion", back_populates="examenes")

    preguntas = relationship("Pregunta", back_populates="examen", cascade="all, delete-orphan")
    intentos = relationship("IntentoExamen", back_populates="examen")


# -------------------------------
# Preguntas
# -------------------------------
class Pregunta(db.Model):
    __tablename__ = 'preguntas'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    texto = db.Column(db.Text, nullable=False)

    examen_id = db.Column(db.Integer, db.ForeignKey('examenes.id'))
    examen = relationship("Examen", back_populates="preguntas")

    opciones = relationship("Opcion", back_populates="pregunta", cascade="all, delete-orphan")


# -------------------------------
# Opciones de respuesta
# -------------------------------
class Opcion(db.Model):
    __tablename__ = 'opciones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    texto = db.Column(db.String(255), nullable=False)
    es_correcta = db.Column(db.Boolean, default=False)

    pregunta_id = db.Column(db.Integer, db.ForeignKey('preguntas.id'))
    pregunta = relationship("Pregunta", back_populates="opciones")


# -------------------------------
# Inscripciones (usuarios ↔ cursos)
# -------------------------------
class Inscripcion(db.Model):
    __tablename__ = 'inscripciones'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    curso_id = db.Column(db.Integer, db.ForeignKey('cursos.id'))
    progreso = db.Column(db.Float, default=0.0)  # porcentaje de avance

    usuario = relationship("User", back_populates="inscripciones")
    curso = relationship("Curso", back_populates="inscripciones")


# -------------------------------
# Intentos de examen
# -------------------------------
class IntentoExamen(db.Model):
    __tablename__ = 'intentos_examen'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'))
    examen_id = db.Column(db.Integer, db.ForeignKey('examenes.id'))
    fecha = db.Column(db.DateTime)
    puntaje = db.Column(db.Float)

    usuario = relationship("User", back_populates="intentos")
    examen = relationship("Examen", back_populates="intentos")