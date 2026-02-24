from flask import Flask
from controllers.HomeController import blueprint_home
from extensions import db, migrate, swagger
from config import Config
from flask_jwt_extended import JWTManager
from controllers.AuthController import auth_bp
from flask_cors import CORS  # 👈 IMPORTANTE


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # 👇 ACTIVAR CORS AQUÍ
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    db.init_app(app)
    migrate.init_app(app, db)
    swagger.init_app(app)

    app.config['JWT_SECRET_KEY'] = 'jwt-super-secret'
    app.config['JWT_TOKEN_LOCATION'] = ['headers']

    jwt = JWTManager(app)

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(blueprint_home)

    @app.route('/')
    def home():
        return {'mensaje': 'hola mundo'}, 200

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)