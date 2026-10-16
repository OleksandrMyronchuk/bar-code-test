# -*- coding: windows-1252 -*-
import re
import threading
import tkinter as tk
from tkinter import Text
from pynput.keyboard import Controller, Key, Listener, KeyCode


class AutoTyper:
    KEY_MAP = {
        'left': Key.left,
        'right': Key.right,
        'up': Key.up,
        'down': Key.down,
        'delete': Key.delete,
        'backspace': Key.backspace,
    }

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

        self.stop_typing = threading.Event()
        self.listener = None        # global Esc listener
        self.wait_listener = None   # listener used by wait_to_continue
        self.typing_thread = None

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

    # ------------------------------------------------------------------
    # Esc handling
    # ------------------------------------------------------------------
    def stop_all(self):
        """Stop typing immediately: set the flag and release anything blocking."""
        self.stop_typing.set()
        wait_listener = self.wait_listener
        if wait_listener is not None:
            wait_listener.stop()  # unblocks wait_listener.join() in the typing thread

    def on_esc_listener_press(self, key):
        if key == Key.esc:
            print("on_esc_listener_press-> Esc")
            self.stop_all()
            return False  # stop the Esc listener

    def on_press(self, key):
        """Listener callback for wait_to_continue."""
        if key == Key.esc:
            self.stop_all()
            return False

        target = self.commands['wait_to_continue']
        if target is None:
            return False
        target_vk = target.vk
        current_vk = self.getValOfKey(key)
        print(f"on_press-> target_vk = {target_vk} | current_vk = {current_vk}")
        if target_vk == current_vk:
            return False  # Stop the listener when the specified key is pressed

    # ------------------------------------------------------------------
    # Helpers that respect the stop flag
    # ------------------------------------------------------------------
    def _sleep(self, seconds):
        """Interruptible sleep. Returns True if Esc was pressed meanwhile."""
        return self.stop_typing.wait(seconds)

    def _tap(self, key):
        """Press and release a key, unless typing was stopped."""
        if self.stop_typing.is_set():
            return
        self.keyboard.press(key)
        self.keyboard.release(key)

    # ------------------------------------------------------------------
    # Main typing logic
    # ------------------------------------------------------------------
    def auto_type(self, text):
        lines = text.split('\n')
        for i, line in enumerate(lines):
            for segment in re.split(r'(\[[^\]]*\])', line):
                if self.stop_typing.is_set():
                    return

                command, value = None, None
                if segment.startswith('[') and segment.endswith(']'):
                    segment_copy = segment[1:-1]
                    if '=' in segment_copy:
                        command, value = segment_copy.split('=', 1)

                if command in self.commands:
                    print(f"auto_type-> command, value = {command}, {value}")
                    try:
                        if command == 'wait_to_continue':
                            self.commands[command] = KeyCode.from_vk(int(value, 16))
                        elif command == 'delay':
                            print(f"auto_type-> delay = {value}")
                            if self._sleep(int(value) / 1000):
                                return
                        elif command == 'key':
                            key = self.KEY_MAP.get(value.strip())
                            if key is None:
                                print(f"auto_type-> unknown key: {value}")
                            else:
                                self._tap(key)
                        else:
                            self.commands[command] = int(value)
                    except ValueError:
                        print(f"auto_type-> invalid value for [{command}={value}]")
                else:
                    for char in segment:
                        if self.stop_typing.is_set():
                            return
                        print(f"auto_type-> char = {char}")
                        self.keyboard.type(char)
                        if self._sleep(self.commands['speed_of_input'] / 1000):
                            return

                if self.commands['wait_to_continue'] is not None:
                    if self.stop_typing.is_set():
                        return
                    self.wait_listener = Listener(on_press=self.on_press)
                    self.wait_listener.start()
                    # Esc may have been pressed just before the listener existed
                    if self.stop_typing.is_set():
                        self.wait_listener.stop()
                    self.wait_listener.join()  # Wait for the key press (or Esc)
                    self.wait_listener = None
                    self.commands['wait_to_continue'] = None  # Reset the command
                    if self.stop_typing.is_set():
                        return

            if self._sleep(self.commands['new_line_delay'] / 1000):
                return
            if i < len(lines) - 2:  # If it's not the last line, press enter
                self._tap(Key.enter)
        print("auto_type-> end")

    def _worker(self, text):
        try:
            self.auto_type(text)
        finally:
            # Typing finished or was stopped: clean up the Esc listener
            listener = self.listener
            if listener is not None:
                listener.stop()

    def run(self):
        # Ignore clicks on Run while typing is already in progress
        if self.typing_thread is not None and self.typing_thread.is_alive():
            return

        text = self.text_input.get("1.0", tk.END)
        self.stop_typing.clear()
        self.commands['wait_to_continue'] = None

        # Start the global Esc listener BEFORE typing begins
        self.listener = Listener(on_press=self.on_esc_listener_press)
        self.listener.start()

        self.typing_thread = threading.Thread(target=self._worker, args=(text,), daemon=True)
        self.typing_thread.start()

    def start(self):
        self.root.mainloop()

    def on_closing(self):
        # Stop typing and release any blocking listener
        self.stop_all()

        # Stop the Esc listener if it exists
        if self.listener is not None:
            self.listener.stop()

        # Wait briefly for the typing thread to finish
        if self.typing_thread is not None and self.typing_thread.is_alive():
            self.typing_thread.join(timeout=1)

        # Destroy the window
        self.root.destroy()


if __name__ == "__main__":
    auto_typer = AutoTyper()
    auto_typer.start()
