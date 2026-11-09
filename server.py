import os
import socket
import threading

IP = "10.200.102.77"
PORT = 4450
ADDR = (IP,PORT)
SIZE = 1024
FORMAT = "utf-8"
SERVER_PATH = "server"

### to handle the clients
def handle_client (conn,addr):

    print(f"[NEW CONNECTION] {addr} connected.")
    conn.send("OK@Welcome to the server".encode(FORMAT))
### Ask Clients for User and Pass
    conn.send("AUTH@Username: ".encode(FORMAT))
    username = conn.recv(SIZE).decode(FORMAT)

    conn.send("AUTH@Password: ".encode(FORMAT))
    password = conn.recv(SIZE).decode(FORMAT)

    if username == "Client1" and password == 1234:
        conn.send("OK@Login successful!".encode(FORMAT))
        print(f"{username} logged in.")
    else:
        conn.send("ERROR@Invalid username or password".encode(FORMAT))
        print(f"[FAILED LOGIN] {addr}")
        conn.close()
        return

    while True:
        data =  conn.recv(SIZE).decode(FORMAT)
        data = data.split("@")
        cmd = data[0]
       
        send_data = "OK@"

        if cmd == "LOGOUT":
            break

        elif cmd == "TASK": 
            send_data += "LOGOUT from the server.\n"

            conn.send(send_data.encode(FORMAT))



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

