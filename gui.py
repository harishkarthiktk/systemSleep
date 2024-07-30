import tkinter as tk

import systemSleep

class Window(tk.Tk):
    def __init__(self):
        super().__init__()
        # following 1500x900 standard, downscalled and reduced vertically for aesthetics reasons
        width = 500
        height = 200
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = (screen_width - width) // 2
        y = (screen_height - height) // 2

        self.geometry(f'{width}x{height}+{x}+{y}')

        self.title("system Sleep.py")
        self.label_text = tk.StringVar()
        self.label_text.set("Sleep Immediately, \nor choose the initial wait (seconds)")

        self.label = tk.Label(self, textvar=self.label_text)
        self.label.pack(fill=tk.BOTH, expand=1, padx=100, pady=30)

        immediate_button = tk.Button(self, text="Sleep Immediately", command=self.immediate_sleep)
        immediate_button.pack(side=tk.LEFT, padx=(20, 0), pady=(0, 20))

        wait_button = tk.Button(self, text="Cancel", command=self.wait_n_sleep)
        wait_button.pack(side=tk.RIGHT, padx=(0, 20), pady=(0, 20))


    def sleep_now(self):
        systemSleep.main()

    def immediate_sleep(self):
        self.label_text.set("Sleeping in 5 seconds..")
        self.after(5000, self.sleep_now)


    def wait_n_sleep(self):
        self.label_text.set("Goodbye! \n (Closing in 3 seconds)")
        self.after(3000, self.destroy)


if __name__ == "__main__":
    window = Window()
    window.mainloop()
