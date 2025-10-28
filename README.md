
# proyectoLA

ProyectoLA es una aplicación sencilla con backend en Flask y frontend estático en HTML/CSS. El servidor Flask sirve las páginas HTML y los activos estáticos (CSS, imágenes, JS si aplica). Este README explica cómo instalar, ejecutar y desplegar el proyecto localmente.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)]()

## Tabla de contenidos
- [Características](#características)
- [Requisitos](#requisitos)
- [Instalación](#instalación)
- [Estructura del proyecto](#estructura-del-proyecto)
- [Uso](#uso)
- [Variables de entorno](#variables-de-entorno)
- [Ejecutar tests](#ejecutar-tests)
- [Despliegue (opcional)](#despliegue-opcional)
- [Contribuir](#contribuir)
- [Licencia](#licencia)
- [Contacto](#contacto)

## Características
- Backend: Flask (Python) que sirve rutas y plantillas Jinja2.
- Frontend: HTML y CSS estático (posible JS opcional).
- Arquitectura simple pensada para aplicaciones estáticas con lógica mínima en servidor.

## Requisitos
- Python 3.8+
- pip
- Git
- (Opcional) Docker y docker-compose para entornos reproducibles

## Instalación (local)

1. Clona el repositorio:
```bash
git clone https://github.com/Zer0M4n/projectoLA.git
cd projectoLA
```

2. Crea y activa un entorno virtual:
```bash
python -m venv .venv
# Linux / macOS
source .venv/bin/activate
# Windows (PowerShell)
.venv\\Scripts\\Activate.ps1
```

3. Instala dependencias:
```bash
pip install -r requirements.txt
```
Si no existe requirements.txt, instala Flask:
```bash
pip install Flask python-dotenv
```

4. Copia el fichero de ejemplo de variables de entorno y edítalo:
```bash
cp .env.example .env
# editar .env según sea necesario
```

## Estructura del proyecto (ejemplo)
Explica la organización típica de este proyecto:
```
projectoLA/
├─ app.py                 # Aplicación Flask principal
├─ requirements.txt
├─ .env.example
├─ templates/             # HTML (Jinja2)
│  ├─ index.html
│  └─ ...
└─ static/
   ├─ css/
   │  └─ styles.css
   ├─ js/
   └─ img/
```

## Uso

Arrancar la aplicación en modo desarrollo:

- Usando flask:
```bash
export FLASK_APP=app.py
export FLASK_ENV=development  # opcional: activa recarga y debug
flask run
# o en Windows (PowerShell)
# $env:FLASK_APP="app.py"; $env:FLASK_ENV="development"; flask run
```

- O ejecutando directamente (si app.py contiene `if __name__ == "__main__": app.run(...)`):
```bash
python app.py
```

Accede a la aplicación en http://127.0.0.1:5000 por defecto.

Ejemplo de una ruta básica en app.py:
```python
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')
```

## Variables de entorno
Coloca configuraciones sensibles en `.env`. Ejemplo de `.env.example`:
```
FLASK_ENV=development
SECRET_KEY=tu_secreto_aqui
PORT=5000
```
Usa python-dotenv o carga manualmente las variables desde `.env` en app.py si lo necesitas.

## Ejecutar tests
Si añades tests (pytest/unittest), ejecuta:
```bash
pytest
```
(Agrega un directorio `tests/` con pruebas unitarias para la lógica del servidor).

## Despliegue (opcional)
- Producir un entorno WSGI con Gunicorn para producción:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```
- Usar Docker:
  - Añade un Dockerfile que instale dependencias y exponga el puerto.
  - Usa docker-compose para orquestación si necesitas servicios adicionales.

## Buenas prácticas
- Mantén CSS y assets en `static/`.
- Separa lógica de las plantillas y evita lógica compleja en Jinja2.
- Añade linter (flake8 / black) y pre-commit si gustas.

## Contribuir
1. Abre un issue describiendo la mejora o bug.
2. Crea una rama descriptiva:
```bash
git checkout -b feat/nombre-corto
```
3. Haz commits claros y atómicos.
4. Abre un Pull Request cuando esté listo.

## Licencia
Proyecto con licencia MIT. Añade un fichero LICENSE con el texto correspondiente si aún no existe.

## Contacto
Mantenedor: Zer0M4n y ZDAII

---

Si quieres, subo este README.md al repositorio y creo una rama + PR; dime si quieres que use la rama base `main` o otra rama, o si prefieres que lo añada directamente a `main`. También puedo generar un ejemplo de app.py y .env.example si te interesa.
