import mysql.connector
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import random

def get_db_connection():
    return mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='dressly_db'
    )

def populate_products():
    products = [
        ('Red Party Dress', 'Elegant and bold party dress', 149.99, 'Party', 'red.jpg'),
        ('Blue Formal Dress', 'Statement piece for galas', 199.99, 'Formal', 'blue.jpg'),
        ('Pink Maxi Dress', 'Flowy and elegant maxi dress', 179.99, 'Maxi', 'pinkmaxi.jpg'),
        ('Green Mini Dress', 'Fun and flirty for parties', 129.99, 'Party', 'green.jpg'),
        ('Yellow Summer Dress', 'Bright and playful for sunny days', 89.99, 'Summer', 'yellow.jpg'),
        ('Beige Work Dress', 'Chic and comfortable for the office', 159.99, 'Work', 'beige.jpg'),
        ('Black Formal Dress', 'Classic formal evening wear', 249.99, 'Formal', 'black.jpg'),
        ('White Casual Dress', 'Perfect for casual outings', 79.99, 'Casual', 'whitecasual.jpg'),
        ('Floral Summer Dress', 'Beautiful floral pattern', 119.99, 'Summer', 'floral.jpg'),
        ('Pink Work Dress', 'Professional and stylish', 169.99, 'Work', 'pinkwork.jpg')
    ]
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for product in products:
        cursor.execute('''
            INSERT INTO products (title, description, price, category, image)
            VALUES (%s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            description=VALUES(description), price=VALUES(price),
            category=VALUES(category), image=VALUES(image)
        ''', product)
    
    conn.commit()
    cursor.close()
    conn.close()

def populate_orders():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user IDs
    cursor.execute('SELECT id FROM dressly_users')
    user_ids = [row[0] for row in cursor.fetchall()]
    
    # Get product IDs
    cursor.execute('SELECT id, price FROM products')
    products = cursor.fetchall()
    
    for user_id in user_ids:
        # Create 1-3 orders for each user
        for _ in range(random.randint(1, 3)):
            order_date = datetime.now() - timedelta(days=random.randint(1, 30))
            # Select 1-3 products for each order
            order_products = random.sample(products, random.randint(1, 3))
            total_amount = sum(product[1] for product in order_products)
            
            cursor.execute('''
                INSERT INTO orders (user_id, total_amount, shipping_address, status, created_at)
                VALUES (%s, %s, %s, %s, %s)
            ''', (user_id, total_amount, '123 Main St, City, Country', 'Delivered', order_date))
            
            order_id = cursor.lastrowid
            
            # Add order items
            for product in order_products:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, price)
                    VALUES (%s, %s, %s, %s)
                ''', (order_id, product[0], 1, product[1]))
    
    conn.commit()
    cursor.close()
    conn.close()

def populate_user_preferences():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    colors = ['Red', 'Blue', 'Black', 'White', 'Yellow', 'Green', 'Pink', 'Beige']
    styles = ['Party', 'Casual', 'Formal', 'Work', 'Summer', 'Maxi', 'Midi', 'Mini']
    
    cursor.execute('SELECT id FROM dressly_users')
    user_ids = [row[0] for row in cursor.fetchall()]
    
    for user_id in user_ids:
        cursor.execute('''
            INSERT INTO user_preferences (user_id, favorite_color, preferred_style, budget)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            favorite_color=VALUES(favorite_color), preferred_style=VALUES(preferred_style),
            budget=VALUES(budget)
        ''', (user_id, random.choice(colors), random.choice(styles), random.randint(50, 300)))
    
    conn.commit()
    cursor.close()
    conn.close()

def populate_reviews():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Get user and product IDs
    cursor.execute('SELECT id FROM dressly_users')
    user_ids = [row[0] for row in cursor.fetchall()]
    
    cursor.execute('SELECT id FROM products')
    product_ids = [row[0] for row in cursor.fetchall()]
    
    reviews = [
        "Absolutely love this dress! The fit is perfect.",
        "Great quality and beautiful design.",
        "Comfortable and stylish, exactly what I wanted.",
        "The color is stunning in person.",
        "Perfect for special occasions!",
        "Very comfortable for office wear.",
        "Excellent quality for the price.",
        "The dress exceeded my expectations!",
        "Beautiful dress, gets lots of compliments.",
        "Perfect fit and very flattering."
    ]
    
    for user_id in user_ids:
        # Add 1-3 reviews per user
        for _ in range(random.randint(1, 3)):
            cursor.execute('''
                INSERT INTO product_reviews (user_id, product_id, rating, review_text)
                VALUES (%s, %s, %s, %s)
            ''', (user_id, random.choice(product_ids), random.randint(4, 5), random.choice(reviews)))
    
    conn.commit()
    cursor.close()
    conn.close()

def populate_offers():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    offers = [
        ('15% OFF on your next purchase!', 'Limited time offer', 15, 0),
        ('Free shipping on orders over $100', 'No minimum purchase required', 0, 100),
        ('20% OFF on formal dresses', 'Weekend special', 20, 150),
        ('Buy one get one 50% OFF', 'Special promotion', 50, 200),
        ('Extra 10% OFF for members', 'Member exclusive', 10, 0)
    ]
    
    for offer in offers:
        cursor.execute('''
            INSERT INTO offers (title, description, discount_percent, min_purchase, valid_from, valid_until, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, TRUE)
        ''', (*offer, datetime.now(), datetime.now() + timedelta(days=30)))
    
    conn.commit()
    cursor.close()
    conn.close()

def populate_user_feedback():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT id FROM dressly_users')
    user_ids = [row[0] for row in cursor.fetchall()]
    
    feedback_texts = [
        "Great selection of dresses!",
        "The website is very easy to use.",
        "Love the personalized recommendations!",
        "Amazing customer service experience.",
        "Very happy with my purchases.",
        "Quick delivery and great packaging.",
        "The style quiz is really helpful.",
        "Best online dress shopping experience.",
        "Excellent quality products.",
        "Very satisfied with my shopping experience."
    ]
    
    for user_id in user_ids:
        cursor.execute('''
            INSERT INTO user_feedback (user_id, feedback_text)
            VALUES (%s, %s)
        ''', (user_id, random.choice(feedback_texts)))
    
    conn.commit()
    cursor.close()
    conn.close()

def main():
    print("Populating test data...")
    populate_products()
    print("Products added...")
    populate_orders()
    print("Orders added...")
    populate_user_preferences()
    print("User preferences added...")
    populate_reviews()
    print("Reviews added...")
    populate_offers()
    print("Offers added...")
    populate_user_feedback()
    print("Feedback added...")
    print("All test data has been populated successfully!")

if __name__ == "__main__":
    main()
