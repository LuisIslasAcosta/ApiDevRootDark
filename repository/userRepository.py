from models.user import User
from extensions import db


class UserRepository:

    @staticmethod
    def create(data):
        user = User(
            nombre=data.get("nombre"),
            apellidop=data.get("apellidop"),
            apellidom=data.get("apellidom"),
            fecha_nacimiento=data.get("fecha_nacimiento"),
            pais=data.get("pais"),
            ciudad=data.get("ciudad"),
            email=data.get("email"),
            pregunta_seguridad=data.get("pregunta_seguridad"),
            respuesta_seguridad=data.get("respuesta_seguridad"),
            telefono=data.get("telefono"),
            foto_perfil=data.get("foto_perfil"),
            rol="usuario"
        )

        user.set_password(data.get("password"))

        db.session.add(user)
        db.session.commit()

        return user

    @staticmethod
    def obtener_usuario_por_id(user_id):
        return User.query.get(user_id)

    @staticmethod
    def find_by_email(email):
        return User.query.filter_by(email=email).first()