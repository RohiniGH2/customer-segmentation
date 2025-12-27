from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'fallback_secret_key_for_development')

# Add static file serving route for production
@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory('static', filename)

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
        role TEXT NOT NULL DEFAULT 'user',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create products table
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        image_url TEXT,
        category TEXT DEFAULT 'dress'
    )''')
    
    # Create ads table  
    cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        content TEXT,
        image_url TEXT,
        is_active INTEGER DEFAULT 1
    )''')
    
    conn.commit()
    cursor.close()
    conn.close()

@app.route('/')
def index():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if we have products, if not, populate ALL products
    cursor.execute("SELECT COUNT(*) FROM products")
    if cursor.fetchone()[0] == 0:
        # Add ALL sample products from your static folder
        sample_products = [
            ('Summer Beige Dress', 45.99, 'beige.jpg'),
            ('Beige Midi Dress', 52.99, 'beigemidi.jpg'),
            ('Black Evening Dress', 89.99, 'black.jpg'),
            ('Blue Casual Dress', 42.99, 'blue.jpg'),
            ('Blue Party Dress', 65.99, 'blueparty.jpg'),
            ('Floral Summer Dress', 39.99, 'floral.jpg'),
            ('Formal Black Dress', 95.99, 'formal.jpg'),
            ('Formal Event Dress', 105.99, 'formalevent.jpg'),
            ('Green Casual Dress', 48.99, 'green.jpg'),
            ('Green Summer Dress', 44.99, 'greensummer.jpg'),
            ('Latest Collection Dress', 67.99, 'latest.jpg'),
            ('Pink Maxi Dress', 55.99, 'pinkmaxi.jpg'),
            ('Pink Mini Dress', 35.99, 'pinkmini.jpg'),
            ('Pink Work Dress', 58.99, 'pinkwork.jpg'),
            ('Red Evening Dress', 78.99, 'red.jpg'),
            ('White Casual Dress', 42.99, 'white.jpg'),
            ('White Casual Day Dress', 41.99, 'whitecasual.jpg'),
            ('Yellow Casual Dress', 46.99, 'yellow.jpg'),
            ('Yellow Maxi Dress', 54.99, 'yellowmaxi.jpg')
        ]
        cursor.executemany('INSERT INTO products (name, price, image_url) VALUES (?, ?, ?)', sample_products)
        
        # Add sample ads
        sample_ads = [
            ('New Collection', 'Latest styles available!', 'latest.jpg'),
            ('Style Analytics', 'Find your perfect style', 'styleanalytics.jpg'),
            ('Analytics Dashboard', 'View your preferences', 'analytics2.jpg')
        ]
        cursor.executemany('INSERT INTO ads (title, content, image_url) VALUES (?, ?, ?)', sample_ads)
        conn.commit()
    
    # Fetch active ads
    cursor.execute("SELECT * FROM ads WHERE is_active = 1")
    ads = cursor.fetchall()
    
    # Fetch ALL products (not just 12)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('index.html', ads=ads, products=products)

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

@app.route('/test-images')
def test_images():
    """Test route to see if images are accessible"""
    import os
    static_path = os.path.join(app.root_path, 'static')
    if os.path.exists(static_path):
        files = os.listdir(static_path)
        image_files = [f for f in files if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))]
        return f"Static folder exists. Image files found: {image_files}"
    else:
        return "Static folder not found"

@app.route('/reset-data')
def reset_data():
    """Reset and populate with ALL products"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Clear existing products
    cursor.execute("DELETE FROM products")
    cursor.execute("DELETE FROM ads")
    
    # Add ALL products from your static folder
    sample_products = [
        ('Summer Beige Dress', 45.99, 'beige.jpg'),
        ('Beige Midi Dress', 52.99, 'beigemidi.jpg'),
        ('Black Evening Dress', 89.99, 'black.jpg'),
        ('Blue Casual Dress', 42.99, 'blue.jpg'),
        ('Blue Party Dress', 65.99, 'blueparty.jpg'),
        ('Floral Summer Dress', 39.99, 'floral.jpg'),
        ('Formal Black Dress', 95.99, 'formal.jpg'),
        ('Formal Event Dress', 105.99, 'formalevent.jpg'),
        ('Green Casual Dress', 48.99, 'green.jpg'),
        ('Green Summer Dress', 44.99, 'greensummer.jpg'),
        ('Latest Collection Dress', 67.99, 'latest.jpg'),
        ('Pink Maxi Dress', 55.99, 'pinkmaxi.jpg'),
        ('Pink Mini Dress', 35.99, 'pinkmini.jpg'),
        ('Pink Work Dress', 58.99, 'pinkwork.jpg'),
        ('Red Evening Dress', 78.99, 'red.jpg'),
        ('White Casual Dress', 42.99, 'white.jpg'),
        ('White Casual Day Dress', 41.99, 'whitecasual.jpg'),
        ('Yellow Casual Dress', 46.99, 'yellow.jpg'),
        ('Yellow Maxi Dress', 54.99, 'yellowmaxi.jpg')
    ]
    cursor.executemany('INSERT INTO products (name, price, image_url) VALUES (?, ?, ?)', sample_products)
    
    # Add sample ads - featuring actual dresses
    sample_ads = [
        ('Summer Beige Collection', 'Elegant beige dresses for any occasion', 'beige.jpg'),
        ('Evening Party Wear', 'Stunning blue dresses for special events', 'blueparty.jpg'),
        ('Floral Collection', 'Beautiful floral patterns for spring', 'floral.jpg')
    ]
    cursor.executemany('INSERT INTO ads (title, content, image_url) VALUES (?, ?, ?)', sample_ads)
    
    conn.commit()
    cursor.close()
    conn.close()
    
    return f"Database reset! Added {len(sample_products)} products and {len(sample_ads)} ads. <a href='/'>Go to Homepage</a>"

@app.route('/populate')
def populate_sample_data():
    """Populate sample data - call this once after deployment"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add sample products
    sample_products = [
        ('Summer Beige Dress', 45.99, '/static/beige.jpg'),
        ('Black Evening Dress', 89.99, '/static/black.jpg'),
        ('Blue Party Dress', 65.99, '/static/blueparty.jpg'),
        ('Floral Summer Dress', 39.99, '/static/floral.jpg'),
        ('Pink Maxi Dress', 55.99, '/static/pinkmaxi.jpg'),
        ('White Casual Dress', 42.99, '/static/whitecasual.jpg')
    ]
    
    try:
        cursor.executemany('INSERT OR IGNORE INTO products (name, price, image_url) VALUES (?, ?, ?)', sample_products)
        
        # Add sample ads
        sample_ads = [
            ('New Collection', 'Latest styles available!', 'latest.jpg'),
            ('Style Analytics', 'Find your perfect style', 'styleanalytics.jpg'),
            ('Analytics Dashboard', 'View your preferences', 'analytics2.jpg')
        ]
        cursor.executemany('INSERT OR IGNORE INTO ads (title, content, image_url) VALUES (?, ?, ?)', sample_ads)
        
        conn.commit()
        return "Sample data populated successfully!"
    except Exception as e:
        return f"Error: {str(e)}"
    finally:
        cursor.close()
        conn.close()

# Initialize database when app starts
init_db()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)