import tkinter as tk
from tkinter import messagebox, ttk
import time
import threading
import subprocess

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
                         font=("Segoe UI", "9", "normal"))
        label.pack(ipadx=5, ipady=2)
    
    def hide_tip(self, _event=None):
        if self.tip_window:
            self.tip_window.destroy()
            self.tip_window = None

# Global variables for control
stop_timer = False
current_thread = None
initial_minutes = 0
enable_cycling = True
wait_minutes_setting = 5

def start_sleep_timer():
    global stop_timer, current_thread, initial_minutes
    
    try:
        minutes = int(entry.get())
        if minutes < 0:
            raise ValueError
        initial_minutes = minutes
    except ValueError:
        messagebox.showerror("Invalid Input", "Please enter a non-negative integer.")
        return
    
    # Confirm action
    if minutes == 0:
        confirm = messagebox.askyesno("Confirm", "Put system to sleep immediately?")
    else:
        cycle_text = " (with cycling enabled)" if enable_cycling else ""
        confirm = messagebox.askyesno("Confirm", f"Start sleep timer for {minutes} minutes{cycle_text}?")
    
    if not confirm:
        return
    
    stop_timer = False
    start_button.config(state='disabled')
    cancel_button.config(state='normal')
    entry.config(state='disabled')
    
    # Reset and start progress bar
    progress_var.set(0)
    progress_bar.config(style="green.Horizontal.TProgressbar")
    
    status_label.config(text=f"Countdown: {minutes:02d}:00", foreground="blue")
    current_thread = threading.Thread(target=sleep_loop, args=(minutes,), daemon=True)
    current_thread.start()

def cancel_timer():
    global stop_timer
    stop_timer = True
    start_button.config(state='normal')
    cancel_button.config(state='disabled')
    entry.config(state='normal')
    status_label.config(text="Timer cancelled", foreground="red")
    progress_var.set(0)

def sleep_loop(initial_minutes_param):
    global stop_timer, wait_minutes_setting, enable_cycling
    
    wait_minutes = initial_minutes_param
    cycle = 1
    
    while not stop_timer:
        seconds = wait_minutes * 60
        total_seconds = seconds
        
        for remaining in range(seconds, 0, -1):
            if stop_timer:
                return
                
            mins, secs = divmod(remaining, 60)
            
            # Update progress bar
            progress_percentage = ((total_seconds - remaining) / total_seconds) * 100
            progress_var.set(progress_percentage)
            
            if cycle == 1:
                status_label.config(text=f"Countdown: {mins:02d}:{secs:02d}")
            else:
                status_label.config(text=f"[Cycle {cycle}] Countdown: {mins:02d}:{secs:02d}")
            
            time.sleep(1)
        
        if stop_timer:
            return
            
        # Sleep phase
        status_label.config(text=f"[Cycle {cycle}] Putting system to sleep...", foreground="orange")
        progress_bar.config(style="orange.Horizontal.TProgressbar")
        
        try:
            subprocess.run(["Rundll32.exe", "Powrprof.dll,SetSuspendState", "Sleep"], check=True)
        except subprocess.CalledProcessError as e:
            status_label.config(text=f"Sleep error: {e}", foreground="red")
            messagebox.showerror("Error", f"Sleep failed: {e}")
            break
        
        # Check if cycling is disabled
        if not enable_cycling:
            status_label.config(text="Sleep completed (cycling disabled)", foreground="green")
            break
            
        # Log and reset for next cycle
        status_label.config(text=f"System woke up. Waiting {wait_minutes_setting} minutes...", foreground="purple")
        wait_minutes = wait_minutes_setting
        cycle += 1
    
    # Reset UI when done
    start_button.config(state='normal')
    cancel_button.config(state='disabled')
    entry.config(state='normal')
    progress_var.set(0)

def open_settings():
    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("350x250")
    settings_window.resizable(False, False)
    settings_window.transient(root)
    settings_window.grab_set()
    
    # Center the window
    settings_window.geometry("+%d+%d" % (root.winfo_rootx() + 50, root.winfo_rooty() + 50))
    
    main_frame = ttk.Frame(settings_window, padding=20)
    main_frame.pack(fill='both', expand=True)
    
    # Cycling settings
    cycling_frame = ttk.LabelFrame(main_frame, text="Sleep Cycling Options", padding=10)
    cycling_frame.pack(fill='x', pady=(0, 15))
    
    global enable_cycling, wait_minutes_setting
    cycling_var = tk.BooleanVar(value=enable_cycling)
    
    cycling_check = ttk.Checkbutton(cycling_frame, text="Enable continuous sleep cycling",
                                   variable=cycling_var)
    cycling_check.pack(anchor='w', pady=(0, 10))
    
    ToolTip(cycling_check, "When enabled, system will sleep again after waking up")
    
    # Wait time setting
    wait_frame = ttk.Frame(cycling_frame)
    wait_frame.pack(fill='x')
    
    ttk.Label(wait_frame, text="Wait time after wake-up (minutes):").pack(side='left')
    wait_spinbox = ttk.Spinbox(wait_frame, from_=1, to=60, value=wait_minutes_setting, 
                              width=8, justify='center')
    wait_spinbox.pack(side='right')
    
    # About section
    about_frame = ttk.LabelFrame(main_frame, text="About", padding=10)
    about_frame.pack(fill='x', pady=(0, 15))
    
    about_text = "Windows Sleep Scheduler v1.1\nSchedule system sleep with customizable options"
    ttk.Label(about_frame, text=about_text, justify='center').pack()
    
    # Buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill='x')
    
    def save_settings():
        global enable_cycling, wait_minutes_setting
        enable_cycling = cycling_var.get()
        wait_minutes_setting = int(wait_spinbox.get())
        messagebox.showinfo("Settings", "Settings saved successfully!")
        settings_window.destroy()
    
    def reset_settings():
        cycling_var.set(True)
        wait_spinbox.set(5)
    
    ttk.Button(button_frame, text="Save", command=save_settings).pack(side='right', padx=(5, 0))
    ttk.Button(button_frame, text="Reset", command=reset_settings).pack(side='right')
    ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side='right', padx=(0, 5))

def on_exit():
    global stop_timer
    if current_thread and current_thread.is_alive():
        confirm = messagebox.askyesno("Confirm Exit", "Timer is running. Are you sure you want to exit?")
        if confirm:
            stop_timer = True
            root.destroy()
    else:
        root.destroy()

# Create main window
root = tk.Tk()
root.title("Windows Sleep Scheduler v1.1")
root.resizable(False, False)

# Configure ttk styles
style = ttk.Style()
style.theme_use('clam')  # Modern theme
style.configure("green.Horizontal.TProgressbar", background="green")
style.configure("orange.Horizontal.TProgressbar", background="orange")

# Main container with better styling
main_frame = ttk.Frame(root, padding=25)
main_frame.pack(fill='both', expand=True)

# Title
title_label = ttk.Label(main_frame, text="Sleep Scheduler", font=('Segoe UI', 16, 'bold'))
title_label.pack(pady=(0, 20))

# Input section
input_frame = ttk.Frame(main_frame)
input_frame.pack(pady=(0, 15))

ttk.Label(input_frame, text="Enter delay before sleep (in minutes):", 
         font=('Segoe UI', 10)).pack(pady=(0, 8))

entry = ttk.Entry(input_frame, width=12, justify='center', font=('Segoe UI', 11))
entry.insert(0, "0")
entry.pack()
ToolTip(entry, "0 means immediate sleep\nPress Enter to start timer")

entry.bind("<Return>", lambda event: start_sleep_timer())

# Progress bar
progress_frame = ttk.Frame(main_frame)
progress_frame.pack(fill='x', pady=15)

ttk.Label(progress_frame, text="Progress:", font=('Segoe UI', 9)).pack(anchor='w')
progress_var = tk.DoubleVar()
progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100, length=300)
progress_bar.pack(fill='x', pady=(5, 0))

# Control buttons
button_frame = ttk.Frame(main_frame)
button_frame.pack(pady=15)

start_button = ttk.Button(button_frame, text="Start Timer", command=start_sleep_timer,
                         style="Accent.TButton")
start_button.pack(side='left', padx=(0, 8))

cancel_button = ttk.Button(button_frame, text="Cancel", command=cancel_timer, state='disabled')
cancel_button.pack(side='left', padx=(0, 8))

settings_button = ttk.Button(button_frame, text="Settings", command=open_settings)
settings_button.pack(side='left', padx=(0, 8))

exit_button = ttk.Button(button_frame, text="Exit", command=on_exit)
exit_button.pack(side='left')

# Status display
status_label = ttk.Label(main_frame, text="Ready to start timer", 
                        font=('Segoe UI', 10, 'bold'), foreground="green")
status_label.pack(pady=(10, 0))

# Footer
footer_label = ttk.Label(main_frame, text="Tip: Use settings to customize cycling behavior", 
                        font=('Segoe UI', 8), foreground="gray")
footer_label.pack(pady=(15, 0))

# Window setup
root.update_idletasks()
root.minsize(root.winfo_width(), root.winfo_height())

# Handle window closing
root.protocol("WM_DELETE_WINDOW", on_exit)

root.mainloop()
