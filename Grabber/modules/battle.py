import requests
import random

def post(dest, alias=None):
    api_keys = ["76ef2764a4226c30987b389802f7912617e5d57d"]#mera
    api_key = random.choice(api_keys)
    base_url = "https://publicearn.com/api"
    payload = {
        "api": api_key,
        "url": dest
    }

    if alias:
        payload["alias"] = alias

    try:
        response = requests.get(base_url, params=payload)
        data = response.json()
        if data['status'] == "success":
            return True, data['shortenedUrl']
        else:
            return False, 'Cannot Generate Shortened URL, Contact Owner.'
    except Exception as e:
        return False, str(e)