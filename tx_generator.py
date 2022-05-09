import base58
import ecdsa
import filelock
import json
import time
from time import sleep
import datetime
import threading
import filelock
import hashlib
import re
import sys
from concurrent.futures import ThreadPoolExecutor
import socket
import os
import pickle
import random
import csv

#Set internal variables
num_of_new_tx = 0
num_of_pending_tx = 0
num_of_blocks = 0
system_stop_point = 10
num_of_tx_to_store = 11
count = 0

#Set system flags
system_start_flag = False
request_OK_flag = False
system_stop_flag = False
node_list = []

iteration_file_name = 'iter2.csv'
with open(iteration_file_name) as f:
    a = list(csv.reader(f))
n = int(a[-1][0])
b = [n+1]
with open(iteration_file_name, 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(b)

DIR = "./files" + str(n) + "/"
try:
    os.mkdir(DIR)
except:
    pass

key_file_name1 = DIR + "key.lock"
key_file_name2 = DIR + "key.txt"
trans_id_file_name1 = DIR + "trans_id.lock"
trans_id_file_name2 = DIR + "trans_id.txt"
peer_list_file_name1 = DIR + 'peer_list.lock'
peer_list_file_name2 = DIR + 'peer_list.txt'

    
def start_test_chain_system():
    print("Start tx generator....")
    p2p_start()
    set_parameters()
    
    #トランザクションの生成のみを行う
    generate_tx_ = threading.Thread(target=generate_tx_manager)
    generate_tx_.start()
    
    sleep(10)
    #Request.main(1)

def set_parameters():
    global system_start_flag
    global request_OK_flag
    global peer_list_file_name1
    global peer_list_file_name2
    
    print("Setting up transaction generator...")
    
    with filelock.FileLock('peer_list.lock',timeout=10):
        try:
            with open('peer_list.txt','r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []
                        
    for peer in peer_list:
        if peer != ID:
            #build_message(1,ID,addr_,port_,host,port,0,0,0,0,0,0)
            try:
                build_message(1,ID,peer_list[peer]['IP address'],peer_list[peer]['Port'],host,port,0,0,0,0,0,0,0)
            except:
                build_message(1,ID,peer_list[peer]['IP address'],peer_list[peer]['Port']+1,host,port,0,0,0,0,0,0,0)

    send_system_start_signal()
    print("Start system")
        
def generate_key():
    global key_file_name1
    global key_file_name2
    
    private_key = ecdsa.SigningKey.generate(curve=ecdsa.SECP256k1)
    public_key = private_key.get_verifying_key()

    private_key = private_key.to_string()
    public_key = public_key.to_string()

    private_b58 = base58.b58encode(private_key).decode('ascii')
    public_b58 = base58.b58encode(public_key).decode('ascii')
    

    with filelock.FileLock(key_file_name1, timeout=10):
        try:
            with open(key_file_name2, 'r') as file:
                key_list = json.load(file)
        except:
            key_list = []

        key_list.append({
            'private': private_b58,
            'public' : public_b58
        })

        with open(key_file_name2, 'w') as file:
            json.dump(key_list, file, indent=2)
    return public_b58, private_b58

def generate_tx_manager():
    global num_of_new_tx
    global num_of_pending_tx
    global num_of_blocks
    global mining_flag
    global system_stop_flag
    
    while True:
        sleep(random.randint(0,5))
        generate_tx()
        num_of_new_tx += 1
        if system_stop_flag == True:
            exit()
            
def generate_tx():
    global key_file_name1
    global key_file_name2
    global trans_file_name1
    global trans_file_name2
    global pending_tx

    generate_key()
    
    with open('data.txt','r') as file:
        data = file.read()

    with filelock.FileLock(key_file_name1,timeout=10):
        try:
            with open(key_file_name2,'r') as file:
                key_list = json.load(file)
        except:
            key_list = []

    time = str(datetime.datetime.now()).encode()
    pub_key = base58.b58decode(key_list[0]['public'])
    pri_key = base58.b58decode(key_list[0]['private'])
    
    sha = hashlib.sha256()
    sha.update(pub_key)
    sha.update(time)
    sha.update(data.encode())
    hash = sha.digest()

    key = ecdsa.SigningKey.from_string(pri_key, curve=ecdsa.SECP256k1)
    sig = key.sign(hash)

    with filelock.FileLock(trans_id_file_name1,timeout=10):
        try:
            with open(trans_id_file_name2,'r') as file:
                tx_list = json.load(file)
        except:
            tx_list = []
            
    tx_list.append({
        'TxID': hash.hex(),
        'time':time.decode(),
        'publisher': pub_key.hex(),
        'data': data,
        'sig': sig.hex()
    })
    with filelock.FileLock(trans_id_file_name1,timeout=10):
        with open(trans_id_file_name2,'w') as file:
            json.dump(tx_list,file,indent=2) 

    share_tx(tx_list[-1],hash.hex())

def share_tx(tx,TxID):
    global peer_list_file_name1
    global peer_list_file_name2
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []
                        
    for peer in peer_list:
        if peer != ID:
            build_message("a",ID,peer_list[peer]['IP address'],peer_list[peer]['Port'],host,port,TxID,"new tx",tx["time"],tx["data"],tx["sig"],tx["publisher"],0)
            
def build_message(msg_type,ID,addr_to,port_to,my_addr,my_port,sp1,sp2,sp3,sp4,sp5,sp6,sp7):
    message = {'msg_type':msg_type,
               'ID':ID,
               'addr':my_addr,
               'port':my_port,
               'sp1':sp1,
               'sp2':sp2,
               'sp3':sp3,
               'sp4':sp4,
               'sp5':sp5,
               'sp6':sp6,
               'sp7':sp7}
    message = json.dumps(message)
    my_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    my_socket.connect((addr_to,port_to))
    my_socket.sendall(message.encode('utf-8'))
        
def p2p_start():
    global host
    global port
    global ID
    global my_socket
    host = get_myip()
    my_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    ID = "N0000"
    port = port_set()
    initialize_peer_list(ID,host,port)
    show_my_info()
    
    #他のノードからのリクエストを常に待機する
    accepting_request = threading.Thread(target=pending)
    accepting_request.setDaemon(True)
    accepting_request.start()
    
    #20秒置きにpeerの生存確認を行う
    #conn_confirmation = threading.Thread(target=connection_confirmation)
    #conn_confirmation.setDaemon(True)
    #conn_confirmation.start()

def port_check(port):
    try:
        my_socket.bind((host,port))
        return 1
    except:    
        return 0
        
def port_set():
    port = 50030
    while True:
        if port_check(port) == 1:
            return port
        else:
            port += 1
            
def get_myip():
    s = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    s.connect(('8.8.8.8',80))
    return s.getsockname()[0]

def pending():
    global system_stop_flag
    my_socket.listen(10)
    while True:
        conn, addr = my_socket.accept()
        handle_message(conn)
        if system_stop_flag == True:
            exit()
        
def initialize_peer_list(ID,host,port):
    global peer_list_file_name1
    global peer_list_file_name2

    my_info = {
              ID:{
                    "time":time.ctime(),
                    "IP address":host,
                    "Port":port}
              }
    
    with filelock.FileLock('peer_list.lock',timeout=10):
        try:
            with open('peer_list.txt','r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []
    peer_list.update(my_info)

    with filelock.FileLock(peer_list_file_name1,timeout=10):           
        with open(peer_list_file_name2,'w') as file:
            json.dump(peer_list,file,indent=2)    

def show_my_info():
    print("Your address is :",host)
    print("Your port is :",port)
    print("Your ID is:",ID)
    
def handle_message(message):
    global host
    global port
    global node_list
    global system_start_flag
    global request_OK_flag
    global num_of_blocks
    global num_of_new_tx
    global count
    
    conn = message
    msg = conn.recv(4096)

    msg = json.loads(msg)
    msg_type = msg['msg_type']
    peer_ID = msg['ID']
    peer_addr = msg['addr']
    peer_port = msg['port']
    
    if msg_type == 0:
        request_OK_flag = True
        print("peer",peer_ID,"OK.")
        share_node_list(peer_addr,peer_port,peer_ID)
        add_core_node(peer_addr,peer_port,peer_ID)
    elif msg_type == 1:  
        print("Request for connection was called.")
        add_core_node(peer_addr,peer_port,peer_ID)
        build_message(0,ID,peer_addr,peer_port,host,port,0,0,0,0,0,0,0)
    elif msg_type == 2:
        renew_core_list(msg["sp1"])
    elif msg_type == 3:
        living_confirmation(peer_addr,peer_port)
    elif msg_type == 4:
        node_list.append(peer_ID)
    elif msg_type == 6:
        send_core_node_list(peer_addr,peer_port)
    elif msg_type == 7:
        #print("living confirmation recieved")
        living_confirmation(peer_addr,peer_port)
    elif msg_type == 8:
        #print("living confirmation recieved2")
        node_list.append(peer_ID)
    elif msg_type == 10:
        system_start_flag = True
    elif msg_type == 11:
        print("New peer added.")
        add_core_node(msg["sp1"],msg["sp2"],msg["sp3"])
    elif msg_type == 100:
        count += 1
        if count == 3:
            exit()
    elif msg_type == 'a':
        tx = {"TxID":msg["sp1"],
              "time":msg["sp3"],
              "publisher":msg["sp6"],
              "data":msg["sp4"],
              "sig":msg["sp5"]}
        verify(msg["sp1"],tx)
    elif msg_type == 'b':
        num_of_blocks += 1
        num_of_new_tx -= len(msg['sp5'])

def living_confirmation(peer_addr,peer_port):
    build_message(8,ID,peer_addr,peer_port,host,port,0,0,0,0,0,0,0)
        
def connection_confirmation():
    global node_list
    global ID
    global host
    global port
    global peer_list_file_name1
    global peer_list_file_name2
    global system_stop_flag
    
    while True:
        if system_stop_flag == True:
            exit()
        sleep(30)
        node_list = []
        #print("Start connection confirmation...")
        peer_list = []
        remove_list = []
        is_change = False
        with filelock.FileLock(peer_list_file_name1,timeout=5):
            try:
                with open(peer_list_file_name2,'r') as file:
                    peer_list = json.load(file)
            except:
                peer_list = []

        for peer in peer_list:
            if peer != ID:
                try:
                    build_message(7,ID,peer_list[peer]['IP address'],peer_list[peer]['Port'],host,port,0,0,0,0,0,0,0)
                except:
                    pass
        sleep(30)
        node_list.append(ID)
        
        for peer in peer_list:
            if peer in node_list:
                continue
            else:
                remove_list.append(peer)
                print("peer ",peer," was disconnected.")
                is_change = True
                
        if is_change:
            print("There was a chenge in network topology.")
            remove_node(remove_list)
    
def add_core_node(peer_addr,peer_port,peer_ID):
    global peer_list_file_name1
    global peer_list_file_name2
    add_info = {
        peer_ID:{
                "time":time.ctime(),
                "IP address":peer_addr,
                "Port":peer_port}
            }
    
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []
        peer_list.update(add_info)
           
        with open(peer_list_file_name2,'w') as file:
            json.dump(peer_list,file,indent=2)    
    
def share_node_list(new_addr,new_port,new_ID):
    global peer_list_file_name1
    global peer_list_file_name2
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []

    for peer in peer_list:
        if peer != new_ID and peer != ID:
            build_message(11,ID,peer_list[peer]['IP address'],peer_list[peer]['Port'],host,port,new_addr,new_port,new_ID,0,0,0,0)
        if peer != ID:
            build_message(11,ID,new_addr,new_port,host,port,peer_list[peer]["IP address"],peer_list[peer]['Port'],peer,0,0,0,0)
        
def send_system_start_signal():
    global peer_list_file_name1
    global peer_list_file_name2
    
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []
                        
    for peer in peer_list:
        if peer != ID:
            build_message(10,ID,peer_list[peer]['IP address'],peer_list[peer]['Port'],host,port,0,0,0,0,0,0,0)
            
def remove_node(remove_list):
    global peer_list_file_name1
    global peer_list_file_name2
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []
                    
    for peer in remove_list:
        peer_list.pop(peer)
    with filelock.FileLock(peer_list_file_name1,timeout=10):    
        with open(peer_list_file_name2,'w') as file:
            json.dump(peer_list,file,indent=2)
        
def renew_core_list(new_peer_list):
    global peer_list_file_name1
    global peer_list_file_name2
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'r') as file:
                peer_list = json.load(file)
        except:
            exit()
        peer_list.update(new_peer_list)
    with filelock.FileLock(peer_list_file_name1,timeout=10):        
        with open(peer_list_file_name2,'w') as file:
            json.dump(peer_list,file,indent=2)
start_test_chain_system()
