from extensions import db
from passlib.hash import bcrypt


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100))
    apellidop = db.Column(db.String(100))
    apellidom = db.Column(db.String(100))
    fecha_nacimiento = db.Column(db.String(20))
    pais = db.Column(db.String(100))
    ciudad = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)
    pregunta_seguridad = db.Column(db.String(200))
    respuesta_seguridad = db.Column(db.String(200))
    telefono = db.Column(db.String(20))
    foto_perfil = db.Column(db.String(250))
    rol = db.Column(db.String(50), default="usuario")

    def set_password(self, password: str):
        self.password = bcrypt.hash(password)

    def check_password(self, password: str) -> bool:
        return bcrypt.verify(password, self.password)

    def to_dict(self):
        return {
            "id": self.id,
            "nombre": self.nombre,
            "apellidop": self.apellidop,
            "apellidom": self.apellidom,
            "fecha_nacimiento": self.fecha_nacimiento,
            "pais": self.pais,
            "ciudad": self.ciudad,
            "email": self.email,
            "telefono": self.telefono,
            "foto_perfil": self.foto_perfil,
            "rol": self.rol
        }