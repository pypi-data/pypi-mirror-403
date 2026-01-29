import ctypes
import time

KEYEVENTF_KEYUP = 0x0002
SYMBOL_MAP = {
    '<': 0xBC, '>': 0xBE, ':': 0xBA, '"': 0xDE, "'": 0xDE,
    ' ': 0x20, '+': 0xBB, '-': 0xBD, '=': 0xBB, '.': 0xBE,
    '\n': 0x0D, '\t': 0x09
}

def press_raw(code, shift=False):
    if shift: ctypes.windll.user32.keybd_event(0x10, 0, 0, 0)
    ctypes.windll.user32.keybd_event(code, 0, 0, 0)
    ctypes.windll.user32.keybd_event(code, 0, KEYEVENTF_KEYUP, 0)
    if shift: ctypes.windll.user32.keybd_event(0x10, 0, KEYEVENTF_KEYUP, 0)

def type_text(text, delay=0.05):
    for char in text:
        if char in SYMBOL_MAP:
            needs_shift = char in '<>:"'
            press_raw(SYMBOL_MAP[char], shift=needs_shift)
        elif char.isupper(): press_raw(ord(char), shift=True)
        elif char.islower(): press_raw(ord(char.upper()), shift=False)
        elif char.isdigit(): press_raw(ord(char), shift=False)
        time.sleep(delay)

def press_key(key_name):
    """Press special keys like 'enter', 'space', 'esc'"""
    key_codes = {"enter": 0x0D, "space": 0x20, "esc": 0x1B, "tab": 0x09, "backspace": 0x08}
    code = key_codes.get(key_name.lower())
    if code: press_raw(code)
