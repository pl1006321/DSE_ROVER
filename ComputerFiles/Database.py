"""
FUNCTIONS:
1. __init__()
   INPUT: None
   OUTPUT: Initialized Database object
   SUMMARY: Initializes database by creating database file and users table if they don't exist

2. connect()
   INPUT: None
   OUTPUT: conn (connection object), cursor (cursor object)
   SUMMARY: Establishes connection to SQLite database and returns connection and cursor objects

3. commit_n_close(conn)
   INPUT: conn (SQLite connection object)
   OUTPUT: None
   SUMMARY: Commits pending changes to database and safely closes the connection

4. create_db()
   INPUT: None
   OUTPUT: None
   SUMMARY: Creates users table with id, username, and password columns if table doesn't exist

5. insert_user(username, password)
   INPUT: username (string), password (string)
   OUTPUT: None
   SUMMARY: Inserts new user credentials into the users table

6. user_exists(username)
   INPUT: username (string)
   OUTPUT: Boolean (True if user exists, False otherwise)
   SUMMARY: Checks if a user with the given username already exists in the database

7. get_password(username)
   INPUT: username (string)
   OUTPUT: password (string) or None if user doesn't exist
   SUMMARY: Retrieves the password for a given username from the database
"""

import sqlite3

class Database:
    # Initialize database by creating database file and users table if they don't exist
    def __init__(self):
        self.create_db() 

    # Establish connection to SQLite database and return connection and cursor objects
    def connect(self):
        conn = sqlite3.connect('userinfo.db')
        cursor = conn.cursor()
        return conn, cursor

    # Commit pending changes to database and safely close the connection
    def commit_n_close(self, conn):
        conn.commit()
        conn.close() 

    # Create users table with id, username, and password columns if table doesn't exist
    def create_db(self):
        conn, cursor = self.connect()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                password TEXT NOT NULL
                )
        ''')
        self.commit_n_close(conn)

    # Insert new user credentials into the users table
    def insert_user(self, username, password):
        conn, cursor = self.connect()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        self.commit_n_close(conn)

    # Check if a user with the given username already exists in the database
    def user_exists(self, username):
        conn, cursor = self.connect()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username, ))
        result = cursor.fetchone()
        self.commit_n_close(conn)
        return result is not None

    # Retrieve the password for a given username from the database
    def get_password(self, username):
        conn, cursor = self.connect()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username, ))
        password = cursor.fetchone()
        self.commit_n_close(conn)
        return password[0] if password else None
