import hashlib
import socket
import time
import threading
import string    
import random


class ServerSocket:
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind((HOST, PORT))

    def start(self):
        self.socket.listen()
        print(f'[LISTENING] {self.HOST}:{self.PORT}')

        while True:
            conn, addr = self.socket.accept()
            print(f'[NEW CONNECTION] {addr}')

            thread = threading.Thread(target=self.handle_connection, args=(conn, addr))
            thread.start()
            print(f'[ACTIVE THREADS] {threading.activeCount()-1}')


    def handle_connection(self, conn, addr):
        if self.auth(conn, addr):
            connected = True
            while connected:   
                self.sendPacket(conn, addr, 1)
                connected = self.recievePacket(conn, addr)

        conn.close()  


    def auth(self, conn, addr):
        startString = "Start_Connection"
        privateString = "PRIVATE_KEY_THIRTY_TWO_CHARACTER"
        randomString = str(''.join(random.choices(string.ascii_letters, k=32)))
        sha1Result = hashlib.sha1(privateString.encode() + randomString.encode()).hexdigest()

        start = conn.recv(len(startString)).decode()
        print(f'[AUTH RECIEVED] Start: {start}')

        if start == startString:
            conn.send(randomString.encode())
            print(f'[AUTH SENT] Random: {randomString}')

            result = conn.recv(40).decode()
            print(f'[AUTH RECIEVED] SHA1: {result}')

            if result == sha1Result:
                message = "Authentication succesful. Do you wish to proceed?"
                conn.send(message.encode())
                print(f'[AUTH SENT] Message: {message}')

                answer = conn.recv(1).decode()
                print(f'[AUTH RECIEVED] Answer: {answer}')

                if answer == "Y":
                    return True
            else:
                message = "Authentication unsuccesful."
                conn.send(message.encode())
                print(f'[AUTH SENT] Message: {message}')

        return False

    
    def sendPacket(self, conn, addr, packet_type):
        if packet_type == 0: #Quesiton
            payload = "Question?".encode()
            payload_size = len(payload)

        elif packet_type == 1: #Time
            payload = str(time.ctime()).encode()
            payload_size = len(payload)

        elif packet_type == 2: #End
            payload = "End".encode()
            payload_size = len(payload)

        header = bytes([packet_type, payload_size])
  
        conn.send(header)
        conn.send(payload)

        print(f'[SENT] Header: {header} - Payload: {payload}')


    def recievePacket(self, conn, addr):
        header = conn.recv(2)
        packet_type = header[0]
        payload = '-empty-'

        if packet_type == 3: #Guess
            payload_size = header[1]
            payload = conn.recv(payload_size).decode()

        print(f'[RECIEVED] Header: {header} - Payload: {payload}')

        if packet_type == 1:
            print(f'[DISCONNECTED] {addr}')
            return False
        else:
            return True



if __name__=="__main__":
    s = ServerSocket('127.0.0.1', 3001)
    s.start()
