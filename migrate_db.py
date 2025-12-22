# Database Migration Script - MySQL to PostgreSQL
# Run this script to convert your existing MySQL database to PostgreSQL format

import os
import csv
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

load_dotenv()

def get_db_connection():
    conn = psycopg2.connect(
        host=os.environ.get('DB_HOST', 'localhost'),
        user=os.environ.get('DB_USER', 'postgres'),
        password=os.environ.get('DB_PASSWORD', ''),
        database=os.environ.get('DB_NAME', 'dressly_db'),
        port=int(os.environ.get('DB_PORT', 5432))
    )
    return conn

def create_tables():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        category VARCHAR(100),
        image_url VARCHAR(500),
        stock_quantity INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    # Create ads table
    cursor.execute('''CREATE TABLE IF NOT EXISTS ads (
        id SERIAL PRIMARY KEY,
        title VARCHAR(255) NOT NULL,
        content TEXT,
        image_url VARCHAR(500),
        target_audience VARCHAR(100),
        is_active BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        valid_from TIMESTAMP,
        valid_until TIMESTAMP
    )''')
    
    # Create carts table
    cursor.execute('''CREATE TABLE IF NOT EXISTS carts (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL,
        is_ordered BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES dressly_users(id)
    )''')
    
    # Create cart_items table
    cursor.execute('''CREATE TABLE IF NOT EXISTS cart_items (
        id SERIAL PRIMARY KEY,
        cart_id INTEGER NOT NULL,
        product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL DEFAULT 1,
        FOREIGN KEY (cart_id) REFERENCES carts(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )''')
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Tables created successfully!")

if __name__ == "__main__":
    create_tables()