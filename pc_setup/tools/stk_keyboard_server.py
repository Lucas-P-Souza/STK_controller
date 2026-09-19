#!/usr/bin/env python3
import sys
import os
import time
import socket
import keyboard

# Exigir sudo no Linux para injeção de hardware
if os.geteuid() != 0:
    print("\033[91mErro: Este script manipula eventos de hardware e precisa ser executado como root (sudo).\x1b[0m")
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
    """Milagrosa função de tap que burla o Wayland e os 60FPS do jogo!"""
    keyboard.press(key)
    time.sleep(0.05) # Delay crucial para o jogo registrar o frame
    keyboard.release(key)

# Hardware level bindings com a lib 'keyboard'
bindings = [
    ['P_LEFT', 'left', keyboard.press],
    ['R_LEFT', 'left', keyboard.release],
    ['P_RIGHT', 'right', keyboard.press],
    ['R_RIGHT', 'right', keyboard.release],
    ['RESCUE', 'backspace', human_tap],
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
