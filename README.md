# systemSleep

## Introduction
- The earlier batch based version has been retired and a gui has been added.
- There are two components, the base script 1) systemSleep.py and 2) sleep_guy.pyw
- Base script uses typing and the GUI uses tkinter, so ensure the requirements are installed before using.

## Installation
> python -m pip install -r requirements.txt

Script uses hiberante, therefore ensure that hibernate is enabled in your PC from powershell:
> powercfg -h on

## How to Use
1) The CLI script "systemSleep.py" can be either invoked through python systemSleep.py, and you can type an initial wait time before sleep. Or you can rename extension as .pyw and invoke by double-click and the system will be put to sleep immediately.

3) **The GUI**: The gui.py can be invoked using cmd>py gui.py and it will invoke the gui with static 5second timer and then sleep.

## Prerequisite
- Tested in Windows 10 OS and Windows 11.
- The program uses python to run; >3.10 is preferred.
- It is preferred to run the sscript as an user with admin rights.
- The feature to hibernate must be enabled in they system. A Powershell script to enable powershell is below:
> powercfg -h on


## Compaitiblity
| Windows Version        | Compatibility | Notes                                                             |
| ---------------------- | ------------- | ----------------------------------------------------------------- |
| **Windows 10**         | ✅ Supported   | Fully tested with `Rundll32.exe` sleep call                       |
| **Windows 11**         | ✅ Supported   | Same API works                                                    |
| **Windows 8 / 8.1**    | ✅ Likely      | Should work, but have not tested.		                          |
| **Windows 7**          | ⚠️ Mixed      | Might work, but UAC and power policy issues can block sleep       |