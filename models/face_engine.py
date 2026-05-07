"""
FaceRecognitionEngine model — CRUD for engine configuration.
"""

from datetime import datetime
from models.db import get_db_connection


def get_engine_config(engine_id='ENG001'):
    """Return the engine config row (singleton-like)."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM face_recognition_engine WHERE engineId = %s", (engine_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row


def upsert_engine_config(engine_id='ENG001', model_path=None, threshold=0.6,
                         frame_rate=30, is_running=True):
    """Insert or update the face recognition engine configuration."""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM face_recognition_engine WHERE engineId = %s", (engine_id,))
    row = cursor.fetchone()

    if row:
        cursor.execute(
            """UPDATE face_recognition_engine
               SET modelPath = %s, threshold = %s, frameRate = %s, isRunning = %s
               WHERE engineId = %s""",
            (model_path, threshold, frame_rate, is_running, engine_id),
        )
    else:
        cursor.execute(
            """INSERT INTO face_recognition_engine
               (engineId, modelPath, threshold, frameRate, isRunning, lastRetrained)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (engine_id, model_path, threshold, frame_rate, is_running, datetime.now()),
        )

    conn.commit()
    cursor.close()
    conn.close()


def update_last_retrained(engine_id='ENG001'):
    """Stamp the lastRetrained timestamp to now."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE face_recognition_engine SET lastRetrained = %s WHERE engineId = %s",
        (datetime.now(), engine_id),
    )
    conn.commit()
    cursor.close()
    conn.close()
