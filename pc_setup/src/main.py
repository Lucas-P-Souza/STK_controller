import cv2
import sys
import os

# Allow imports from pc_setup
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import config
from src.vision.tracker import VisionTracker
from src.core.player_controller import PlayerStateController

def main():
    tracker = VisionTracker()
    logic = PlayerStateController()
    
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return

    print("Vision tracking started. Press 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        frame = cv2.flip(frame, 1)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        faces, hands = tracker.process_frame(rgb_frame, gray_frame)
        hand_boxes = tracker.get_hand_boxes(hands, frame.shape[1], frame.shape[0])

        # Core logic evaluation (Binary collision version)
        action_text, action_color = logic.update(faces, hand_boxes, frame.shape[1], frame.shape[0])

        # Draw detected faces
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), config.COLOR_RED, 2)
            
        # Draw detected hand landmarks
        if hands:
            for hand_landmarks in hands:
                for mark in hand_landmarks:
                    cx, cy = int(mark.x * frame.shape[1]), int(mark.y * frame.shape[0])
                    cv2.circle(frame, (cx, cy), 5, config.COLOR_CYAN, cv2.FILLED)

        # Draw digital action
        cv2.putText(frame, action_text, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, action_color, 2)

        cv2.imshow('STK Controller - Logic', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
