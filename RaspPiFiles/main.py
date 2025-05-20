import threading
import subprocess
import time

def run_file(filename):
  subprocess.run(['python', filename])

thread1 = threading.Thread(target=run_file, args=("API.py",))
thread2 = threading.Thread(target=run_file, args=("Video.py",))

thread1.start() 
time.sleep(3)
thread2.start() 

thread1.join()
thread2.join() 

