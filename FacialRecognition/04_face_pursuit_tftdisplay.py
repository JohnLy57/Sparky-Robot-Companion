''''
Real Time Face Recogition
	==> Each face stored on dataset/ dir, should have a unique numeric integer ID as 1, 2, 3, etc                       
	==> LBPH computed model (trained faces) should be on trainer/ dir
Based on original code by Anirban Kar: https://github.com/thecodacus/Face-Recognition    

Developed by Marcelo Rovai - MJRoBot.org @ 21Feb18  

'''

import cv2
import numpy as np
import os 
import time
import RPi.GPIO as GPIO
import two_wheel_mod as tw
# import subprocess

# # Initialize Text Document
# record = 'echo "New Session ---------------" > face_position.txt'
# print(subprocess.check_output(record, shell=True))

import pygame
from pygame.locals import *
os.putenv('SDL_VIDEODRIVER', 'fbcon') # Display on piTFT
os.putenv('SDL_FBDEV', '/dev/fb0')
#os.putenv('SDL_MOUSEDRV', 'TSLIB') # Track mouse clicks on piTFT
#os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
pygame.init()
screen=pygame.display.set_mode((240,320))
BLACK = 0,0,0

screen.fill(BLACK)
########################
#-- BUTTON OPERATION --#
########################

panicStop = False
GPIO.setmode(GPIO.BCM)
# on pin interrupt signal, handle motor functions
def GPIO_callback(channel):
    for pin in tw.piTFT_Buttons:
        if (not GPIO.input(pin)):
            print("falling edge detected on {}".format(pin))
            if pin is 27:
                GPIO.cleanup()
                pygame.quit()
                sys.exit()


buttonControls = {17:"start", 22:"search", 23:"add_face", 27:"quit"}

# setup for all piTFT buttons as inputs using pull up resistors
print("setting up piTFT buttons")
for pin in tw.piTFT_Buttons:
    GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
    print("GPIO {} setup".format(pin))
    GPIO.add_event_detect(pin, GPIO.FALLING, callback=GPIO_callback, bouncetime=300)

########################
#-- FACE RECOGNITION --#
########################

recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read('trainer/trainer.yml')
cascadePath = "haarcascade_frontalface_default.xml"
faceCascade = cv2.CascadeClassifier(cascadePath)

font = cv2.FONT_HERSHEY_SIMPLEX

#iniciate id counter
id = 0

# names related to ids: example ==> Marcelo: id=1,  etc
names = ['None', 'John', 'Carlos', 'X', 'Y', 'Z'] 

# Initialize and start realtime video capture
cam = cv2.VideoCapture(0)
width, height = 320, 240 
cam.set(3, width) # set video width
cam.set(4, height) # set video height

# Define min window size to be recognized as a face
minW = 0.05*cam.get(3)
minH = 0.05*cam.get(4)

# Define parameters for pursuit
target = False
speed = 30
midX = width/2
driveTime = time.time()

while True:
    time.sleep(0.005)
    ret, img =cam.read()
    img = cv2.flip(img, -1) # Flip vertically

    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    faces = faceCascade.detectMultiScale( 
        gray,
        scaleFactor = 1.2,
        minNeighbors = 5,
        minSize = (int(minW), int(minH)),
       )

    # target = False

    for(x,y,w,h) in faces:

        cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)

        id, confidence = recognizer.predict(gray[y:y+h,x:x+w])
        
        # Check if confidence is less them 100 ==> "0" is perfect match 
        if (confidence < 100):
            id = names[id]
            confidence = "  {0}%".format(round(100 - confidence))
            target = True
            driveTime = time.time() + 0.05

            # Send relavent data to a text document
            midX = (x + w/2)/width * 100
            # record = f"echo {midX} >> face_position.txt"
            # print(subprocess.check_output(record, shell=True))

        else:
            id = "unknown"
            confidence = "  {0}%".format(round(100 - confidence))
        
        cv2.putText(img, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
        cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)  
    
    #Display on TFT
    resized=cv2.resize(img,(240,160))
    cv2.imwrite('tmp.jpg',resized)
    image=pygame.image.load('tmp.jpg')
    screen.blit(image,(0,0))
    pygame.display.update()
    #cv2.imshow('camera',img) 


    if target: 
        print(f"X:{midX}")
        slowSpeed = speed-(np.abs(50-midX))
        
        if slowSpeed <= 0:
            slowSpeed=0
            
        print(f"Speed:{slowSpeed}")
        if midX < 45:
            tw.drive("forward", slowSpeed, speed)
            print("Lean left")
        elif midX > 55:
            tw.drive("forward", speed, slowSpeed)
            print("Lean right")
        else:
            tw.drive("forward",speed,speed)
        
        # step through to a new motion when enough time has elapsed
        if time.time() > driveTime:
            target = False
    else:
        tw.drive("stop")
    

    
    
    k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
    if k == 27:
        break

# Do a bit of cleanup
print("\n [INFO] Exiting Program and cleanup stuff")
cam.release()
cv2.destroyAllWindows()
