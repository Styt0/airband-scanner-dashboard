import requests
from config import config

def check_tor_connectivity():
    try:
        proxies = {
            'http': config.TOR_PROXY,
            'https': config.TOR_PROXY
        }
        response = requests.get('https://check.torproject.org/', proxies=proxies, timeout=10)
        if "Congratulations. This browser is configured to use Tor." in response.text:
            return True, "Tor is configured correctly."
        else:
            return False, "Tor is not configured correctly."
    except Exception as e:
        return False, f"Tor connectivity error: {e}"

if __name__ == "__main__":
    is_connected, message = check_tor_connectivity()
    print(message)
