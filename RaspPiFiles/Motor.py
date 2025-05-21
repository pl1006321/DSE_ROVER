from adafruit_motorkit import MotorKit
from gpiozero import DistanceSensor
import board

import time
kit = MotorKit(0x40)
ultrasonic = DistanceSensor(echo=17, trigger=4)


# this function powers both motors forward
def forward():
    kit.motor1.throttle = -0.77
    # motor 1 is slightly weaker than motor 2 so adjustments had to be made
    kit.motor2.throttle = -0.70


# this function powers both motors backward
def backward():
    kit.motor1.throttle = 0.74
    kit.motor2.throttle = 0.715
    # same throttles as moving forward, but negated values 


# this function moves the right motor forward and the left motor backward
# this creates a counterclockwise sprin 
def left():
    # moves it backward slightly before turning 
    kit.motor1.throttle = -0.793 
    kit.motor2.throttle = 0.75 
    # time.sleep(0.15) # allows for turning in small increments


# this function moves the right motor backward and the left motor forward
# this creates a clockwise spin
def right():
    kit.motor1.throttle = 0.793 
    kit.motor2.throttle = -0.75
    # time.sleep(0.15) # allows for turning in small incremenets


# this function sets both motors speed to 0, stopping movement 
def stop():
    kit.motor1.throttle = 0.0
    kit.motor2.throttle = 0.0

def get_distance():
    distance = ultrasonic.distance
    return distance < 0.25
