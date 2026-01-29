import ctypes
import time

# Access user32 DLL
user32 = ctypes.windll.user32

# Mouse event constants
LEFTDOWN = 0x0002
LEFTUP = 0x0004
RIGHTDOWN = 0x0008
RIGHTUP = 0x0010

# Move the mouse
def set_mouse_position(x, y):
    user32.SetCursorPos(x, y)


def glide_mouse(target_x, target_y, duration=1.0):
    # Get current position
    class POINT(ctypes.Structure):
        _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
    
    pt = POINT()
    ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
    start_x, start_y = pt.x, pt.y
    
    # Calculate how many steps to take
    steps = 100 
    sleep_time = duration / steps
    
    for i in range(1, steps + 1):
        # Linear interpolation (LERP) formula
        current_x = int(start_x + (target_x - start_x) * (i / steps))
        current_y = int(start_y + (target_y - start_y) * (i / steps))
        
        # Move the mouse to the new small step
        ctypes.windll.user32.SetCursorPos(current_x, current_y)
        time.sleep(sleep_time)



# Left click
def left_click():
    user32.mouse_event(LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)  # tiny delay
    user32.mouse_event(LEFTUP, 0, 0, 0, 0)

# Right click
def right_click():
    user32.mouse_event(RIGHTDOWN, 0, 0, 0, 0)
    time.sleep(0.05)
    user32.mouse_event(RIGHTUP, 0, 0, 0, 0)


