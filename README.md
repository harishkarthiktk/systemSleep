# systemSleep

## Introduction
I use my desktop at high performance power mode (similar) always and hardly ever shut it down. I put it to hibernate and switch it on when I need to use it. The machine might be chugging along because it might be running a game as well, drawing full energy to GPU and CPU. However, the cat might walk over the keyboard of someone in my house might touch it, and it will wake the machine up automatically. If I am away from work or travelling, this leaves the machine running on full throttle until I am back. This is waste of electricity. And there is no power mgmt tool that auto-hibernates the machine in case of accidental wake up.

This program puts the Windows machines to sleep. And if it is woken, it will wait for 5 minutes and then goes back to sleep unless intercepted.

1) **The Script**: When it is run, it asks if the is a wait before the sleep needs to be done or if it should happen immediately. Then the system will be put to sleep. And if the system wakes up in the mean time, it waits for 5 minutes and puts the machine back to sleep. To exit the sleep, use ctrl+c to break.

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
