from flask import Flask, render_template, request, redirect, url_for, session
import database  # This is our custom module
import re
import subprocess
import datetime

app = Flask(__name__)
app.secret_key = "MEEJ"

# Initialize database when app starts
database.init_db()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()  # Normalize email
        password = request.form['password']
        print("Attempting login for:", email)
        
        # Check if the user is a student
        student = database.get_student_by_email(email)
        if student:
            student_dict = dict(student)
            if student_dict['password'] == password:
                session['user_id'] = student_dict.get('student_id', student_dict.get('id'))
                session['email'] = student_dict['email']
                session['name'] = student_dict['name']
                session['role'] = 'student'
                print("Student login successful; redirecting to student home.")
                return redirect(url_for('student_home'))
        
        # Check if the user is faculty
        faculty = database.get_faculty_by_email(email)
        if faculty:
            faculty_dict = dict(faculty)
            if faculty_dict['password'] == password:
                session['user_id'] = faculty_dict.get('faculty_id', faculty_dict.get('id'))
                session['email'] = faculty_dict['email']
                session['name'] = faculty_dict['name']
                session['role'] = 'faculty'
                print("Faculty login successful; redirecting to faculty home.")
                return redirect(url_for('faculty_home'))
        
        print("Invalid credentials.")
        return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html', success=request.args.get('success'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        firstname = request.form['firstname'].strip().title()
        lastname = request.form['lastname'].strip().title()
        name = f"{firstname} {lastname}"
        email = request.form['email'].strip().lower()
        password = request.form['password']

        student_match = re.match(r'^(\d{10})@student\.csn\.edu$', email)
        faculty_match = re.match(r'.+@(csn\.edu|faculty\.csn\.edu)$', email)

        if student_match:
            user_type = 'student'
            nshe_id = student_match.group(1)

            if password != nshe_id:
                error = "For student accounts, the password must match your 10-digit NSHE ID."
                return render_template('signup.html', error=error)

        elif faculty_match:
            user_type = 'faculty'
        else:
            error = "Invalid email format. Students must use a 10-digit NSHE ID followed by @student.csn.edu, and faculty must use a valid csn domain."
            return render_template('signup.html', error=error)

        # Prevent duplicate emails across both tables
        if database.get_student_by_email(email) or database.get_faculty_by_email(email):
            error = "Email already exists. Please log in or choose a different email."
            return render_template('signup.html', error=error)

        # Add and login user
        if user_type == 'student':
            database.add_student(name, firstname, lastname, email, password)
            user = database.get_student_by_email(email)
            session['user_id'] = user['student_id'] if 'student_id' in user.keys() else user['id']
            session['email'] = user['email']
            session['name'] = user['name']
            session['role'] = 'student'
            return redirect(url_for('student_home'))

        else:
            database.add_faculty(name, firstname, lastname, email, password)
            user = database.get_faculty_by_email(email)
            session['user_id'] = user['faculty_id'] if 'faculty_id' in user.keys() else user['id']
            session['email'] = user['email']
            session['name'] = user['name']
            session['role'] = 'faculty'
            return redirect(url_for('faculty_home'))

    return render_template('signup.html')



@app.route('/student_home')
def student_home():
    return render_template('student_home.html')

@app.route('/faculty_home')
def faculty_home():
    return render_template('faculty_home.html')

@app.route('/')
def index():
    return render_template('gocsn.html')

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()
        print(f"Processing forgot password request for email: {email}")
        
        # Check if email is a valid CSN email format
        student_match = re.match(r'^(\d{10})@student\.csn\.edu$', email)
        faculty_match = re.match(r'.+@(csn\.edu|faculty\.csn\.edu)$', email)
        
        if not (student_match or faculty_match):
            return render_template('forgot_password.html',
                error="Invalid Email Address")
        
        if student_match:
            print("Student email detected - reset not allowed")
            return render_template('forgot_password.html', 
                error="Students must use their NSHE ID as their password. Reset Not Allowed.")
        
        faculty = database.get_faculty_by_email(email)
        print(f"Faculty check result: {faculty is not None}")
        
        if faculty:
            try:
                # Generate reset token
                token = database.create_password_reset_token(email)
                print(f"Generated token: {token}")
                
                reset_link = url_for('reset_password', token=token, _external=True)
                print(f"Reset link generated: {reset_link}")
                
                # For now, let's show the link on the page instead of redirecting
                return render_template('forgot_password.html',
                    success=f"Follow This Link to Reset Your Password: <br><a href='{reset_link}' style='color: #00008B;'>Reset Password</a>")
            except Exception as e:
                print(f"Error generating reset token: {str(e)}")
                return render_template('forgot_password.html',
                    error="An error occurred while processing your request. Please try again.")
        
        # Don't reveal if the email exists or not for security
        print("Email not found or invalid")
        return render_template('forgot_password.html', 
            info="If a faculty account exists with this email, a password reset link will be sent.")
    
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    # Verify token and get associated email
    token_data = database.get_email_by_token(token)
    
    if not token_data:
        return render_template('error.html', 
            error="Invalid or expired password reset link. Please request a new password reset.")
    
    # Verify this is a faculty email
    email = token_data['email']
    faculty = database.get_faculty_by_email(email)
    if not faculty:
        return render_template('error.html', 
            error="This reset link is not valid for student accounts.")
    
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Validate password
        if new_password != confirm_password:
            return render_template('reset_password.html', 
                error="Passwords do not match.", token=token)
        
        # Update password and clear token
        conn = database.get_db_connection()
        conn.execute("UPDATE FACULTY SET password = ? WHERE email = ?", 
                    (new_password, email))
        conn.commit()
        conn.close()
        
        database.clear_password_token(email)
        
        return redirect(url_for('login', success="Password Reset"))
    
    return render_template('reset_password.html', token=token)



@app.route('/register_exam', methods=['GET', 'POST'])
def register_exam():
    if session.get('role') != 'student':
        return redirect(url_for('login'))

    return render_template('register_exam.html')


@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
    if session.get('role') != 'faculty':
        return redirect(url_for('login'))

    return render_template('create_exam.html')

@app.route('/registered_exams')
def registered_exams():
    if session.get('role') != 'student':
        return redirect(url_for('login'))
    
    # Get registered exams for the student (placeholder for now)
    registered_exams = []  # This will be replaced with actual database query later
    
    return render_template('registered_exams.html', registered_exams=registered_exams)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login', success="You have been logged out successfully."))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
