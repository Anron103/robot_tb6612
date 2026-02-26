# tts server parameters
SERVER_URL = "http://192.168.137.1:8000"  # replace with your windows server ip
TTS_SPEAKER = "baya"
TTS_SAMPLE_RATE = 48000
TTS_TIMEOUT = 30
HEALTH_CHECK_TIMEOUT = 5

# stt parameters
STT_SAMPLE_RATE = 16000
STT_LANGUAGE = 'ru-RU'

# audio device parameters
# set to None for auto-detection, or specify device index (0, 1, 2, etc.)
AUDIO_INPUT_DEVICE_INDEX = None  # microphone input device
AUDIO_OUTPUT_DEVICE_NAME = 'default'  # pygame mixer device name
AUDIO_BUFFER_SIZE = 2048  # pygame mixer buffer size
AUDIO_FREQUENCY = 44100  # audio playback frequency

# movement parameters
BASE_SPEED = 60
BACKWARD_TIME = 0.7
TURN_TIME = 1.3
OBSTACLE_AVOIDANCE_SPEED = 70
COMPLEX_MANEUVER_SPEED = 80

# voice control parameters
WAKE_WORDS = ['радик']
WAKE_COOLDOWN = 3.0  # seconds between wake word activations
COMMAND_LISTEN_TIMEOUT = 15.0  # maximum time to listen for command
BACKGROUND_LISTEN_TIMEOUT = 10.0  # background listening timeout
BACKGROUND_PHRASE_LIMIT = 5.0  # maximum phrase duration in background

# speech recognition parameters
RECOGNITION_TIMEOUT = 4.0
PHRASE_TIME_LIMIT = 12.0
RETRY_COUNT = 3
CALIBRATION_DURATION = 2.0  # microphone calibration duration

# energy threshold for microphone
ENERGY_THRESHOLD = 500
DYNAMIC_ENERGY_THRESHOLD = True
DYNAMIC_ENERGY_ADJUSTMENT_DAMPING = 0.15
PAUSE_THRESHOLD = 0.8
PHRASE_THRESHOLD = 0.1

# thread control parameters
UPDATE_LOOP_FPS = 30
SENSOR_READ_DELAY = 0.05
MOVEMENT_DELAY = 0.05
THREAD_SLEEP_INTERVAL = 0.1

# eye animation parameters
RANDOM_EYE_CHANCE = 0.05  # 5% chance per iteration
EYE_ANIMATION_INTERVAL_MIN = 2.0  # minimum seconds between eye changes
EYE_ANIMATION_INTERVAL_MAX = 4.0  # maximum seconds between eye changes
GESTURE_EYE_DELAY = 0.2  # delay between eye animation frames in gesture

# display parameters
ROBOT_DISPLAY_SIZE = (848, 480)
ROBOT_DISPLAY_POSITION = (0, 0)
# tts interface display (smaller overlay)
TTS_DISPLAY_SIZE = (480, 320)
TTS_DISPLAY_POSITION = (0, 0)

#gesture parameters
GESTURE_DELAY_SHORT = 0.3  # short gesture movement duration
GESTURE_DELAY_MEDIUM = 0.6  # medium gesture movement duration
GESTURE_DELAY_BETWEEN = 0.2  # delay between gesture movements

# signal definitions
# robot control signals
SIGNAL_TOGGLE_MODE = 'SIGUSR1'  # toggle autonomous/manual mode
SIGNAL_FORWARD = 'SIGUSR2'      # move forward
SIGNAL_BACKWARD = 'SIGWINCH'    # move backward
SIGNAL_TURN_LEFT = 'SIGIO'      # turn left
SIGNAL_TURN_RIGHT = 'SIGPWR'    # turn right
SIGNAL_STOP = 'SIGXCPU'         # stop motors
SIGNAL_PAUSE = 'SIGTRAP'        # pause robot
SIGNAL_RESUME = 'SIGALRM'       # resume robot
SIGNAL_RESET_SENSORS = 'SIGPROF'  # reset sensor state

# system state definitions
STATE_WAITING_FOR_WAKE_WORD = 0
STATE_LISTENING_COMMAND = 1
STATE_PROCESSING_RESPONSE = 2

# eye image names
EYE_IMAGES = {
    'closed': 'closed',
    'common': 'common',
    'crazy': 'crazy',
    'cry': 'cry',
    'error': 'error',
    'evil': 'evil',
    'flinch': 'flinch',
    'happy': 'happy',
    'irritate': 'irritate',
    'pop': 'pop',
    'rolled': 'rolled',
    'sad': 'sad'
}
# file paths
TEMP_AUDIO_FILE = '/tmp/response.wav'