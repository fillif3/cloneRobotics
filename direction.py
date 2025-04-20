import numpy as np


def euler_to_quanternion(euler_angles):
    """
    Convert an Euler angle to a quaternion.

    Input
      :param roll: The roll (rotation around x-axis) angle in radians.
      :param pitch: The pitch (rotation around y-axis) angle in radians.
      :param yaw: The yaw (rotation around z-axis) angle in radians.

    Output
      :return qx, qy, qz, qw: The orientatios,bmcn in quaternion [x,y,z,w] format
    """
    qx = np.sin(euler_angles['roll'] / 2) * np.cos(euler_angles['pitch'] / 2) * np.cos(euler_angles['yaw'] / 2) - \
         np.cos(euler_angles['roll'] / 2) * np.sin(euler_angles['pitch']  / 2) * np.sin(euler_angles['yaw']  / 2)
    qy = np.cos(euler_angles['roll'] / 2) * np.sin(euler_angles['pitch']  / 2) * np.cos(euler_angles['yaw']  / 2) + \
         np.sin(euler_angles['roll'] / 2) * np.cos(euler_angles['pitch']  / 2) * np.sin(euler_angles['yaw']  / 2)
    qz = np.cos(euler_angles['roll'] / 2) * np.cos(euler_angles['pitch']  / 2) * np.sin(euler_angles['yaw']  / 2) - \
         np.sin(euler_angles['roll'] / 2) * np.sin(euler_angles['pitch']  / 2) * np.cos(euler_angles['yaw']  / 2)
    qw = np.cos(euler_angles['roll'] / 2) * np.cos(euler_angles['pitch']  / 2) * np.cos(euler_angles['yaw']  / 2) + \
         np.sin(euler_angles['roll'] / 2) * np.sin(euler_angles['pitch']  / 2) * np.sin(euler_angles['yaw']  / 2)
    return {'x':qx,'y':qy,'z':qz,'w':qw}

def get_euler_angles_from_accelerometer(accelerometer_msg):
    #https://www.nxp.com/docs/en/application-note/AN3461.pdf
    #No information of order of euler angles, I assume it is xyz
    roll=np.arctan(accelerometer_msg['yAcc']/accelerometer_msg['zAcc'])
    pitch=np.arctan(-accelerometer_msg['xAcc']/np.sqrt(accelerometer_msg['yAcc']**2+accelerometer_msg['zAcc']**2))
    return roll,pitch

def get_yaw_from_magnetometer(magnetometer_msg):
    #https://www.nxp.com/docs/en/application-note/AN4248.pdf
    return np.arctan(-magnetometer_msg['yMag']/magnetometer_msg['xMag'])

def normalize_euler_angles(euler_angles):
    for key in ('roll', 'pitch', 'yaw'):
        while euler_angles[key]<=np.pi/2:
            euler_angles[key]=euler_angles[key]+np.pi/2
        while euler_angles[key]>np.pi/2:
            euler_angles[key]=euler_angles[key]-np.pi/2


def initialize_euler_angles(measure_arr):
    euler_angles= {'roll': (get_euler_angles_from_accelerometer(measure_arr))[0],
                   'pitch': (get_euler_angles_from_accelerometer(measure_arr))[1],
                   'yaw': get_yaw_from_magnetometer(measure_arr)}
    euler_angles_variance={'roll':1000000,'pitch':1000000,'yaw':1000000}
    return euler_angles,euler_angles_variance

def update_euler_angles(measure_arr,angles_prediction,angles_variance,last_time_step):
    absolute_angles,absolute_angles_variance=initialize_euler_angles(measure_arr)
    integrated_angles,integrated_angles_variance=get_euler_angles_from_gyroscope(measure_arr,last_time_step,angles_prediction) #TODO finish
    angles_intermediate,angles_variance_intermediate=kalman_euler_angles(angles_prediction,angles_variance,
                                                                         absolute_angles,absolute_angles_variance)
    angles_updated, angles_variance_updated = kalman_euler_angles(angles_intermediate, angles_variance_intermediate,
                                                                            integrated_angles, integrated_angles_variance)
    return angles_updated, angles_variance_updated

    #We assume that measurments are uncolarted so we can do this sequnatially
    # https://math.stackexchange.com/questions/4011815/kalman-filtering-processing-all-measurements-together-vs-processing-them-sequen
    # OTherwise, we would need to implment them toghether


    # A simple example how kalman filter works for 1-dimensional stats
    # I worked under assumption the each angle is measured but it is not true. In real-world, UKF should be used. Moreover,
    # in such a case, varaince woulf be coupled so it would be required to use matricies instead of scalar values. It would
    # also be required to use matrcies if model was avaiable.

def get_euler_angles_from_gyroscope(measure_arr,last_time_step,angles):
    # https://liqul.github.io/blog/assets/rotation.pdf
    # Note: Integration could be  improved with Runge-Kutta 4 instead of Euler method
    rate_rad={}
    for key in ('xGyro', 'yGyro', 'zGyro'):
        rate_rad[key]=mdeg_to_rad(measure_arr[key])
    roll_rate=rate_rad['xGyro']+rate_rad['yGyro']*np.sin(angles['roll'])*np.tan(angles['pitch'])+ \
              rate_rad['zGyro']*np.sin(angles['roll'])*np.tan(angles['pitch'])
    pitch_rate=rate_rad['yGyro']*np.cos(angles['roll'])-rate_rad['zGyro']*np.sin(angles['roll'])
    yaw_rate=rate_rad['yGyro']*np.sin(angles['roll'])/np.cos(angles['pitch'])+rate_rad['zGyro']*\
             np.cos(angles['roll'])/np.cos(angles['pitch'])

    time_diff=(measure_arr['timestampGyro']-last_time_step)/1000
    euler_angles={'roll':roll_rate*time_diff+angles['roll'],'pitch':pitch_rate*time_diff+angles['pitch'],\
                             'yaw':yaw_rate*time_diff+angles['yaw']}
    euler_angles_variance = {'roll': 1, 'pitch': 1, 'yaw': 1}
    return euler_angles,euler_angles_variance

def kalman_euler_angles(state,state_var,measurement,measurement_var):
    updated_state={}
    updated_var={}
    for key in ('roll', 'pitch', 'yaw'):
        kalman_gain=state_var[key]/(state_var[key]+measurement_var[key])
        updated_state[key]=state[key]+kalman_gain*(measurement[key]-state[key])
        updated_var[key]=(1-kalman_gain)*state_var[key]
    return updated_state,updated_var

def mdeg_to_rad(mdeg):
    return mdeg*np.pi/180/1000

