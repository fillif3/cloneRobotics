import socket
import pickle


def run_client():
    # create a socket object
    client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

    socket_path = '/tmp/my_socket' #TODO sys.argv
    # establish connection with server
    client.connect(socket_path)

    try:
        while True:
            # get input message from user and send it to the server

            #client.sendall('')

            # receive message from the server
            msg = client.recv(1024)
            measure_arr=pickle.loads(msg) #Mention unsafe
            print('----------')	
            print(measure_arr)

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

