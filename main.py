import pandas as pd
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
from geopy.distance import geodesic
import folium
from PyQt5 import QtWidgets, QtWebEngineWidgets
import time

# Step 1: Read CSV File
df = pd.read_csv('testData.csv')

# Step 2: Geocode Addresses
geolocator = Nominatim(user_agent="geo_mapper")

def geocode_address(address, retries=5):
    for i in range(retries):
        try:
            location = geolocator.geocode(address, timeout=10)
            if location:
                return (location.latitude, location.longitude)
            else:
                return (None, None)
        except (GeocoderTimedOut, GeocoderServiceError):
            print(f"Retrying ({i+1}/{retries})...")
            time.sleep(2 ** i)  # Exponential backoff
    return (None, None)

# Add latitude and longitude columns
df['coordinates'] = df['address'].apply(geocode_address)
df = df.dropna(subset=['coordinates'])
df[['latitude', 'longitude']] = pd.DataFrame(df['coordinates'].tolist(), index=df.index)

# Step 3: Group by Distance
threshold = 10  # Distance in kilometers
groups = []

def calculate_distance(loc1, loc2):
    return geodesic(loc1, loc2).kilometers

for index, row in df.iterrows():
    location = (row['latitude'], row['longitude'])
    added = False
    for group in groups:
        if calculate_distance(location, group[0]) < threshold:
            group.append(location)
            added = True
            break
    if not added:
        groups.append([location])

# Step 4: Display on GUI Map
class MapWindow(QtWidgets.QMainWindow):
    def __init__(self, map_html):
        super().__init__()
        self.setWindowTitle('Location Map')
        self.browser = QtWebEngineWidgets.QWebEngineView()
        self.browser.setHtml(map_html)
        self.setCentralWidget(self.browser)

# Create a folium map
map_center = [df['latitude'].mean(), df['longitude'].mean()]
map = folium.Map(location=map_center, zoom_start=12)

# Add markers to the map
for group in groups:
    for loc in group:
        folium.Marker(location=loc).add_to(map)

# Save the map as HTML
map.save('map.html')

# Display the map in a PyQt GUI
app = QtWidgets.QApplication([])
window = MapWindow(open('map.html').read())
window.show()
app.exec_()

