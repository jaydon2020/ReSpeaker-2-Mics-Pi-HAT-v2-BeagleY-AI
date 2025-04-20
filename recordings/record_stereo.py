import pyaudio
import numpy as np
import soundfile

device_index = 1
input_rate = 44100
seconds_per_run = 5

p = pyaudio.PyAudio()

# Modified for stereo input (channels=2)
stream = p.open(
    rate=input_rate,
    channels=2,  # Changed from 1 to 2 for stereo
    format=pyaudio.paInt16,
    input=True,
    input_device_index=device_index
)

print('Start recording')
audio_data = stream.read(num_frames=input_rate * seconds_per_run, exception_on_overflow=False)
print('Stopped recording')

# Convert to numpy array and reshape for stereo
audio_formatted = np.frombuffer(audio_data, dtype=np.int16)
audio_formatted = audio_formatted.reshape((-1, 2))  # Reshape to (samples, 2 channels)

print(f'Audio shape: {audio_formatted.shape}')  # Should show (240000, 2) for 5 seconds

# Save as stereo WAV file
soundfile.write('output_stereo.wav', audio_formatted, input_rate)

# Cleanup
stream.stop_stream()
stream.close()
p.terminate()