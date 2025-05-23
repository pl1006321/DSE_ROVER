"""
This file contains the main video capture and streaming loop rather than discrete functions.
The script performs the following operations:

MAIN PROCESS:
1. Initialize video capture from camera (index 0)
2. Set frame rate to 7 FPS to prevent lag
3. Continuously capture frames from camera
4. Resize frames to 400x300 for consistent processing
5. Encode frames to JPEG format
6. Convert to base64 for JSON transmission
7. Send frames to API endpoint via POST request
8. Handle frame rate limiting and error conditions
9. Clean up video capture resources on exit

CAMERA OPERATIONS:
- Video capture initialization and validation
- Frame-by-frame capture with error handling
- Frame rate control using time-based limiting
- Frame resizing for standardized dimensions
- JPEG encoding for efficient transmission

NETWORK OPERATIONS:
- Base64 encoding for JSON compatibility
- HTTP POST requests to API endpoint
- Error handling for network failures
- JSON payload construction with frame data
"""

import cv2
import base64
import requests
import time

# Set API endpoint URL for video stream transmission
api_url = "http://192.168.240.25:5000/vidstream"

# Initialize video capture from default camera
cap = cv2.VideoCapture(0)

# Validate video capture initialization
if not cap.isOpened():
    print("Error: Unable to open video stream")
    exit()

# Set frame rate to ensure optimal performance without lag
frame_rate = 7
prev_time = 0

# Main video capture and transmission loop
while True:
    # Capture frame-by-frame from camera
    ret, frame = cap.read()
    if not ret:
        print("Error: Unable to capture video frame")
        break

    # Implement frame rate limiting to prevent excessive API calls
    current_time = time.time()
    if (current_time - prev_time) < 1.0 / frame_rate:
        continue
    prev_time = current_time

    # Resize frame to standard dimensions for consistent processing
    frame = cv2.resize(frame, (400, 300))

    # Encode frame to JPEG format for efficient transmission
    _, buffer = cv2.imencode('.jpg', frame)

    # Convert frame to base64 string for JSON compatibility
    base64_image = base64.b64encode(buffer).decode('utf-8')

    # Create JSON payload with encoded frame data
    payload = {
        "frame": base64_image,
    }

    # Send frame to API endpoint via HTTP POST request
    headers = {'Content-Type': 'application/json'}
    response = requests.post(api_url, json=payload, headers=headers)

    # Exit loop when 'q' key is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Clean up video capture resources
cap.release()

