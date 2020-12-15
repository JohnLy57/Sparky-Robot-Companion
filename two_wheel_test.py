# Two Wheel (Python 3)
# Author: John Ly (jtl222), Carlos Gutierrez (cag334)
# Lab 3: October 30, 2020

# Purpose: Sets up two motors with the motor controller and uses piTFT buttons 
# to control motors for CW, CCW, and STOP

import RPi.GPIO as GPIO
import time
from collections import namedtuple
from enum import Enum

# set pin naming convention to the Broadcom (BCM) convention
GPIO.setmode(GPIO.BCM)

########################
#-- BUTTON OPERATION --#
########################

# array corresponds to the available buttons on the piTFT by GPIO numbering
piTFT_Buttons = [17, 22, 23, 27]

# on pin interrupt signal, handle motor functions
def GPIO_callback(channel):
    for pin in piTFT_Buttons:
        if (not GPIO.input(pin)):
            print("falling edge detected on {}".format(pin))
            servo(buttonControls[pin][0],buttonControls[pin][1])

# setup for all piTFT buttons as inputs using pull up resistors
print("setting up piTFT buttons")
for pin in piTFT_Buttons:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("GPIO {} setup".format(pin))
    GPIO.add_event_detect(pin, GPIO.FALLING, callback=GPIO_callback, bouncetime=300)


#######################
#-- MOTOR OPERATION --#
#######################

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
    def pinList(self):
        return [self.In1, self.In2, self.PWM_pin]

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
def servo(motor: 'Motor', direction: 'MotorState'):
    if direction in MotorState:
        motor.currState = direction # update state in motor class
        GPIO.output(motor.In1, direction[0])
        GPIO.output(motor.In2, direction[1])
    # special case due to only having 4 buttons
    if direction is "REVERSE":
        # default to CW from STOP
        if motor.currState is MotorState.STOP or motor.currState is MotorState.CCW:
            motor.currState = MotorState.CW
            GPIO.output(motor.In1, MotorState.CW[0])
            GPIO.output(motor.In2, MotorState.CW[1])
        elif motor.currState is MotorState.CW:
            motor.currState = MotorState.CCW
            GPIO.output(motor.In1, MotorState.CCW[0])
            GPIO.output(motor.In2, MotorState.CCW[1])

    print("{}: {}".format(motor,motor.currState.name))

# dictionary connecting the button values to predetermined motor commands
buttonControls = {17:(motorA, MotorState.STOP), 22:(motorA, 'REVERSE'), 23:(motorB, MotorState.STOP), 27:(motorB, 'REVERSE')}


##################
#-- CODE START --#
##################

# initialize servo state to stop
servo(motorA, 'STOP')
servo(motorB, 'STOP')
# create PWM objects for speed control and initialize duty ratio
duty = 75
motorA.PWM.start(duty)
motorB.PWM.start(duty)

quit = False
# stop program after 60 seconds
tend = time.time() + 60
while not quit and time.time() < tend:
    # press q to quit program early
    quit = True if input("Type 'q' to exit: ") is "q" else False
GPIO.cleanup()


