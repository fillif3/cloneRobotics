import numpy as np
from copy import copy
import math

MODEL_VARIANCE_MATRIX=np.diag([5,0.1]) #System variance aka Q matrix in Kalman filter
SENSOR_VARIANCE_MATRIX=np.diag([10,1]) #Sensor variance aka R matrix in Kalman filter

def euler_to_quanternion(euler_angles,system):
    """
    Convert an Euler angle to a quaternion.

    Input
      :dict euler_angles: dict with euler angles ('roll', 'pitch', 'yaw')
      :string system: 'XYZ' or 'YXZ'

    Output
      :return quanternion: Dict representing the quaternion with keys 'w', 'x', 'y', 'z'
    """
    if system=='XYZ':
        qx = np.sin(euler_angles['roll'] / 2) * np.cos(euler_angles['pitch'] / 2) * np.cos(euler_angles['yaw'] / 2) - \
             np.cos(euler_angles['roll'] / 2) * np.sin(euler_angles['pitch']  / 2) * np.sin(euler_angles['yaw']  / 2)
        qy = np.cos(euler_angles['roll'] / 2) * np.sin(euler_angles['pitch']  / 2) * np.cos(euler_angles['yaw']  / 2) + \
             np.sin(euler_angles['roll'] / 2) * np.cos(euler_angles['pitch']  / 2) * np.sin(euler_angles['yaw']  / 2)
        qz = np.cos(euler_angles['roll'] / 2) * np.cos(euler_angles['pitch']  / 2) * np.sin(euler_angles['yaw']  / 2) - \
             np.sin(euler_angles['roll'] / 2) * np.sin(euler_angles['pitch']  / 2) * np.cos(euler_angles['yaw']  / 2)
        qw = np.cos(euler_angles['roll'] / 2) * np.cos(euler_angles['pitch']  / 2) * np.cos(euler_angles['yaw']  / 2) + \
             np.sin(euler_angles['roll'] / 2) * np.sin(euler_angles['pitch']  / 2) * np.sin(euler_angles['yaw']  / 2)
    elif system=='YXZ': #I was unable to find transformation from this system to quaternion, so I used rotation matrix
        # as an intermediate step
        # source: https://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/
        Rx = np.array([
            [1, 0, 0],
            [0, np.cos(euler_angles['roll']), np.sin(euler_angles['roll'])],
            [0, -np.sin(euler_angles['roll']), np.cos(euler_angles['roll'])]
        ])
        Ry = np.array([
            [np.cos(euler_angles['pitch']), 0, -np.sin(euler_angles['pitch'])],
            [0, 1, 0],
            [np.sin(euler_angles['pitch']), 0, np.cos(euler_angles['pitch'])]
        ])
        Rz = np.array([
            [np.cos(euler_angles['yaw']), np.sin(euler_angles['yaw']), 0],
            [-np.sin(euler_angles['yaw']), np.cos(euler_angles['yaw']), 0],
            [0, 0, 1]
        ])

        # Combine the rotations
        R = matmul3(Ry,Rx,Rz)

        # Extract quaternion components
        qw = np.sqrt(1 + R[0, 0] + R[1, 1] + R[2, 2]) / 2
        qx = (R[2, 1] - R[1, 2]) / (4 * qw)
        qy = (R[0, 2] - R[2, 0]) / (4 * qw)
        qz = (R[1, 0] - R[0, 1]) / (4 * qw)

    else:
        raise Exception('Unknown system')


    return {'x':qx,'y':qy,'z':qz,'w':qw}

def get_euler_angles_from_accelerometer(accelerometer_msg,rot_system):
    """
    This function gets euler angles from accelerometer raw data.

    :param accelerometer_msg: dict with accelerometer data (keys: 'xAcc', 'yAcc', 'zAcc')
    :param rot_system: 'XYZ' or 'YXZ'
    :return roll,pitch: The euler angles ('roll', 'pitch')
    """
    #https://www.nxp.com/docs/en/application-note/AN3461.pdf
    if rot_system == 'XYZ':
        # There are at least 2 solutions (tan function returns two possible solution between -180 to 180 degrees). We restrict pitch to be between -90 to 90 degrees
        pitch=np.arctan(-accelerometer_msg['xAcc']/np.sqrt(accelerometer_msg['yAcc']**2+accelerometer_msg['zAcc']**2))
        roll=np.arctan(accelerometer_msg['yAcc']/accelerometer_msg['zAcc'])# Returns solution between -90 to 90 degreees
        # Check If roll between -90 to 90 degreees is correct. Otherwise, choose a different solution of tan function
        # cos(roll) is always positive (we restrict it to be between -90 and 90 degrees but it is not equal because there is a system to prevent the lock)
        if not math.copysign(1,roll)==math.copysign(1,accelerometer_msg['yAcc']):
            if roll<0: roll=roll+np.pi
            else: roll=roll+np.pi
    elif rot_system == 'YXZ':
        # There are at least 2 solutions. We restrict roll to be between -90 to 90 degrees
        roll=np.arctan(accelerometer_msg['yAcc']/np.sqrt(accelerometer_msg['xAcc']**2+accelerometer_msg['zAcc']**2))
        pitch = np.arctan(-accelerometer_msg['xAcc'] / accelerometer_msg['zAcc'])
    else: raise Exception('Unknown system') #This software supports only 'XYZ' and 'YXZ'. Accelerometer gives data only
    # for these values
    return roll,pitch

def get_yaw_from_magnetometer(magnetometer_msg):
    #https://www.nxp.com/docs/en/application-note/AN4248.pdf
    """
    This function gets yaw from magnetometer raw data.
    :param magnetometer_msg: dict with magnetometer data (keys: 'xMag', 'yMag')
    :return yaw: The yaw:
    """
    return np.arctan(-magnetometer_msg['yMag']/magnetometer_msg['xMag'])

def normalize_euler_angles(euler_angles):
    """
    This function ensures all angles are between -pi and +pi

    :param euler_angles: dict with euler angles ('roll', 'pitch', 'yaw')
    :return: None
    """
    for key in ('roll', 'pitch', 'yaw'):
        while euler_angles[key]<=np.pi:
            euler_angles[key]=euler_angles[key]+np.pi
        while euler_angles[key]>np.pi:
            euler_angles[key]=euler_angles[key]-np.pi


def initialize_euler_angles(measure_arr):
    """
    This function initializes euler angles and their rates according to raw data
    :param measure_arr: dict with raw data (keys: 'xAcc', 'yAcc', 'zAcc', 'xMag', 'yMag', 'xGyro', 'yGyro', 'zGyro')
    :return:
    """
    rot_system = 'XYZ'
    euler_angles= {'roll': (get_euler_angles_from_accelerometer(measure_arr,rot_system))[0],
                   'pitch': (get_euler_angles_from_accelerometer(measure_arr,rot_system))[1],
                   'yaw': get_yaw_from_magnetometer(measure_arr)}
    if  abs(abs(euler_angles['pitch'])-np.pi/2)<0.17: #almost 10 deg
        rot_system = 'YXZ'
        euler_angles = {'roll': (get_euler_angles_from_accelerometer(measure_arr, rot_system))[0],
                        'pitch': (get_euler_angles_from_accelerometer(measure_arr, rot_system))[1],
                        'yaw': get_yaw_from_magnetometer(measure_arr)}



    variance={'roll':copy(SENSOR_VARIANCE_MATRIX),'pitch':copy(SENSOR_VARIANCE_MATRIX),'yaw':copy(SENSOR_VARIANCE_MATRIX)}
    angles_rates=get_rates_euler_angles_from_gyroscope(measure_arr,euler_angles)
    return euler_angles,angles_rates,variance,rot_system

def update_euler_angles(measure_arr,angles_old,rates_old,variance_old,last_time_step,rot_system):
    """
    This function updates euler angles and their rates from raw data
    :param measure_arr: Raw data saved as dict with keys:(keys: 'xAcc', 'yAcc', 'zAcc', 'xMag', 'yMag', 'xGyro', 'yGyro',
     'zGyro','timestampGyro')
    :param angles_old: Previously estimated euler angles saved as dict with keys:(keys: 'roll', 'pitch', 'yaw')
    :param rates_old: Previously estimated rates of euler angles saved as dict with keys:(keys: 'roll', 'pitch', 'yaw')
    :param variance_old: Previously estimated covariance matrices saved as dict with keys:(keys: 'roll', 'pitch', 'yaw')
    :param last_time_step: int: last time a measurement was received (in ms)
    :param rot_system: "XYZ" or "YXZ
    :return:
         angles_updated: Newly estimated angles (stored in dict with keys: 'roll', 'pitch', 'yaw')
         angles_rates_updated: Newly estimated rates of angles (stored in dict with keys: 'roll', 'pitch', 'yaw')
         angles_variance_updated: Newly estimated covariance matrices (stored in dict with keys: 'roll', 'pitch', 'yaw')
         new_rot_system: "XYZ" or "YXZ
    """
    angles,rates,variance,new_rot_system=initialize_euler_angles(measure_arr)
    if not rot_system==new_rot_system: angles_old=change_euler_order(angles_old,new_rot_system)[0]
    time_diff = (measure_arr['timestampGyro'] - last_time_step) / 1000
    angles_updated,angles_rates_updated, angles_variance_updated = kalman_euler_angles(angles,rates,
                                                                angles_old,rates_old,variance_old,time_diff)
    normalize_euler_angles(angles_updated)
    return angles_updated, angles_rates_updated,angles_variance_updated,new_rot_system

def get_rates_euler_angles_from_gyroscope(measure_arr,angles):
    # https://liqul.github.io/blog/assets/rotation.pdf
    """
    This function gets rates of euler angles from gyroscope
    :param measure_arr: dict with raw data (keys: 'xGyro', 'yGyro', 'zGyro') 
    :param angles: dict with angles (keys: 'roll', 'pitch', 'yaw')
    :return direction_rate: rate of euler angles (dict with keys: 'roll', 'pitch', 'yaw')
    """
    rate_rad={}
    for key in ('xGyro', 'yGyro', 'zGyro'):
        rate_rad[key]=mdeg_to_rad(measure_arr[key])
    direction_rate= {'roll': rate_rad['xGyro'] + rate_rad['yGyro'] * np.sin(angles['roll']) * np.tan(angles['pitch']) + \
                             rate_rad['zGyro'] * np.sin(angles['roll']) * np.tan(angles['pitch']),
                     'pitch': rate_rad['yGyro'] * np.cos(angles['roll']) - rate_rad['zGyro'] * np.sin(angles['roll']),
                     'yaw': rate_rad['yGyro'] * np.sin(angles['roll']) / np.cos(angles['pitch']) + rate_rad['zGyro'] * \
                            np.cos(angles['roll']) / np.cos(angles['pitch'])}
    return direction_rate

def kalman_euler_angles(angles,rates,angles_old,rates_old,variance_old,time_diff):
    """
    :param angles: Rotation according to measured data (keys: 'roll', 'pitch', 'yaw')
    :param rates: Rates of rotation according to measured data (keys: 'roll', 'pitch', 'yaw')
    :param angles_old: Rotation according to state estimation (keys: 'roll', 'pitch', 'yaw')
    :param rates_old: Rates of rotation according to state estimation (keys: 'roll', 'pitch', 'yaw')
    :param variance_old: Numpy matrices (stored in dict with keys: 'roll', 'pitch', 'yaw') containing covariance matrices
    :param time_diff: float time difference between measurements
    :return:
         updated_angles: Newly estimated angles (stored in dict with keys: 'roll', 'pitch', 'yaw')
         updated_rates: Newly estimated rates of angles (stored in dict with keys: 'roll', 'pitch', 'yaw')
         updated_var: Newly estimated covariance matrices (stored in dict with keys: 'roll', 'pitch', 'yaw')
    """
    # Initialization
    updated_angles={}
    updated_rates={}
    updated_var={}
    transition_matrix=np.matrix([[1,time_diff],[0,1]]) #Simple model of a discrete integrator

    #Iterate for each euler angle and Kalman filter
    for key in ('roll', 'pitch', 'yaw'):
        # Predict state (state is a 2-element vector of 1 euler angle and its rate)
        state=np.array([angles_old[key],rates_old[key]])
        state=np.matmul(transition_matrix,state)
        # Update covariance matrix
        updated_var[key]=matmul3(transition_matrix,variance_old[key],np.transpose(transition_matrix))+MODEL_VARIANCE_MATRIX

        # Update state based on prediction
        kalman_gain = np.matmul(updated_var[key],np.linalg.inv(updated_var[key]+SENSOR_VARIANCE_MATRIX))
        state=state+np.transpose(np.matmul(kalman_gain,np.transpose(np.array([angles[key],rates[key]])-state)))
        updated_var[key]=matmul3((np.identity(2)-kalman_gain),updated_var[key],np.transpose(np.identity(2)-kalman_gain)) \
                         + matmul3(kalman_gain,SENSOR_VARIANCE_MATRIX,np.transpose(kalman_gain))

        # Save predicted state as a dict
        updated_angles[key]=state[0,0]
        updated_rates[key]=state[0,1]

    return updated_angles,updated_rates,updated_var

def matmul3(a,b,c):
    """
    Matrix multiplication of 3 matrices
    :param a: Numpy matrix
    :param b: Numpy matrix
    :param c: Numpy matrix
    :return: Numpy matrix
    """
    return np.matmul(np.matmul(a,b),c)

def mdeg_to_rad(mdeg):
    """
    This function transforms orientation in milidegrees to radians
    :param mdeg: milidegrees
    :return: radians
    """
    return mdeg*np.pi/180/1000

def eul_2_rot(angles,system):
    """
    This function transforms euler angles to rotation matrix according to chosen sequence
    :param angles: Euler angles saved as dict with keys:(keys: 'roll', 'pitch', 'yaw')
    :param system: 'XYZ' or 'YXZ'
    :return: Rotation matrix (Numpy matrix)
    """
    # Compute rotation matrix around each axis
    rot_x=np.matrix([[1,0,0],
                     [0,np.cos(angles['roll']),-np.sin(angles['roll'])],
                     [0,np.sin(angles['roll']),np.cos(angles['roll'])]])
    rot_y=np.matrix([[np.cos(angles['pitch']),0,-np.sin(angles['pitch'])],
                     [0,1,0],
                     [-np.sin(angles['pitch']), 0, np.cos(angles['pitch'])]])
    rot_z=np.matrix([[np.cos(angles['yaw']),-np.sin(angles['yaw']),0],
                     [np.sin(angles['yaw']),np.cos(angles['yaw']),0],
                     [0,0,1]])
    # Find final rotation matrix by using specified squander
    if system=='XYZ': return matmul3(rot_x,rot_y,rot_z)
    elif system=='YXZ': return matmul3(rot_y,rot_x,rot_z)
    else: raise NotImplementedError

def rot_2_euler(rot,system):
    # https://eecs.qmul.ac.uk/~gslabaugh/publications/euler.pdf
    """
    This function transforms rotation matrix to euler angles  according to chosen sequence
    :param rot: Rotation matrix (Numpy matrix)
    :param system: 'XYZ' or 'YXZ'
    :return: euler angles (dict with keys: 'roll', 'pitch', 'yaw')
    """
    angles={}
    if system=='XYZ':
        if abs(rot[0,2])==1: raise NotImplementedError
        else:
            #There are two ways to get a solution because there are two pairs of euler angles that creates the same rotations
            # Here, I will choose one randomly
            angles['pitch']=np.arcsin(-rot[0,2])
            angles['roll'] = np.arctan2(-rot[1, 2] / np.cos(angles['pitch']), rot[2, 2] / np.cos(angles['pitch']))
            angles['yaw']=np.arctan2(-rot[0,1]/np.cos(angles['pitch']),rot[0,0]/np.cos(angles['pitch']))

    elif system=='YXZ':
        if abs(rot[1,2])==1: raise NotImplementedError
        else:
            angles['roll']=np.arcsin(rot[1,2])
            angles['pitch']=np.arctan2(-rot[0, 2] / np.cos(angles['roll']), rot[2, 2] / np.cos(angles['roll']))
            angles['yaw'] = np.arctan2(-rot[1, 0] / np.cos(angles['roll']), rot[1, 1] / np.cos(angles['roll']))

    else: raise NotImplementedError
    return angles

def change_euler_order(angles,system):
    """
    This function changes the order of euler angles (from 'XYZ' to 'YXZ' ot from 'YXZ' to 'XYZ')
    :param angles: Euler angles saved as dict with keys: 'roll', 'pitch', 'yaw'
    :param system: Current sequence (to be changed) 'XYZ' or 'YXZ'
    :return:
            new_angles: Transformed euler angles saved as dict with keys: 'roll', 'pitch', 'yaw'
            new_system: system for new transformed euler angles
    """
    rot = eul_2_rot(angles,system)
    if system=='XYZ': new_system='YXZ'
    elif system=='YXZ': new_system='XYZ'
    else: raise NotImplementedError
    new_angles=rot_2_euler(rot,new_system)
    return new_angles, new_system
