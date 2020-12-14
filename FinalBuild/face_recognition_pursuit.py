
import cv2
import numpy as np
import os 
import time
import RPi.GPIO as GPIO
import two_wheel_mod as tw
import pygame

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
names = ['None', 'John', 'Carlos'] 

# Initialize and start realtime video capture
cam = cv2.VideoCapture(0)
width, height = 320, 240 
# cam.set(3, width) # set video width
# cam.set(4, height) # set video height

# Define min window size to be recognized as a face
minW = 0.05*cam.get(3)
minH = 0.05*cam.get(4)

# Define parameters for pursuit
target = False
speed = 90
midX = width/2
driveTime = time.time()

targetPerson = "John" # change to output of voice input



def identify_faces(targetPerson):
    global target, speed, midX, driveTime

    time.sleep(0.005)
    ret, img =cam.read()
    img = cv2.flip(img, -1) # Flip vertically

    img_gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    img_gray = cv2.equalizeHist(img_gray)

    faces = faceCascade.detectMultiScale( 
        img_gray,
        # scaleFactor = 1.2,
        # minNeighbors = 5,
        # minSize = (int(minW), int(minH)),
       )

    for(x,y,w,h) in faces:

        # cv2.rectangle(img, (x,y), (x+w,y+h), (0,255,0), 2)
        center = (x + w//2, y + h//2)
        img = cv2.ellipse(img, center, (w//2, h//2), 0, 0, 360, (255, 0, 255), 4)

        id, mismatch = recognizer.predict(img_gray[y:y+h,x:x+w])
        
        # Check if mismatch is less them 100 ==> "0" is perfect match 
        if (mismatch < 100):
            person = names[id] # determine name of face
            confidence = "  {0}%".format(round(100 - mismatch))
            if person == targetPerson:
                target = True
                driveTime = time.time() + 0.05
                midX = (x + w/2)/width * 100


        else:
            person = "unknown"
            confidence = "  {0}%".format(round(100 - mismatch))
        
        cv2.putText(img, str(person), (x+5,y-5), font, 1, (255,255,255), 2)
        cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)  

        # # Display on TFT
        # resized=cv2.resize(img,(240,160))
        # cv2.imwrite('tmp.jpg',resized)
        # image=pygame.image.load('tmp.jpg')
        # screen.blit(image,(0,0))
        # pygame.display.update()
        # # cv2.imshow('camera',img) 

        return target

def pursue_target(target):
    # when we see a known target, have robot travel towards face
    if target: 
        # print(f"Target: {targetPerson}, X:{midX}")
        slowSpeed = speed-(np.abs(50-midX))
        if slowSpeed <= 0:
            slowSpeed=0
        # print(f"Speed:{slowSpeed}")
        if midX < 45:
            tw.drive("forward", slowSpeed, speed)
            print("Lean left")
        elif midX > 55:
            tw.drive("forward", speed, slowSpeed)
            print("Lean right")
        else:
            tw.drive("forward", speed, speed)
        
        # step through to a new motion when enough time has elapsed
        if time.time() > driveTime:
            target = False
    else:
        tw.drive("stop")

        

# while True:

#     target = identify_faces()
#     pursue_target(target)

#     k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
#     if k == 27:
#         break

# # Do a bit of cleanup
# print("\n [INFO] Exiting Program and cleanup stuff")
# cam.release()
# cv2.destroyAllWindows()
