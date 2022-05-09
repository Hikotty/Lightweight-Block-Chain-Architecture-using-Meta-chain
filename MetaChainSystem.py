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

iteration_file_name = 'iter.csv'
with open(iteration_file_name) as f:
    a = list(csv.reader(f))
n = int(a[-1][0])
b = [n+1]
with open(iteration_file_name, 'a', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(b)

DIR = 'files' + str(n) + '/'
os.mkdir(DIR)

#Set file names
key_file_name1 = DIR + "key.lock"
key_file_name2 = DIR + "key.txt"
trans_file_name1 = DIR + "trans.lock"
trans_file_name2 = DIR + "trans.txt"
block_file_name1 = DIR + "block.lock"
block_file_name2 = DIR + "block.txt"
pending_trans_file_name1 = DIR + 'pending_trans.lock'
pending_trans_file_name2 = DIR + 'pending_trans.txt'
meta_chain_file_name1 = DIR + "MetaChain.lock"
meta_chain_file_name2 = DIR + "MetaChain.txt"
peer_list_file_name1 = DIR + 'peer_list.lock'
peer_list_file_name2 = DIR + 'peer_list.txt'

#System parameters
k = 4
system_stop_point = 25
num_of_tx_to_store = 20
num_of_node = 4

#Internal variables
num_of_new_tx = 0
num_of_pending_tx = 0
num_of_blocks = 0

#Internal flags
mining_exit_flag = False
mining_flag = False
pending_tx = True
system_start_flag = False
pending_tx = False
request_OK_flag = False
system_stop_flag = False
node_list = []

#Tx generator info
tx_generator_ip = ''
tx_generator_port = ''

#Reqester info
reqester_ip = ''
reqester_port = 0

def start_test_chain_system():
    global system_start_flag
    global request_OK_flag
    
    print("Waiting for setting up tx generator....")
    p2p_start()
    while True:
        sleep(1)
        if system_start_flag == True:
            print("Start system")
            sleep(15)
            break

    mining_manager()

def generate_tx_manager():
    global num_of_new_tx
    global num_of_pending_tx
    global mining_flag
    global system_stop_flag
    
    while True:
        if mining_flag == True:
            sleep(random.randint(30,60))
            generate_tx()
            num_of_pending_tx += 1
            print("I made ",num_of_pending_tx,"th pending tx.")
        elif mining_flag == False:
            sleep(random.randint(1,10))
            generate_tx()
            num_of_new_tx += 1
            print("I made ",num_of_new_tx,"th tx.")
            
        if system_stop_flag == True:
            exit()
        
def generate_tx():
    global key_file_name1
    global key_file_name2
    global trans_file_name1
    global trans_file_name2
    global pending_trans_file_name1
    global pending_trans_file_name2
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
    
    if pending_tx == True:
        with filelock.FileLock(pending_trans_file_name1, timeout=10):
            try:
                with open(pending_trans_file_name2, 'r') as file:
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
        with filelock.FileLock(pending_trans_file_name1, timeout=10):
            with open(pending_trans_file_name2, 'w') as file:
                json.dump(tx_list, file, indent=2)
        share_tx(tx_list[-1],hash.hex())
    else:
        with filelock.FileLock(trans_file_name1, timeout=10):
            try:
                with open(trans_file_name2, 'r') as file:
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
        with filelock.FileLock(trans_file_name1, timeout=10):
            with open(trans_file_name2, 'w') as file:
                json.dump(tx_list, file, indent=2)
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

def verify_block(block):
    sha = hashlib.sha256()
    sha.update(bytes(block['nonce']))
    sha.update(bytes.fromhex(block['previous_hash']))
    sha.update(bytes.fromhex(block['tx_hash']))
    hash = sha.digest()
    
    if hash.hex() == block['hash']:
        return True
    else:
        return False

def add_block(block,tx_id_list,block_maker_ID):
    global num_of_new_tx
    global num_of_blocks
    global system_stop_point
    global mining_exit_flag
    global pending_tx
    global block_file_name1
    global block_file_name2
    global trans_file_name1
    global trans_file_name2
    global tx_generator_ip
    global tx_generator_port
    global reqester_ip
    global reqester_port
    process_pending_tx()
    if verify_block(block) == True and randomize() == True:
        add_block_in_hashchain(block)
        with filelock.FileLock(block_file_name1, timeout=10):
            try:
                with open(block_file_name2, 'r') as file:
                    block_list = json.load(file)
            except:
                block_list = []

        with filelock.FileLock(trans_file_name1, timeout=10):
            try:
                with open(trans_file_name2, 'r') as file:
                    file_tx_list = json.load(file)
            except:
                file_tx_list = []

        unprosessed_tx_list = []
        tx_list = []
        #省略ID
        file_tx_id_list = []
        lost_tx_list = []

        for tx in file_tx_list:
            if tx['TxID'][:10] in tx_id_list:
                tx_list.append(tx)
                file_tx_id_list.append(tx['TxID'][:10])
            else:
                unprosessed_tx_list.append(tx)
        
        if int(block['size']) != len(tx_list):
            print("\nLost tx occured\n")
            for TxID in tx_id_list:
                if TxID not in file_tx_id_list:
                    print("\nRequesting lost tx")
                    print(TxID)
                    require_lost_tx(TxID,block_maker_ID)
                    
        block["tx"] = tx_list
        block_list.append(block)
            
        with filelock.FileLock(block_file_name1,timeout=10):
            with open(block_file_name2, 'w') as file:
                json.dump(block_list, file, indent=2)

        with filelock.FileLock(trans_file_name1,timeout=10):
            with open(trans_file_name2,"w") as file:
                json.dump(unprosessed_tx_list,file,indent=2)

        num_of_new_tx = len(unprosessed_tx_list)
        num_of_blocks += 1
        print(num_of_blocks,"th block has made.")
        mining_exit_flag = False
    else:
        add_block_in_hashchain(block)
        #with filelock.FileLock(block_file_name1, timeout=10):
        #    try:
        #        with open(block_file_name2, 'r') as file:
        #            block_list = json.load(file)
        #    except:
        #        block_list = []

        with filelock.FileLock(trans_file_name1, timeout=10):
            try:
                with open(trans_file_name2, 'r') as file:
                    file_tx_list = json.load(file)
            except:
                file_tx_list = []

        unprosessed_tx_list = []
        tx_list = []
        #省略ID
        file_tx_id_list = []
        lost_tx_list = []

        for tx in file_tx_list:
            if tx['TxID'][:10] in tx_id_list:
                tx_list.append(tx)
                file_tx_id_list.append(tx['TxID'][:10])
            else:
                unprosessed_tx_list.append(tx)
        
        if int(block['size']) > len(tx_list):
            print("\nLost tx occured\n")
            for TxID in tx_id_list:
                if TxID not in file_tx_id_list:
                    print("\nRequesting lost tx")
                    print(TxID)
                    require_lost_tx(TxID,block_maker_ID)
                    
        #block["tx"] = tx_list
        #block_list.append(block)
            
        #with filelock.FileLock(block_file_name1,timeout=10):
        #    with open(block_file_name2, 'w') as file:
        #        json.dump(block_list, file, indent=2)

        with filelock.FileLock(trans_file_name1,timeout=10):
            with open(trans_file_name2,"w") as file:
                json.dump(unprosessed_tx_list,file,indent=2)

        num_of_new_tx = len(unprosessed_tx_list)
        num_of_blocks += 1
        print(num_of_blocks,"th block has made.")
        mining_exit_flag = False
        
    if num_of_blocks == system_stop_point:
        print("Number of block has reached system to stop value.")
        build_message(100,ID,tx_generator_ip,tx_generator_port,host,port,0,0,0,0,0,0,0)
        build_message(100,ID,reqester_ip,reqester_port,host,port,0,0,0,0,0,0,0)
        exit()

def require_lost_tx(TxID,block_maker_ID):
    global peer_list_file_name1
    global peer_list_file_name2
    global ID
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []
    #print("Sending Request of lost tx")
    for peer in peer_list:
        if ID != peer:
            build_message("d",ID,peer_list[peer]['IP address'],peer_list[peer]['Port'],host,port,TxID,0,0,0,0,0,0)
    
def reply_lost_tx(TxID,reqester_ID):
    global block_file_name1
    global block_file_name2
    global peer_list_file_name1
    global peer_list_file_name2
    global ID
    
    with filelock.FileLock(block_file_name1, timeout=10):
        try:
            with open(block_file_name2, 'r') as file:
                block_list = json.load(file)
        except:
            block_list = []
            
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []     
            
    for block in block_list:
        for tx in block['tx']:
            height = block['height']
            if TxID == tx['TxID'][:10]:
                print("Replying lost tx")
                print(reqester_ID,peer_list[reqester_ID]['IP address'],peer_list[reqester_ID]['Port'])
                build_message('e',ID,peer_list[reqester_ID]['IP address'],peer_list[reqester_ID]['Port'],host,port,tx['TxID'],"new tx",tx["time"],tx["data"],tx["sig"],tx["publisher"],height)
                break

def process_lost_tx(tx,height):
    global block_file_name1
    global block_file_name2
    global trans_file_name1
    global trans_file_name2
    
    with filelock.FileLock(block_file_name1, timeout=10):
        try:
            with open(block_file_name2, 'r') as file:
                block_list = json.load(file)
        except:
            block_list = []
            
    with filelock.FileLock(trans_file_name1, timeout=10):
        try:
            with open(trans_file_name2, 'r') as file:
                file_tx_list = json.load(file)
        except:
            file_tx_list = []
            
    tx_list = []
    for tx_ in file_tx_list:
        if tx['TxID'] != tx_['TxID']:
            tx_list.append(tx_)
            
    for block in block_list:
        if block['height'] == height:
            if tx not in block['tx']:
                block['tx'].append(tx)
        elif block['height'] > height:
            break
            
    with filelock.FileLock(block_file_name1,timeout=10):
        with open(block_file_name2, 'w') as file:
            json.dump(block_list, file, indent=2)

    with filelock.FileLock(trans_file_name1,timeout=10):
        with open(trans_file_name2,"w") as file:
            json.dump(tx_list,file,indent=2)
            
def randomize():
    global k
    global num_of_node
    global ID
    
    seed = 13
    random.seed(seed+time.time())
    #print(seed)
    
    if k >= random.randint(1,num_of_node):
        print("I saved the block.")
        return True
    else:
        False

def add_block_in_hashchain(block):
    global meta_chain_file_name1
    global meta_chain_file_name2
    
    with filelock.FileLock(meta_chain_file_name1, timeout=10):
        try:
            with open(meta_chain_file_name2, 'r') as file:
                meta_block_list = json.load(file)
        except:
            meta_block_list = []
    
    meta_block_list.append({
        'hash' : block['hash'],
        'timestamp':block['timestamp']
    })
    
    with filelock.FileLock(meta_chain_file_name1,timeout=10):
        with open(meta_chain_file_name2, 'w') as file:
            json.dump(meta_block_list, file, indent=2)

def verify(new_tx_id,new_tx):
    global mining_flag
    global pending_tx
    global num_of_new_tx
    global num_of_pending_tx
    global num_of_tx_to_store
    global trans_file_name1
    global trans_file_name2
    global pending_trans_file_name1
    global pending_trans_file_name2
    
    if mining_flag == True:
        verify_pending_tx(new_tx)
    elif mining_flag == False:
        with filelock.FileLock(trans_file_name1, timeout=10):
            try:
                with open(trans_file_name2, 'r') as file:
                    file_tx_list = json.load(file)
            except:
                file_tx_list = []
        tx_publisher = bytes.fromhex(new_tx['publisher'])
        time = new_tx['time']
        data = new_tx['data']
        tx_sig = bytes.fromhex(new_tx['sig'])

        sha = hashlib.sha256()
        sha.update(tx_publisher)
        sha.update(time.encode())
        sha.update(data.encode())
        hash = sha.digest()
        key = ecdsa.VerifyingKey.from_string(tx_publisher, curve=ecdsa.SECP256k1)
        if key.verify(tx_sig, hash) == True:
            file_tx_list.append(new_tx)
            
        with filelock.FileLock(trans_file_name1, timeout=10):
            with open(trans_file_name2,"w") as file:
                json.dump(file_tx_list, file, indent=2)
        num_of_new_tx += 1
        
        print("Peer made ",num_of_new_tx,"th tx.")

def process_pending_tx():
    global pending_tx
    global num_of_new_tx
    global num_of_pending_tx
    global pending_trans_file_name1
    global pending_trans_file_name2
    global trans_file_name1
    global trans_file_name2
    
    with filelock.FileLock(trans_file_name1, timeout=10):
        try:
            with open(trans_file_name2, 'r') as file:
                file_tx_list = json.load(file)
        except:
            file_tx_list = []
            
    with filelock.FileLock(pending_trans_file_name1, timeout=10):
        try:
            with open(pending_trans_file_name2, 'r') as file:
                file_pending_tx_list = json.load(file)
        except:
            file_pending_tx_list = []
            
    for tx in file_pending_tx_list:
        file_tx_list.append(tx)
        
    with filelock.FileLock(trans_file_name1, timeout=10):
        with open(trans_file_name2,"w") as file:
            json.dump(file_tx_list, file, indent=2)

    with filelock.FileLock(pending_trans_file_name1, timeout=10):
        with open(pending_trans_file_name2,"w") as file:
            json.dump([], file, indent=2)
            
    pending_tx = False
    num_of_new_tx += num_of_pending_tx
    print(num_of_pending_tx,"Pending tx has processed.")
    num_of_pending_tx = 0
    
def verify_pending_tx(new_tx):
    global pending_tx
    global num_of_pending_tx
    global pending_trans_file_name1
    global pending_trans_file_name2
    
    with filelock.FileLock(pending_trans_file_name1, timeout=10):
        try:
            with open(pending_trans_file_name2, 'r') as file:
                file_tx_list = json.load(file)
        except:
            file_tx_list = []
                    
    tx_publisher = bytes.fromhex(new_tx['publisher'])
    time = new_tx['time']
    data = new_tx['data']
    tx_sig = bytes.fromhex(new_tx['sig'])

    sha = hashlib.sha256()
    sha.update(tx_publisher)
    sha.update(time.encode())
    sha.update(data.encode())
    hash = sha.digest()

    key = ecdsa.VerifyingKey.from_string(tx_publisher, curve=ecdsa.SECP256k1)
    if key.verify(tx_sig, hash) == True:
        file_tx_list.append(new_tx)

    with filelock.FileLock(pending_trans_file_name1,timeout=10):
        with open(pending_trans_file_name2, 'w') as file:
            file_tx_list = json.dump(file_tx_list,file,indent=2)
    pending_tx = True                    
    num_of_pending_tx += 1
    print("Peer made ",num_of_pending_tx,"th pending tx.")

def mining():
    global mining_flag
    global mining_exit_flag
    global pending_tx
    global num_of_blocks
    global system_stop_point
    global num_of_new_tx
    global block_file_name1
    global block_file_name2
    global trans_file_name1
    global trans_file_name2
    global tx_generator_ip
    global tx_generator_port
    global reqester_ip
    global reqester_port
    global meta_chain_file_name1
    global meta_chain_file_name2
    global num_of_pending_tx
    
    process_pending_tx()
    print('-----Start mining-----')

    DIFFICULTY = 4
    public_key = generate_key()[0]

    with filelock.FileLock(block_file_name1, timeout=10):
        try:
            with open(block_file_name2, 'r') as file:
                block_list = json.load(file)
            previous_hash = block_list[-1]['hash']
        except:
            block_list = []
            
    with filelock.FileLock(meta_chain_file_name1, timeout=10):
        try:
            with open(meta_chain_file_name2, 'r') as file:
                meta_block_list = json.load(file)
                previous_hash = meta_block_list[-1]['hash']
        except:
            meta_block_list = []
            previous_hash = ''

    with filelock.FileLock(trans_file_name1, timeout=10):
        try:
            with open(trans_file_name2, 'r') as file:
                file_tx_list = json.load(file)
        except:
            file_tx_list = []
            
    tx_id_list = []
    tx_list = []
    
    sha = hashlib.sha256()
    for tx in file_tx_list:
        tx_id_list.append(tx['TxID'][:10])
        sha.update(bytes.fromhex(tx['TxID']))
        tx_list.append(tx)
        if len(tx_list) == num_of_tx_to_store:
            break
            
    tmp = file_tx_list
    file_tx_list = []
    
    for tx in tmp:
        if tx['TxID'][:10] not in tx_id_list:
            file_tx_list.append(tx)
            
    tx_hash = sha.digest()
    for nonce in range(random.randint(0,99999),100000000):
        if mining_exit_flag == True:
            mining_exit_flag = False
            mining_flag = False
            return
        #f num_of_pending_tx >= 50:
        #    print('Adjusting mining difficulty...')
        #    DIFFICULTY = 3
        sha = hashlib.sha256()
        sha.update(bytes(nonce))
        sha.update(bytes.fromhex(previous_hash))
        sha.update(tx_hash)
        hash = sha.digest()

        if re.match(r'0{' + str(DIFFICULTY) + r'}', hash.hex()):
            break

    block_list.append({
        'hash' : hash.hex(),
        'timestamp':str(datetime.datetime.now()),
        'nonce': nonce,
        'previous_hash': previous_hash,
        'tx_hash': tx_hash.hex(),
        'height': num_of_blocks,
        'size':len(tx_list),
        'tx'   : tx_list
    })
    
    if randomize() == True:
        with filelock.FileLock(block_file_name1, timeout=10):
            with open(block_file_name2, 'w') as file:
                json.dump(block_list, file, indent=2)

    with filelock.FileLock(trans_file_name1, timeout=10):
        with open(trans_file_name2, 'w') as file:
            json.dump(file_tx_list, file, indent=2)
    #print(tx_id_list)
    share_block(block_list[-1],tx_id_list)
    add_block_in_hashchain(block_list[-1])
    
    num_of_blocks += 1
    mining_flag = False
    num_of_new_tx -= len(tx_list)
    print('-----End mining-----')
    print("found golden nonce!",nonce)
    print(num_of_blocks,"th blocks has made.")
    
    if num_of_blocks == system_stop_point:
        print("Number of block has reached system to stop value.")
        build_message(100,ID,tx_generator_ip,tx_generator_port,host,port,0,0,0,0,0,0,0)
        build_message(100,ID,reqester_ip,reqester_port,host,port,0,0,0,0,0,0,0)
        exit()
    process_pending_tx()
            
def share_block(block,tx_id_list):
    global ID
    global peer_list_file_name1
    global peer_list_file_name2
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'r') as file:
                peer_list = json.load(file)
        except:
            peer_list = []
    #def build_message(msg_type,ID,addr_to,port_to,my_addr,my_port,sp1,sp2,sp3,sp4,sp5,sp6):
    for peer in peer_list:
        if peer != ID:
            build_message('b',ID,peer_list[peer]['IP address'],peer_list[peer]['Port'],host,port,block['hash'],block['nonce'],block['previous_hash'],block['tx_hash'],tx_id_list,block['height'],block['timestamp'])

def mining_manager():
    global mining_flag
    global num_of_new_tx
    global system_stop_flag
    global num_of_tx_to_store
    global num_of_blocks
    global system_stop_point
    
    print("mining manager start...")
    while True:
        sleep(1)
        if mining_flag == False and num_of_blocks <= system_stop_point:
            mining_flag = True
            mining_exit_flag = False
            mining()
        elif system_stop_flag == True or num_of_blocks > system_stop_point:
            exit()
        else:
            sleep(3)

def process_query(TxID,requester_ip,requester_port):
    global block_file_name1
    global block_file_name2
    
    with filelock.FileLock(block_file_name1, timeout=10):
        try:
            with open(block_file_name2, 'r') as file:
                block_list = json.load(file)
            previous_hash = block_list[-1]['hash']
        except:
            block_list = []
            
    for block in block_list:
        for tx in block['tx']:
            if tx['TxID'] == TxID:
                build_message('d',ID,requester_ip,requester_port,host,port,tx['TxID'],tx['time'],tx['publisher'],tx['data'],tx['sig'],0,0)
                return
    build_message('d',ID,requester_ip,requester_port,host,port,0,0,0,0,0,0,0)
    
def p2p_start():
    global host
    global port
    global ID
    global my_socket
    host = get_myip()
    my_socket = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    port = port_set()
    ID = "N" + host[-2:] + str(port)[-2:]
    initialize_peer_list(ID,host,port)
    show_my_info()
    print(ID)
    
    #他のノードからのリクエストを常に待機する
    accepting_request = threading.Thread(target=pending)
    accepting_request.setDaemon(True)
    accepting_request.start()
    
    #20秒置きにpeerの生存確認を行う
    conn_confirmation = threading.Thread(target=connection_confirmation)
    conn_confirmation.setDaemon(True)
    conn_confirmation.start()

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
    edge_node_list = {}
    my_info = {
              ID:{
                    "time":time.ctime(),
                    "IP address":host,
                    "Port":port}
              }
    
    with filelock.FileLock(peer_list_file_name1,timeout=10):
        try:
            with open(peer_list_file_name2,'w') as file:
                json.dump(my_info,file,indent=2)
        except:
            exit()

def show_my_info():
    print("Your address is :",host)
    print("Your port is :",port)
    print("Your ID is:",ID)
    
def handle_message(message):
    global host
    global port
    global node_list
    global system_start_flag
    global mining_exit_flag
    global mining_flag
    global request_OK_flag
    global tx_generator_ip
    global tx_generator_port
    global reqester_ip
    global reqester_port
    
    conn = message
    msg = conn.recv(4096)

    msg = json.loads(msg)
    msg_type = msg['msg_type']
    peer_ID = msg['ID']
    peer_addr = msg['addr']
    peer_port = msg['port']
    
    if msg_type == 0:
        request_OK_flag = True
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
    elif msg_type == 'a':
        tx_generator_ip = peer_addr
        tx_generator_port = peer_port
        tx = {"TxID":msg["sp1"],
              "time":msg["sp3"],
              "publisher":msg["sp6"],
              "data":msg["sp4"],
              "sig":msg["sp5"]}
        verify(msg["sp1"],tx)
    elif msg_type == 'b':
        mining_exit_flag = True
        print('-----End mining-----')
        print(peer_ID,"has found golden nonce,",msg['sp2'])
        block = {"hash":msg['sp1'],
                 'timestamp':msg['sp7'],
                 'nonce':msg['sp2'],
                 'previous_hash':msg['sp3'],
                 'tx_hash':msg['sp4'],
                 'height':msg['sp6'],
                 'size':len(msg['sp5']),
                 'tx':[]}
        add_block(block,msg['sp5'],peer_ID)
    elif msg_type == 'c':
        reqester_ip = peer_addr
        reqester_port = peer_port 
        process_query(msg['sp1'],peer_addr,peer_port)
    elif msg_type == 'd':
        print("Cought lost tx Request")
        reply_lost_tx(msg['sp1'],peer_ID)
    elif msg_type == 'e':
        print("\nJJJ\n")
        tx = {"TxID":msg["sp1"],
              "time":msg["sp3"],
              "publisher":msg["sp6"],
              "data":msg["sp4"],
              "sig":msg["sp5"]}
        process_lost_tx(tx,msg["sp7"])
        
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
