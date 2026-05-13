"""
app.py — IMDTools Suite
Clean entry point. Only registers blueprints and serves pages.

To add a new converter in future:
    1. Create routes/maxtemp.py
    2. from routes.maxtemp import maxtemp_bp
    3. app.register_blueprint(maxtemp_bp)
app.register_blueprint(spi_bp)
app.register_blueprint(merger_bp)
    Done. Nothing else changes.
"""

from flask import Flask, send_from_directory
from flask_cors import CORS

from routes.rainfall import rainfall_bp
from routes.mintemp  import mintemp_bp
from routes.maxtemp  import maxtemp_bp
from routes.spi        import spi_bp
from routes.merger      import merger_bp

# ── App ───────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app)

app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500 MB

# ── Skip ngrok browser warning ─────────────────────────────────────────
@app.after_request
def add_ngrok_header(response):
    response.headers['ngrok-skip-browser-warning'] = 'true'
    return response

# ── Register blueprints ───────────────────────────────────────────────
app.register_blueprint(rainfall_bp)
app.register_blueprint(mintemp_bp)
app.register_blueprint(maxtemp_bp)
app.register_blueprint(spi_bp)
app.register_blueprint(merger_bp)

# ── Page routes ────────────────────────────────────────────────────────
@app.route('/')
def landing():
    return send_from_directory('../frontend', 'landing.html')

@app.route('/rainfall')
def rainfall_page():
    return send_from_directory('../frontend', 'index.html')

@app.route('/mintemp')
def mintemp_page():
    return send_from_directory('../frontend', 'mintemp.html')

@app.route('/maxtemp')
def maxtemp_page():
    return send_from_directory('../frontend', 'maxtemp.html')

@app.route('/spi')
def spi_page():
    return send_from_directory('../frontend', 'spi.html')


@app.route('/merger')
def merger_page():
    return send_from_directory('../frontend', 'merger.html')

# ── Serve static files (css, js, images) ──────────────────────────────
@app.route('/<path:path>', methods=['GET'])
def serve_static(path):
    return send_from_directory('../frontend', path)

# ── Run ────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    app.run(debug=True, port=5000)