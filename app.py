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
from routes.chat_routes import chat_bp
from routes.certificados_routes import certificados_bp
from routes.intentos_routes import intento_bp
from routes.firmas_routes import firmas_bp
from routes.musica_routes import musica_bp

app = Flask(__name__)
# Clave JWT desde .env (nunca escrita en el código)
jwt_secret = os.getenv('JWT_SECRET_KEY')
if not jwt_secret:
    jwt_secret = secrets.token_hex(32)
    print("ADVERTENCIA: JWT_SECRET_KEY no está en .env; se generó una temporal "
          "(las sesiones se cerrarán cada vez que se reinicie la API).")
app.config['JWT_SECRET_KEY'] = jwt_secret
# Tokens de acceso cortos y de renovación revocables (ver controllers/sesiones.py)
from controllers.sesiones import DURACION_ACCESO, DURACION_RENOVACION, renovacion_vigente
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = DURACION_ACCESO
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = DURACION_RENOVACION
app.config['JWT_TOKEN_LOCATION'] = ['headers']

# Tamaño máximo de archivos subidos (MB), configurable desde .env
app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_UPLOAD_MB', '200')) * 1024 * 1024

# Orígenes permitidos: los del frontend oficial siempre, más los que se agreguen en .env (CORS_ORIGINS)
FRONTENDS_OFICIALES = [
    'https://devrootdark.netlify.app',
    'http://localhost:5173',
]
cors_origins = list(dict.fromkeys(
    FRONTENDS_OFICIALES + [o.strip().rstrip('/') for o in os.getenv('CORS_ORIGINS', '').split(',') if o.strip()]
))

CORS(app,
     resources={r"/api/*": {"origins": cors_origins}},
     supports_credentials=True)

jwt = JWTManager(app)


# Los tokens de renovación se pueden revocar (cerrar sesión, cambio de contraseña)
@jwt.token_in_blocklist_loader
def token_revocado(_cabecera, datos):
    if datos.get("type") != "refresh":
        return False
    return not renovacion_vigente(datos.get("jti"))


# Respuestas de error del token en el mismo formato que el resto de la API
def _error_token(mensaje, codigo=401, clave="sin_sesion"):
    return jsonify({"mensaje": mensaje, "message": mensaje, "codigo": clave}), codigo


jwt.expired_token_loader(lambda _c, _d: _error_token("Tu sesión expiró. Inicia sesión de nuevo.", 401, "token_expirado"))
jwt.invalid_token_loader(lambda _m: _error_token("Sesión no válida. Inicia sesión de nuevo.", 401))
jwt.unauthorized_loader(lambda _m: _error_token("Inicia sesión para continuar.", 401))
jwt.revoked_token_loader(lambda _c, _d: _error_token("La sesión se cerró. Inicia sesión de nuevo.", 401, "token_revocado"))
jwt.needs_fresh_token_loader(lambda _c, _d: _error_token("Por seguridad, vuelve a escribir tu contraseña para continuar.", 401, "requiere_contrasena"))


# Cabeceras de seguridad en todas las respuestas de la API
@app.after_request
def cabeceras_seguridad(respuesta):
    respuesta.headers.setdefault("X-Content-Type-Options", "nosniff")
    respuesta.headers.setdefault("X-Frame-Options", "DENY")
    respuesta.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    respuesta.headers.setdefault("Cross-Origin-Resource-Policy", "cross-origin")
    if respuesta.mimetype == "application/json":
        respuesta.headers.setdefault("Cache-Control", "no-store")
    return respuesta

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
app.register_blueprint(chat_bp, url_prefix='/api')
app.register_blueprint(certificados_bp, url_prefix='/api')
app.register_blueprint(intento_bp, url_prefix='/api')
app.register_blueprint(firmas_bp, url_prefix='/api')
app.register_blueprint(musica_bp, url_prefix='/api')


# Archivos subidos: se entregan con validación (los de lecciones requieren permiso del curso)
from utils.archivos import entregar

@app.route('/api/uploads/<path:filename>')
def subir_archivo(filename):
    return entregar(filename)

@app.route('/')
def home():
    return render_template('correcto.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', '5000')),
            debug=os.getenv('FLASK_DEBUG', '0') == '1')
