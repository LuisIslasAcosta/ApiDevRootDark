from werkzeug.security import generate_password_hash, check_password_hash

def hash_contraseña(contraseña):
    return generate_password_hash(contraseña)

def verificar_contraseña(contraseña_hash, contraseña):
    return check_password_hash(contraseña_hash, contraseña)