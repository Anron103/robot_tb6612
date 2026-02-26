import sys
from audio_device_manager import test_audio_system, setup_audio_devices
# test file to check volume from robot 
def interactive_setup():
    print("\n" + "="*70)
    print("raspberry pi 4 audio device setup")
    print("="*70)
    print("\nthis tool will help you configure audio input and output devices.")
    print("press ctrl+c at any time to exit.\n")
    try:
        input("\npress enter to begin audio system tsst")
        test_audio_system()
        print("\n" + "="*70)
        print("test results")
        print("="*70)
        print("\ndid you hear the test tone?")
        print("  1. yes, audio is working correctly")
        print("  2. no, i didn't hear anything")
        print("  3. i heard something but it was distorted")
        choice = input("\nenter your choice (1/2/3): ").strip()
        if choice == '1':
            print("\naudio system is working correctly!")
            print("\nto make these settings permanent, update config.py:")
            print("  - audio_input_device_index: set to your microphone device index")
            print("  - audio_output_device_name: set to your speaker device name")
        elif choice == '2':
            print("\nno audio detected. troubleshooting steps:")
            print("  1. check that speakers are connected and powered on")
            print("  2. run 'alsamixer' to check volume levels")
            print("  3. try 'sudo raspi-config' to configure audio output")
            print("  4. check /etc/asound.conf for correct device configuration")
        elif choice == '3':
            print("\naudio quality issues detected. try:")
            print("  1. adjust volume with 'alsamixer'")
            print("  2. check cable connections")
            print("  3. try different audio_buffer_size in config.py (try 1024 or 4096)")
        else:
            print("\ninvalid choice. please run setup again.")
        print("\n" + "="*70)
    except KeyboardInterrupt:
        print("\nsetup cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\nerror during setup: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    interactive_setup()