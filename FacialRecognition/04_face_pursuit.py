''''
Real Time Face Recogition
	==> Each face stored on dataset/ dir, should have a unique numeric integer ID as 1, 2, 3, etc                       
	==> LBPH computed model (trained faces) should be on trainer/ dir
Based on original code by Anirban Kar: https://github.com/thecodacus/Face-Recognition    
Based on code by Marcelo Rovai: https://github.com/Mjrovai/OpenCV-Face-Recognition

Written by John Ly

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

#initiate id counter
id = 0

# names related to ids: example ==> Marcelo: id=1,  etc
names = ['None', 'John', 'Carlos', 'X', 'Y', 'Z'] 

# Initialize and start realtime video capture
cam = cv2.VideoCapture(0)
width, height = 640, 480 
cam.set(3, width) # set video width
cam.set(4, height) # set video height

# Define min window size to be recognized as a face
minW = 0.05*cam.get(3)
minH = 0.05*cam.get(4)

# Define parameters for pursuit
target = False
speed = 90
midX = width/2
driveTime = time.time()

targetPerson = "John"

while True:

    ret, img = cam.read()
    img = cv2.flip(img, -1) # Flip vertically

    frame_gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.equalizeHist(frame_gray)

    faces = faceCascade.detectMultiScale( 
        frame_gray,
        # scaleFactor = 1.2,
        # minNeighbors = 5,
        # minSize = (int(minW), int(minH)),
       )

    # target = False

    for(x,y,w,h) in faces:

        # cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
        center = (x + w//2, y + h//2)
        img = cv2.ellipse(img, center, (w//2, h//2), 0, 0, 360, (255, 0, 255), 4)

        id, mismatch = recognizer.predict(frame_gray[y:y+h,x:x+w])
        
        # Check if mismatch is less them 100 ==> "0" is perfect match 
        if (mismatch < 100):
            id = names[id] # determine name of face
            confidence = "  {0}%".format(round(100 - mismatch))
            if id == targetPerson:
                target = True
                driveTime = time.time() + 0.05
                midX = (x + w/2)/width * 100

            # record = f"echo {midX} >> face_position.txt"
            # print(subprocess.check_output(record, shell=True))

        else:
            id = "unknown"
            confidence = "  {0}%".format(round(100 - mismatch))
        
        cv2.putText(img, str(id), (x+5,y-5), font, 1, (255,255,255), 2)
        cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)  
    
    cv2.imshow('camera',img) 

    # when we see a known target, have robot travel towards face
    if target: 
        print(f"Target: {targetPerson}, X:{midX}")
        slowSpeed = speed-(np.abs(50-midX))
        # print(f"Speed:{slowSpeed}")
        if midX < 45:
            tw.drive("forward", slowSpeed, speed)
            print("Lean left")
        elif midX > 55:
            tw.drive("forward", speed, slowSpeed)
            print("Lean right")
        else:
            tw.drive("forward")
        
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
