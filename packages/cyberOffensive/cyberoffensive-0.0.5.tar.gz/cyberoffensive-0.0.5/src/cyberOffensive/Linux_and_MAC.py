import subprocess
import platform


class ForLinuxMac:
    def __init__(self):
        print(platform.system())

    def run_background_command(self, command: str):
        try:
            subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                stdin=subprocess.DEVNULL
            )

            return True
        
        except Exception as e:
            print(e)

            return False