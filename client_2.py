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

#helper function when sending files
def send_file(client, filename):
    filepath = filename

    if not os.path.isfile(filepath): #checks if file exists
        print("File doesn't exist")
        return

    filesize = os.path.getsize(filepath)
    filename = os.path.basename(filename).encode(FORMAT)

    client.sendall(struct.pack("!I", len(filename))) #prepare file structure
    client.sendall(filename)
    client.sendall(struct.pack("!Q", filesize))

    # Start measuring upload time
    start_time = time.perf_counter()

    with open(filepath, "rb") as file: #open and sending of file data
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

#helper function of receiving a file
def receive_file(client):
    filename_length = struct.unpack("!I", recv_exact(client, 4))[0] #checks file structure
    filename = recv_exact(client, filename_length).decode(FORMAT)
    filename = os.path.basename(filename)

    filesize = struct.unpack("!Q", recv_exact(client, 8))[0]

    os.makedirs("client_data", exist_ok=True) #client storage space for file
    filepath = os.path.join("client_data", filename)

    received = 0

    # Start measuring download time
    start_time = time.perf_counter()

    with open(filepath, "wb") as file: #open and download file
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

#helper function for file sizes
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
            answer = pwinput.pwinput(prompt=f"{msg} ", mask="*").strip() #security mask for authentication
            client.send(answer.encode(FORMAT))
        elif cmd == "OK": # shows command menu
            print(msg)
            print(
                "=== COMMANDS ===\n1. UPLOAD\n2. DOWNLOAD\n3. DELETE\n4. DIR\n5. SUBCREATE\n6. SUBDELETE\n7. LOGOUT\n================")
            data = input("> ")
            data = data.split(" ")
            cmd = data[0]
            if cmd == "TASK":
                client.send(cmd.encode(FORMAT))

            elif cmd == "UPLOAD": #uploading a file
                filename = input("Enter filename: ")
                client.sendall(b"UPLOAD")
                response = client.recv(SIZE).decode(FORMAT)
                if response == "READY": #confirms server side is ready for transfer
                    send_file(client, filename)
                else:
                    print(response)

            elif cmd == "DOWNLOAD": #downloading a file
                filename = input("Enter filename: ")
                client.sendall(b"DOWNLOAD")
                response = client.recv(SIZE).decode(FORMAT)
                if response == "READY": #confirms server side for file transfer
                    client.sendall(filename.encode(FORMAT))
                    response = client.recv(SIZE).decode(FORMAT)
                    if response == "FILE": #receives file when sent
                        receive_file(client)
                    else:
                        print(response)
                else:
                    print(response)

            elif cmd == "DELETE": #deleting a file
                filename = input("Enter filename: ")
                start_time = time.perf_counter()
                client.sendall(f"DELETE@{filename}".encode(FORMAT)) #sends command to server
                response = client.recv(SIZE).decode(FORMAT)
                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000
                print(response) #when command finishes
                print(f"System response time: {response_time:.2f} ms")


            elif cmd == "DIR": #viewing file directory
                start_time = time.perf_counter()
                client.sendall(b"DIR")
                response = client.recv(SIZE).decode(FORMAT)
                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000
                print("\n=== SERVER DIRECTORY ===")
                print(response) #shows files sent from server
                print("========================")
                print(f"System response time: {response_time:.2f} ms")

            elif cmd == "SUBCREATE": #creating a subfolder
                foldername = input("Enter folder name: ")
                start_time = time.perf_counter()
                client.sendall(f"SUBCREATE@{foldername}".encode(FORMAT)) #sends command for name of subfolder creation
                response = client.recv(SIZE).decode(FORMAT)
                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000
                print(response) #confirm when command complete
                print(f"System response time: {response_time:.2f} ms")

            elif cmd == "SUBDELETE": #deleting a subfolder
                foldername = input("Enter folder name: ")
                start_time = time.perf_counter()
                client.sendall(f"SUBDELETE@{foldername}".encode(FORMAT)) #checks server for subfolder name to delete
                response = client.recv(SIZE).decode(FORMAT)
                end_time = time.perf_counter()
                response_time = (end_time - start_time) * 1000
                print(response) #confirm when command complete
                print(f"System response time: {response_time:.2f} ms")

            elif cmd == "LOGOUT": #to disconnect client from server
                client.send(cmd.encode(FORMAT))
                break #ends connection
        elif cmd == "DISCONNECTED":
            print(msg)
            break

    print("Disconnected from the server.")
    client.close()  ## close the connection


if __name__ == "__main__":
    main()
