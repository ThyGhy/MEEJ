from flask import Flask, render_template, request, redirect, url_for, session
import database  # This is our custom module
import re

app = Flask(__name__)
app.secret_key = "MEEJ"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        # Retrieve user info via our database module
        user = database.get_user_by_email(email)
        if user and user['password'] == password:
            session['user_id'] = user['user_id']
            session['role'] = user['role']
            session['email'] = user['email']
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error="Invalid credentials.")
    return render_template('login.html')

@app.route('/register_exam', methods=['GET', 'POST'])
def register_exam():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        exam_id = request.form['exam_id']
        success, message = database.register_for_exam(session['user_id'], exam_id)
        if success:
            return redirect(url_for('registered_exams'))
        else:
            exams = database.fetch_exams()
            return render_template('register_exam.html', exams=exams, error=message)
    
    # For GET request, simply fetch exam data
    exams = database.fetch_exams()
    return render_template('register_exam.html', exams=exams)

@app.route('/registered_exams')
def registered_exams():
    # Implement a similar approach to fetch and display registered exams
    # using functions from your database module.
    pass

@app.route('/test', methods=['GET', 'POST'])
def test():
    message = None
    emails = []
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            email = request.form.get('email')
            password = request.form.get('password')
            # Validate email format: exactly 10 digits followed by @student or @student.csn.edu
            # Adjust the pattern as needed.
            pattern = r'^\d{10}@student(?:\.csn\.edu)?$'
            if not re.match(pattern, email):
                message = "Email must be in NSHE format (10 digits) and use '@student' (optionally '@student.csn.edu')."
            else:
                database.add_email(email, password)
                message = f"Added {email} to the database."
        elif action == 'fetch':
            # No need for email validation when fetching emails
            emails = database.fetch_emails()
    return render_template('test.html', message=message, emails=emails)

@app.route('/home')
def home():
    return render_template('home.html')

@app.route('/')
def index():
    return render_template('index.html')

if __name__ == "__main__":
    app.run(debug=True)