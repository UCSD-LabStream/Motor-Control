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


def main():
    """
    main():
    ------

    Performs all actions of the KDC101
    :return: None
    """

    if sys.version_info < (3, 8):
        os.chdir(r"C:\Program Files\Thorlabs\Kinesis")
    else:
        os.add_dll_directory(r"C:\Program Files\Thorlabs\Kinesis")

    lib: CDLL = cdll.LoadLibrary("Thorlabs.MotionControl.KCube.DCServo.dll")

    # Uncomment this line if you are using simulations
    #lib.TLI_InitializeSimulations()

    # Set constants
    serial_num = c_char_p(b"27262362")

    # Open the device
    if lib.TLI_BuildDeviceList() == 0:
        lib.CC_Open(serial_num)
        lib.CC_StartPolling(serial_num, c_int(200))

        # Home the device
        lib.CC_Home(serial_num)
        time.sleep(1)

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
        while True:
            #get user input for rotation amount
            current_local_time = time.localtime()
            if current_local_time.tm_hour >= 24:
                break
            # Replace with your API endpoint
           
            data = 0
            try:
                # Send a GET request
                response = requests.get(GET_URL)

                # Check if the request was successful
                if response.status_code == 200:
                    # Parse the JSON response if applicable
                    data = response.json()
                    print("Value retrieved:", data)  # Replace 'your_key' with the actual key
                else:
                    print(f"Failed to retrieve data: {response.status_code} - {response.text}")
                    continue
            except requests.RequestException as e:
                print(f"An error occurred: {e}")
            
            user_input = int(data) #not sure this is how it works, need to characterize the motor
            if user_input  < -2 or user_input > 2 or user_input is not int or user_input == 0: 
                time.sleep(1000)
                continue
            # set a new speed and direction
            motor_direction = 1
            motor_speed = 0
            if user_input <=0: 
                #reverse
                motor_direction = 2
            else: 
                #forward
                motor_direction = 1
            if abs(user_input) == 2: 
                #fast
                motor_speed = 1.75
            else: 
                #slow speed
                motor_speed = 0.25
            

            dev_pos1 = c_int(lib.CC_GetPosition(serial_num))
            real_pos = c_double()
            lib.CC_GetRealValueFromDeviceUnit(serial_num,
                                           dev_pos1,
                                           byref(real_pos),
                                           0)
            #user_input = real_pos.value + 10
            
            new_pos_dev = c_int()
            lib.CC_GetDeviceUnitFromRealValue(serial_num,
                                        new_pos_real,
                                        byref(new_pos_dev),
                                        0)
            
            print(f'{new_pos_real.value} in Device Units: {new_pos_dev.value}')
        
            response = requests.post(IN_PROGRESS_URL)
            # print(response.status_code)
            while(not response.status_code == 200):
                response = requests.post(IN_PROGRESS_URL)
            print("finished sending response")

            new_jog_dev = c_int()
            lib.CC_GetDeviceUnitFromRealValue(serial_num,
                                        c_double(motor_speed),
                                        byref(new_jog_dev),
                                        0)
            # Move to new position as an jog move (incremental).
            lib.CC_SetJogStepSize(serial_num, new_jog_dev)
            time.sleep(0.25)
            print("hey")
            x = 12 if motor_speed == 1.75 else x = 83
            while(x > 0):
                print("jogging")
                lib.CC_MoveJog(serial_num, motor_direction)
                time.sleep(0.95)
                dev_pos1 = c_int(lib.CC_GetPosition(serial_num))
                real_pos = c_double()
                lib.CC_GetRealValueFromDeviceUnit(serial_num,
                                        dev_pos1,
                                        byref(real_pos),
                                        0)
                if real_pos.value > 20.7:
                    break
                x-=1
            #lib.CC_MoveAbsolute(serial_num)
            dev_pos1 = c_int(lib.CC_GetPosition(serial_num))
            real_pos = c_double()
            lib.CC_GetRealValueFromDeviceUnit(serial_num,
                                        dev_pos1,
                                        byref(real_pos),
                                        0)
            print(real_pos.value)
            print("finished moving")

            # response = requests.post(DONE_URL)
            # while(not response.status_code == 200):
            #     response = requests.post(DONE_URL)
            
        # time.sleep(0.75)
        #reset position when done
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

    return


if __name__ == "__main__":
    main()