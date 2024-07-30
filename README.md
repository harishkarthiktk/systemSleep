# systemSleep

## Introduction
This is a simple script that puts Windows machines to sleep. There are two components, (1) the python script and (2) a Windows batch.

1) **The Script**: When it is run, it asks if the is a wait before the sleep needs to be done or if it should happen immeidately. Then the system will be put to sleep. And if the system wakes up in the mean time, it waits for 5 minutes and puts the machine back to sleep. To exit the sleep, use ctrl+c to break.

2) **The Batch**: When the batch can be setup as a shortcut or program to invoke the python script. This is a first iteration, and this will be made into a Windows executable later.

3) **The GUI**: The gui.py can be invoked using cmd>py gui.py and it will invoke the gui with static 5second timer and then sleep.

## Prerequisite
- Tested in Windows 10 OS and Windows 11.
- The program uses python to run; >3.10 is preferred.
- It is preferred to run the sscript as an user with admin rights.
- The feature to hibernate must be enabled in they system. A Powershell script to enable powershell is below:
> powercfg -h on

## Future Works:
- Script will include a GUI for operations with configurable wait times.


## Reference Repository:
- https://github.com/PacktPublishing/Tkinter-GUI-Programming-by-Example/blob/master/