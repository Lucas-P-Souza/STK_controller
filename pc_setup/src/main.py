"""Main entry point: captures video, processes vision, and draws UI."""
import sys
import os
import cv2

# Ensure we can import from src regardless of execution directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import config
from src.vision.tracker import VisionTracker
from src.core.player_controller import PlayerStateController
from src.core.network_client import STKNetworkClient
import subprocess
import atexit

def main():
    tracker = VisionTracker()
    logic = PlayerStateController()
    net_client = STKNetworkClient(config.UDP_IP, config.UDP_PORT)
    
    cap = cv2.VideoCapture(0)
    # Tweak: Force OpenCV to NOT queue frames, always grabbing the absolute latest physical frame
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
        
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.CAM_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.CAM_HEIGHT)

    print("Server running. Press '2' for 2-player mode, '3' for 3-player mode. 'q' to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to grab frame.")
            break

        frame = cv2.flip(frame, 1)
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        height, width, _ = frame.shape

        faces, hands = tracker.process_frame(rgb_frame, gray_frame)
        
        # Get hand boxes
        hand_boxes = tracker.get_hand_boxes(hands, width, height)
        action_text, action_color, steering_val, active_keys = logic.update(faces, hand_boxes, width, height)

        # Network dispatch (Keyboard emulation commands)
        for key in active_keys:
            net_client.send_command(key)

        # --- DRAWING UI ---
        # Draw hand boxes
        for h_box in hand_boxes:
            hx, hy, hw, hh = h_box
            cv2.rectangle(frame, (hx, hy), (hx+hw, hy+hh), config.COLOR_PURPLE, 2)
            
        # Draw faces and eye points
        for i in range(logic.active_players):
            if logic.memory[i].get('box'):
                x, y, w, h = logic.memory[i]['box']
                cv2.rectangle(frame, (x, y), (x+w, y+h), config.COLOR_GREEN, 2)
                cv2.putText(frame, f"P{i+1}", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_NORMAL, config.COLOR_GREEN, config.FONT_THICKNESS)
                
            if logic.memory[i].get('eyes'):
                for pt in logic.memory[i]['eyes']:
                    cv2.circle(frame, pt, 4, config.COLOR_GREEN, -1)

        # Draw Status Text
        cv2.putText(frame, f"MODE: {logic.active_players} PLAYERS", (20, 40), 
                    cv2.FONT_HERSHEY_SIMPLEX, 1.0, config.COLOR_WHITE, config.FONT_THICKNESS)
        cv2.putText(frame, action_text, (20, 90), 
                    cv2.FONT_HERSHEY_SIMPLEX, config.FONT_SCALE_LARGE, action_color, 3)
                    
        # Draw Steering UI bar
        center_x = width // 2
        cv2.line(frame, (center_x - 100, 130), (center_x + 100, 130), config.COLOR_GRAY, 4)
        cv2.circle(frame, (center_x + int(steering_val * 100), 130), 8, config.COLOR_CYAN, -1)

        cv2.imshow('STK Vision Controller', frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('2'):
            logic.set_player_mode(2)
        elif key == ord('3'):
            logic.set_player_mode(3)

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()