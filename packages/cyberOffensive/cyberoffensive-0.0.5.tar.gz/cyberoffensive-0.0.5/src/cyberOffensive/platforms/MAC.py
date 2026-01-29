import os
import sys


class ForMAC:
    def __init__(self):
        print("For only MAC")

    def get_admin_mac(self):
        script = f'''
        do shell script "{sys.executable} {' '.join(sys.argv)}" with administrator privileges
        '''
        os.system(f"osascript -e '{script}'")

        sys.exit()