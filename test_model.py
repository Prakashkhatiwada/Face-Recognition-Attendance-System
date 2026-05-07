import joblib
import numpy as np
from sklearn.neighbors import KNeighborsClassifier
import os

model_path = 'd:/OneDrive/Desktop/app/Face-Recognition-Attendance-System-main/static/face_recognition_model.pkl'

if os.path.exists(model_path):
    try:
        model = joblib.load(model_path)
        print("Model loaded successfully!")
        print("Model type:", type(model))
    except Exception as e:
        print(f"Error loading model: {e}")
else:
    print("Model file not found at:", model_path)
