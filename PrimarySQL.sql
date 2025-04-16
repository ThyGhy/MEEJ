BEGIN TRANSACTION;

-- Drop existing tables if they exist
DROP TABLE IF EXISTS EXAM_REGISTRATIONS;
DROP TABLE IF EXISTS RESERVATIONS;
DROP TABLE IF EXISTS LOCATION;
DROP TABLE IF EXISTS FACULTY;
DROP TABLE IF EXISTS STUDENTS;
DROP TABLE IF EXISTS AUTHENTICATION;
DROP TABLE IF EXISTS PASSWORD_TOKENS;

-- Authentication table for login management
CREATE TABLE IF NOT EXISTS AUTHENTICATION (
    UserID INTEGER PRIMARY KEY AUTOINCREMENT,
    Email TEXT NOT NULL UNIQUE,
    Password TEXT NOT NULL,
    Role TEXT NOT NULL CHECK (Role IN ('Student', 'Faculty')),
    CreatedAt DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Students table with personal information
CREATE TABLE IF NOT EXISTS STUDENTS (
    StudentID INTEGER PRIMARY KEY,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    NSHEID TEXT NOT NULL UNIQUE,
    RegistrationDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (StudentID) REFERENCES AUTHENTICATION(UserID)
);

-- Faculty table with personal information
CREATE TABLE IF NOT EXISTS FACULTY (
    FacultyID INTEGER PRIMARY KEY,
    FirstName TEXT NOT NULL,
    LastName TEXT NOT NULL,
    Department TEXT,
    FOREIGN KEY (FacultyID) REFERENCES AUTHENTICATION(UserID)
);

-- Location table for exam locations
CREATE TABLE IF NOT EXISTS LOCATION (
    LocationID INTEGER PRIMARY KEY AUTOINCREMENT,
    CampusName TEXT NOT NULL,
    Building TEXT NOT NULL,
    RoomNumber TEXT NOT NULL,
    UNIQUE(CampusName, Building, RoomNumber)
);

-- Reservations table for exam scheduling
CREATE TABLE IF NOT EXISTS RESERVATIONS (
    ReservationID INTEGER PRIMARY KEY AUTOINCREMENT,
    LocationID INTEGER NOT NULL,
    ExamDate DATE NOT NULL,
    ExamTime TIME NOT NULL,
    ProctorID INTEGER NOT NULL,
    ExamCapacity INTEGER DEFAULT 20 CHECK (ExamCapacity <= 20),
    CurrentEnrollment INTEGER DEFAULT 0 CHECK (CurrentEnrollment <= ExamCapacity),
    Class TEXT NOT NULL,
    FOREIGN KEY (LocationID) REFERENCES LOCATION(LocationID),
    FOREIGN KEY (ProctorID) REFERENCES FACULTY(FacultyID)
);

-- Junction table for student exam registrations
CREATE TABLE IF NOT EXISTS EXAM_REGISTRATIONS (
    RegistrationID INTEGER PRIMARY KEY AUTOINCREMENT,
    StudentID INTEGER NOT NULL,
    ReservationID INTEGER NOT NULL,
    RegistrationDate DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (StudentID) REFERENCES STUDENTS(StudentID),
    FOREIGN KEY (ReservationID) REFERENCES RESERVATIONS(ReservationID),
    UNIQUE(StudentID, ReservationID)
);

-- Password reset token management
CREATE TABLE IF NOT EXISTS PASSWORD_TOKENS (
    TokenID INTEGER PRIMARY KEY AUTOINCREMENT,
    Email TEXT NOT NULL,
    Token TEXT NOT NULL UNIQUE,
    CreatedAt TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ExpiresAt TIMESTAMP NOT NULL DEFAULT (DATETIME(CURRENT_TIMESTAMP, '+1 hour')),
    Used INTEGER DEFAULT 0 CHECK (Used IN (0, 1)),
    FOREIGN KEY (Email) REFERENCES AUTHENTICATION(Email)
);

-- Trigger to update CurrentEnrollment when a student registers
CREATE TRIGGER IF NOT EXISTS after_registration_insert
AFTER INSERT ON EXAM_REGISTRATIONS
BEGIN
    UPDATE RESERVATIONS 
    SET CurrentEnrollment = CurrentEnrollment + 1
    WHERE ReservationID = NEW.ReservationID;
END;

-- Trigger to update CurrentEnrollment when a student cancels registration
CREATE TRIGGER IF NOT EXISTS after_registration_delete
AFTER DELETE ON EXAM_REGISTRATIONS
BEGIN
    UPDATE RESERVATIONS 
    SET CurrentEnrollment = CurrentEnrollment - 1
    WHERE ReservationID = OLD.ReservationID;
END;

-- Trigger to enforce 3 exam registration limit per student
CREATE TRIGGER IF NOT EXISTS check_exam_limit
BEFORE INSERT ON EXAM_REGISTRATIONS
BEGIN
    SELECT CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM EXAM_REGISTRATIONS 
            WHERE StudentID = NEW.StudentID
        ) >= 3 
        THEN RAISE(ABORT, 'Students are limited to 3 exam registrations.')
    END;
END;

COMMIT;