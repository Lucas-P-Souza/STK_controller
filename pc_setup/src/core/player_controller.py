from src import config

class PlayerStateController:
    def __init__(self):
        self.active_players = config.MAX_PLAYERS

    def set_player_mode(self, num_players):
        if num_players in [1, 2, 3]:
            self.active_players = num_players

    def _extract_eye_coords(self, face_box):
        x, y, w, h = face_box
        eye_y = int(y + h * config.EYE_HEIGHT_RATIO)
        left_eye_x = int(x + w * 0.30)
        right_eye_x = int(x + w * 0.70)
        return [(left_eye_x, eye_y), (right_eye_x, eye_y)]

    def update(self, faces, hand_boxes, width, height):
        # We store status of [LeftEye, RightEye] for each player
        player_status = {i: [False, False] for i in range(self.active_players)}
        
        if len(faces) > 0:
            sorted_faces = sorted(faces, key=lambda f: f[0])
            
            for i in range(min(len(sorted_faces), self.active_players)):
                face_box = sorted_faces[i]
                eyes = self._extract_eye_coords(face_box)
                
                # Check left eye (eyes[0])
                left_eye_pt = eyes[0]
                left_covered = False
                for h_box in hand_boxes:
                    hx, hy, hw, hh = h_box
                    if hx < left_eye_pt[0] < (hx + hw) and hy < left_eye_pt[1] < (hy + hh):
                        left_covered = True
                        break
                
                # Check right eye (eyes[1])
                right_eye_pt = eyes[1]
                right_covered = False
                for h_box in hand_boxes:
                    hx, hy, hw, hh = h_box
                    if hx < right_eye_pt[0] < (hx + hw) and hy < right_eye_pt[1] < (hy + hh):
                        right_covered = True
                        break

                player_status[i] = [left_covered, right_covered]

        return self._evaluate_action(player_status)

    def _evaluate_action(self, status):
        action_text = "RETURN_NEUTRAL"
        action_color = config.COLOR_WHITE
        
        if self.active_players == 1:
            # 1 Player Mode (For testing alone): Left eye = Left, Right eye = Right
            left_eye_covered = status[0][0]
            right_eye_covered = status[0][1]
            
            if left_eye_covered and not right_eye_covered:
                action_text, action_color = "TURN_LEFT", config.COLOR_CYAN
            elif not left_eye_covered and right_eye_covered:
                action_text, action_color = "TURN_RIGHT", config.COLOR_CYAN
                
        elif self.active_players == 3:
            # 3 Player Mode (Final Project): P1 = Left, P2 = Center, P3 = Right
            # A player is considered covered if ANY eye is covered
            p1_covered = status[0][0] or status[0][1]
            p2_covered = status[1][0] or status[1][1]
            p3_covered = status[2][0] or status[2][1]
            
            if p1_covered and not p2_covered and not p3_covered:
                action_text, action_color = "TURN_LEFT", config.COLOR_CYAN
            elif not p1_covered and not p2_covered and p3_covered:
                action_text, action_color = "TURN_RIGHT", config.COLOR_CYAN

        return action_text, action_color
