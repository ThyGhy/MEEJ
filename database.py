import sqlite3

DATABASE = 'ExamRegistration.db'

def get_db_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Allows you to access columns by name
    return conn

def get_user_by_email(email):
    """Retrieve a user record by email."""
    conn = get_db_connection()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user

def fetch_exams():
    """Retrieve all exam records."""
    conn = get_db_connection()
    exams = conn.execute("SELECT * FROM exams").fetchall()
    conn.close()
    return exams

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

def add_email(email, password):
    conn = get_db_connection()
    # Insert with a default role for testing, e.g., "tester"
    conn.execute(
        "INSERT INTO users (email, password, role) VALUES (?, ?, ?)",
        (email, password, "tester")
    )
    conn.commit()
    conn.close()

def fetch_emails():
    conn = get_db_connection()
    emails = conn.execute("SELECT email FROM users").fetchall()
    conn.close()
    return emails
