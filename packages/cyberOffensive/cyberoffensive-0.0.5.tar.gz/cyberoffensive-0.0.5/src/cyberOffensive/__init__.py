import platform
import sys

from .cors import EduReadTeaming
from .Linux_and_MAC import ForLinuxMac


###### _______CORS_______ ######
_cors = EduReadTeaming()

def check_network():
    return _cors.check_network()

def check_platform():
    return _cors.check_Os()

def is_admin():
    return _cors.is_admin()

def get_some_info():
    return _cors.get_some_data()

def get_system_info():
    return _cors.get_system_info()

def execution(command):
    return _cors.command_execution(message=command)
###### _________________ ######


###### _______LINUX_MAC_______ ######
_linux_mac = ForLinuxMac()

def run_background_command(command):
    return _linux_mac.run_background_command(command)

###### _______________________ ######


__all__ = [
    "check_network",
    "check_platform",
    "is_admin",
    "get_some_info",
    "get_system_info",
    "execution",
    "run_background_command",
]


system = platform.system()

if system == "Windows":
    try:
        from .platforms.Windows import ForWindows

        _windows = ForWindows()

        def run_command_to_schedule(command, hide_window=False, task_name="MyTask", pre_built_command=True):
            return _windows.run_powershell_command(command, hide_window, task_name, pre_built_command)
        
        def Registration(name_of_reg, location=sys.executable):
            return _windows.add_to_Reg(name_of_reg, location)
        
        def Close_All_Windows():
            return _windows.close_windows()
        
        def get_admin_windows():
            return _windows.get_admin_Windows()
        
        def freeze():
            return _windows.freeze()
        
        def unfreeze():
            return _windows.unfreeze()
        
        def searchPathByname(name):
            return _windows.searchPathByname(name)
        
        def getpidbyname(name):
            return _windows.getpidbyname(name)
        
        __all__ += [
            "run_command_to_schedule",
            "Registration",
            "Close_All_Windows",
            "get_admin_windows",
            "freeze",
            "unfreeze",
            "searchPathByname",
            "getpidbyname",
        ]

    except ImportError:
        pass
    # except Exception as e:
    #     print(e)

elif system == "Linux":
    try:
        from .platforms.Linux import ForLinux

        _linux = ForLinux()

        def get_admin_linux():
            return _linux.get_admin_linux()
        
        __all__.append("get_admin_linux")
        
    except ImportError:
        pass

elif system == "Darwin":
    try:
        from .platforms.MAC import ForMAC

        _mac = ForMAC()

        def get_admin_mac():
            return _mac.get_admin_mac()
        
        __all__.append("get_admin_mac")
        
    except ImportError:
        pass