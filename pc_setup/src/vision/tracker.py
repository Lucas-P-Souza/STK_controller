"""Wrapper for Vision tasks: OpenCV for robust Face tracking, MediaPipe for Hands."""
import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from src import config

class VisionTracker:
    def __init__(self):
        # Face Detector
        face_base = python.BaseOptions(model_asset_path=config.FACE_DETECTOR_PATH)
        face_opts = vision.FaceDetectorOptions(base_options=face_base, min_detection_confidence=0.6)
        self.face_tracker = vision.FaceDetector.create_from_options(face_opts)

        # Hand Landmarker
        hand_base = python.BaseOptions(model_asset_path=config.HAND_MODEL_PATH)
        hand_opts = vision.HandLandmarkerOptions(
            base_options=hand_base, 
            num_hands=config.MAX_PLAYERS * 2, 
            min_hand_detection_confidence=config.HAND_MIN_CONFIDENCE
        )
        self.hand_tracker = vision.HandLandmarker.create_from_options(hand_opts)

    def process_frame(self, rgb_frame, gray_frame):
        
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Hand tracking
        hands = self.hand_tracker.detect(mp_image).hand_landmarks
        
        # Face tracking
        face_results = self.face_tracker.detect(mp_image)
        faces = []
        if face_results.detections:
            for detection in face_results.detections:
                bbox = detection.bounding_box
                faces.append([int(bbox.origin_x), int(bbox.origin_y), int(bbox.width), int(bbox.height)])
        
        return faces, hands

    def get_hand_boxes(self, hand_landmarks, width, height):
        """Converts hand landmarks into a simple Bounding Box [x, y, w, h]."""
        boxes = []
        if hand_landmarks:
            for hand in hand_landmarks:
                x_coords = [int(lm.x * width) for lm in hand]
                y_coords = [int(lm.y * height) for lm in hand]
                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)
                boxes.append([x_min, y_min, x_max - x_min, y_max - y_min])
        return boxes