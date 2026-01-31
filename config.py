import os
from dotenv import load_dotenv
load_dotenv()

class Config:
    ENV = os.getenv('FLASK_ENV')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # 🔹 Clave secreta para JWT
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'clave_super_segura')

    # 🔹 Opcional: tiempo de expiración del token (ejemplo: 1 hora)
    JWT_ACCESS_TOKEN_EXPIRES = 3600  

    # 🔹 Opcional: clave secreta de Flask (para sesiones, CSRF, etc.)
    SECRET_KEY = os.environ.get('SECRET_KEY', 'otra_clave_segura')