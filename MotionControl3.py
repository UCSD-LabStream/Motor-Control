import time
import os
import sys
from ctypes import *
import requests

IN_PROGRESS_URL = "http://13.57.216.198/motor_state/1/in_progress"
DONE_URL = "http://13.57.216.198/motor_state/1/done"
GET_URL =  "http://13.57.216.198/get_gears/1"
GET_SPEED_URL = "http://13.57.216.198/" #need to implement --> gives the steps per revolution
GET_STOP_URL = "http://13.57.216.198/" #need to implement --> if the user triggers the faster speed, this stops the motor, otherwise it will keep running

def createMotor(serial_n, lib):
    # if sys.version_info < (3, 8):
    #     os.chdir(r"C:\Program Files\Thorlabs\Kinesis")
    # else:
    #     os.add_dll_directory(r"C:\Program Files\Thorlabs\Kinesis")

    # lib: CDLL = cdll.LoadLibrary("Thorlabs.MotionControl.KCube.DCServo.dll")

    # Uncomment this line if you are using simulations
    #lib.TLI_InitializeSimulations()

    # Set constants
    serial_num = c_char_p(serial_n)

    # Open the device
    if lib.TLI_BuildDeviceList() == 0:
        lib.CC_Open(serial_num)
        lib.CC_StartPolling(serial_num, c_int(200))

        sleepTimerCounter = 0
        sleepTime = 5

        # Home the device
        home(serial_n, lib)
        # lib.CC_Home(serial_num)
        # time.sleep(10)

        # Set up the device to convert real units to device units
        STEPS_PER_REV = c_double(20000.00)  # for the PRM1-Z8
        STEPS_PER_DEGREE = 2000.00/360.00
        gbox_ratio = c_double(1.0)  # gearbox ratio
        pitch = c_double(1.0)

        # Apply these values to the device
        lib.CC_SetMotorParamsExt(serial_num, STEPS_PER_REV, gbox_ratio, pitch)

        # Get the device's current position in dev units
        lib.CC_RequestPosition(serial_num)
        time.sleep(0.2)
        dev_pos = c_int(lib.CC_GetPosition(serial_num))
        # Convert device units to real units
        real_pos = c_double()
        lib.CC_GetRealValueFromDeviceUnit(serial_num,
                                          dev_pos,
                                          byref(real_pos),
                                          0)

        print(f'Position after homing: {real_pos.value}')
        if not real_pos.value > 0:
            new_pos_real = c_double(0)  # in real units

            lib.CC_SetMoveAbsolutePosition(serial_num, dev_pos)
            time.sleep(0.25)
            lib.CC_MoveAbsolute(serial_num)
        return True
    else:
        print("returning false")
        return False 
    
def home(serial_n, lib):
    serial_num = c_char_p(serial_n)

    # Open the device
    if lib.TLI_BuildDeviceList() == 0:
        lib.CC_Open(serial_num)
        lib.CC_StartPolling(serial_num, c_int(200))

        sleepTimerCounter = 0
        sleepTime = 5

        # Set up the device to convert real units to device units
        STEPS_PER_REV = c_double(20000.00)  # for the PRM1-Z8
        STEPS_PER_DEGREE = 2000.00/360.00
        gbox_ratio = c_double(1.0)  # gearbox ratio
        pitch = c_double(1.0)

        # Apply these values to the device
        lib.CC_SetMotorParamsExt(serial_num, STEPS_PER_REV, gbox_ratio, pitch)

        # Get the device's current position in dev units
        lib.CC_RequestPosition(serial_num)
        time.sleep(0.2)
        dev_pos = c_int(lib.CC_GetPosition(serial_num))
        # Convert device units to real units
        real_pos = c_double()
        lib.CC_GetRealValueFromDeviceUnit(serial_num,
                                          dev_pos,
                                          byref(real_pos),
                                          0)

        # Home the device
        lib.CC_Home(serial_num)
        if real_pos.value < 7.5:
            print("sleeping for 15")
            time.sleep(15)
        else:
            time.sleep(min(28, float(real_pos.value) * 2.0))
    

def Thorlabs_Motor(serial_n, motor_state, lib):
    """
    main():
    ------

    Performs all actions of the KDC101
    :return: None
    """

    # if sys.version_info < (3, 8):
    #     os.chdir(r"C:\Program Files\Thorlabs\Kinesis")
    # else:
    #     os.add_dll_directory(r"C:\Program Files\Thorlabs\Kinesis")

    # lib: CDLL = cdll.LoadLibrary("Thorlabs.MotionControl.KCube.DCServo.dll")

    # Uncomment this line if you are using simulations
    #lib.TLI_InitializeSimulations()

    # Set constants
    serial_num = c_char_p(serial_n)

    print("setting speed")
    # set a new speed and direction
    motor_direction = 1
    motor_speed = 0
    if motor_state <=0: 
        #reverse
        motor_direction = 1
    else: 
        #forward
        motor_direction = 2
    if abs(motor_state) == 2: 
        #fast
        motor_speed = 1.75
    elif abs(motor_state) == 1: 
        #slow speed
        motor_speed = 0.25
            

    dev_pos1 = c_int(lib.CC_GetPosition(serial_num))
    real_pos = c_double()
    lib.CC_GetRealValueFromDeviceUnit(serial_num,
                                    dev_pos1,
                                    byref(real_pos),
                                    0)
    #user_input = real_pos.value + 10
            
    # new_pos_dev = c_int()
    # lib.CC_GetDeviceUnitFromRealValue(serial_num,
    #                             new_pos_real,
    #                             byref(new_pos_dev),
    #                             0)
    
    # print(f'{new_pos_real.value} in Device Units: {new_pos_dev.value}')



    new_jog_dev = c_int()
    lib.CC_GetDeviceUnitFromRealValue(serial_num,
                                c_double(motor_speed),
                                byref(new_jog_dev),
                                0)
    # Move to new position as an jog move (incremental).
    lib.CC_SetJogStepSize(serial_num, new_jog_dev)
    time.sleep(0.25)
    print("hey")
    dev_pos1 = c_int(lib.CC_GetPosition(serial_num))
    real_pos = c_double()
    lib.CC_GetRealValueFromDeviceUnit(serial_num,
                            dev_pos1,
                            byref(real_pos),
                            0)
    if motor_direction == 2: 
        if real_pos.value < 20.7:
            print("jogging")
            lib.CC_MoveJog(serial_num, motor_direction)
            time.sleep(1.65)
    elif motor_direction == 1: 
        if real_pos.value > -0.1:
            print("jogging back")
            lib.CC_MoveJog(serial_num, motor_direction)
            time.sleep(1.65)
    
    #lib.CC_MoveAbsolute(serial_num)
    dev_pos1 = c_int(lib.CC_GetPosition(serial_num))
    real_pos = c_double()
    lib.CC_GetRealValueFromDeviceUnit(serial_num,
                                dev_pos1,
                                byref(real_pos),
                                0)
    print("new Pos: " + str(real_pos.value))
    if real_pos.value > 20.4 and motor_direction == 2:
        return (1, real_pos.value)
    
    elif real_pos.value < -0.1 and motor_direction == 1:
        return (2, real_pos.value)
    print("finished moving")

        # response = requests.post(DONE_URL)
        # while(not response.status_code == 200):
        #     response = requests.post(DONE_URL)
        
    # time.sleep(0.75)
    #reset position when done
    

    return (0, real_pos.value)


def closeMotor(serial_n, lib):
    # if sys.version_info < (3, 8):
    #     os.chdir(r"C:\Program Files\Thorlabs\Kinesis")
    # else:
    #     os.add_dll_directory(r"C:\Program Files\Thorlabs\Kinesis")

    # lib: CDLL = cdll.LoadLibrary("Thorlabs.MotionControl.KCube.DCServo.dll")

    # Uncomment this line if you are using simulations
    #lib.TLI_InitializeSimulations()

    # Set constants
    serial_num = c_char_p(serial_n)

    new_pos_real = c_double(0)  # in real units
    new_pos_dev = c_int()
    lib.CC_GetDeviceUnitFromRealValue(serial_num,
                                    new_pos_real,
                                    byref(new_pos_dev),
                                    0)

    # Move to new position as an absolute move.
    lib.CC_SetMoveAbsolutePosition(serial_num, new_pos_dev)
    time.sleep(0.25)
    lib.CC_MoveAbsolute(serial_num)

    # Close the device
    lib.CC_Close(serial_num)
    #lib.TLI_UninitializeSimulations()


# if __name__ == "__main__":
#     main()