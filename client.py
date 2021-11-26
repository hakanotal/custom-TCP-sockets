import hashlib
import socket
import threading
import os


startString = "Start_Connection"
privateString = "PRIVATE_STR_THIRTY_TWO_CHARACTER"


clear = lambda : os.system('cls' if os.name == 'nt' else 'clear')

class Game:
    def __init__(self, client):
        self.started = False
        self.time = 30
        self.client = client
        self.choice = -1
        self.gotPoints = False
        self.points = 0
        self.question = ''
    
    def printMenu(self):
        clear()
        print("***** Number Guessing Game *****")
        if not self.started:
            if self.gotPoints:
                print(f'\nGame finished. You got {self.points} points!')
            print('\n0. Start game\nq. Close connection\nEnter your choice:')
        else:
            print(f'\nRemaining time : {self.time}\n\n1. Terminate game\n2. Get time\n3. Make a guess\nEnter your choice:')

    def takeInput(self):
        inp = input()
        if inp == 'q':
            self.client.close()
            return
        
        self.choice = int(inp)
        if self.choice not in [0,1,2,3]:
            print("Invalid choice.")
        elif self.choice == 3:
            guess = input(self.question)
            if self.started:
                self.client.sendPacket(self.choice, guess)
                self.printMenu()
        else:
            self.client.sendPacket(self.choice)

        self.choice = -1


class ClientSocket:
    def __init__(self, HOST, PORT):
        self.HOST = HOST
        self.PORT = PORT
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        
    def start(self):
        self.socket.connect((self.HOST, self.PORT))
        print(f'[CONNECTING] {self.HOST}:{self.PORT}')
        self.connected = True

        if self.auth():
            game = Game(self)
            threading.Thread(target=self.handleServer, args=(game,)).start()
            #self.sendPacket(0)
            game.printMenu()
            while self.connected:
                game.takeInput()
                     
    def handleServer(self, game):
        while self.connected:
            packet_type, payload = self.recievePacket()
            if packet_type == 0: # Question
                #print(f'[STARTED] {payload}')
                game.started = True
                game.gotPoints = False
                game.question = payload
            elif packet_type == 1: # Remaining time
                #print(f'[TIME] Remaining: {payload}')
                game.time = payload
            elif packet_type == 2: # End game
                #print(f'[ENDED] Points: {payload}')
                game.started = False
                game.choice = -1
                game.gotPoints = True
                game.points = payload
            
            if game.choice != 3:
                game.printMenu()

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

        answer = input("[MESSAGE] "+message+" ")
        self.socket.send(answer.encode())
        print(f'[AUTH SENT] Answer: {answer}')

        if answer == 'Y':
            return True
        else:
            return False
    
    def sendPacket(self, packet_type, data=''):
        payload = data.encode() # <CharArray>
        payload_size = len(payload)
        packet = bytes([packet_type, payload_size])+payload
  
        self.socket.send(packet)
        #print(f'[SENT] PacketType: {packet_type} - Payload: {payload}')
    
    def recievePacket(self):
        try:
            packet = self.socket.recv(1024)
        except:
            print("[CLOSED] Connection closed")
            return (-1,-1)

        packet_type = packet[0]
        payload_size = packet[1]

        if packet_type == 0: # <CharArray>
            payload = packet[2:2+payload_size].decode()
        elif packet_type == 1: # <Uint-16>
            payload = int.from_bytes(packet[2:2+payload_size], byteorder='big', signed=False)
        elif packet_type == 2: # <Int-16>
            payload = int.from_bytes(packet[2:2+payload_size], byteorder='big', signed=True)
        else:
            print(f'[ERROR] PacketType: {packet_type}')
            return (-1,-1)

        #print(f'[RECIEVED] PacketType: {packet_type} - Payload: {packet[2:2+payload_size]}')
        return (packet_type, payload)

    def close(self):
        self.connected = False
        self.socket.close()


'''
    Example
        packet_type :   3  <Uint8>
        payload_size :  4  <Uint8>
        payload :       'even' <Char array>
        
        packet :        b'\x03\x02even'
'''


if __name__=="__main__":
    c = ClientSocket('localhost', 3001)
    c.start()