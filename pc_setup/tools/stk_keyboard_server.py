#!/usr/bin/env python3
import sys
import socket
from pynput.keyboard import Key, Controller

GREEN = '\033[92m'
WHITE = '\x1b[0m'
YELLOW = '\033[93m'
RED = '\033[91m'

stop = False
DEBUG = False

address = ('localhost', 6006)
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(address)

keyboard = Controller()

def human_tap(key):
    """Vulnerable Wayland tap implementation using pynput."""
    keyboard.tap(key)

# Hardware level bindings
bindings = [
    ['P_LEFT', Key.left, keyboard.press],
    ['R_LEFT', Key.left, keyboard.release],
    ['P_RIGHT', Key.right, keyboard.press],
    ['R_RIGHT', Key.right, keyboard.release],
    ['RESCUE', Key.backspace, human_tap],
    ['P_ACCELERATE', Key.up, keyboard.press],
    ['R_ACCELERATE', Key.up, keyboard.release],
    ['P_BRAKE', Key.down, keyboard.press],
    ['R_BRAKE', Key.down, keyboard.release]
]

commands = [b[0] for b in bindings]

if len(sys.argv) > 1:
    for i in range(1, len(sys.argv)):
        if sys.argv[i] == '-d':
            DEBUG = True

print('\nSTK Keyboard Emulator Server (pynput version) started ', end='')
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
