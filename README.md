# cloneRobotics

# How to use?

First, look at the dependencies. This software was only tested for one version of each package, Python, and OS, but it is likely to work with other versions. In real life, it would need to be more tested.

To run the server, open the console in the project directory and use the "python3 pub.py" command. This command runs the server with default settings. To change settings, it is possible to open software with named arguments. To add named arguments (i.e. change default settings), you need to add after the command argument following text " --$1=$2 ", where "$1" has to be replaced with the name of the setting and "$2" has to be replaced with the chosen value of the setting. Note, you can change multiple settings.

Possible arguments are "socket-path", "log-level" and "frequency-hz". "socket-path" represents a path where a socket should be created. Both server and client should use the same value. The default value is "/tmp/my_socket". "log-level" specifies the logging level. The higher the level the fewer logs will be created. Possible values are: 'NOTSET'->(0), 'DEBUG'->(10), 'INFO'->(20), 'WARNING'->(30), 'ERROR'->(40), 'CRITICAL'->(50). The default value is 'INFO'. "frequency-hz" specifies how often messages should be sent. It must be a positive number. The default value is 500. If any value is incorrect, the software uses a default value and prints this information in the command window. 

Running client works almost exactly the same but the command is "python3 sub.py" and there is no "frequency-hz" name because the client works as often as the server sends messages. Instead, there is a "timeout-ms" argument that shows how long clients should wait for a massage in milliseconds. If a message is not received, the client shuts down. The default argument is 100.

# How does the software work?

The software creates connections between the server and the client by using Unix sockets. The logger object creates logs for the server (in "logs_server") and client (in "logs_clients") in a file named after the time when the software started to be running. Logs include, among others, sent messages, information if there is a connection, or estimated Euler angles. Note, that the server makes logs even if it is not connected to the client.

The server reads random measurements from sensors. The measurements are serialized and sent to the client. The client uses them to estimate Euler angles in sequence "XYZ" and their rates. If the message is got for the first time, the software initializes the new Euler angles and their rates as a "state" for a Kalman filter with high variance. Then, for each new message, Kalman filtering is used to update the state. The updated Euler angles are used to compute quaternion.

Gimbal lock happens when the middle axis in the sequence ("Y" in our case) rotates in such a way other axes rotate around the same axis. In this case, it happens when Y rotates around -90deg or 90deg. In a case when rotation in "Y" approaches 90deg, the system of Euler angles is transformed into a sequence "YXZ". 

Note that gimbal lock can't happen simultaneously in two sequences (at least if sensors work correctly and the measurements are sent frequently which I assume would happen in real life). According to [1], we always get at least two solutions for Euler angles. We can restrict the middle one (in our case the rotation around "Y") to be between -90 to 90 deg. The rotation around Y in "XYZ" is calculated with atan(-Xacc/sqrt(Yacc^2+Zacc^2)) where "Xacc", "Yacc" and "Zacc" are readings of the accelerometer. As we can see, the lock can happen only when the value inside atan function goes to infinity or - infinity which happens only when abs(Xacc)>>abs(Yacc). In the "YXZ" sequence with a constraint on the rotation of "X" to be between -90 to 90 deg, the rotation around X is equal to atan(Yacc/sqrt(Xacc^2+Zacc^2)) which means lock can only happen if bs(Xacc)<<abs(Yacc). Note we use only "XYZ" and "YXZ" because according to [1], these are the only sequences where rotations can be calculated with an accelerometer without a magnetometer. It is important that rotations around "X" and "Y" still be calculated in case the magnetometer stops working.


# My changes and assumptions

Regarding the measurements, I assumed the random variables are all between -1 to 1 (as shown by references, such measurements are possible from a physical point of view, but it depends on what system we want to measure) however software was written with measurements that make sense instead of random values. Moreover, there is a constant part in the accelerometer's measurement on the z-axis. There was no unit for the accelerometer so I assumed it is m/s^2. Gyroscope measurements are supposed to be integers but it is not consistent with an example so I used floats instead. As there is no typedef in Python, I used "dict" instead and the pickle library to serialize the data.

There is no information that log level should be configurable accoridng to the instructions but it is part of the example so I added it anyway. 

"Euler angles/quaternions" is not clear if it means ""eauler angles and quaternions" or "eauler angles or quaternions". I assumed the former.

# Dependencies

Python 3.10.12
Ubuntu 22.04
Numpy 1.23.5


# References

[1] Procedure to calculate Euler angles (roll and pitch) from accelerometer's raw measurements https://www.nxp.com/docs/en/application-note/AN3461.pdf

[2] Equations to transform rotation matrix to Quaternion https://www.euclideanspace.com/maths/geometry/rotations/conversions/matrixToQuaternion/

[3] Procedure to calculate yaw from magnetometer's raw data https://www.nxp.com/docs/en/application-note/AN4248.pdf

[4] Procedure to calculate rates of angles from gyroscope https://liqul.github.io/blog/assets/rotation.pdf

[5] Equations to transform rotation matrix to Euler angles https://eecs.qmul.ac.uk/~gslabaugh/publications/euler.pdf 

[6] An example that shows that the upper bound of gyroscope measurements is possible https://mavicpilots.com/threads/angular-speed.76807/

[7] An example that shows that upper bound magnetometer mearuemnts are possible https://sensysmagnetometer.com/products/magdrone-r3-magnetometer-for-drone/


# Possible extensions

There are still a lot ways how to imrpove this software. In this section, I will list some of them:

1. There should be unit tests (e.g. with Pytest) implemented
2. The simple Kalman filter was created but in real-world, I think there should be 2 more extensions implmented.
2.1 I implemented the Kalman filter under the assumption that the measured states are affected by Gaussian noise. Even if the measurements are affected by Gaussian Noise, the sensors do not measure states directly. Instead, we need to propagate raw data through nonlinear functions which means that even if the original raw measurements were affected by Gaussian Noise, the states are affected by non-Guassian Noise. To consider it, an algorithm created for a nonlinear system (e.g. UKF) should be used instead.
2.2 I assumed a very simple model for the system (integrator in 3 dirmensiosn). In real world, I would try to find more accurate model, to raise accuracy of prediction part of the filter.
3. I chose R and Q matrices for Kalman filtering randomly. In real-world, I would try to find them in documenation (or another source) or tune them if they are aviable. If it is not possible (e.g. noises change over time), I would conisde a different filter (e.g. UFIR). 
4. There should be implemented an algorithm to deal with random outliers. I was unable to do it here because (in this toy example) all measurements are outliers.

