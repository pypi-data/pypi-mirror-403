import os
import platform

def system_beep(text="system_beep"):
    """
    使系统发声
    """
    system = platform.system()
    if system == "Windows":
        import winsound
        winsound.Beep(1000, 1000)
    elif system == "Darwin":  # macOS
        # 或者播放系统声音
        os.system('afplay /System/Library/Sounds/Ping.aiff')
        os.system(f'say "{text}"')

    elif system == "Linux":
        # 需要安装sox: sudo apt-get install sox
        os.system('play -nq -t alsa synth 1 sine 1000')
    else:
        print("\a")  # 终端响铃
