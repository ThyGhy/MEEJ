import sqlite3
import uuid
import datetime

DATABASE = 'ExamRegistration.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def get_user_by_email(email):
    """Get user from Authentication table."""
    conn = get_db_connection()
    user = conn.execute("""
        SELECT * FROM AUTHENTICATION WHERE Email = ?
    """, (email,)).fetchone()
    conn.close()
    return user

def get_student_details(student_id):
    """Get student details including authentication info."""
    conn = get_db_connection()
    student = conn.execute("""
        SELECT 
            s.*,
            a.Email,
            a.Role
        FROM STUDENTS s
        JOIN AUTHENTICATION a ON s.StudentID = a.UserID
        WHERE s.StudentID = ?
    """, (student_id,)).fetchone()
    conn.close()
    return student

def get_faculty_details(faculty_id):
    """Get faculty details including authentication info."""
    conn = get_db_connection()
    try:
        faculty = conn.execute("""
            SELECT 
                f.*,
                a.Email,
                a.Role
            FROM FACULTY f
            JOIN AUTHENTICATION a ON f.FacultyID = a.UserID
            WHERE f.FacultyID = ?
        """, (faculty_id,)).fetchone()
        return faculty
    except Exception as e:
        print(f"Error getting faculty details: {str(e)}")  # Debug log
        return None
    finally:
        conn.close()

def add_student(firstname, lastname, email, password):
    """Add a new student with authentication."""
    conn = get_db_connection()
    try:
        # First create authentication entry
        conn.execute(
            "INSERT INTO AUTHENTICATION (Email, Password, Role) VALUES (?, ?, ?)",
            (email, password, 'Student')
        )
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Then create student entry
        conn.execute(
            "INSERT INTO STUDENTS (StudentID, FirstName, LastName) VALUES (?, ?, ?)",
            (user_id, firstname, lastname)
        )
        conn.commit()
        return True, "Student added successfully"
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error: {str(e)}")  # Debug logging
        conn.rollback()
        if "UNIQUE constraint failed: AUTHENTICATION.Email" in str(e):
            return False, "Error: Email already exists"
        return False, f"Database error: {str(e)}"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug logging
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def add_faculty(firstname, lastname, email, password):
    """Add a new faculty member with authentication."""
    print(f"Starting faculty registration process for {email}")  # Debug log
    conn = get_db_connection()
    try:
        # First create authentication entry
        print("Creating authentication entry")  # Debug log
        conn.execute(
            "INSERT INTO AUTHENTICATION (Email, Password, Role) VALUES (?, ?, ?)",
            (email, password, 'Faculty')
        )
        user_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        print(f"Created authentication entry with ID: {user_id}")  # Debug log
        
        # Then create faculty entry
        print("Creating faculty entry")  # Debug log
        conn.execute(
            "INSERT INTO FACULTY (FacultyID, FirstName, LastName) VALUES (?, ?, ?)",
            (user_id, firstname, lastname)
        )
        conn.commit()
        print("Faculty registration completed successfully")  # Debug log
        return True, "Faculty added successfully"
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error: {str(e)}")  # Debug log
        conn.rollback()
        if "UNIQUE constraint failed: AUTHENTICATION.Email" in str(e):
            return False, "Error: Email already exists"
        return False, f"Database error: {str(e)}"
    except Exception as e:
        print(f"Unexpected error during faculty registration: {str(e)}")  # Debug log
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def create_password_reset_token(email):
    """Create a password reset token that expires in 1 hour."""
    token = str(uuid.uuid4())
    conn = get_db_connection()
    try:
        # Verify email exists in Authentication
        user = conn.execute("SELECT 1 FROM AUTHENTICATION WHERE Email = ?", (email,)).fetchone()
        if not user:
            return None
            
        # Delete any existing tokens for this email
        conn.execute("DELETE FROM PASSWORD_TOKENS WHERE Email = ?", (email,))
        
        # Create new token (ExpiresAt is handled by default value in schema)
        conn.execute(
            "INSERT INTO PASSWORD_TOKENS (Email, Token) VALUES (?, ?)", 
            (email, token)
        )
        conn.commit()
        return token
    except sqlite3.IntegrityError:
        conn.rollback()
        return None
    finally:
        conn.close()

def get_email_by_token(token):
    """Get email by token if it hasn't expired and hasn't been used."""
    conn = get_db_connection()
    result = conn.execute("""
        SELECT Email, CreatedAt, ExpiresAt 
        FROM PASSWORD_TOKENS 
        WHERE Token = ? 
        AND Used = 0 
        AND ExpiresAt > CURRENT_TIMESTAMP
    """, (token,)).fetchone()
    conn.close()
    
    if result:
        return {
            'email': result['Email'],
            'created_at': result['CreatedAt'],
            'expires_at': result['ExpiresAt']
        }
    return None

def mark_token_used(token):
    """Mark a token as used after successful password reset."""
    conn = get_db_connection()
    conn.execute("UPDATE PASSWORD_TOKENS SET Used = 1 WHERE Token = ?", (token,))
    conn.commit()
    conn.close()

def update_password(email, new_password):
    """Update user's password in Authentication table."""
    conn = get_db_connection()
    try:
        conn.execute(
            "UPDATE AUTHENTICATION SET Password = ? WHERE Email = ?",
            (new_password, email)
        )
        conn.commit()
        return True, "Password updated successfully"
    except sqlite3.Error as e:
        return False, f"Error updating password: {str(e)}"
    finally:
        conn.close()

def get_available_exam_slots():
    """Get all available exam slots with location and proctor details."""
    conn = get_db_connection()
    slots = conn.execute("""
        SELECT 
            R.ReservationID,
            R.ExamDate,
            R.ExamTime,
            R.Class,
            R.ExamCapacity,
            R.CurrentEnrollment,
            L.CampusName,
            L.Building,
            L.RoomNumber,
            F.FirstName || ' ' || F.LastName as ProctorName
        FROM RESERVATIONS R
        JOIN LOCATION L ON R.LocationID = L.LocationID
        JOIN FACULTY F ON R.ProctorID = F.FacultyID
        WHERE R.CurrentEnrollment < R.ExamCapacity
        ORDER BY R.ExamDate, R.ExamTime
    """).fetchall()
    conn.close()
    return slots

def register_for_exam(student_id, reservation_id):
    """Register a student for an exam."""
    conn = get_db_connection()
    try:
        # Check if student exists
        student = conn.execute("SELECT 1 FROM STUDENTS WHERE StudentID = ?", (student_id,)).fetchone()
        if not student:
            return False, "Student not found"
            
        # Check if reservation exists and has space
        reservation = conn.execute("""
            SELECT ExamCapacity, CurrentEnrollment 
            FROM RESERVATIONS 
            WHERE ReservationID = ?
        """, (reservation_id,)).fetchone()
        
        if not reservation:
            return False, "Exam reservation not found"
            
        if reservation['CurrentEnrollment'] >= reservation['ExamCapacity']:
            return False, "This exam session is full"
            
        # Try to register (triggers will handle enrollment count and limit checks)
        conn.execute(
            "INSERT INTO EXAM_REGISTRATIONS (StudentID, ReservationID) VALUES (?, ?)",
            (student_id, reservation_id)
        )
        conn.commit()
        return True, "Successfully registered for exam"
        
    except sqlite3.IntegrityError as e:
        if "Students are limited to 3 exam registrations" in str(e):
            return False, "You have reached the maximum limit of 3 exam registrations"
        elif "UNIQUE constraint failed" in str(e):
            return False, "You are already registered for this exam"
        return False, f"Registration error: {str(e)}"
    finally:
        conn.close()

