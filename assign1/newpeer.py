#!/usr/bin/python3

import socket
import threading
import sys
import csv
import random
import pickle
import time
import logging
from hashlib import sha256
from datetime import datetime
import config
import ast

class Peer:
    def __init__(self, host_name, port,config_file_name):
        """Initialize all the attributes of the peer and start thread for listening and sending messages

        Args:
            host (string): peer ip address
            port (int): peer port number
        """
        self.host = host_name
        self.LISTEN_PORT = port
        self.config_file_name = config_file_name
        self.CHUNK_SIZE = 1024
        self.FORMAT = 'utf-8'
        self.seeders_list = []
        self.seeders_socket_list = []
        self.peers_socket_list = []
        self.PEER_LIST = []
        self.message_list = {}
        self.liveness = {}
        self.parseConfigFile()
        self.connectToSeeders()
        self.connectToPeers()

    def parseConfigFile(self):
        """Function to parse config file and add information about seed in seeder_list
        """
        with open("./config.csv", "r") as csv_file:
            csv_reader = csv.reader(csv_file)
            tmp_seeders = []
            for row in csv_reader:
                tmp_seeders.append(row[0])
        for s in random.sample(tmp_seeders, len(tmp_seeders)//2 + 1):
            self.seeders_list.append(s)

    def connectToSeeders(self):
        """Function to connect with atmost floor(n/2) + 1 seeders and add peers received from
        seed into PEER_LIST
        """
        tmp_peers = set()
        for s in self.seeders_list:
            addr = s.split(":")
            seed = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            print(addr[0]+" "+addr[1])
            seed.connect((addr[0], int(addr[1])))
            seed.send(bytes(str(self.LISTEN_PORT),self.FORMAT))
            self.seeders_socket_list.append(seed)
            output_message = f"Added to the seed {s}"
            self.dump_to_file(output_message)
            print(output_message)
            res = ast.literal_eval(seed.recv(self.CHUNK_SIZE).decode(self.FORMAT)) 
            peers = set(res)
            #print("PEER: "+peers)
            tmp_peers = tmp_peers.union(peers)
        if len(tmp_peers) == 0:
            self.dump_to_file("Empty list Received")
            print("Empty list Received")
        else:
            self.dump_to_file("List of Peers : {tmp_peers}")
            print("List of Peers : {tmp_peers}")
        if len(tmp_peers) <= 4:
            for p in tmp_peers:
                self.PEER_LIST.append(p)
        else:
            for p in random.sample(tmp_peers, 4):
                self.PEER_LIST.append(p)

    def connectToPeers(self):
        """Function to connect with the peers (atmost 4) and start thread to receive message from them.
        """
        print(self.PEER_LIST)
        for addr in self.PEER_LIST:
            tmp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            #print(addr)
            tmp_socket.connect(addr)
            tmp_socket.send(bytes(str(self.LISTEN_PORT),self.FORMAT))
            self.peers_socket_list.append(tmp_socket)
            self.liveness[tmp_socket] = [addr[0], addr[1], 0]
            output_message = f"{datetime.now().timestamp()} : Connected with the peer <{addr[0]}:{addr[1]}>"
            self.dump_to_file(output_message)
            print(output_message)
            thread = threading.Thread(
                target=self.handlePeers, args=(tmp_socket, addr[0], addr[1], ))
            thread.start()

    def handlePeers(self, peer, ip, port):
        """Function to receive messages from peers in separate thread and handle different messages

        Args:
            peer (socket): peer socket info
            ip (string): peer ip address
            port (int): peer port number
        """
        while True:
            try:
                #message = pickle.loads(peer.recv(2048))
                message = peer.recv(self.CHUNK_SIZE).decode(self.FORMAT)
                msg_type, *other = message.split(":")
                if msg_type.strip() == "Liveness Request":
                    message = f"Liveness Reply:{other[0]}:{other[1]}:{other[2]}:{self.host}:{self.LISTEN_PORT}"
                    #peer.send(pickle.dumps(message))
                    peer.send(bytes(message, self.FORMAT))
                    self.liveness[peer][2] = float(other[0])
                elif msg_type.strip() == "Liveness Reply":
                    self.liveness[peer][2] = float(other[0])
                else:
                    message_hash = sha256(
                        message.encode('utf-8')).hexdigest()
                    if message_hash not in self.message_list.keys():
                        self.message_list[message_hash] = True
                        output_message = f"{datetime.now().timestamp()} : {self.host} {message}"
                        self.dump_to_file(output_message)
                        print(output_message)
                        for p in self.peers_socket_list:
                            if p != peer:
                                p.send(bytes(message,self.FORMAT))
            except:
                pass

    def dump_to_file(self,msg):
        filename = './output_peer/output_peer'+str(self.LISTEN_PORT)+'.txt'
        file = open(filename,'a')
        msg = msg+"\n"
        file.write(msg)
        file.close()

    def listen(self):
        """Function to accept new peers and add them to the peer list.
        """
        while True:
            peer, address = self.server.accept()
            #peer_port = pickle.loads(peer.recv(self.CHUNK_SIZE))
            peer_port = int(peer.recv(self.CHUNK_SIZE).decode(self.FORMAT))
            # adding client peer to peer socket list
            self.peers_socket_list.append(peer)
            # adding client peer port and address to PEER_LIST 
            
            if (address[0], peer_port) not in self.PEER_LIST:
                self.PEER_LIST.append((address[0], peer_port))
            output_message = f"{datetime.now().timestamp()} : Connected with the peer <{address[0]}:{peer_port}>"
            #log.debug(output_message)
            self.dump_to_file(str(output_message))
            print(str(output_message))
            self.liveness[peer] = [address[0],
                                   peer_port, datetime.now().timestamp()]
            thread = threading.Thread(
                target=self.handlePeers, args=(peer, address[0], peer_port, ))
            thread.start()

    def sendGossipMessage(self):
        """Send Gossip Message to all the adjacent peers and stop after 10 messages.
        """
        num_of_msg_send = 0
        while num_of_msg_send < 10:
            # <self.timestamp > : < self.IP > : < self.Msg  # >
            message = f"{datetime.now()}:{self.host}:{self.LISTEN_PORT}:Message {num_of_msg_send}"
            message_hash = sha256(message.encode('utf-8')).hexdigest()
            self.message_list[message_hash] = True
            flag = False
            for p in self.peers_socket_list:
                try:
                    p.send(bytes(message,self.FORMAT))
                    flag = True
                except:
                    pass
            num_of_msg_send += 1 if flag else 0
            time.sleep(5)

    def sendLivenessMessage(self):
        """Send Liveness Message to all the adjacent peers and If reply not received for last 3 request 
        then send dead node request to the connected seeders.
        """
        for p in self.peers_socket_list:
            self.liveness[p][2] = datetime.now().timestamp()
        while True:
            current = datetime.now().timestamp()
            for p in self.peers_socket_list:
                try:
                    if int(current - self.liveness[p][2]) < 40:
                        message = f"Liveness Request:{current}: {self.host}:{self.LISTEN_PORT}"
                        p.send(bytes(message,self.FORMAT))
                    else:
                        dead_message = f"Dead Node:{self.liveness[p][0]}:{self.liveness[p][1]}:{current}:{self.host}:{self.LISTEN_PORT}"
                        output_message = f"{datetime.now().timestamp()} : {self.host}:{self.LISTEN_PORT} Reporting Dead Node Message For {self.liveness[p][0]}:{self.liveness[p][1]}>"
                        self.dump_to_file(output_message)
                        print(output_message)
                        for s in self.seeders_socket_list:
                             s.send(bytes(dead_message,self.FORMAT))
                        self.PEER_LIST.remove(
                            (self.liveness[p][0], int(self.liveness[p][1])))
                        self.peers_socket_list.remove(p)
                        del self.liveness[p]
                except:
                    pass
            time.sleep(13)

    def run(self):
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.LISTEN_PORT))
        self.server.listen(5)
        threading.Thread(target=self.listen).start()
        threading.Thread(target=self.sendGossipMessage).start()
        threading.Thread(target=self.sendLivenessMessage).start()

if __name__ == "__main__":
    '''
    read_length = 1024
    log = logging.getLogger()
    log.setLevel(logging.DEBUG)
    log.addHandler(logging.FileHandler(f"outputpeer_{port}.txt"))
    log.addHandler(logging.StreamHandler(sys.stdout))
    lock = threading.Lock()
    Peer(host, port)
    '''
    sections = [ 'TOTAL PEERS','RUNNING PEERS','PEERS LISTEN PORT']
    file_name = 'peers_port.ini'
    sections_keys = ['max_peer','peer_count']
    listen_port = config.get_port_from_config_file(file_name,sections,sections_keys)
    host = '127.0.0.1'
    print(f'[LISTEN PORT]: {listen_port}')
    lock = threading.Lock()
    peer = Peer(host,listen_port,file_name)
    peer.run()
