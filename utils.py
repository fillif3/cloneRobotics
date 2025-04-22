import os
import stat
import pathlib
import logging
import datetime
import argparse

def get_logger(level,is_server=True):
    """
    This function creates a logger and returns it.
    :param level: Level (NOTSET'->(0), 'DEBUG'->(10), 'INFO'->(20), 'WARNING'->(30),
    'ERROR'->(40), 'CRITICAL'->(50) of logging to create.
    :param is_server: If true, logger for server is created. Otherwise, logger for client is created.
    :return: Logger object.
    """
    if is_server:
        folder_name = os.path.dirname(__file__) + '/logs_server'
    else:
        folder_name = os.path.dirname(__file__) + '/logs_client'

    pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True)

    while True: #Try to find a name for a file. If it exists, another name will be proposed in the next iteration
        file_name = folder_name + '/' + datetime.datetime.utcnow().isoformat(sep=' ', timespec='milliseconds') + '.txt'
        try:
            logging.basicConfig(filename=file_name,
                                format='%(asctime)s %(message)s',
                                filemode='x')
            break
        except FileExistsError:
            pass
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))
    return logger


def is_positive_float(element):
    """
    This function checks whether string input can be treated as a positive float.
    :param element: The function was written with string input, but it can be used on anything
    :return: Flag that answers if element can be treated as a positive float.
    """
    if element is None: #Check if None
        return False
    try:
        new_element=float(element)
        if new_element>0: return True
        else: return False
    except ValueError: return False #It is not possible to convert element to float


def can_use_unix_socket(path):
    """
    This function checks whether path can be used as a unix socket.
    :param path: String to check.
    :return: Flag that answers if path can be used as a unix socket.
    """
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

        return True

    #If there is anything wrong with the path (I cant even imagine what is sent here) just raise an exception
    except Exception: return False

def test_inputs(args,is_server=True):
    """
    This function checks whether input arguments from CLI are valid. If they are not, they are replaced with the default
    input arguments.
    :param args: Object with properties being arguments from CLI.
    :param is_server: Flag if server is used. Otherwise, client is used.
    :return: None
    """
    if args.socket_path is None: args.socket_path='/tmp/my_socket'
    if not can_use_unix_socket(args.socket_path):
        print('The chosen path is not a directory. "/tmp/my_socket" will be used instead')
        args.socket_path='/tmp/my_socket'
    if is_server:
        try: os.unlink(args.socket_path)
        except PermissionError: raise PermissionError("You do not have permission to use this path. Please, specify different path.")
        except OSError:
            if os.path.exists(args.socket_path):
                raise OSError("The chosen path is used by a different software (maybe another socket). Please, specify different path.")
    if args.log_level is None:
        args.log_level='INFO'
    if not args.log_level in ['INFO', 'DEBUG', 'NOTSET', 'ERROR', 'CRITICAL', 'WARNING']: # Current Logger is very simple but it is a good base
        #More logs could be added in the future depending on the requirements and what we want to test
        print("Invalid log level. Log level is set to INFO")
        args.log_level='INFO'
    if is_server:
        if not is_positive_float(args.frequency_hz):
            if args.frequency_hz is not None:
                print('You have incorrect frequency. Frequency is set to 500 Hz')
            args.frequency_hz=500
        else:
            args.frequency_hz=float(args.frequency_hz)
    else:
        if not is_positive_float(args.timeout_ms):
            if args.timeout_ms is not None:
                print('You have incorrect timeout. timeout is set to 100 ms')
            args.timeout_ms=100
        else:
            args.timeout_ms=float(args.timeout_ms)

def get_args_from_cli(is_server=True):
    """
    This function gets arguments from CLI.
    :param is_server: If true, server is used. Otherwise, client is used.
    :return: Object with properties being arguments from CLI.
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("--socket-path", help="Path used for communicating between sockets.")
    parser.add_argument("--log-level", help="""This variable specifies the logging level. The higher level
    the less logs will be created. Possible values are: 'NOTSET'->(0), 'DEBUG'->(10), 'INFO'->(20), 'WARNING'->(30), 
    'ERROR'->(40), 'CRITICAL'->(50)""")
    if is_server:parser.add_argument("--frequency-hz", help="Frequency that shows how often will the massages be sent.")
    else:parser.add_argument("--timeout-ms", help="""This variable specifies how long client should wait before timeout""")
    return parser.parse_args()