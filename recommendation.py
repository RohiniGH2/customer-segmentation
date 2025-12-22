import pandas as pd
import numpy as np
import joblib
from sklearn.metrics.pairwise import cosine_similarity

# Load product data (dresses)
PRODUCTS_CSV = 'data.csv'  # Should contain all dresses with features: id, title, category, color, style, price, image, etc.

# Load clustered customer segments if available
CLUSTERED_CUSTOMERS_CSV = 'clustered_customers.csv'  # Should contain user_id, cluster, and possibly preferences

# Load KMeans model and scaler for customer segmentation
KMEANS_MODEL_PATH = 'kmeans_model.pkl'
SCALER_PATH = 'scaler.pkl'

# --- Data Loading ---
def load_products():
    return pd.read_csv(PRODUCTS_CSV)

def load_clustered_customers():
    try:
        return pd.read_csv(CLUSTERED_CUSTOMERS_CSV)
    except Exception:
        return None

def load_kmeans_and_scaler():
    try:
        kmeans = joblib.load(KMEANS_MODEL_PATH)
        scaler = joblib.load(SCALER_PATH)
        return kmeans, scaler
    except Exception:
        return None, None

# --- Recommendation Logic ---
def recommend_for_user(user_id=None, user_profile=None, history=None, quiz_answers=None, top_n=6):
    """
    Recommend dresses for a user based on their segment, history, and preferences.
    - user_id: ID of the user (to look up cluster/segment)
    - user_profile: dict with user features (age, income, etc.)
    - history: list of product IDs the user has viewed/purchased
    - quiz_answers: dict with quiz answers (favorite color, style, budget)
    - top_n: number of recommendations to return
    Returns: List of product dicts
    """
    products = load_products()
    clustered = load_clustered_customers()
    kmeans, scaler = load_kmeans_and_scaler()

    # 1. Segment the user (cluster)
    user_cluster = None
    if user_id and clustered is not None:
        row = clustered[clustered['id'] == user_id]
        if not row.empty:
            user_cluster = int(row.iloc[0]['Cluster'])
    elif user_profile and scaler is not None and kmeans is not None:
        # Predict cluster from profile
        features = np.array([[user_profile.get('Age', 30),
                              user_profile.get('Annual Income (k$)', 50),
                              user_profile.get('Spending Score (1-100)', 50)]])
        features_scaled = scaler.transform(features)
        user_cluster = int(kmeans.predict(features_scaled)[0])

    # 2. Filter by quiz/preferences
    filtered = products.copy()
    if quiz_answers:
        if 'favColor' in quiz_answers:
            filtered = filtered[filtered['color'].str.lower() == quiz_answers['favColor'].lower()]
        if 'favStyle' in quiz_answers:
            filtered = filtered[filtered['category'].str.lower() == quiz_answers['favStyle'].lower()]
        if 'budget' in quiz_answers:
            try:
                budget = float(quiz_answers['budget'])
                filtered = filtered[filtered['price'] <= budget]
            except Exception:
                pass

    # 3. If user has a cluster, boost products popular in that segment
    if user_cluster is not None and 'Cluster' in products.columns:
        filtered = filtered[filtered['Cluster'] == user_cluster]

    # 4. If user has history, use content-based similarity
    if history:
        # Get features for history items
        history_items = filtered[filtered['id'].isin(history)]
        if not history_items.empty:
            # Use color, category, style, price as features
            def get_features(df):
                # One-hot encode categorical, normalize price
                color_dummies = pd.get_dummies(df['color'], prefix='color')
                cat_dummies = pd.get_dummies(df['category'], prefix='cat')
                price_norm = (df['price'] - df['price'].min()) / (df['price'].max() - df['price'].min() + 1e-6)
                return pd.concat([color_dummies, cat_dummies, price_norm.rename('price_norm')], axis=1)
            prod_features = get_features(filtered)
            hist_features = get_features(history_items)
            sim = cosine_similarity(prod_features, hist_features)
            sim_scores = sim.mean(axis=1)
            filtered = filtered.copy()
            filtered['sim_score'] = sim_scores
            filtered = filtered.sort_values('sim_score', ascending=False)
            return filtered.head(top_n).to_dict(orient='records')

    # 5. Otherwise, recommend top-rated or most popular
    if 'popularity' in filtered.columns:
        filtered = filtered.sort_values('popularity', ascending=False)
    elif 'rating' in filtered.columns:
        filtered = filtered.sort_values('rating', ascending=False)
    else:
        filtered = filtered.sample(frac=1, random_state=42)  # Shuffle
    return filtered.head(top_n).to_dict(orient='records')

# --- Admin Recommendation for Ads ---
def recommend_for_ad_segment(cluster=None, style=None, color=None, price_range=None, top_n=3):
    """
    Recommend products for admin to advertise to a segment or preference group.
    """
    products = load_products()
    if cluster is not None and 'Cluster' in products.columns:
        products = products[products['Cluster'] == cluster]
    if style:
        products = products[products['category'].str.lower() == style.lower()]
    if color:
        products = products[products['color'].str.lower() == color.lower()]
    if price_range:
        min_p, max_p = price_range
        products = products[(products['price'] >= min_p) & (products['price'] <= max_p)]
    # Recommend most popular or random
    if 'popularity' in products.columns:
        products = products.sort_values('popularity', ascending=False)
    elif 'rating' in products.columns:
        products = products.sort_values('rating', ascending=False)
    else:
        products = products.sample(frac=1, random_state=42)
    return products.head(top_n).to_dict(orient='records')

# --- Example Usage ---
# recommendations = recommend_for_user(user_id=1, history=[101, 102], quiz_answers={'favColor': 'Red', 'budget': 100})
# admin_ads = recommend_for_ad_segment(cluster=2, style='Party', price_range=(50, 150))