import pyaudio
import numpy as np
import soundfile
import time

device_index = 1
input_rate = 48000
seconds_per_run = 5

p = pyaudio.PyAudio()

#get audio
stream = p.open(rate=input_rate, channels=1, format=pyaudio.paInt16, input=True, input_device_index=device_index) 

print('Start recording')
audio_data = stream.read(num_frames=input_rate*seconds_per_run, exception_on_overflow = False)

print('Stopped recording')

t1 = time.time_ns()
audio_formatted = np.frombuffer(audio_data, dtype=np.int16) #convert from byte stream to audio samples. Littleendian signed 16bit ints#output into floats
t2 = time.time_ns()
print(audio_formatted.shape)


print('Processed audio in %f ms' % ((t2-t1)/1e6))
print('Audio resampled')

soundfile.write('output_mono.wav', audio_formatted, input_rate)