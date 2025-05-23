"""
FUNCTIONS:
1. apply_gaussian_blur(image, kernel_size)
   INPUT: image (OpenCV image), kernel_size (tuple, default (9,9))
   OUTPUT: Blurred image
   SUMMARY: Applies Gaussian blur filter to reduce image noise

2. canny_edge_detection(image, low_threshold, high_threshold)
   INPUT: image (OpenCV image), low_threshold (int, default 150), high_threshold (int, default 200)
   OUTPUT: Edge-detected binary image
   SUMMARY: Detects edges in image using Canny edge detection algorithm

3. dilate_with_buffer(image, buffer_radius)
   INPUT: image (OpenCV image), buffer_radius (int, default 5)
   OUTPUT: Dilated image
   SUMMARY: Applies morphological dilation to expand white regions in binary image

4. calc_angle(x1, y1, x2, y2)
   INPUT: x1, y1, x2, y2 (coordinates of two points)
   OUTPUT: Angle in degrees
   SUMMARY: Calculates angle between two points using arctangent

5. calc_distance(x1, y1, x2, y2)
   INPUT: x1, y1, x2, y2 (coordinates of two points)
   OUTPUT: Euclidean distance
   SUMMARY: Calculates straight-line distance between two points

6. bluescale(frame)
   INPUT: frame (OpenCV BGR image)
   OUTPUT: Blue-tinted image
   SUMMARY: Converts image to blue color scheme by setting HSV hue to 120 degrees

7. hsv_mask(frame)
   INPUT: frame (OpenCV BGR image)
   OUTPUT: Masked image with white/bright regions isolated
   SUMMARY: Creates HSV mask to isolate bright white regions in image

8. closing(masked, full)
   INPUT: masked (processed image), full (original image)
   OUTPUT: Morphologically closed image
   SUMMARY: Applies morphological closing operation to fill gaps in detected regions

9. polyfit_line(points)
   INPUT: points (numpy array of coordinate points)
   OUTPUT: Line coordinates [x1, y1, x2, y2] or None
   SUMMARY: Fits best-fit line through points using polynomial fitting

10. horizontal_detection(frame)
    INPUT: frame (OpenCV image)
    OUTPUT: detect_flag (boolean), new (image with horizontal line overlay)
    SUMMARY: Detects horizontal lines using Hough transform and draws weighted center line

11. vertical_detection(frame)
    INPUT: frame (OpenCV image)
    OUTPUT: detect_flag (boolean), new (image with vertical line overlays)
    SUMMARY: Detects left/right vertical lines and draws center path between them

12. post_direction(direction)
    INPUT: direction (string, default 'forward')
    OUTPUT: None
    SUMMARY: Sends movement command to robot API endpoint

13. apply_overlay(frame, movement_queue)
    INPUT: frame (OpenCV image), movement_queue (Queue object)
    OUTPUT: processed_frame, line_type (string or None)
    SUMMARY: Main processing function that detects martians, horizontal/vertical lines and queues commands

14. martian_detection(frame)
    INPUT: frame (OpenCV image)
    OUTPUT: existence (boolean), processed_frame
    SUMMARY: Uses ORB feature matching to detect martian reference image in current frame
"""

import cv2
import numpy as np
import time
import requests

# Apply Gaussian blur filter to reduce image noise
def apply_gaussian_blur(image, kernel_size=(9, 9)):
    return cv2.GaussianBlur(image, kernel_size, 0)

# Detect edges in image using Canny edge detection algorithm
def canny_edge_detection(image, low_threshold=150, high_threshold=200):
    return cv2.Canny(image, low_threshold, high_threshold)

# Apply morphological dilation to expand white regions in binary image
def dilate_with_buffer(image, buffer_radius=5):
    kernel = np.ones((buffer_radius, buffer_radius), np.uint8)
    return cv2.dilate(image, kernel, iterations=1)

# Calculate angle between two points using arctangent
def calc_angle(x1, y1, x2, y2):
    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
    return angle

# Calculate straight-line distance between two points
def calc_distance(x1, y1, x2, y2):
    return np.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)

# Convert image to blue color scheme by setting HSV hue to 120 degrees
def bluescale(frame):
    copy = frame.copy()
    hsv_ver = cv2.cvtColor(copy, cv2.COLOR_BGR2HSV)
    hsv_ver[:, :, 0] = 120
    return cv2.cvtColor(hsv_ver, cv2.COLOR_HSV2BGR)

# Create HSV mask to isolate bright white regions in image
def hsv_mask(frame):
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

    lower = np.array([0, 0, 150])
    upper = np.array([180, 170, 255])
    mask = cv2.inRange(hsv, lower, upper)

    masked = cv2.bitwise_and(frame, frame, mask=mask)

    return masked

# Apply morphological closing operation to fill gaps in detected regions
def closing(masked, full):
    gray = cv2.cvtColor(masked, cv2.COLOR_BGR2GRAY)
    closing = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8), iterations=3)
    final = cv2.bitwise_and(masked, full, mask=closing)
    return final

# Fit best-fit line through points using polynomial fitting
def polyfit_line(points):
    try:
        slope, intercept = np.polyfit(points[:, 0], points[:, 1], 1)
        x1, x2 = min(points[:, 0]), max(points[:, 0])
        y1, y2 = (slope * x1 + intercept), (slope * x2 + intercept)
        return [x1, y1, x2, y2]
    except:
        return None

# Detect horizontal lines using Hough transform and draw weighted center line
def horizontal_detection(frame):
    new = frame.copy()

    detect_flag = False

    lines = cv2.HoughLinesP(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1, np.pi / 180, 100, minLineLength=80,
                            maxLineGap=10)
    if lines is not None:
        hori_lines = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if abs(y2 - y1) < abs(x2 - x1):
                hori_lines.append(((y1 + y2) // 2, abs(x2 - x1)))

        if hori_lines:
            detect_flag = True
            weighted_sum = sum(y * length for y, length in hori_lines)
            total_length = sum(length for _, length in hori_lines)

            if total_length > 0:
                center_y = int(weighted_sum / total_length)
            else:
                center_y = frame.shape[0] // 2

            cv2.line(new, (0, center_y), (new.shape[1], center_y), (0, 0, 255), 2)

    return detect_flag, new

# Detect left/right vertical lines and draw center path between them
def vertical_detection(frame):
    new = frame.copy()
    detect_flag = False

    leftline = []
    rightline = []
    lines = cv2.HoughLinesP(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), 1, np.pi / 180, 100, minLineLength=80,
                            maxLineGap=10)
    if lines is not None:
        for line in lines:
            x1, y1, x2, y2 = line[0]
            if not abs(y2 - y1) > abs(x2 - x1):
                return detect_flag, new
            if x2 - x1 != 0:
                if (y2 - y1) / (x2 - x1) > 0:
                    leftline.append([x1, y1, x2, y2])
                else:
                    rightline.append([x1, y1, x2, y2])

    if len(leftline) < 1 or len(rightline) < 1:
        return detect_flag, new

    leftline = np.array(leftline)
    rightline = np.array(rightline)

    leftline = polyfit_line(leftline)
    rightline = polyfit_line(rightline)

    if leftline is None or rightline is None:
        return detect_flag, new

    l_x1, l_y1, l_x2, l_y2 = leftline
    r_x1, r_y1, r_x2, r_y2 = rightline

    cv2.line(new, (l_x1, l_y1), (l_x2, l_y2), (0, 0, 255), 3)
    cv2.line(new, (r_x1, r_y1), (r_x2, r_y2), (0, 0, 255), 3)

    if calc_distance(l_x1, l_y1, r_x1, r_y1) < calc_distance(l_x1, l_y1, r_x2, r_y2):
        mid_x1 = (l_x1 + r_x1) // 2
        mid_y1 = (l_y1 + r_y1) // 2
        mid_x2 = (l_x2 + r_x2) // 2
        mid_y2 = (l_y2 + r_y2) // 2
    else:
        mid_x1 = (l_x1 + r_x2) // 2
        mid_y1 = (l_y1 + r_y2) // 2
        mid_x2 = (l_x2 + r_x1) // 2
        mid_y2 = (l_y2 + r_y1) // 2

    cv2.line(new, (mid_x1, mid_y1), (mid_x2, mid_y2), (0, 0, 255), 3)
    detect_flag = True

    return detect_flag, new

# Send movement command to robot API endpoint
def post_direction(direction='forward'):
    try:
        url = 'http://192.168.240.25:5000/'
        endpoint = url + 'moving'
        data = {'direction': direction}
        req = requests.post(endpoint, json=data)
    except Exception as e:
        print(f'error: {e}')

# Main processing function that detects martians, horizontal/vertical lines and queues commands
def apply_overlay(frame, movement_queue):
    new = frame.copy()

    # first, do martian detection
    martian_frame, existence = martian_detection(new)
    if existence:
        try:
            movement_queue.put(('move', ('stop', 0)))
        except:
            pass
        cv2.putText(martian_frame, 'WE ARE NOT ALONE', (10, 50), cv2.FONT_HERSHEY_COMPLEX, 1, (0, 0, 255), 2,
                    cv2.LINE_AA)
        return martian_frame, None

    # then, process the image before further line detection
    blurred = apply_gaussian_blur(new)
    bluescaled = bluescale(blurred)
    masked = hsv_mask(bluescaled)
    closed = closing(masked, new)

    # now, do horizontal line detection
    hori_cropped = closed[130:170, :].copy()
    hori_flag, overlay = horizontal_detection(hori_cropped)
    if hori_flag:
        try:
            movement_queue.put(('horizontal_line_detected', None))
        except:
            pass
        new[130:170, :] = overlay
        cv2.rectangle(new, (0, 130), (new.shape[1], 170), (255, 0, 255), 2)
        return new, 'horizontal'

    # now, if that didnt work, do vertical line detection
    vert_flag, overlay = vertical_detection(closed)
    if vert_flag:
        return overlay, 'vertical'

    return new, None

# Use ORB feature matching to detect martian reference image in current frame
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
