import os
import socket
import struct

# IP = "192.168.1.101" #"localhost"
IP = "10.200.102.77"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024 ## byte .. buffer size
FORMAT = "utf-8"
SERVER_DATA_PATH = "server_data"

def send_file(client, filename):
    filepath=filename
    if not os.path.isfile(filepath):
        print("File doesn't exist")
        return
    filesize=os.path.getsize(filepath)
    filename=os.path.basename(filename).encode(FORMAT)
    client.sendall(struct.pack.("!I", len(filename)))
    client.sendall(filename)
    client.sendall(struct.pack("!Q", filesize))
    with open(filepath, "rb") as file:
        while True:
            data=file.read(SIZE)
            if not data:
                break
            client.sendall(data)
    print("File uploaded successfully")

def receive_file(client):
    filename_length=struct.unpack("!I", recv_exact(client, 4))[0]
    filename=recv_exact(client, filename_length).decode(FORMAT)
    filename=os.path.basename(filename)
    filesize=struct.unpack("!Q", recv_exact(client, 8))[0]
    os.makedirs("client_data", exist_ok=True)
    filepath=os.path.join("client_data", filename)
    received=0
    with open(filepath, "wb") as file:
        while received<filesize:
            data=client.recv(min(SIZE, filesize-received))
            if not data:
                raise ConnectionError("Connection lost")
            file.write(data)
            received+=len(data)
    print(f"{filename} downloaded successfully")

def recv_exact(conn, length):
    data=b""
    while len(data)<length:
        packet=conn.recv(length-len(data))
        if not packet:
            raise ConnectionError("Connection lost")
        data+=packet
    return data

def main():
    
    client = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    client.connect(ADDR)
    while True:  ### multiple communications
        data = client.recv(SIZE).decode(FORMAT)
        cmd, msg = data.split("@")
        if cmd == "OK":
            print(f"{msg}")
        elif cmd == "DISCONNECTED":
            print(f"{msg}")
            break

        printf("=== COMMANDS ===\n1. UPLOAD\n2. DOWNLOAD\n3. DELETE\n4. DIR\n5. SUBCREATE\n6. SUBDELETE\n7. LOGOUT\n================")
        
        data = input("> ") 
        data = data.split(" ")
        cmd = data[0]

        if cmd == "TASK":
            client.send(cmd.encode(FORMAT))

        elif cmd == "UPLOAD":
            filename=input(Enter filename: ")
            client.sendall(b"UPLOAD")
            response=client.recv(SIZE).decode(FORMAT)
            if response=="READY":
                send_file(client, filename)
            else:
                print(response)

        elif cmd == "DOWNLOAD":
            filename=input("Enter filename: ")
            client.sendall(b"DOWNLOAD")
            response=client.recv(SIZE).decode(FORMAT)
            if response=="READY":
                client.sendall(filename.encode(FORMAT))
                response=client.recv(SIZE).decode(FORMAT)
                if response=="FILE":
                    receive_file(client)
                else:
                    print(response)
            else:
                print(response)

        elif cmd == "DELETE":
            filename=input("Enter filename: ")
            client.sendall(f"DELETE@{filename}".encode(FORMAT))
            response=client.recv(SIZE).decode(FORMAT)
            print(response)

        elif cmd == "DIR":
            client.send(cmd.encode(FORMAT))

        elif cmd == "SUBCREATE":
            client.send(cmd.encode(FORMAT))

        elif cmd == "SUBDELETE":
            client.send(cmd.encode(FORMAT))

        elif cmd == "LOGOUT":
            client.send(cmd.encode(FORMAT))
            break
      



    print("Disconnected from the server.")
    client.close() ## close the connection

if __name__ == "__main__":
    main()
