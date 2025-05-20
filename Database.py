import sqlite3

"""
set up a class for initializing, accessing, and editing
an sqlite3 database for managing the credentials of 
the login interface of the program.
"""
class Database:
    # initializes the database upon creating an instance
    # of the database class 
    def __init__(self):
        self.create_db() 

    # connects to the sqlite3 database, returns the 
    # connection object and the cursor for executing 
    # further queries. this function must be called
    # every time before accessing and modifying the
    # database 
    def connect(self):
        conn = sqlite3.connect('userinfo.db')
        cursor = conn.cursor()
        return conn, cursor

    # commits changes to the database and closes the 
    # connection, ensuring changes are saved and that
    # the connection is safely closed each time 
    def commit_n_close(self, conn):
        conn.commit()
        conn.close() 

    # creates the database if it does not already 
    # exist. called when creating an instance of the 
    # database class 
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

    # inserts a new set of user credentials into
    # the users table. takes in the inputs username
    # and password to insert into the database
    def insert_user(self, username, password):
        conn, cursor = self.connect()
        cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
        self.commit_n_close(conn)

    # takes in the input username, then checks if 
    # a user in the database with the given username 
    # already exists in the database. if the user 
    # already exists, reutrn True. otherwise, False
    def user_exists(self, username):
        conn, cursor = self.connect()
        cursor.execute('SELECT id FROM users WHERE username = ?', (username, ))
        result = cursor.fetchone()
        self.commit_n_close(conn)
        return result is not None

    # takes in the input username, then returns 
    # the password for the given username. If the 
    # user does not exist, return None. otherwise, 
    # return the password
    def get_password(self, username):
        conn, cursor = self.connect()
        cursor.execute('SELECT password FROM users WHERE username = ?', (username, ))
        password = cursor.fetchone()
        self.commit_n_close(conn)
        return password[0] if password else None
