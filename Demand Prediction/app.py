import streamlit as st
import pandas as pd
import joblib
from sklearn.cluster import KMeans
from preprocessing.preprocess import scale_coordinates
from visualization.plots import plot_clusters
from sklearn.metrics import silhouette_score


# --- Page Config ---
st.set_page_config(page_title="EV Clustering by City", layout="centered")

# --- Title ---
st.title("🔋 EV Charging Station Clustering")
st.markdown("Identify **EV hot cities** and optimize station clusters using location data.")

# --- Upload File ---
st.sidebar.header("⚙️ Upload or Use Sample Data")
uploaded_file = st.sidebar.file_uploader("Upload EV Stations Excel file", type=["xlsx"])

if uploaded_file:
    df = pd.read_excel(uploaded_file, sheet_name='ev_locations')
else:
    df = pd.read_excel("data/ev_stations.xlsx", sheet_name='ev_locations')

# --- Data Cleaning ---
if not {'latitude', 'longitude', 'city'}.issubset(df.columns):
    st.error("The file must contain 'latitude', 'longitude', and 'city' columns.")
    st.stop()

df = df[['latitude', 'longitude', 'city', 'name']].dropna()

# --- Hot City Detection ---
st.sidebar.header("📍 City Selection")
city_counts = df['city'].value_counts()
hot_cities = city_counts[city_counts >= 10].index.tolist()

if not hot_cities:
    st.error("❌ No cities with enough EV stations (≥10) found.")
    st.stop()

selected_city = st.sidebar.selectbox("Select a Hot City", sorted(hot_cities))
city_df = df[df['city'] == selected_city]

if len(city_df) < 3:
    st.warning(f"{selected_city} has too few stations to cluster.")
    st.stop()

# --- Cluster Count Selection ---
max_clusters = min(10, len(city_df))
k = st.sidebar.slider("Number of Clusters", 2, max_clusters, 3)

# --- Clustering ---
scaled_data, scaler = scale_coordinates(city_df)
kmeans = KMeans(n_clusters=k, random_state=42)
city_df['Cluster'] = kmeans.fit_predict(scaled_data)

# --- Output ---
st.subheader(f"📊 Clusters in **{selected_city}** (K={k})")

# --- Map View ---
st.map(city_df[['latitude', 'longitude']])

# --- Cluster Plot ---
fig = plot_clusters(city_df, k)
st.pyplot(fig)

# --- Data View ---
with st.expander("📄 View Clustered Station Data"):
    st.dataframe(city_df)
    
# After predicting clusters
score = silhouette_score(scaled_data, city_df['Cluster'])
st.success(f"🧠 Silhouette Score: {score:.3f}")

# --- Footer ---
st.markdown("---")
st.markdown("Made to improve EV infrastructure planning.")
