from flask import Blueprint, request, jsonify, Response
import requests
from flask_cors import cross_origin

proxy_bp = Blueprint("proxy_bp", __name__)

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
        response = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        
        print(f"DEBUG PROXY: Status code: {response.status_code}")
        print(f"DEBUG PROXY: Content-Type: {response.headers.get('Content-Type')}")
        
        if response.status_code == 200:
            print(f"DEBUG PROXY: Imagen obtenida exitosamente, tamaño: {len(response.content)} bytes")
            return Response(
                response.content,
                mimetype=response.headers.get('Content-Type', 'image/jpeg'),
                headers={
                    'Access-Control-Allow-Origin': '*',
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
