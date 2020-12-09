import struct 
import numpy as np
import os
import RPi.GPIO as GPIO
import pyaudio
from picovoice import Picovoice
import sys

_keyword_path="sparky.ppn" #sparky hotword (to initiate)
_context_path="smart_lighting_raspberry-pi.rhn" #uses the smart lighting intents ( we changing it to our own) 
pa = None
audio_stream = None


def wake_word_callback():
	print('[wake word]\n') 
	#GPIO.output(13, GPIO.HIGH)

#### Example: Sparky, turn all the lights on 
def inference_callback(inference):
	if inference.is_understood:
		print("intent:")
		print(type(inference.intent))
		print('\n')
		print(type(inference.slots.items()))
		print('\n')
		for slot, value in inference.slots.items():
			print('slot:')
			print(type(slot))
			print('\n value:')
			print(type(value))
			print('\n')
		
		if inference.is_understood:
			print('{')
			print("  intent : '%s'" % inference.intent)
			print('  slots : {')
			for slot, value in inference.slots.items():
				print("    %s : '%s'" % (slot, value))
			print('  }')
			print('}\n')
		else:
			print("Didn't understand the command.\n")





_picovoice=Picovoice(
	keyword_path=_keyword_path,
	wake_word_callback=wake_word_callback,
	context_path=_context_path,
	inference_callback=inference_callback,
	porcupine_library_path=None,
	porcupine_model_path=None,
	rhino_sensitivity=0.8, 
	rhino_library_path=None,
	rhino_model_path=None,
	porcupine_sensitivity=0.8)


			 
pa = pyaudio.PyAudio()
audio_stream = pa.open(
				rate=_picovoice.sample_rate,
				channels=1,
				format=pyaudio.paInt16,
				input=True,
				frames_per_buffer=_picovoice.frame_length)

try:

	while True:
		pcm = audio_stream.read(_picovoice.frame_length)
		pcm = struct.unpack_from("h" * _picovoice.frame_length, pcm)
		_picovoice.process(pcm)
        
finally:
	if _picovoice is not None:
		_picovoice.delete()

	if audio_stream is not None:
		audio_stream.close()

	if pa is not None:
		pa.terminate()
