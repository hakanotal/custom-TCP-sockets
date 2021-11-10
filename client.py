import hashlib
import socket
import time
import threading
import string    


class ClientSocket:
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        

    def start(self):
        self.socket.connect((self.HOST, self.PORT))
        print(f'[CONNECTING] {self.HOST}:{self.PORT}')

        if self.auth():
            connected = True
            while connected:
                self.recievePacket()
                time.sleep(3)
                self.sendPacket(1)
                connected = False
    

    def auth(self):
        startString = "Start_Connection"
        privateString = "PRIVATE_KEY_THIRTY_TWO_CHARACTER"

        self.socket.send(startString.encode())
        print(f'[AUTH SENT] Start: {startString}')

        randomString = self.socket.recv(32).decode()
        print(f'[AUTH RECIEVED] Random: {randomString}')

        sha1Result = hashlib.sha1(privateString.encode() + randomString.encode()).hexdigest()
        self.socket.send(sha1Result.encode())
        print(f'[AUTH SENT] SHA1: {sha1Result}')

        message = self.socket.recv(256).decode()
        print(f'[AUTH RECIEVED] Message: {message}')

        if message == "Authentication unsuccesful.":
            return False

        answer = input(message)
        self.socket.send(answer.encode())
        print(f'[AUTH SENT] Answer: {answer}')

        return True


    def sendPacket(self, packet_type):
        payload = '-empty-'
        payload_size = 0

        if packet_type == 3: #Guess
            payload = str(input("Guess number between [0-36]: ")).encode()
            payload_size = len(payload)

        header = bytes([packet_type, payload_size])
  
        self.socket.send(header)
        if packet_type == 3:
            self.socket.send(payload)
        print(f'[SENT] Header: {header} - Payload: {payload}')

        if packet_type == 1:
            print(f'[DISCONNECTING]')
    

    def recievePacket(self):
        header = self.socket.recv(2)
        packet_type = header[0]
        payload_size = header[1]
        payload = self.socket.recv(payload_size)

        print(f'[RECIEVED] Header: {header} - Payload: {payload}')


if __name__=="__main__":
    c = ClientSocket('localhost', 3001)
    c.start()