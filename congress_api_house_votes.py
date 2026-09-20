import os
import re
import html
import requests
import json
from dotenv import load_dotenv
load_dotenv()

BILL_TYPES = {"HR", "S", "HJRES", "SJRES", "HCONRES", "SCONRES", "HRES", "SRES"}

def get_house_votes(congress: int, max_votes=None):
    url = f"https://api.congress.gov/v3/house-vote/{congress}"
    votes = []
    offset = 0
    while True:
        print(f"Fetching votes for congress {congress} with offset {offset}")
        # 250 is the API's ceiling, but ask for less when only a sample is wanted.
        page_size = 250 if max_votes is None else min(250, max_votes - len(votes))
        params = {
            "api_key": os.getenv("CONGRESS_API_KEY"),
            "format": "json",
            "congress": congress,
            "limit": page_size,
            "offset": offset,
            }
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        votes.extend(data.get("houseRollCallVotes") or [])
        # next is always set while records remain, so a sample has to stop itself.
        reached_max_votes = max_votes is not None and len(votes) >= max_votes
        if reached_max_votes or not data.get("pagination", {}).get("next"):
            break
        offset += page_size
    return votes


def get_vote_positions(congress: int, session_number: int, roll_call_number: int):
    url = f"https://api.congress.gov/v3/house-vote/{congress}/{session_number}/{roll_call_number}/members"
    params = {
        "api_key": os.getenv("CONGRESS_API_KEY"),
        "format": "json",
        "limit": 250,
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    results = (data.get("houseRollCallVoteMemberVotes") or {}).get("results") or []
    return [
        {
            "bioguide_id": position.get("bioguideID"),
            "vote_cast": position.get("voteCast"),
        }
        for position in results
    ]


def get_text_versions(congress: int, legislation_type: str, legislation_number: str):
    bill_type = legislation_type.lower()
    url = f"https://api.congress.gov/v3/bill/{congress}/{bill_type}/{legislation_number}/text"
    params = {
        "api_key": os.getenv("CONGRESS_API_KEY"),
        "format": "json",
    }
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    return response.json().get("textVersions")


def pick_text_version(text_versions, vote_date=None):
    # Versions carry the date of the action they belong to, so the text that was
    # voted on is the newest one published on or before the vote.
    candidates = list(enumerate(text_versions))
    if vote_date:
        on_or_before = [
            (index, version)
            for index, version in candidates
            if (version.get("date") or "")[:10] <= vote_date[:10]
        ]
        candidates = on_or_before or candidates
    if not candidates:
        return None
    return max(candidates, key=lambda pair: ((pair[1].get("date") or ""), pair[0]))[1]


def get_full_text(text_version):
    formats = {item.get("type"): item.get("url") for item in text_version.get("formats") or []}
    source_url = formats.get("Formatted Text")

    # congress.gov throttles bulk text downloads, so pull the same file from GovInfo.
    package_id = source_url.rsplit("/", 1)[-1].rsplit(".", 1)[0]
    govinfo_url = f"https://www.govinfo.gov/content/pkg/{package_id}/html/{package_id}.htm"

    response = requests.get(govinfo_url, timeout=30)
    response.raise_for_status()
    text = html.unescape(re.sub(r"<[^>]+>", "", response.text)).strip()
    return package_id, text


def get_legislation_text(congress: int, legislation_type: str, legislation_number: str, vote_date):
    text_versions = get_text_versions(congress, legislation_type, legislation_number)
    text_version = pick_text_version(text_versions, vote_date)

    package_id, full_text = get_full_text(text_version)
    return {
        "version_type": text_version.get("type"),
        "version_date": text_version.get("date"),
        "package_id": package_id,
        "full_text": full_text,
    }


def get_house_votes_with_details(votes, count: int):
    text_cache = {}
    for vote in votes:
        count += 1
        print(f"Getting vote positions for vote {count}")
        vote["positions"] = get_vote_positions(
            vote["congress"],
            vote["sessionNumber"],
            vote["rollCallNumber"],
        )

        legislation_type = vote.get("legislationType")
        legislation_number = vote.get("legislationNumber")
        if legislation_type not in BILL_TYPES or not legislation_number:
            vote["text"] = None
            continue

        # The vote date decides which version is picked, so it belongs in the key.
        key = (vote["congress"], legislation_type, legislation_number, vote.get("startDate"))
        if key not in text_cache:
            text_cache[key] = get_legislation_text(
                vote["congress"],
                legislation_type,
                legislation_number,
                vote.get("startDate"),
            )
        vote["text"] = text_cache[key]

    return votes

def get_transformed_house_votes_by_congress(congress: int):
    votes = get_house_votes(congress)
    count = 0
    return get_house_votes_with_details(votes, count)
