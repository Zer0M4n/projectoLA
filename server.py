from flask import Flask, request, jsonify, send_from_directory
from interpreter import Interpreter
import os

# Configuramos Flask para que 'static' sea la carpeta de archivos estáticos.
app = Flask(__name__, static_folder="static")

# 1. Rutas para index.html
# Mapea la ruta raíz (/) Y la ruta /index.html al archivo 'index.html'
@app.route("/")
@app.route("/index.html")
def home():
    # El primer argumento es el directorio ('static'), el segundo es el nombre del archivo.
    return send_from_directory("static", "index.html")

# 2. Rutas para manual.html
# Mapea la ruta /manual Y la ruta /manual.html al archivo 'manual.html'
@app.route("/manual")
@app.route("/manual.html")
def manual_page():
    # Servimos 'manual.html' desde la carpeta 'static'.
    return send_from_directory("static", "manual.html")

# Endpoint que ejecuta el código del editor (Sin cambios)
@app.route("/run", methods=["POST"])
def run_code():
    data = request.get_json()
    code = data.get("code", "")
    interp = Interpreter()
    try:
        result = interp.run(code)
    except Exception as e:
        result = f"Error: {e}"
    return jsonify({"output": result})

# Ejecutar el servidor Flask
if __name__ == "__main__":
    port = 5000
    print(f"\n🚀 Servidor corriendo en:")
    print(f"   → http://127.0.0.1:{port}")
    
    # Intento de obtener la IP de red
    try:
        # Nota: 'hostname -I' solo funciona en sistemas operativos tipo Unix (Linux/macOS)
        ip = os.popen('hostname -I').read().strip()
        if ip:
            print(f"   → http://{ip}:{port}\n")
    except:
        # En caso de error o en Windows, se omite esta línea
        print("   (Verifique su IP de red si la necesita)\n")
        
    app.run(host="0.0.0.0", port=port, debug=True)