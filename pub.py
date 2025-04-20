import socket
import os
import select
import sys
import time
import pickle
import pathlib # Path
import logging
import sensors




def main():
    socket_path = '/tmp/my_socket' #TODO check
    #socket_path = sys.argv[1]
    try:
        os.unlink(socket_path)
    except OSError:
        if os.path.exists(socket_path):
            raise
    # create a socket object
    #time_increment = 1/float(sys.argv[2]) #TODO check
    time_increment=1
    time_increment_file=max(1,time_increment)
    client=None
    folder_name = os.path.dirname(__file__)+'/logs'
    pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True)

    while True:
        file_name=folder_name+'/'+time.strftime("%Y-%m-%d %H:%M:%S",time.gmtime(time.time()))+'.txt'
        try:
            logging.basicConfig(filename=file_name,
                                format='%(asctime)s %(message)s',
                                filemode='x')
            break
        except FileNotFoundError:
            print('error') #TODO fix
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)


    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        # bind the socket to the host and port

        #server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.settimeout(time_increment)
        server.bind(socket_path)
        server.listen()
        logger.info('Server started working!\n')
        file_curr_time=time.time()
        while True:

            #try: (conn, (ip, port)) = tcpServer.accept()
            if client is  None:
                try: (client, _) = server.accept()
                except socket.timeout: pass
            curr_time = time.time()




            measure_arr = sensors.get_measurements() #TODO implement correct function
            msg = pickle.dumps(measure_arr)
            #if 'client' in locals(): send_msg(client,address,msg)
            if client is not None: client.sendall(msg) #TODO check returned msfg
            if (file_curr_time+time_increment_file)<time.time():
                logger.info("Connection:"+str(client is not None)+";MSG:"+str(measure_arr)+'Time:'+str(time.time())+'\n')
                file_curr_time=time.time()

            if client is not None: time.sleep(time_increment+(curr_time-time.time())/1000)






        
#def send_msg(client,address,msg):
#    for key in clients_dict:
#        clients_dict[key].send(msg)
                
                
            
    
    

    
def pop_client(keys_to_):
    pass
        
def add_client(clients_dict, client_socket, addr):
    clients_dict[addr]=client_socket






    try:
        # print(f"Accepted connection from {addr[0]}:{addr[1]}")
        i=1
        while True:
            # receive and print client messages
            print(i)
            i=i+1
            time.sleep(3)
            #request = client_socket.recv(1024).decode("utf-8")
            #if request.lower() == "close":
            #    client_socket.send("closed".encode("utf-8"))
            #    break
            #print(f"Received: {request}")
            # convert and send accept response to the client
            response = str(i)
            client_socket.send(response.encode("utf-8"))
    except Exception as e:
        print(f"Error when hanlding client: {e}")
    finally:
        client_socket.close()
        print(f"Connection to client ({addr[0]}:{addr[1]}) closed")
        
if __name__ == "__main__":
    main()
