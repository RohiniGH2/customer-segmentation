import mysql.connector
from datetime import date, timedelta

# --- CONFIGURE THESE ---
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = ''
DB_NAME = 'dressly_db'

# --- Connect to MySQL ---
conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)
cursor = conn.cursor()

# --- Example ads data ---
ads_data = [
    # id is auto-increment, so not included
    # (product_id, title, description, image, target_segment, start_date, end_date, is_active)
    (1, 'Summer Sale', 'Get 30% off on all summer dresses!', 'static/yellow.jpg', 2, date.today(), date.today() + timedelta(days=30), 1),
    (2, 'New Arrivals', 'Check out our latest floral collection.', 'static/floral.jpg', 1, date.today(), date.today() + timedelta(days=45), 1),
    (3, 'Formal Event', 'Elegant dresses for your next event.', 'static/formalevent.jpg', 0, date.today(), date.today() + timedelta(days=60), 1),
    (4, 'Maxi Dress Offer', 'Special price on pink maxi dresses!', 'static/pinkmaxi.jpg', 3, date.today(), date.today() + timedelta(days=20), 1),
    (5, 'Workwear Edit', 'Upgrade your work wardrobe with our new arrivals.', 'static/pinkwork.jpg', None, date.today(), date.today() + timedelta(days=25), 1),
]

for ad in ads_data:
    cursor.execute('''
        INSERT INTO ads (product_id, title, description, image, target_segment, start_date, end_date, is_active)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    ''', ad)

conn.commit()
cursor.close()
conn.close()
print('Sample ads inserted into ads table.')
