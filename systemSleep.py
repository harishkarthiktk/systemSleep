import os, sys
import time
import platform
import json

# configurations are stored in config.json
# this is done simply to offload configurations externally and manage them there without touching the core script.

with open("config.json", "r") as rfile:
	config_data = json.loads(
							rfile.read()
						  )

# global variables
sleep_time_in_minutes = config_data["sleep_time_in_minutes"] 
default_method = config_data["default_method"]

def sleepy():
	if 'windows' == str(platform.system()).lower():
		with open('sleep.log', 'a', encoding='UTF8') as afile:
			tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst = time.localtime()
			current_datetime = f'[{tm_mday}-{tm_mon}-{tm_year}][{tm_hour}:{tm_min}:{tm_sec}]'

			afile.write(f'{current_datetime}: putting system to sleep...\n')
			try:
				os.system("Rundll32.exe Powrprof.dll,SetSuspendState Sleep")
				status = True
			except KeyboardInterrupt as ki:
				afile.write(f'{current_datetime}: keyboard interupt detected, hence closing: {str(ki)}')
			except Exception as ex:
				afile.write(f'{current_datetime}: putting system to sleep failed with error: {str(ex)}')
				status = False
			finally:
				if status:
					print(f'sleep success at {current_datetime}')
				else:
					print(f'sleep failure at {current_datetime}')
	else:
		print('the script works only in MS Windows operating systems, and is tested in Windows 10')
		sys.exit(0)


def main():
	while True:
		sleepy()
		time.sleep(1 * 60 * sleep_time_in_minutes) # 1 second * 60 * global_variable

if __name__ == '__main__':
	method = default_method
	
	# place holder for the gui hook

	if method == 'gui': 
		selection = input('selection from gui') ## have to add the method for using gui for selection
	elif method == "cli": 
		selection = input('should system sleep after sometime: (y/n)?')

	if str(selection).lower() == 'y':
		pre_sleep_time = int(input('enter the time in minutes: '))
		print(f'will sleep in {pre_sleep_time}minutes')
		time.sleep(pre_sleep_time * 60)


	main()
