import streamlit as st
import requests
import polyline
from geopy.distance import geodesic
import folium
from streamlit_folium import st_folium
import time

# ------------- FUNCTIONS -------------
def get_coords(city):
    url = f"https://nominatim.openstreetmap.org/search?q={city}&format=json&limit=1"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    data = response.json()
    if data:
        return float(data[0]['lat']), float(data[0]['lon'])
    return None, None

def get_route(start, end, ors_api_key):
    url = "https://api.openrouteservice.org/v2/directions/driving-car"
    headers = {"Authorization": ors_api_key, "Content-Type": "application/json"}
    body = {
        "coordinates": [[start[1], start[0]], [end[1], end[0]]],
        "instructions": False
    }
    res = requests.post(url, json=body, headers=headers)
    res.raise_for_status()
    data = res.json()
    return polyline.decode(data['routes'][0]['geometry'])

def get_mapmyindia_token(client_id, client_secret):
    token_url = "https://outpost.mapmyindia.com/api/security/oauth/token"
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret
    }
    res = requests.post(token_url, data=payload)
    return res.json().get("access_token")

def show_nearby_chargers(lat, lon, token):
    url = f"https://atlas.mapmyindia.com/api/places/nearby/json?keywords=ev+charging+station&refLocation={lat},{lon}"
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get(url, headers=headers)
    try:
        data = response.json()
    except:
        st.error("Failed to decode charger response")
        return []
    return data.get("suggestedLocations", [])

# ------------- STREAMLIT UI -------------
st.set_page_config(page_title="EV Trip Planner", layout="wide")
st.title("⚡ EV Trip Planner")

start_city = st.text_input("Enter Start City", "Nagpur")
end_city = st.text_input("Enter Destination City", "Pune")
ev_range_km = st.slider("EV Range (in km)", min_value=100, max_value=500, value=250, step=10)
safe_limit_km = int(ev_range_km * 0.8)

if st.button("Plan Trip"):
    start = get_coords(start_city)
    end = get_coords(end_city)

    if not all(start) or not all(end):
        st.error("Invalid city names")
        st.stop()

    st.success(f"Route from {start_city} to {end_city} being generated...")

    # ROUTE PATH
    ors_api_key = "<your_ors_api_key>"
    route_path = get_route(start, end, ors_api_key)

    # MapmyIndia Token
    client_id = "your_MapmyIndia_Token_client_id"
    client_secret = "<your_MapmyIndia_Token_client_secret>"
    token = get_mapmyindia_token(client_id, client_secret)

    st.markdown(f"""
    ### 📍 Start: {start[0]} {start[1]}
    ### 🏁 End: {end[0]} {end[1]}
    ### 📌 Route points count: {len(route_path)}
    """)

    # Plan stops
    stops = [("Start", route_path[0][0], route_path[0][1])]
    dist_covered = 0
    total_dist = 0
    prev_point = route_path[0]

    for point in route_path[1:]:
        seg_dist = geodesic(prev_point, point).km
        dist_covered += seg_dist
        total_dist += seg_dist
        prev_point = point

        if dist_covered >= safe_limit_km:
            st.markdown(f"""
            ### \n📍 At approx {point}
            🔍 Searching nearby EV charging stations...
            """)
            chargers = show_nearby_chargers(point[0], point[1], token)
            if chargers:
                st.markdown(f"🔋 Found {len(chargers)} nearby EV charging station(s):")
                for i, c in enumerate(chargers[:5]):
                    name = c.get("placeName", "Charger")
                    addr = c.get("placeAddress", "No address")
                    dist = c.get("distance", "N/A")
                    st.markdown(f"  {i+1}. **{name}** - {addr} ({dist} m)")
                ch = chargers[0]
                stops.append((ch.get("placeName", "Charger"), point[0], point[1]))
            else:
                st.warning("⚠️ No chargers found nearby.")
            st.markdown(f"🚗 Total distance covered so far: {int(total_dist)} km")
            dist_covered = 0
            time.sleep(1)

    stops.append(("Destination", route_path[-1][0], route_path[-1][1]))

    # Map
    # Create a Folium map centered on the start location
    m = folium.Map(location=[start[0], start[1]], zoom_start=7)
    # Add markers
    for name, lat, lon in stops:
        color = 'green' if name == "Destination" else 'blue'
        folium.Marker(
            location=[lat, lon],
            popup=folium.Popup(name, max_width=300),
            icon=folium.Icon(color=color)
        ).add_to(m)
    # Add polyline for route
    folium.PolyLine([(lat, lon) for _, lat, lon in stops], color="blue", weight=3).add_to(m)
    # Display map using streamlit-folium (important: assign the return)
    map_data = st_folium(m, width=1000, height=600, returned_objects=[])

    # Output
    st.subheader("📍 Stop Summary")
    for i, (name, lat, lon) in enumerate(stops):
        st.write(f"{i+1}. {name} at ({round(lat, 4)}, {round(lon, 4)})")
