# -*- coding: windows-1252 -*-
import re
import time
import threading
import tkinter as tk
from tkinter import Text
from pynput import keyboard
from pynput.keyboard import Controller, Key, Listener, KeyCode



class AutoTyper:
    def __init__(self): 
        app_description = """
1. **Graphical User Interface**: The program has a simple GUI with a large text input field and a 'Run' button. Enter your text and commands into this field and start the auto-typing process by clicking the 'Run' button.
2. **Text Input**: The program accepts any text input. This text will be automatically typed out by the program.
3. **Special Commands**: The program recognizes special commands enclosed in square brackets ([]). These commands control the behavior of the auto-typer:
    - `[speed_of_input=500]`: Sets the typing speed of the auto-typer, measured in milliseconds per character. Replace `500` with any positive integer.
    - `[new_line_delay=1000]`: Sets the delay time after the auto-typer presses 'Enter' to create a new line. The delay is measured in milliseconds. Replace `1000` with any positive integer.
    - `[wait_to_continue=0x12]`: Pauses the auto-typer until the user presses the specified key (e.g., '0x12' is the Virtual-Key Code for 'Alt (Right)'). Replace '0x12' with any valid Virtual-Key Code.
    - `[delay=500]`: Pauses the auto-typing process for the specified time (in milliseconds). Replace `500` with any positive integer.
    - `[key=right]: This command instructs the auto-typer to press a specific key. In this case, it’s the right arrow key. You can replace right with up, down, or left to make the auto-typer press the corresponding arrow key.`
4. **Command Execution**: The program executes the special commands as it encounters them in the text.
5. **Text Output**: All other text that is not enclosed in square brackets is typed out by the program as regular text.
6. **Immediate Stop**: Press the 'Escape' key to stop the auto-typing process immediately.
7. **Error Handling**: The program includes error handling to deal with situations such as invalid command formats or non-existent keys.
Example 1:[wait_to_continue=0x10][delay=500][speed_of_input=200][new_line_delay=400][delay=500]

Example 2:[wait_to_continue=0x10][delay=500][speed_of_input=100][new_line_delay=200]
fun main() {
println("This is the first line")
println("This is the second line")
println("This is the third line")[key=right]}
#just a simple example
"""

        self.keyboard = Controller()
        self.commands = {
            'speed_of_input': 1000,
            'new_line_delay': 1000,
            'delay': None,
            'wait_to_continue': None,
            'key': None
        }
        self.root = tk.Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Make the window resizable
        self.root.resizable(True, True)

        # Use grid instead of pack for the textbox
        self.text_input = Text(self.root)
        self.text_input.grid(sticky='nsew')
        self.text_input.insert('1.0', app_description)

        # Create a frame to hold the buttons
        button_frame = tk.Frame(self.root)
        button_frame.grid(row=1, column=0, sticky='ew')

        self.run_button = tk.Button(button_frame, text='Run', command=self.run)
        self.run_button.pack(side=tk.LEFT)

        # Add clear button
        self.clear_button = tk.Button(button_frame, text='Clear', command=self.clear_text)
        self.clear_button.pack(side=tk.LEFT)

        self.stop_typing = threading.Event()

        # Configure the grid to expand the textbox when the window is resized
        self.root.grid_rowconfigure(0, weight=1)
        self.root.grid_columnconfigure(0, weight=1)

    def clear_text(self):
        self.text_input.delete('1.0', 'end')  # Clear the text input field        

    def getValOfKey(self, key):
        VK_CODE = {
            'Key.shift': 0x10,
            'Key.ctrl_l': 0xA2,
            'Key.ctrl_r': 0xA3,
            'Key.alt_l': 0xA4,
            'Key.alt_r': 0xA5,
            # Add more keys as needed
        }
        return VK_CODE.get(str(key), None)        

    def for_hotkey(self, key):
        self.hotkey.press(key)

    def on_hotkey_pressed(self):
        print("on_hotkey_pressed-> Esc")
        self.stop_typing.set()  # Stop typing when the hotkey is pressed
        self.listener.stop()  # Stop the hotkey listener

    def on_press(self, key):
        target_vk = self.commands['wait_to_continue'].vk
        current_vk = self.getValOfKey(key)
        print(f"on_press-> target_vk = {target_vk} | current_vk = {current_vk}")
        if target_vk == current_vk:
            return False  # Stop the listener when the specified key is pressed

    def auto_type(self, text):
        lines = text.split('\n')
        for i, line in enumerate(lines):
            for segment in re.split(r'(\[[^\]]*\])', line):
                command, value = None, None
                if segment.startswith('[') and segment.endswith(']'):
                    segment_copy = segment[1:-1]
                    if '=' in segment_copy:
                        command, value = segment_copy.split('=')
                if command in self.commands:
                    print(f"auto_type-> command, value = {command}, {value}")
                    if command == 'wait_to_continue':
                        self.commands[command] = KeyCode.from_vk(int(value, 16))  # Convert the string to a KeyCode object
                    elif command == 'delay':
                        print(f"auto_type-> delay = {value}")
                        time.sleep(int(value) / 1000)
                    elif command == 'key':
                        if(value == 'left'):
                            self.keyboard.press(Key.left)
                            self.keyboard.release(Key.left)   
                        elif(value == 'right'):
                            self.keyboard.press(Key.right)
                            self.keyboard.release(Key.right)
                        elif(value == 'up'):
                            self.keyboard.press(Key.up)
                            self.keyboard.release(Key.up)
                        elif(value == 'down'):
                            self.keyboard.press(Key.down)
                            self.keyboard.release(Key.down)
                        elif(value == 'delete'):
                            self.keyboard.press(Key.delete)
                            self.keyboard.release(Key.delete)
                        elif(value == 'backspace'):
                            self.keyboard.press(Key.backspace)
                            self.keyboard.release(Key.backspace)
                    else:
                        self.commands[command] = int(value)
                else:
                    for char in segment:
                        print(f"auto_type-> char = {char}")
                        if self.stop_typing.is_set():
                            return
                        self.keyboard.type(char)
                        time.sleep(self.commands['speed_of_input'] / 1000)                    
                if self.commands['wait_to_continue'] is not None:
                    self.wait_listener = Listener(on_press=self.on_press)  # Keep a reference to the listener
                    self.wait_listener.start()
                    self.wait_listener.join()  # Wait for the key press
                    self.commands['wait_to_continue'] = None  # Reset the command
            time.sleep(self.commands['new_line_delay'] / 1000)
            if i < len(lines) - 2:  # If it's not the last line, press enter
                self.keyboard.press(Key.enter)
                self.keyboard.release(Key.enter)   
        print("auto_type-> end")



    def run(self):
        text = self.text_input.get("1.0", tk.END)
        self.stop_typing.clear()
        self.typing_thread = threading.Thread(target=self.auto_type, args=(text,))  # Keep a reference to the thread
        self.typing_thread.start()
        # Create a global hotkey for the 'Escape' key
        self.hotkey = keyboard.HotKey(
            keyboard.HotKey.parse('<esc>'),
            self.on_hotkey_pressed
        )
        # Restart the listener for the hotkey
        self.listener = keyboard.Listener(
            on_press=self.for_hotkey,
            on_release=None
        )
        self.listener.start()
    
    def start(self):
        self.root.mainloop()

    def on_closing(self):
        # Set the stop_typing event to stop the typing thread
        self.stop_typing.set()

        # Stop the hotkey listener if it exists
        if hasattr(self, 'listener') and self.listener is not None:
            self.listener.stop()

        # Stop the wait_to_continue listener if it exists
        if hasattr(self, 'wait_listener') and self.wait_listener is not None:
            self.wait_listener.stop()

        # If the typing thread is alive, join it
        if hasattr(self, 'typing_thread') and self.typing_thread.is_alive():
            self.typing_thread.join()

        # Destroy the window
        self.root.destroy()

if __name__ == "__main__":
    auto_typer = AutoTyper()
    auto_typer.start()