"""
RASPBERRY PI SERVER ENTRY POINT - main.py

This file serves as the entry point for the Raspberry Pi robot server system. It orchestrates
the simultaneous execution of the Flask API server and video capture system using threading.

IMPORTED MODULES AND THEIR FUNCTIONS:
1. threading - Enables concurrent execution of multiple processes
   - Thread creation and management for parallel operations
   - Daemon thread handling for proper cleanup

2. subprocess - Handles execution of Python scripts as separate processes
   - Process spawning and management
   - Inter-process communication and error handling

3. time - Provides timing control for startup sequencing
   - Delay mechanisms to ensure proper initialization order

EXECUTED SCRIPTS AND THEIR ROLES:
1. API.py - Flask web server for robot control
   - REST API endpoints for movement commands (/moving)
   - Video stream handling (/vidstream)
   - Logging and obstacle detection endpoints
   - Motor control integration and command processing

2. Video.py - Camera capture and streaming system
   - Real-time video capture from Pi camera
   - Frame encoding and transmission to API
   - Frame rate control and error handling
   - Base64 encoding for network transmission

THREADING ARCHITECTURE:
1. Thread 1 (API Server): Starts first to establish network endpoints
2. 3-second delay: Ensures API server is fully initialized
3. Thread 2 (Video Capture): Starts after API is ready to receive frames
4. Both threads run concurrently until completion

STARTUP SEQUENCE:
1. Create separate threads for API server and video capture
2. Start API server thread to establish network interface
3. Wait 3 seconds for API initialization
4. Start video capture thread to begin frame transmission
5. Wait for both threads to complete execution
"""

import threading
import subprocess
import time

# Execute Python script as separate subprocess
def run_file(filename):
  subprocess.run(['python', filename])

# Create thread for API server execution
thread1 = threading.Thread(target=run_file, args=("API.py",))
# Create thread for video capture system execution
thread2 = threading.Thread(target=run_file, args=("Video.py",))

# Start API server thread first to establish network endpoints
thread1.start() 
# Wait for API server initialization before starting video capture
time.sleep(3)
# Start video capture thread to begin frame transmission
thread2.start() 

# Wait for both threads to complete execution
thread1.join()
thread2.join()
