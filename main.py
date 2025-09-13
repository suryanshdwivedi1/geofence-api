import os
from fastapi import FastAPI
from pydantic import BaseModel
from geopy.distance import geodesic
from supabase import create_client, Client

# --- Connect to your Supabase database ---
# This is the corrected section. It looks for the variables by their NAME.
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# Now, we create the client. This will only work if the variables are found.
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
    """
    Fetches ALL zones directly from the Supabase database.
    This is now live data!
    """
    response = supabase.table('zones').select("*").execute()
    return response.data

@app.post("/check-location")
def check_user_location(location: UserLocation):
    """
    Checks a user's location against the LIVE zones from the database.
    """
    user_coords = (location.lat, location.lon)

    # Fetch the latest zones from the database on every single check.
    response = supabase.table('zones').select("*").execute()
    live_risk_zones = response.data

    # Find the highest risk zone the user is in
    highest_risk = {"level": "none", "name": "Safe Area"}
    risk_priority = {"red": 3, "yellow": 2, "green": 1, "none": 0}

    for zone in live_risk_zones:
        zone_coords = (zone["lat"], zone["lon"])
        distance = geodesic(user_coords, zone_coords).meters

        if distance <= zone["radius_meters"]:
            # User is inside this zone. Is it higher risk than what we've already found?
            if risk_priority.get(zone["risk"], 0) > risk_priority.get(highest_risk["level"], 0):
                highest_risk["level"] = zone["risk"]
                highest_risk["name"] = zone["name"]

    if highest_risk["level"] != "none":
        return {"status": "in_zone", "zone_name": highest_risk["name"], "risk_level": highest_risk["level"]}
    else:
        return {"status": "safe", "risk_level": "none"}
