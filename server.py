import os
import socket
import threading
import struct

IP = "10.200.102.77"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_PATH = "server"

#helper function for file sizes
def recv_exact(conn, length):
    data=b""
    while len(data)<length:
        packet=conn.recv(length-len(data))
        if not packet:
            raise ConnectionError("Connection lost")
        data+=packet
    return data

### to handle the clients
def handle_client (conn,addr):

    print(f"[NEW CONNECTION] {addr} connected.")
### Ask Clients for User and Pass
    conn.send("AUTH@Username: ".encode(FORMAT))
    username = conn.recv(SIZE).decode(FORMAT).strip()

    conn.send("AUTH@Password: ".encode(FORMAT))
    password = conn.recv(SIZE).decode(FORMAT).strip()

    if (username == "Client1" or username == "Client2") and password == "1234": #verifies username and password
        conn.send("OK@Login successful!".encode(FORMAT))
        print(f"{username} logged in.")
    else:
        conn.send("ERROR@Invalid username or password".encode(FORMAT)) #if login info is incorrect
        print(f"[FAILED LOGIN] {addr}")
        conn.close()
        return

    while True: #run while connection is up
        data =  conn.recv(SIZE).decode(FORMAT)
        data = data.split("@") #for reading commands
        cmd = data[0]
       
        send_data = "OK@"

        if cmd == "LOGOUT": #to disconnect client from server
            break

        elif cmd == "UPLOAD": #handle file uploads
            conn.sendall("READY".encode(FORMAT))
            filename_length=struct.unpack("!I", recv_exact(conn, 4))[0] #examine file structure
            filename=recv_exact(conn, filename_length).decode(FORMAT)
            filename=os.path.basename(filename)
            filesize=struct.unpack("!Q", recv_exact(conn, 8))[0]
            os.makedirs(SERVER_PATH, exist_ok=True) #make space to store file
            filepath=os.path.join(SERVER_PATH, filename)
            received=0
            with open(filepath, "wb") as file: #storing file
                while received<filesize:
                    data=conn.recv(min(SIZE, filesize-received))
                    if not data:
                        break
                    file.write(data)
                    received+=len(data)
            print(f"[UPLOAD] Received {filename} from {username}") #confirmation message
            conn.send(f"OK@{username} uploaded {filename} successfully.".encode(FORMAT)) #resend command menu when finished

        elif cmd == "DOWNLOAD": #handle file downloads
            conn.sendall(b"READY")
            filename=conn.recv(SIZE).decode(FORMAT) #prepare file for transfer
            filename=os.path.basename(filename)
            filepath=os.path.join(SERVER_PATH, filename)
            if not os.path.isfile(filepath): #check if file exists
                conn.sendall(b"ERROR@File not found")
            else:
                conn.sendall(b"FILE")
                filename_bytes=filename.encode(FORMAT)
                filesize=os.path.getsize(filepath)
                conn.sendall(struct.pack("!I", len(filename_bytes))) #create file structure for client
                conn.sendall(filename_bytes)
                conn.sendall(struct.pack("!Q", filesize))
                with open(filepath, "rb") as file: #file transfer for client
                    while True:
                        data=file.read(SIZE)
                        if not data:
                            break
                        conn.sendall(data)
                print(f"[DOWNLOAD] Sent {filename} from {username}") #confirmation message
                conn.send(f"OK@{username} downloaded {filename} successfully.".encode(FORMAT)) #resend command menu when finished

        elif cmd == "DELETE": #handle deleting files
            filename=data[1]
            filename=os.path.basename(filename)
            filepath=os.path.join(SERVER_PATH, filename)
            if os.path.isfile(filepath): #check if file exists
                os.remove(filepath)
                conn.send(f"OK@{filename} deleted successfully by {username}".encode(FORMAT)) #confirmation and resend command menu
            else:
                send_data="ERROR@File not found" #stop at error
            conn.sendall(send_data.encode(FORMAT))
            print(f"[DELETE] {username} deleted {filename}") #when finished

        elif cmd == "DIR": #handle viewing directory
            files=os.listdir(SERVER_PATH)
            if len(files)==0: #check if files in directory
                conn.send(f"OK@{username}, the server directory is empty.".encode(FORMAT)) #message and resend command menu
            else:
                conn.send(f"OK@{username}, here are the files in the server directory:\n".encode(FORMAT)) #message and resend command menu
                send_data+="\n".join(files)
            conn.sendall(send_data.encode(FORMAT))
            print(f"[DIR] {username} viewed the server directory") #confirmation when finished

        elif cmd == "SUBCREATE": #handle creating a subfolder
            foldername=data[1]
            foldername=os.path.basename(foldername) #subfolder name
            folderpath=os.path.join(SERVER_PATH, foldername)
            if not os.path.exists(folderpath): #check for duplicates
                os.makedirs(folderpath)
                conn.send(f"'OK@{foldername}' created successfully by {username}".encode(FORMAT)) #message and resend command menu
            else:
                conn.send(f"'{foldername}' already exists".encode(FORMAT)) #message and resend command menu
            conn.sendall(send_data.encode(FORMAT))
            print(f"[SUBCREATE] {username} created folder {foldername}") #confirmation when finished

        elif cmd == "SUBDELETE": #handle deleting a subfolder
            foldername=data[1]
            foldername=os.path.basename(foldername) #subfolder name
            folderpath=os.path.join(SERVER_PATH, foldername)
            if os.path.isdir(folderpath) and not os.path.islink(folderpath): #check for subfolder existence
                try:
                    os.rmdir(folderpath)
                    conn.send(f"'OK@{foldername}' deleted successfully by {username}".encode(FORMAT)) #message and resend command menu
                except OSError:
                    conn.send(f"'{foldername}' is not empty".encode(FORMAT)) #stop at error
            else:
                conn.send(f"'OK@{foldername}' doesn't exist".encode(FORMAT)) #message and resend command menu
            conn.sendall(send_data.encode(FORMAT))
            print(f"[SUBDELETE] {username} deleted folder {foldername}") #confirmation when finished

        elif cmd == "TASK": 
            send_data += "OK@LOGGED OUT from the server.\n"

            conn.send(send_data.encode(FORMAT))
            print(f"[TASK] {username} LOGGED OUT from the server.\n")



    print(f"{addr} disconnected")
    conn.close()


def main():
    print("Starting the server")
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM) ## used IPV4 and TCP connection
    server.bind(ADDR) # bind the address
    server.listen() ## start listening
    print(f"server is listening on {IP}: {PORT}")
    while True:
        conn, addr = server.accept() ### accept a connection from a client
        thread = threading.Thread(target = handle_client, args = (conn, addr)) ## assigning a thread for each client
        thread.start()


if __name__ == "__main__":
    main()

