#------ IMPORTS ------

from oscpy.server import OSCThreadServer
from time import sleep
import socket
import time
import serial
import threading
import queue

#------ ARDUINO ------
SERIAL_PORT = "COM4"
BAUD_RATE = 9600
ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)

# Thread-safe queue to transmit lines read by the serial thread
serial_queue = queue.Queue(maxsize=1)
stop_serial_thread = threading.Event()


def serial_reader():
    """
    Runs in a separate thread: reads the serial port continuously.
    If Arduino freezes (e.g., blocked I2C bus), this thread stays blocked
    without slowing down the main control loop.
    """
    while not stop_serial_thread.is_set():
        try:
            line = ser.readline().decode('utf-8', errors='ignore').strip()
        except serial.SerialException as e:
            print(f"[serial_reader] serial port error: {e}")
            time.sleep(0.5)
            continue

        if line:
            # Keep only the most recent line: if the main thread
            # did not consume the previous one, overwrite it
            if serial_queue.full():
                try:
                    serial_queue.get_nowait()
                except queue.Empty:
                    pass
            serial_queue.put(line)


#------ COMMUNICATION WITH SERVER PROGRAM ------
address = ('localhost', 6006)
client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

#------ GLOBAL PARAMETERS ------
ANGLE_MIN = 10.0
ANGLE_MAX = 45.0
LOOP_HZ = 90
dt = 1.0 / LOOP_HZ
state = 0
state_lux = 0
state_dist = 0
rescue_state = 0

MIN_STATE_DURATION = 0.05
MAX_STATE_DURATION = 0.3

#------ GLOBAL FUNCTIONS ------
def normalize(raw_value, min_value, max_value):
    """
    Normalizes a raw value between min and max into a 0.0 to 1.0 range.
    """
    a = abs(raw_value)
    if a < min_value:
        return 0.0
    v = (a - min_value) / (max_value - min_value)
    return max(0.0, min(1.0, v))


def dump(address, *values):
    """
    Prints OSC messages received by the server.
    """
    print(u'{}: {}'.format(
        address.decode('utf8'),
        ', '.join(
            '{}'.format(v.decode('utf8') if isinstance(v, bytes) else v)
            for v in values if values
        )
    ))


#------ CLASS PULSE SEND MSG ------

class PulsedCommand:
    """
    Manages pulsed OSC commands to simulate button presses and releases.
    """

    def __init__(self, pressed_cmd, released_cmd):
        """
        Initializes a pulsed command with press and release OSC messages.
        """
        self.pressed_cmd = pressed_cmd
        self.released_cmd = released_cmd
        self.value = 0.0
        self.state = 'released'
        self.next_switch = 0.0

    def set_value(self, v):
        """
        Sets the command value clamped between 0.0 and 1.0.
        """
        self.value = max(0.0, min(1.0, v))

    def update(self, now):
        """
        Updates the pulsed command state based on elapsed time.
        """
        if now < self.next_switch:
            return

        if self.value <= 0.0:
            if self.state != 'released':
                client_socket.sendto(self.released_cmd, address)
                self.state = 'released'
            self.next_switch = now + MIN_STATE_DURATION
            return

        if self.value >= 1.0:
            if self.state != 'pressed':
                client_socket.sendto(self.pressed_cmd, address)
                self.state = 'pressed'
            self.next_switch = now + MIN_STATE_DURATION
            return

        if self.state == 'released':
            client_socket.sendto(self.pressed_cmd, address)
            self.state = 'pressed'
            t1 = MIN_STATE_DURATION + self.value * (MAX_STATE_DURATION - MIN_STATE_DURATION)
            self.next_switch = now + t1
        else:
            client_socket.sendto(self.released_cmd, address)
            self.state = 'released'
            t2 = MIN_STATE_DURATION + (1.0 - self.value) * (MAX_STATE_DURATION - MIN_STATE_DURATION)
            self.next_switch = now + t2


#------ GLOBAL PARAMETERS 2 ------
right_cmd = PulsedCommand(b'P_RIGHT', b'R_RIGHT')
left_cmd = PulsedCommand(b'P_LEFT', b'R_LEFT')


#------ DRIFT ------
def callback_press_pad_x(*values):
    """
    Sends skidding command when pad X is pressed.
    """
    if values:
        client_socket.sendto(b'P_SKIDDING', address)

def callback_press_pad_y(*values):
    """
    Placeholder callback for pad Y press.
    """
    pass

def callback_unpress_pad(*values):
    """
    Releases skidding command when pad is unpressed.
    """
    if values:
        client_socket.sendto(b'R_SKIDDING', address)



#------ CALLBACK GYROSCOPE FOR LEFT/RIGHT ------
def callback_roll(*values):
    """
    Placeholder callback for gyroscope roll.
    """
    pass

def callback_pitch(*values):
    """
    Maps gyroscope pitch to left/right turning commands.
    """
    v = values[0]
    m = normalize(v, ANGLE_MIN, ANGLE_MAX)
    if v >= ANGLE_MIN:
        right_cmd.set_value(m)
        left_cmd.set_value(0.0)
    elif v <= -ANGLE_MIN:
        left_cmd.set_value(m)
        right_cmd.set_value(0.0)
    else:
        left_cmd.set_value(0.0)
        right_cmd.set_value(0.0)


def callback_yaw(*values):
    """
    Placeholder callback for gyroscope yaw.
    """
    pass


#------ CALLBACK HEAD POSITION FOR ACC/BRAKE AND RESCUE ------
def callback_head_pos(x, y, z):
    """
    Maps head position coordinates to acceleration, braking, and rescue commands.
    """
    global state, rescue_state
    if x > -5:
        state = 1
        client_socket.sendto(b'P_ACCELERATE', address)
        client_socket.sendto(b'R_BRAKE', address)
    elif -10 <= x <= -5:
        state = 2
        client_socket.sendto(b'R_ACCELERATE', address)
        client_socket.sendto(b'P_BRAKE', address)
    elif state != 0:
        state = 0
        client_socket.sendto(b'R_ACCELERATE', address)
        client_socket.sendto(b'P_BRAKE', address)

    if z <= 20 and rescue_state == 1:
        client_socket.sendto(b'P_RESCUE', address)
        rescue_state = 0
    elif rescue_state != 1:
        rescue_state = 1
        client_socket.sendto(b'R_RESCUE', address)






#------ FIRE WITH ARDUINO ------
def fire_ultrasound(dist):
    """
    Fires weapon when ultrasonic sensor detects an object within 5cm.
    """
    global state_dist
    if dist:
        try:
            distance_cm = float(dist)
            if distance_cm <= 5 and distance_cm > 0:
                client_socket.sendto(b'P_FIRE', address)
                state_dist = 0
            elif state_dist == 0:
                client_socket.sendto(b'R_FIRE', address)
                state_dist = 1
        except ValueError:
            pass


#------ NITRO WITH ARDUINO ------
def nitro_lux(lux):
    """
    Triggers nitro when light sensor reading falls below a threshold.
    """
    global state_lux
    if lux:
        try:
            lux_val = float(lux)
            if lux_val <= 400:
                client_socket.sendto(b'P_NITRO', address)
                state_lux = 1
            elif state_lux == 1:
                client_socket.sendto(b'R_NITRO', address)
                state_lux = 0
        except ValueError:
            pass



#------ MAIN ------
def main():
    """
    Main entry point: initializes server, binds callbacks, and runs the control loop.
    """
    osc = OSCThreadServer(default_handler=dump)
    osc.listen(address='0.0.0.0', port=8000, default=True)
    print("---------------------")

    osc.bind(b'/multisense/orientation/pitch', callback_pitch)  # LEFT RIGHT
    osc.bind(b'/multisense/orientation/roll', callback_roll)    # pass
    osc.bind(b'/multisense/orientation/yaw', callback_yaw)      # pass
    osc.bind(b'/multisense/pad/x', callback_press_pad_x)    # DRIFT
    osc.bind(b'/multisense/pad/y', callback_press_pad_y)    # DRIFT
    osc.bind(b'/multisense/pad/touchUP', callback_unpress_pad)    # DRIFT
    osc.bind(b'/tracker/head/pos_xyz', callback_head_pos)       # ACC/BRAKE AND RESCUE

    # Dedicated thread for serial reading to prevent blocking the 90Hz loop
    reader_thread = threading.Thread(target=serial_reader, daemon=True)
    reader_thread.start()

    try:
        while True:
            now = time.time()
            right_cmd.update(now)
            left_cmd.update(now)

            # ARDUINO: take the latest available line without blocking
            try:
                line = serial_queue.get_nowait()
                parts = line.split(",")
                if len(parts) == 2:
                    dist, lux = parts
                    fire_ultrasound(dist)  # FIRE
                    nitro_lux(lux)         # NITRO
            except queue.Empty:
                pass

            time.sleep(dt)
    except KeyboardInterrupt:
        pass
    except Exception as e:
        # Prevent unexplained silent crash
        print(f"[main] unexpected error: {e}")
    finally:
        stop_serial_thread.set()
        osc.stop()


#------ TEST ------
if __name__ == '__main__':
    main()