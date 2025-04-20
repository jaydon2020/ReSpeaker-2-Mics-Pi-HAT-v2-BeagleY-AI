import pyaudio

audio = pyaudio.PyAudio()

dev_info = audio.get_host_api_info_by_index(0)
num_dev = dev_info.get('deviceCount')

for k in range(0, num_dev):
    if (audio.get_device_info_by_host_api_device_index(0, k).get('maxInputChannels')) > 0:
        dev_name = audio.get_device_info_by_host_api_device_index(0, k).get('name')
        print("Audio Input ID and name: ", k, " - ", dev_name)