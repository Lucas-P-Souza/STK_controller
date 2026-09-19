"""Core game logic: Boxes, NMS filter, and Point-in-Box collision."""
from src import config

class PlayerStateController:
    def __init__(self):
        self.active_players = config.MAX_PLAYERS
        self.memory = {i: {'eyes': [], 'box': (), 'nose_x': -1.0, 'ttl': 0} for i in range(config.MAX_PLAYERS)}
        self.rescue_fired = False
        self.steering_val = 0.0
        self.pwm_counter = 0

    def set_player_mode(self, num_players):
        if num_players not in [2, 3]: return 
        self.active_players = num_players
        self.memory = {i: {'eyes': [], 'box': (), 'nose_x': -1.0, 'ttl': 0} for i in range(config.MAX_PLAYERS)}
        self.rescue_fired = False
        self.steering_val = 0.0
        self.pwm_counter = 0

    def _extract_eye_coords(self, face_box):
        x, y, w, h = face_box
        eye_y = int(y + h * config.EYE_HEIGHT_RATIO)
        left_eye_x = int(x + w * 0.30)
        right_eye_x = int(x + w * 0.70)
        return [(left_eye_x, eye_y), (right_eye_x, eye_y)]

    def update(self, faces, hand_boxes, width, height):
        if len(faces) > 0:
            # NMS Filter
            filtered_faces = []
            for face_box in faces:
                x, y, w, h = face_box
                cx, cy = x + w/2, y + h/2
                is_inside = False
                for (fx, fy, fw, fh) in filtered_faces:
                    if fx < cx < fx + fw and fy < cy < fy + fh:
                        is_inside = True
                        break
                if not is_inside:
                    filtered_faces.append(face_box)
            
            # Prioritize closest faces
            filtered_faces = sorted(filtered_faces, key=lambda f: f[2]*f[3], reverse=True)[:self.active_players]

            if len(filtered_faces) == self.active_players:
                sorted_faces = sorted(filtered_faces, key=lambda f: f[0] + f[2]/2)
                for i, face_box in enumerate(sorted_faces):
                    self.memory[i]['box'] = face_box
                    self.memory[i]['eyes'] = self._extract_eye_coords(face_box)
                    self.memory[i]['nose_x'] = (face_box[0] + face_box[2]/2) / width
                    self.memory[i]['ttl'] = config.MEMORY_TTL_FRAMES
            else:
                for face_box in filtered_faces:
                    nose_x = (face_box[0] + face_box[2]/2) / width
                    best_match = -1
                    min_dist = 2.0
                    for i in range(self.active_players):
                        if self.memory[i]['nose_x'] != -1.0:
                            dist = abs(self.memory[i]['nose_x'] - nose_x)
                            if dist < min_dist and dist < config.FACE_MATCH_MAX_DIST: 
                                min_dist = dist
                                best_match = i
                    if best_match != -1:
                        self.memory[best_match]['box'] = face_box
                        self.memory[best_match]['eyes'] = self._extract_eye_coords(face_box)
                        self.memory[best_match]['nose_x'] = nose_x
                        self.memory[best_match]['ttl'] = config.MEMORY_TTL_FRAMES

        # Assign hand boxes to players
        player_hands = {i: [] for i in range(self.active_players)}
        for h_box in hand_boxes:
            hx, hy, hw, hh = h_box
            cx = (hx + hw/2) / width
            
            best_player = -1
            min_dist = 2.0
            for i in range(self.active_players):
                if self.memory[i]['nose_x'] != -1.0:
                    dist = abs(self.memory[i]['nose_x'] - cx)
                    if dist < min_dist:
                        min_dist = dist
                        best_player = i
            if best_player != -1 and min_dist < config.HAND_ASSIGN_MAX_DIST: 
                player_hands[best_player].append(h_box)

        # Fast collision check (Point inside AABB Box)
        player_status = {i: False for i in range(self.active_players)}
        for i in range(self.active_players):
            if not self.memory[i]['eyes']: continue
            is_covered = False
            
            for h_box in player_hands[i]:
                hx, hy, hw, hh = h_box
                for pt in self.memory[i]['eyes']:
                    px, py = pt
                    if hx < px < (hx + hw) and hy < py < (hy + hh):
                        is_covered = True
                        break
                if is_covered: break
                
            if is_covered:
                player_status[i] = True
                self.memory[i]['ttl'] = config.MEMORY_TTL_FRAMES

        # TTL Decay
        for i in range(self.active_players):
            if not player_status[i]:
                if self.memory[i]['ttl'] > 0:
                    self.memory[i]['ttl'] -= 1
                else:
                    self.memory[i]['eyes'] = []
                    self.memory[i]['box'] = ()
                    self.memory[i]['nose_x'] = -1.0 

        return self._evaluate_action(player_status)

    def _evaluate_action(self, status):
        left_covered = status[0]
        rescue_condition = False
        
        if self.active_players == 3:
            center_covered = status[1]
            right_covered = status[2]
            if left_covered and center_covered and right_covered:
                rescue_condition = True
        elif self.active_players == 2:
            right_covered = status[1]
            if left_covered and right_covered:
                rescue_condition = True

        action_text = "RETURN_NEUTRAL"
        action_color = config.COLOR_WHITE
        active_keys = []

        if rescue_condition:
            active_keys.append("RESCUE")
            action_text, action_color = "RESCUE_ACTIVATED", config.COLOR_RED
            
            # Block steering during rescue
            self.steering_val *= 0.8
        
        # Continuous Steering (Float calculation)
        is_turning = False
        if not rescue_condition:
            if self.active_players == 3:
                if left_covered and not center_covered and not right_covered:
                    self.steering_val = max(-1.0, self.steering_val - config.PWM_STEP)
                    is_turning = True
                    action_text, action_color = "TURN_LEFT", config.COLOR_CYAN
                elif not left_covered and not center_covered and right_covered:
                    self.steering_val = min(1.0, self.steering_val + config.PWM_STEP)
                    is_turning = True
                    action_text, action_color = "TURN_RIGHT", config.COLOR_CYAN
            elif self.active_players == 2:
                if left_covered and not right_covered:
                    self.steering_val = max(-1.0, self.steering_val - config.PWM_STEP)
                    is_turning = True
                    action_text, action_color = "TURN_LEFT", config.COLOR_CYAN
                elif not left_covered and right_covered:
                    self.steering_val = min(1.0, self.steering_val + config.PWM_STEP)
                    is_turning = True
                    action_text, action_color = "TURN_RIGHT", config.COLOR_CYAN
                    
            if not is_turning:
                self.steering_val *= config.PWM_DECAY
                if abs(self.steering_val) < config.PWM_DEADZONE:
                    self.steering_val = 0.0

            # --- PWM Key Output Logic ---
            self.pwm_counter = (self.pwm_counter + 1) % config.PWM_WINDOW_FRAMES
            active_keys.extend(["R_LEFT", "R_RIGHT"]) # Default release

            if self.steering_val < -config.PWM_DEADZONE: # Left
                duty_frames = int(abs(self.steering_val) * config.PWM_WINDOW_FRAMES)
                if self.pwm_counter < duty_frames:
                    active_keys.remove("R_LEFT")
                    active_keys.append("P_LEFT")
            elif self.steering_val > config.PWM_DEADZONE: # Right
                duty_frames = int(abs(self.steering_val) * config.PWM_WINDOW_FRAMES)
                if self.pwm_counter < duty_frames:
                    active_keys.remove("R_RIGHT")
                    active_keys.append("P_RIGHT")

        return action_text, action_color, self.steering_val, active_keys