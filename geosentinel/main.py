import time
from config import config
from utils import check_tor_connectivity

def main():
    print("GeoSentinel (Geospatial Monitoring & OSINT) Initialized")
    print("-" * 50)
    
    try:
        config.validate()
        print("Configuration validated.")
    except ValueError as e:
        print(f"Configuration error: {e}")
        return

    print(f"TomTom API Key: {config.TOMTOM_API_KEY[:5]}...")
    print(f"Tor Proxy: {config.TOR_PROXY}")
    print(f"Ollama Host: {config.OLLAMA_HOST}")
    print(f"Data Directory: {config.DATA_DIR}")

    print("-" * 50)
    print("Checking Tor connectivity...")
    is_connected, message = check_tor_connectivity()
    print(message)

    print("-" * 50)
    print("Monitoring active. Waiting for input/triggers...")
    
    while True:
        # Main monitoring loop
        time.sleep(60)

if __name__ == "__main__":
    main()
