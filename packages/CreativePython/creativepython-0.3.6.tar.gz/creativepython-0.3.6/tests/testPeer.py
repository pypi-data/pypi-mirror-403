# localhost_udp_test.py
import socket

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("127.0.0.1", 57111))
print("Listening on 127.0.0.1:57111")
while True:
    data, addr = sock.recvfrom(4096)
    print("Received:", data, "from", addr)