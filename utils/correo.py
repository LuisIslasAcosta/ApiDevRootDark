"""
Envío de correos de DevRootDark (confirmación de cuenta).

Configuración en .env (ejemplo con Gmail y contraseña de aplicación):
    MAIL_SERVER=smtp.gmail.com
    MAIL_PORT=465
    MAIL_USERNAME=tucorreo@gmail.com
    MAIL_PASSWORD=abcdefghijklmnop      (contraseña de aplicación de 16 letras)
    MAIL_FROM_NAME=DevRootDark
    FRONTEND_URL=https://darling-scone-5f7dba.netlify.app
"""
import os
import smtplib
import ssl
from email.message import EmailMessage
from email.utils import formataddr, make_msgid

from flask import current_app
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired

import dns.resolver

SAL_VERIFICACION = "devrootdark-verificar-correo"
VIGENCIA_SEGUNDOS = 24 * 60 * 60  # 24 horas


# ---------------------------------------------------------------- Tokens
def _serializador():
    secreto = current_app.config.get("JWT_SECRET_KEY") or os.getenv("JWT_SECRET_KEY")
    return URLSafeTimedSerializer(secreto, salt=SAL_VERIFICACION)


def crear_token_verificacion(email):
    return _serializador().dumps(email.lower())


def leer_token_verificacion(token):
    """Devuelve (email, None) o (None, 'expirado' | 'invalido')."""
    try:
        return _serializador().loads(token, max_age=VIGENCIA_SEGUNDOS), None
    except SignatureExpired:
        return None, "expirado"
    except BadSignature:
        return None, "invalido"


# ---------------------------------------------------------------- Dominio real
def dominio_recibe_correo(email):
    """True si el dominio del correo tiene servidor de correo (registros MX)."""
    dominio = email.rsplit("@", 1)[-1].strip().lower()
    try:
        respuestas = dns.resolver.resolve(dominio, "MX", lifetime=5)
        return len(respuestas) > 0
    except (dns.resolver.NXDOMAIN, dns.resolver.NoAnswer):
        return False  # el dominio no existe o no recibe correos
    except Exception:
        # Falla de red o del DNS (no del dominio): no bloqueamos el registro
        return True


# ---------------------------------------------------------------- Envío
def correo_configurado():
    return bool(os.getenv("MAIL_USERNAME") and os.getenv("MAIL_PASSWORD"))


def url_frontend():
    url = os.getenv("FRONTEND_URL")
    if not url:
        origenes = [o.strip() for o in os.getenv("CORS_ORIGINS", "").split(",") if o.strip().startswith("https://")]
        url = origenes[0] if origenes else "http://localhost:5173"
    return url.rstrip("/")


def _enviar(destinatario, asunto, texto, html):
    if not correo_configurado():
        raise RuntimeError("El envío de correos no está configurado (MAIL_USERNAME / MAIL_PASSWORD).")

    usuario = os.getenv("MAIL_USERNAME")
    msg = EmailMessage()
    msg["Subject"] = asunto
    msg["From"] = formataddr((os.getenv("MAIL_FROM_NAME", "DevRootDark"), usuario))
    msg["To"] = destinatario
    msg["Message-ID"] = make_msgid(domain=usuario.split("@")[-1])
    msg.set_content(texto)
    msg.add_alternative(html, subtype="html")

    servidor = os.getenv("MAIL_SERVER", "smtp.gmail.com")
    puerto = int(os.getenv("MAIL_PORT", "465"))
    contexto = ssl.create_default_context()
    if puerto == 465:
        with smtplib.SMTP_SSL(servidor, puerto, context=contexto, timeout=20) as smtp:
            smtp.login(usuario, os.getenv("MAIL_PASSWORD"))
            smtp.send_message(msg)
    else:
        with smtplib.SMTP(servidor, puerto, timeout=20) as smtp:
            smtp.starttls(context=contexto)
            smtp.login(usuario, os.getenv("MAIL_PASSWORD"))
            smtp.send_message(msg)


def enviar_correo_verificacion(email, nombre):
    """Envía el correo con el enlace para confirmar la cuenta."""
    base = url_frontend()
    enlace = f"{base}/verificar-correo?token={crear_token_verificacion(email)}"
    nombre = (nombre or "").strip() or "Hola"

    texto = (
        f"{nombre}, gracias por registrarte en DevRootDark.\n\n"
        f"Confirma tu correo abriendo este enlace (válido por 24 horas):\n{enlace}\n\n"
        "Si tú no creaste esta cuenta, ignora este mensaje."
    )

    html = f"""<!DOCTYPE html>
<html lang="es">
<body style="margin:0;padding:0;background:#eef1f6;font-family:Segoe UI,Roboto,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#eef1f6;padding:32px 12px;">
    <tr><td align="center">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="max-width:560px;background:#ffffff;border-radius:16px;overflow:hidden;box-shadow:0 8px 24px rgba(10,12,24,.08);">
        <tr><td align="center" style="background:#0a0c18;padding:28px 24px;">
          <img src="{base}/icons/logo-banner.png" width="300" alt="DevRootDark" style="display:block;width:300px;max-width:100%;height:auto;border:0;">
        </td></tr>
        <tr><td style="padding:32px 32px 8px;color:#1f2937;">
          <h1 style="margin:0 0 12px;font-size:22px;">¡Bienvenido, {nombre}!</h1>
          <p style="margin:0 0 16px;font-size:15px;line-height:1.6;color:#4b5563;">
            Gracias por crear tu cuenta en <strong>DevRootDark</strong>. Solo falta confirmar que este correo es tuyo.
          </p>
        </td></tr>
        <tr><td align="center" style="padding:8px 32px 24px;">
          <a href="{enlace}" style="display:inline-block;padding:14px 28px;border-radius:10px;background:#2ee6c3;color:#0a0c18;font-weight:700;font-size:15px;text-decoration:none;">
            Confirmar mi correo
          </a>
        </td></tr>
        <tr><td style="padding:0 32px 28px;color:#6b7280;font-size:13px;line-height:1.6;">
          El enlace es válido por 24 horas. Si el botón no funciona, copia esta dirección en tu navegador:<br>
          <a href="{enlace}" style="color:#2563eb;word-break:break-all;">{enlace}</a>
        </td></tr>
        <tr><td style="padding:18px 32px;background:#f7f8fb;color:#9ca3af;font-size:12px;text-align:center;">
          Si tú no creaste esta cuenta, ignora este mensaje.<br>DevRootDark · Aprende a programar desde la raíz
        </td></tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

    _enviar(email, "Confirma tu correo en DevRootDark", texto, html)
