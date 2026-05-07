"""
Centralized configuration for the Face Recognition Attendance System.
"""
import os

# ─── Flask ───────────────────────────────────────────────
SECRET_KEY = os.environ.get('FLASK_SECRET', 'change_this_random_secret')
JWT_SECRET = os.environ.get('JWT_SECRET', 'jwt_super_secret_key')
JWT_EXPIRY_HOURS = 24

# ─── MySQL Database ─────────────────────────────────────
DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", "12345"),
    "database": os.environ.get("DB_NAME", "attendance_system"),
}

# ─── Paths ──────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FACES_DIR = os.path.join(BASE_DIR, 'static', 'faces')
MODEL_PATH = os.path.join(BASE_DIR, 'static', 'face_recognition_model.pkl')
HAAR_CASCADE_PATH = os.path.join(BASE_DIR, 'haarcascade_frontalface_default.xml')

# ─── Face Recognition Engine Defaults ───────────────────
FACE_RESIZE = (50, 50)
DEFAULT_THRESHOLD = 0.6
DEFAULT_FRAME_RATE = 30
DEFAULT_N_NEIGHBORS = 5

# ─── Attendance Time Windows ────────────────────────────
CHECK_IN_START = 10   # 10 AM
CHECK_IN_END = 11     # 11 AM
CHECK_OUT_START = 16  # 4 PM
CHECK_OUT_END = 17    # 5 PM

# ─── Messages ───────────────────────────────────────────
WELCOME_MESSAGE = "WELCOME — To register your attendance, click 'a' on the keyboard."
