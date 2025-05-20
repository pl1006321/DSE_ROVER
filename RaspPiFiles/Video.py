import cv2
import base64
import requests
import time

# make sure to change this to the correct url!! 
api_url = "http://192.168.240.22:5000/vidstream"

cap = cv2.VideoCapture(0)

# make sure video capture is open
if not cap.isOpened():
    print("Error: Unable to open video stream")
    exit()

# set frame rate to ensure its not lagging that badly 
frame_rate = 7
prev_time = 0

# capture n send frames
while True:
    # capture frame by frame
    ret, frame = cap.read()
    if not ret:
        print("Error: Unable to capture video frame")
        break

    # limit frame rate
    current_time = time.time()
    if (current_time - prev_time) < 1.0 / frame_rate:
        continue
    prev_time = current_time

    frame = cv2.resize(frame, (400, 300))

    # encode frame to jpeg
    _, buffer = cv2.imencode('.jpg', frame)

    # convert to b64 for jsonifying
    base64_image = base64.b64encode(buffer).decode('utf-8')

    # create the json payload
    payload = {
        "frame": base64_image,
    }

    # send frame to api
    headers = {'Content-Type': 'application/json'}
    response = requests.post(api_url, json=payload, headers=headers)

    # break loop once q is clicked
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# release capture 
cap.release()
