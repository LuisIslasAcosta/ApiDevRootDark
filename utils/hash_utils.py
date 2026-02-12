from werkzeug.security import generate_password_hash, check_password_hash

def hash_contraseña(texto):
    return generate_password_hash(texto)

def verificar_hash(texto, hash_guardado):
    return check_password_hash(hash_guardado, texto)
