import struct 
import numpy as np
import os
import RPi.GPIO as GPIO
import pyaudio
from picovoice import Picovoice
import sys
import two_wheel_mod as tw
import time
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
                GPIO.cleanup()
                #pygame.quit()
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





'''
def main():
	
	while(not quit_flag):
		
		pcm = audio_stream.read(_picovoice.frame_length)
		pcm = struct.unpack_from("h" * _picovoice.frame_length, pcm)
		_picovoice.process(pcm)
		
		if instruction.v_move:
			movement_1sec(instruction.word,30,30)
	'''		
		


try:
	
	while True:
		pcm = audio_stream.read(_picovoice.frame_length)
		pcm = struct.unpack_from("h" * _picovoice.frame_length, pcm)
		_picovoice.process(pcm)
		
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
		
		if instruction.v_tricks:
			
			
finally:
	if _picovoice is not None:
		_picovoice.delete()

	if audio_stream is not None:
		audio_stream.close()

	if pa is not None:
		pa.terminate()
