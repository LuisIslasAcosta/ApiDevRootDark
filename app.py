from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import os
import secrets
from dotenv import load_dotenv

load_dotenv()

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
from routes.promedio_routes import spark_bp
from routes.kmeans_routes import kmeans_bp
from routes.predicciones_routes import prediccion_bp
from routes.analisis_respuestas import analisis_bp
from routes.analisis_dificultad_routes import analisis_dificultad_bp
from routes.segmentacion_routes import segmentacion_bp
from routes.ventas_routes import ventas_bp
from routes.ventas_decision_tree_routes import ventas_dt_bp
from routes.regresion_logistica_routes import regresion_logistica_bp
from routes.analisis_progreso_routes import analisis_progreso_bp
from routes.recomendaciones_routes import recomendacion_bp
from routes.segmentacion_alumnos_routes import segmentacion_alumnos_bp
from routes.proxy_routes import proxy_bp
from routes.importar_excel import excel_bp
from routes.progreso_academico_routes import progreso_academico_bp

app = Flask(__name__)
# Clave JWT desde .env (nunca escrita en el código)
jwt_secret = os.getenv('JWT_SECRET_KEY')
if not jwt_secret:
    jwt_secret = secrets.token_hex(32)
    print("ADVERTENCIA: JWT_SECRET_KEY no está en .env; se generó una temporal "
          "(las sesiones se cerrarán cada vez que se reinicie la API).")
app.config['JWT_SECRET_KEY'] = jwt_secret

# Tamaño máximo de archivos subidos (MB), configurable desde .env
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_MB', '200')) * 1024 * 1024

# Orígenes permitidos (separados por coma en .env)
cors_origins = [o.strip() for o in os.getenv(
    'CORS_ORIGINS', 'http://localhost:5173').split(',') if o.strip()]

CORS(app,
     resources={r"/api/*": {"origins": cors_origins}},
     supports_credentials=True)

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
app.register_blueprint(spark_bp, url_prefix='/api')
app.register_blueprint(analisis_bp, url_prefix='/api')
app.register_blueprint(prediccion_bp, url_prefix='/api')
app.register_blueprint(analisis_dificultad_bp, url_prefix='/api')
app.register_blueprint(segmentacion_bp, url_prefix='/api')
app.register_blueprint(analisis_progreso_bp, url_prefix='/api')
app.register_blueprint(recomendacion_bp, url_prefix='/api')
app.register_blueprint(ventas_bp, url_prefix='/api')
app.register_blueprint(ventas_dt_bp, url_prefix='/api')
app.register_blueprint(regresion_logistica_bp, url_prefix='/api')
app.register_blueprint(kmeans_bp, url_prefix='/api')
app.register_blueprint(segmentacion_alumnos_bp, url_prefix='/api')
app.register_blueprint(proxy_bp, url_prefix='/api')
app.register_blueprint(excel_bp, url_prefix='/api')
app.register_blueprint(progreso_academico_bp, url_prefix='/api')


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
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')),
            debug=os.getenv('FLASK_DEBUG', '0') == '1')
