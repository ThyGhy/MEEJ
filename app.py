from flask import Flask, flash, render_template, request, redirect, url_for, session
import database  # This is our custom module
import re
import datetime

app = Flask(__name__)
app.secret_key = "MEEJ"

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email'].strip().lower()  # Normalize email
        password = request.form['password']
        print("Attempting login for:", email)
        
        # Check user in Authentication table
        user = database.get_user_by_email(email)
        if not user:
            print("User not found")
            return render_template('login.html', error="Invalid credentials.")
            
        if user['Password'] != password:
            print("Invalid password")
            return render_template('login.html', error="Invalid credentials.")
            
        # Set basic session data
        session['user_id'] = user['Auth_ID']  # Using Auth_ID from Authentication table
        session['email'] = user['CSN_Email']
        session['role'] = user['Role']
        
        # Get additional details based on role
        if user['Role'] == 'Student':
            student = database.get_student_details(user['Auth_ID'])
            if student:
                session['name'] = f"{student['FirstName']} {student['LastName']}"
                print("Student login successful; redirecting to student home.")
                return redirect(url_for('student_home'))
        else:
            faculty = database.get_faculty_details(user['Auth_ID'])
            if faculty:
                session['name'] = f"{faculty['FirstName']} {faculty['LastName']}"
                print("Faculty login successful; redirecting to faculty home.")
                return redirect(url_for('faculty_home'))
        
        # If we get here, something went wrong with getting user details
        session.clear()
        return render_template('login.html', error="Error retrieving user details.")
            
    return render_template('login.html', success=request.args.get('success'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        firstname = request.form['firstname'].strip().title()
        lastname = request.form['lastname'].strip().title()
        email = request.form['email'].strip().lower()
        password = request.form['password']

        student_match = re.match(r'^(\d{10})@student\.csn\.edu$', email)
        faculty_match = re.match(r'.+@(csn\.edu|faculty\.csn\.edu)$', email)

        if student_match:
            nshe_id = student_match.group(1)
            if password != nshe_id:
                error = "For student accounts, the password must match your 10-digit NSHE ID."
                return render_template('signup.html', error=error)
                
            success, message = database.add_student(firstname, lastname, email, nshe_id)
            if not success:
                return render_template('signup.html', error=message)
                
            # Get the new user for session data
            user = database.get_user_by_email(email)
            session['user_id'] = user['Auth_ID']  # Fixed: Use Auth_ID
            session['email'] = user['CSN_Email']  # Fixed: Use CSN_Email
            session['name'] = f"{firstname} {lastname}"
            session['role'] = 'Student'
            return redirect(url_for('student_home'))

        elif faculty_match:
            print(f"Attempting faculty registration for {email}")  # Debug log
            try:
                success, message = database.add_faculty(firstname, lastname, email, password)
                print(f"Faculty registration result: success={success}, message={message}")  # Debug log
                if not success:
                    return render_template('signup.html', error=message)
                    
                # Get the new user for session data
                user = database.get_user_by_email(email)
                if not user:
                    print("Failed to retrieve newly created faculty user")  # Debug log
                    return render_template('signup.html', error="Failed to create faculty account")
                    
                session['user_id'] = user['Auth_ID']  # Fixed: Use Auth_ID
                session['email'] = user['CSN_Email']  # Fixed: Use CSN_Email
                session['name'] = f"{firstname} {lastname}"
                session['role'] = 'Faculty'
                return redirect(url_for('faculty_home'))
            except Exception as e:
                print(f"Exception during faculty registration: {str(e)}")  # Debug log
                return render_template('signup.html', error=f"Registration error: {str(e)}")
        else:
            error = "Invalid email format. Students must use a 10-digit NSHE ID followed by @student.csn.edu, and faculty must use a valid csn domain."
            return render_template('signup.html', error=error)

    return render_template('signup.html')

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
        
        # Check if faculty email exists
        user = database.get_user_by_email(email)
        if user and user['Role'] == 'Faculty':
            try:
                # Generate reset token
                token = database.create_password_reset_token(email)
                if token:
                    reset_link = url_for('reset_password', token=token, _external=True)
                    print(f"Reset link generated: {reset_link}")
                    return render_template('forgot_password.html',
                        success=f"Follow This Link to Reset Your Password: <br><a href='{reset_link}' style='color: #00008B;'>Reset Password</a>")
                else:
                    return render_template('forgot_password.html',
                        error="Error generating reset token. Please try again.")
            except Exception as e:
                print(f"Error generating reset token: {str(e)}")
                return render_template('forgot_password.html',
                    error="An error occurred while processing your request. Please try again.")
        
        # Don't reveal if the email exists or not for security
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
    user = database.get_user_by_email(token_data['email'])
    if not user or user['Role'] != 'Faculty':
        return render_template('error.html', 
            error="This reset link is not valid for student accounts.")
    
    if request.method == 'POST':
        new_password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        if new_password != confirm_password:
            return render_template('reset_password.html', 
                error="Passwords do not match.", token=token)
        
        success, message = database.update_password(token_data['email'], new_password)
        if success:
            database.mark_token_used(token)
            return redirect(url_for('login', success="Password Reset Successfully"))
        else:
            return render_template('reset_password.html',
                error=message, token=token)
    
    return render_template('reset_password.html', token=token)

@app.route('/student_home')
def student_home():
    if 'user_id' not in session or session.get('role') != 'Student':
        return redirect(url_for('login'))
    return render_template('student_home.html')

@app.route('/faculty_home')
def faculty_home():
    if 'user_id' not in session or session.get('role') != 'Faculty':
        return redirect(url_for('login'))
    return render_template('faculty_home.html')

@app.route('/')
def index():
    return render_template('gocsn.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login', success="You have been logged out successfully."))

@app.route('/register_exam', methods=['GET', 'POST'])
def register_exam():
    if 'user_id' not in session or session.get('role') != 'Student':
        return redirect(url_for('login'))
        
    # Get student ID from session
    student = database.get_student_details(session['user_id'])
    if not student:
        return redirect(url_for('login'))
        
    # Check if student has reached the exam limit
    exam_count = database.get_registered_exam_count(student['StudentID'])
    if exam_count >= 3:
        return render_template('register_exam.html', 
                            error="Maximum limit of 3 exams reached. Please unregister from an exam before searching for new ones.",
                            exam_count=exam_count)
        
    if request.method == 'POST':
        # Save search criteria to session
        session['search_criteria'] = {
            'subject': request.form.get('subject', ''),
            'courseNum': request.form.get('courseNum', ''),
            'campus': request.form.get('campus', ''),
            'days': request.form.getlist('days[]'),
            'minDate': request.form.get('minDate', ''),
            'maxDate': request.form.get('maxDate', '')
        }
        
        # Search for exams, excluding already registered ones
        exams = database.search_exams(
            subject=session['search_criteria']['subject'],
            course_num=session['search_criteria']['courseNum'],
            campus=session['search_criteria']['campus'],
            days=session['search_criteria']['days'] if session['search_criteria']['days'] else None,
            min_date=session['search_criteria']['minDate'] if session['search_criteria']['minDate'] else None,
            max_date=session['search_criteria']['maxDate'] if session['search_criteria']['maxDate'] else None,
            student_id=student['StudentID']
        )
        
        return render_template('register_exam.html', 
                            exam_count=exam_count)
        
    # For GET requests, use saved search criteria if it exists
    search_criteria = session.get('search_criteria', {
        'subject': '',
        'courseNum': '',
        'campus': '',
        'days': [],
        'minDate': '',
        'maxDate': ''
    })
    
    return render_template('register_exam.html', 
                         exam_count=exam_count)

@app.route('/register_for_exam/<int:exam_id>', methods=['POST'])
def register_for_exam(exam_id):
    if 'user_id' not in session or session.get('role') != 'Student':
        return redirect(url_for('login'))
        
    # Get student ID from session
    student = database.get_student_details(session['user_id'])
    if not student:
        return redirect(url_for('login'))
        
    # Check if student has reached the exam limit
    exam_count = database.get_registered_exam_count(student['StudentID'])
    if exam_count >= 3:
        return redirect(url_for('exam_results', error="Maximum limit of 3 exams reached. Please unregister from an exam before registering for new ones."))
        
    success, message = database.register_for_exam(student['StudentID'], exam_id)
    if success:
        # Get the search parameters from the form
        subject = request.form.get('subject')
        course_num = request.form.get('courseNum')
        campus = request.form.get('campus')
        days = request.form.getlist('days[]')
        min_date = request.form.get('minDate')
        max_date = request.form.get('maxDate')
        
        # Search for exams again to update the list
        exams = database.search_exams(
            subject=subject,
            course_num=course_num,
            campus=campus,
            days=days if days else None,
            min_date=min_date if min_date else None,
            max_date=max_date if max_date else None,
            student_id=student['StudentID']
        )
        
        # Calculate pagination values
        EXAMS_PER_PAGE = 15
        total_exams = len(exams)
        total_pages = (total_exams + EXAMS_PER_PAGE - 1) // EXAMS_PER_PAGE
        current_page = 1  # After registration, return to first page
        
        # Slice exams for current page
        start_idx = 0  # First page starts at index 0
        end_idx = EXAMS_PER_PAGE
        current_page_exams = exams[start_idx:end_idx]
        
        return render_template('exam_results.html',
                            exam_results=current_page_exams,
                            success="Successfully registered for exam!",
                            exam_count=exam_count + 1,
                            current_page=current_page,
                            total_pages=total_pages)
    else:
        return redirect(url_for('exam_results', error=message))

@app.route('/registered_exams')
def registered_exams():
    if 'user_id' not in session or session.get('role') != 'Student':
        return redirect(url_for('login'))
        
    # Get student ID from session
    student = database.get_student_details(session['user_id'])
    if not student:
        return redirect(url_for('login'))
        
    registrations = database.get_student_exams(student['StudentID'])
    exam_count = database.get_registered_exam_count(student['StudentID'])
    return render_template('registered_exams.html', 
                         registrations=registrations,
                         exam_count=exam_count)

@app.route('/cancel_registration/<int:exam_id>', methods=['POST'])
def cancel_registration(exam_id):
    if 'user_id' not in session or session.get('role') != 'Student':
        return redirect(url_for('login'))
        
    # Get student ID from session
    student = database.get_student_details(session['user_id'])
    if not student:
        return redirect(url_for('login'))
        
    success, message = database.cancel_exam_registration(student['StudentID'], exam_id)
    return redirect(url_for('registered_exams'))

@app.route('/create_exam', methods=['GET', 'POST'])
def create_exam():
    if 'user_id' not in session or session.get('role') != 'Faculty':
        return redirect(url_for('login'))
    return render_template('create_exam.html')

@app.route('/debug/exams')
def debug_exams():
    exams = database.get_all_exams_debug()
    return f"Check console for debug output. Found {len(exams)} exams."

@app.route('/debug/exam_capacity/<int:exam_id>', methods=['GET'])
def debug_exam_capacity(exam_id):
    action = request.args.get('action', 'fill')
    if action == 'fill':
        num_registrations = int(request.args.get('num', 20))
        success, message = database.debug_fill_exam(exam_id, num_registrations)
    elif action == 'subtract':
        num_to_remove = int(request.args.get('num', 1))
        success, message = database.debug_subtract_registrations(exam_id, num_to_remove)
    else:  # clear
        success, message = database.debug_clear_exam_registrations(exam_id)
    
    return f"Debug result: {message}"

@app.route('/exam_results', methods=['GET', 'POST'])
def exam_results():
    if 'user_id' not in session or session.get('role') != 'Student':
        return redirect(url_for('login'))
        
    # Get student ID from session
    student = database.get_student_details(session['user_id'])
    if not student:
        return redirect(url_for('login'))
        
    # Get current exam count
    exam_count = database.get_registered_exam_count(student['StudentID'])
    
    # If student has reached the exam limit, show error and return to register page
    if exam_count >= 3:
        return render_template('register_exam.html',
                            exams=None,
                            error="Maximum limit of 3 exams reached. Please unregister from an exam before searching for new ones.",
                            exam_count=exam_count)
        
    if request.method == 'POST':
        # Get search parameters
        subject = request.form.get('subject')
        course_num = request.form.get('courseNum')
        campus = request.form.get('campus')
        days = request.form.getlist('days[]')
        min_date = request.form.get('minDate')
        max_date = request.form.get('maxDate')
        
        # Get page number from form, default to 1
        try:
            page = int(request.form.get('page', 1))
        except ValueError:
            page = 1
        
        # Search for all matching exams
        all_exams = database.search_exams(
            subject=subject,
            course_num=course_num,
            campus=campus,
            days=days if days else None,
            min_date=min_date if min_date else None,
            max_date=max_date if max_date else None,
            student_id=student['StudentID']
        )
        
        # Calculate pagination
        EXAMS_PER_PAGE = 15
        total_exams = len(all_exams)
        total_pages = (total_exams + EXAMS_PER_PAGE - 1) // EXAMS_PER_PAGE  # Ceiling division
        
        # Adjust page number if out of bounds
        page = max(1, min(page, total_pages))
        
        # Slice the exams for current page
        start_idx = (page - 1) * EXAMS_PER_PAGE
        end_idx = start_idx + EXAMS_PER_PAGE
        current_page_exams = all_exams[start_idx:end_idx]
        
        return render_template('exam_results.html', 
                            exam_results=current_page_exams,
                            exam_count=exam_count,
                            current_page=page,
                            total_pages=total_pages)
        
    return render_template('exam_results.html', 
                         exam_results=None,
                         exam_count=exam_count,
                         current_page=1,
                         total_pages=1)

@app.route('/debug/clear_all_samples')
def debug_clear_all_samples():
    """Debug endpoint to clear all sample exams and registrations."""
    success, message = database.debug_clear_all_sample_data()
    return f"Debug result: {message}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
