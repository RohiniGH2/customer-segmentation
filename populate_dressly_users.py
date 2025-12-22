import csv
import mysql.connector
from werkzeug.security import generate_password_hash

# --- CONFIGURE THESE ---
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'dressly_db'
CSV_FILE = 'clustered_customers.csv'
DEFAULT_PASSWORD = 'Dressly@2025'

# --- Connect to MySQL ---
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = conn.cursor()x

# --- Read CSV and Insert Users ---
with open(CSV_FILE, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        customer_id = int(row['CustomerID'])
        username = f"user{customer_id}"
        email = f"user{customer_id}@dressly.com"
        password_hash = generate_password_hash(DEFAULT_PASSWORD)

        # Skip admin and RohiniGH2 if present
        if username.lower() in ['admin', 'rohiniGH2']:
            continue

        # Insert user if not exists (ignore duplicates)
        cursor.execute('''
            INSERT IGNORE INTO dressly_users (username, email, password_hash)
            VALUES (%s, %s, %s)
        ''', (username, email, password_hash))

conn.commit()
cursor.close()
conn.close()
print('All customer credential records inserted/updated in dressly_users.')
