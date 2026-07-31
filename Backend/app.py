# app.py
# ─────────────────────────────────────────────
# Entry point — just wires everything together
# ─────────────────────────────────────────────

from flask          import Flask, send_from_directory
from config         import Config
from extensions     import db, jwt, cors
import os

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # ── Init extensions ───────────────────────
    db.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={
        r'/api/*': {
            'origins':      ['http://localhost:4200'],
            'methods':      ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
            'allow_headers': ['Content-Type', 'Authorization']
        }
    })

    # ── Register blueprints ───────────────────
    from routes.auth_routes     import auth_bp
    from routes.profile_routes  import profile_bp
    from routes.settings_routes import settings_bp
    from routes.analysis_routes import analysis_bp

    app.register_blueprint(auth_bp,     url_prefix='/api')
    app.register_blueprint(profile_bp,  url_prefix='/api/profile')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')
    app.register_blueprint(analysis_bp, url_prefix='/api/analysis')

    # ── Serve uploaded profile photos ─────────
    @app.route('/uploads/profiles/<filename>')
    def serve_photo(filename):
        upload_folder = app.config['UPLOAD_FOLDER']
        return send_from_directory(upload_folder, filename)

    # ── Create all tables ─────────────────────
    with app.app_context():
        import models          # noqa: F401  triggers model registration
        db.create_all()
        print('✅ Database tables ready!')

    # ── Health check ──────────────────────────
    @app.route('/')
    def home():
        return {'status': 'ToxiScan API running 🚀'}, 200

    return app


# ── Run ───────────────────────────────────────
app = create_app()

if __name__ == '__main__':
    app.run(debug=True, port=5000)