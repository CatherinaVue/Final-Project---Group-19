import os
import socket
import struct
import pwinput
import time

# IP = "192.168.1.101" #"localhost"
IP = "10.200.102.77"
PORT = 4450
ADDR = (IP, PORT)
SIZE = 1024  ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"


def send_file(client, filename):
    filepath = filename

    if not os.path.isfile(filepath):
        print("File doesn't exist")
        return

    filesize = os.path.getsize(filepath)
    filename = os.path.basename(filename).encode(FORMAT)

    client.sendall(struct.pack("!I", len(filename)))
    client.sendall(filename)
    client.sendall(struct.pack("!Q", filesize))

    # Start measuring upload time
    start_time = time.perf_counter()

    with open(filepath, "rb") as file:
        while True:
            data = file.read(SIZE)
            if not data:
                break
            client.sendall(data)

    # Stop measuring upload time
    end_time = time.perf_counter()

    elapsed = end_time - start_time
    filesize_mb = filesize / (1024 * 1024)
    speed = filesize_mb / elapsed if elapsed > 0 else 0

    print("\n=== UPLOAD PERFORMANCE ===")
    print(f"File size: {filesize_mb:.2f} MiB")
    print(f"Transfer time: {elapsed:.4f} seconds")
    print(f"Upload speed: {speed:.2f} MiB/s")
    print("===========================")
    print("File uploaded successfully")


def receive_file(client):
    filename_length = struct.unpack("!I", recv_exact(client, 4))[0]
    filename = recv_exact(client, filename_length).decode(FORMAT)
    filename = os.path.basename(filename)

    filesize = struct.unpack("!Q", recv_exact(client, 8))[0]

    os.makedirs("client_data", exist_ok=True)
    filepath = os.path.join("client_data", filename)

    received = 0

    # Start measuring download time
    start_time = time.perf_counter()

    with open(filepath, "wb") as file:
        while received < filesize:
            data = client.recv(min(SIZE, filesize - received))

            if not data:
                raise ConnectionError("Connection lost")

            file.write(data)
            received += len(data)

    # Stop measuring download time
    end_time = time.perf_counter()

    elapsed = end_time - start_time
    filesize_mb = filesize / (1024 * 1024)
    speed = filesize_mb / elapsed if elapsed > 0 else 0

    print("\n=== DOWNLOAD PERFORMANCE ===")
    print(f"File size: {filesize_mb:.2f} MiB")
    print(f"Transfer time: {elapsed:.4f} seconds")
    print(f"Download speed: {speed:.2f} MiB/s")
    print("=============================")
    print(f"{filename} downloaded successfully")


def recv_exact(conn, length):
    data = b""
    while len(data) < length:
        packet = conn.recv(length - len(data))
        if not packet:
            raise ConnectionError("Connection lost")
        data += packet
    return data


def main():
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(ADDR)
    while True:  ### multiple communications
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split("@")

        if cmd == "AUTH":
            answer = pwinput.pwinput(prompt=f"{msg} ", mask="*").strip()
            client.send(answer.encode(FORMAT))
        elif cmd == "OK":
            print(msg)
            print(
                "=== COMMANDS ===\n1. UPLOAD\n2. DOWNLOAD\n3. DELETE\n4. DIR\n5. SUBCREATE\n6. SUBDELETE\n7. LOGOUT\n================")
            data = input("> ")
            data = data.split(" ")
            cmd = data[0]
            if cmd == "TASK":
                client.send(cmd.encode(FORMAT))

            elif cmd == "UPLOAD":
                filename = input("Enter filename: ")
                client.sendall(b"UPLOAD")
                response = client.recv(SIZE).decode(FORMAT)
                if response == "READY":
                    send_file(client, filename)
                else:
                    print(response)

            elif cmd == "DOWNLOAD":
                filename = input("Enter filename: ")
                client.sendall(b"DOWNLOAD")
                response = client.recv(SIZE).decode(FORMAT)
                if response == "READY":
                    client.sendall(filename.encode(FORMAT))
                    response = client.recv(SIZE).decode(FORMAT)
                    if response == "FILE":
                        receive_file(client)
                    else:
                        print(response)
                else:
                    print(response)

            elif cmd == "DELETE":
                filename = input("Enter filename: ")
                start_time = time.perf_counter()
                client.sendall(f"DELETE@{filename}".encode(FORMAT))
                response = client.recv(SIZE).decode(FORMAT)
                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000
                print(response)
                print(f"System response time: {response_time:.2f} ms")


            elif cmd == "DIR":
                start_time = time.perf_counter()
                client.sendall(b"DIR")
                response = client.recv(SIZE).decode(FORMAT)
                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000
                print("\n=== SERVER DIRECTORY ===")
                print(response)
                print("========================")
                print(f"System response time: {response_time:.2f} ms")

            elif cmd == "SUBCREATE":
                foldername = input("Enter folder name: ")
                start_time = time.perf_counter()
                client.sendall(f"SUBCREATE@{foldername}".encode(FORMAT))
                response = client.recv(SIZE).decode(FORMAT)
                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000
                print(response)
                print(f"System response time: {response_time:.2f} ms")

            elif cmd == "SUBDELETE":
                foldername = input("Enter folder name: ")
                start_time = time.perf_counter()
                client.sendall(f"SUBDELETE@{foldername}".encode(FORMAT))
                response = client.recv(SIZE).decode(FORMAT)
                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000
                print(response)
                print(f"System response time: {response_time:.2f} ms")

            elif cmd == "LOGOUT":
                client.send(cmd.encode(FORMAT))
                break
        elif cmd == "DISCONNECTED":
            print(msg)
            break

    print("Disconnected from the server.")
    client.close()  ## close the connection


if __name__ == "__main__":
    main()
