"""
Attendance routes blueprint — home page, camera attendance, recognition API, kiosk.
"""

from datetime import date, datetime

import cv2
import numpy as np
from flask import Blueprint, redirect, render_template, request, url_for, jsonify
from PIL import Image

from services.attendance_service import extract_attendance_from_db, add_attendance_db
from services.face_service import extract_faces, identify_face, totalreg
import config

attendance_bp = Blueprint('attendance', __name__)

datetoday2 = date.today().strftime("%d-%B-%Y")


@attendance_bp.route('/home')
def home():
    names, rolls, times, l = extract_attendance_from_db()
    return render_template(
        'home.html',
        names=names, rolls=rolls, times=times, l=l,
        totalreg=totalreg(), datetoday2=datetoday2,
        mess=config.WELCOME_MESSAGE,
    )


@attendance_bp.route('/start')
def start():
    import os
    if not os.path.isfile(config.MODEL_PATH):
        names, rolls, times, l = extract_attendance_from_db()
        return render_template(
            'home.html',
            names=names, rolls=rolls, times=times, l=l,
            totalreg=totalreg(), datetoday2=datetoday2,
            mess='No trained model found. Add users to train the model.',
        )

    cap_local = cv2.VideoCapture(0)
    marked = False
    result_msg = ''
    while True:
        ret, frame = cap_local.read()
        if not ret:
            break
        faces = extract_faces(frame)
        for (x, y, w, h) in faces:
            face = cv2.resize(frame[y:y+h, x:x+w], config.FACE_RESIZE)
            identified = identify_face(face.reshape(1, -1))[0]
            cv2.putText(frame, identified, (x+6, y-6),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 20), 2)
            if cv2.waitKey(1) == ord('a'):
                result = add_attendance_db(identified)
                if result == 'time_restricted_in':
                    result_msg = f'Attendance REJECTED for {identified}: Time not allowed (10-11 AM only)'
                elif result == 'time_restricted_out':
                    result_msg = f'Attendance REJECTED for {identified}: Time not allowed (4-5 PM only)'
                else:
                    result_msg = f'Attendance operation: {result} for {identified}'
                marked = True
                break
        cv2.imshow('Attendance', frame)
        if cv2.waitKey(1) == ord('q') or marked:
            break

    cap_local.release()
    cv2.destroyAllWindows()
    names, rolls, times, l = extract_attendance_from_db()
    return render_template(
        'home.html',
        names=names, rolls=rolls, times=times, l=l,
        totalreg=totalreg(), datetoday2=datetoday2,
        mess=result_msg or config.WELCOME_MESSAGE,
    )


@attendance_bp.route('/recognize', methods=['POST'])
def recognize():
    """
    Accept multipart/form-data image file (FormData 'image').
    Return JSON: { success, label, logged, message }
    """
    try:
        if 'image' not in request.files:
            return jsonify(success=False, message="No image file provided"), 400

        file = request.files['image']
        img = Image.open(file.stream).convert('RGB')
        img_np = np.array(img)[:, :, ::-1]  # RGB -> BGR

        faces = extract_faces(img_np)
        if len(faces) == 0:
            return jsonify(success=False, message="No face detected"), 200

        x, y, w, h = faces[0]
        face_crop = img_np[y:y+h, x:x+w]
        face_resized = cv2.resize(face_crop, config.FACE_RESIZE)
        features = face_resized.reshape(1, -1)

        try:
            label = identify_face(features)[0]
        except FileNotFoundError:
            return jsonify(success=False, message="Trained model not found"), 500
        except Exception as e:
            return jsonify(success=False, message=str(e)), 500

        result = add_attendance_db(label)
        logged = (result in ('check-in', 'check-out'))

        msg = f"Attendance {result}"
        if result == 'time_restricted_in':
            msg = "Attendance REJECTED: Time not allowed (10-11 AM only)"
        elif result == 'time_restricted_out':
            msg = "Attendance REJECTED: Time not allowed (4-5 PM only)"

        return jsonify(success=True, label=label, logged=logged, message=msg), 200

    except Exception as e:
        return jsonify(success=False, message=str(e)), 500


@attendance_bp.route('/kiosk')
def kiosk():
    """Kiosk mode — auto-attendance via webcam."""
    import os
    if not os.path.isfile(config.MODEL_PATH):
        return "Model not found. Please add users first."

    cap_local = cv2.VideoCapture(0)
    last_attendance_time = {}

    while True:
        ret, frame = cap_local.read()
        if not ret:
            break

        faces = extract_faces(frame)
        for (x, y, w, h) in faces:
            face = cv2.resize(frame[y:y+h, x:x+w], config.FACE_RESIZE)
            try:
                identified = identify_face(face.reshape(1, -1))[0]

                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(frame, identified, (x, y-10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

                now = datetime.now()
                if identified not in last_attendance_time or \
                   (now - last_attendance_time[identified]).total_seconds() > 5:
                    result = add_attendance_db(identified)
                    print(f"Auto-attendance: {result} for {identified}")
                    last_attendance_time[identified] = now

                    if result == 'time_restricted_in':
                        msg, color = "REJECTED: 10-11 AM only", (0, 0, 255)
                    elif result == 'time_restricted_out':
                        msg, color = "REJECTED: 4-5 PM only", (0, 0, 255)
                    else:
                        msg, color = f"Logged: {result}", (0, 255, 255)

                    cv2.putText(frame, msg, (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            except Exception as e:
                print(f"Recognition error: {e}")

        cv2.imshow('Kiosk Mode - Press Q to Exit', frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cap_local.release()
    cv2.destroyAllWindows()
    return redirect(url_for('attendance.home'))
