from flask import Blueprint, request, jsonify, Response
import requests
import socket
import ipaddress
from urllib.parse import urlparse, urljoin
from flask_cors import cross_origin

proxy_bp = Blueprint("proxy_bp", __name__)


def _url_es_segura(url):
    """Solo permite URLs http/https públicas (bloquea localhost y la red local)."""
    try:
        partes = urlparse(url)
        if partes.scheme not in ("http", "https") or not partes.hostname:
            return False
        for info in socket.getaddrinfo(partes.hostname, None):
            ip = ipaddress.ip_address(info[4][0])
            if (ip.is_private or ip.is_loopback or ip.is_link_local
                    or ip.is_reserved or ip.is_multicast or ip.is_unspecified):
                return False
        return True
    except Exception:
        return False


def _descargar_segura(url, headers, max_redirecciones=5):
    """Descarga la URL validando también cada redirección."""
    for _ in range(max_redirecciones + 1):
        if not _url_es_segura(url):
            return None
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=False)
        if resp.is_redirect or resp.status_code in (301, 302, 303, 307, 308):
            url = urljoin(url, resp.headers.get("Location", ""))
            continue
        return resp
    return None

@proxy_bp.route("/proxy/imagen", methods=["GET"])
@cross_origin()
def proxy_imagen():
    """
    Proxy para imágenes externas (Google Drive, etc.)
    """
    url = request.args.get("url")
    
    print(f"DEBUG PROXY: Recibida solicitud para URL: {url}")
    
    if not url:
        print("DEBUG PROXY: Error - URL no proporcionada")
        return jsonify({"error": "URL requerida"}), 400
    
    try:
        # Headers para simular un navegador real
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': 'https://drive.google.com/'
        }
        
        print(f"DEBUG PROXY: Haciendo request a: {url}")
        response = _descargar_segura(url, headers)
        if response is None:
            return jsonify({"error": "URL no permitida"}), 400
        
        print(f"DEBUG PROXY: Status code: {response.status_code}")
        print(f"DEBUG PROXY: Content-Type: {response.headers.get('Content-Type')}")
        
        tipo = response.headers.get('Content-Type', '')
        if response.status_code == 200 and not tipo.startswith('image/'):
            return jsonify({"error": "La URL no es una imagen"}), 400

        if response.status_code == 200:
            print(f"DEBUG PROXY: Imagen obtenida exitosamente, tamaño: {len(response.content)} bytes")
            return Response(
                response.content,
                mimetype=response.headers.get('Content-Type', 'image/jpeg'),
                headers={
                    'Cache-Control': 'public, max-age=86400'
                }
            )
        else:
            print(f"DEBUG PROXY: Error en respuesta: {response.status_code}")
            return jsonify({"error": f"Error al obtener imagen: {response.status_code}"}), 400
            
    except Exception as e:
        print(f"DEBUG PROXY: Excepción: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Error: {str(e)}"}), 500
