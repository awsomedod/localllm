import os
import requests
import json
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

def get_house_votes(congress: int):
    url = f"https://api.congress.gov/v3/house-vote/{congress}"
    votes = []
    offset = 0
    while True:
        params = {
            "api_key": os.getenv("CONGRESS_API_KEY"),
            "format": "json",
            "congress": congress,
            "limit": 250,
            "offset": offset,
            }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        votes.extend(data.get("houseRollCallVotes") or [])
        if not data.get("pagination", {}).get("next"):
            break
        offset += 250
    return votes


house_votes = get_house_votes(118)
print(json.dumps(house_votes[0], indent=4))
print(len(house_votes))