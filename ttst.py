import socket
import threading
import json
import time

recieved_messages = []

class SafeQueue:
    """ Class wraps a list with a mutex to prevent race conditions """
    def __init__(self, mutex):
        """ Simple constructor creates the queue and assigns the mutex """
        self.mutex = threading.Lock()
        self.wait_lock = threading.Lock()
        self.wait_lock.aquire()
        self.queue = []

    def wait_queue(self):
        self.wait_lock.acquire()
        self.wait_lock.release()

    def push(self, item):
        """ push an item onto the queue"""
        self.mutex.acquire()
        self.queue.append(item)
        self.wait_lock.release()
        self.mutex.release()

    def dequeue(self):
        """
        Protected de-queue, cannot dequeue or queue at the same time
        """
        self.mutex.acquire()
        if len(self.queue) == 1: # If De-queueing results in an empty queue, lock the mutex
            self.wait_lock.acquire()
        value = self.queue.pop(0)
        self.mutex.release()
        return value

class Server:
    """
    TableTop simulator will respond to messages by attempting to send a JSON
    string over port 39998 using basic TCP.
    """
    def __init__(self):
        """ 
        Initialize the server by creating a socket and binding it to
        localhost and port 39998.
        39998 is the expected port that TableTop Simulator will send messages on
        """
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('localhost', 39998))
        self.s.listen(1)
        self.running = True
        self.messages = SafeQueue()

    def __del__(self):
        self.stop()

    def stop(self):
        """ 
        Stop the server by exiting the listen loop and
        closing the server socket
        """
        self.running = False
        self.s.close()

    def start(self):
        """
        Start the listen loop
        Will block until self.stop() is called so this should be run
        in a different thread
        """
        while self.running:
            # conn is the actual socket connection to read from
            # addr is the address we are receiving data from,
            # we don't really care about the address right now
            # but it could be used for logging
            conn, addr = self.s.accept()
            try:
                data = recieve_data(conn)
            finally:
                conn.close()
            self.messages.push(json.loads(data))

    def recieve_data(self, socket_connection):
        """
        Do a buffered read on the socket connection until no more data
        is being sent
        """
        data = b''
        while True:
            b = socket_connection.recv(1024)
            if not b: break
            data += b
        return data
            

def push_message(message):
    """ 
    Push a message to the table top simulator instance
    Tabletop simulator listens on port 39999 and should be on localhost
    """
    port = 39999
    host = 'localhost'

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
    except ConnectionRefusedError:
        print("Could not connect to talbe top simulator on port" + str(port))
        print("Is table top simulator running?")
        exit(1)
    try:
        s.sendall(message.encode())
    finally:
        s.close()

server = Server()
t = threading.Thread(target=server.start)
t.start()

push_message(json.dumps({"messageID": 0}))


#server.stop()
