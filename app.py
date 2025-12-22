from flask import Flask, render_template, redirect, url_for, session, request, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime
from flask import jsonify
import csv
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
    
    # Create users table with created_at field
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
    
    # Create orders table
    cursor.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL,
        shipping_address TEXT NOT NULL,
        status TEXT NOT NULL,
        created_at DATETIME NOT NULL,
        FOREIGN KEY (user_id) REFERENCES dressly_users(id)
    )''')
    
    # Create order_items table
    cursor.execute('''CREATE TABLE IF NOT EXISTS order_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL,
        price REAL NOT NULL,
        FOREIGN KEY (order_id) REFERENCES orders(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    
    # Create product_reviews table
    cursor.execute('''CREATE TABLE IF NOT EXISTS product_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        rating INTEGER NOT NULL,
        review_text TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES dressly_users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    
    # Create user_preferences table
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_preferences (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        favorite_color TEXT,
        preferred_style TEXT,
        budget REAL,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES dressly_users(id)
    )''')
    
    # Create recently_viewed table
    cursor.execute('''CREATE TABLE IF NOT EXISTS recently_viewed (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        viewed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES dressly_users(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    
    # Create user_feedback table
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        feedback_text TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES dressly_users(id)
    )''')
    
    # Create offers table
    cursor.execute('''CREATE TABLE IF NOT EXISTS offers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        discount_percent INT,
        min_purchase DECIMAL(10,2),
        valid_from DATETIME,
        valid_until DATETIME,
        is_active BOOLEAN DEFAULT TRUE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create user_offers table to track which offers are available to which users
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_offers (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        offer_id INT NOT NULL,
        is_used BOOLEAN DEFAULT FALSE,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES dressly_users(id),
        FOREIGN KEY (offer_id) REFERENCES offers(id)
    )''')
    
    # Create user_sessions table to track login activity
    cursor.execute('''CREATE TABLE IF NOT EXISTS user_sessions (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        session_id VARCHAR(255) NOT NULL,
        last_login DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES dressly_users(id)
    )''')

    # Create products table if not exists (it's referenced by other tables)
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id INT AUTO_INCREMENT PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        category VARCHAR(100),
        image VARCHAR(255),
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )''')

    # Create carts table for persistent cart tracking
    cursor.execute('''CREATE TABLE IF NOT EXISTS carts (
        id INT AUTO_INCREMENT PRIMARY KEY,
        user_id INT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_ordered BOOLEAN DEFAULT FALSE,
        FOREIGN KEY (user_id) REFERENCES dressly_users(id)
    )''')

    # Create cart_items table for persistent cart items
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart_items (
        id INT AUTO_INCREMENT PRIMARY KEY,
        cart_id INT NOT NULL,
        product_id INT NOT NULL,
        title VARCHAR(255),
        color VARCHAR(50),
        size VARCHAR(20),
        quantity INT DEFAULT 1,
        price DECIMAL(10,2) DEFAULT 0,
        FOREIGN KEY (cart_id) REFERENCES carts(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')

    conn.commit()
    cursor.close()
    conn.close()

init_db()

# Function to check and add column if it doesn't exist
def add_column_if_not_exists(cursor, table, column, definition):
    try:
        cursor.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (column,))
        if not cursor.fetchone():
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
            return True
    except mysql.connector.Error as err:
        print(f"Error checking/adding column {column} to {table}: {err}")
    return False

# Function to ensure all required columns exist
def ensure_columns():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Add created_at to dressly_users
    add_column_if_not_exists(cursor, 'dressly_users', 'created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
    
    # Add created_at to products
    add_column_if_not_exists(cursor, 'products', 'created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
    
    # Add category to products
    add_column_if_not_exists(cursor, 'products', 'category', 'VARCHAR(100)')
    
    # Add required columns to product_reviews
    add_column_if_not_exists(cursor, 'product_reviews', 'created_at', 'DATETIME DEFAULT CURRENT_TIMESTAMP')
    
    conn.commit()
    cursor.close()
    conn.close()

# --- ADS TABLE CREATION ---
def init_ads_table():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
        id INT AUTO_INCREMENT PRIMARY KEY,
        product_id INT,
        title VARCHAR(255),
        description TEXT,
        image VARCHAR(255),
        target_segment INT,
        start_date DATE,
        end_date DATE,
        is_active BOOLEAN DEFAULT TRUE
    )''')
    conn.commit()
    cursor.close()
    conn.close()

# Initialize tables
init_db()
init_ads_table()
# Ensure all required columns exist
ensure_columns()

@app.route('/')
def index():
    # Fetch only active ads
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM ads WHERE is_active = 1")
    ads = cursor.fetchall()
    # Fetch all products
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('index.html', ads=ads, products=products)
# Product page route
@app.route('/product/<int:product_id>')
def product_page(product_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # Get main product
    cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
    product = cursor.fetchone()
    # Get other products (exclude current)
    cursor.execute('SELECT * FROM products WHERE id != %s LIMIT 6', (product_id,))
    other_products = cursor.fetchall()
    cursor.close()
    conn.close()
    if not product:
        return "Product not found", 404
    return render_template('product.html', product=product, other_products=other_products)
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']
        password_hash = generate_password_hash(password)
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        # Check if username or email exists
        cursor.execute('SELECT * FROM dressly_users WHERE username = %s OR email = %s', (username, email))
        existing_user = cursor.fetchone()
        if existing_user:
            if existing_user['role'] != role:
                flash(f"This username/email is already registered as a {existing_user['role'].capitalize()}. Please choose a different one or log in.", "error")
            else:
                flash('Username or email already exists.', 'error')
            cursor.close()
            conn.close()
            return render_template('register.html')
        try:
            cursor.execute('INSERT INTO dressly_users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)',
                           (username, email, password_hash, role))
            conn.commit()
            cursor.close()
            conn.close()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except mysql.connector.IntegrityError:
            cursor.close()
            conn.close()
            flash('Username or email already exists.', 'error')
            return render_template('register.html')
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        # Get user data
        cursor.execute('SELECT * FROM dressly_users WHERE username = %s AND role = %s', (username, role))
        user = cursor.fetchall()
        
        if user and check_password_hash(user[0]['password_hash'], password):
            session['username'] = user[0]['username']
            session['role'] = user[0]['role']
            session['user_id'] = user[0]['id']  # Ensure user_id is set for cart tracking
            # Record the login in user_sessions
            cursor.execute(
                'INSERT INTO user_sessions (user_id, session_id) VALUES (%s, %s)', 
                (user[0]['id'], session.sid if hasattr(session, 'sid') else 'unknown')
            )
            # Load persistent cart from DB (carts table, is_ordered=0)
            cursor.execute('SELECT id FROM carts WHERE user_id = %s AND is_ordered = 0 ORDER BY created_at DESC LIMIT 1', (user[0]['id'],))
            cart_row = cursor.fetchone()
            if cart_row:
                session['cart_id'] = cart_row['id']
                # Load cart items from cart_items table (if exists)
                try:
                    conn2 = get_db_connection()
                    cursor2 = conn2.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
                    cursor2.execute('SELECT * FROM cart_items WHERE cart_id = %s', (cart_row['id'],))
                    cart_items = cursor2.fetchall()
                    session['cart'] = cart_items if cart_items else []
                    cursor2.close()
                    conn2.close()
                except Exception as e:
                    print('Error loading cart items:', e)
            else:
                session['cart'] = []
            conn.commit()
            cursor.close()
            conn.close()
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('index'))
        else:
            cursor.close()
            conn.close()
            flash('Invalid credentials or role.', 'danger')
            return render_template('login.html')
            
    return render_template('login.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/services')
def services():
    return render_template('service.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/admin_dashboard')
def admin_dashboard():
    import csv
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # Registered users
    cursor.execute('SELECT id, username, email, role FROM dressly_users')
    users = cursor.fetchall()
    # Ads management
    cursor.execute('SELECT id, product_id, title, description, image, target_segment, start_date, end_date, is_active FROM ads')
    ads = cursor.fetchall()
    # Customer segmentation from clustered_customers.csv
    clustered_customers = []
    try:
        with open('clustered_customers.csv', newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                clustered_customers.append(row)
    except Exception as e:
        print('Error reading clustered_customers.csv:', e)

    # --- SALES & TRENDS METRICS ---
    # Top Seller
    cursor.execute('''
        SELECT p.title, SUM(oi.quantity) AS total_sold
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        GROUP BY p.id
        ORDER BY total_sold DESC
        LIMIT 1
    ''')
    top_seller = cursor.fetchone()

    # Repeat Purchase Rate
    cursor.execute('''
        SELECT COUNT(DISTINCT user_id) AS total_users FROM orders
    ''')
    total_users = cursor.fetchone()['total_users']
    cursor.execute('''
        SELECT user_id, COUNT(*) AS order_count FROM orders GROUP BY user_id HAVING order_count > 1
    ''')
    repeat_buyers = cursor.fetchall()
    repeat_purchase_rate = round((len(repeat_buyers) / total_users) * 100, 2) if total_users else 0

    # Abandoned Cart Rate (assume you have a carts table with is_ordered flag)
    try:
        cursor.execute('SELECT COUNT(*) AS total_carts FROM carts')
        total_carts = cursor.fetchone()['total_carts']
        cursor.execute('SELECT COUNT(*) AS ordered_carts FROM carts WHERE is_ordered = 1')
        ordered_carts = cursor.fetchone()['ordered_carts']
        abandoned_cart_rate = round(((total_carts - ordered_carts) / total_carts) * 100, 2) if total_carts else 0
    except:
        abandoned_cart_rate = None

    # Sales Table: sales by date
    cursor.execute('''
        SELECT DATE(created_at) AS date, SUM(total_amount) AS sales
        FROM orders
        GROUP BY DATE(created_at)
        ORDER BY date DESC
        LIMIT 30
    ''')
    sales_trends = cursor.fetchall()

    # ...existing analytics code...
    cursor.execute('''SELECT pe.*, p.title FROM product_engagement pe JOIN products p ON pe.product_id = p.id ORDER BY pe.views DESC LIMIT 10''')
    engagement = cursor.fetchall()
    cursor.execute('''SELECT pe.*, p.title FROM product_engagement pe JOIN products p ON pe.product_id = p.id ORDER BY pe.avg_rating DESC, pe.rating_count DESC LIMIT 1''')
    top_rated = cursor.fetchone()
    cursor.execute('''SELECT du.username, COUNT(us.id) AS activity_count FROM user_sessions us JOIN dressly_users du ON us.user_id = du.id GROUP BY us.user_id ORDER BY activity_count DESC LIMIT 1''')
    most_active_user = cursor.fetchone()
    cursor.execute('''SELECT du.username, COUNT(o.id) AS purchases FROM orders o JOIN dressly_users du ON o.user_id = du.id GROUP BY o.user_id ORDER BY purchases DESC LIMIT 1''')
    top_buyer = cursor.fetchone()
    cursor.execute('''SELECT p.category, SUM(pe.views) AS total_views FROM product_engagement pe JOIN products p ON pe.product_id = p.id GROUP BY p.category ORDER BY total_views DESC LIMIT 1''')
    most_viewed_category = cursor.fetchone()
    cursor.execute('''
        SELECT p.category, COUNT(DISTINCT o.user_id) AS user_count
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE p.category IS NOT NULL AND p.category != ''
        GROUP BY p.category
        ORDER BY user_count DESC
        LIMIT 1
    ''')
    most_popular_segment = cursor.fetchone()
    cursor.close()
    conn.close()
    return render_template('admin_dashboard.html', users=users, ads=ads, clustered_customers=clustered_customers, engagement=engagement, top_rated=top_rated,
        most_active_user=most_active_user, top_buyer=top_buyer, most_viewed_category=most_viewed_category, most_popular_segment=most_popular_segment,
        top_seller=top_seller, repeat_purchase_rate=repeat_purchase_rate, abandoned_cart_rate=abandoned_cart_rate, sales_trends=sales_trends)

# --- ADMIN ADS ROUTES ---
@app.route('/admin/ads', methods=['GET', 'POST'])
def admin_ads():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    if request.method == 'POST':
        product_id = request.form['product_id']
        title = request.form['title']
        description = request.form['description']
        image = request.form['image']
        target_segment = request.form['target_segment']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        is_active = 1 if 'is_active' in request.form else 0
        cursor.execute('''INSERT INTO ads (product_id, title, description, image, target_segment, start_date, end_date, is_active)
                          VALUES (%s, %s, %s, %s, %s, %s, %s, %s)''',
                       (product_id, title, description, image, target_segment, start_date, end_date, is_active))
        conn.commit()
        flash('Ad created successfully!', 'success')
    cursor.execute('SELECT * FROM ads')
    ads = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template('admin_ads.html', ads=ads)

@app.route('/admin/ads/delete/<int:ad_id>', methods=['POST'])
def delete_ad(ad_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM ads WHERE id = %s', (ad_id,))
    conn.commit()
    cursor.close()
    conn.close()
    flash('Ad deleted.', 'success')
    return redirect(url_for('admin_ads'))

@app.route('/admin/ads/toggle/<int:ad_id>', methods=['POST'])
def toggle_ad(ad_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE ads SET is_active = NOT is_active WHERE id = %s', (ad_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('admin_ads'))

# --- FETCH ACTIVE ADS FOR USER SEGMENT ---
def get_active_ads_for_segment(segment):
    today = datetime.now().date()
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''SELECT * FROM ads WHERE is_active=1 AND (target_segment=%s OR target_segment IS NULL)
                      AND (start_date IS NULL OR start_date<=%s) AND (end_date IS NULL OR end_date>=%s)''',
                   (segment, today, today))
    ads = cursor.fetchall()
    cursor.close()
    conn.close()
    return ads

# Function to get user preferences
def get_user_preferences(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT * FROM user_preferences 
        WHERE user_id = %s
    ''', (user_id,))
    prefs = cursor.fetchone()
    cursor.close()
    conn.close()
    return prefs

# Function to get recently viewed products
def get_recently_viewed(user_id, limit=3):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT p.*, rv.viewed_at 
        FROM recently_viewed rv
        JOIN products p ON rv.product_id = p.id
        WHERE rv.user_id = %s
        ORDER BY rv.viewed_at DESC
        LIMIT %s
    ''', (user_id, limit))
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return products

# Function to get user-specific offers
def get_user_offers(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute('''
        SELECT o.* 
        FROM offers o
        LEFT JOIN user_offers uo ON o.id = uo.offer_id AND uo.user_id = %s
        WHERE o.is_active = TRUE 
        AND (uo.id IS NULL OR uo.is_used = FALSE)
        AND (o.valid_until IS NULL OR o.valid_until > NOW())
        LIMIT 3
    ''', (user_id,))
    offers = cursor.fetchall()
    cursor.close()
    conn.close()
    return offers

# Function to get personalized recommendations
def get_recommendations(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    # Get user preferences
    prefs = get_user_preferences(user_id)
    
    # Base query with product details
    query = '''
        SELECT DISTINCT p.*, 
        CASE 
            WHEN up.favorite_color = p.color THEN 2
            WHEN p.price <= up.budget THEN 1
            ELSE 0
        END as relevance_score
        FROM products p
        LEFT JOIN user_preferences up ON up.user_id = %s
        WHERE 1=1
    '''
    params = [user_id]
    
    if prefs:
        if prefs.get('favorite_color'):
            query += ' AND p.color = %s'
            params.append(prefs['favorite_color'])
        if prefs.get('preferred_style'):
            query += ' OR p.category = %s'
            params.append(prefs['preferred_style'])
        if prefs.get('budget'):
            query += ' AND p.price <= %s'
            params.append(prefs['budget'])
    
    query += ' ORDER BY relevance_score DESC, RAND() LIMIT 3'
    
    cursor.execute(query, tuple(params))
    recommendations = cursor.fetchall()
    cursor.close()
    conn.close()
    return recommendations

@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Get user ID
        cursor.execute('SELECT id FROM dressly_users WHERE username = %s', (session['username'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        favorite_color = request.form.get('favorite_color')
        preferred_style = request.form.get('preferred_style')
        budget = request.form.get('budget')
        
        # Update or insert preferences
        cursor.execute('''
            INSERT INTO user_preferences (user_id, favorite_color, preferred_style, budget)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            favorite_color = VALUES(favorite_color),
            preferred_style = VALUES(preferred_style),
            budget = VALUES(budget)
        ''', (user['id'], favorite_color, preferred_style, budget))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Preferences updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Get user ID
        cursor.execute('SELECT id FROM dressly_users WHERE username = %s', (session['username'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        feedback_text = request.form.get('feedback')
        
        if not feedback_text:
            return jsonify({'success': False, 'message': 'Feedback cannot be empty'}), 400
        
        cursor.execute('''
            INSERT INTO user_feedback (user_id, feedback_text)
            VALUES (%s, %s)
        ''', (user['id'], feedback_text))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Feedback submitted successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/update_profile', methods=['POST'])
def update_profile():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        shipping_address = request.form.get('shipping_address')
        zip_code = request.form.get('zip_code')
        
        cursor.execute('''
            UPDATE dressly_users
            SET shipping_address = %s,
                zip_code = %s
            WHERE username = %s
        ''', (shipping_address, zip_code, session['username']))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Profile updated successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

@app.route('/claim_offer/<int:offer_id>', methods=['POST'])
def claim_offer(offer_id):
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Please login first'}), 401
    
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Get user ID
        cursor.execute('SELECT id FROM dressly_users WHERE username = %s', (session['username'],))
        user = cursor.fetchone()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Check if offer exists and is active
        cursor.execute('''
            SELECT * FROM offers 
            WHERE id = %s AND is_active = TRUE 
            AND (valid_until IS NULL OR valid_until > NOW())
        ''', (offer_id,))
        offer = cursor.fetchone()
        
        if not offer:
            return jsonify({'success': False, 'message': 'Offer not found or expired'}), 404
        
        # Add to user_offers
        cursor.execute('''
            INSERT INTO user_offers (user_id, offer_id)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE is_used = FALSE
        ''', (user['id'], offer_id))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Offer claimed successfully'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()

# --- USER DASHBOARD: PASS ADS AND USER DATA ---
@app.route('/user_dashboard')
def user_dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    
    try:
        # Get user data
        cursor.execute('SELECT id, created_at, shipping_address, zip_code FROM dressly_users WHERE username = %s', (session['username'],))
        user = cursor.fetchone()
        
        if not user:
            return redirect(url_for('login'))
        
        user_id = user['id']
        
        # Initialize dashboard data
        dashboard_data = {
            'username': session['username'],
            'user': user,
            'total_spent': 0.0,
            'review_count': 0,
            'order_count': 0,
            'recent_order': None,
            'last_login': None,
            'favorite_category': "Not enough data",
            'ads': []
        }
        
        # Get order count and total spent
        cursor.execute('''
            SELECT COUNT(*) as order_count, COALESCE(SUM(total_amount), 0) as total_spent
            FROM orders 
            WHERE user_id = %s
        ''', (user_id,))
        order_stats = cursor.fetchone()
        if order_stats:
            dashboard_data['order_count'] = order_stats['order_count']
            dashboard_data['total_spent'] = float(order_stats['total_spent'])
        
        # Get order history
        cursor.execute('''
            SELECT o.*, GROUP_CONCAT(p.title) as products
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = %s
            GROUP BY o.id
            ORDER BY o.created_at DESC
            LIMIT 5
        ''', (user_id,))
        dashboard_data['orders'] = cursor.fetchall()
        
        # Get most recent order details
        cursor.execute('''
            SELECT o.created_at, GROUP_CONCAT(oi.quantity, ' x ', p.title) as items
            FROM orders o
            JOIN order_items oi ON o.id = oi.order_id
            JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = %s
            GROUP BY o.id, o.created_at
            ORDER BY o.created_at DESC
            LIMIT 1
        ''', (user_id,))
        recent_order = cursor.fetchone()
        if recent_order:
            dashboard_data['recent_order'] = {
                'items': recent_order['items'].split(',')[0] if recent_order['items'] else "No orders yet",
                'date': recent_order['created_at'].strftime('%Y-%m-%d') if recent_order['created_at'] else None
            }
        
        # Get review count and history
        cursor.execute('SELECT COUNT(*) as review_count FROM product_reviews WHERE user_id = %s', (user_id,))
        review_count = cursor.fetchone()
        if review_count:
            dashboard_data['review_count'] = review_count['review_count']
        
        cursor.execute('''
            SELECT pr.*, p.title as product_title, p.image
            FROM product_reviews pr
            JOIN products p ON pr.product_id = p.id
            WHERE pr.user_id = %s
            ORDER BY pr.created_at DESC
            LIMIT 5
        ''', (user_id,))
        dashboard_data['reviews'] = cursor.fetchall()
        
        # Get last login time
        cursor.execute('''
            SELECT last_login 
            FROM user_sessions 
            WHERE user_id = %s 
            ORDER BY last_login DESC 
            LIMIT 1
        ''', (user_id,))
        last_login = cursor.fetchone()
        if last_login and last_login['last_login']:
            dashboard_data['last_login'] = last_login['last_login'].strftime('%Y-%m-%d %I:%M %p')
        
        # Get favorite category
        cursor.execute('''
            SELECT p.category, COUNT(*) as count
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            JOIN products p ON oi.product_id = p.id
            WHERE o.user_id = %s AND p.category IS NOT NULL
            GROUP BY p.category
            ORDER BY count DESC
            LIMIT 1
        ''', (user_id,))
        favorite_category = cursor.fetchone()
        if favorite_category and favorite_category['category']:
            dashboard_data['favorite_category'] = favorite_category['category']
        
        # Get user segment and ads
        segment = 0  # Default segment
        try:
            with open('clustered_customers.csv', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get('user_id') == str(user_id):
                        segment = int(row.get('cluster', 0))
                        break
        except Exception as e:
            print('Error reading clustered_customers.csv:', e)
        
        # Get active ads for the user's segment
        dashboard_data['ads'] = get_active_ads_for_segment(segment)
        
        # Get user preferences and recommendations
        dashboard_data['preferences'] = get_user_preferences(user_id)
        dashboard_data['recently_viewed'] = get_recently_viewed(user_id)
        dashboard_data['recommendations'] = get_recommendations(user_id)
        dashboard_data['offers'] = get_user_offers(user_id)
        
        # Get user feedback
        cursor.execute('SELECT * FROM user_feedback WHERE user_id = %s ORDER BY created_at DESC LIMIT 3', (user_id,))
        dashboard_data['feedback'] = cursor.fetchall()
        
        return render_template('user_dashboard.html', **dashboard_data)
        
    except Exception as e:
        print(f"Error in user_dashboard: {e}")
        flash('An error occurred while loading your dashboard.', 'error')
        return redirect(url_for('index'))
    
    finally:
        cursor.close()
        conn.close()

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    if 'username' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401
    item = request.get_json()
    if not item:
        return {'success': False, 'error': 'No item data'}, 400
    cart = session.get('cart', [])
    # Always fetch product_id from products table by title
    product_title = item.get('title')
    product_id = None
    if product_title:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM products WHERE title=%s", (product_title,))
            result = cursor.fetchone()
            if result:
                product_id = result[0]
            cursor.close()
            conn.close()
        except Exception as e:
            print('Error fetching product_id:', e)
    if product_id:
        item['product_id'] = product_id
    # Check if item already exists (match by title, color, size)
    found = False
    for cart_item in cart:
        if (cart_item.get('title') == item.get('title') and
            cart_item.get('color') == item.get('color') and
            cart_item.get('size') == item.get('size')):
            cart_item['quantity'] = cart_item.get('quantity', 1) + 1
            found = True
            break
    if not found:
        item['quantity'] = 1
        cart.append(item)
    session['cart'] = cart
    # Save cart items to DB (cart_items table)
    cart_id = session.get('cart_id')
    if cart_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Remove all previous items for this cart (optional: for simplicity)
            cursor.execute('DELETE FROM cart_items WHERE cart_id = %s', (cart_id,))
            for cart_item in cart:
                cursor.execute('''INSERT INTO cart_items (cart_id, product_id, title, color, size, quantity, price) VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                               (cart_id, cart_item.get('product_id'), cart_item.get('title'), cart_item.get('color'), cart_item.get('size'), cart_item.get('quantity', 1), cart_item.get('price', 0)))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Error saving cart items to DB:', e)

    # --- Update product_engagement.add_to_cart in DB ---
    if product_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Increment add_to_cart
            cursor.execute("UPDATE product_engagement SET add_to_cart = add_to_cart + 1 WHERE product_id = %s", (product_id,))
            # Increment views
            cursor.execute("UPDATE product_engagement SET views = views + 1 WHERE product_id = %s", (product_id,))
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Error updating add_to_cart/views in product_engagement:', e)

    # --- Ensure cart is tracked in DB for abandoned cart analytics ---
    cart_id = session.get('cart_id')
    # Debug print to verify user_id
    print('add_to_cart: session user_id =', session.get('user_id'))
    if not cart_id:
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            # Insert new cart record
            cursor.execute('''INSERT INTO carts (user_id, created_at, is_ordered) VALUES (%s, NOW(), 0)''', (session['user_id'],))
            cart_id = cursor.lastrowid
            session['cart_id'] = cart_id
            conn.commit()
            cursor.close()
            conn.close()
        except Exception as e:
            print('Error inserting cart for abandoned cart tracking:', e)

    # Return the total quantity of items in the cart (not just types)
    total_quantity = sum(i.get('quantity', 1) for i in cart)
    return {'success': True, 'cart_count': total_quantity}

@app.route('/cart')
def cart():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('cart.html')

@app.route('/get_cart')
def get_cart():
    cart = session.get('cart', [])
    return jsonify(cart)

@app.route('/checkout', methods=['POST'])
def checkout():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Please log in to checkout'}), 401
    
    data = request.get_json()
    if not data or 'items' not in data:
        return jsonify({'success': False, 'error': 'No items in cart'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get user id
        cursor.execute('SELECT id FROM dressly_users WHERE username = %s', (session['username'],))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({'success': False, 'error': 'User not found'}), 400
        user_id = user[0]
        # Calculate total amount
        items = data['items']
        total_amount = 0.0
        for item in items:
            try:
                price = float(item.get('price', 0))
            except Exception:
                price = 0.0
            try:
                quantity = int(item.get('quantity', 1))
            except Exception:
                quantity = 1
            total_amount += price * quantity
        # Always get shipping address from checkout form data
        # Accept 'address' from frontend as shipping_address
        shipping_address = data.get('address', '').strip()
        if not shipping_address:
            shipping_address = data.get('shipping_address', '').strip()
        if not shipping_address:
            shipping_address = session.get('shipping_address', '')
        # Insert order with correct total_amount and shipping_address
        cursor.execute('''INSERT INTO orders (user_id, total_amount, shipping_address, status, created_at) VALUES (%s, %s, %s, %s, NOW())''',
                       (user_id, total_amount, shipping_address, 'Placed'))
        order_id = cursor.lastrowid
        # Insert order items
        for item in items:
            try:
                product_id = int(item.get('product_id', 0))
            except Exception:
                product_id = 0
            # Check if product_id exists in products table
            cursor.execute('SELECT id FROM products WHERE id = %s', (product_id,))
            valid_product = cursor.fetchone()
            if not valid_product:
                continue  # Skip invalid product_id
            try:
                quantity = int(item.get('quantity', 1))
            except Exception:
                quantity = 1
            try:
                price = float(item.get('price', 0))
            except Exception:
                price = 0.0
            cursor.execute('''INSERT INTO order_items (order_id, product_id, quantity, price) VALUES (%s, %s, %s, %s)''',
                           (order_id, product_id, quantity, price))
        conn.commit()
        cursor.close()
        conn.close()
        session['cart'] = []

        # --- Mark cart as ordered after successful checkout ---
        cart_id = session.get('cart_id')
        if cart_id:
            try:
                conn = get_db_connection()
                cursor = conn.cursor()
                cursor.execute('UPDATE carts SET is_ordered = 1 WHERE id = %s', (cart_id,))
                conn.commit()
                cursor.close()
                conn.close()
                session.pop('cart_id', None)
            except Exception as e:
                print('Error updating cart as ordered:', e)

        return jsonify({'success': True, 'redirect': url_for('checkout_success')})
    except Exception as e:
        print('Error placing order:', e)
        session['cart'] = []
        return jsonify({'success': False, 'error': str(e)})

@app.route('/checkout_success')
def checkout_success():
    return render_template('checkout_success.html')


@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    idx = request.json.get('idx')
    cart = session.get('cart', [])
    if idx is not None and 0 <= idx < len(cart):
        cart.pop(idx)
        session['cart'] = cart
        return {'success': True}
    return {'success': False, 'error': 'Invalid index'}, 400

@app.route('/update_cart', methods=['POST'])
def update_cart():
    if 'username' not in session:
        return {'success': False, 'error': 'Not logged in'}, 401
    data = request.get_json()
    cart = session.get('cart', [])
    # If data is a dict with idx/action, handle increment/decrement
    if isinstance(data, dict) and 'idx' in data and 'action' in data:
        idx = data['idx']
        action = data['action']
        if 0 <= idx < len(cart):
            cart[idx]['quantity'] = cart[idx].get('quantity', 1)
            if action == 'increment':
                cart[idx]['quantity'] += 1
            elif action == 'decrement' and cart[idx]['quantity'] > 1:
                cart[idx]['quantity'] -= 1
            session['cart'] = cart
            return {'success': True}
        return {'success': False, 'error': 'Invalid index'}, 400
    # Otherwise, replace cart (legacy support)
    if isinstance(data, list):
        for item in data:
            if 'quantity' not in item:
                item['quantity'] = 1
        session['cart'] = data
        return {'success': True}
    return {'success': False, 'error': 'Invalid data'}, 400

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin_dashboard_data')
def admin_dashboard_data():
    import csv
    import traceback
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cursor.execute("SELECT id, username, email, role FROM dressly_users")
        registered_users = cursor.fetchall()
        # Fetch ads data
        cursor.execute("SELECT id, product_id, title, description, image, target_segment, start_date, end_date, is_active FROM ads")
        ads = cursor.fetchall()

        # Fetch most viewed product
        cursor.execute('''
            SELECT p.id, p.title, p.image, pe.views
            FROM product_engagement pe
            JOIN products p ON pe.product_id = p.id
            ORDER BY pe.views DESC
            LIMIT 1
        ''')
        most_viewed = cursor.fetchone()

        # Fetch most added to cart product
        cursor.execute('''
            SELECT p.id, p.title, p.image, pe.add_to_cart
            FROM product_engagement pe
            JOIN products p ON pe.product_id = p.id
            ORDER BY pe.add_to_cart DESC
            LIMIT 1
        ''')
        most_added = cursor.fetchone()

        # Fetch product with highest conversion rate (purchases/views)
        cursor.execute('''
            SELECT p.id, p.title, p.image,
                   pe.purchases, pe.views,
                   CASE WHEN pe.views > 0 THEN ROUND(pe.purchases / pe.views, 4) ELSE 0 END AS conversion_rate
            FROM product_engagement pe
            JOIN products p ON pe.product_id = p.id
            ORDER BY conversion_rate DESC
            LIMIT 1
        ''')
        highest_conversion = cursor.fetchone()

        cursor.close()
        conn.close()

        data = {}
        data["registered_users"] = registered_users
        data["ads"] = ads
        # Add most_viewed_product if found
        data["most_viewed_product"] = most_viewed if most_viewed else None
        # Add most_added_product if found
        data["most_added_product"] = most_added if most_added else None
        # Add highest_conversion_rate product
        data["highest_conversion_product"] = highest_conversion if highest_conversion else None

        # Read clustered_customers.csv and add to data
        csv_rows = []
        try:
            with open('clustered_customers.csv', newline='', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    csv_rows.append(row)
        except Exception as e:
            print('Error reading clustered_customers.csv:', e)
            traceback.print_exc()
            csv_rows = []
        data["clustered_customers"] = csv_rows
        return jsonify(data)
    except Exception as e:
        print('Error in /admin_dashboard_data:', e)
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

from flask import request, session, jsonify
import mysql.connector

# Helper: Get product_id by title (or use product_id directly if available)
def get_product_id_by_title(title):
    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id FROM products WHERE title=%s", (title,))
    result = cursor.fetchone()
    cursor.close()
    return result[0] if result else None

# Increment product view
@app.route('/track_view', methods=['POST'])
def track_view():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    data = request.json
    product_id = get_product_id_by_title(data['title'])
    if product_id:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE product_engagement SET views = views + 1 WHERE product_id = %s", (product_id,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# Increment add to cart
@app.route('/track_add_to_cart', methods=['POST'])
def track_add_to_cart():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    data = request.json
    product_id = get_product_id_by_title(data['title'])
    if product_id:
        cursor = mysql.connection.cursor()
        cursor.execute("UPDATE product_engagement SET add_to_cart = add_to_cart + 1 WHERE product_id = %s", (product_id,))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# Increment purchases and recalculate conversion rate
@app.route('/track_purchase', methods=['POST'])
def track_purchase():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    data = request.json
    product_id = get_product_id_by_title(data['title'])
    if product_id:
        cursor = mysql.connection.cursor()
        # Increment purchases
        cursor.execute("UPDATE product_engagement SET purchases = purchases + 1 WHERE product_id = %s", (product_id,))
        # Recalculate conversion rate: purchases/views * 100
        cursor.execute("SELECT purchases, views FROM product_engagement WHERE product_id = %s", (product_id,))
        purchases, views = cursor.fetchone()
        conversion_rate = (purchases / views * 100) if views > 0 else 0
        cursor.execute("UPDATE product_engagement SET conversion_rate = %s WHERE product_id = %s", (conversion_rate, product_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# Update average time spent
@app.route('/track_time', methods=['POST'])
def track_time():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    data = request.json
    product_id = get_product_id_by_title(data['title'])
    time_spent = int(data.get('time_spent', 0))
    if product_id and time_spent > 0:
        cursor = mysql.connection.cursor()
        # Get current avg and views
        cursor.execute("SELECT avg_time_seconds, views FROM product_engagement WHERE product_id = %s", (product_id,))
        avg_time, views = cursor.fetchone()
        # New average: (old_avg * (views-1) + new_time) / views
        new_avg = int(((avg_time * (views - 1)) + time_spent) / views) if views > 0 else time_spent
        cursor.execute("UPDATE product_engagement SET avg_time_seconds = %s WHERE product_id = %s", (new_avg, product_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# Update average rating
@app.route('/track_rating', methods=['POST'])
def track_rating():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Login required'}), 401
    data = request.json
    product_id = get_product_id_by_title(data['title'])
    rating = float(data.get('rating', 0))
    if product_id and 1 <= rating <= 5:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT avg_rating, rating_count FROM product_engagement WHERE product_id = %s", (product_id,))
        avg_rating, rating_count = cursor.fetchone()
        new_count = rating_count + 1
        new_avg = ((avg_rating * rating_count) + rating) / new_count if rating_count > 0 else rating
        cursor.execute("UPDATE product_engagement SET avg_rating = %s, rating_count = %s WHERE product_id = %s", (new_avg, new_count, product_id))
        mysql.connection.commit()
        cursor.close()
        return jsonify({'success': True})
    return jsonify({'success': False}), 400

# Update user preferences

# Track product view
@app.route('/track_view', methods=['POST'])
def track_product_view():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        data = request.get_json()
        user_id = session.get('user_id')
        product_id = data.get('product_id')
        
        cursor.execute('''
            INSERT INTO recently_viewed (user_id, product_id)
            VALUES (%s, %s)
        ''', (user_id, product_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Get recent feedback
@app.route('/get_recent_feedback')
def get_recent_feedback():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        
        cursor.execute('''
            SELECT uf.*, u.username 
            FROM user_feedback uf
            JOIN dressly_users u ON uf.user_id = u.id
            ORDER BY uf.created_at DESC
            LIMIT 5
        ''')
        
        feedback = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'feedback': feedback})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Submit review
@app.route('/submit_review', methods=['POST'])
def submit_review():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        data = request.get_json()
        user_id = session.get('user_id')
        product_id = data.get('product_id')
        rating = data.get('rating')
        review_text = data.get('review')
        
        cursor.execute('''
            INSERT INTO product_reviews (user_id, product_id, rating, review_text)
            VALUES (%s, %s, %s, %s)
        ''', (user_id, product_id, rating, review_text))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

        return jsonify({'success': False, 'error': str(e)}), 500

# Get chat support status
@app.route('/chat_support/status')
def chat_support_status():
    # Simulate chat support availability
    return jsonify({
        'success': True,
        'available': True,
        'wait_time': '2 minutes'
    })

@app.route('/test_db_structure')
def test_db_structure():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()
        db_structure = {}
        for (table_name,) in tables:
            cursor.execute(f"DESCRIBE {table_name}")
            columns = cursor.fetchall()
            db_structure[table_name] = [
                {
                    'Field': col[0],
                    'Type': col[1],
                    'Null': col[2],
                    'Key': col[3],
                    'Default': col[4],
                    'Extra': col[5]
                } for col in columns
            ]
        cursor.close()
        conn.close()
        return jsonify(db_structure)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/submit_rating', methods=['POST'])
def submit_rating():
    if 'username' not in session:
        return jsonify({'success': False, 'message': 'Login required'}), 401
    data = request.get_json()
    product_id = data.get('product_id')
    rating = data.get('rating')
    if not product_id or not rating:
        return jsonify({'success': False, 'message': 'Missing product or rating'}), 400
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        # Get current rating info
        cursor.execute('SELECT avg_rating, rating_count FROM product_engagement WHERE product_id = %s', (product_id,))
        result = cursor.fetchone()
        if result:
            avg_rating, rating_count = result
            rating_count = rating_count or 0
            avg_rating = float(avg_rating or 0)
            new_count = rating_count + 1
            new_avg = ((avg_rating * rating_count) + float(rating)) / new_count
            cursor.execute('UPDATE product_engagement SET avg_rating = %s, rating_count = %s WHERE product_id = %s', (new_avg, new_count, product_id))
        else:
            cursor.execute('INSERT INTO product_engagement (product_id, avg_rating, rating_count) VALUES (%s, %s, %s)', (product_id, float(rating), 1))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
