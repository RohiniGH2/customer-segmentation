import csv
import random

# Simple recommendation system without ML dependencies
def load_products_simple():
    """Load products from CSV without pandas"""
    products = []
    try:
        with open('data.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                products.append(row)
    except FileNotFoundError:
        # Return dummy data if CSV not found
        products = [
            {'id': '1', 'name': 'Summer Dress', 'category': 'dress', 'price': '29.99'},
            {'id': '2', 'name': 'Evening Gown', 'category': 'formal', 'price': '89.99'},
            {'id': '3', 'name': 'Casual Top', 'category': 'casual', 'price': '19.99'},
        ]
    return products

def get_recommendations_simple(user_id=None, limit=6):
    """Simple recommendation without ML"""
    products = load_products_simple()
    # Return random products for now
    return random.sample(products, min(limit, len(products)))

def get_trending_products_simple(limit=6):
    """Get trending products without ML"""
    products = load_products_simple()
    return products[:limit]