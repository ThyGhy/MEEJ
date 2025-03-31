from flask import Flask, render_template, request, redirect, url_for, session
import database  # This is our custom module
import re

app = Flask(__name__)
app.secret_key = "MEEJ"

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
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name'].strip()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        # Student emails: exactly 10 digits followed by @student.csn.edu
        student_regex = r'^\d{10}@student\.csn\.edu$'
        # Faculty emails: any characters followed by @csn.edu or @faculty.csn.edu
        faculty_regex = r'.+@(csn\.edu|faculty\.csn\.edu)$'

        if re.match(student_regex, email):
            user_type = 'student'
        elif re.match(faculty_regex, email):
            user_type = 'faculty'
        else:
            error = "Invalid email format. Students must use a 10-digit NSHE ID followed by @student.csn.edu, and faculty must use a valid csn domain."
            return render_template('signup.html', error=error)

        # Prevent duplicate emails across both tables
        if database.get_student_by_email(email) or database.get_faculty_by_email(email):
            error = "Email already exists. Please log in or choose a different email."
            return render_template('signup.html', error=error)

        # Insert into the proper table based on the user_type
        if user_type == 'student':
            database.add_student(name, email, password)
        else:
            database.add_faculty(name, email, password)
        
        return redirect(url_for('login'))
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

if __name__ == "__main__":
    app.run(debug=True)