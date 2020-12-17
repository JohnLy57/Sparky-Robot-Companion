
import cv2
import numpy as np
import os 
import time
import RPi.GPIO as GPIO
import two_wheel_mod as tw
import pygame

###################
#-- PYGAME INIT --#
###################

# os.putenv('SDL_VIDEODRIVER', 'fbcon') # Display on piTFT
# os.putenv('SDL_FBDEV', '/dev/fb1')
#os.putenv('SDL_MOUSEDRV', 'TSLIB') # Track mouse clicks on piTFT
#os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')

# pygame.init()
# screen = pygame.display.set_mode((240,320))
# BLACK = 0,0,0

# screen.fill(BLACK)

#============================================================
#TFT Button Operation
#============================================================
# panicStop = False
# GPIO.setmode(GPIO.BCM)
# # on pin interrupt signal, handle motor functions
# def GPIO_callback(channel):
#     global search, TFT, screen
#     for pin in tw.piTFT_Buttons:
#         if (not GPIO.input(pin)):
#             # print("falling edge detected on {}".format(pin))
#             if pin is 27:
#                 print("\n [INFO] Exiting Program and cleanup stuff")
#                 GPIO.cleanup()
#                 cam.release()
#                 cv2.destroyAllWindows()
#                 pygame.quit()
#                 sys.exit()


# buttonControls = {17:"start", 22:"search", 23:"add face", 27:"quit"}

# # setup for all piTFT buttons as inputs using pull up resistors
# print("setting up piTFT buttons")
# for pin in tw.piTFT_Buttons:
#     GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#     print("GPIO {} setup".format(pin))
#     GPIO.add_event_detect(pin, GPIO.FALLING, callback=GPIO_callback, bouncetime=300)

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
width, height = 640, 480 
cam.set(3, width) # set video width
cam.set(4, height) # set video height

# Define min window size to be recognized as a face
minW = 0.05*cam.get(3)
minH = 0.05*cam.get(4)

# Define parameters for pursuit
# target = False
speed = 90
midX = width/2
driveTime = time.time()

targetPerson = "John" # change to output of voice input
findFaceInit = True

# Rotate until we find an identifiable face
# Return true if the desired person is found
def find_faces(init, targetPerson, img):
    global findFaceInit
    print(f"Init: {findFaceInit}")
    target = False
    print("search mode")
    # Do a fun search init maneuver
    # quickly spin ~180 left then right
    if init:
        findFaceInit = False
        for turn in ['left', 'right']:
            startTime = time.time()
            tw.drive('stop', speed, speed)
            while time.time() < startTime + 1:
                tw.drive(turn, 70, 70)
                target, _ = identify_faces(targetPerson, img)
                if target:
                    return True

    # slowly turn left to find the desired person
    tw.drive('left', 40, 40)
    target, _ = identify_faces(targetPerson, img)
    if target:
        return True
    else:
        return False



def identify_faces(targetPerson, img):
    # " Reads from camera and detects faces
    # " 
    # " Params:
    # "    targetPerson: (string) name of person we wish to find
    # " Return:
    # "   target: (boolean) determines if targetPerson is in view and recognized
    # "   stopCondition: (boolean) determines if targetPerson is close enough to the camera 
    # "

    global speed, midX, driveTime, findFaceInit
    
    target = False
    stopCondition = False
    
    # time.sleep(0.005)
    # ret, img =cam.read()
    # # if frame is read correctly ret is True
    # if not ret:
    #     print("Can't receive frame (stream end?). Exiting ...")
    #     return
    # img = cv2.flip(img, -1) # Flip vertically

    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
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
            # determine if person detected is our desired target
            if person == targetPerson:
                target = True
                driveTime = time.time() + 0.05
                midX = (x + w/2)/width * 100

                # reached destination so stop tracking
                if w > width/4 or h > height/2:
                    target = False
                    stopCondition = True
                    findFaceInit = True
                    tw.drive("stop")


        else:
            person = "unknown"
            confidence = "  {0}%".format(round(100 - mismatch))
        
        cv2.putText(img, str(person), (x+5,y-5), font, 1, (255,255,255), 2)
        cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)  

        # Display on TFT
        # resized=cv2.resize(img,(240,160))
        # cv2.imwrite('tmp.jpg',resized)
        # image=pygame.image.load('tmp.jpg')
        # screen.blit(image,(0,0))
        # pygame.display.update(pygame.Rect((0,0), (240,160)))
        # cv2.imshow('camera',img) 

    return target, stopCondition, img

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
    


# testTime = time.time()
# while time.time() < testTime + 10:
#     # Capture frame-by-frame
#     ret, frame = cam.read()
#     frame = cv2.flip(frame, -1) # Flip vertically
#     # if frame is read correctly ret is True
#     if not ret:
#         print("Can't receive frame (stream end?). Exiting ...")
#         break
#     # Our operations on the frame come here
    
#     # Display the resulting frame
#     cv2.imshow('frame', frame)
#     if cv2.waitKey(1) == ord('q'):
#         break

### Not yet Updated Test Code
# search = True
# while True:
#     if search:
#         foundFace = find_faces(findFaceInit, targetPerson)
#         if foundFace:
#             search = False
#     if foundFace:
#         target,stopCondition = identify_faces(targetPerson)
#         pursue_target(target)
#         if stopCondition:
#             foundFace = False
#             print(f"Found {targetPerson}")
#     if not search and not foundFace:
#         identify_faces("None")

#     k = cv2.waitKey(10) & 0xff # Press 'ESC' for exiting video
#     if k == 27:
#         break

# Do a bit of cleanup
print("\n [INFO] Exiting Program and cleanup stuff")
cam.release()
cv2.destroyAllWindows()
