import os
import sys

class ForLinux:
    def __init__(self):
        pass

    def get_admin_linux(self):
        os.execvp("sudo", ["sudo", sys.executable] + sys.argv)