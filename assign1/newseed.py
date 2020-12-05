import socket
import threading
import random
import time
import config
from datetime import datetime

class Seed:
    def __init__(self, host_name, listen_port,filename):
        self.HOST = host_name
        self.PORT = listen_port
        self.PEER_LIST = []
        self.MESSAGE_LIST = {}
        self.CHUNK_SIZE = 1024
        self.FORMAT = 'utf-8'
        self.config_file_name = filename

    def handlePeers(self, peer):
        while True:
            try:
                message = peer.recv(self.CHUNK_SIZE).decode(self.FORMAT)
                msg_type, *_ = message.split(":")
                if msg_type.strip() == "Dead Node":
                    _, dead_ip, dead_port, time, sender_ip, sender_port = message.split(
                        ":")
                    output_message = f"{datetime.now().timestamp()} : Receiving Dead Node Message For <{dead_ip}:{dead_port}> from <{sender_ip}:{sender_port}> at {time}"
                    self.dump_to_file(output_message)
                    print(output_message)
                    addr = (dead_ip, int(dead_port))
                    if addr in self.PEER_LIST:
                        self.PEER_LIST.remove(addr)
                        self.dump_to_file(
                            f"Removed peer <{dead_ip}:{dead_port}> from peerlist")
                        print(f"Removed peer <{dead_ip}:{dead_port}> from peerlist")    
                    else:
                        self.dump_to_file(
                            f"Peer <{dead_ip}:{dead_port}> not present in peerlist")
                        print(f"Peer <{dead_ip}:{dead_port}> not present in peerlist")
            except:
                peer.close()

    def dump_to_file(self,msg):
        filename = './output_seed/output_seed'+str(self.PORT)+'.txt'
        file = open(filename,'a')
        msg = msg+"\n"
        file.write(msg)
        file.close()

    def listen(self):
        """Function to accept new peers and add them to the peer list.
        """
        while True:
            peer, address = self.server.accept()
            peer_port = int(peer.recv(self.CHUNK_SIZE).decode(self.FORMAT))
            peer.send(bytes(str(self.PEER_LIST),self.FORMAT))
            if (address[0], peer_port) not in self.PEER_LIST:
                self.PEER_LIST.append((address[0], peer_port))
            output_message = f"{datetime.now().timestamp()} : Added <{address[0]}:{peer_port}> to the Peer_list"
            self.dump_to_file(output_message)
            print(output_message)
            thread = threading.Thread(target=self.handlePeers, args=(peer, ))
            thread.start()

    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.HOST, self.PORT))
        self.server.listen(5)
        listen_thread = threading.Thread(target=self.listen)
        listen_thread.start()

if __name__ == "__main__":
    # port number at which seed will listen to for peer connection reqs
    sections = [ 'TOTAL SEED','RUNNING SERVER','SEED LISTEN PORT']
    file_name = 'config.ini'
    sections_keys = ['seed_count','server_count']
    host_name = "127.0.0.1" 
    port = config.get_port_from_config_file(file_name,sections,sections_keys)
    print(f'[LISTEN PORT]: {port}')
    seed = Seed(host_name,port,file_name)
    seed.run()
    
