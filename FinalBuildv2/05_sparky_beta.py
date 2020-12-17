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
import face_recognition
import pickle

import numpy as np
import pygame
from pygame.locals import *
###################
#-- PYGAME INIT --#
###################

os.putenv('SDL_VIDEODRIVER', 'fbcon') # Display on piTFT
os.putenv('SDL_FBDEV', '/dev/fb0')
# #os.putenv('SDL_MOUSEDRV', 'TSLIB') # Track mouse clicks on piTFT
# #os.putenv('SDL_MOUSEDEV', '/dev/input/touchscreen')
pygame.init()
screen=pygame.display.set_mode((240,320)) # PiTFT Mode
# screen=pygame.display.set_mode((360,360)) # Desktop Mode
pygame.mouse.set_visible(False)
dispW, dispH = screen.get_size()
dispRect = pygame.Rect((0,0), (dispW,dispH))
BLACK = (0,0,0)
WHITE = (255,255,255)
fontSm = pygame.font.SysFont(None, 12)
fontLg = pygame.font.SysFont(None, 24)

updateText = False
party_over = False

screen.fill(BLACK)

def draw_counter(number):
	text = fontLg.render(f'{number}', True, WHITE, BLACK)
	textRect = text.get_rect(center=(0.5*dispW, 0.90*dispH))
	screen.fill(BLACK, textRect.inflate(20,0))
	screen.blit(text,textRect)
	pygame.display.update(textRect)

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
# LEDs
#============================================================
GPIO.setup(13,GPIO.OUT) # LED pin


	


#===============================================
#Voice Recognition 
#===============================================
timerStart = time.time()
prevCount = 0
imgCount = 0

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
	global updateText, timerStart
	timerStart = time.time()

	if inference.is_understood:
		instruction.v_search=False
		instruction.v_direction=False
		instruction.v_tricks=False
		print(inference)
		updateText = True
		
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
# Movement
#=============================================================
endtime=0 
led_endtime=0
turn=True
def movement_3sec(direction: 'string', speedL: "int" =75, speedR: "int" =75):
	global endtime,turn,updateText
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
			updateText=False
		else:
			endtime=time.time()+0.5

c=0
def move_breakdance():
	global c,endtime
	
	if (c % 2) ==0:
		tw.drive('stop')
		tw.drive("left",50,50)
		
	else:
		tw.drive('stop')
		tw.drive("right",60,60)
		
		
	if time.time() > endtime:
		
		
		if endtime >0:
			c+=1
			endtime=0
			if c >= 10:
				tw.drive('stop')
				instruction.v_tricks=False
				c=0
				
		else:
			endtime=time.time()+0.5


########################
#-- FACE RECOGNITION --#
########################

#Initialize 'currentname' to trigger only when a new person is identified.
currentname = "unknown"
#Determine faces from encodings.pickle file model created from train_model.py
encodingsP = "encodings.pickle"
#use this xml file
cascade = "haarcascade_frontalface_default.xml"

# load the known faces and embeddings along with OpenCV's Haar
# cascade for face detection
print("[INFO] loading encodings + face detector...")
data = pickle.loads(open(encodingsP, "rb").read())
detector = cv2.CascadeClassifier(cascade)

font = cv2.FONT_HERSHEY_SIMPLEX


# Initialize and start realtime video capture
cam = cv2.VideoCapture(0)
camW, camH = 640,480 #960,720 # 1280,720 
cam.set(3, camW) # set video width
cam.set(4, camH) # set video height
camRect = pygame.Rect((0,0), (camW,camH))
camWs, camHs = 240, 180  
textAreaRect = pygame.Rect((0,camHs), (dispW,dispH-camHs))

# fps = FPS().start()

# Define min window size to be recognized as a face
minW = 0.05*cam.get(3)
minH = 0.05*cam.get(4)

# Define parameters for pursuit
# target = False
speed = 90
midX = camW/2
driveTime = time.time()

#targetPerson = "John" # change to output of voice input
findFaceInit = True
search = True
misses = 0

# Rotate until we find an identifiable face
# Return true if the desired person is found
def find_faces(targetPerson, img):
	global findFaceInit
	# print(f"Init: {findFaceInit}")
	target = False
	# print("search mode")
	# Do a fun search init maneuver
	# quickly spin ~180 left then right
	if findFaceInit:
		findFaceInit = False
		for turn in ['left', 'right']:
			startTime = time.time()
			tw.drive('stop', speed, speed)
			while time.time() < startTime + 1:
				tw.drive(turn, 70, 70)
				target,_,_ = identify_faces(targetPerson, img)
				if target:
					driveTime = time.time() + 0.2
					while time.time() < driveTime:
						adjustment = 'right' if turn is 'left' else 'left'
						tw.drive(adjustment, 60, 60)
					tw.drive("stop")
					return True

    # slowly turn left to find the desired person
	tw.drive('left', 50, 50)
	target,_,_ = identify_faces(targetPerson, img)
	if target:
		driveTime = time.time() + 0.2
		while time.time() < driveTime:
			tw.drive("right", 60, 60)
		tw.drive("stop")
		return True
	else:
		tw.drive("stop")
		return False

def detect_faces_quick(img):
	# Reads from camera and detects faces quickly
	#
	# Params:
	#    targetPerson: (string) name of person we wish to find
	# Return:
	#   boolean: True if single face present, False if too many faces or none

	global speed, midX, driveTime, findFaceInit

	# convert the input frame from (1) BGR to grayscale (for face detection)
	img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

	# simple face detection
	faces = detector.detectMultiScale( 
	img_gray,
	scaleFactor = 1.3, # higher scaleFactor increases speed of detection for smaller faces but reduces accuarcy
	minNeighbors = 5, # number of matching rectangles required before allowing face detection
	minSize = (int(minW), int(minH)), # minimum Size allowed for object detection
	flags = cv2.CASCADE_SCALE_IMAGE
	)

	# determine number of faces seen
	# print(np.asarray(faces))
	if np.shape(np.asarray(faces))[0] != 1:
		tw.drive("stop")
		return False
	
	else:
		chance = np.random.rand(1)
		if chance < 0.99:
			for (x,y,w,h) in faces:
				# when very close, force a face recgnition check
				if (not search) and (w > camW/4 or h > camH/2):
					tw.drive("stop")
					return False

				centerX, centerY = x + w//2, y + h//2
				img = cv2.ellipse(img, (centerX, centerY), (w//2, h//2), 0, 0, 360, (255, 0, 255), 4)	

				driveTime = time.time() + 0.2
				midX = (x + w/2)/camW * 100	
				return True
		else:
			return False


def identify_faces(targetPerson, img, mode = "None"):
	# Reads from camera and detects faces 
	# Face Recognition is slow but accurate
	# 
	# Params:
	#    targetPerson: (string) name of person we wish to find
	# Return:
	#   target: (boolean) determines if targetPerson is in view and recognized
	#   stopCondition: (boolean) determines if targetPerson is close enough to the camera 

	global speed, midX, driveTime, findFaceInit

	target = False
	stopCondition = False
	
	# convert the input frame from (1) BGR to grayscale (for face detection) and
	# (2) from BGR to RGB for (face recogniton)
	img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
	img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

	# simple face detection
	faces = detector.detectMultiScale( 
	img_gray,
	scaleFactor = 1.3, # higher scaleFactor increases speed of detection for smaller faces but reduces accuarcy
	minNeighbors = 5, # number of matching rectangles required before allowing face detection
	minSize = (int(minW), int(minH)), # minimum Size allowed for object detection
	flags = cv2.CASCADE_SCALE_IMAGE
	)

	# OpenCV returns bounding box coordinates in (x, y, w, h) order
	# but we need them in (top, right, bottom, left) order, so we
	# need to do a bit of reordering
	boxes = [(y, x + w, y + h, x) for (x, y, w, h) in faces]

	# compute the facial embeddings for each face bounding box
	encodings = face_recognition.face_encodings(img_rgb, boxes)
	names = []

	# loop over the facial embeddings
	for encoding in encodings:
		# attempt to match each face in the input image to our known
		# encodings
		matches = face_recognition.compare_faces(data["encodings"],
			encoding)
		name = "Unknown" #if face is not recognized, then print Unknown

		# check to see if we have found a match
		if True in matches:
			# find the indexes of all matched faces then initialize a
			# dictionary to count the total number of times each face
			# was matched
			matchedIdxs = [i for (i, b) in enumerate(matches) if b]
			counts = {}

			# loop over the matched indexes and maintain a count for
			# each recognized face face
			for i in matchedIdxs:
				name = data["names"][i]
				if name is targetPerson:
					tw.drive("stop")
				counts[name] = counts.get(name, 0) + 1

			# determine the recognized face with the largest number
			# of votes (note: in the event of an unlikely tie Python
			# will select first entry in the dictionary)
			name = max(counts, key=counts.get)
			
			# #If someone in your dataset is identified, print their name on the screen
			# if currentname != name:
			# 	currentname = name
			# 	print(currentname)
		
		# update the list of names
		names.append(name)

	# loop over the detected faces and label them
	for ((topY, rightX, bottomY, leftX), name) in zip(boxes, names):
		center = ((leftX+rightX)//2, (bottomY+topY)//2)
		w,h = rightX-leftX, bottomY-topY

		cv2.ellipse(img, (center[0], center[1]), (w//2, h//2), 0, 0, 360, (255, 0, 255), 2)	
		cv2.putText(img, str(name), (leftX-15,bottomY+30), font, 1.2, (255,255,255), 2)

		if mode is "party_time":
			if name is not "Unknown":
				# Icon made by "https://www.flaticon.com/authors/freepik"
				hat = cv2.imread('party-hat.png', cv2.IMREAD_UNCHANGED)
				hat = cv2.resize(hat,(h,h))
				hatY, hatX, _ = hat.shape
				offsetY, offsetX = topY-hatY, center[0]-hatX//2 # top left corner of hat position
				yStartImg = np.amax([0,offsetY])
				yEndImg = np.amax([0,topY])
				yStartHat = np.amax([0,hatY-topY])
				alpha_hat = hat[:,:,3] / 255.0
				alpha_img = 1.0 - alpha_hat
				# alpha will either be 0 or 1 here
				# merge images using alpha value to remove hat bkgd
				for c in range(0,3):
					img[yStartImg:yEndImg, offsetX:offsetX+hatX, c] = \
						alpha_hat[yStartHat:, :] * hat[yStartHat:, :, c] + \
						alpha_img[yStartHat:, :] * img[yStartImg:yEndImg, offsetX:offsetX+hatX, c]
			else:
				# Draw Triangle Hat
				pts = np.array([[leftX+w//8,topY], [leftX+w-w//8,topY], [leftX+w//2,topY-w]], np.int32).reshape((-1,1,2))
				img = cv2.polylines(img,[pts],True,(0,255,255),4)

	
		# determine if person detected is our desired target
		if name == targetPerson:
			target = True
			driveTime = time.time() + 0.05
			midX = (leftX + w/2)/camW * 100

			# reached destination so stop tracking
			if (not search) and (w > camW/4 or h > camH/2):
				target = False
				stopCondition = True
				findFaceInit = True
				tw.drive("stop")

	return target, stopCondition, img

def pursue_target(target):
	# when we see a known target, have robot travel towards face
	while target and time.time() < driveTime:
		# print(f"Target: {targetPerson}, X:{midX}")
		slowSpeed = speed-(np.abs(50-midX//4))
		if slowSpeed <= 0:
			slowSpeed=0
		# print(f"Speed:{slowSpeed}")
		if midX < 45:
			tw.drive("forward", slowSpeed, speed)
			# print("Lean left")
		elif midX > 55:
			tw.drive("forward", speed, slowSpeed)
			# print("Lean right")
		else:
			tw.drive("forward", speed, speed)
	else:
		tw.drive("forward", 40, 40)



try:

	while True:
					
		pcm = audio_stream.read(_picovoice.frame_length,exception_on_overflow=False)
		pcm = struct.unpack_from("h" * _picovoice.frame_length, pcm)
		_picovoice.process(pcm)

		# video capture
		ret, img =cam.read()
		img = cv2.flip(img, -1) # Flip vertically
		# resize for faster processing
		# img = cv2.resize(img, (640,480), interpolation = cv2.INTER_AREA)
		

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
				movement_3sec('forward',90,90)
			if instruction.word == 'back':
				movement_3sec('backward',90,90)
			if instruction.word == 'right':
				movement_3sec('right',90,90)
			if instruction.word == 'left':
				movement_3sec('left',90,90)
			if instruction.word == 'spin':
				tw.drive("left",90,90)
			
			screen.fill(BLACK, textAreaRect)
			text = fontLg.render(f'Moving {instruction.word}', True, WHITE, BLACK)
			textRect = text.get_rect(center=(0.5*dispW, 0.75*dispH))
			screen.fill(BLACK, textRect.inflate(240,0))
			screen.blit(text,textRect)
			pygame.display.update(textRect)
				
				
		if instruction.v_search:
			#use instruction.word for the user pass to FaceRec
			#variable contains name of the user asked for
			#change instruction.v_search to False after user found

			if updateText:
					updateText = False
					search = True
					# screen.fill(BLACK, textAreaRect)
					text = fontLg.render(f'Looking for {instruction.word} . . .', True, WHITE, BLACK)
					textRect = text.get_rect(center=(0.5*dispW, 0.75*dispH))
					screen.fill(BLACK, textRect.inflate(240,0))
					screen.blit(text,textRect)
					pygame.display.update(textRect)

			if time.time() < timerStart + 20:			
				if search:
					foundFace = find_faces(instruction.word, img)
					if foundFace:
						print("spotted...")
						# time.sleep(0.5)
						search=False
						misses = 0

				elif foundFace:
					# after finding our target, move to face 90% of time with face detection only
					# use face recognition for the other 10% of the time
					search = False
					facePresent = detect_faces_quick(img)
					if facePresent:
						pursue_target(True)
					else: 
						tw.drive("stop")
						target, stopCondition, img = identify_faces(instruction.word, img)
						if target:
							misses = 0
							pursue_target(target)
						else:
							misses += 1
							if misses > 10:
								# driveTime = time.time() + 1.0
								# while time.time() < driveTime:
								# 	tw.drive("right", 75, 75)
								# _, _, img = identify_faces(instruction.word, img)
								foundFace = find_faces(instruction.word, img) # delay
								search = True
								foundFace = False

						if stopCondition:
							foundFace = False
							search = True
							instruction.v_search = False
							updateText = True
							print(f"Found {instruction.word}")
							#screen.fill(BLACK, textAreaRect)
							text = fontLg.render(f'Found {instruction.word}!', True, WHITE, BLACK)
							textRect = text.get_rect(center=(0.5*dispW, 0.75*dispH))
							screen.fill(BLACK, textRect.inflate(240,0))
							screen.blit(text,textRect)
							pygame.display.update(textRect)

				counter = int(time.time() - timerStart)
				if prevCount != counter:
					prevCount = counter
					draw_counter(counter)
			else:
				tw.drive("stop")
				findFaceInit = True
				prevCount = 0
				instruction.v_search = False

		
		if instruction.v_tricks:
			if instruction.word == 'party':
				if updateText:
					imgCount += 1
					
					#screen.fill(BLACK, textAreaRect)
					text = fontLg.render('Party Time!', True, WHITE, BLACK)
					textRect = text.get_rect(center=(0.5*dispW, 0.75*dispH))
					screen.fill(BLACK, textRect.inflate(240,0))
					screen.blit(text,textRect)
					pygame.display.update(textRect)

				_,_,img = identify_faces(None, img, mode = "party_time")

				if time.time() < timerStart + 10:
					counter = int(time.time() - timerStart)
					if prevCount != counter:
						prevCount = counter
						draw_counter(counter)

				else:
					instruction.v_tricks = False
					prevCount = 0
					party_over=True
					updateText = False
				

			if instruction.word == 'break dance':
				move_breakdance()
				#screen.fill(BLACK, textAreaRect)
				text = fontLg.render('Breakdancing!!!', True, WHITE, BLACK)
				textRect = text.get_rect(center=(0.5*dispW, 0.75*dispH))
				screen.fill(BLACK, textRect.inflate(240,0))
				screen.blit(text,textRect)
				pygame.display.update(textRect)
		
		if not updateText:
			if party_over:
				party_over=False
				cv2.imwrite('party_time/image_' + str(imgCount) +'.jpg',img)
				screen.fill(BLACK, textAreaRect)
				photo = cv2.resize(img,(120,73))
				cv2.imwrite('tmp_photo.jpg',photo)
				photo = pygame.image.load('tmp_photo.jpg')
				screen.blit(photo,(0,247))
				pygame.display.update(textAreaRect)
				
			#screen.fill(BLACK, textAreaRect)
			text = fontLg.render('Sparky is sitting waiting ...', True, WHITE, BLACK)
			textRect = text.get_rect(center=(0.5*dispW, 0.75*dispH))
			screen.fill(BLACK, textRect.inflate(260,0))
			screen.blit(text,textRect)
			pygame.display.update(textRect)
		# Aspect Ratios
		# 16/9 = 1280,720 -> 640,360 -> 320,180 -> 160,90 -> 240,135
		# 4/3 = 960,720 -> 720,540 -> 240,180
		
		resized=cv2.resize(img,(camWs,camHs)) # PiTFT Mode (240,180)
		# resized=cv2.resize(img,(360,270)) # Desktop Mode
		cv2.imwrite('tmp.jpg',resized)
		image=pygame.image.load('tmp.jpg')
		screen.blit(image,(0,0))
		pygame.display.update(camRect)


finally:
	if _picovoice is not None:
		_picovoice.delete()

	if audio_stream is not None:
		audio_stream.close()

	if pa is not None:
		pa.terminate()
