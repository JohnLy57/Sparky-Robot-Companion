# Run Test (Python 3)
# Author: John Ly (jtl222), Carlos Gutierrez (cag334)
# Lab 3: October 30, 2020

# Purpose: Builds on top of rolling_control with an additional autonomous 
# driving mode via a Start button

import two_wheel_mod as TW
import time
import pygame
import sys,os
import RPi.GPIO as GPIO
import subprocess
from collections import namedtuple
from recordtype import recordtype

########################
#-- BUTTON OPERATION --#
########################

panicStop = False
# on pin interrupt signal, handle motor functions
def GPIO_callback(channel):
    for pin in TW.piTFT_Buttons:
        if (not GPIO.input(pin)):
            print("falling edge detected on {}".format(pin))
            if not panicStop:
                # motor# and state control
                TW.servo(TW.buttonControls[pin][0],TW.buttonControls[pin][1])

# setup for all piTFT buttons as inputs using pull up resistors
print("setting up piTFT buttons")
for pin in TW.piTFT_Buttons:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("GPIO {} setup".format(pin))
    GPIO.add_event_detect(pin, GPIO.FALLING, callback=GPIO_callback, bouncetime=300)

#########################
#-- DISPLAY OPERATION --#
#########################
fix_touch = '/home/pi/lab2_files_f20/fix_touchscreen'
print(subprocess.check_output(fix_touch, shell=True))

os.putenv('SDL_VIDEODRIVER', 'fbcon') # Display on piTFT
os.putenv('SDL_FBDEV', '/dev/fb1') # Display on piTFT with no monitor connected

# try:
#     os.putenv('SDL_FBDEV', '/dev/fb1') # Display on piTFT with monitor connected
# except pygame.error as message:
#     print("No monitor connected.")
#     try:    
#         os.putenv('SDL_FBDEV', '/dev/fb0')
#     except pygame.error as message:
#         print("No display device available.")
os.putenv('SDL_MOUSEDRV', 'TSLIB') # Track mouse clicks on piTFT
os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# draws text onto screen at a specified position
def drawText(text: 'String', position: 'Tuple'):
    text_surface = std_font20.render(text, True, white)
    textRect = text_surface.get_rect(center=position)
    screen.blit(text_surface,textRect)

# updates panic button graphics and returns panic rect
# additionally controls looping conditional variable
def updatePanicButton(text: 'String'):
    global screen_buttons, panicStop, startDriveTest
    buttonPos = (screen_buttons["Panic"].x,screen_buttons["Panic"].y)
    if text is "STOP":
        background = red
        panicStop = False
        screen_buttons["Panic"].text = text
    elif text is "RESUME":
        background = green
        panicStop = True
        screen_buttons["Panic"].text = text
    text_surface = std_font30.render(text, True, white, background)
    textRect = text_surface.get_rect(center=buttonPos)
    panicButton = pygame.draw.circle(screen, background, buttonPos, textRect.w//2+3)
    screen.blit(text_surface,textRect)
    return panicButton

# draw text for log with updated data at corresponding positions
def updateLog():
    # draw headers
    for title in titles.values():
        drawText(title.text,(title.x,title.y))
    # update log values draw log values on-screen
    logA = TW.motorA.history
    logB = TW.motorB.history
    for i in range(len(logA)):
        drawText(logA[i].state,(leftLogPos[i].x,leftLogPos[i].y))
        drawText(logA[i].time,(leftLogPos[i].x+50,leftLogPos[i].y))
    for i in range(len(logB)):
        drawText(logB[i].state,(rightLogPos[i].x,rightLogPos[i].y))
        drawText(logB[i].time,(rightLogPos[i].x+50,rightLogPos[i].y))

# test sequence to test motor operation
def drive(direction: 'string'):
    # Stop by default
    TW.servo(TW.motorA, TW.MotorState.STOP)
    TW.servo(TW.motorB, TW.MotorState.STOP)
    if direction is "forward":
        TW.servo(TW.motorA, TW.MotorState.CCW)
        TW.servo(TW.motorB, TW.MotorState.CW)
    elif direction is "backward":
        TW.servo(TW.motorA, TW.MotorState.CW)
        TW.servo(TW.motorB, TW.MotorState.CCW)  
    elif direction is "left":
        TW.servo(TW.motorA, TW.MotorState.CW)
        TW.servo(TW.motorB, TW.MotorState.CW)  
    elif direction is "right":
        TW.servo(TW.motorA, TW.MotorState.CCW)
        TW.servo(TW.motorB, TW.MotorState.CCW)  
    else:
        TW.servo(TW.motorA, TW.MotorState.STOP)
        TW.servo(TW.motorB, TW.MotorState.STOP)

# prewritten test sequence as defined with adjustable timing parameters
Motion = recordtype("Motion", ["direction", "time"])
startDriveTest = False
driveTestSequence = [Motion("forward", 3), Motion("stop", 2), Motion("backward", 3), Motion("stop", 2), Motion("left", 1), Motion("stop", 2), Motion("right", 1), Motion("stop", 2)]


# Pygame Initilization
pygame.init()
clock = pygame.time.Clock()
frameRate = 30
print("FPS: {}".format(frameRate))
screen = pygame.display.set_mode((320, 240))
white = 255, 255, 255
red = 255, 0, 0
green = 0, 255, 0
black = 0, 0, 0
pygame.mouse.set_visible(False)

std_font20 = pygame.font.Font(None, 20)
std_font30 = pygame.font.Font(None, 30)

Text = recordtype("Text", ['text','x','y',])
Pos = recordtype("Position", ['x','y'])
# Interactable Buttons
screen_buttons = {
    'Panic':Text("STOP",160,120),
    'Start':(80,200),
    'Quit':(240,200)
}
# Rolling History Positions
titles = {
    "Left": Text("Left History", 70, 70),
    "Right": Text("Right History", 250, 70)
}
leftLogPos = [
    Pos(50, 100),
    Pos(50, 120),
    Pos(50, 140)
]
rightLogPos = [
    Pos(230, 100),
    Pos(230, 120),
    Pos(230, 140)
]

# PyGame Screen Drawings
screen.fill(black)

panic_text_surface = std_font30.render("STOP", True, red) # rectangle text to be rendered   
panicRect = panic_text_surface.get_rect( \
    center=(screen_buttons['Panic'].x,screen_buttons['Panic'].y)) # text rectangle location
# screen.blit(panic_text_surface, panicRect) # place text and positional rect onto workspace surface
panicButton = updatePanicButton("STOP")

start_text_surface = std_font30.render("Start", True, white) # rectangle text to be rendered   
startRect = start_text_surface.get_rect(center=screen_buttons['Start']) # text rectangle location
screen.blit(start_text_surface, startRect) # place text and positional rect onto workspace surface

quit_text_surface = std_font30.render("Quit", True, white) # rectangle text to be rendered   
quitRect = quit_text_surface.get_rect(center=screen_buttons['Quit']) # text rectangle location
screen.blit(quit_text_surface, quitRect) # place text and positional rect onto workspace surface

# update and set variables for polling changes in motor state
updateLog()
prevStateA = TW.motorA.history[0].time
prevStateB = TW.motorB.history[0].time

pygame.display.flip()

quit = False
# stop program after 60 seconds
tend = time.time() + 60
while not quit and time.time() < tend:
    clock.tick(frameRate)
    # touch events and system quiting
    for event in pygame.event.get():   

        # upon mouse click event, get position      
        if (event.type is pygame.MOUSEBUTTONDOWN):            
            pos = pygame.mouse.get_pos()
        
        # refresh screen to black upon new mouse event
        elif (event.type is pygame.MOUSEBUTTONUP):            
            pos = pygame.mouse.get_pos() 
            print("touch at {}".format(pos))
            screen.fill(black)

            # handle panic button press for stop and resume
            if panicButton.collidepoint(pos):
                # stop motors and change visuals from stop to resume 
                # and record remaining time
                if screen_buttons["Panic"].text is "STOP":
                    print("Panic Stop")
                    TW.servo(TW.motorA, TW.MotorState.STOP)
                    TW.servo(TW.motorB, TW.MotorState.STOP)
                    panicButton = updatePanicButton("RESUME")
                    remainingTime = driveTime - time.time() 
                    if startDriveTest:
                        startDriveTest = False
                # resume system by starting from last drive sequence operation
                # and run for remaining time but only if startDriveTest has started
                else:
                    print("Resume System")
                    step = driveTestSequence[index]
                    drive(step.direction)
                    driveTime = time.time() + remainingTime
                    panicButton = updatePanicButton("STOP")
                    if startDriveTest == False:
                        startDriveTest = True
            
            # begin test driving sequence with initilized parameters for looping
            if startRect.collidepoint(pos):        
                    print("Start button pressed")
                    startDriveTest = True
                    index = -1
                    driveTime = time.time()
                    print("New sequence")

            # quit python program
            if quitRect.collidepoint(pos):        
                    print("Quit button pressed")
                    quit = True
                    GPIO.cleanup()
                    pygame.quit()
                    sys.exit()

            # draw screen elements onto workspace
            screen.blit(start_text_surface, startRect) 
            screen.blit(quit_text_surface, quitRect)

        # if quit event occurs, exit pygame
        if event.type == pygame.QUIT: 
                GPIO.cleanup()
                sys.exit() 

    # check to see if we've issues a new motor command recently
    if TW.motorA.currState is not prevStateA or TW.motorB.currState is not prevStateB:
        prevStateA = TW.motorA.history[0].time
        prevStateB = TW.motorB.history[0].time
        # redraw piTFT display
        screen.fill(black)
        updatePanicButton(screen_buttons["Panic"].text)
        screen.blit(start_text_surface, startRect) 
        screen.blit(quit_text_surface, quitRect)
        updateLog()
    
    if startDriveTest:
        # step through to a new motion when enough time has elapsed
        if time.time() > driveTime:
            # maintain index of driveTestSequence
            index += 1
            # repeat sequence
            if index >= len(driveTestSequence):
                index = 0
                print("New sequence")
            # set motor direction and duration
            step = driveTestSequence[index]
            drive(step.direction)
            driveTime = time.time() + step.time
            
    pygame.display.flip()
GPIO.cleanup()

