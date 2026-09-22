import serial
import socket
import time
import threading

# --- CONFIGURATION ---
# Target serial port (adjust as needed, e.g., /dev/ttyUSB0)
SERIAL_PORT = "/dev/ttyACM0" 
BAUD_RATE = 9600

# STK Server settings
UDP_IP = "127.0.0.1"
UDP_PORT = 6006

# Maximum distance (cm) for item activation
DISTANCE_THRESHOLD = 5.0  

def send_cmd(sock, cmd):
    sock.sendto(cmd.encode("utf-8"), (UDP_IP, UDP_PORT))

def main():
    print(f"[INFO] Connecting to Arduino on port {SERIAL_PORT}...")
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        time.sleep(2) # Wait for Arduino to reset
    except Exception as e:
        print(f"[ERROR] Failed to open serial port: {e}")
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    print("[SUCCESS] Arduino Client connected. Forwarding to STK Server (port 6006).")

    # State tracking
    state_fire = False
    state_nitro = False
    state_accelerate = False
    state_brake = False

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                parts = line.split(',')
                # Expecting: distance, nitro_flag, accel_flag
                if len(parts) == 3:
                    try:
                        distance = float(parts[0])
                        nitro_flag = int(parts[1])
                        accel_flag = int(parts[2])

                        # 1. Fire Logic (Ultrasonic)
                        if distance > 0 and distance <= DISTANCE_THRESHOLD:
                            if not state_fire:
                                send_cmd(sock, "FIRE")
                                print(f"[ACTION] FIRE! (Dist: {distance}cm)")
                                state_fire = True
                        else:
                            state_fire = False

                        # 2. Nitro Logic
                        if nitro_flag == 1:
                            if not state_nitro:
                                def hold_nitro():
                                    send_cmd(sock, "P_NITRO")
                                    print("[ACTION] NITRO ENGAGED")
                                    time.sleep(2.0)
                                    send_cmd(sock, "R_NITRO")
                                    print("[ACTION] NITRO RELEASED")
                                threading.Thread(target=hold_nitro, daemon=True).start()
                                state_nitro = True
                        else:
                            state_nitro = False

                        # 3. Acceleration & Braking Logic (Analog Motor)
                        if accel_flag == 1:
                            # Forward
                            if state_brake:
                                send_cmd(sock, "R_BRAKE")
                                state_brake = False
                            if not state_accelerate:
                                send_cmd(sock, "P_ACCELERATE")
                                print("[ACTION] ACCELERATING (Forward)")
                                state_accelerate = True
                        elif accel_flag == 2:
                            # Backward / Brake
                            if state_accelerate:
                                send_cmd(sock, "R_ACCELERATE")
                                state_accelerate = False
                            if not state_brake:
                                send_cmd(sock, "P_BRAKE")
                                print("[ACTION] BRAKING (Backward)")
                                state_brake = True
                        else:
                            # Stopped
                            if state_accelerate:
                                send_cmd(sock, "R_ACCELERATE")
                                print("[ACTION] MOTOR STOPPED (Released Gas)")
                                state_accelerate = False
                            if state_brake:
                                send_cmd(sock, "R_BRAKE")
                                print("[ACTION] MOTOR STOPPED (Released Brake)")
                                state_brake = False

                    except ValueError:
                        pass # Ignore malformed data
            else:
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
    finally:
        ser.close()
        sock.close()

if __name__ == "__main__":
    main()
