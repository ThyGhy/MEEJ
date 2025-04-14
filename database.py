import sqlite3
import uuid
import datetime
import os

DATABASE = 'ExamRegistration.db'

def init_db():
    """Initialize the database and create tables if they don't exist."""
    conn = get_db_connection()
    
    # Read the SQL file
    with open('PrimarySQL.sql', 'r') as f:
        sql_script = f.read()
    
    # Execute the SQL script
    conn.executescript(sql_script)
    conn.commit()
    conn.close()
    print("Database initialized successfully")

def get_db_connection():
    """Get a database connection. Creates the database file if it doesn't exist."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_student_by_email(email):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
    conn.close()
    return student

def add_student(name, firstname, lastname, email, password):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO students (name, firstname, lastname, email, password) VALUES (?, ?, ?, ?, ?)",
        (name, firstname, lastname, email, password)
    )
    conn.commit()
    conn.close()

def get_faculty_by_email(email):
    conn = get_db_connection()
    faculty = conn.execute("SELECT * FROM faculty WHERE email = ?", (email,)).fetchone()
    conn.close()
    return faculty

def add_faculty(name, firstname, lastname, email, password):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO faculty (name, firstname, lastname, email, password) VALUES (?, ?, ?, ?, ?)",
        (name, firstname, lastname, email, password)
    )
    conn.commit()
    conn.close()
    
def fetch_exams():
    """Retrieve all exam records."""
    conn = get_db_connection()
    exams = conn.execute("SELECT * FROM exams").fetchall()
    conn.close()
    return exams

def create_password_reset_token(email):
    """Create a password reset token that expires in 1 hour."""
    token = str(uuid.uuid4())
    created_at = datetime.datetime.utcnow()
    conn = get_db_connection()
    
    # Delete any existing tokens for this email
    conn.execute("DELETE FROM PASSWORD_TOKENS WHERE email = ?", (email,))
    
    # Create new token
    conn.execute("INSERT INTO PASSWORD_TOKENS (email, token, created_at) VALUES (?, ?, ?)", 
                (email, token, created_at))
    conn.commit()
    conn.close()
    return token

def get_email_by_token(token):
    """Get email by token if it hasn't expired (1 hour validity)."""
    conn = get_db_connection()
    one_hour_ago = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    
    result = conn.execute("""
        SELECT email, created_at 
        FROM PASSWORD_TOKENS 
        WHERE token = ? AND created_at > ?
    """, (token, one_hour_ago)).fetchone()
    
    conn.close()
    
    if result:
        return {'email': result['email'], 'created_at': result['created_at']}
    return None

def clear_password_token(email):
    """Clear the password reset token after successful reset."""
    conn = get_db_connection()
    conn.execute("DELETE FROM PASSWORD_TOKENS WHERE email = ?", (email,))
    conn.commit()
    conn.close()

def register_for_exam(user_id, exam_id):
    """Register a user for an exam, with basic duplicate and capacity check."""
    conn = get_db_connection()
    
    # Check for duplicate registration
    duplicate = conn.execute(
        "SELECT * FROM registrations WHERE user_id = ? AND exam_id = ?",
        (user_id, exam_id)
    ).fetchone()
    if duplicate:
        conn.close()
        return False, "Already registered for this exam."
    
    # Check exam capacity
    current_count = conn.execute(
        "SELECT COUNT(*) as count FROM registrations WHERE exam_id = ?",
        (exam_id,)
    ).fetchone()['count']
    
    exam = conn.execute(
        "SELECT capacity FROM exams WHERE exam_id = ?",
        (exam_id,)
    ).fetchone()
    
    if current_count >= exam['capacity']:
        conn.close()
        return False, "This exam session is full."
    
    # Insert registration record
    conn.execute(
        "INSERT INTO registrations (user_id, exam_id) VALUES (?, ?)",
        (user_id, exam_id)
    )
    conn.commit()
    conn.close()
    return True, "Registration successful."

