import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, 'assets', 'models')

# Model Paths
HAND_MODEL_PATH = os.path.join(MODELS_DIR, 'hand_landmarker.task')
FACE_DETECTOR_PATH = os.path.join(MODELS_DIR, 'blaze_face_short_range.tflite')

# Limits
MAX_PLAYERS = 3
HAND_MIN_CONFIDENCE = 0.5

# UI Colors
COLOR_RED = (0, 0, 255)
COLOR_GREEN = (0, 255, 0)
COLOR_CYAN = (255, 255, 0)
COLOR_WHITE = (255, 255, 255)
COLOR_ORANGE = (0, 165, 255)
