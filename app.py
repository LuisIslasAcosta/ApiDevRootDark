from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from routes.User_routes import user_bp
from routes.Curso_Routes import curso_bp
from routes.estadisticas import estadisticas_bp
from routes.respaldo_routes import respaldo_bp


app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'qwertydark444'

CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
jwt = JWTManager(app)

app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(curso_bp, url_prefix='/api')
app.register_blueprint(estadisticas_bp, url_prefix='/api')
app.register_blueprint(respaldo_bp, url_prefix='/api')

@app.route('/')
def home():
    return render_template('correcto.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)