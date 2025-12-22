import pandas as pd
import numpy as np
from datetime import datetime

# Color palette for reference (for frontend):
# --chocolate-cosmos: #412220
# --wine: #69212D
# --cordovan: #8C2F39
# --redwood: #B23A48
# --light-coral: #D77A7D

# --- Data Loading ---
def load_products():
    return pd.read_csv('data.csv')

def load_user_events():
    """
    Should return a DataFrame with columns:
    user_id, product_id, event_type (view, add_to_cart, purchase), timestamp, duration (for view)
    """
    try:
        return pd.read_csv('user_events.csv')
    except Exception:
        # Return empty DataFrame if not found
        return pd.DataFrame(columns=['user_id','product_id','event_type','timestamp','duration'])

def load_users():
    try:
        return pd.read_csv('users.csv')
    except Exception:
        return pd.DataFrame(columns=['id','username','email','role','cluster'])

# --- 1. Product Engagement ---
def get_product_engagement():
    events = load_user_events()
    products = load_products()
    # Views
    view_counts = events[events['event_type']=='view'].groupby('product_id').size().rename('views')
    # Time spent
    avg_time = events[events['event_type']=='view'].groupby('product_id')['duration'].mean().rename('avg_time_spent')
    # Add to cart
    add_counts = events[events['event_type']=='add_to_cart'].groupby('product_id').size().rename('add_to_cart')
    # Purchases
    buy_counts = events[events['event_type']=='purchase'].groupby('product_id').size().rename('purchases')
    # Merge
    engagement = pd.DataFrame(index=products['id'])
    engagement = engagement.join([view_counts, avg_time, add_counts, buy_counts])
    engagement = engagement.fillna(0)
    # Conversion rate
    engagement['conversion_rate'] = np.where(engagement['views']>0, engagement['purchases']/engagement['views'], 0)
    # Add product info
    engagement = engagement.join(products.set_index('id')[['title','category','color','price']])
    return engagement.reset_index()

# --- 2. User Behavior ---
def get_user_behavior():
    events = load_user_events()
    users = load_users()
    # Most active users
    active = events.groupby('user_id').size().rename('activity_count')
    # Browsing history
    history = events[events['event_type']=='view'].groupby('user_id')['product_id'].apply(list).rename('browsing_history')
    # Purchase history
    purchases = events[events['event_type']=='purchase'].groupby('user_id')['product_id'].apply(list).rename('purchase_history')
    # Merge
    behavior = pd.DataFrame(index=users['id'])
    behavior = behavior.join([active, history, purchases])
    behavior = behavior.join(users.set_index('id')[['username','role','cluster']], how='left')
    behavior = behavior.fillna({'activity_count':0, 'browsing_history':[], 'purchase_history':[]})
    return behavior.reset_index()

# --- 3. Sales & Trends ---
def get_sales_trends():
    events = load_user_events()
    products = load_products()
    # Top sellers
    top_sellers = events[events['event_type']=='purchase'].groupby('product_id').size().sort_values(ascending=False)
    # Sales over time
    events['date'] = pd.to_datetime(events['timestamp']).dt.date
    sales_by_day = events[events['event_type']=='purchase'].groupby('date').size()
    # Abandoned cart: viewed but not purchased
    viewed = events[events['event_type']=='view'].groupby('user_id')['product_id'].apply(set)
    bought = events[events['event_type']=='purchase'].groupby('user_id')['product_id'].apply(set)
    abandoned = {uid: list(viewed.get(uid,set()) - bought.get(uid,set())) for uid in viewed.index}
    # Repeat purchase rate
    repeat = events[events['event_type']=='purchase'].groupby('user_id')['product_id'].nunique().rename('unique_products')
    repeat_rate = (repeat>1).mean()
    return {
        'top_sellers': top_sellers.head(10).to_dict(),
        'sales_by_day': sales_by_day.to_dict(),
        'abandoned_cart': abandoned,
        'repeat_purchase_rate': repeat_rate
    }

# --- 4. Marketing & Recommendations ---
def get_marketing_stats():
    events = load_user_events()
    # Ad clicks (assume event_type 'ad_click')
    ad_clicks = events[events['event_type']=='ad_click'].groupby('product_id').size().rename('ad_clicks')
    # Recommendation clicks (assume event_type 'rec_click')
    rec_clicks = events[events['event_type']=='rec_click'].groupby('product_id').size().rename('rec_clicks')
    # Coupon usage (assume event_type 'coupon_used')
    coupon = events[events['event_type']=='coupon_used'].groupby('product_id').size().rename('coupon_used')
    stats = pd.concat([ad_clicks, rec_clicks, coupon], axis=1).fillna(0)
    return stats.reset_index()

# These functions can be called from your Flask admin dashboard route to display analytics.
