# Two Wheel (Python 3)
# Author: John Ly (jtl222), Carlos Gutierrez (cag334)
# Date: December 17, 2020

# Purpose: Sets up two motors with the motor controller and uses piTFT buttons to control 
# motors for CW, CCW, and STOP
# Includes inital setup parameters and functions only

import RPi.GPIO as GPIO
import time
from collections import namedtuple
from enum import Enum
from recordtype import recordtype


# set pin naming convention to the Broadcom (BCM) convention
GPIO.setmode(GPIO.BCM)

########################
#-- BUTTON OPERATION --#
########################

# array corresponds to the available buttons on the piTFT by GPIO numbering
piTFT_Buttons = [17, 22, 23, 27]

# # on pin interrupt signal, handle motor functions
# def GPIO_callback(channel):
#     for pin in piTFT_Buttons:
#         if (not GPIO.input(pin)):
#             print("falling edge detected on {}".format(pin))
#             servo(buttonControls[pin][0],buttonControls[pin][1])

# # setup for all piTFT buttons as inputs using pull up resistors
# print("setting up piTFT buttons")
# for pin in piTFT_Buttons:
#     GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#     print("GPIO {} setup".format(pin))
#     GPIO.add_event_detect(pin, GPIO.FALLING, callback=GPIO_callback, bouncetime=300)


#######################
#-- MOTOR OPERATION --#
#######################

# Class for logging data
Data = recordtype("Data", ['state','time'])

# Motor Class containing information and setup for each new motor object
class Motor:

    def __init__(self, In1, In2, PWM_pin):
        self.In1 = In1
        self.In2 = In2
        self.PWM_pin = PWM_pin
        freq = 50 # default motor response rate of 50 Hz
        print("Motor assigned to GPIO {}, {}, {}".format(In1,In2,PWM_pin))
        for pin in self.pinList():
            GPIO.setup(pin, GPIO.OUT)
            print("GPIO {} setup".format(pin))
        self.PWM = GPIO.PWM(self.PWM_pin, freq)
        print("PWM instance started on GPIO {}".format(self.PWM_pin))
        self.currState = MotorState.STOP
        self.history = []

    def pinList(self):
        return [self.In1, self.In2, self.PWM_pin]

    # updates motor history of states, maintains length of history
    def updateHistory(self, Log: 'Data'):
        self.history.append(Log)
        if len(self.history) > 3:
            self.history.pop(0)    


# Motor States: STOP, CW, CCW, BRAKE
# controls logic level for motor control input pins
class MotorState(namedtuple('MotorState', 'In1 In2'), Enum):
    STOP = (0,0)
    CW = (1,0)
    CCW = (0,1)
    BRAKE = (1,1)
    def __str__(self) -> str:
        return self.name
            
# create and setup Motor objects
motorA = Motor(4,5,26)
motorB = Motor(20,21,16)
motorTuple = (motorA,motorB)

# Dictates motor state and adjusts motor control pins accordingly
# Parameters: 
#   motor: Motor to be controlled | motorA(left) or motorB(right)
#   direction: spin state of motor | MotorState. STOP, CW, CCW, BRAKE
#       additional option "REVERSE" to toggle between CW and CCW
def servo(motor: 'Motor', direction: 'MotorState', duty: "int" = 75):
    motor.currState = direction # update state in motor class
    motor.PWM.ChangeDutyCycle(duty)
    GPIO.output(motor.In1, direction[0])
    GPIO.output(motor.In2, direction[1])
    motor.updateHistory(Data(str(motor.currState),str(int(time.time()-startTime))))
    print("{}: {}".format(motor,motor.currState.name))

# test sequence to test motor operation
def drive(direction: 'string', speedL: "int" =75, speedR: "int" =75):
    # Stop by default
    # servo(motorA, MotorState.STOP)
    # servo(motorB, MotorState.STOP)
    if direction is "forward":
        servo(motorA, MotorState.CCW, speedL)
        servo(motorB, MotorState.CW, speedR)
    elif direction is "backward":
        servo(motorA, MotorState.CW, speedL)
        servo(motorB, MotorState.CCW, speedR)  
    elif direction is "left":
        servo(motorA, MotorState.CW, speedL)
        servo(motorB, MotorState.CW, speedR)  
    elif direction is "right":
        servo(motorA, MotorState.CCW, speedL)
        servo(motorB, MotorState.CCW, speedR)  
    else:
        servo(motorA, MotorState.STOP)
        servo(motorB, MotorState.STOP)

##################
#-- CODE START --#
##################

startTime = time.time()

# initialize servo state to stop
servo(motorA, MotorState.STOP)
servo(motorB, MotorState.STOP)
# create PWM objects for speed control and initialize duty ratio
duty = 75
motorA.PWM.start(duty)
motorB.PWM.start(duty)


