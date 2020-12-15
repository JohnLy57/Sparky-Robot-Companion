import struct 
import numpy as np
import os
import RPi.GPIO as GPIO
import pyaudio
from picovoice import Picovoice
import sys
import two_wheel_mod as tw
import time
import cv2
# import pygame
#import face_recognition_pursuit as fr
import pygame
from pygame.locals import *
###################
#-- PYGAME INIT --#
###################

# os.putenv('SDL_VIDEODRIVER', 'fbcon') # Display on piTFT
# os.putenv('SDL_FBDEV', '/dev/fb1')
# #os.putenv('SDL_MOUSEDRV', 'TSLIB') # Track mouse clicks on piTFT
# #os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
pygame.init()
screen=pygame.display.set_mode((240,320))
BLACK = 0,0,0

screen.fill(BLACK)

#============================================================
#TFT Button Operation
#============================================================
panicStop = False
GPIO.setmode(GPIO.BCM)
# on pin interrupt signal, handle motor functions
def GPIO_callback(channel):
	for pin in tw.piTFT_Buttons:
		if (not GPIO.input(pin)):
			print("falling edge detected on {}".format(pin))
			if pin is 27:
				print("\n [INFO] Exiting Program and cleanup stuff")
				GPIO.cleanup()
				cam.release()
				cv2.destroyAllWindows()
				# pygame.quit()
				sys.exit()



buttonControls = {17:"start", 22:"search", 23:"add_face", 27:"quit"}

# setup for all piTFT buttons as inputs using pull up resistors
print("setting up piTFT buttons")
for pin in tw.piTFT_Buttons:
	GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
	print("GPIO {} setup".format(pin))
	GPIO.add_event_detect(pin, GPIO.FALLING, callback=GPIO_callback, bouncetime=300)
#============================================================

#============================================================
GPIO.setup(13,GPIO.OUT) # LED pin


	


#===============================================
#Voice Recognition 
#===============================================
_keyword_path="sparky.ppn" #sparky hotword (to initiate)
_context_path="sparky.rhn" #uses the smart lighting intents ( we changing it to our own) 
pa = None
audio_stream = None
class v_instructions:
	v_search=False
	v_direction=False
	v_tricks=False
	led_on=False
	word=''
	
instruction=v_instructions()
global instructions




def wake_word_callback():
	print('[wake word]\n') 
	GPIO.output(13, GPIO.HIGH)
	instruction.led_on=True
	tw.drive('stop')
	instruction.v_search=False
	instruction.v_direction=False
	instruction.v_tricks=False
	

#### Example: Sparky, turn all the lights on 
def inference_callback(inference):
	
	if inference.is_understood:
		instruction.v_search=False
		instruction.v_direction=False
		instruction.v_tricks=False
		print(inference)
		
		if inference.intent == 'search':
			instruction.v_search=True
			instruction.word=inference.slots['users']
			print(f"Looking for friend {instruction.word} .....")
			
		elif inference.intent =='move':
			for slot,value in inference.slots.items():
				if slot == 'direction':
					instruction.v_direction=True
					instruction.word=value 
				elif slot == 'tricks':
					instruction.v_tricks=True
					instruction.word=value
				else:
					instruction.word=''

		else:
			instruction.word=''
	
		
	
	'''
		if inference.is_understood:
			print('{')
			print("  intent : '%s'" % inference.intent)
			print('  slots : {')
			print(inference.slots.items())
			
			for slot, value in inference.slots.items():
				print("    %s : '%s'" % (slot, value))
			print('  }')
			print('}\n')
		else:
			print("Didn't understand the command.\n")
'''

_picovoice=Picovoice(
	keyword_path=_keyword_path,
	wake_word_callback=wake_word_callback,
	context_path=_context_path,
	inference_callback=inference_callback,
	porcupine_library_path=None,
	porcupine_model_path=None,
	rhino_sensitivity=0.2, 
	rhino_library_path=None,
	rhino_model_path=None,
	porcupine_sensitivity=1)


			 
pa = pyaudio.PyAudio()
audio_stream = pa.open(
	rate=_picovoice.sample_rate,
	channels=1,
	format=pyaudio.paInt16,
	input=True,
	frames_per_buffer=_picovoice.frame_length)
				
#=============================================================

#=============================================================
endtime=0 
led_endtime=0
turn=True
def movement_3sec(direction: 'string', speedL: "int" =75, speedR: "int" =75):
	global endtime,turn
	if direction == 'forward' or 'backward' or 'right' or 'left':
		tw.drive(direction,speedL,speedR)
	else:
		tw.drive("left",90,90)
		
			
			
	print(time.time())
	print(endtime)
	if time.time() > endtime:
		if endtime >0:
			tw.drive('stop',speedL,speedR)
			endtime=0
			instruction.v_direction=False
		else:
			endtime=time.time()+3



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

#targetPerson = "John" # change to output of voice input



def identify_faces(targetPerson,img):
	
	# " Reads from camera and detects faces
	# " 
	# " Params:
	# "    targetPerson: (string) name of person we wish to find
	# " Return:
	# "   target: (boolean) determines if targetPerson is in view and recognized
	# "   stopCondition: (boolean) determines if targetPerson is close enough to the camera 
	# "

	global speed, midX, driveTime

	target = False
	stopCondition = False

	time.sleep(0.005)
	#ret, img =cam.read()
	# if frame is read correctly ret is True
	if not ret:
		print("Can't receive frame (stream end?). Exiting ...")
		return
	

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
			if person == targetPerson:
				target = True
				driveTime = time.time() + 0.05
				midX = (x + w/2)/width * 100

			# reached destination so stop tracking
			if w > width/4 or h > height/4:
				stopCondition = True


		else:
			
			person = "unknown"
			confidence = "  {0}%".format(round(100 - mismatch))
        
		cv2.putText(img, str(person), (x+5,y-5), font, 1, (255,255,255), 2)
		cv2.putText(img, str(confidence), (x+5,y+h-5), font, 1, (255,255,0), 1)  


	
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





try:

	while True:
					
		pcm = audio_stream.read(_picovoice.frame_length,exception_on_overflow=False)
		pcm = struct.unpack_from("h" * _picovoice.frame_length, pcm)
		_picovoice.process(pcm)

		ret, img =cam.read()
		img = cv2.flip(img, -1) # Flip vertically
		if instruction.led_on:
			if time.time() > led_endtime:
				if led_endtime >0:
					GPIO.output(13, GPIO.LOW)
					led_endtime=0
					instruction.led_on=False
				else:
					led_endtime=time.time()+5
					
	
		if instruction.v_direction:
			if instruction.word == 'forward':
				movement_3sec('forward',30,30)
			if instruction.word == 'back':
				movement_3sec('backward',30,30)
			if instruction.word == 'right':
				movement_3sec('right',30,30)
			if instruction.word == 'left':
				movement_3sec('left',30,30)
			if instruction.word == 'spin':
				tw.drive("left",90,90)
				
				
		if instruction.v_search:
			#use instruction.word for the user pass to FaceRec
			#variable contains name of the user asked for
			#change instruction.v_search to False after user found
			

			
		#	instruction.word='John'
			target_found, stopCondition,img = identify_faces('John',img)

			print(target_found)
			print(stopCondition)
			if stopCondition:
				tw.drive("stop")
				instruction.v_search = False
				print('stop')
				
			if target_found:
				pursue_target(target_found)

	
			
		resized=cv2.resize(img,(240,160))
		cv2.imwrite('tmp.jpg',resized)
		image=pygame.image.load('tmp.jpg')
		screen.blit(image,(0,0))
		pygame.display.update()
		
		if instruction.v_tricks:
			pass
			
			
finally:
	if _picovoice is not None:
		_picovoice.delete()

	if audio_stream is not None:
		audio_stream.close()

	if pa is not None:
		pa.terminate()
