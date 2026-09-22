import socket
from src import config

class STKNetworkClient:
    def __init__(self, ip=config.UDP_IP, port=config.UDP_PORT):
        self.ip = ip
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.connected = True
        print(f"UDP Client initialized targeting {self.ip}:{self.port}")

    def send_command(self, cmd_string):
        """Sends a plain string command to the Keyboard Emulator Server."""
        if self.connected:
            self.client.sendto(cmd_string.encode('utf-8'), (self.ip, self.port))
