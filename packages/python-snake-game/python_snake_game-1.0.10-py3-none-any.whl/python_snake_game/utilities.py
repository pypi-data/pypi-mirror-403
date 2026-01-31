import sys
import os
import time

if sys.platform.startswith('win'):
    import msvcrt
elif sys.platform.startswith('linux'):
    import tty
    import termios
    import select


class KeyboardHandling:
    @staticmethod
    def windows(custom='wasd'):
        up_button,left_button,down_button,right_buttom =[bytes(x,encoding='utf-8') for x in custom ]

        if not msvcrt.kbhit():
            return -1  # no key pressed

        key = -1
        first_char = msvcrt.getch()

        if first_char == b'\xe0':  # special key (arrow keys)
            second_char = msvcrt.getch()
            if second_char == b'H':
                key = 0  # up
            elif second_char == b'P':
                key = 2  # down
            elif second_char == b'M':
                key = 3  # right
            elif second_char == b'K':
                key = 1  # left

        elif first_char in [up_button, b'8']:
            key = 0
        elif first_char in [down_button, b'2']:
            key = 2
        elif first_char in [right_buttom, b'6']:
            key = 3
        elif first_char in [left_button, b'4']:
            key = 1
        elif first_char == b' ':
            key = 4
        elif first_char == b'\x03':  # Ctrl+C
            key = 5

        return key


def handle_keyboard(custom):
    if sys.platform.startswith('win'):
        return KeyboardHandling.windows(custom)
    elif sys.platform.startswith('linux'):
        return KeyboardHandling.linux()
    else:
        raise RuntimeError("This game is made only for Windows and Linux .")


# DEV UTILITIES 
# # FOR LOGGING
def custom_print (*args):
    print(*args,sep="     ",file=open("output.txt","a",encoding="utf-8"))