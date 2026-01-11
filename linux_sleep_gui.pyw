#!/usr/bin/env python3
"""
Linux Sleep Scheduler GUI - Tkinter-based interface for systemd sleep management
Supports both sleep scheduling and sleep prevention
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import subprocess
import time
import sys
import signal

import config_loader
import linux_sleep_helpers
import log_manager


# Global state
current_mode = "sleep"
current_sleep_type = "suspend"
stop_operation = False
prevent_process = None
enable_cycling = True
wait_minutes_setting = 5
force_ignore_inhibitors = False
logger = None

# Timeout for sleep commands
TIMEOUT = 15


class ToolTip:
    """Simple tooltip helper (from sleep_gui_new.pyw pattern)"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.widget.bind("<Enter>", self.on_enter)
        self.widget.bind("<Leave>", self.on_leave)
        self.tipwindow = None

    def on_enter(self, event=None):
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 10
        y = self.widget.winfo_rooty() + 30
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        label = tk.Label(tw, text=self.text, background="lightyellow",
                        relief="solid", borderwidth=1, font=("Segoe UI", 9))
        label.pack(ipadx=5)

    def on_leave(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


def create_mode_selector(parent):
    """Create mode selection radio buttons"""
    mode_frame = ttk.LabelFrame(parent, text="Operation Mode", padding=10)
    mode_frame.pack(fill='x', pady=(0, 15))

    mode_var = tk.StringVar(value="sleep")

    sleep_radio = ttk.Radiobutton(mode_frame, text="Sleep System",
                                  variable=mode_var, value="sleep",
                                  command=lambda: on_mode_change("sleep"))
    sleep_radio.pack(side='left', padx=(0, 20))

    prevent_radio = ttk.Radiobutton(mode_frame, text="Prevent Sleep",
                                    variable=mode_var, value="prevent",
                                    command=lambda: on_mode_change("prevent"))
    prevent_radio.pack(side='left')

    ToolTip(sleep_radio, "Schedule system sleep with countdown timer")
    ToolTip(prevent_radio, "Keep system awake indefinitely")

    return mode_var


def on_mode_change(new_mode):
    """Handle mode change - show/hide appropriate controls"""
    global current_mode, prevent_process

    # Stop any active prevent mode when switching modes (fixes inhibitor lock)
    if prevent_process and prevent_process.poll() is None:
        logger.info("Stopping active sleep prevention before mode switch")
        try:
            prevent_process.terminate()
            prevent_process.wait(timeout=2)
        except Exception as e:
            logger.warning(f"Error stopping prevent process: {e}")
        prevent_process = None

    current_mode = new_mode

    if new_mode == "sleep":
        sleep_type_frame.pack(fill='x', pady=(0, 10))
        delay_frame.pack(fill='x', pady=(0, 15))
        reason_frame.pack_forget()
    else:  # prevent
        sleep_type_frame.pack_forget()
        delay_frame.pack_forget()
        reason_frame.pack(fill='x', pady=(0, 15))


def update_button_states():
    """Update button states and text based on current operation"""
    global current_mode, prevent_process

    # Check if prevent sleep is currently active
    prevent_active = current_mode == "prevent" and prevent_process and prevent_process.poll() is None

    if prevent_active:
        # During prevent sleep operation
        start_btn.config(state='disabled')
        cancel_btn.config(state='normal', text="Stop Prevention")
        settings_btn.config(state='disabled')
        exit_btn.config(state='disabled')
    else:
        # Normal state
        start_btn.config(state='normal', text="Start")
        cancel_btn.config(state='normal', text="Cancel")
        settings_btn.config(state='normal')
        exit_btn.config(state='normal')


def disable_controls():
    """Disable all control buttons except cancel"""
    start_btn.config(state='disabled')
    # Keep cancel_btn enabled so user can cancel operations
    settings_btn.config(state='disabled')
    exit_btn.config(state='disabled')
    cancel_btn.config(state='normal')  # Always enable cancel during operations


def enable_controls():
    """Re-enable all control buttons and update button states"""
    update_button_states()


def start_operation():
    """Start either sleep or prevent mode based on current_mode"""
    global stop_operation, prevent_process

    if current_mode == "sleep":
        # Validate inputs
        try:
            minutes = int(entry_delay.get())
            if minutes < 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Invalid Input",
                               "Please enter a non-negative integer.")
            return

        # Check permissions
        has_perm, error = linux_sleep_helpers.check_sleep_permissions(current_sleep_type)
        if not has_perm:
            messagebox.showerror("Permission Error", error)
            return

        # Confirm
        cycle_text = " (with cycling enabled)" if enable_cycling else ""
        confirm = messagebox.askyesno("Confirm",
                                     f"Start {current_sleep_type} timer for {minutes} minutes{cycle_text}?")
        if not confirm:
            logger.info(f"Sleep timer cancelled by user (type: {current_sleep_type}, delay: {minutes}m)")
            return

        logger.info(f"Sleep timer started (type: {current_sleep_type}, delay: {minutes}m, cycling: {enable_cycling})")
        # Disable controls and start thread
        disable_controls()
        stop_operation = False
        current_thread = threading.Thread(
            target=sleep_mode_thread,
            args=(minutes, current_sleep_type),
            daemon=True
        )
        current_thread.start()

    else:  # prevent mode
        reason = entry_reason.get().strip()
        if not reason:
            reason = "User requested via GUI"

        confirm = messagebox.askyesno("Confirm",
                                     f"Prevent system sleep?\nReason: {reason}")
        if not confirm:
            logger.info("Sleep prevention cancelled by user")
            return

        logger.info(f"Sleep prevention started - Reason: {reason}")
        # Disable controls and start thread
        disable_controls()
        stop_operation = False
        prevent_process = None
        current_thread = threading.Thread(
            target=prevent_mode_thread,
            args=(reason,),
            daemon=True
        )
        current_thread.start()


def cancel_operation():
    """Cancel current operation"""
    global stop_operation, prevent_process

    # Special handling for prevent sleep operations
    if current_mode == "prevent" and prevent_process and prevent_process.poll() is None:
        confirm = messagebox.askyesno(
            "Stop Prevention",
            "Stop sleep prevention and remove inhibitor?\n\n"
            "This will allow the system to sleep again."
        )
        if not confirm:
            logger.info("Stop operation cancelled by user")
            return

    logger.info("Operation cancelled by user")
    stop_operation = True

    if prevent_process and prevent_process.poll() is None:
        try:
            logger.info(f"Terminating prevent sleep process (PID: {prevent_process.pid})")
            prevent_process.terminate()
            prevent_process.wait(timeout=2)
            logger.info("Prevent sleep process terminated successfully")
        except subprocess.TimeoutExpired:
            logger.warning("Prevent sleep process did not terminate, killing forcefully")
            try:
                prevent_process.kill()
                prevent_process.wait(timeout=1)
            except:
                pass
        except Exception as e:
            logger.error(f"Error stopping prevent process: {e}")

    status_label.config(text="Operation stopped", foreground="blue")
    enable_controls()


def sleep_mode_thread(initial_minutes, sleep_type):
    """Sleep mode loop with countdown"""
    global stop_operation, wait_minutes_setting, enable_cycling, current_sleep_type, force_ignore_inhibitors

    wait_minutes = initial_minutes
    cycle = 1

    while not stop_operation:
        # Countdown phase
        seconds = wait_minutes * 60
        total_seconds = seconds

        for remaining in range(seconds, 0, -1):
            if stop_operation:
                enable_controls()
                return

            mins, secs = divmod(remaining, 60)
            progress_percentage = ((total_seconds - remaining) / total_seconds) * 100
            progress_var.set(progress_percentage)

            status_text = f"Countdown: {mins:02d}:{secs:02d}"
            if cycle > 1:
                status_text = f"[Cycle {cycle}] {status_text}"
            status_label.config(text=status_text, foreground="black")
            root.update()  # Process GUI events to make cancel button responsive

            time.sleep(1)

        if stop_operation:
            enable_controls()
            return

        # Sleep phase
        status_label.config(text=f"[Cycle {cycle}] Putting system to {sleep_type}...",
                          foreground="orange")
        progress_bar.config(style="orange.Horizontal.TProgressbar")
        root.update()

        try:
            cmd = linux_sleep_helpers.get_sleep_command(sleep_type)
            # Add -i flag to ignore inhibitors if enabled
            if force_ignore_inhibitors and "-i" not in cmd:
                cmd.insert(1, "-i")
                logger.info(f"Using -i flag to ignore inhibitors for {sleep_type}")
            subprocess.run(cmd, check=True, timeout=TIMEOUT)
        except subprocess.TimeoutExpired:
            status_label.config(text="Sleep command timed out", foreground="red")
            messagebox.showerror("Timeout", f"Sleep command timed out after {TIMEOUT}s")
            break
        except subprocess.CalledProcessError as e:
            status_label.config(text=f"Sleep error: {e}", foreground="red")
            messagebox.showerror("Error", f"Sleep failed: {e}")
            break

        # Check if user cancelled during sleep
        if stop_operation:
            enable_controls()
            return

        # Check cycling
        if not enable_cycling:
            status_label.config(text="Sleep completed (cycling disabled)",
                              foreground="green")
            progress_bar.config(style="green.Horizontal.TProgressbar")
            break

        # Next cycle
        status_label.config(text=f"System woke up. Waiting {wait_minutes_setting} minutes...",
                          foreground="purple")
        progress_bar.config(style="purple.Horizontal.TProgressbar")
        wait_minutes = wait_minutes_setting
        cycle += 1

    enable_controls()


def prevent_mode_thread(reason):
    """Prevent mode thread - keeps inhibit alive until cancelled"""
    global stop_operation, prevent_process

    try:
        # Start systemd-inhibit
        inhibit_cmd = [
            "systemd-inhibit",
            "--what=sleep",
            "--who=linuxSleep GUI",
            f"--why={reason}",
            "sleep", "infinity"
        ]

        prevent_process = subprocess.Popen(inhibit_cmd)

        status_label.config(text=f"Sleep prevention active (PID: {prevent_process.pid})",
                          foreground="green")
        progress_var.set(100)
        progress_bar.config(style="green.Horizontal.TProgressbar")

        # Update button state to show "Stop Prevention"
        cancel_btn.config(text="Stop Prevention", state='normal')
        settings_btn.config(state='disabled')
        root.update()

        # Keep alive until cancelled
        while not stop_operation and prevent_process.poll() is None:
            root.update()  # Process GUI events to make cancel button responsive
            time.sleep(0.1)  # Shorter sleep for more responsive cancellation

        # Cleanup
        if prevent_process.poll() is None:
            prevent_process.terminate()
            try:
                prevent_process.wait(timeout=2)
            except:
                pass

        status_label.config(text="Sleep prevention stopped", foreground="blue")

    except FileNotFoundError:
        status_label.config(text="Error: systemd-inhibit not found", foreground="red")
        messagebox.showerror("Error", "systemd-inhibit command not found")
    except Exception as e:
        status_label.config(text=f"Error: {e}", foreground="red")
        messagebox.showerror("Error", f"Failed to prevent sleep: {e}")

    finally:
        enable_controls()


def list_active_inhibitors():
    """List active systemd sleep inhibitors"""
    try:
        result = subprocess.run(
            ["systemd-inhibit", "--list"],
            capture_output=True,
            text=True,
            timeout=5
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error listing inhibitors: {result.stderr}"
    except FileNotFoundError:
        return "Error: systemd-inhibit command not found"
    except Exception as e:
        return f"Error: {e}"


def cleanup_gui_inhibitors():
    """Clean up leftover linuxSleep GUI inhibitors"""
    try:
        # Get list of inhibitors
        result = subprocess.run(
            ["systemd-inhibit", "--list"],
            capture_output=True,
            text=True,
            timeout=5
        )

        if result.returncode != 0:
            return False, f"Failed to list inhibitors: {result.stderr}"

        lines = result.stdout.strip().split('\n')
        cleaned_count = 0
        errors = []

        # Skip header line and process each inhibitor
        for line in lines[1:]:
            if not line.strip():
                continue

            # Check if this is a linuxSleep GUI inhibitor
            if "linuxSleep GUI" in line:
                # Extract PID (usually first column after USER)
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        # Try to find and kill the process
                        # The line format is: USER PID UID UID WHAT WHY WHO
                        pid = parts[1]
                        logger.info(f"Found linuxSleep GUI inhibitor (PID {pid}), attempting cleanup")
                        subprocess.run(
                            ["kill", "-9", pid],
                            timeout=2,
                            capture_output=True
                        )
                        cleaned_count += 1
                    except Exception as e:
                        errors.append(f"Error killing PID {pid}: {e}")

        if cleaned_count > 0:
            logger.info(f"Cleaned {cleaned_count} linuxSleep GUI inhibitor(s)")
            return True, f"Successfully cleaned {cleaned_count} inhibitor(s)"
        else:
            return True, "No linuxSleep GUI inhibitors found"

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return False, f"Cleanup error: {e}"


def open_settings():
    """Settings dialog"""
    global enable_cycling, wait_minutes_setting, current_sleep_type, force_ignore_inhibitors

    settings_window = tk.Toplevel(root)
    settings_window.title("Settings")
    settings_window.geometry("400x650")
    settings_window.transient(root)
    settings_window.grab_set()

    main_frame = ttk.Frame(settings_window, padding=20)
    main_frame.pack(fill='both', expand=True)

    # Cycling settings
    cycling_frame = ttk.LabelFrame(main_frame, text="Sleep Cycling Options", padding=10)
    cycling_frame.pack(fill='x', pady=(0, 15))

    cycling_var = tk.BooleanVar(value=enable_cycling)

    cycling_check = ttk.Checkbutton(cycling_frame,
                                   text="Enable continuous sleep cycling",
                                   variable=cycling_var)
    cycling_check.pack(anchor='w', pady=(0, 10))

    wait_frame = ttk.Frame(cycling_frame)
    wait_frame.pack(fill='x')

    ttk.Label(wait_frame, text="Wait time after wake-up (minutes):").pack(side='left')
    wait_spinbox = ttk.Spinbox(wait_frame, from_=1, to=60,
                              value=wait_minutes_setting, width=8)
    wait_spinbox.pack(side='right')

    # Sleep settings
    sleep_settings_frame = ttk.LabelFrame(main_frame, text="Sleep Settings", padding=10)
    sleep_settings_frame.pack(fill='x', pady=(0, 15))

    ttk.Label(sleep_settings_frame, text="Default sleep type:").pack(anchor='w')
    default_sleep_combo = ttk.Combobox(sleep_settings_frame,
                                       values=["suspend", "hibernate", "hybrid-sleep"],
                                       state='readonly', width=15)
    default_sleep_combo.set(current_sleep_type)
    default_sleep_combo.pack(anchor='w', pady=(5, 0))

    # Permission check button
    check_frame = ttk.Frame(sleep_settings_frame)
    check_frame.pack(fill='x', pady=(10, 0))

    def check_permissions():
        sleep_type = default_sleep_combo.get()
        has_perm, error = linux_sleep_helpers.check_sleep_permissions(sleep_type)
        if has_perm:
            messagebox.showinfo("Permissions",
                              f"✓ You have permission to use {sleep_type}")
        else:
            messagebox.showerror("Permissions", error)

    ttk.Button(check_frame, text="Check Permissions",
              command=check_permissions).pack(side='left')

    # Advanced sleep options
    advanced_frame = ttk.LabelFrame(main_frame, text="Advanced Sleep Options", padding=10)
    advanced_frame.pack(fill='x', pady=(0, 15))

    force_inhibitors_var = tk.BooleanVar(value=force_ignore_inhibitors)
    force_inhibitors_check = ttk.Checkbutton(advanced_frame,
                                            text="Force sleep ignoring other inhibitors",
                                            variable=force_inhibitors_var)
    force_inhibitors_check.pack(anchor='w')
    ttk.Label(advanced_frame, text="(e.g., from other running programs)",
             font=('TkDefaultFont', 8), foreground="gray").pack(anchor='w')

    # Inhibitor cleanup section
    cleanup_frame = ttk.LabelFrame(main_frame, text="Cleanup Inhibitors", padding=10)
    cleanup_frame.pack(fill='x', pady=(0, 15))

    ttk.Label(cleanup_frame, text="Clean up leftover sleep inhibitors:",
             font=('TkDefaultFont', 9)).pack(anchor='w', pady=(0, 10))

    cleanup_button_frame = ttk.Frame(cleanup_frame)
    cleanup_button_frame.pack(fill='x', pady=(0, 10))

    def show_inhibitors():
        """Show active inhibitors in a popup"""
        inhibitors = list_active_inhibitors()
        info_window = tk.Toplevel(settings_window)
        info_window.title("Active Inhibitors")
        info_window.geometry("500x300")
        info_window.transient(settings_window)

        text_widget = tk.Text(info_window, wrap='word', font=('Courier', 9))
        text_widget.pack(fill='both', expand=True, padx=10, pady=10)
        text_widget.insert('1.0', inhibitors)
        text_widget.config(state='disabled')

        ttk.Button(info_window, text="Close", command=info_window.destroy).pack(pady=5)

    def run_cleanup():
        """Run cleanup and show result"""
        success, message = cleanup_gui_inhibitors()
        if success:
            messagebox.showinfo("Cleanup Complete", message)
        else:
            messagebox.showerror("Cleanup Failed", message)

    ttk.Button(cleanup_button_frame, text="List Inhibitors",
              command=show_inhibitors).pack(side='left', padx=(0, 5))
    ttk.Button(cleanup_button_frame, text="Cleanup linuxSleep GUI",
              command=run_cleanup).pack(side='left')

    ttk.Label(cleanup_frame, text="Use this if the app crashed with an active inhibitor",
             font=('TkDefaultFont', 8), foreground="gray").pack(anchor='w')

    # About section
    about_frame = ttk.LabelFrame(main_frame, text="About", padding=10)
    about_frame.pack(fill='x', pady=(0, 15))

    about_text = (
        "Linux Sleep Scheduler v1.0\n"
        "Systemd-based sleep management\n"
        "\n"
        "Supports: suspend, hibernate, hybrid-sleep\n"
        "Prevents system sleep during important tasks\n"
        "\n"
        "Uses systemctl for sleep operations"
    )
    ttk.Label(about_frame, text=about_text, justify='center',
             font=('TkDefaultFont', 9)).pack()

    # Save/Cancel buttons
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill='x', pady=(20, 0))

    def save_settings():
        global enable_cycling, wait_minutes_setting, current_sleep_type, force_ignore_inhibitors
        enable_cycling = cycling_var.get()
        wait_minutes_setting = int(wait_spinbox.get())
        current_sleep_type = default_sleep_combo.get()
        force_ignore_inhibitors = force_inhibitors_var.get()
        logger.info(f"Settings saved: cycling={enable_cycling}, wake_delay={wait_minutes_setting}m, "
                   f"sleep_type={current_sleep_type}, force_inhibitors={force_ignore_inhibitors}")
        settings_window.destroy()

    ttk.Button(button_frame, text="Save", command=save_settings).pack(side='left', padx=(0, 10))
    ttk.Button(button_frame, text="Cancel", command=settings_window.destroy).pack(side='left')


def exit_app():
    """Exit application"""
    global stop_operation
    logger.info("Exiting application")
    stop_operation = True
    root.quit()


# Create main window
root = tk.Tk()
root.title("Linux Sleep Scheduler")
root.geometry("500x500")
root.resizable(False, False)

# Load config
config = config_loader.get_script_config("linux_sleep_gui")
enable_cycling = config.get("enable_cycling", True)
wait_minutes_setting = config.get("wake_delay_minutes", 5)
current_sleep_type = config.get("default_sleep_type", "suspend")
force_ignore_inhibitors = config.get("force_ignore_inhibitors", False)

# Initialize logger
logger = log_manager.init_logger("linux_sleep_gui")
logger.info("GUI application started")

# Setup styles
style = ttk.Style()
style.configure("orange.Horizontal.TProgressbar", background="orange")
style.configure("green.Horizontal.TProgressbar", background="green")
style.configure("purple.Horizontal.TProgressbar", background="purple")

# Main content frame
main_frame = ttk.Frame(root, padding=15)
main_frame.pack(fill='both', expand=True)

# Title
title_label = ttk.Label(main_frame, text="Linux Sleep Scheduler",
                       font=("Segoe UI", 14, "bold"))
title_label.pack(pady=(0, 20))

# Mode selector
mode_var = create_mode_selector(main_frame)

# Sleep type selector (initially visible for sleep mode)
sleep_type_frame = ttk.Frame(main_frame)
sleep_type_frame.pack(fill='x', pady=(0, 10))
ttk.Label(sleep_type_frame, text="Sleep Type:", font=('Segoe UI', 10)).pack(side='left', padx=(0, 10))
sleep_type_combo = ttk.Combobox(sleep_type_frame,
                                values=["suspend", "hibernate", "hybrid-sleep"],
                                state='readonly', width=15)
sleep_type_combo.set(current_sleep_type)
sleep_type_combo.pack(side='left')
sleep_type_combo.bind("<<ComboboxSelected>>",
                     lambda e: globals().__setitem__('current_sleep_type', sleep_type_combo.get()))

ToolTip(sleep_type_combo,
        "Suspend: Sleep to RAM (fast wake)\n"
        "Hibernate: Sleep to disk (slower, survives power loss)\n"
        "Hybrid: Both suspend and hibernate")

# Delay input (visible in sleep mode)
delay_frame = ttk.LabelFrame(main_frame, text="Sleep Delay", padding=10)
delay_frame.pack(fill='x', pady=(0, 15))
ttk.Label(delay_frame, text="Enter delay before sleep (minutes):").pack(anchor='w', pady=(0, 5))
entry_delay = ttk.Spinbox(delay_frame, from_=0, to=1440, width=10)
entry_delay.set(config.get("default_delay_minutes", 0))
entry_delay.pack(anchor='w')

# Reason input (visible in prevent mode)
reason_frame = ttk.LabelFrame(main_frame, text="Prevention Reason", padding=10)
ttk.Label(reason_frame, text="Reason for preventing sleep:").pack(anchor='w', pady=(0, 5))
entry_reason = ttk.Entry(reason_frame, width=40)
entry_reason.insert(0, config.get("prevent_sleep_reason", "User requested via GUI"))
entry_reason.pack(anchor='w', fill='x')

# Initially hide reason frame (sleep mode is default)
reason_frame.pack_forget()

# Progress bar
progress_var = tk.DoubleVar(value=0)
progress_bar = ttk.Progressbar(main_frame, variable=progress_var, maximum=100,
                               mode='determinate')
progress_bar.pack(fill='x', pady=(0, 15))

# Status label
status_label = ttk.Label(main_frame, text="Ready to start", foreground="blue",
                        font=('Segoe UI', 10))
status_label.pack(fill='x', pady=(0, 15))

# Button frame
button_frame = ttk.Frame(main_frame)
button_frame.pack(fill='x', pady=(0, 10))

start_btn = ttk.Button(button_frame, text="Start", command=start_operation)
start_btn.pack(side='left', padx=(0, 5))

cancel_btn = ttk.Button(button_frame, text="Cancel", command=cancel_operation)
cancel_btn.pack(side='left', padx=(0, 5))
ToolTip(cancel_btn, "Cancel current operation\n"
                    "For prevent sleep: Stop inhibitor and allow system to sleep")

settings_btn = ttk.Button(button_frame, text="Settings", command=open_settings)
settings_btn.pack(side='left', padx=(0, 5))

exit_btn = ttk.Button(button_frame, text="Exit", command=exit_app)
exit_btn.pack(side='left')

# Status bar
status_bar = ttk.Separator(main_frame, orient='horizontal')
status_bar.pack(fill='x', pady=(10, 0))

footer = ttk.Label(main_frame, text="Use settings for cycling options",
                  font=('Segoe UI', 8), foreground="gray")
footer.pack(anchor='e', pady=(5, 0))

# Run GUI
if __name__ == "__main__":
    root.mainloop()
