"""
Servidor Flask mejorado para Mini IDE Pyra
Mantiene la estructura de directorios original
"""

from flask import Flask, request, jsonify, send_from_directory
from interpreter import Interpreter
from checker import Checker
import os
import logging
from functools import wraps
import time

app = Flask(__name__, static_folder="static")

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Caché simple para evitar procesar el mismo código repetidamente
cache = {
    'lint': {},
    'last_cleanup': time.time()
}

# Límite de tamaño de código (100KB)
MAX_CODE_SIZE = 100 * 1024

def validate_code_size(f):
    """Decorador para validar tamaño del código"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        data = request.get_json()
        if not data:
            return jsonify({"error": "No se recibió JSON válido"}), 400
        
        code = data.get("code", "")
        if len(code) > MAX_CODE_SIZE:
            return jsonify({
                "error": f"Código demasiado largo (máximo {MAX_CODE_SIZE} bytes)"
            }), 413
        
        return f(*args, **kwargs)
    return decorated_function

def cleanup_cache():
    """Limpia el caché cada 5 minutos"""
    current_time = time.time()
    if current_time - cache['last_cleanup'] > 300:  # 5 minutos
        cache['lint'].clear()
        cache['last_cleanup'] = current_time
        logger.info("Caché limpiado")

# ==================== PÁGINAS ====================

@app.route("/")
@app.route("/index.html")
def home():
    """Página principal del IDE"""
    try:
        return send_from_directory("static", "index.html")
    except FileNotFoundError:
        logger.error("index.html no encontrado en /static")
        return jsonify({"error": "Archivo no encontrado"}), 404

@app.route("/manual")
@app.route("/manual.html")
def manual_page():
    """Página del manual (opcional)"""
    try:
        return send_from_directory("static", "manual.html")
    except FileNotFoundError:
        # Si no existe manual.html, devolver info básica
        return """
        <html>
        <head><title>Manual Pyra</title></head>
        <body>
            <h1>Manual no disponible</h1>
            <p>Usa el botón "📖 Manual" en el IDE para ver la documentación.</p>
        </body>
        </html>
        """, 200

# ==================== API ENDPOINTS ====================

@app.route("/run", methods=["POST"])
@validate_code_size
def run_code():
    """Ejecutar código del intérprete"""
    data = request.get_json()
    code = data.get("code", "")
    
    if not code.strip():
        return jsonify({"output": "⚠️ No hay código para ejecutar"}), 200
    
    logger.info(f"Ejecutando código ({len(code)} bytes)")
    
    interp = Interpreter()
    try:
        result = interp.run(code)
        
        # Si no hay salida, indicarlo
        if not result or not result.strip():
            result = "✓ Código ejecutado sin errores (sin salida)"
        
        return jsonify({
            "success": True,
            "output": result
        })
    
    except Exception as e:
        logger.error(f"Error en ejecución: {e}")
        # IMPORTANTE: Devolver el error detallado al cliente
        error_msg = str(e)
        return jsonify({
            "success": False,
            "output": error_msg if error_msg else "Error desconocido al ejecutar el código"
        }), 200  # Cambiado a 200 para que el cliente pueda leer el mensaje

@app.route("/lint", methods=["POST"])
@validate_code_size
def lint_code():
    """Verificar errores de sintaxis"""
    data = request.get_json()
    code = data.get("code", "")
    
    # Limpiar caché periódicamente
    cleanup_cache()
    
    # Usar caché si el código no ha cambiado
    code_hash = hash(code)
    if code_hash in cache['lint']:
        logger.debug("Usando resultado de lint desde caché")
        return jsonify(cache['lint'][code_hash])
    
    logger.info(f"Analizando código ({len(code)} bytes)")
    
    checker = Checker()
    try:
        errors = checker.check(code)
        
        result = {
            "success": True,
            "errors": errors,
            "error_count": len([e for e in errors if e.get('severity') == 'error']),
            "warning_count": len([e for e in errors if e.get('severity') == 'warning'])
        }
        
        # Guardar en caché
        cache['lint'][code_hash] = result
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error en lint: {e}")
        return jsonify({
            "success": False,
            "errors": [],
            "error": str(e)
        }), 500

# ==================== ENDPOINTS ADICIONALES ====================

@app.route("/health", methods=["GET"])
def health_check():
    """Verificar estado del servidor"""
    return jsonify({
        "status": "ok",
        "version": "1.0",
        "cache_size": len(cache['lint'])
    })

@app.route("/examples", methods=["GET"])
def get_examples():
    """Obtener ejemplos de código"""
    examples = {
        "factorial": """func factorial(n):
    if n <= 1:
        return 1
    else:
        return n * factorial(n - 1)

var resultado = factorial(5)
print(resultado)""",
        
        "fibonacci": """func fibonacci(n):
    if n <= 1:
        return n
    else:
        return fibonacci(n - 1) + fibonacci(n - 2)

for i in range(10):
    print(fibonacci(i))""",
        
        "bucles": """for i in range(5):
    print(i)

var x = 0
while x < 3:
    print(x)
    x = x + 1""",
        
        "listas": """var numeros = [1, 2, 3, 4, 5]
print(sum(numeros))
print(max(numeros))
print(sorted(numeros))"""
    }
    
    return jsonify(examples)

# ==================== MANEJO DE ERRORES ====================

@app.errorhandler(400)
def bad_request(e):
    logger.warning(f"Bad request: {e}")
    return jsonify({"error": "Solicitud inválida"}), 400

@app.errorhandler(404)
def not_found(e):
    logger.warning(f"Not found: {request.path}")
    return jsonify({"error": "Endpoint no encontrado"}), 404

@app.errorhandler(413)
def request_too_large(e):
    return jsonify({"error": "Código demasiado grande"}), 413

@app.errorhandler(500)
def server_error(e):
    logger.error(f"Error interno: {e}")
    return jsonify({"error": "Error interno del servidor"}), 500

@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Excepción no manejada: {e}")
    return jsonify({"error": "Error inesperado en el servidor"}), 500

# ==================== MIDDLEWARE ====================

@app.before_request
def log_request():
    """Log de todas las peticiones"""
    logger.info(f"{request.method} {request.path} - {request.remote_addr}")

@app.after_request
def add_headers(response):
    """Agregar headers de seguridad"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# ==================== INICIO DEL SERVIDOR ====================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("DEBUG", "True").lower() == "true"
    
    print("\n" + "="*50)
    print("🐍 Mini IDE Pyra - Servidor Flask")
    print("="*50)
    print(f"\n🚀 Servidor corriendo en:")
    print(f"   → http://127.0.0.1:{port}")
    print(f"   → http://localhost:{port}")
    
    # Intentar obtener IP local
    try:
        import socket
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        print(f"   → http://{local_ip}:{port}")
    except:
        pass
    
    print(f"\n📁 Sirviendo archivos desde: {os.path.abspath('static')}")
    print(f"🔍 Modo debug: {'Activado' if debug else 'Desactivado'}")
    print(f"\n💡 Endpoints disponibles:")
    print(f"   - GET  /            → IDE principal")
    print(f"   - GET  /manual      → Manual de usuario")
    print(f"   - POST /run         → Ejecutar código")
    print(f"   - POST /lint        → Analizar código")
    print(f"   - GET  /health      → Estado del servidor")
    print(f"   - GET  /examples    → Ejemplos de código")
    print("\n" + "="*50 + "\n")
    
    # Verificar que existe el directorio static
    if not os.path.exists("static"):
        logger.warning("⚠️  Directorio 'static' no encontrado. Creando...")
        os.makedirs("static")
    
    # Verificar archivos necesarios
    if not os.path.exists("static/index.html"):
        logger.error("❌ Error: static/index.html no existe")
        print("\n⚠️  Por favor, mueve index.html a la carpeta 'static/'\n")
    
    try:
        app.run(
            host="0.0.0.0", 
            port=port, 
            debug=debug,
            use_reloader=debug
        )
    except KeyboardInterrupt:
        print("\n\n👋 Servidor detenido por el usuario")
    except Exception as e:
        logger.error(f"Error al iniciar servidor: {e}")
        print(f"\n❌ Error: {e}\n")