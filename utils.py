import os
import stat
import pathlib
import logging
import time

def get_logger(level,is_server=True):
    if is_server:
        folder_name = os.path.dirname(__file__) + '/logs_server'
    else:
        folder_name = os.path.dirname(__file__) + '/logs_client'

    pathlib.Path(folder_name).mkdir(parents=True, exist_ok=True)

    while True:
        file_name = folder_name + '/' + time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time())) + '.txt'
        try:
            logging.basicConfig(filename=file_name,
                                format='%(asctime)s %(message)s',
                                filemode='x')
            break
        except FileNotFoundError:
            print('error')  # TODO fix
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))
    return logger


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

def can_use_unix_socket(path):
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

def test_inputs(args,is_server=True):
    if args.socket_path is None: args.socket_path='/tmp/my_socket'
    if not can_use_unix_socket(args.socket_path):
        print('The chosen path is not a directory. "/tmp/my_socket" will be used instead')
        args.socket_path='/tmp/my_socket'
    if is_server:
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
                print('You have incorrect timeout. timeout is set to 500 Hz')
            args.timeout_ms=100
        else:
            args.timeout_ms=float(args.timeout_ms)
