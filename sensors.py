import random
import time
G_CONST=9.81

def get_measurements():
    measurement={
        "xAcc":2*random.random()-1, #
        "yAcc":2*random.random()-1, #If I understand correctly the information in brackets, I am supposed to use Netwons
        # but it is easier to just send accelaration (otherwise both softwares need to know mass) and I believe it is
        # best to make software as simple as possible. This is also how it works in, e.g., ROS
        "zAcc":2*random.random()-1 + G_CONST, # gravity is required to find directions
        "timestampAcc":int(time.time()),
        "xGyro": 2*random.random()-1, #It must be float
        "yGyro": 2*random.random()-1, #I use 0 mean so the drone does not fall (i.e. the most unlucky sates are less liekly)
        "zGyro": 2*random.random()-1, #Ranges are much higher https://mavicpilots.com/threads/angular-speed.76807/
        "timestampGyro": int(time.time()),
        "xMag": 2*random.random()-1, #Ranges: up to 7.5 https://sensysmagnetometer.com/products/magdrone-r3-magnetometer-for-drone/
        "yMag": 2*random.random()-1,
        "zMag": 2*random.random()-1,
        "timestampGyro": int(time.time())
    }
    return measurement
    

