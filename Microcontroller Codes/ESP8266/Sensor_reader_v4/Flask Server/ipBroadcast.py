import socket

DISCOVERY_PORT = 4210

def discovery_server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(("", DISCOVERY_PORT))

    print("Discovery service running...")

    while True:
        data, addr = sock.recvfrom(1024)
        message = data.decode()

        if message == "WHO_IS_SERVER_PROA_II":
            print(f"Discovery request from {addr}")
            sock.sendto(b"SERVER_HERE", addr)

print("Starting discovery server thread...")