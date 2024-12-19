from flask import Flask, render_template, request, redirect, url_for, flash, session, send_from_directory
import os
from werkzeug.utils import secure_filename
import sqlite3

app = Flask(__name__)
app.secret_key = "your_secret_key"

# Configure upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Configure SQLite database
DATABASE = os.path.join(os.getcwd(), "instance", "users.db")
if not os.path.exists(os.path.dirname(DATABASE)):
    os.makedirs(os.path.dirname(DATABASE))


# Initialize the database
def init_db():
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )''')
        conn.commit()


init_db()


# Helper function to get user by email
def get_user_by_email(email):
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        return cursor.fetchone()


# Routes
@app.route('/')
def home():
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'username' in session:  # If the user is already logged in
        flash("You are already logged in.", "info")
        return redirect(url_for('upload'))

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if not username or not email or not password:
            flash("All fields are required!", "error")
            return redirect(request.url)

        try:
            with sqlite3.connect(DATABASE) as conn:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)",
                               (username, email, password))
                conn.commit()
                flash("Registration successful! Please log in.", "success")
                return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Username or email already exists.", "error")
            return redirect(request.url)
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'username' in session:  # If the user is already logged in
        flash("You are already logged in.", "info")
        return redirect(url_for('upload'))

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = get_user_by_email(email)
        if user and user[3] == password:
            session['username'] = user[1]  # Store username in session
            flash("Login successful!", "success")
            return redirect(url_for('upload'))
        else:
            flash("Invalid email or password.", "error")
            return redirect(request.url)
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    flash("You have been logged out.", "info")
    return redirect(url_for('login'))


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'username' not in session:
        flash("Please log in to upload files.", "error")
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)

        if file:
            filename = secure_filename(file.filename)
            user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
            if not os.path.exists(user_folder):
                os.makedirs(user_folder)
            file.save(os.path.join(user_folder, filename))
            flash('File successfully uploaded', 'success')
            return redirect(url_for('files'))
    return render_template('uploads.html')


@app.route('/files', methods=['GET', 'POST'])
def files():
    if 'username' not in session:
        flash("Please log in to view your files.", "error")
        return redirect(url_for('login'))

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    if not os.path.exists(user_folder):
        flash("No files uploaded yet.", "info")
        return render_template('files.html', files=[])

    files = os.listdir(user_folder)
    return render_template('files.html', files=files)


@app.route('/delete/<filename>', methods=['POST'])
def delete_file(filename):
    if 'username' not in session:
        flash("Please log in to delete files.", "error")
        return redirect(url_for('login'))

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    file_path = os.path.join(user_folder, filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash(f"File '{filename}' successfully deleted.", "success")
    else:
        flash(f"File '{filename}' not found.", "error")
    return redirect(url_for('files'))


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    if 'username' not in session:
        flash("Please log in to view files.", "error")
        return redirect(url_for('login'))

    user_folder = os.path.join(app.config['UPLOAD_FOLDER'], session['username'])
    return send_from_directory(user_folder, filename)


if __name__ == '__main__':
    app.run(debug=True)
