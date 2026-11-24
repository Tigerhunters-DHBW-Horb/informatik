import socket
import time

MULTICAST_IP = "224.5.23.2"
PORT = 10006

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

counter = 0

print(f"Sende Testdaten an {MULTICAST_IP}:{PORT}")

while True:
    message = f"Testpaket {counter}".encode("utf-8")

    sock.sendto(message, (MULTICAST_IP, PORT))

    print(f"Gesendet: {message.decode()}")

    counter += 1

    time.sleep(1)
