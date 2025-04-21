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
        "xAcc":2*random.random()-1, #
        "yAcc":2*random.random()-1, #If I understand correctly the information in brackets, I am supposed to use Netwons,
        # but it is easier to just send acceleration (otherwise both softwares need to know mass) and I believe it is
        # best to make software as simple as possible. This is also how it works in, e.g., ROS
        "zAcc":2*random.random()-1 + G_CONST, # gravity is required to find directions
        "timestampAcc":int(time.time()*1000),
        "xGyro": 2*random.random()-1, #It must be float
        "yGyro": 2*random.random()-1, #I use 0 mean so the drone does not fall (i.e. the most unlucky sates are less likely)
        "zGyro": 2*random.random()-1, #Ranges are much higher https://mavicpilots.com/threads/angular-speed.76807/
        "timestampGyro": int(time.time()*1000),
        "xMag": 2*random.random()-1, #Ranges: up to 7.5 https://sensysmagnetometer.com/products/magdrone-r3-magnetometer-for-drone/
        "yMag": 2*random.random()-1,
        "zMag": 2*random.random()-1,
        "timestampGyro": int(time.time()*1000)
    }
    return measurement
    

