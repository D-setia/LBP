import socket

HOST = '127.0.0.1'  # The server's hostname or IP address
PORT = 65432        # The port used by the server

data = 12345
print(data.to_bytes(1024, "big"))
print(int.from_bytes(data.to_bytes(1024, "big"), "big"))
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((HOST, PORT))
        s.sendall(data.to_bytes(10, "big"))
        data = s.recv(1024)

        print('Received', repr(data))

