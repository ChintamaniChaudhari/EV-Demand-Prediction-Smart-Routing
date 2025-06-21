# clustering.py
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import joblib

def load_data(path):
    df = pd.read_excel(path, sheet_name='ev_locations')
    return df[['latitude', 'longitude']].dropna()

def preprocess_data(data):
    scaler = StandardScaler()
    scaled_data = scaler.fit_transform(data)
    return scaled_data, scaler

def train_kmeans(scaled_data, n_clusters=3):
    model = KMeans(n_clusters=n_clusters, random_state=42)
    model.fit(scaled_data)
    return model

def calculate_silhouette_score(data, labels):
    score = silhouette_score(data, labels)
    return score

def save_model(model, scaler, model_path='models/kmeans_model.pkl'):
    joblib.dump({'model': model, 'scaler': scaler}, model_path)

def main():
    df = load_data('data/ev_stations.xlsx')
    scaled_data, scaler = preprocess_data(df)
    model = train_kmeans(scaled_data, n_clusters=3)
    save_model(model, scaler)

if __name__ == "__main__":
    main()
