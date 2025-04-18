import os
import sys
import time
from ctypes import *
import paho.mqtt.client as paho
import MotionControl3 as MC

broker="labstream.ucsd.edu"

MOTOR_SERIAL_NUMS = [b"27262362"]
current_state = -3
#define callback
def on_message(client, userdata, message):
    global current_state
    time.sleep(1)
    print("received message =",str(message.payload.decode("utf-8")))
    print("message topic =", str(message.topic))
    if str(message.topic) == "filter_motor":
        if current_state != int(message.payload.decode("utf-8")):
            current_state = int(message.payload.decode("utf-8"))
        #MC.Thorlabs_Motor(serial_n=MOTOR_SERIAL_NUMS[0], motor_state=int(message.payload.decode("utf-8")), lib=userdata)


if sys.version_info < (3, 8):
    os.chdir(r"C:\Program Files\Thorlabs\Kinesis")
else:
    os.add_dll_directory(r"C:\Program Files\Thorlabs\Kinesis")

lib: CDLL = cdll.LoadLibrary("Thorlabs.MotionControl.KCube.DCServo.dll")



client= paho.Client(transport="websockets") #create client object client1.on_publish = on_publish #assign function to callback client1.connect(broker,port) #establish connection client1.publish("house/bulb1","on")
######Bind function to callback
client.on_message=on_message
client.user_data_set(current_state)
#####
print("connecting to broker ",broker)
client.connect(broker, 9001)#connect
for motor in MOTOR_SERIAL_NUMS:
    MC.createMotor(motor, lib)
client.loop_start() #start loop to process received messages
print("subscribing ")
client.subscribe([("filter_motor", 2), ("image_motor", 2)])#subscribe
time.sleep(2)
print("publishing ")
client.publish("filter_mount_done","3")#publish
time.sleep(1)

current_local_time = time.localtime()
try:
    while current_local_time.tm_hour <= 1 and current_state != -5:
    #if current_local_time.tm_hour >= 22:
        print(current_state)
        time.sleep(0.1)
        current_local_time = time.localtime()
        MC.Thorlabs_Motor(serial_n=MOTOR_SERIAL_NUMS[0], motor_state=current_state, lib=lib)
        #print("hey")
        
except  KeyboardInterrupt:
    print("Keyboard")

    
print("Shutdown time")
for motor in MOTOR_SERIAL_NUMS:
    MC.closeMotor(motor, lib)
client.disconnect() #disconnect
client.loop_stop() #stop loop