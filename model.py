import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import joblib

# 1. Load the data
data = pd.read_csv('data.csv')

# 2. Preprocess the data
# Example: Assume columns like 'Age', 'Annual Income', 'Spending Score'
# Modify these columns as per your actual data.csv
features = ['Age', 'Annual Income (k$)', 'Spending Score (1-100)']
X = data[features]

# Handle missing values if any
X = X.fillna(X.mean())

# Scale features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 3. Apply KMeans clustering
kmeans = KMeans(n_clusters=4, random_state=42)  # You can choose the number of clusters
clusters = kmeans.fit_predict(X_scaled)

# Add cluster labels to the original data (optional, for admin analysis)
data['Cluster'] = clusters

# 4. Save the model and scaler for use in Flask app
joblib.dump(kmeans, 'kmeans_model.pkl')
joblib.dump(scaler, 'scaler.pkl')

# 5. (Optional) Save clustered data for admin dashboard
data.to_csv('clustered_customers.csv', index=False)

print("Model trained and saved. Number of clusters:", kmeans.n_clusters)