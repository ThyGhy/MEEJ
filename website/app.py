from flask import Flask, render_template, request, redirect, url_for, session
from auth import auth  # Import the auth blueprint

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Secret key for sessions

# Temporary in-memory user store (replace with a real database in production)
users = {}

app.register_blueprint(auth, url_prefix='/auth')  # Register the auth blueprint

@app.route('/')
def home():
    if 'username' in session:
        return redirect(url_for('auth.logout'))  # Redirect to logout page if logged in
    return render_template('home.html')  # Show the home page with login/signup options

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    password = request.form['password']
    if username in users and users[username] == password:
        session['username'] = username  # Store username in session (login the user)
        return redirect(url_for('home'))  # Redirect to home page after successful login
    else:
        return "Invalid username or password", 400

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove user from session (logout)
    return render_template('logout.html')  # Show logout message

@app.route('/signup', methods=['POST'])
def signup():
    username = request.form['new-username']
    password = request.form['new-password']
    if username in users:
        return "Username already exists", 400
    users[username] = password  # Add the new user to the in-memory store
    return redirect(url_for('auth.login'))  # Redirect to login page after successful signup

if __name__ == '__main__':
    app.run(debug=True)
