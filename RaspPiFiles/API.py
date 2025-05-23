"""
FUNCTIONS:
1. FWD()
   INPUT: None
   OUTPUT: JSON response with direction 'forward'
   SUMMARY: Sets direction to forward, calls motor forward function, returns JSON confirmation

2. BACKWD()
   INPUT: None
   OUTPUT: JSON response with direction 'backward'
   SUMMARY: Sets direction to backward, calls motor backward function, returns JSON confirmation

3. LEFT()
   INPUT: None
   OUTPUT: JSON response with direction 'left'
   SUMMARY: Sets direction to left, calls motor left function, returns JSON confirmation

4. RIGHT()
   INPUT: None
   OUTPUT: JSON response with direction 'right'
   SUMMARY: Sets direction to right, calls motor right function, returns JSON confirmation

5. STOP()
   INPUT: None
   OUTPUT: JSON response with direction 'stop'
   SUMMARY: Sets direction to stop, calls motor stop function, returns JSON confirmation

6. default()
   INPUT: None (GET request to root)
   OUTPUT: String message
   SUMMARY: Returns landing page message identifying API creator

7. direction()
   INPUT: JSON with direction field (POST) or None (GET)
   OUTPUT: JSON response with movement confirmation or last command
   SUMMARY: Handles movement commands via POST and returns status via GET

8. log_direction(the_direction, ip_addr)
   INPUT: the_direction (string), ip_addr (string) - optional parameters
   OUTPUT: JSON log data or None
   SUMMARY: Logs movement commands with timestamp and IP, returns log data on GET request

9. video_stream()
   INPUT: Base64 encoded frame (POST) or None (GET)
   OUTPUT: Success message (POST) or base64 frame (GET)
   SUMMARY: Receives video frames via POST and serves latest frame via GET

10. get_obstacle_status()
    INPUT: None (GET request)
    OUTPUT: JSON with distance sensor reading
    SUMMARY: Returns current obstacle detection status from ultrasonic sensor
"""

from flask import Flask, jsonify, request
from datetime import *
import base64
import cv2
import numpy as np
import time

import Motor as motor

global result
json_thing = {'direction': None}  # sets up dictionary to be edited later on in functions
final_log = {}

app = Flask(__name__)  # creates instance of flask

# Set direction to forward, call motor forward function, return JSON confirmation
def FWD():
    json_thing['direction'] = 'forward'
    print('going forward')  # debugging purposes; makes sure api has received the command
    motor.forward()
    return jsonify(json_thing)  # returns json data into the main function
    # the function structure + logic is the same for all other movement functions

# Set direction to backward, call motor backward function, return JSON confirmation
def BACKWD():
    json_thing['direction'] = 'backward'
    print('going backward')
    motor.backward()
    return jsonify(json_thing)

# Set direction to left, call motor left function, return JSON confirmation
def LEFT():
    json_thing['direction'] = 'left'
    print('going left')
    motor.left()
    return jsonify(json_thing)

# Set direction to right, call motor right function, return JSON confirmation
def RIGHT():
    json_thing['direction'] = 'right'
    print('going right')
    motor.right()
    return jsonify(json_thing)

# Set direction to stop, call motor stop function, return JSON confirmation
def STOP():
    json_thing['direction'] = 'stop'
    print('stopping')
    motor.stop()
    return jsonify(json_thing)

# Return landing page message identifying API creator
@app.route('/', methods=['GET'])  # landing page
def default():
    return 'api created by left no scrums'

# Handle movement commands via POST and return status via GET
@app.route('/moving', methods=['POST', 'GET'])
def direction():
    if request.method == 'POST':
        direction = request.json['direction']  # extracts the direction out of json

        ip = request.remote_addr  # gets ip from where the request was sent
        log_direction(direction, ip)

        # runs a function based on which command was posted to api using if-elif
        if direction == 'forward':
            result = FWD()
        elif direction == 'backward':
            result = BACKWD()
        elif direction == 'left':
            result = LEFT()
        elif direction == 'right':
            result = RIGHT()
        elif direction == 'stop':
            result = STOP()

        try:
            time = request.json['time']
            time.sleep(time)
        except Exception as e:
            pass

        return result  # returns json data to api, which robot can then get the directional command
    if request.method == 'GET':
        # i want my code to return the last received directional command so its shown when visited on a browser
        return jsonify(json_thing)

# Log movement commands with timestamp and IP, return log data on GET request
@app.route('/logging', methods=['GET'])
def log_direction(the_direction=None, ip_addr=None):
    global final_log
    if the_direction and ip_addr:
        ip = ip_addr
        direction = the_direction
        time = datetime.now()
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        final_log = {'IP Address': ip,
                     'Direction Sent': direction,
                     'Timestamp': timestamp}
    else:
        return jsonify(final_log)

# Receive video frames via POST and serve latest frame via GET
@app.route('/vidstream', methods=['GET', 'POST'])
def video_stream():
    global latest_frame
    if request.method == 'POST':
        b64_image = request.get_json()['frame']
        decoded_img = base64.b64decode(b64_image)

        np_img = np.frombuffer(decoded_img, dtype=np.uint8)
        latest_frame = cv2.imdecode(np_img, cv2.IMREAD_COLOR)

        return jsonify({"message": "Frame received successfully!"})

    if request.method == 'GET':
        _, buffer = cv2.imencode('.jpg', latest_frame)
        b64_image = base64.b64encode(buffer).decode('utf-8')
        return jsonify({'frame': b64_image})

# Return current obstacle detection status from ultrasonic sensor
@app.route('/obstacle_status', methods=['GET'])
def get_obstacle_status():
    distance = motor.get_distance()
    return jsonify({
        'detect_flag': distance
    })

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # runs api

