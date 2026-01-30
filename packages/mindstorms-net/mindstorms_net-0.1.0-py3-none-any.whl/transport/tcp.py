import socket

class TCPTransport:
    def __init__(self, host, port=9000):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((host, port))

    def send(self, msg):
        self.sock.send(msg.encode('utf-8') + b"\n")

    def receive(self):
        self.sock.setblocking(False)
        try:
            data = self.sock.recv(1024).decode()
            return data.split("\n") if data else []
        except:
            return []
