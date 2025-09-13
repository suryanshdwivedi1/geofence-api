# main.py
from fastapi import FastAPI
from pydantic import BaseModel
from geopy.distance import geodesic

# Create the main app object
app = FastAPI()

# --- Our "Database" of Risk Zones ---
RISK_ZONES = [
    {
        "name": "Downtown High-Crime Area",
        "lat": 28.7865,
        "lon": 77.4429,
        "radius_meters": 500,
        "risk": "red"
    },
    {
        "name": "Heavy Traffic Junction",
        "lat": 28.7890,
        "lon": 77.4350,
        "radius_meters": 750,
        "risk": "yellow"
    }
]

# --- Define the data models ---
# This tells FastAPI what the incoming data from the app should look like
class UserLocation(BaseModel):
    lat: float
    lon: float

# --- API Endpoints ---
# An "endpoint" is a specific URL the app can visit to get data.

# A simple endpoint to check if the API is online
@app.get("/")
def read_root():
    return {"status": "Geofence API is online"}

# Endpoint to give the app ALL zones to draw on a map
@app.get("/risk-zones")
def get_all_zones():
    return RISK_ZONES

# Endpoint to check a single user's location
@app.post("/check-location")
def check_user_location(location: UserLocation):
    user_coords = (location.lat, location.lon)

    for zone in RISK_ZONES:
        zone_coords = (zone["lat"], zone["lon"])
        distance = geodesic(user_coords, zone_coords).meters

        if distance <= zone["radius_meters"]:
            # User is inside this zone
            return {"status": "in_zone", "zone_name": zone["name"], "risk_level": zone["risk"]}

    # If the user is not in any zone
    return {"status": "safe", "risk_level": "none"}