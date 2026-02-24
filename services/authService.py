from repository.userRepository import UserRepository
from flask_jwt_extended import create_access_token
from datetime import timedelta


class AuthService:

    @staticmethod
    def register(data):
        return UserRepository.create(data)

    @staticmethod
    def obtener_usuario_por_id(user_id):
        return UserRepository.obtener_usuario_por_id(user_id)

    @staticmethod
    def login(email, password):
        user = UserRepository.find_by_email(email)

        if not user:
            return None

        if not user.check_password(password):
            return None

        claims = {
            "email": user.email,
            "rol": user.rol
        }

        token = create_access_token(
            identity=str(user.id),
            additional_claims=claims,
            expires_delta=timedelta(hours=8)
        )

        return {
            "access_token": token,
            "usuario": user
        }