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


def FWD():
    json_thing['direction'] = 'forward'
    print('going forward')  # debugging purposes; makes sure api has received the command
    motor.forward()
    return jsonify(json_thing)  # returns json data into the main function
    # the function structure + logic is the same for all other movement functions


def BACKWD():
    json_thing['direction'] = 'backward'
    print('going backward')
    motor.backward()
    return jsonify(json_thing)


def LEFT():
    json_thing['direction'] = 'left'
    print('going left')
    motor.left()
    return jsonify(json_thing)


def RIGHT():
    json_thing['direction'] = 'right'
    print('going right')
    motor.right()
    return jsonify(json_thing)


def STOP():
    json_thing['direction'] = 'stop'
    print('stopping')
    motor.stop()
    return jsonify(json_thing)


@app.route('/', methods=['GET'])  # landing page
def default():
    return 'api created by left no scrums'


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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)  # runs api
