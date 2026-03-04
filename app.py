from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os

# Blueprints
from routes.User_routes import user_bp
from routes.Curso_Routes import curso_bp
from routes.estadisticas import estadisticas_bp
from routes.respaldo_routes import respaldo_bp
from routes.inscripciones_routes import inscripcion_bp
from routes.examenes_routes import examen_bp
from routes.preguntas_routes import pregunta_bp
from routes.lecciones_route import leccion_bp
from routes.respuestas_route import respuesta_bp
from routes.reportes import reportes_bp
from routes.niveles_routes import nivel_bp

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'qwertydark444'

CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
jwt = JWTManager(app)

# Registro de blueprints
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(curso_bp, url_prefix='/api')
app.register_blueprint(estadisticas_bp, url_prefix='/api')
app.register_blueprint(respaldo_bp, url_prefix='/api')
app.register_blueprint(examen_bp, url_prefix='/api')
app.register_blueprint(pregunta_bp, url_prefix='/api')
app.register_blueprint(inscripcion_bp, url_prefix='/api')
app.register_blueprint(leccion_bp, url_prefix='/api')
app.register_blueprint(respuesta_bp, url_prefix='/api')
app.register_blueprint(reportes_bp, url_prefix='/api')
app.register_blueprint(nivel_bp, url_prefix='/api')

# Carpeta de uploads
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")

# Servir archivos estáticos desde /uploads
@app.route('/api/uploads/<path:filename>')
def subir_archivo(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/')
def home():
    return render_template('correcto.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
