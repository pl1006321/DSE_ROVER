"""
Code Version 3.2

MAIN ENTRY POINT - main.py

This file serves as the entry point for the robot control application. It imports all necessary modules and launches the graphical user interface system.

IMPORTED MODULES AND THEIR FUNCTIONS:
1. Automation - Handles automated robot movement and video processing
   - Video stream processing and feature detection
   - Obstacle avoidance sequences
   - Line following algorithms
   - Movement command queue management

2. Database - Manages user authentication and credential storage
   - SQLite database initialization and connection management
   - User account creation and validation
   - Secure credential storage and retrieval

3. GUI - Provides the graphical user interface
   - Login page with username/password authentication
   - Robot control panel with movement buttons
   - Video stream display (original and overlay)
   - Command logging and system monitoring
   - Integration with automation system

4. Processing - Computer vision and image processing functions
   - Gaussian blur, edge detection, and morphological operations
   - Horizontal and vertical line detection using Hough transforms
   - Martian detection using ORB feature matching
   - HSV masking and color space conversions

APPLICATION FLOW:
1. Import all required modules
2. Launch GUI system via GUI.launch_guis()
3. User authentication through login interface
4. Robot control interface becomes available
5. Video processing and automation can be activated
"""

import Automation
import Database
from GUI import GUI
import Processing
from tkinter import *
from sqlite3 import *

# Launch the main GUI application
GUI.launch_guis()
