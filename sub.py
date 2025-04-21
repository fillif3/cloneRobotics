import socket
import pickle
import direction
import utils



def run_client():
    # create a socket object
    args=utils.get_args_from_cli(is_server=False)
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)


    # args.socket_path='/tmp/socket/32132131'
    utils.test_inputs(args,is_server=False)
    client.settimeout(args.timeout_ms/1000)
    # establish connection with server
    logger = utils.get_logger(args.log_level,is_server=False)
    try:client.connect(args.socket_path)
    except ConnectionRefusedError:
        logger.error("Connection refused, exiting")
        raise ConnectionRefusedError('Connection refused, exiting')
    msg_time = None
    euler_angles=None
    while True:
        # get input message from user and send it to the server

        #client.sendall('')

        # receive message from the server
        try: msg = client.recv(1024)
        except TimeoutError:
            logger.error("Waiting too long for a response from a server")
            break
        try: measure_arr=pickle.loads(msg)
        except EOFError:
            logger.error("Error receiving data")
            break
         #Mention unsafe
        if euler_angles is None:
            euler_angles,angles_rates,euler_angles_variance,current_system=direction.initialize_euler_angles(measure_arr)
        else:
            euler_angles,angles_rates,euler_angles_variance,current_system=direction.update_euler_angles(measure_arr,euler_angles,
                                                                        angles_rates, euler_angles_variance,msg_time,current_system)
        msg_time=measure_arr['timestampGyro']# We only use timestamp of Gyro because it is the only sensor, which return rates
        quaternion=direction.euler_to_quanternion(euler_angles,current_system)
        # We should add unit tests
        logger.info(
            "Current system:" + current_system + ";Euler angles:" + str(euler_angles) + ';Quaternion:' + str(quaternion) + '\n')

        # if server sent us "closed" in the payload, we break out of
        # the loop and close our socket
        if msg.lower() == "closed":
            break

        #print(f"Received: {response}")
    #except Exception as e:
    #   print(f"Error: {e}")
    #finally:
    #    close client socket (connection to the server)
    #    client.close()
    #    print("Connection to server closed")


run_client()

