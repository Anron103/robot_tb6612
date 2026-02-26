import os
import sys
import signal
import time
import subprocess
# launch robot and tts processes
def launch_robot_systems():
    robot_process = subprocess.Popen(
        ['python3', 'robot_tb6612.py'],
        preexec_fn=os.setsid
    )
    robot_pid = robot_process.pid
    tts_process = subprocess.Popen(
        ['python3', 'tts2.py', str(robot_pid)]
    )
    return robot_process, tts_process, robot_pid

def print_controls(robot_pid):
    print("\n" + "="*60)
    print("robot control instructions")
    print("="*60)
    print(f"\nrobot pid: {robot_pid}")
    print("\nkeyboard controls (click on eyes window, then press keys):")
    print("  w - move forward")
    print("  s - move backward")
    print("  a - turn left")
    print("  d - turn right")
    print("  space - stop")
    print("  r - toggle autonomous/manual mode")
    print("  p - pause/resume")
    print("  q - quit system")
    print("\nvoice control:")
    print("  say 'радик' to activate voice commands")
    print("\nimportant: click on the eyes window to give it keyboard focus!")
    print("="*60 + "\n")

def main():
    # launch processes
    robot_proc, tts_proc, robot_pid = launch_robot_systems()
    # print control information
    print_controls(robot_pid)
    try:
        while robot_proc.poll() is None and tts_proc.poll() is None:
            time.sleep(0.5)
    except KeyboardInterrupt:
        print("\nshutting down system")
    finally:
        # clean shutdown
        print("\nstopping processes")
        if robot_proc.poll() is None:
            try:
                print("  stopping robot process")
                os.killpg(os.getpgid(robot_proc.pid), signal.SIGTERM)
                robot_proc.wait(timeout=3.0)
                print("  robot stopped")
            except Exception as e:
                print(f"  force killing robot: {e}")
                try:
                    robot_proc.kill()
                except:
                    pass
        if tts_proc.poll() is None:
            try:
                print("  stopping tts process")
                tts_proc.terminate()
                tts_proc.wait(timeout=3.0)
                print("  tts stopped")
            except Exception as e:
                print(f"  force killing tts: {e}")
                try:
                    tts_proc.kill()
                except:
                    pass
        print("\nsystem stopped")

if __name__ == "__main__":
    main()