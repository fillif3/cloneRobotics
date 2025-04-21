import socket
import pickle
import direction
import argparse
import utils



def run_client():
    # create a socket object
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket-path", help="Path used for communicating between sockets.")
    parser.add_argument("--log-level", help="""This variable specifies the logging level. The higher level
        the less logs will be created. Possible values are: 'NOTSET'->(0), 'DEBUG'->(10), 'INFO'->(20), 'WARNING'->(30), 
        'ERROR'->(40), 'CRITICAL'->(50)""")
    parser.add_argument("--timeout-ms", help="""This variable specifies how long client should wait before timeout""")
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)


    args = parser.parse_args()
    # args.socket_path='/tmp/socket/32132131'
    utils.test_inputs(args,is_server=False)
    client.settimeout(args.timeout_ms)
    # establish connection with server
    logger = utils.get_logger(args.log_level,is_server=False)
    try:client.connect(args.socket_path)
    except ConnectionRefusedError:
        logger.error("Connection refused, exiting")
        raise ConnectionRefusedError('Connection refused, exiting')
    msg_time = None
    euler_angles=None
    current_system='XYZ'
    #try:
    while True:
        # get input message from user and send it to the server

        #client.sendall('')

        # receive message from the server
        msg = client.recv(1024)
        measure_arr=pickle.loads(msg) #Mention unsafe
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

