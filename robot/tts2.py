import os
import sys
import signal
import queue
import threading
import time
import psutil
import requests
import pygame
import speech_recognition as sr
import base64
import random
from config import *
from display_overlay import show_image

# get robot pid from command line
robot_pid = None
if len(sys.argv) > 1:
    try:
        robot_pid = int(sys.argv[1])
    except ValueError:
        print("error: invalid robot pid")
        sys.exit(1)

pygame.mixer.init()

# thread-safe command queue
command_queue = queue.Queue(maxsize=10)
wake_word_queue = queue.Queue(maxsize=5)

# system state with thread-safe access
class SystemState:
    WAITING_FOR_WAKE_WORD = 0
    LISTENING_COMMAND = 1
    PROCESSING_RESPONSE = 2
    current_state = SystemState.WAITING_FOR_WAKE_WORD
    state_lock = threading.Lock()
    last_wake_time = 0
    last_command_time = 0
    
#thread-safe audio player
class AudioPlayer:
    def __init__(self):
        self.playing = False
        self.lock = threading.Lock()
    #play audio data in background thread
    def play_audio_from_server(self, audio_data):
        def playback_thread():
            with self.lock:
                self.playing = True
            try:
                temp_filename = "/tmp/response.wav"
                with open(temp_filename, 'wb') as f:
                    f.write(audio_data)
                print("playing")
                pygame.mixer.music.load(temp_filename)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    time.sleep(0.05)
                try:
                    os.remove(temp_filename)
                except:
                    pass
                print("playback complete")
            except Exception as e:
                print(f"playback error: {e}")
                show_image('error')
                time.sleep(1.0)
                show_image('common')
            finally:
                with self.lock:
                    self.playing = False

        threading.Thread(target=playback_thread, daemon=True).start()
        
#stop playback
    def stop(self):
        with self.lock:
            try:
                pygame.mixer.music.stop()
            except:
                pass
            self.playing = False
            
#speech recognition with continuous background listening
class SileroSTTClient:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = None
        self.running = True
        #recognizer parameters from config
        self.recognizer.energy_threshold = ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_threshold = DYNAMIC_ENERGY_THRESHOLD
        self.recognizer.dynamic_energy_adjustment_damping = DYNAMIC_ENERGY_ADJUSTMENT_DAMPING
        self.recognizer.pause_threshold = PAUSE_THRESHOLD
        self.recognizer.phrase_threshold = PHRASE_THRESHOLD
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                print(f"calibrating microphone ({CALIBRATION_DURATION} seconds)")
                self.recognizer.adjust_for_ambient_noise(source, duration=CALIBRATION_DURATION)
                print("microphone ready")
        except Exception as e:
            print(f"microphone error: {e}")
            try:
                self.microphone = sr.Microphone()
            except Exception as e2:
                print(f"failed to initialize microphone: {e2}")
                self.microphone = None
                
    #thread for continuous wake word detection
    def continuous_listening(self):
        global last_wake_time
        print("listening thread started")
        if self.microphone is None:
            print("error: microphone not available")
            return
        while self.running:
            try:
                with self.microphone as source:
                    audio = self.recognizer.listen(
                        source,
                        timeout=BACKGROUND_LISTEN_TIMEOUT,
                        phrase_time_limit=BACKGROUND_PHRASE_LIMIT
                    )
                    text = self.recognizer.recognize_google(audio, language=STT_LANGUAGE).lower()
                    print(f"background recognized: '{text}'")
                    # check for wake word
                    if any(word in text for word in WAKE_WORDS):
                        current_time = time.time()
                        if current_time - last_wake_time >= WAKE_COOLDOWN:
                            last_wake_time = current_time
                            print(f"wake word detected: '{text}'")
                            wake_word_queue.put(text)
                            # animate eyes on wake word
                            threading.Thread(target=self._animate_wake_eyes, daemon=True).start()
                    with state_lock:
                        if current_state == SystemState.LISTENING_COMMAND:
                            if text and not any(word in text for word in WAKE_WORDS):
                                print(f"command received during listening: '{text}'")
                                try:
                                    command_queue.put_nowait(text)
                                except queue.Full:
                                    pass
            except sr.WaitTimeoutError:
                continue
            except sr.UnknownValueError:
                continue
            except sr.RequestError as e:
                print(f"speech recognition service error: {e}")
                time.sleep(THREAD_SLEEP_INTERVAL)
            except Exception as e:
                if "recording" not in str(e).lower():
                    print(f"background recognition error: {e}")
                time.sleep(THREAD_SLEEP_INTERVAL)
                
 #animate eyes when wake word is detected
    def _animate_wake_eyes(self):
        show_image('irritate')
        time.sleep(GESTURE_EYE_DELAY)
        show_image('pop')
        time.sleep(GESTURE_EYE_DELAY)
        show_image('rolled')

   #command listening with visual feedback
    def listen_for_command(self, timeout=COMMAND_LISTEN_TIMEOUT):
        print("listening")
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                if not command_queue.empty():
                    return command_queue.get_nowait()
                time.sleep(0.1)
            except queue.Empty:
                continue
        print("command listening timeout")
        return None


#        send text to server and get audio response with error flag
#        uses /conversation endpoint for api integration
#        returns: (audio_data, is_error)
    def generate_speech(self, text):
        try:
            print(f"requesting com: '{text[:50]}'")
            response = requests.post(
                f"{SERVER_URL}/conversation",
                json={
                    "user_text": text,
                    "speaker": TTS_SPEAKER,
                    "sample_rate": TTS_SAMPLE_RATE
                },
                timeout=TTS_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                audio_base64 = data.get('audio_base64')
                is_error = data.get('is_error', False)
                text_length = data.get('text_length', 0)
                if audio_base64:
                    audio_data = base64.b64decode(audio_base64)
                    print(f"received {len(audio_data)} bytes (error={is_error}, length={text_length})")
                    return audio_data, is_error
                else:
                    print("no audio_base64 in response")
                    return None, False
            else:
                print(f"server error {response.status_code}: {response.text}")
                return None, False
        except requests.exceptions.Timeout:
            print("server connection timeout")
            return None, False
        except requests.exceptions.ConnectionError:
            print("server connection error")
            return None, False
        except Exception as e:
            print(f"tts error: {e}")
            return None, False

# initialize clients
stt_client = SileroSTTClient()
audio_player = AudioPlayer()

def ensure_manual_mode():
    print("switch to M")
    if robot_pid and psutil.pid_exists(robot_pid):
        try:
            os.kill(robot_pid, getattr(signal, SIGNAL_TOGGLE_MODE))
            time.sleep(THREAD_SLEEP_INTERVAL * 5)
            print("manual mode")
            # will show this all the time M is active
            show_image('evil')
        except ProcessLookupError:
            print("error: robot process not found!")
        except Exception as e:
            print(f"error switching mode: {e}")
#kill the robot
def stop_robot():
    if robot_pid and psutil.pid_exists(robot_pid):
        try:
            os.kill(robot_pid, getattr(signal, SIGNAL_STOP))
            time.sleep(THREAD_SLEEP_INTERVAL * 2)
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"error: {e}")
# gestures after detection of the wake word
def execute_gesture_sequence():
    print("gestures S")
    ensure_manual_mode()
    stop_robot()
    time.sleep(THREAD_SLEEP_INTERVAL * 5)
    if robot_pid and psutil.pid_exists(robot_pid):
        try:
            # turn left (short)
            os.kill(robot_pid, getattr(signal, SIGNAL_TURN_LEFT))
            time.sleep(GESTURE_DELAY_SHORT)
            os.kill(robot_pid, getattr(signal, SIGNAL_STOP))
            time.sleep(GESTURE_DELAY_BETWEEN)
            # turn right (medium)
            os.kill(robot_pid, getattr(signal, SIGNAL_TURN_RIGHT))
            time.sleep(GESTURE_DELAY_MEDIUM)
            os.kill(robot_pid, getattr(signal, SIGNAL_STOP))
            time.sleep(GESTURE_DELAY_BETWEEN)
            # turn left (short)
            os.kill(robot_pid, getattr(signal, SIGNAL_TURN_LEFT))
            time.sleep(GESTURE_DELAY_SHORT)
            os.kill(robot_pid, getattr(signal, SIGNAL_STOP))
            time.sleep(GESTURE_DELAY_BETWEEN)
            stop_robot()
            print("gestures C")
        except ProcessLookupError:
            print("error: robot process not found!")
        except Exception as e:
            print(f"gesture execution error: {e}")

def return_to_auto_mode():
    print("returning into A")
    stop_robot()
    time.sleep(THREAD_SLEEP_INTERVAL * 5)
    if robot_pid and psutil.pid_exists(robot_pid):
        try:
            # toggle back to auto mode
            os.kill(robot_pid, getattr(signal, SIGNAL_TOGGLE_MODE))
            time.sleep(THREAD_SLEEP_INTERVAL * 5)
            # reset sensors
            os.kill(robot_pid, getattr(signal, SIGNAL_RESET_SENSORS))
            time.sleep(THREAD_SLEEP_INTERVAL * 5)
            show_image('common')
        except ProcessLookupError:
            pass
        except Exception as e:
            print(f"error returning to auto mode: {e}")

#    process user command with non-blocking tts playback
#    handles error flag from server for api failure detection
def process_command(clean_command):
    global current_state
    with state_lock:
        current_state = SystemState.PROCESSING_RESPONSE
    print(f"processing c: {clean_command}")
    show_image('rolled')
    # get audio response with error flag
    audio_data, is_error = stt_client.generate_speech(clean_command)
    if audio_data:
        print("response handling")
        # show error eyes if api failed, otherwise normal speaking face
        if is_error:
            print("api error detected - showing error eyes")
            show_image('error')
        else:
            show_image('happy')
        audio_player.play_audio_from_server(audio_data)
        # eye animation during playback
        def eye_animation():
            time.sleep(1.5)
            if not is_error:
                show_image('flinch')
            while audio_player.playing:
                time.sleep(0.1)
            show_image('common')
        threading.Thread(target=eye_animation, daemon=True).start()
    else:
        print("failed to get audio response")
        show_image('error')
        # this is unnecessary but why not
        time.sleep(1.5)
        show_image('common')
    # return to auto mode after delay
    def delayed_return():
        time.sleep(3.0)
        return_to_auto_mode()
        with state_lock:
            global current_state
            current_state = SystemState.WAITING_FOR_WAKE_WORD
            show_image('closed')
    threading.Thread(target=delayed_return, daemon=True).start()

def check_server_connection():
    try:
        response = requests.get(f"{SERVER_URL}/health", timeout=HEALTH_CHECK_TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            if data.get('model_loaded'):
                print("server connected and model loaded")
                return True
            else:
                print("server connected but model not loaded")
                return False
        else:
            print(f"server error: {response.status_code}")
            return False
    except Exception as e:
        print(f"failed to connect to server: {e}")
        return False

def main():
    global current_state, last_wake_time
    # do not initialize overlay here - robot process owns it
    # only use show_image() to control existing overlay
    print(f"system started. robot pid: {robot_pid}")
    print(f"server: {SERVER_URL}")
    if not check_server_connection():
        print("could not connect to server")
        return
    # start continuous background listening
    listening_thread = threading.Thread(
        target=stt_client.continuous_listening,
        daemon=True,
        name="STT-Listener"
    )
    listening_thread.start()
    print("continuous background listening started")
    # show initial eye state (overlay created by robot_tb6612.py)
    show_image('common')
    try:
        print("system ready")
        while True:
            try:
                wake_word_text = wake_word_queue.get_nowait()
                print(f"wake word activated: '{wake_word_text}'")
                execute_gesture_sequence()
                with state_lock:
                    current_state = SystemState.LISTENING_COMMAND
                print("listening for command...")
                show_image('irritate')
                command = stt_client.listen_for_command(timeout=COMMAND_LISTEN_TIMEOUT)
                if command:
                    print(f"processing command: '{command}'")
                    threading.Thread(
                        target=process_command,
                        args=(command,),
                        daemon=True,
                        name="Command-Processor"
                    ).start()
                else:
                    print("no command received, returning to wait state")
                    return_to_auto_mode()
                    with state_lock:
                        current_state = SystemState.WAITING_FOR_WAKE_WORD
                    show_image('closed')
            except queue.Empty:
                # random eye animations during idle
                with state_lock:
                    if current_state == SystemState.WAITING_FOR_WAKE_WORD:
                        if random.random() < RANDOM_EYE_CHANCE:
                            show_image(random.choice(['common', 'happy', 'crazy']))
                time.sleep(THREAD_SLEEP_INTERVAL)
    except KeyboardInterrupt:
        print("shutting down...")
    finally:
        if stt_client:
            stt_client.running = False
        audio_player.stop()
        print("tts system stopped")

if __name__ == "__main__":
    main()