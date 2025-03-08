import socket
import os

def list_files():
    files = os.listdir('.')
    return "\n".join(files)

def handle_client(conn):
    while True:
        try:
            command = conn.recv(1024).decode()
            if not command:
                break
        except Exception as e:
            print("Error:", e)
            break

        if command.startswith("LIST"):
            files = list_files()
            conn.send(files.encode())
        
        elif command.startswith("DOWNLOAD"):
            parts = command.split(maxsplit=1)
            if len(parts) < 2:
                conn.send("ER".encode())
                continue
            filename = parts[1].strip()
            if not os.path.exists(filename):
                conn.send("ER".encode())
            else:
                conn.send("OK".encode()) 
                file_size = os.path.getsize(filename)
                header = f"{file_size:<10}"
                conn.send(header.encode())
                with open(filename, "rb") as f:
                    while chunk := f.read(1024):
                        conn.send(chunk)
        
        elif command.startswith("UPLOAD"):
            parts = command.split(maxsplit=1)
            if len(parts) < 2:
                conn.send("ER".encode())
                continue
            filename = parts[1].strip()
            conn.send("READY".encode())
            with open(filename, "wb") as f:
                while True:
                    data = conn.recv(1024)
                    if data.endswith(b"EOF"):
                        f.write(data[:-3])
                        break
                    f.write(data)
        
        elif command.startswith("EXIT"):
            break
        
        else:
            conn.send("ER".encode())
    conn.close()

def main():
    host = "0.0.0.0"
    port = 8080
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((host, port))
    server_socket.listen(5)
    print("Server waiting for connections…")
    while True:
        conn, addr = server_socket.accept()
        print("Connected to:", addr)
        handle_client(conn)

if __name__ == "__main__":
    main()
