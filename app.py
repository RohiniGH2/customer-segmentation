from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_development')

def get_db_connection():
    conn = sqlite3.connect('users.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''CREATE TABLE IF NOT EXISTS dressly_users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        shipping_address TEXT,
        zip_code TEXT
    )''')
    
    # Create products table
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        category TEXT,
        image_url TEXT,
        stock_quantity INTEGER DEFAULT 0,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create ads table
    cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        image_url TEXT,
        target_audience TEXT,
        is_active INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html', ads=[], products=[])

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM dressly_users WHERE username = ? OR email = ?', (username, email))
            if cursor.fetchone():
                flash('Username or email already exists!', 'error')
                return render_template('register.html')
            
            password_hash = generate_password_hash(password)
            cursor.execute('''INSERT INTO dressly_users (username, email, password_hash, role) 
                             VALUES (?, ?, ?, ?)''', (username, email, password_hash, role))
            conn.commit()
            flash('Registration successful!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash('Registration failed. Please try again.', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form.get('role', 'user')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('SELECT * FROM dressly_users WHERE username = ? AND role = ?', (username, role))
            user = cursor.fetchone()
            
            if user and check_password_hash(user['password_hash'], password):
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                flash('Login successful!', 'success')
                
                if role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))
            else:
                flash('Invalid credentials!', 'error')
        except Exception as e:
            flash('Login failed. Please try again.', 'error')
        finally:
            cursor.close()
            conn.close()
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))

@app.route('/user_dashboard')
def user_dashboard():
    if 'username' not in session or session.get('role') != 'user':
        return redirect(url_for('login'))
    return render_template('user_dashboard.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'username' not in session or session.get('role') != 'admin':
        return redirect(url_for('login'))
    return render_template('admin_dashboard.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/service')
def service():
    return render_template('service.html')

@app.route('/cart')
def cart():
    return render_template('cart.html')

# Initialize database when app starts
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)