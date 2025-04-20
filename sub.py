import socket
import pickle
import direction



def run_client():
    # create a socket object
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    socket_path = '/tmp/my_socket' #TODO sys.argv
    # establish connection with server
    client.connect(socket_path)
    msg_time = None
    euler_angles=None
    try:
        while True:
            # get input message from user and send it to the server

            #client.sendall('')

            # receive message from the server
            msg = client.recv(1024)
            measure_arr=pickle.loads(msg) #Mention unsafe
            if euler_angles is None:
                euler_angles,euler_angles_variance=direction.initialize_euler_angles(measure_arr)
            else:
                euler_angles,euler_angles_variance=direction.update_euler_angles(measure_arr,euler_angles,euler_angles_variance,msg_time)
            msg_time=msg['timestampGyro']# We only use timestamp of Gyro because it is the only sensor, which return rates
            quanternion=direction.euler_to_quanternion(euler_angles)

            print(euler_angles)
            print(quanternion)

            # if server sent us "closed" in the payload, we break out of
            # the loop and close our socket
            if msg.lower() == "closed":
                break

            #print(f"Received: {response}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        # close client socket (connection to the server)
        client.close()
        print("Connection to server closed")


run_client()

