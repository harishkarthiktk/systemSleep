# systemSleep
Just a simple script that puts Windows 10 system to sleep. When the script is run, if the system wakes up, it simplely loops itself and sleeps again. Often, someone hits the keyboard, or cat walks over, and wakes up the machine. The script is a way to address that problem and put the machine to sleep again.

## Operation
- Loop
  - The loop runs every predefined time limit (5 minutes) to put the system to sleep if it is awake. The script works right now only on Windows OS and has been tested on Windows 10.
- Operation
  - A log file will be left behind with dates capturing the script operations. This is purely functional and can be improved with logging capabilities.

## Prerequisite
- Windows 10 OS
- The script must be executed from CMD as an Administrator
