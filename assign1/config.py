from configparser import ConfigParser
import random


config = ConfigParser()
STORED_PORT = {}

def clear_file(file_name):
    file = open(file_name,"w")
    file.close()   

def generate_port(n,lower_bound,upper_bound):
    ports = random.sample(range(lower_bound, upper_bound),n)
    return ports

def create_section(config,section_name,TOTAL_SEED,RUNNING_SERVER):
    if not config.has_section(TOTAL_SEED):
        print("no total_seed section")
        config.add_section(TOTAL_SEED)
        config.set(TOTAL_SEED,'max_peer',"0")

    if not config.has_section(RUNNING_SERVER):
        print("no running section")
        config.add_section(RUNNING_SERVER)
        config.set(RUNNING_SERVER,'peer_count',"0") 

    if not config.has_section(section_name):
        print("no seed listen port section")
        config.add_section(section_name)

def get_port_from_config_file(file_name,sections,sections_keys):
    config = ConfigParser()
    config.read(file_name)
    
    TOTAL_SEED = sections[0]
    RUNNING_SERVER = sections[1]
    section_name = sections[2]
    
    max_peer = sections_keys[0]
    running_count = sections_keys[1]

    create_section(config,section_name,TOTAL_SEED,RUNNING_SERVER)
    max_count = int(config.get(TOTAL_SEED,max_peer))
    running = int(config.get(RUNNING_SERVER,running_count)) + 1
    # print(f'[PEER SERVER]:{running}')
    config.set(RUNNING_SERVER,running_count,str(running))
    port = -1
    if( running <= max_count ):
        port = int(config.get(section_name,str(running)))
    else:
        print(f'[ALL PORT USED FROM CONFIG FILE]')
        port = int(input('Enter New port no:'))
        config.set(section_name, str(running), str(port) )
        config.set(TOTAL_SEED,max_peer,str(max_count+1))
    with open(file_name, 'w') as f:
        config.write(f)
    return port

def decrease_running_count(file_name,section_name,key):
        config = ConfigParser()
        config.read(file_name)
        running = int(config.get(section_name,key))-1
        config.set(section_name,key,str(running))
        with open(file_name, 'w') as f:
            config.write(f)

def write_config(ports):
    # Clear previously stored data
    file_name = 'config.ini'
    clear_file(file_name)

    section_name = 'SEED LISTEN PORT'
    TOTAL_SEED = 'TOTAL SEED'
    RUNNING_SERVER = 'RUNNING SERVER'
    # fill new data
    config.read(file_name)
    if not config.has_section(TOTAL_SEED):
        config.add_section(TOTAL_SEED)
        config.set(TOTAL_SEED,'seed_count',"0") 

    if not config.has_section(RUNNING_SERVER):
        config.add_section(RUNNING_SERVER)
        config.set(RUNNING_SERVER,'server_count',"0") 

    if not config.has_section(section_name):
        config.add_section(section_name)
    
    # total_seed = int(input("Number of seed server want:"))
    total_seed = len(ports)
    config.set(TOTAL_SEED,"seed_count",str(total_seed))
    count=1

    for port_no in ports:
        port_no = str(port_no)
        STORED_PORT[int(port_no)] = count
        config.set(section_name, str(count), port_no)
        count = count+1
        total_seed = total_seed-1

    with open(file_name, 'w') as f:
        config.write(f)

def write_peers_port(ports):
    file_name = 'peers_port.ini'
    clear_file(file_name)

    section_name = 'PEERS LISTEN PORT'
    TOTAL_SEED = 'TOTAL PEERS'
    RUNNING_SERVER = 'RUNNING PEERS'
    
    # fill new data
    config.read(file_name)
    if not config.has_section(TOTAL_SEED):
        config.add_section(TOTAL_SEED)
        config.set(TOTAL_SEED,'max_peer',"0") 

    if not config.has_section(RUNNING_SERVER):
        config.add_section(RUNNING_SERVER)
        config.set(RUNNING_SERVER,'peer_count',"0") 

    if not config.has_section(section_name):
        config.add_section(section_name)
    
    # total_seed = int(input("Number of seed server want:"))
    total_seed = len(ports)
    config.set(TOTAL_SEED,"max_peer",str(total_seed))
    count=1

    for port_no in ports:
        port_no = str(port_no)
        STORED_PORT[int(port_no)] = count
        config.set(section_name, str(count), port_no)
        count = count+1
        total_seed = total_seed-1

    with open(file_name, 'w') as f:
        config.write(f)

def reset_running_count(file_name,section,key):
    config = ConfigParser()
    config.read(file_name)
    config.set(section,key,"0")
    with open(file_name, 'w') as f:
        config.write(f)

def main():
    print("Generate ports for Seed and Pee")
    choice = int(input("1:SEED and 2:PEERS and 3:RESET COUNT:-"))
    if(choice == 1):
        n=int(input("Number of seed server:"))
        lower_bound = 9888
        upper_bound = 9999
        ports = generate_port(n,lower_bound,upper_bound)
        write_config(ports)
    elif(choice == 2):
        n=int(input("Number of Peers Port:"))
        lower_bound = 9555
        upper_bound = 9777
        ports = generate_port(n,lower_bound,upper_bound)
        write_peers_port(ports)
    elif(choice == 3):
        file_name = 'config.ini'
        reset_running_count(file_name,"RUNNING SERVER","server_count")
        file_name = 'peers_port.ini'
        reset_running_count(file_name,"RUNNING PEERS","peer_count")

if __name__ == "__main__":
    main()