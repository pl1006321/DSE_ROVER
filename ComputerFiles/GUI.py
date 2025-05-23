"""
FUNCTIONS:
1. __init__(root)
   INPUT: root (Tkinter root window object)
   OUTPUT: Initialized GUI object
   SUMMARY: Initializes main GUI window, database object, and launches login page

2. setup_login_page()
   INPUT: None
   OUTPUT: None
   SUMMARY: Creates login interface with username/password fields and login/create account buttons

3. login()
   INPUT: None (uses self.user_entry_text and self.pw_entry_text)
   OUTPUT: None
   SUMMARY: Validates user credentials against database and launches robot GUI on success

4. create_acc()
   INPUT: None (uses self.user_entry_text and self.pw_entry_text)
   OUTPUT: None
   SUMMARY: Creates new user account in database if username doesn't already exist

5. post_direction(direction)
   INPUT: direction (string: movement command)
   OUTPUT: None
   SUMMARY: Sends movement command to robot API and logs the action

6. play_button()
   INPUT: None
   OUTPUT: None
   SUMMARY: Initializes automation system and starts video/movement threads

7. stop_button_handler()
   INPUT: None
   OUTPUT: None
   SUMMARY: Stops automation threads and sends stop command to robot

8. create_robot_gui()
   INPUT: None
   OUTPUT: None
   SUMMARY: Creates main robot control interface with video streams, control buttons, and logging

9. logging(direction)
   INPUT: direction (string: movement command)
   OUTPUT: None
   SUMMARY: Retrieves timestamp from API, logs command to file and text area

10. stop_video()
    INPUT: None
    OUTPUT: None
    SUMMARY: Sets video pause flag to stop video processing

11. open_log_file()
    INPUT: None
    OUTPUT: None
    SUMMARY: Opens system log file in default system application

12. launch_guis() [static method]
    INPUT: None
    OUTPUT: None
    SUMMARY: Creates Tkinter root window and starts main GUI application loop
"""

from tkinter import *
from tkinter.scrolledtext import *
from tkinter.font import Font
from PIL import Image, ImageTk
import os
import subprocess
import socket
from threading import Thread
import cv2
import numpy as np
import Database
import requests
from tkinter import messagebox
import base64
from datetime import datetime
import Automation

url = 'http://192.168.240.22:5000/'

class GUI:
    # Initialize main GUI window, database object, and launch login page
    def __init__(self, root):
        self.root = root
        self.root.title('user login')
        self.root.geometry('320x150')
        self.database = Database.Database()
 
        self.setup_login_page()

    # Create login interface with username/password fields and login/create account buttons
    def setup_login_page(self):
        self.user_entry_text = StringVar()
        self.pw_entry_text = StringVar()

        entries_panel = Frame(self.root)
        entries_panel.grid(row=1, column=1, rowspan=3, padx=10, pady=5, sticky='NWSE')

        username_entry_label = Label(entries_panel, text='username: ')
        username_entry_label.grid(row=1, column=1, padx=5, pady=5)

        username_entry = Entry(entries_panel, textvariable=self.user_entry_text,)
        username_entry.grid(row=1, column=2, padx=5, pady=5)

        password_entry_label = Label(entries_panel, text='password: ')
        password_entry_label.grid(row=2, column=1, padx=5, pady=5)

        password_entry = Entry(entries_panel, textvariable=self.pw_entry_text, show='*')
        password_entry.grid(row=2, column=2, padx=5, pady=5)

        buttons_panel = Frame(self.root)
        buttons_panel.grid(row=5, column=1, rowspan=1, padx=45, pady=5, sticky='NWSE')

        login_button = Button(buttons_panel, text='login', command=self.login)
        login_button.grid(row=1, column=1, ipadx=3, ipady=2, padx=5, pady=5)

        create_acc_button = Button(buttons_panel, text='create account', command=self.create_acc) 
        create_acc_button.grid(row=1, column=2, ipadx=3, ipady=2, padx=5, pady=5)

    # Validate user credentials against database and launch robot GUI on success
    def login(self):
        username = self.user_entry_text.get()
        password = self.pw_entry_text.get()

        if not username or not password:
            messagebox.showinfo(message='one or more entries were left blank. please try again')
            return
        
        if not self.database.user_exists(username):
            messagebox.showinfo(message='invalid username. please try again')
            return
    
        if password != self.database.get_password(username):
            messagebox.showinfo(message='invalid password. please try again')
            return

        self.username = username
        
        messagebox.showinfo(message=f'login successful! welcome {username}')
        self.create_robot_gui()

    # Create new user account in database if username doesn't already exist
    def create_acc(self):
        username = self.user_entry_text.get()
        password = self.pw_entry_text.get()

        if not username or not password:
            messagebox.showinfo(message='one or more entries were left blank. please try again')
            return
        
        if self.database.user_exists(username):
            messagebox.showinfo(message='account with this username already exists.')
            return
        
        self.database.insert_user(username, password)
        messagebox.showinfo(message=f'account creation successful!')

    # Send movement command to robot API and log the action
    def post_direction(self, direction):
        try:
            endpoint = url + 'moving'
            data = {'direction': direction}
            req = requests.post(endpoint, json=data)
            print('command sent successfully')
            self.logging(direction)
        except:
            print('something happened; error')

    # Initialize automation system and start video/movement threads
    def play_button(self):
        self.automation = Automation.Automation(self.stream_elem, self.overlay_elem)
        self.video_thread, self.movement_thread = self.automation.start_threads()

    # Stop automation threads and send stop command to robot
    def stop_button_handler(self):
        if hasattr(self, 'automation'):
            self.automation.stop_event.set()
            self.automation.stop_automation()
            self.post_direction('stop')
        else:
            self.post_direction('stop')

    # Create main robot control interface with video streams, control buttons, and logging
    def create_robot_gui(self):
        robot_gui = Toplevel()
        robot_gui.title('robot gui')
        robot_gui.geometry('1100x800')

        custom_font = Font(family='Poppins', size=20)
        
        vid_stream_panel = Frame(robot_gui)
        vid_stream_panel.grid(row=5, column=1, rowspan=1, padx=5, pady=5, sticky='NWSE')

        buttons_panel = Frame(robot_gui)
        buttons_panel.grid(row=5, column=2, rowspan=1, padx=20, pady=95, sticky='NWSE')

        vid_overlay_panel = Frame(robot_gui)
        vid_overlay_panel.grid(row=6, column=1, rowspan=1, padx=5, pady=5, sticky='NWSE')

        log_panel = Frame(robot_gui)
        log_panel.grid(row=6, column=2, rowspan=1, padx=10, pady=50, sticky='NS')

        self.text_area = ScrolledText(log_panel, width=55, height=5)
        self.text_area.grid(row=1, padx=5, pady=5, ipadx=20, ipady=20)
        self.text_area.config(state='disabled')

        log_button = Button(log_panel, text='open log file', command=self.open_log_file, font=custom_font, padx=5, pady=7)
        log_button.grid(row=2, padx=4, pady=5, ipadx=5, ipady=5)

        black_img = np.zeros((300, 400, 3), dtype=np.uint8)
        black_img = ImageTk.PhotoImage(Image.fromarray(black_img))

        self.stream_elem = Label(vid_stream_panel, text='video stream')
        self.stream_elem.grid(padx=50, pady=40)
        self.stream_elem.imgtk = black_img
        self.stream_elem.configure(image=black_img)

        self.overlay_elem = Label(vid_overlay_panel, text='overlay stream')
        self.overlay_elem.grid(padx=50, pady=10)
        self.overlay_elem.imgtk = black_img
        self.overlay_elem.configure(image=black_img)

        forward = Button(buttons_panel, text='move forward', font=custom_font, padx=5, pady=7,)
        forward.grid(row=1, column=2, padx=5, pady=5, ipadx=5, ipady=5, sticky='we', columnspan=2)
        forward.bind('<ButtonPress-1>', lambda event: self.post_direction('forward'))
        forward.bind('<ButtonRelease-1>', lambda event: self.post_direction('stop'))

        left = Button(buttons_panel, text='move left', font=custom_font, padx=5, pady=7)
        left.grid(row=2, column=1, padx=2.5, pady=5, ipadx=5, ipady=5)
        left.bind('<ButtonPress-1>', lambda event: self.post_direction('left'))
        left.bind('<ButtonRelease-1>', lambda event: self.post_direction('stop'))

        play = Button(buttons_panel, text='play', font=custom_font, padx=5, pady=7, command = self.play_button)
        play.grid(row=2, column=2, padx=2.5, pady=5, ipadx=5, ipady=5, sticky='we')

        stop = Button(buttons_panel, text='stop', font=custom_font, padx=5, pady=7, command=self.stop_button_handler)
        stop.grid(row=2, column=3, padx=2.5, pady=5, ipadx=5, ipady=5, sticky='we')

        right = Button(buttons_panel, text='move right', font=custom_font, padx=5, pady=7)
        right.grid(row=2, column=4, padx=2.5, pady=5, ipadx=5, ipady=5)
        right.bind('<ButtonPress-1>', lambda event: self.post_direction('right'))
        right.bind('<ButtonRelease-1>', lambda event: self.post_direction('stop'))

        backward = Button(buttons_panel, text='move backward', font=custom_font, padx=5, pady=7)
        backward.grid(row=3, column=2, padx=2.5, pady=5, ipadx=5, ipady=5, sticky='we', columnspan=2)
        backward.bind('<ButtonPress-1>', lambda event: self.post_direction('backward'))
        backward.bind('<ButtonRelease-1>', lambda event: self.post_direction('stop'))

        ip_addr = socket.gethostbyname(socket.gethostname())
        time = datetime.now() 
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')        
        msg = f'{self.username}@{ip_addr} has logged in at {timestamp}\n'
        with open('system_log.txt', 'a') as file:
            file.write(msg)
        file.close()
        self.text_area.config(state='normal')
        self.text_area.insert(END, msg)
        self.text_area.see(END)
        self.text_area.config(state='disabled')

    # Retrieve timestamp from API, log command to file and text area
    def logging(self, direction):
        try:
            endpoint = url + 'logging'
            log = requests.get(endpoint)
            log = log.json()
            log_str = f"{log['Timestamp']} - {self.username}@{log['IP Address']} sent the command: {direction}\n"
            with open("system_log.txt", 'a') as file:
                file.write(log_str)
            self.text_area.config(state='normal')
            self.text_area.insert(END, log_str)
            self.text_area.see(END)
            self.text_area.config(state='disabled')
        except:
            print('an error occured sorry!')

    # Set video pause flag to stop video processing
    def stop_video(self):
        self.video_paused = True

    # Open system log file in default system application
    def open_log_file(self):
        file_path = 'system_log.txt'
        if not os.path.exists(file_path):
            open(file_path, 'w').close()
        subprocess.call(('open', file_path))

    # Create Tkinter root window and start main GUI application loop
    @staticmethod
    def launch_guis():
        root = Tk() 
        app = GUI(root)
        root.mainloop()

