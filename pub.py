import socket
import time
import pickle
import sensors
import utils




def main():
    args=utils.get_args_from_cli()
    #args.socket_path='/tmp/socket/32132131'
    utils.test_inputs(args)
    #socket_path = sys.argv[1]

    # create a socket object
    #time_increment = 1/float(sys.argv[2]) #TODO check

    time_increment=1/args.frequency_hz
    time_increment_file=max(0.01,time_increment)
    client=None

    logger=utils.get_logger(args.log_level)

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

            try:
                if client is not None: client.sendall(msg) #TODO check returned msfg
            except BrokenPipeError:
                client=None
                logger.warning('Client disconnected.')
            if (file_curr_time+time_increment_file)<time.time():
                logger.info("Connection:"+str(client is not None)+";MSG:"+str(measure_arr)+'Time:'+str(time.time())+'\n')
                file_curr_time=time.time()

            if client is not None: time.sleep(time_increment+(curr_time-time.time())/1000)




if __name__ == "__main__":
    main()
