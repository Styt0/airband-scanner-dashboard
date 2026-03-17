import os
import time
import requests
from dotenv import load_dotenv

# Load configuration
load_dotenv()
API_KEY = os.getenv("TOMTOM_API_KEY")
BASE_URL = "https://api.tomtom.com/traffic/services/4/incidentDetails/s3"

def check_traffic(bbox):
    """
    Checks for traffic incidents within a bounding box.
    BBOX format: minLon,minLat,maxLon,maxLat
    Example BeNeLux: 2.5,49.4,7.2,53.5
    """
    if not API_KEY or API_KEY == "YOUR_KEY_HERE":
        print("[ERROR] TomTom API Key is not set in .env")
        return

    params = {
        "key": API_KEY,
        "bbox": bbox,
        "fields": "{incidents{type,geometry{type,coordinates},properties{description,delay,magnitude,length}}}",
        "language": "en-GB"
    }

    try:
        response = requests.get(BASE_URL, params=params)
        if response.status_code == 200:
            data = response.json()
            incidents = data.get("incidents", [])
            print(f"[INFO] Found {len(incidents)} incidents in monitored area.")
            for inc in incidents:
                props = inc.get("properties", {})
                print(f" - [{props.get('magnitude')}] {props.get('description')}")
        else:
            print(f"[ERROR] API returned status {response.status_code}: {response.text}")
    except Exception as e:
        print(f"[ERROR] Request failed: {e}")

if __name__ == "__main__":
    # Example area: Brussels center
    BBOX_BRUSSELS = "4.3,50.8,4.4,50.9"
    print("GeoSentinel Traffic Monitor Starting...")
    while True:
        check_traffic(BBOX_BRUSSELS)
        time.sleep(300) # Check every 5 minutes
