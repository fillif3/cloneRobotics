import socket
import os
import argparse
import stat
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


def can_use_unix_socket(path: str) -> bool:
    try:
        # Must be an absolute path and not contain null bytes
        if not path.startswith('/') or '\x00' in path:
            return False

        # Path length limit for UNIX sockets (platform-dependent, 108 is typical on Linux)
        if len(path.encode()) >= 108:
            return False

        parent = os.path.dirname(path)

        # Parent directory must exist and be a directory
        if not os.path.isdir(parent):
            return False

        # You need write and execute permission on the parent
        if not os.access(parent, os.W_OK | os.X_OK):
            return False

        # If the path already exists:
        if os.path.exists(path):
            # If it’s already a socket, we might want to allow replacing it
            mode = os.stat(path).st_mode
            if stat.S_ISSOCK(mode):
                return os.access(path, os.W_OK)  # Can we remove/replace it?
            else:
                return False  # Some other file exists there

        # All good
        return True

    except Exception:
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket-path", help="Path used for communicating between sockets.")
    parser.add_argument("--log-level", help="""This variable specifies the logging level. The higher level
    the less logs will be created. Possible values are: 'NOTSET'->(0), 'DEBUG'->(10), 'INFO'->(20), 'WARNING'->(30), 
    'ERROR'->(40), 'CRITICAL'->(50)""")
    parser.add_argument("--frequency-hz", help="Frequency that shows how often will the massages be sent.")
    args = parser.parse_args()
    #args.socket_path='/tmp/socket/32132131'
    if args.socket_path is None: args.socket_path='/tmp/my_socket'
    if not can_use_unix_socket(args.socket_path):
        print('The chosen path is not a directory. "/tmp/my_socket" will be used instead')
        args.socket_path='/tmp/my_socket'

    try: os.unlink(args.socket_path)
    except PermissionError: raise PermissionError("You do not have permission to use this path. Please, specify different path.")
    except OSError:
        if os.path.exists(args.socket_path):
            raise OSError("The chose path is used be a different software (maybe anther socket). Please, specify different path.")
    if args.log_level is None:
        args.log_level='INFO'
    if not args.log_level in ['INFO', 'DEBUG', 'NOTSET', 'ERROR', 'CRITICAL', 'WARNING']: # Current Logger is very simple but it is a good base
        #More logs could be added in the future depending on the requirments and what we want to test
        print("Invalid log level. Log level set to INFO")
        args.log_level='INFO'
    if not is_positive_float(args.frequency_hz):
        if args.frequency_hz is not None:
            print('You have incorrect frequency. Frequency is set to 500 Hz')
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



if __name__ == "__main__":
    main()
