import numpy as np
from copy import copy
#I choose random values. These values should be found in documentation or in an exepriment. If it is not possible to
# find them, another filter (e.g. UFIR) should be used
MODEL_VARIANCE_MATRIX=np.diag([5,0.1])
SENSOR_VARIANCE_MATRIX=np.diag([10,1])

def euler_to_quanternion(euler_angles,system):
    """
    Convert an Euler angle to a quaternion.

    Input
      :param roll: The roll (rotation around x-axis) angle in radians.
      :param pitch: The pitch (rotation around y-axis) angle in radians.
      :param yaw: The yaw (rotation around z-axis) angle in radians.

    Output
      :return qx, qy, qz, qw: The orientatios,bmcn in quaternion [x,y,z,w] format
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
    elif system=='YXZ': #I was unable to find transfomration from this system to quanternion, so I used rotation matrix
        # as an intermidate step
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
    #https://www.nxp.com/docs/en/application-note/AN3461.pdf
    if rot_system == 'XYZ':
        roll=np.arctan(accelerometer_msg['yAcc']/accelerometer_msg['zAcc'])
        pitch=np.arctan(-accelerometer_msg['xAcc']/np.sqrt(accelerometer_msg['yAcc']**2+accelerometer_msg['zAcc']**2))
    elif rot_system == 'YXZ':
        roll=np.arctan(accelerometer_msg['yAcc']/np.sqrt(accelerometer_msg['xAcc']**2+accelerometer_msg['zAcc']**2))
        pitch = np.arctan(-accelerometer_msg['xAcc'] / accelerometer_msg['zAcc'])
    else: raise Exception('Unknown system')
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
    rot_system = 'XYZ'
    euler_angles= {'roll': (get_euler_angles_from_accelerometer(measure_arr,rot_system))[0],
                   'pitch': (get_euler_angles_from_accelerometer(measure_arr,rot_system))[1],
                   'yaw': get_yaw_from_magnetometer(measure_arr,rot_system)}
    if  abs(abs(euler_angles['pitch']-np.pi/2))<0.17: #almost 10 deg
        rot_system = 'YXZ'
        euler_angles = {'roll': (get_euler_angles_from_accelerometer(measure_arr, rot_system))[0],
                        'pitch': (get_euler_angles_from_accelerometer(measure_arr, rot_system))[1],
                        'yaw': get_yaw_from_magnetometer(measure_arr, rot_system)}



    variance={'roll':copy(SENSOR_VARIANCE_MATRIX),'pitch':copy(SENSOR_VARIANCE_MATRIX),'yaw':copy(SENSOR_VARIANCE_MATRIX)}
    angles_rates=get_euler_angles_from_gyroscope(measure_arr,euler_angles)
    return euler_angles,angles_rates,variance,rot_system

def update_euler_angles(measure_arr,angles_old,rates_old,varaince_old,last_time_step,rot_system):
    angles,rates,variance,new_rot_system=initialize_euler_angles(measure_arr)
    if not rot_system==new_rot_system: angles_old=change_euler_order(angles_old,new_rot_system)[0]
    time_diff = (measure_arr['timestampGyro'] - last_time_step) / 1000
    angles_updated,angles_rates_updated, angles_variance_updated = kalman_euler_angles(angles,rates,variance,
                                                                angles_old,rates_old,varaince_old,time_diff)
    normalize_euler_angles(angles_updated)
    return angles_updated, angles_rates_updated,angles_variance_updated

    #We assume that measurments are uncolarted so we can do this sequnatially
    # https://math.stackexchange.com/questions/4011815/kalman-filtering-processing-all-measurements-together-vs-processing-them-sequen
    # OTherwise, we would need to implment them toghether


    # A simple example how kalman filter works for 1-dimensional stats
    # I worked under assumption each angle is measured but it is not true. In real-world, UKF should be used. Moreover,
    # in such a case, varaince woulf be coupled so it would be required to use matricies instead of scalar values. It would
    # also be required to use matrcies if model was avaiable.

def get_euler_angles_from_gyroscope(measure_arr,angles):
    # https://liqul.github.io/blog/assets/rotation.pdf
    # Note: Integration could be  improved with Runge-Kutta 4 instead of Euler method
    rate_rad={}
    for key in ('xGyro', 'yGyro', 'zGyro'):
        rate_rad[key]=mdeg_to_rad(measure_arr[key])
    direction_rate= {'roll': rate_rad['xGyro'] + rate_rad['yGyro'] * np.sin(angles['roll']) * np.tan(angles['pitch']) + \
                             rate_rad['zGyro'] * np.sin(angles['roll']) * np.tan(angles['pitch']),
                     'pitch': rate_rad['yGyro'] * np.cos(angles['roll']) - rate_rad['zGyro'] * np.sin(angles['roll']),
                     'yaw': rate_rad['yGyro'] * np.sin(angles['roll']) / np.cos(angles['pitch']) + rate_rad['zGyro'] * \
                            np.cos(angles['roll']) / np.cos(angles['pitch'])}
    return direction_rate

    #time_diff=(measure_arr['timestampGyro']-last_time_step)/1000
    #euler_angles={'roll':roll_rate*time_diff+angles['roll'],'pitch':pitch_rate*time_diff+angles['pitch'],\
    #                         'yaw':yaw_rate*time_diff+angles['yaw']}


    # It would be better to treat system as each angle would be described by 2 states: angle and rate. It would let us
    # use infomration that even though we know rate, its integration does not neecraily tell us correctly angle

def kalman_euler_angles(angles,rates,variance,angles_old,rates_old,varaince_old,time_diff):
    updated_state={}
    updated_rates={}
    updated_var={}
    transition_matrix=np.matrix([[1,time_diff],[0,1]])
    for key in ('roll', 'pitch', 'yaw'):
        state=np.array([angles_old[key],rates_old[key]])
        state=np.matmul(transition_matrix,state)
        updated_var[key]=matmul3(transition_matrix,varaince_old[key],np.transpose(transition_matrix))+MODEL_VARIANCE_MATRIX

        kalman_gain = np.matmul(updated_var[key],np.linalg.inv(updated_var[key]+SENSOR_VARIANCE_MATRIX))
        state=state+np.transpose(np.matmul(kalman_gain,np.transpose(np.array([angles[key],rates[key]])-state)))
        updated_var[key]=matmul3((np.identity(2)-kalman_gain),updated_var[key],np.transpose(np.identity(2)-kalman_gain)) \
                         + matmul3(kalman_gain,SENSOR_VARIANCE_MATRIX,np.transpose(kalman_gain))

        updated_state[key]=state[0,0]
        updated_rates[key]=state[0,1]

    return updated_state,updated_rates,updated_var

def matmul3(a,b,c):
    return np.matmul(np.matmul(a,b),c)

def mdeg_to_rad(mdeg):
    return mdeg*np.pi/180/1000

def eul_2_rot(angles,system):
    rot_x=np.matrix([[1,0,0],
                     [0,np.cos(angles['roll']),-np.sin(angles['roll'])],
                     [0,np.sin(angles['roll']),np.cos(angles['roll'])]])
    rot_y=np.matrix([[np.cos(angles['pitch']),0,-np.sin(angles['pitch'])],
                     [0,1,0],
                     [-np.sin(angles['pitch']), 0, np.cos(angles['pitch'])]])
    rot_z=np.matrix([[np.cos(angles['yaw']),-np.sin(angles['yaw']),0],
                     [np.sin(angles['yaw']),np.cos(angles['yaw']),0],
                     [0,0,1]])
    if system=='XYZ': return matmul3(rot_x,rot_y,rot_z)
    elif system=='YXZ': return matmul3(rot_y,rot_x,rot_z)
    else: raise NotImplementedError

def rot_2_euler(rot,system):
    # https://eecs.qmul.ac.uk/~gslabaugh/publications/euler.pdf
    # Check special cases I work under assumptios there are
    # Gimbal lock will not happen (under aumptions sensors work correctly) because XYZ gimbal lock happens when
    # abs(Gpx)>>abs(Gpy) or it is opposite for YXZ
    # Software requires unit tests
    # Software can be rewriiten with ojbects in mind if many exentsions are required
    angles={}
    if system=='XYZ':
        if abs(rot[0,2])==1: raise NotImplementedError
        else:
            #There are two ways to get a solution becaucse there are two pairs of euler anges that creates the same rotations
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

def change_euler_order(angles,system):
    # We work with -pi/2 to pi/2 because of sensors anyway
    rot = eul_2_rot(angles,system)
    if system=='XYZ': new_system='YXZ'
    elif system=='YXZ': new_system='XYZ'
    else: raise NotImplementedError
    new_angles=rot_2_euler(rot,new_system)
    return new_angles, new_system
