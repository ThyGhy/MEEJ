import sqlite3

DATABASE = 'ExamRegistration.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_student_by_email(email):
    conn = get_db_connection()
    student = conn.execute("SELECT * FROM students WHERE email = ?", (email,)).fetchone()
    conn.close()
    return student

def add_student(name, email, password):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO students (name, email, password) VALUES (?, ?, ?)",
        (name, email, password)
    )
    conn.commit()
    conn.close()

def get_faculty_by_email(email):
    conn = get_db_connection()
    faculty = conn.execute("SELECT * FROM faculty WHERE email = ?", (email,)).fetchone()
    conn.close()
    return faculty

def add_faculty(name, email, password):
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO faculty (name, email, password) VALUES (?, ?, ?)",
        (name, email, password)
    )
    conn.commit()
    conn.close()
    
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

