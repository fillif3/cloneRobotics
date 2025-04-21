import random
import time
G_CONST=9.81


def get_measurements():#Matlab mention
    """
    This function returns randomly generated raw data from sensors.
    :return: dict with raw data where prefix "x", "y", and "z" represent axis, Acc, Gyro, Mag represent readings from
    Accelerometer, Gyroscope and Magnetometer respectively (e.g. yAcc represents Accelerometer's reading with respect to
    y-axis. Prefix timestamp represents time of measurement in ms.
    """
    measurement={
        "xAcc":2*random.random()-1,
        "yAcc":2*random.random()-1,
        "zAcc":2*random.random()-1 + G_CONST,
        "timestampAcc":int(time.time()*1000),
        "xGyro": 2*random.random()-1,
        "yGyro": 2*random.random()-1,
        "zGyro": 2*random.random()-1,
        "timestampGyro": int(time.time()*1000),
        "xMag": 2*random.random()-1,
        "yMag": 2*random.random()-1,
        "zMag": 2*random.random()-1,
        "timestampMag": int(time.time()*1000)
    }
    return measurement
    

