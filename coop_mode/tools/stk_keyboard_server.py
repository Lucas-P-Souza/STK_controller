#!/usr/bin/env python3
# Based on STK_input_server.py given in TP0 (Michael Ortega).
# Changes for the project:
#  - must be run with sudo on linux (the keyboard lib needs root)
#  - single press commands use human_tap instead of press_and_release

import sys
import os
import time
import socket
import keyboard

# Require sudo on Linux for hardware injection
if os.geteuid() != 0:
    print("\033[91mError: This script handles hardware events and must be run as root (sudo).\x1b[0m")
    sys.exit(1)

GREEN = '\033[92m'
WHITE = '\x1b[0m'
YELLOW = '\033[93m'
RED = '\033[91m'

stop = False
DEBUG = False

address = ('localhost', 6006)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(address)

def human_tap(key):
    """Press and release a key with a small delay."""
    keyboard.press(key)
    time.sleep(0.05) # Crucial delay for the game to register the input
    keyboard.release(key)

# Hardware level bindings with the 'keyboard' library
bindings = [
    ['UP', 'up', human_tap],
    ['DOWN', 'down', human_tap],
    ['LEFT', 'left', human_tap],
    ['RIGHT', 'right', human_tap],
    ['SELECT', 'enter', human_tap],
    ['CANCEL', 'backspace', human_tap],
    ['BACK', 'backspace', human_tap],
    ['FIRE', 'space', human_tap],
    ['NITRO', 'n', human_tap],
    ['P_NITRO', 'n', keyboard.press],
    ['R_NITRO', 'n', keyboard.release],
    ['P_SKIDDING', 'v', keyboard.press],
    ['R_SKIDDING', 'v', keyboard.release],
    ['P_LOOKBACK', 'b', keyboard.press],
    ['R_LOOKBACK', 'b', keyboard.release],
    ['RESCUE', 'backspace', human_tap],
    ['PAUSE', 'escape', human_tap],
    ['P_UP', 'up', keyboard.press],
    ['R_UP', 'up', keyboard.release],
    ['P_DOWN', 'down', keyboard.press],
    ['R_DOWN', 'down', keyboard.release],
    ['P_LEFT', 'left', keyboard.press],
    ['R_LEFT', 'left', keyboard.release],
    ['P_RIGHT', 'right', keyboard.press],
    ['R_RIGHT', 'right', keyboard.release],
    ['P_ACCELERATE', 'up', keyboard.press],
    ['R_ACCELERATE', 'up', keyboard.release],
    ['P_BRAKE', 'down', keyboard.press],
    ['R_BRAKE', 'down', keyboard.release]
]

commands = [b[0] for b in bindings]

if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-d':
            DEBUG = True

print('\nSTK Keyboard Emulator Server (Hardware Level) started ', end='')
if DEBUG:
    print(GREEN + '(Debug mode)' + WHITE)
print()

while not stop:
    try:
        data, addr = sock.recvfrom(1024)
        if type(data) is bytes:
            data = data.decode("utf-8").strip()

        if data == 'STOPSERVEUR':
            stop = True
        else:
            if data in commands:
                if DEBUG:
                    print(YELLOW + f'\t{data}' + WHITE)
                else:
                    b = bindings[commands.index(data)]
                    b[2](b[1])  # Execute keyboard function
            else:
                if DEBUG:
                    print(RED + f'\t{data} (Unknown)' + WHITE)
    except KeyboardInterrupt:
        break

print('STK Keyboard Emulator stopped')
