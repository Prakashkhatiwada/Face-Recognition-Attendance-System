"""
Face Service — face detection, recognition and model training.

Extracted from the monolithic app.py so it can be reused by any route or
background task.
"""

import os

import cv2
import joblib
import numpy as np
from sklearn.neighbors import KNeighborsClassifier

import config


# Initialise the Haar cascade once at module level
face_detector = cv2.CascadeClassifier(config.HAAR_CASCADE_PATH)


def extract_faces(img):
    """Return a list of (x, y, w, h) bounding boxes for detected faces."""
    if img is None:
        return []
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    face_points = face_detector.detectMultiScale(gray, 1.3, 5)
    return face_points if len(face_points) > 0 else []


def identify_face(face_array):
    """
    Predict the label for one or more face feature arrays.

    Parameters
    ----------
    face_array : np.ndarray
        Shape ``(n_samples, n_features)`` — typically a single face is
        ``face.reshape(1, -1)``.

    Returns
    -------
    np.ndarray of predicted labels.

    Raises
    ------
    FileNotFoundError
        If the trained model does not exist on disk.
    """
    if not os.path.isfile(config.MODEL_PATH):
        raise FileNotFoundError(
            "Trained model not found. Train model first by adding users."
        )
    model = joblib.load(config.MODEL_PATH)
    return model.predict(face_array)


def train_model():
    """
    Retrain the KNN classifier from images stored in ``static/faces/<label>/``.

    Each sub-folder name becomes the label.  Images are resized to
    ``config.FACE_RESIZE``, flattened, then used to fit a
    ``KNeighborsClassifier``.
    """
    faces = []
    labels = []
    if not os.path.isdir(config.FACES_DIR):
        os.makedirs(config.FACES_DIR, exist_ok=True)
        return

    for emp_type in os.listdir(config.FACES_DIR):
        emp_dir = os.path.join(config.FACES_DIR, emp_type)
        if not os.path.isdir(emp_dir):
            continue
        for user in os.listdir(emp_dir):
            user_dir = os.path.join(emp_dir, user)
            if not os.path.isdir(user_dir):
                continue
            for imgname in os.listdir(user_dir):
                img_path = os.path.join(user_dir, imgname)
                img = cv2.imread(img_path)
                if img is None:
                    continue
                resized = cv2.resize(img, config.FACE_RESIZE)
                faces.append(resized.ravel())
                labels.append(user)

    if not faces:
        print("No faces found to train.")
        return

    print(f"Training model with {len(faces)} faces from users: {list(set(labels))}")
    faces = np.array(faces)

    # Adaptive n_neighbors
    n_neighbors = min(config.DEFAULT_N_NEIGHBORS, len(faces))
    knn = KNeighborsClassifier(n_neighbors=n_neighbors, weights='distance')
    knn.fit(faces, labels)
    joblib.dump(knn, config.MODEL_PATH)
    print(f"Model trained — n_neighbors={n_neighbors}, weights='distance'.")


def totalreg():
    """Return the number of registered user folders."""
    if not os.path.isdir(config.FACES_DIR):
        return 0
    count = 0
    for emp_type in os.listdir(config.FACES_DIR):
        emp_dir = os.path.join(config.FACES_DIR, emp_type)
        if os.path.isdir(emp_dir):
            count += len([d for d in os.listdir(emp_dir) if os.path.isdir(os.path.join(emp_dir, d))])
    return count
