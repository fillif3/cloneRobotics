import socket
import os
import argparse
#import sys
import time
import pickle
import pathlib # Path
import logging
import sensors

def is_positive_float(element):
    #If you expect None to be passed:
    if element is None:
        return False
    try:
        new_element=float(element)
        if new_element>0: return True
        else: return False
    except ValueError:
        return False



def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket-path", help="Path used for communicating between sockets.")
    parser.add_argument("--log-level", help="""This variable specifies the logging level. The higher level
    the less logs will be created. Possible values are: 'NOTSET'->(0), 'DEBUG'->(10), 'INFO'->(20), 'WARNING'->(30), 
    'ERROR'->(40), 'CRITICAL'->(50)""")
    parser.add_argument("--frequency-hz", help="Frequency that shows how often will the massages be sent.")
    args = parser.parse_args()
    if args.socket_path is None:
        args.socket_path='/tmp/my_socket'
    try:
        os.unlink(args.socket_path)
    except PermissionError:
        raise PermissionError("You do not have permission to use this path. Please, specify different path.")
    except OSError:
        raise OSError("The chose path is used be a different software (maybe anther socket). Please, specify different path.")
    if args.log_level is None:
        args.log_level='INFO'
    if not args.log_level in ['INFO', 'DEBUG', 'NOTSET', 'ERROR', 'CRITICAL', 'WARNING']:
        print("Invalid log level. Log level set to INFO")
    if not is_positive_float(args.frequency_hz):
        print('You have not specified frequency of the specified is not a positive number. Frequency is set to 500 Hz')
        args.frequency_hz=500

    #socket_path = sys.argv[1]

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
    logger.setLevel(getattr(logging, args.log_level))


    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        # bind the socket to the host and port

        #server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.settimeout(time_increment)
        server.bind(args.socket_path)
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
