import os

# Path Resolution
SRC_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(SRC_DIR)
MODELS_DIR = os.path.join(ROOT_DIR, 'assets', 'models')

# Network
UDP_IP = '127.0.0.1'
UDP_PORT = 6006

# Camera
CAM_WIDTH = 1280
CAM_HEIGHT = 720
CAM_FPS = 30

# AI Models
FACE_MODEL_PATH = os.path.join(MODELS_DIR, 'face_landmarker.task')
HAND_MODEL_PATH = os.path.join(MODELS_DIR, 'hand_landmarker.task')

# Tracking Thresholds
HAND_MIN_CONFIDENCE = 0.5

# Game Logic
MAX_PLAYERS = 3
MEMORY_TTL_FRAMES = 30

# PWM Steering
PWM_STEP = 0.25      
PWM_DECAY = 0.8
PWM_DEADZONE = 0.05
PWM_WINDOW_FRAMES = 5 

# Spatial Thresholds
FACE_MATCH_MAX_DIST = 0.2
HAND_ASSIGN_MAX_DIST = 0.3
EYE_HEIGHT_RATIO = 0.35

# UI & Rendering
COLOR_WHITE = (255, 255, 255)
COLOR_RED = (0, 0, 255)
COLOR_CYAN = (255, 255, 0)
COLOR_GREEN = (0, 255, 0)
COLOR_PURPLE = (250, 44, 121)
COLOR_ORANGE = (0, 165, 255)
COLOR_GRAY = (100, 100, 100)

FONT_SCALE_NORMAL = 0.9
FONT_SCALE_LARGE = 1.2
FONT_THICKNESS = 2


FACE_DETECTOR_PATH = os.path.join(MODELS_DIR, 'blaze_face_short_range.tflite')
