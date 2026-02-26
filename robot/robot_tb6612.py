import RPi.GPIO as GPIO
import time
import threading
import xr_gpio
import os
import signal
import random
import pygame
from display_overlay import show_image, init_overlay

# sensor pins
LEFT_IR = xr_gpio.IR_L
RIGHT_IR = xr_gpio.IR_R

# motor pwm controllers
pwm_a = xr_gpio.ENA_pwm
pwm_b = xr_gpio.ENB_pwm

# motor control pins
AIN1 = xr_gpio.IN1
AIN2 = xr_gpio.IN2
BIN1 = xr_gpio.IN3
BIN2 = xr_gpio.IN4

# movement parameters
BACKWARD_TIME = 0.7
TURN_TIME = 1.3
BASE_SPEED = 60

class RobotState:
    def __init__(self):
        self.lock = threading.Lock()
        self.left_ir = False
        self.right_ir = False
        self.running = True
        self.autonomous = True  # start in autonomous mode
        self.paused = False
        self.pre_pause_mode = None
        self.force_sensor_update = False
        self.last_sensor_read = (False, False)
        self.sensor_reset_requested = False

robot_state = RobotState()
#set motor pwm duty cycle
def set_motor_speed(left, right):
    pwm_a.ChangeDutyCycle(left)
    pwm_b.ChangeDutyCycle(right)
#move robot forward
def motor_forward(speed=BASE_SPEED):
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)
    set_motor_speed(speed, speed)
#move robot backward
def motor_backward(speed=BASE_SPEED):
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    set_motor_speed(speed, speed)
#turn robot left
def motor_turn_left(speed=BASE_SPEED, duration=None):
    GPIO.output(AIN1, GPIO.HIGH)
    GPIO.output(AIN2, GPIO.LOW)
    GPIO.output(BIN1, GPIO.HIGH)
    GPIO.output(BIN2, GPIO.LOW)
    set_motor_speed(speed, speed)
    if duration:
        time.sleep(duration)
        motor_stop()
#turn robot right
def motor_turn_right(speed=BASE_SPEED, duration=None):
    GPIO.output(AIN1, GPIO.LOW)
    GPIO.output(AIN2, GPIO.HIGH)
    GPIO.output(BIN1, GPIO.LOW)
    GPIO.output(BIN2, GPIO.HIGH)
    set_motor_speed(speed, speed)
    if duration:
        time.sleep(duration)
        motor_stop()
#stop all motors
def motor_stop():
    set_motor_speed(0, 0)
    for pin in [AIN1, AIN2, BIN1, BIN2]:
        GPIO.output(pin, GPIO.LOW)
#reset sensor state for forced update
def reset_sensor_state():
    with robot_state.lock:
        robot_state.force_sensor_update = True
        robot_state.last_sensor_read = (False, False)
        robot_state.left_ir = False
        robot_state.right_ir = False
        robot_state.sensor_reset_requested = True
    print("sensor state reset - forced update")
#handler for auto/manual mode switching
def mode_handler(sig, frame):
    robot_state.autonomous = not robot_state.autonomous
    if robot_state.autonomous:
        print("mode: A")
        reset_sensor_state()
        motor_forward()
        time.sleep(0.1)
        show_image('common')
    else:
        print("mode: M")
        motor_stop()
        show_image('evil')
#handler for pause
def pause_handler(sig, frame):
    if not robot_state.paused:
        robot_state.pre_pause_mode = robot_state.autonomous
        robot_state.paused = True
        motor_stop()
        print("robot paused")
        show_image('closed')
#handler for resume
def resume_handler(sig, frame):
    if robot_state.paused:
        robot_state.paused = False
        robot_state.autonomous = robot_state.pre_pause_mode
        print("robot resumed")
        if robot_state.autonomous:
            reset_sensor_state()
            show_image('common')
#handler for manual control
def manual_handler(sig, frame):
    if robot_state.paused:
        return
    if not robot_state.autonomous:
        if sig == signal.SIGUSR2:
            motor_forward()
            print("forward")
        elif sig == signal.SIGWINCH:
            motor_backward()
            print("backward")
        elif sig == signal.SIGIO:
            motor_turn_left()
            print("turn left")
        elif sig == signal.SIGPWR:
            motor_turn_right()
            print("turn right")
        elif sig == signal.SIGXCPU:
            motor_stop()
            print("stop")

def sensor_reset_handler(sig, frame):
    reset_sensor_state()
#handle keyboard input from pygame overlay window
def handle_keyboard_input():
    last_key_time = {}
    key_cooldown = 0.15  # 150ms cooldown between same key presses/ not the best solution
    while robot_state.running:
        current_time = time.time()
        # process all pygame events (not just one per iteration)
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.KEYDOWN:
                key = event.key
                key_name = pygame.key.name(key)
                # implement cooldown to prevent key repeat issues
# ALL this works but sometimes pressed button just dont register
                if key in last_key_time:
                    if current_time - last_key_time[key] < key_cooldown:
                        continue  # skip if too soon after last press
                last_key_time[key] = current_time
                # handle keyboard commands
                if key == pygame.K_w or key == pygame.K_UP:
                    print(f"w/up pressed")
                    if not robot_state.autonomous and not robot_state.paused:
                        motor_forward()
                elif key == pygame.K_s or key == pygame.K_DOWN:
                    print(f"s/down pressed")
                    if not robot_state.autonomous and not robot_state.paused:
                        motor_backward()
                elif key == pygame.K_a or key == pygame.K_LEFT:
                    print(f"a/left pressed")
                    if not robot_state.autonomous and not robot_state.paused:
                        motor_turn_left()
                elif key == pygame.K_d or key == pygame.K_RIGHT:
                    print(f"d/right pressed")
                    if not robot_state.autonomous and not robot_state.paused:
                        motor_turn_right()
                elif key == pygame.K_SPACE:
                    print("space pressed")
                    motor_stop()
                elif key == pygame.K_r:
                    print("r pressed - toggle mode")
                    mode_handler(None, None)
                elif key == pygame.K_p:
                    print("p pressed - pause/resume")
                    if robot_state.paused:
                        resume_handler(None, None)
                    else:
                        pause_handler(None, None)
                elif key == pygame.K_q:
                    print("\nq pressed - quitting system...")
                    robot_state.running = False
                    return
        time.sleep(0.01)
#thread for reading sensor data
def sensor_thread():
    last_reported = (False, False)
    while robot_state.running:
        if robot_state.paused:
            time.sleep(0.1)
            continue
        current_left = not GPIO.input(LEFT_IR)
        current_right = not GPIO.input(RIGHT_IR)
        current_state = (current_left, current_right)
        with robot_state.lock:
            robot_state.left_ir = current_left
            robot_state.right_ir = current_right
            if robot_state.force_sensor_update:
                with robot_state.lock:
                    robot_state.force_sensor_update = False
                last_reported = (False, False)
        if current_state != last_reported:
            print(f"sensors: left={current_left}, right={current_right}")
            last_reported = current_state
        time.sleep(0.05)
#thread for autonomous movement
def movement_thread():
    last_processed = (False, False)
    last_eye_change = 0
    eye_cycle = ['common', 'happy', 'crazy']
    eye_index = 0
    while robot_state.running:
        if robot_state.paused or not robot_state.autonomous:
            time.sleep(0.1)
            continue
        current_time = time.time()
        with robot_state.lock:
            left, right = robot_state.left_ir, robot_state.right_ir
            force_update = robot_state.force_sensor_update
            sensor_reset = robot_state.sensor_reset_requested
        if left and right and (current_time - last_eye_change > random.uniform(2.0, 4.0)):
            eye_index = (eye_index + 1) % len(eye_cycle)
            show_image(eye_cycle[eye_index])
            last_eye_change = current_time
        if force_update or sensor_reset or (left, right) != last_processed:
            print(f"processing movement: left={left}, right={right}")
            if left and right:
                motor_forward()
            elif not left and right:
                motor_backward(70)
                time.sleep(BACKWARD_TIME)
                motor_turn_right(70, TURN_TIME)
                show_image('irritate')
                time.sleep(0.5)
                show_image('common')
            elif left and not right:
                motor_backward(70)
                time.sleep(BACKWARD_TIME)
                motor_turn_left(70, TURN_TIME)
                show_image('irritate')
                time.sleep(0.5)
                show_image('common')
            elif not left and not right:
                motor_backward(80)
                time.sleep(BACKWARD_TIME)
                motor_turn_right(80, TURN_TIME)
                show_image('crazy')
                time.sleep(0.5)
                show_image('common')
            last_processed = (left, right)
            with robot_state.lock:
                robot_state.force_sensor_update = False
                robot_state.sensor_reset_requested = False
        time.sleep(0.05)

def main():
    time.sleep(1)
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BCM)
    try:
        for pin in [AIN1, AIN2, BIN1, BIN2]:
            GPIO.setup(pin, GPIO.OUT)
        # initialize overlay before starting threads
        init_overlay(screen_size=(848, 450)) # 848, 450 for top panel to show itself | 848, 480 for full screen
        show_image('closed')
        # register signal handlers
        signal.signal(signal.SIGUSR1, mode_handler)
        signal.signal(signal.SIGUSR2, manual_handler)
        signal.signal(signal.SIGWINCH, manual_handler)
        signal.signal(signal.SIGIO, manual_handler)
        signal.signal(signal.SIGPWR, manual_handler)
        signal.signal(signal.SIGXCPU, manual_handler)
        signal.signal(signal.SIGTRAP, pause_handler)
        signal.signal(signal.SIGALRM, resume_handler)
        signal.signal(signal.SIGPROF, sensor_reset_handler)
        threads = [
            threading.Thread(target=sensor_thread, daemon=True, name="SensorThread"),
            threading.Thread(target=movement_thread, daemon=True, name="MovementThread"),
            threading.Thread(target=handle_keyboard_input, daemon=True, name="KeyboardThread")
        ]
        for t in threads:
            t.start()
        print(f"robot started. pid: {os.getpid()}")
        print("important: click on the eyes window to enable keyboard controls!")
        print("controls: w/s/a/d/space/r/p/q")
        reset_sensor_state()
        if robot_state.autonomous:
            motor_forward()
            time.sleep(0.2)
            show_image('common')
        while robot_state.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("\nshutting down")
    except Exception as e:
        print(f"error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        robot_state.running = False
        motor_stop()
        try:
            from display_overlay import shutdown_overlay
            shutdown_overlay()
        except:
            pass
        GPIO.cleanup()
        print("robot system stopped")

if __name__ == "__main__":
    main()