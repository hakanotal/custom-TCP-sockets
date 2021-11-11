import hashlib
import socket
import time
import threading
import string    

startString = "Start_Connection"
privateString = "PRIVATE_KEY_THIRTY_TWO_CHARACTER"


class ClientSocket:
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        

    def start(self):
        self.socket.connect((self.HOST, self.PORT))
        print(f'[CONNECTING] {self.HOST}:{self.PORT}')

        if self.auth():
            threading.Thread(target=self.handleServer).start()
            self.sendPacket(0)
            time.sleep(2)
            self.sendPacket(3, '32')
            time.sleep(2)
            self.sendPacket(2)
                
    
    def handleServer(self):
        connected = True
        while connected:
            packet_type, payload = self.recievePacket()
            if packet_type == 0: # Question
                print(f'[QUESTION] {payload}')
            elif packet_type == 1: # Remaining time
                print(f'[TIME] Remaining: {payload}')
            elif packet_type == 2: # End game
                print(f'[POINTS] Points: {payload}')


    def auth(self):
        self.socket.send(startString.encode())
        print(f'[AUTH SENT] Start: {startString}')

        randomString = self.socket.recv(32).decode()
        print(f'[AUTH RECIEVED] Random: {randomString}')

        sha1Result = hashlib.sha1(privateString.encode() + randomString.encode()).hexdigest()
        self.socket.send(sha1Result.encode())
        print(f'[AUTH SENT] SHA1: {sha1Result}')

        message = self.socket.recv(256).decode()
        print(f'[AUTH RECIEVED] {message}')

        if message == "Authentication unsuccesful.":
            return False

        answer = input(message+" ")
        self.socket.send(answer.encode())
        print(f'[AUTH SENT] Answer: {answer}')

        return True

    
    def sendPacket(self, packet_type, data=''):
        payload = data.encode() # <CharArray>
        payload_size = len(payload)
        packet = bytes([packet_type, payload_size])+payload
  
        self.socket.send(packet)
        print(f'[SENT] PacketType: {packet_type} - Payload: {payload}')
    

    def recievePacket(self):
        packet = self.socket.recv(1024)
        packet_type = packet[0]
        payload_size = packet[1]

        if packet_type == 0: # <CharArray>
            payload = packet[2:2+payload_size].decode()
        elif packet_type == 1: # <Uint-16>
            payload = int.from_bytes(packet[2:2+payload_size], byteorder='big', signed=False)
        elif packet_type == 2: # <Int-16>
            payload = int.from_bytes(packet[2:2+payload_size], byteorder='big', signed=True)

        print(f'[RECIEVED] PacketType: {packet_type} - Payload: {packet[2:2+payload_size]}')
        return (packet_type, payload)



'''
    Example
        packet_type :   3  <Uint8>
        payload_size :  4  <Uint8>
        payload :       even <Char array>
        
        packet :        b'\x03\x02even'
'''


if __name__=="__main__":
    c = ClientSocket('localhost', 3001)
    c.start()