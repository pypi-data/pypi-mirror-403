import pyautogui as pya
import pyperclip
import time


def copy_clipboard():
    pya.hotkey("ctrl", "c")
    time.sleep(0.01)
    return pyperclip.paste()