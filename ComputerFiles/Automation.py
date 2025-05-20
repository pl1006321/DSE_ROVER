import threading
from tkinter import *
import requests
import base64
import numpy as np
import cv2
from PIL import Image, ImageTk
import Processing
import time
from queue import Queue

url = 'http://192.168.240.25:5000/'

class Automation:
    def __init__(self, stream_elem=None, overlay_elem=None):
        # UI elements
        self.stream_elem = stream_elem
        self.overlay_elem = overlay_elem

        # Threading and state variables
        self.movement_queue = Queue()
        self.stop_event = threading.Event()
        self.pause_event = threading.Event()
        self.line_type_detected = None
        self.automation_active = False
        self.is_executing_sequence = False
        
        # Debug/logging
        self.last_command = None
        self.sequence_start_time = None

    def start_threads(self):
        """Start vision processing and movement execution threads"""
        # Clear any existing state
        self.stop_event.clear()
        self.pause_event.clear()
        self.automation_active = True
        
        # Start video processing thread
        video_thread = threading.Thread(target=self.update_vid_stream)
        video_thread.daemon = True
        video_thread.start()

        # Start movement execution thread
        movement_thread = threading.Thread(target=self.execute_movements)
        movement_thread.daemon = True
        movement_thread.start()
        
        # Initiate movement
        self.start_automation()
        
        return video_thread, movement_thread

    def update_vid_stream(self):
        """Process video stream and detect features"""
        while not self.stop_event.is_set():
            try:
                # Get frame from API
                response = requests.get(url + 'vidstream')
                b64_image = response.json().get('frame')
                if not b64_image:
                    print('Received empty frame from API')
                    time.sleep(0.1)
                    continue

                # Decode image
                decoded_img = base64.b64decode(b64_image)
                np_image = np.frombuffer(decoded_img, dtype=np.uint8)
                stream = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
                if stream is None:
                    print('Failed to decode image')
                    time.sleep(0.1)
                    continue

                # Process frame using Processing.apply_overlay
                # This is the key connection between Automation.py and Processing.py
                overlay, line_type = Processing.apply_overlay(stream, self.movement_queue)

                # Handle line type detection
                if line_type != self.line_type_detected:
                    self.line_type_detected = line_type
                    print(f'Line type detected: {line_type}')
                    
                    # If horizontal line detected and automation is active, queue sequence
                    if self.automation_active and line_type == 'horizontal' and not self.is_executing_sequence:
                        print('Horizontal line detected! Queueing sequence...')
                        self.movement_queue.put(('horizontal_line_detected', None))

                # Resize and convert images for display
                if overlay is not None:
                    stream = cv2.resize(stream, (400, 300))
                    overlay = cv2.resize(overlay, (400, 300))
                    stream = cv2.cvtColor(stream, cv2.COLOR_BGR2RGB)
                    overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)

                    # Update UI elements
                    stream_img = ImageTk.PhotoImage(Image.fromarray(stream))
                    overlay_img = ImageTk.PhotoImage(Image.fromarray(overlay))

                    if self.stream_elem and self.overlay_elem and self.stream_elem.winfo_exists() and self.overlay_elem.winfo_exists():
                        self.stream_elem.imgtk = stream_img
                        self.stream_elem.configure(image=stream_img)
                        self.overlay_elem.imgtk = overlay_img
                        self.overlay_elem.configure(image=overlay_img)
                    else:
                        break
                    
            except Exception as e:
                print(f'Error in video stream: {e}')
                time.sleep(0.1)

    def execute_movements(self):
        """Execute movement commands from the queue"""
        last_command_time = time.time()
        last_direction = None

        while not self.stop_event.is_set():
            try:
                # If we're paused, wait until unpaused
                if self.pause_event.is_set():
                    time.sleep(0.1)
                    continue

                try:
                    # Try to get a command from the queue with a timeout of 0.1 seconds
                    command, data = self.movement_queue.get(timeout=0.1)
                    last_command_time = time.time()  # Reset timer when we get a command

                    # Process the command
                    if command == 'horizontal_line_detected' and not self.is_executing_sequence:
                        self.is_executing_sequence = True
                        self.sequence_start_time = time.time()
                        self.horizontal_line_sequence()
                        self.is_executing_sequence = False
                        print(f"Sequence completed in {time.time() - self.sequence_start_time:.2f} seconds")
                    elif command == 'move':
                        direction, duration = data
                        self.post_direction(direction)
                        last_direction = direction
                        if duration > 0:
                            time.sleep(duration)
                            # Only stop if not executing a sequence
                            if not self.is_executing_sequence:
                                self.post_direction('stop')
                                last_direction = 'stop'

                    # Mark the command as done
                    self.movement_queue.task_done()

                except Exception as e:
                    # Queue is empty - only stop if we've been stopped for a while and we're not
                    # in a sequence and the last direction wasn't already stop
                    current_time = time.time()
                    if (current_time - last_command_time > 3.0 and
                            not self.is_executing_sequence and
                            last_direction != 'stop' and
                            self.automation_active):
                        self.post_direction('forward')  # Default to moving forward
                        last_direction = 'forward'
                        last_command_time = current_time
                    time.sleep(0.1)
                    continue

            except Exception as e:
                print(f'Error in movement automation: {e}')
                time.sleep(0.1)

    def start_automation(self):
        """Start automated movement"""
        print("Starting automation...")
        self.automation_active = True
        self.post_direction('forward')
        self.line_type_detected = None
        self.pause_event.clear()

    def pause_automation(self):
        """Pause automation without stopping threads"""
        print("Pausing automation...")
        self.pause_event.set()
        self.post_direction('stop')
        
    def resume_automation(self):
        """Resume automation after pausing"""
        print("Resuming automation...")
        self.pause_event.clear()
        if self.automation_active:
            self.post_direction('forward')

    def stop_automation(self):
        """Stop automation and clear queue"""
        print("Stopping automation...")
        self.automation_active = False
        self.clear_queue()
        self.post_direction('stop')

    def check_vertical_path(self):
        """Check if there's a valid vertical line in current view"""
        try:
            # Get frame from API
            response = requests.get(url + 'vidstream')
            b64_image = response.json().get('frame')
            if not b64_image:
                return False

            # Decode image
            decoded_img = base64.b64decode(b64_image)
            np_image = np.frombuffer(decoded_img, dtype=np.uint8)
            frame = cv2.imdecode(np_image, cv2.IMREAD_COLOR)
            
            if frame is None:
                return False

            # Process the frame to detect vertical lines
            # Prepare the frame similar to how Processing.apply_overlay does it
            blurred = Processing.apply_gaussian_blur(frame)
            bluescaled = Processing.bluescale(blurred)
            masked = Processing.hsv_mask(bluescaled)
            
            # Use Processing's vertical_detection function
            vertical_flag, _ = Processing.vertical_detection(masked)
            
            return vertical_flag
            
        except Exception as e:
            print(f'Error checking vertical path: {e}')
            return False

    def horizontal_line_sequence(self):
        """
        Execute the horizontal line sequence with path detection:
        1. Stop and move forward a bit
        2. Turn left and check for vertical path
        3. If no path on left, turn right and check
        4. If no path on right, center and continue
        """
        # Stop movement
        self.post_direction('stop')
        time.sleep(0.3)

        # Move forward
        self.post_direction('forward')
        time.sleep(2.5)

        # Stop before turning
        self.post_direction('stop')
        time.sleep(0.3)

        # First try turning left and check for path
        print("Turning left to check for vertical path")
        self.post_direction('left')
        time.sleep(1.4)  # Full left turn
        
        # Stop to check for vertical line
        self.post_direction('stop')
        time.sleep(0.5)
        
        # Check if there's a vertical path on the left
        left_path_valid = self.check_vertical_path()
        
        if left_path_valid:
            print("Valid vertical path found on the left")
            # Move forward on this path
            self.post_direction('forward')
            time.sleep(1.2)
        else:
            # No path on left, try turning right
            print("No vertical path on left, checking right")
            self.post_direction('right')
            time.sleep(2.8)  # Need to turn from full left to full right
            
            # Stop to check for vertical path
            self.post_direction('stop')
            time.sleep(0.5)
            
            # Check if there's a vertical path on the right
            right_path_valid = self.check_vertical_path()
            
            if right_path_valid:
                print("Valid vertical path found on the right")
                # Move forward on this path
                self.post_direction('forward')
                time.sleep(1.2)
            else:
                # No path found on either side, return to center
                print("No vertical paths found, returning to center")
                self.post_direction('left')
                time.sleep(1.4)  # Turn from right to center
                
                # Move forward from center
                self.post_direction('stop')
                time.sleep(0.3)
                self.post_direction('forward')
                time.sleep(1.2)
        
        # Final stop at the end of sequence
        self.post_direction('stop')
        time.sleep(0.5)
        
        # Resume normal forward movement if automation is still active
        if self.automation_active:
            self.post_direction('forward')

    def post_direction(self, direction):
        """Send movement command to the robot API"""
        try:
            # Only log if direction changed
            if self.last_command != direction:
                print(f"Sending command: {direction}")
                self.last_command = direction
                
            # Send command to robot
            endpoint = url + 'moving'
            data = {'direction': direction}
            req = requests.post(endpoint, json=data)

            # If stopping, clear the movement queue
            if direction == 'stop' and not self.is_executing_sequence:
                self.clear_queue()
                
        except Exception as e:
            print(f'Error posting to API: {e}')

    def clear_queue(self):
        """Clear all pending commands from the queue"""
        print("Clearing command queue...")
        while not self.movement_queue.empty():
            try:
                self.movement_queue.get_nowait()
                self.movement_queue.task_done()
            except Exception as e:
                print(f'Error clearing queue: {e}')
                break
        print('Queue cleared')

    def stop_threads(self):
        """Stop all threads and automation"""
        print("Stopping all threads...")
        self.stop_automation()
        self.stop_event.set()
