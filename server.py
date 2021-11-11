import hashlib
import socket
import time
import threading
import string    
import random

startString = "Start_Connection"
privateString = "PRIVATE_KEY_THIRTY_TWO_CHARACTER"

class Game:
    def __init__(self):
        self.points = 0
        self.number = -1
        self.startTime = -1
        self.started = False

    def start(self):
        self.number = random.randint(0,36)
        self.startTime = time.time()
        self.started = True

    def reset(self):
        self.points = 0
        self.number = -1
        self.startTime = -1
        self.started = False

    def remaining(self):
        return 30 - int(time.time() - self.startTime)

    def guess(self, g):
        if g.isdecimal() and int(g) == self.number:
            self.points += 35
        elif g == 'even' and self.number%2==0:
            self.points += 1
        elif g == 'odd' and self.number%2==1:
            self.points += 1
        else:
            self.points -= 1



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

            thread = threading.Thread(target=self.handleClient, args=(conn, addr))
            thread.start()
            print(f'[ACTIVE THREADS] {threading.activeCount()-1}')


    def handleClient(self, conn, addr):
        if self.auth(conn, addr):
            game = Game()
            connected = True
            while connected:                
                # Recieve
                packet_type, payload = self.recievePacket(conn, addr)
                
                if not game.started and packet_type == 0: # Start game
                    self.sendPacket(conn, addr, 0, "What is your guess? Number, even, odd?")
                    game.start()
                    print(f'[GAME STARTED] Number: {game.number}')
                    threading.Thread(target=self.timer, args=(conn, addr, game)).start()  

                elif game.started and packet_type == 1: # Terminate game
                    self.sendPacket(conn, addr, 2, game.points)
                    print(f'[TERMINATE] Points: {game.points}')
                    game.reset()

                elif game.started and packet_type == 2: # Get time
                    remaining = game.remaining()
                    self.sendPacket(conn, addr, 1, remaining)
                    print(f'[TIME] Remaining: {remaining}')

                elif game.started and packet_type == 3: # Guess
                    game.guess(payload)
                    self.sendPacket(conn, addr, 2, game.points)
                    print(f'[GUESS] Number: {game.number} - Guess: {payload} - Points: {game.points}')
                    game.number = random.randint(0,36)

                else:
                    print(f'[ERROR] PacketType: {packet_type} - Payload: {payload}')
                    connected = False

        conn.close()  


    def auth(self, conn, addr):
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
           
        message = "Authentication unsuccesful."
        conn.send(message.encode())
        print(f'[AUTH SENT] {message}')
        return False

    
    def sendPacket(self, conn, addr, packet_type, data):
        if packet_type == 0: # <CharArray>
            payload = data.encode()
        elif packet_type == 1: # <Uint-16>
            payload = data.to_bytes(2, byteorder="big", signed=False) 
        elif packet_type == 2: # <Int-16>
            payload = data.to_bytes(2, byteorder="big", signed=True)

        payload_size = len(payload)
        packet = bytes([packet_type, payload_size])+payload

        conn.send(packet)
        print(f'[SENT] PacketType: {packet_type} - Payload: {payload}')


    def recievePacket(self, conn, addr):
        packet = conn.recv(1024)
        packet_type = packet[0]
        payload_size = packet[1]
        payload = packet[2:2+payload_size]

        print(f'[RECIEVED] PacketType: {packet_type} - Payload: {payload}')
        return (packet_type, payload.decode())


    def timer(self, conn, addr, game):   
        remaining = 30
        while remaining > 3:
            remaining = game.remaining()
            self.sendPacket(conn, addr, 1, remaining)
            print(f'[TIME] Remaining: {remaining}')
            time.sleep(3)  

        self.sendPacket(conn, addr, 2, game.points)
        print(f'[TERMINATE] Points: {game.points}')
        game.reset()


if __name__=="__main__":
    s = ServerSocket('127.0.0.1', 3001)
    s.start()
