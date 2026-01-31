import threading
import time
import tkinter as tk

import pyautogui
import keyboard


def run():
    clicking = False
    click_thread = None

    # ---------------- CLICK LOOP ----------------
    def click_loop():
        nonlocal clicking
        while clicking:
            cps = cps_var.get()
            ratio = hold_var.get()

            if cps <= 0:
                time.sleep(0.05)
                continue

            interval = 1.0 / cps
            hold_time = interval * ratio
            release_time = interval * (1.0 - ratio)

            x, y = pyautogui.position()
            pyautogui.mouseDown(x=x, y=y)
            time.sleep(hold_time)
            pyautogui.mouseUp()
            time.sleep(release_time)

    # ---------------- TOGGLE ----------------
    def toggle_clicking():
        nonlocal clicking, click_thread
        clicking = not clicking

        status_label.config(
            text="Status: ACTIVE" if clicking else "Status: INACTIVE",
            fg="green" if clicking else "red"
        )

        if clicking:
            click_thread = threading.Thread(
                target=click_loop,
                daemon=True
            )
            click_thread.start()

    # ---------------- APPLY KEYBIND ----------------
    def apply_keybind():
        keyboard.clear_all_hotkeys()
        key = keybind_var.get().lower()
        keyboard.add_hotkey(key, toggle_clicking)

    # ---------------- EXIT ----------------
    def exit_program():
        nonlocal clicking
        clicking = False
        keyboard.clear_all_hotkeys()
        root.destroy()

    # ---------------- GUI ----------------
    root = tk.Tk()
    root.title("Python AutoClicker (Windows)")
    root.geometry("320x300")
    root.resizable(False, False)

    tk.Label(root, text="Global Toggle Key").pack(pady=4)
    keybind_var = tk.StringVar(value="f6")
    tk.Entry(root, textvariable=keybind_var).pack()

    tk.Button(root, text="Apply Keybind", command=apply_keybind).pack(pady=6)

    tk.Label(root, text="Clicks per Second").pack(pady=4)
    cps_var = tk.DoubleVar(value=10)
    tk.Scale(
        root,
        from_=1,
        to=50,
        orient="horizontal",
        variable=cps_var
    ).pack()

    tk.Label(root, text="Hold Ratio (Pressed vs Released)").pack(pady=4)
    hold_var = tk.DoubleVar(value=0.5)
    tk.Scale(
        root,
        from_=0.1,
        to=0.9,
        resolution=0.05,
        orient="horizontal",
        variable=hold_var
    ).pack()

    status_label = tk.Label(
        root,
        text="Status: INACTIVE",
        fg="red"
    )
    status_label.pack(pady=8)

    tk.Button(root, text="Exit", command=exit_program).pack(pady=10)

    # Default hotkey
    keyboard.add_hotkey(keybind_var.get().lower(), toggle_clicking)

    root.mainloop()

def main():
    run()