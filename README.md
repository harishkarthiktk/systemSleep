# systemSleep

## Introduction
This is a simple script that puts Windows machines to sleep. There are two components, (1) the python script and (2) a Windows batch.

1) **The Script**: When it is run, it asks if the is a wait before the sleep needs to be done or if it should happen immeidately. Then the system will be put to sleep. And if the system wakes up in the mean time, it waits for 5 minutes and puts the machine back to sleep. To exit the sleep, use ctrl+c to break.

2) **The Batch**: When the batch can be setup as a shortcut or program to invoke the python script. This is a first iteration, and this will be made into a Windows executable later.

## Prerequisite
- Tested in Windows 10 OS; use in Win11 at your own risk.
- The script must be executed from CMD as an Administrator
- The feature to hibernate must be enabled in they system. PS script to enable powershell is below:
> powercfg -h on

## Future Works:
- Test for Win11
- Script will include a GUI for operations.
- Include the hiberation check test and enable hibernate from within the GUI.


## Reference Repository:
- https://github.com/PacktPublishing/Tkinter-GUI-Programming-by-Example/blob/master/