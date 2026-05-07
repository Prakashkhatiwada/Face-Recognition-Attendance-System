"""
Face Recognition Employee Attendance Management System
======================================================
Slim application entry-point.  All logic lives in:

    models/   – database table operations
    routes/   – Flask blueprints (auth, admin, attendance)
    services/ – business logic (face recognition, attendance, auth)
    utils/    – decorators and helpers
    config.py – centralised configuration
"""

import os

from flask import Flask

import config
from models.db import init_db
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.attendance import attendance_bp
from routes.user import user_bp


def create_app():
    """Application factory."""
    app = Flask(__name__)
    app.secret_key = config.SECRET_KEY

    # Ensure required directories exist
    os.makedirs(config.FACES_DIR, exist_ok=True)
    os.makedirs(os.path.join(config.FACES_DIR, 'full_time'), exist_ok=True)
    os.makedirs(os.path.join(config.FACES_DIR, 'part_time'), exist_ok=True)

    # Register blueprints
    app.register_blueprint(auth_bp)           # / , /sign, /logout …
    app.register_blueprint(admin_bp)          # /admin/dashboard, /admin/add …
    app.register_blueprint(attendance_bp)     # /home, /start, /recognize, /kiosk
    app.register_blueprint(user_bp)           # /user/notifications, /user/activity

    # Initialise database tables (idempotent)
    with app.app_context():
        init_db()

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=1000)
