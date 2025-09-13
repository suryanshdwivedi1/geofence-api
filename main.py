import os
from fastapi import FastAPI
from pydantic import BaseModel
from geopy.distance import geodesic
from supabase import create_client, Client

# --- Connect to your Supabase database ---
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- FastAPI App ---
app = FastAPI()

class UserLocation(BaseModel):
    lat: float
    lon: float

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "Live Geofence API is online"}

@app.get("/risk-zones")
def get_all_zones():
    response = supabase.table('zones').select("*").execute()
    return response.data

@app.post("/check-location")
def check_user_location(location: UserLocation):
    # --- START OF DEBUG CODE ---
    print("--- NEW REQUEST RECEIVED ---")
    print(f"Received coordinates from frontend: lat={location.lat}, lon={location.lon}")
    # --- END OF DEBUG CODE ---

    user_coords = (location.lat, location.lon)

    response = supabase.table('zones').select("*").execute()
    live_risk_zones = response.data

    # --- START OF DEBUG CODE ---
    print(f"Fetched {len(live_risk_zones)} zones from the Supabase database.")
    if not live_risk_zones:
        print("!!! WARNING: The list of zones from the database is EMPTY. Check RLS policies in Supabase. !!!")
    # --- END OF DEBUG CODE ---

    highest_risk = {"level": "none", "name": "Safe Area"}
    risk_priority = {"red": 3, "yellow": 2, "green": 1, "none": 0}

    for zone in live_risk_zones:
        # --- START OF DEBUG CODE ---
        print(f"\nChecking against zone: '{zone.get('name', 'N/A')}'")
        # --- END OF DEBUG CODE ---
        
        zone_lat = zone.get('lat')
        zone_lon = zone.get('lon')
        zone_radius = zone.get('radius_meters')
        zone_risk = zone.get('risk')

        # Type checking to be extra safe
        if isinstance(zone_lat, (int, float)) and isinstance(zone_lon, (int, float)):
            zone_coords = (zone_lat, zone_lon)
            distance = geodesic(user_coords, zone_coords).meters

            # --- START OF DEBUG CODE ---
            print(f"  - Zone Coords: {zone_coords} | User Coords: {user_coords}")
            print(f"  - Calculated Distance: {distance:.2f} meters")
            print(f"  - Zone Radius: {zone_radius} meters")
            print(f"  - Condition check: is {distance:.2f} <= {zone_radius}? -> {distance <= zone_radius}")
            # --- END OF DEBUG CODE ---

            if distance <= zone_radius:
                if risk_priority.get(zone_risk, 0) > risk_priority.get(highest_risk["level"], 0):
                    highest_risk["level"] = zone_risk
                    highest_risk["name"] = zone.get('name')
                    # --- START OF DEBUG CODE ---
                    print(f"  ---> NEW HIGHEST RISK FOUND: {highest_risk}")
                    # --- END OF DEBUG CODE ---
        else:
            # --- START OF DEBUG CODE ---
            print(f"  - !!! SKIPPING ZONE: Invalid coordinates in database. lat={zone_lat}, lon={zone_lon} !!!")
            # --- END OF DEBUG CODE ---


    print(f"\n--- FINAL DECISION: {highest_risk} ---")
    if highest_risk["level"] != "none":
        return {"status": "in_zone", "zone_name": highest_risk["name"], "risk_level": highest_risk["level"]}
    else:
        return {"status": "safe", "risk_level": "none"}

