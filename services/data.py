import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("OPENTRIP_API_KEY")

BASE = "https://api.opentripmap.com/0.1/en/places"

def get_landmarks(query):
    try:
        geo = requests.get(
            f"{BASE}/geoname",
            params={"name": query, "apikey": API_KEY},
            timeout=5
        ).json()

        if geo.get("status") != "OK":
            return []

        lat, lon = geo["lat"], geo["lon"]

        places = requests.get(
            f"{BASE}/radius",
            params={
                "radius": 10000,
                "lon": lon,
                "lat": lat,
                "limit": 5,
                "format": "json",
                "apikey": API_KEY
            },
            timeout=5
        ).json()

        return places

    except:
        return []