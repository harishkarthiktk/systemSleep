import tkinter as tk
from tkinter import messagebox
import time
import threading
import subprocess

import config_loader

# Load configuration
config = config_loader.get_script_config("sleep_gui")
TIMEOUT = config.get("sleep_command_timeout", 15)
WAKE_DELAY = config.get("wake_delay_minutes", 5)
DEFAULT_DELAY = config.get("default_delay_minutes", 0)


class ToolTip:
    """Tooltip for a widget."""
    def __init__(self, widget, text='widget info'):
        self.widget = widget
        self.text = text
        self.tip_window = None
        widget.bind("<Enter>", self.show_tip)
        widget.bind("<Leave>", self.hide_tip)

    def show_tip(self, _event=None):
        if self.tip_window or not self.text:
            return
        x, y, cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 30
        y = y + cy + self.widget.winfo_rooty() + 30
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, justify='left',
                         background="#ffffe0", relief='solid', borderwidth=1,
                         font=("tahoma", "9", "normal"))
        label.pack(ipadx=5, ipady=2)

    def hide_tip(self, _event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

def start_sleep_timer():
    try:
        minutes = int(entry.get())
        if minutes < 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a non-negative integer.")
        return

    start_button.config(state='disabled')
    entry.config(state='disabled')
    status_label.config(text=f"Countdown: {minutes:02d}:00")
    threading.Thread(target=sleep_loop, args=(minutes,), daemon=True).start()

# deprecated function, wil delete after testing.
def delayed_sleep(minutes):
    seconds = minutes * 60
    for remaining in range(seconds, 0, -1):
        mins, secs = divmod(remaining, 60)
        status_label.config(text=f"Countdown: {mins:02d}:{secs:02d}")
        time.sleep(1)
    status_label.config(text="Putting system to sleep...")
    try:
        subprocess.run(["Rundll32.exe", "Powrprof.dll,SetSuspendState", "Sleep"], check=True)
        status_label.config(text="System sleep command issued.")
    except subprocess.CalledProcessError as e:
        status_label.config(text=f"Failed to sleep: {e}")
        messagebox.showerror("Sleep Error", f"Failed to sleep system: {e}")
    finally:
        start_button.config(state='normal')
        entry.config(state='normal')


def sleep_loop(initial_minutes):
    wait_minutes = initial_minutes
    cycle = 1
    while True:
        seconds = wait_minutes * 60
        for remaining in range(seconds, 0, -1):
            mins, secs = divmod(remaining, 60)
            status_label.config(text=f"[Cycle {cycle}] Countdown: {mins:02d}:{secs:02d}")
            time.sleep(1)
        status_label.config(text=f"[Cycle {cycle}] Sleeping now...")
        try:
            subprocess.run(["Rundll32.exe", "Powrprof.dll,SetSuspendState", "Sleep"], check=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            status_label.config(text="Sleep command timed out")
            messagebox.showerror("Timeout Error", f"Sleep command timed out after {TIMEOUT} seconds. System may be unresponsive.")
            break
        except subprocess.CalledProcessError as e:
            status_label.config(text=f"Sleep error: {e}")
            messagebox.showerror("Error", f"Sleep failed: {e}")
            break

        # Log and reset
        status_label.config(text=f"System woke up. Waiting {WAKE_DELAY} minutes...")
        wait_minutes = WAKE_DELAY
        cycle += 1

    # Re-enable controls when loop exits (due to error or stop)
    start_button.config(state='normal')
    entry.config(state='normal')


def on_exit():
    root.destroy()

root = tk.Tk()
root.title("Windows Sleep Scheduler")
root.resizable(False, False)

# Widgets
frame = tk.Frame(root, padx=20, pady=20)
frame.pack()

label = tk.Label(frame, text="Enter delay before sleep (in minutes):")
label.pack(pady=(0, 8))

entry = tk.Entry(frame, width=10, justify='center')
entry.insert(0, str(DEFAULT_DELAY))
entry.pack()
ToolTip(entry, "0 means immediate sleep")

entry.bind("<Return>", lambda event: start_sleep_timer())

start_button = tk.Button(frame, text="Start Sleep Timer", command=start_sleep_timer)
start_button.pack(pady=10)

exit_button = tk.Button(frame, text="Exit", command=on_exit)
exit_button.pack()

status_label = tk.Label(frame, text="", fg="blue")
status_label.pack(pady=8)

root.update_idletasks()
root.minsize(root.winfo_width(), root.winfo_height())
root.mainloop()
