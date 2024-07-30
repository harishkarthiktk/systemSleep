import tkinter as tk
from time import sleep

import systemSleep

class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("system Sleep.py")
        self.label_text = tk.StringVar()
        self.label_text.set("Sleep Immediately, or choose the initial wait (seconds)")

        self.label = tk.Label(self, textvar=self.label_text)
        self.label.pack(fill=tk.BOTH, expand=1, padx=100, pady=30)

        immediate_button = tk.Button(self, text="Sleep Immediately", command=self.immediate_sleep)
        immediate_button.pack(side=tk.LEFT, padx=(20, 0), pady=(0, 20))

        wait_button = tk.Button(self, text="Cancel", command=self.wait_n_sleep)
        wait_button.pack(side=tk.RIGHT, padx=(0, 20), pady=(0, 20))

    def immediate_sleep(self): 
            self.label_text.set(f"Sleeping in 5 seconds..") 
            systemSleep.main()


    def wait_n_sleep(self):
        self.label_text.set("Goodbye! \n (Closing in 2 seconds)")
        self.after(2000, self.destroy)


if __name__ == "__main__":
    window = Window()
    window.mainloop()
        