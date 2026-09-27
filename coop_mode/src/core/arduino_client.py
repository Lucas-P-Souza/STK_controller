import serial
import socket
import time
import threading

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def send_cmd(sock, cmd):
    """Sends a UDP command to the server."""
    sock.sendto(cmd.encode("utf-8"), (config.UDP_IP, config.UDP_PORT))

def main():
    """Main loop for reading Arduino serial data and forwarding actions."""
    print(f"[INFO] Connecting to Arduino on port {config.SERIAL_PORT}...")
    try:
        ser = serial.Serial(config.SERIAL_PORT, config.BAUD_RATE, timeout=1)
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
    state_drift = False
    last_motor_time = 0.0

    try:
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='ignore').strip()
                if not line:
                    continue
                
                parts = line.split(',')
                if len(parts) == 4:
                    try:
                        distance = float(parts[0])
                        nitro_flag = int(parts[1])
                        accel_flag = int(parts[2])
                        drift_flag = int(parts[3])

                        # 1. Fire Logic (Ultrasonic)
                        if distance > 0 and distance <= config.DISTANCE_THRESHOLD:
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
                                    """Holds nitro and acceleration for a set duration."""
                                    send_cmd(sock, "P_NITRO")
                                    send_cmd(sock, "P_ACCELERATE")
                                    print("[ACTION] NITRO ENGAGED")
                                    time.sleep(2.0)
                                    send_cmd(sock, "R_NITRO")
                                    send_cmd(sock, "R_ACCELERATE")
                                    print("[ACTION] NITRO RELEASED")
                                threading.Thread(target=hold_nitro, daemon=True).start()
                                state_nitro = True
                        else:
                            state_nitro = False

                        # 3. Acceleration & Braking Logic (Time-Held)
                        if accel_flag == 1:
                            last_motor_time = time.time()
                            if state_brake:
                                send_cmd(sock, "R_BRAKE")
                                state_brake = False
                            if not state_accelerate:
                                send_cmd(sock, "P_ACCELERATE")
                                print(f"[ACTION] ACCELERATING (Holding for {config.MOTOR_HOLD_SECONDS}s)")
                                state_accelerate = True
                        elif accel_flag == 2:
                            last_motor_time = time.time()
                            if state_accelerate:
                                send_cmd(sock, "R_ACCELERATE")
                                state_accelerate = False
                            if not state_brake:
                                send_cmd(sock, "P_BRAKE")
                                print(f"[ACTION] BRAKING (Holding for {config.MOTOR_HOLD_SECONDS}s)")
                                state_brake = True
                        else:
                            # Stopped, but check if hold time has passed
                            if time.time() - last_motor_time >= config.MOTOR_HOLD_SECONDS:
                                if state_accelerate:
                                    send_cmd(sock, "R_ACCELERATE")
                                    print("[ACTION] MOTOR STOPPED (Hold time expired)")
                                    state_accelerate = False
                                if state_brake:
                                    send_cmd(sock, "R_BRAKE")
                                    print("[ACTION] MOTOR STOPPED (Hold time expired)")
                                    state_brake = False

                        # 4. Drift Logic (Touch Sensor)
                        if drift_flag == 1:
                            if not state_drift:
                                send_cmd(sock, "P_SKIDDING")
                                print("[ACTION] DRIFTING (Touch)")
                                state_drift = True
                        else:
                            if state_drift:
                                send_cmd(sock, "R_SKIDDING")
                                print("[ACTION] DRIFT RELEASED")
                                state_drift = False

                    except ValueError:
                        pass # Ignore malformed data
            else:
                # Still check timeout even if no data is received yet
                if time.time() - last_motor_time >= config.MOTOR_HOLD_SECONDS:
                    if state_accelerate:
                        send_cmd(sock, "R_ACCELERATE")
                        print("[ACTION] MOTOR STOPPED (Hold time expired)")
                        state_accelerate = False
                    if state_brake:
                        send_cmd(sock, "R_BRAKE")
                        print("[ACTION] MOTOR STOPPED (Hold time expired)")
                        state_brake = False
                        
                time.sleep(0.01)

    except KeyboardInterrupt:
        print("\n[INFO] Shutting down...")
    finally:
        ser.close()
        sock.close()

if __name__ == "__main__":
    main()
