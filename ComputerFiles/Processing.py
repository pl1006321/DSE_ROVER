import cv2
import numpy as np
import time
import requests

# Functions that use the basic OpenCv functions to help detect things within the image
def apply_gaussian_blur(image, kernel_size=(9, 9)):
    return cv2.GaussianBlur(image, kernel_size, 0)

def canny_edge_detection(image, low_threshold=150, high_threshold=200):
    return cv2.Canny(image, low_threshold, high_threshold)

def dilate_with_buffer(image, buffer_radius=5):
    kernel = np.ones((buffer_radius, buffer_radius), np.uint8)
    return cv2.dilate(image, kernel, iterations=1)

def calc_angle(x1, y1, x2, y2):
    angle = np.degrees(np.arctan2(y2-y1, x2-x1))
    return angle

def calc_distance(x1, y1, x2, y2):
    return np.sqrt((y2-y1)**2 + (x2-x1)**2)

def bluescale(frame):
    copy = frame.copy()
    hsv_ver = cv2.cvtColor(copy, cv2.COLOR_BGR2HSV)
    hsv_ver[:, :, 0] = 120
    return cv2.cvtColor(hsv_ver, cv2.COLOR_HSV2BGR)

def hsv_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower_blue = np.array([100, 50, 50])
    upper_blue = np.array([140, 255, 255])
    mask = cv2.inRange(hsv, lower_blue, upper_blue)

    masked = cv2.bitwise_and(frame, frame, mask=mask)

    return masked
    
def horizontal_detection(frame):
    new = frame.copy()

    detect_flag = False

    new = cv2.cvtColor(new, cv2.COLOR_BGR2GRAY)
    lines = cv2.HoughLinesP(new, 1, np.pi/180, 100, minLineLength=80, maxLineGap=10)
    if lines is not None:
        hori_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y2-y1) < abs(x2-x1):
                hori_lines.append(((y1 + y2) // 2, abs(x2-x1)))

        if hori_lines:
            detect_flag = True
            weighted_sum = sum(y * length for y, length in hori_lines)
            total_length = sum(length for _, length in hori_lines)

            if total_length > 0:
                center_y = int(weighted_sum / total_length)
            else: 
                center_y = frame.shape[0] // 2
            
            cv2.line(new, (0, center_y), (new.shape[1], center_y),(0, 0, 255), 2)
    
    return detect_flag, new

def vertical_detection(frame):
    new = frame.copy() 
    detect_flag = False

    x_vals = []
    new = cv2.cvtColor(new, cv2.COLOR_BGR2GRAY)
    lines = cv2.HoughLinesP(new, 1, np.pi/180, 100, minLineLength=80, maxLineGap=10)
    if lines is not None:    
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y2-y1) > abs(x2-x1):
                x_vals.append((x1 + x2) // 2)

    if len(x_vals) > 0:
        mid_x = sum(x_vals) // len(x_vals)
        cv2.line(new, (mid_x, 0), (mid_x, new.shape[0]), (0, 0, 255), 2)
        detect_flag = True

    return detect_flag, new
    

def post_direction(direction='forward'):
    try:
        url = 'http://192.168.240.25:5000/'
        endpoint = url + 'moving'
        data = {'direction': direction}
        req = requests.post(endpoint, json=data)
    except Exception as e:
        print(f'error: {e}')


def apply_overlay(frame, movement_queue):
    new = frame.copy() 
    
    # first, do martian detection
    martian_frame, existence = martian_detection(new)
    if existence:
        try:
            movement_queue.put(('move', ('stop', 0)))
        except: pass
        cv2.putText(martian_frame, 'WE ARE NOT ALONE', (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        return martian_frame, None
    
    # then, process the image before further line detection
    blurred = apply_gaussian_blur(new)
    bluescaled = bluescale(blurred)
    masked = hsv_mask(bluescaled)

    # now, do horizontal line detection
    hori_cropped = masked[130:170, :].copy()
    hori_flag, overlay = horizontal_detection(hori_cropped)
    if hori_flag:
        try:
            movement_queue.put(('horizontal_line_detected', None))
        except: pass
        new[130:170, :] = overlay
        cv2.rectangle(new, (0, 130), (new.shape[1], 170), (255, 0, 255), 2)
        return new, 'horizontal'
    
    # now, if that didnt work, do vertical line detection 
    vert_flag, overlay = vertical_detection(masked)
    if vert_flag:
        return overlay, 'vertical'
    
    return new, None


def martian_detection(frame):
    existence = False

    ref = cv2.imread('ref_marvin.jpeg', cv2.IMREAD_GRAYSCALE)
    h, w = ref.shape

    frame_processed = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_processed = cv2.GaussianBlur(frame_processed, (9, 9), 0)
    orb = cv2.ORB_create()

    keypts_ref, descriptors_ref = orb.detectAndCompute(ref, None)
    keypts_frame, descriptors_frame = orb.detectAndCompute(frame_processed, None)

    if descriptors_frame is None or descriptors_ref is None:
        return frame.copy(), existence

    if descriptors_frame.shape[1] != descriptors_ref.shape[1]:
        return frame.copy(), existence

    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    good_matches1to2 = []
    good_matches2to1 = []

    matches1to2 = bf.knnMatch(descriptors_ref, descriptors_frame, k=2)
    for match in matches1to2:
        if len(match) == 2:
            m, n = match
            if m.distance < 0.7 * n.distance:
                good_matches1to2.append(m)

    matches2to1 = bf.knnMatch(descriptors_frame, descriptors_ref, k=2)
    for match in matches2to1:
        if len(match) == 2:
            m, n = match
            if m.distance < 0.7 * n.distance:
                good_matches2to1.append(m)

    good_matches = []
    for m in good_matches1to2:
        for n in good_matches2to1:
            if m.queryIdx == n.trainIdx and m.trainIdx == n.queryIdx:
                good_matches.append(m)
                break

    print(f'good matches: {len(good_matches)}')

    if len(good_matches) >= 2:
        existence = True
        post_direction('stop')
        print('martian detected!')
        cv2.putText(frame, 'martian detected!', (10, 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2, cv2.LINE_AA)
        return frame.copy(), existence

    return frame.copy(), existence
