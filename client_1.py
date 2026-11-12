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
            client.send(cmd.encode(FORMAT))

        elif cmd == "DELETE":
            client.send(cmd.encode(FORMAT))

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
