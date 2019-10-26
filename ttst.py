import socket
import threading
import json
import os
import argparse

class RxServer:
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
        self.messages = list()
        self.wait_message = threading.Lock()
        self.wait_message.acquire()
        self.server_thread = threading.Thread(target=self.listen_loop)

    def __del__(self):
        self.stop()

    def stop(self):
        """ 
        Stop the server by exiting the listen loop and
        closing the server socket
        """
        self.s.close()
        self.running = False
        self.server_thread.join()

    def listen_loop(self):
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
                data = self.recieve_data(conn)
            finally:
                conn.close()
            self.messages.append(json.loads(data))
            self.wait_message.release()

    def start(self):
        self.server_thread.start()

    def pop_message(self):
        """
        Blocks until a message is available and returns the first item
        """
        self.wait_message.acquire()
        self.wait_message.release()
        message = self.messages.pop(0)
        return message

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
    s.connect((host, port))

    try:
        s.sendall(message.encode())
    finally:
        s.close()

def collect_local_lua_scripts():
    """ Get all lua files in the cwd """
    cwd = os.getcwd()
    files = []
    for f in os.listdir(cwd):
        if os.path.isfile(os.path.join(cwd, f)) and f.split('.')[-1] == 'lua':
            files.append(f)
    return files

def build_push_json(files):
    json_array = []
    for f in files:
        json_array.append({
            'name': '.'.join(f.split('.')[0:-1])
        })
    return json_array

def get_scripts():
    try:
        push_message(json.dumps({"messageID": 0}))
    except ConnectionRefusedError:
        print("Unable to connect to instance of table top simulator, is it running?")
        os._exit(1)

    response = server.pop_message()

    for script in response['scriptStates']:
        with open(script['name'] + ".lua", "w") as f:
            f.write(script['script'])

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Table Top Simulator code tool")
    parser.add_argument('action')
    args = parser.parse_args()

    if args.action == 'get':
        server = RxServer()
        server.start()
        get_scripts()
        os._exit(0)
    elif args.action == 'push':
        # TODO
        print('push code to TableTop simulator instance')
        files = collect_local_lua_scripts()
        json = build_push_json(files)
        print(json)
    elif args.action == 'listen':
        server = RxServer()
        server.start()
        print(server.pop_message())
