import os
import time
import platform

def sleepy():
	if 'windows' == str(platform.system()).lower():
		with open('sleep.log', 'a', encoding='UTF8') as afile:
			tm_year, tm_mon, tm_mday, tm_hour, tm_min, tm_sec, tm_wday, tm_yday, tm_isdst = time.localtime()
			current_datetime = f'[{tm_mday}-{tm_mon}-{tm_year}][{tm_hour}:{tm_min}:{tm_sec}]'

			afile.write(f'{current_datetime}: putting system to sleep...\n')

			try:
				os.system("Rundll32.exe Powrprof.dll,SetSuspendState Sleep")
				status= True
			except Exception as ex:
				afile.write(f'{current_datetime}: putting system to sleep failed with error: {str(ex)}')
				status= False
			finally:
				if status:
					print('sleep success')
				else:
					print('sleep failure')
	else:
		print('the script works only in MS Windows operating systems, and is tested in Windows 10')


def main():
	while True:
		sleepy()
		time.sleep(1*60*5) # 1sec * 60* 5 minutes

if __name__ == '__main__':
	main()
