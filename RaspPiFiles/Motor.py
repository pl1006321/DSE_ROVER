"""
FUNCTIONS:
1. forward()
   INPUT: None
   OUTPUT: None
   SUMMARY: Powers both motors forward with adjusted throttle values to compensate for motor differences

2. backward()
   INPUT: None
   OUTPUT: None
   SUMMARY: Powers both motors backward with negated throttle values from forward motion

3. left()
   INPUT: None
   OUTPUT: None
   SUMMARY: Creates counterclockwise spin by moving right motor forward and left motor backward

4. right()
   INPUT: None
   OUTPUT: None
   SUMMARY: Creates clockwise spin by moving left motor forward and right motor backward

5. stop()
   INPUT: None
   OUTPUT: None
   SUMMARY: Sets both motor throttles to zero to stop all movement

6. get_distance()
   INPUT: None
   OUTPUT: Boolean (True if obstacle detected within 0.25m, False otherwise)
   SUMMARY: Reads ultrasonic sensor distance and returns obstacle detection status
"""

from adafruit_motorkit import MotorKit
from gpiozero import DistanceSensor
import board

import time
kit = MotorKit(0x40)
ultrasonic = DistanceSensor(echo=17, trigger=4)

# Power both motors forward with adjusted throttle values to compensate for motor differences
def forward():
    kit.motor1.throttle = -0.77
    # motor 1 is slightly weaker than motor 2 so adjustments had to be made
    kit.motor2.throttle = -0.70

# Power both motors backward with negated throttle values from forward motion
def backward():
    kit.motor1.throttle = 0.74
    kit.motor2.throttle = 0.715
    # same throttles as moving forward, but negated values 

# Create counterclockwise spin by moving right motor forward and left motor backward
def left():
    # moves it backward slightly before turning 
    kit.motor1.throttle = -0.793 
    kit.motor2.throttle = 0.75 
    # time.sleep(0.15) # allows for turning in small increments

# Create clockwise spin by moving left motor forward and right motor backward
def right():
    kit.motor1.throttle = 0.793 
    kit.motor2.throttle = -0.75
    # time.sleep(0.15) # allows for turning in small incremenets

# Set both motor throttles to zero to stop all movement
def stop():
    kit.motor1.throttle = 0.0
    kit.motor2.throttle = 0.0

# Read ultrasonic sensor distance and return obstacle detection status
def get_distance():
    distance = ultrasonic.distance
    return distance < 0.25

