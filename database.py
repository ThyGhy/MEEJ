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
        SELECT * FROM AUTHENTICATION WHERE CSN_Email = ?
    """, (email,)).fetchone()
    conn.close()
    return user

def get_student_details(auth_id):
    """Get student details including authentication info."""
    conn = get_db_connection()
    student = conn.execute("""
        SELECT 
            s.*,
            a.CSN_Email as Email,
            a.Role
        FROM STUDENTS s
        JOIN AUTHENTICATION a ON s.Auth_ID = a.Auth_ID
        WHERE a.Auth_ID = ?
    """, (auth_id,)).fetchone()
    conn.close()
    return student

def get_faculty_details(faculty_id):
    """Get faculty details including authentication info."""
    conn = get_db_connection()
    try:
        faculty = conn.execute("""
            SELECT 
                f.*,
                a.CSN_Email as Email,
                a.Role
            FROM FACULTY f
            JOIN AUTHENTICATION a ON f.Auth_ID = a.Auth_ID
            WHERE f.FacultyID = ?
        """, (faculty_id,)).fetchone()
        return faculty
    except Exception as e:
        print(f"Error getting faculty details: {str(e)}")  # Debug log
        return None
    finally:
        conn.close()

def add_student(firstname, lastname, email, nsheid):
    """Add a new student with authentication account."""
    conn = get_db_connection()
    try:
        # First create authentication entry
        conn.execute(
            "INSERT INTO AUTHENTICATION (CSN_Email, Password, Role) VALUES (?, ?, ?)",
            (email, nsheid, 'Student')  # For students, NSHE ID is the password
        )
        auth_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        
        # Then create student entry
        conn.execute(
            """INSERT INTO STUDENTS 
               (Auth_ID, FirstName, LastName, Email, NSHEID) 
               VALUES (?, ?, ?, ?, ?)""",
            (auth_id, firstname, lastname, email, nsheid)
        )
        conn.commit()
        return True, "Student added successfully"
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error: {str(e)}")  # Debug logging
        conn.rollback()
        if "UNIQUE constraint failed: AUTHENTICATION.CSN_Email" in str(e):
            return False, "Error: Email already exists"
        elif "UNIQUE constraint failed: STUDENTS.NSHEID" in str(e):
            return False, "Error: NSHE ID already exists"
        elif "UNIQUE constraint failed: STUDENTS.Email" in str(e):
            return False, "Error: Email already exists"
        return False, f"Database error: {str(e)}"
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug logging
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def add_faculty(firstname, lastname, email, password):
    """Add a new faculty member with authentication account."""
    print(f"Starting faculty registration process for {email}")  # Debug log
    conn = get_db_connection()
    try:
        # First create authentication entry
        print("Creating authentication entry")  # Debug log
        conn.execute(
            "INSERT INTO AUTHENTICATION (CSN_Email, Password, Role) VALUES (?, ?, ?)",
            (email, password, 'Faculty')
        )
        auth_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        print(f"Created authentication entry with ID: {auth_id}")  # Debug log
        
        # Then create faculty entry - note that Salary is optional in schema
        print("Creating faculty entry")  # Debug log
        conn.execute(
            """INSERT INTO FACULTY 
               (Auth_ID, FirstName, LastName, Email) 
               VALUES (?, ?, ?, ?)""",
            (auth_id, firstname, lastname, email)
        )
        conn.commit()
        print("Faculty registration completed successfully")  # Debug log
        return True, "Faculty added successfully"
    except sqlite3.IntegrityError as e:
        print(f"Database integrity error: {str(e)}")  # Debug log
        conn.rollback()
        if "UNIQUE constraint failed: AUTHENTICATION.CSN_Email" in str(e):
            return False, "Error: Email already exists"
        elif "UNIQUE constraint failed: FACULTY.Email" in str(e):
            return False, "Error: Faculty email already exists"
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
        # Verify email exists in Authentication table
        user = conn.execute("SELECT 1 FROM AUTHENTICATION WHERE CSN_Email = ?", (email,)).fetchone()
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
            "UPDATE AUTHENTICATION SET Password = ? WHERE CSN_Email = ?",
            (new_password, email)
        )
        conn.commit()
        return True, "Password updated successfully"
    except sqlite3.Error as e:
        return False, f"Error updating password: {str(e)}"
    finally:
        conn.close()

def get_registered_exam_count(student_id):
    """Get the number of exams a student is registered for."""
    conn = get_db_connection()
    try:
        count = conn.execute("""
            SELECT COUNT(*) as count
            FROM EXAM_REGISTRATIONS
            WHERE StudentID = ?
        """, (student_id,)).fetchone()
        return count['count']
    finally:
        conn.close()

def search_exams(subject=None, course_num=None, campus=None, days=None, min_date=None, max_date=None, student_id=None):
    """Search for available exams based on criteria."""
    # Day mapping for both 3-letter abbreviations and full names
    day_mapping = {
        'Sun': '0', 'Sunday': '0',
        'Mon': '1', 'Monday': '1',
        'Tue': '2', 'Tuesday': '2',
        'Wed': '3', 'Wednesday': '3',
        'Thu': '4', 'Thursday': '4',
        'Fri': '5', 'Friday': '5',
        'Sat': '6', 'Saturday': '6',
        # Also support direct numeric values
        '0': '0', '1': '1', '2': '2', '3': '3', '4': '4', '5': '5', '6': '6'
    }

    conn = get_db_connection()
    try:
        query = """
            SELECT DISTINCT
                e.*,
                l.CampusName,
                l.Building,
                l.RoomNumber,
                f.FirstName || ' ' || f.LastName as ProctorName,
                strftime('%w', date(e.ExamDate)) as DayOfWeek,
                CASE WHEN er.StudentID IS NOT NULL THEN 1 ELSE 0 END as IsRegistered
            FROM EXAMS e
            JOIN LOCATION l ON e.LocationID = l.LocationID
            JOIN FACULTY f ON e.ProctorID = f.FacultyID
            LEFT JOIN EXAM_REGISTRATIONS er ON e.Exam_ID = er.Exam_ID AND er.StudentID = ?
            WHERE 1=1
            AND (er.StudentID IS NULL)  -- Only show exams the student is not registered for
            AND (e.CurrentEnrollment < e.ExamCapacity)  -- Only show exams that aren't full
        """
        
        params = [student_id] if student_id else [None]
            
        if subject and subject.strip():
            # Use exact match for subject by looking at everything before the space
            query += " AND e.Class LIKE ? || ' %'"  # This will match "CS 135" but not "CSCO 135"
            params.append(subject)
            
        if course_num:
            query += " AND e.Class LIKE '% ' || ? || '%'"  # This will match the course number part
            params.append(course_num)
            
        if campus:
            query += " AND l.CampusName = ?"
            params.append(campus)
            
        if min_date:
            query += " AND date(e.ExamDate) >= date(?)"
            params.append(min_date)
            
        if max_date:
            query += " AND date(e.ExamDate) <= date(?)"
            params.append(max_date)
            
        if days:
            day_conditions = []
            for day in days:
                # Convert day to SQLite format using mapping
                sqlite_day = day_mapping.get(day)
                if sqlite_day is not None:
                    day_conditions.append(f"strftime('%w', date(e.ExamDate)) = '{sqlite_day}'")
            if day_conditions:
                query += " AND (" + " OR ".join(day_conditions) + ")"
            
        # Sort by ExamDate and ExamTime
        query += " ORDER BY e.ExamDate, e.ExamTime"
        
        exams = conn.execute(query, params).fetchall()
        return exams
    finally:
        conn.close()

def register_for_exam(student_id, exam_id):
    """Register a student for an exam."""
    conn = get_db_connection()
    try:
        # Check if student is already registered for this exam
        existing = conn.execute(
            "SELECT 1 FROM EXAM_REGISTRATIONS WHERE StudentID = ? AND Exam_ID = ?",
            (student_id, exam_id)
        ).fetchone()
        
        if existing:
            return False, "You are already registered for this exam"
            
        # Check if exam is full
        exam = conn.execute(
            "SELECT ExamCapacity, CurrentEnrollment FROM EXAMS WHERE Exam_ID = ?",
            (exam_id,)
        ).fetchone()
        
        if not exam:
            return False, "Exam not found"
            
        if exam['CurrentEnrollment'] >= exam['ExamCapacity']:
            return False, "This exam is full"
            
        # Register the student (trigger will handle CurrentEnrollment update)
        conn.execute(
            "INSERT INTO EXAM_REGISTRATIONS (StudentID, Exam_ID) VALUES (?, ?)",
            (student_id, exam_id)
        )
        
        conn.commit()
        return True, "Successfully registered for exam"
        
    except sqlite3.IntegrityError as e:
        conn.rollback()
        return False, str(e)
    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def get_student_exams(student_id):
    """Get all exams a student is registered for."""
    conn = get_db_connection()
    try:
        exams = conn.execute("""
            SELECT 
                e.*,
                l.CampusName,
                l.Building,
                l.RoomNumber,
                f.FirstName || ' ' || f.LastName as ProctorName,
                er.RegistrationDate
            FROM EXAM_REGISTRATIONS er
            JOIN EXAMS e ON er.Exam_ID = e.Exam_ID
            JOIN LOCATION l ON e.LocationID = l.LocationID
            JOIN FACULTY f ON e.ProctorID = f.FacultyID
            WHERE er.StudentID = ?
            ORDER BY e.ExamDate, e.ExamTime
        """, (student_id,)).fetchall()
        return exams
    finally:
        conn.close()

def cancel_exam_registration(student_id, exam_id):
    """Cancel a student's exam registration."""
    conn = get_db_connection()
    try:
        # First check if the registration exists
        registration = conn.execute(
            "SELECT 1 FROM EXAM_REGISTRATIONS WHERE StudentID = ? AND Exam_ID = ?",
            (student_id, exam_id)
        ).fetchone()
        
        if not registration:
            return False, "Registration not found"
            
        # Get current enrollment count
        current = conn.execute(
            "SELECT CurrentEnrollment FROM EXAMS WHERE Exam_ID = ?",
            (exam_id,)
        ).fetchone()
        
        if current and current['CurrentEnrollment'] > 0:
            # Delete the registration
            conn.execute(
                "DELETE FROM EXAM_REGISTRATIONS WHERE StudentID = ? AND Exam_ID = ?",
                (student_id, exam_id)
            )
            
            # Decrement the CurrentEnrollment count, ensuring it doesn't go below 0
            conn.execute(
                "UPDATE EXAMS SET CurrentEnrollment = MAX(0, CurrentEnrollment - 1) WHERE Exam_ID = ?",
                (exam_id,)
            )
            
            conn.commit()
            return True, "Registration cancelled successfully"
        else:
            conn.rollback()
            return False, "Error: Invalid enrollment count"
    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def get_all_exams_debug():
    """Debug function to list all exams in database."""
    conn = get_db_connection()
    try:
        exams = conn.execute("""
            SELECT 
                e.*,
                l.CampusName,
                l.Building,
                l.RoomNumber,
                f.FirstName || ' ' || f.LastName as ProctorName
            FROM EXAMS e
            JOIN LOCATION l ON e.LocationID = l.LocationID
            JOIN FACULTY f ON e.ProctorID = f.FacultyID
            ORDER BY e.ExamDate, e.ExamTime
        """).fetchall()
        
        print("\nDEBUG - All exams in database:")
        print(f"Total exams found: {len(exams)}")
        for exam in exams:
            print(f"Exam: {exam['Class']}, Date: {exam['ExamDate']}, Time: {exam['ExamTime']}, Campus: {exam['CampusName']}")
        return exams
    finally:
        conn.close()

def debug_fill_exam(exam_id, num_registrations):
    """Debug function to simulate multiple registrations for an exam.
    Returns the current enrollment count and capacity."""
    conn = get_db_connection()
    try:
        # First get the exam's current state
        exam = conn.execute("""
            SELECT Exam_ID, ExamCapacity, CurrentEnrollment, Class 
            FROM EXAMS WHERE Exam_ID = ?
        """, (exam_id,)).fetchone()
        
        if not exam:
            return False, f"Exam ID {exam_id} not found"
        
        # Convert and validate num_registrations
        try:
            num_registrations = int(num_registrations)
            if num_registrations <= 0:
                return False, f"Number of registrations must be positive"
        except ValueError:
            return False, f"Invalid number of registrations requested"
            
        # Calculate how many spots we can actually fill
        available_spots = exam['ExamCapacity'] - exam['CurrentEnrollment']
        spots_to_fill = min(available_spots, num_registrations)
        
        if spots_to_fill <= 0:
            return False, f"Exam {exam['Class']} (ID: {exam_id}) is already full or cannot add more. Capacity: {exam['ExamCapacity']}, Current: {exam['CurrentEnrollment']}"
        
        # Get the starting enrollment count
        starting_count = exam['CurrentEnrollment']
        target_count = starting_count + num_registrations
        
        # Add registrations one by one
        spots_filled = 0
        current_count = starting_count
        
        while spots_filled < num_registrations and current_count < exam['ExamCapacity']:
            try:
                # Generate unique dummy student ID
                dummy_student_id = 900000000 + current_count
                
                # Add the registration
                conn.execute(
                    "INSERT INTO EXAM_REGISTRATIONS (StudentID, Exam_ID) VALUES (?, ?)",
                    (dummy_student_id, exam_id)
                )
                
                spots_filled += 1
                current_count += 1
                
                # Update enrollment count for this registration
                conn.execute(
                    "UPDATE EXAMS SET CurrentEnrollment = ? WHERE Exam_ID = ?",
                    (current_count, exam_id)
                )
                conn.commit()
                
            except sqlite3.IntegrityError as e:
                print(f"Skipping registration due to: {str(e)}")
                conn.rollback()
                continue
                
        # Get final exam state
        final_state = conn.execute(
            "SELECT ExamCapacity, CurrentEnrollment FROM EXAMS WHERE Exam_ID = ?",
            (exam_id,)
        ).fetchone()
        
        return True, f"Added exactly {spots_filled} registrations to {exam['Class']} (ID: {exam_id}). Previous: {starting_count}, Now: {final_state['CurrentEnrollment']}/{final_state['ExamCapacity']}"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def debug_clear_exam_registrations(exam_id):
    """Debug function to clear all dummy registrations from an exam."""
    conn = get_db_connection()
    try:
        # Remove all registrations with dummy student IDs
        conn.execute("""
            DELETE FROM EXAM_REGISTRATIONS 
            WHERE Exam_ID = ? AND StudentID >= 900000000
        """, (exam_id,))
        
        # Reset the enrollment count to actual registrations
        actual_count = conn.execute("""
            SELECT COUNT(*) as count 
            FROM EXAM_REGISTRATIONS 
            WHERE Exam_ID = ?
        """, (exam_id,)).fetchone()['count']
        
        conn.execute(
            "UPDATE EXAMS SET CurrentEnrollment = ? WHERE Exam_ID = ?",
            (actual_count, exam_id)
        )
        
        conn.commit()
        return True, f"Cleared dummy registrations. Current enrollment: {actual_count}"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def debug_subtract_registrations(exam_id, num_to_remove):
    """Debug function to remove a specific number of dummy registrations from an exam."""
    conn = get_db_connection()
    try:
        # First get the exam's current state
        exam = conn.execute("""
            SELECT Exam_ID, ExamCapacity, CurrentEnrollment, Class 
            FROM EXAMS WHERE Exam_ID = ?
        """, (exam_id,)).fetchone()
        
        if not exam:
            return False, f"Exam ID {exam_id} not found"
            
        # Convert and validate num_to_remove
        try:
            num_to_remove = int(num_to_remove)
            if num_to_remove <= 0:
                return False, f"Number of registrations to remove must be positive"
        except ValueError:
            return False, f"Invalid number of registrations to remove"
            
        # Get starting state
        starting_count = exam['CurrentEnrollment']
        
        # Get count of dummy registrations
        dummy_count = conn.execute("""
            SELECT COUNT(*) as count 
            FROM EXAM_REGISTRATIONS 
            WHERE Exam_ID = ? AND StudentID >= 900000000
        """, (exam_id,)).fetchone()['count']
        
        if dummy_count == 0:
            return False, f"No dummy registrations to remove from {exam['Class']} (ID: {exam_id})"
            
        # Calculate how many we can actually remove
        removable = min(dummy_count, num_to_remove)
        
        # Get the dummy registrations to remove
        dummy_students = conn.execute("""
            SELECT StudentID 
            FROM EXAM_REGISTRATIONS 
            WHERE Exam_ID = ? AND StudentID >= 900000000 
            ORDER BY StudentID DESC
            LIMIT ?
        """, (exam_id, removable)).fetchall()
        
        # Remove registrations one by one
        removed = 0
        current_count = starting_count
        
        for student in dummy_students:
            if removed >= num_to_remove:
                break
                
            try:
                # Remove the registration
                conn.execute("""
                    DELETE FROM EXAM_REGISTRATIONS 
                    WHERE Exam_ID = ? AND StudentID = ?
                """, (exam_id, student['StudentID']))
                
                removed += 1
                current_count -= 1
                
                # Update enrollment count
                conn.execute("""
                    UPDATE EXAMS 
                    SET CurrentEnrollment = ? 
                    WHERE Exam_ID = ?
                """, (current_count, exam_id))
                
                conn.commit()
                
            except Exception as e:
                print(f"Error removing registration: {str(e)}")
                conn.rollback()
                continue
        
        # Get final state
        final_state = conn.execute("""
            SELECT ExamCapacity, CurrentEnrollment 
            FROM EXAMS WHERE Exam_ID = ?
        """, (exam_id,)).fetchone()
        
        return True, f"Removed exactly {removed} dummy registrations from {exam['Class']} (ID: {exam_id}). Previous: {starting_count}, Now: {final_state['CurrentEnrollment']}/{final_state['ExamCapacity']}"
        
    except Exception as e:
        conn.rollback()
        return False, f"Error: {str(e)}"
    finally:
        conn.close()

def debug_clear_all_sample_data():
    """Debug function to clear all exam registrations (both sample and student) and reset enrollment counts."""
    conn = get_db_connection()
    try:
        # Get counts before deletion for reporting
        sample_count = conn.execute("""
            SELECT COUNT(*) as count 
            FROM EXAM_REGISTRATIONS 
            WHERE StudentID >= 900000000
        """).fetchone()['count']
        
        student_count = conn.execute("""
            SELECT COUNT(*) as count 
            FROM EXAM_REGISTRATIONS 
            WHERE StudentID < 900000000
        """).fetchone()['count']
        
        # Remove all registrations (both dummy and real student registrations)
        conn.execute("DELETE FROM EXAM_REGISTRATIONS")
        
        # Reset all exam enrollment counts to zero
        conn.execute("UPDATE EXAMS SET CurrentEnrollment = 0")
        
        conn.commit()
        return True, f"Successfully cleared {sample_count} sample registrations and {student_count} student registrations. All exam enrollment counts reset to 0."
        
    except Exception as e:
        conn.rollback()
        return False, f"Error clearing data: {str(e)}"
    finally:
        conn.close()

def get_faculty_exams(faculty_id):
    """Get all exams where the faculty member is the proctor."""
    conn = get_db_connection()
    try:
        exams = conn.execute("""
            SELECT 
                e.*,
                l.CampusName,
                l.Building,
                l.RoomNumber,
                COUNT(DISTINCT er.StudentID) as RegisteredCount
            FROM EXAMS e
            JOIN LOCATION l ON e.LocationID = l.LocationID
            LEFT JOIN EXAM_REGISTRATIONS er ON e.Exam_ID = er.Exam_ID
            WHERE e.ProctorID = ?
            GROUP BY e.Exam_ID, e.LocationID, e.Exam_Name, e.ExamDate, e.ExamTime,
                     e.ProctorID, e.ExamCapacity, e.CurrentEnrollment, e.Class,
                     l.CampusName, l.Building, l.RoomNumber
            ORDER BY e.ExamDate DESC, e.ExamTime DESC
        """, (faculty_id,)).fetchall()
        return exams
    finally:
        conn.close()

def get_exam_details(exam_id):
    """Get detailed exam information including registered students."""
    conn = get_db_connection()
    try:
        # Get exam details
        exam = conn.execute("""
            SELECT 
                e.*,
                l.CampusName,
                l.Building,
                l.RoomNumber,
                f.FirstName || ' ' || f.LastName as ProctorName
            FROM EXAMS e
            JOIN LOCATION l ON e.LocationID = l.LocationID
            JOIN FACULTY f ON e.ProctorID = f.FacultyID
            WHERE e.Exam_ID = ?
        """, (exam_id,)).fetchone()
        
        if not exam:
            return None, []
            
        # Get registered students
        students = conn.execute("""
            SELECT 
                s.FirstName,
                s.LastName,
                s.Email,
                s.NSHEID,
                er.RegistrationDate
            FROM EXAM_REGISTRATIONS er
            JOIN STUDENTS s ON er.StudentID = s.StudentID
            WHERE er.Exam_ID = ?
            ORDER BY s.LastName, s.FirstName
        """, (exam_id,)).fetchall()
        
        return exam, students
    finally:
        conn.close()

