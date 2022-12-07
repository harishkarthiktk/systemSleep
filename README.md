# systemSleep
Just a simple script that puts Windows 10 system to sleep. If the script is run, it loops itself and sleeps again, if the system wakes up. Often, someone hits the keyboard, or cat walks over, and wakes up the machine. The script is a workaround for it.


## Operation
- Loop
  - The loop runs every predefined time limit (5 minutes) to put the system to sleep if it is awake. The script works right now only on Windows OS and has been tested on Windows 10.
- Operation
  - A log file will be left behind with dates capturing the script operations. This is purely functional and can be improved with logging capabilities.

## Prerequisite
- Windows 10 OS
- The script must be executed from CMD as an Administrator
