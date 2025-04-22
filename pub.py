import socket
import time
import pickle
import sensors
import utils




def main():
    # Get and test user's inputs
    args=utils.get_args_from_cli()
    utils.test_inputs(args)

    # Set how often msgs will be sent
    time_increment=1/args.frequency_hz
    time_increment_file=max(0.01,time_increment) # We do not want to log msgs too often
    client=None

    logger=utils.get_logger(args.log_level)

    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server:
        #Prepare server
        server.settimeout(time_increment)
        server.bind(args.socket_path)
        server.listen()
        logger.info('Server started working!\n')
        file_curr_time=time.time()
        while True:


            #Try to connect with client
            if client is  None:
                try: (client, _) = server.accept()
                except socket.timeout: pass
            curr_time = time.time()

            # Get msg from sensors and cipher it
            measure_arr = sensors.get_measurements()
            msg = pickle.dumps(measure_arr)
            #if 'client' in locals(): send_msg(client,address,msg)

            try:
                if client is not None: client.sendall(msg) #Try to send msg
            except BrokenPipeError: #Client diconnected
                client=None
                logger.warning('Client disconnected.')
            # Log a msg
            if (file_curr_time+time_increment_file)<time.time():
                logger.info("Connection:"+str(client is not None)+";MSG:"+str(measure_arr)+'Time:'+str(time.time())+'\n')
                file_curr_time=time.time()

            #Sleep only when connected. Otherwise server.accept() slows down program
            if client is not None: time.sleep(time_increment+(curr_time-time.time())/1000)




if __name__ == "__main__":
    main()
