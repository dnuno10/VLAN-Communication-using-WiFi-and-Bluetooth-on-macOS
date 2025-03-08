import socket
import os

def list_files(client_socket):
    client_socket.send("LIST".encode())
    files = client_socket.recv(4096).decode()
    print("\nAvailable files on server:\n" + files)

def download_file(client_socket):
    filename = input("Enter the filename to download: ")
    client_socket.send(f"DOWNLOAD {filename}".encode())

    status = client_socket.recv(2).decode()
    if status != "OK":
        print(f"File '{filename}' not found on server.")
        return

    file_size_str = client_socket.recv(10).decode()
    try:
        file_size = int(file_size_str.strip())
    except ValueError:
        print("Error al recibir el tamaño del archivo.")
        return

    bytes_received = 0
    with open(filename, "wb") as file:
        while bytes_received < file_size:
            data = client_socket.recv(1024)
            if not data:
                break
            file.write(data)
            bytes_received += len(data)

    print(f"File '{filename}' downloaded successfully!")

def upload_file(client_socket):
    """Send file to server."""
    filename = input("Enter the filename to upload: ")

    if not os.path.exists(filename):
        print("File not found!")
        return

    client_socket.send(f"UPLOAD {filename}".encode())

    response = client_socket.recv(1024).decode()
    if response != "READY":
        print("Server did not acknowledge file transfer. Aborting.")
        return

    with open(filename, "rb") as file:
        while (chunk := file.read(1024)):
            client_socket.send(chunk)
    client_socket.send(b"EOF")

    print(f"File '{filename}' uploaded successfully!")

def client_program():
    server_ip = "192.168.1.70"
    port = 8080

    while True:
        print("\nOptions:")
        print("1. List files on server")
        print("2. Download file from server")
        print("3. Upload file to server")
        print("4. Exit")
        choice = input("Enter choice: ")

        client_socket = socket.socket()
        client_socket.connect((server_ip, port))

        if choice == "1":
            list_files(client_socket)
        elif choice == "2":
            download_file(client_socket)
        elif choice == "3":
            upload_file(client_socket)
        elif choice == "4":
            client_socket.send("EXIT".encode())
            client_socket.close()
            break
        else:
            print("Invalid choice.")

        client_socket.close()

if __name__ == "__main__":
    client_program()
