import pyaudio
import pygame
import os
import sys

class AudioDeviceManager:
    def __init__(self):
        self.pyaudio_instance = None
        self.input_device_info = None
        self.output_device_info = None
        self.mixer_initialized = False

    def list_audio_devices(self):
        #list all available audio devices
        print("\n" + "="*60)
        print("available audio devices")
        print("="*60)
        try:
            p = pyaudio.PyAudio()
            device_count = p.get_device_count()
            print(f"\ntotal devices found: {device_count}\n")
            for i in range(device_count):
                device_info = p.get_device_info_by_index(i)
                device_name = device_info.get('name', 'Unknown')
                max_input_channels = device_info.get('maxInputChannels', 0)
                max_output_channels = device_info.get('maxOutputChannels', 0)
                device_type = []
                if max_input_channels > 0:
                    device_type.append('INPUT')
                if max_output_channels > 0:
                    device_type.append('OUTPUT')
                print(f"device {i}: {device_name}")
                print(f"  type: {'/'.join(device_type) if device_type else 'NONE'}")
                print(f"  input channels: {max_input_channels}")
                print(f"  output channels: {max_output_channels}")
                print(f"  default sample rate: {device_info.get('defaultSampleRate', 'N/A')}")
                print()
            p.terminate()
            return True
        except Exception as e:
            print(f"error listing audio devices: {e}")
            return False

    def select_input_device(self, device_index=None):
        #select and configure input device (microphone)
        try:
            self.pyaudio_instance = pyaudio.PyAudio()
            if device_index is None:
                # auto-detect default input device
                device_count = self.pyaudio_instance.get_device_count()
                for i in range(device_count):
                    device_info = self.pyaudio_instance.get_device_info_by_index(i)
                    if device_info.get('maxInputChannels', 0) > 0:
                        self.input_device_info = device_info
                        print(f"auto-selected input device: {device_info.get('name')}")
                        return i
                print("warning: no input device found")
                return None
            else:
                # use specified device index
                device_info = self.pyaudio_instance.get_device_info_by_index(device_index)
                self.input_device_info = device_info
                print(f"selected input device: {device_info.get('name')}")
                return device_index
        except Exception as e:
            print(f"error selecting input device: {e}")
            return None

    def initialize_output_device(self, device_name='default', buffer_size=2048, frequency=44100):
        #initialize pygame mixer for audio output
        try:
            # set environment variable for audio device if specified
            if device_name != 'default':
                os.environ['SDL_AUDIODRIVER'] = 'alsa'
                os.environ['AUDIODEV'] = device_name
            # initialize pygame mixer with configured parameters
            pygame.mixer.init(
                frequency=frequency,
                size=-16,  # 16-bit signed
                channels=2,  # stereo
                buffer=buffer_size
            )
            self.mixer_initialized = True
            print(f"audio output initialized: {device_name}")
            print(f"  frequency: {frequency} Hz")
            print(f"  buffer size: {buffer_size} samples")
            return True
        except pygame.error as e:
            print(f"pygame mixer initialization error: {e}")
            print("attempting fallback initialization")
            try:
                # fallback: minimal initialization
                pygame.mixer.init()
                self.mixer_initialized = True
                print("fallback audio initialization successful")
                return True
            except Exception as e2:
                print(f"fallback failed: {e2}")
                return False
        except Exception as e:
            print(f"error initializing audio output: {e}")
            return False

    def test_audio_output(self):
        #test audio output with a simple beep
        if not self.mixer_initialized:
            print("audio output not initialized")
            return False
        try:
            print("you should hear a beep")
            # generate a simple 440Hz tone for 0.5 seconds
            import numpy as np
            import wave
            duration = 0.5
            frequency = 440.0
            sample_rate = 44100
            amplitude = 32767
            t = np.linspace(0, duration, int(sample_rate * duration), False)
            tone = (amplitude * np.sin(2 * np.pi * frequency * t)).astype(np.int16)
            temp_file = '/tmp/test_tone.wav'
            with wave.open(temp_file, 'w') as wf:
                wf.setnchannels(1)
                wf.setsampwidth(2)
                wf.setframerate(sample_rate)
                wf.writeframes(tone.tobytes())
            # play the tone
            pygame.mixer.music.load(temp_file)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(10)
            os.remove(temp_file)
            print("audio test complete")
            return True
        except Exception as e:
            print(f"audio test failed: {e}")
            return False

    def cleanup(self):
        if self.pyaudio_instance:
            try:
                self.pyaudio_instance.terminate()
            except:
                pass
        if self.mixer_initialized:
            try:
                pygame.mixer.quit()
            except:
                pass
        print("audio resources cleaned up")

def setup_audio_devices(device_index=None):
#    complete audio device setup routine
#    returns: (input_device_index, audio_manager_instance)
    from config import AUDIO_INPUT_DEVICE_INDEX, AUDIO_OUTPUT_DEVICE_NAME, AUDIO_BUFFER_SIZE, AUDIO_FREQUENCY
    manager = AudioDeviceManager()
    print("\nsetting up audio devices")
    # list available devices
    manager.list_audio_devices()
    # select input device
    if device_index is None:
        device_index = AUDIO_INPUT_DEVICE_INDEX
    input_device_index = manager.select_input_device(device_index)
    # initialize output device
    output_initialized = manager.initialize_output_device(
        device_name=AUDIO_OUTPUT_DEVICE_NAME,
        buffer_size=AUDIO_BUFFER_SIZE,
        frequency=AUDIO_FREQUENCY
    )
    if not output_initialized:
        print("warning: audio output initialization failed")
        print("system will continue without audio playback")
    return input_device_index, manager

def test_audio_system():
    manager = AudioDeviceManager()
    print("\n audio system test \n")
    # test input
    print("testing input device...")
    input_idx = manager.select_input_device(None)
    if input_idx is not None:
        print("input device configured")
    else:
        print("input device configuration failed")
    # test output
    print("\ntesting output device")
    if manager.initialize_output_device():
        print("output device configured")
        manager.test_audio_output()
    else:
        print("output device configuration failed")
    manager.cleanup()
    print("\n test complete \n")

if __name__ == "__main__":
    test_audio_system()