# 🚀 MoreModule
**The easiest way to automate Windows without installing anything!**

---

## 💡 Why use MoreModule?


- ✅ **Zero Dependencies:** Works with standard Python (no `pip install` needed).
- ✅ **Beginner Friendly:** Scratch-style commands like `glide_mouse()`.
- ✅ **Lightweight:** Uses only built-in Windows `ctypes` and `tkinter`.

---

## 🛠️ How to Setup
1. Create a new file named `whateveryoulike.py` in your project folder.
2. Copy and paste the **Full Source Code** (found at the bottom of this page) into that file.
3. In your own script, just type `import moremodule` and start coding!

---

## 📖 Examples & Usage

### 🖱️ Smooth Mouse Glide (Scratch Style)
Move the mouse smoothly over time instead of teleporting!
```python
import moremodule

# Move to X:500, Y:500 over 2 seconds
moremodule.glide_mouse(500, 500, duration=2.0)
```

---


### 🖱️ Set mouse postion
```python
import moremodule
moremodule.set_mouse_position(100,200) # set mouse position to X:100, Y:200
```
### 🖱️ Click Mouse
```python
import moremodule

# Click the right button
moremodule.right_click()
# CLick the left button
moremodule.left_click()
```

---

### Random number!
```python
import moremodule
print(moremodule.randint(1,100)) # example: 36
primt(moremodule.unitform(0.1,0.9)) # example: 0.5
```

---

### Wait time!:
```python
import moremodule
moremodule.wait(1) # wait 1 second
```

---

### Get the screen height and width
```python
import moremodule
print(moremodule.get_screen_height()) # print your height

print(moremodule.get_screen_width()) # print your width
```

### Doing something with your keyboard!
```python
import moremodule
moremodule.type_text("This is an example!", delay=0.1) # write "This is an example" per 0.1 second
moremodule.press_key("enter") # press 'enter'
```