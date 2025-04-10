from flask import Flask, render_template, request, redirect, url_for, session
import database  # This is our custom module
import re
import subprocess
import datetime

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
        # need to figure out best way to reset password here. Maybe some form of email situation? idk
        return render_template('forgot_password.html', message="If this email exists, a reset link will be sent.")
    return render_template('forgot_password.html')

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



#This is to Make Sure the Website Stays Up To Date.
@app.route('/webhook', methods=['POST'])
def webhook():
    import datetime
    import subprocess
    import os

    print("[Webhook] Webhook was called at", datetime.datetime.now())  # Always shows in Docker logs

    try:
        log_path = "/app/webhook.log"
        script_path = "/mnt/StoragePool/Github/MEEJ/update.sh"

        with open(log_path, "a") as f:
            f.write(f"[{datetime.datetime.now()}] Webhook triggered.\n")
            f.write(f"Running script: {script_path}\n")

        result = subprocess.run(
            ["/usr/bin/env", "bash", script_path],
            capture_output=True,
            text=True
        )

        with open(log_path, "a") as f:
            f.write(f"Return Code: {result.returncode}\n")
            f.write(f"STDOUT:\n{result.stdout}\n")
            f.write(f"STDERR:\n{result.stderr}\n")
            f.write("------\n")

    except Exception as e:
        print(f"[Webhook] Exception occurred: {str(e)}")
        with open("/app/webhook.log", "a") as f:
            f.write(f"Exception: {str(e)}\n")

    return '', 204



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
